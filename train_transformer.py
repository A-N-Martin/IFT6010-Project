"""
Train a unimodal or multimodal transformer model to translate from source to target language
"""

import argparse
import json
import os
import time
from typing import List, Union

import numpy as np
import tensorflow as tf
import tensorflow_datasets as tfds
from tensorflow.compat.v1 import ConfigProto, InteractiveSession
from tensorflow.python.framework.errors_impl import NotFoundError

from scripts.config import ConfigTrainTransformer
from utils.data_utils import (build_tokenizer, create_transformer_dataset,
                              create_transformer_multi_dataset, project_root, get_features)
from utils.tensorboard_utils import get_summary_tf, hparams_transformer
from utils.transformer_utils import (CustomSchedule, create_masks, load_transformer)
from evaluator import generate_predictions, compute_bleu

# The following config setting is necessary to work on my local RTX2070 GPU
# Comment if you suspect it's causing trouble
tf_config = ConfigProto()
tf_config.gpu_options.allow_growth = True
session = InteractiveSession(config=tf_config)

os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"


def load_tokenizer(name: str, path: str, input_file: List[str], vocab_size: int):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:

        tokenizer = tfds.deprecated.text.SubwordTextEncoder.load_from_file(path)
        #tokenizer = tfds.features.text.SubwordTextEncoder.load_from_file(path)
        tf.print(f"Loaded {name} tokenizer from {path}")
    except NotFoundError:
        tf.print(f"Could not find {name} tokenizer in {path}, building tokenizer...")
        tokenizer = build_tokenizer(input_file, target_vocab_size=vocab_size)
        tokenizer.save_to_file(path)
        tf.print(f"{name} tokenizer saved to {path}")
        # Reload to avoid weird error about mismatch vocabulary size
        tokenizer = tfds.deprecated.text.SubwordTextEncoder.load_from_file(path)
        #tokenizer = tfds.features.text.SubwordTextEncoder.load_from_file(path)

    return tokenizer


def train_transformer(
        config_path: str,
        data_path: str,
        save_path: str,
        restore_checkpoint: bool,
        print_all_scores: bool = False
) -> None:
    """
    Train the Transformer model
    """
    tf.random.set_seed(42)  # Set seed for reproducibility

    assert os.path.isfile(config_path), f"invalid config file: {config_path}"
    with open(config_path, "r") as f_in:
        config: ConfigTrainTransformer = json.load(f_in)

    num_examples = config["num_examples"]  # set to a smaller number for debugging if needed

    source_training = os.path.join(data_path, config["source_training"])
    source_validation = os.path.join(data_path, config["source_validation"])
    source_target_vocab_size = config["source_target_vocab_size"]

    target_training = os.path.join(data_path, config["target_training"])
    target_validation = os.path.join(data_path, config["target_validation"])
    target_target_vocab_size = config["target_target_vocab_size"]

    tokenizer_source_path = os.path.join(save_path, config["tokenizer_source_path"])
    tokenizer_target_path = os.path.join(save_path, config["tokenizer_target_path"])

    multi = config["multi"] # if true, multimodal transformer receives image and text features
    if multi:
        vf_train_path = os.path.join(data_path, config["vfeature_training"])
        vf_valid_path = os.path.join(data_path, config["vfeature_validation"])
        # return tupple of numpy arrays... (for now)
        vfeat_training, vfeat_validation = get_features(vf_train_path, vf_valid_path)
        #print(vfeat_train.shape, vfeat_val.shape)
        shuffled = config["shuffled"] # if true, randomly shuffle images in the train set
        if shuffled:
            # shuffles the array in place along the first axis of a multi-dimensional array
            np.random.shuffle(vfeat_training)
    else:
        vfeat_validation = None

    # Set hyperparameters
    d_model = config["d_model"]
    batch_size = config["batch_size"]
    epochs = config["epochs"]
    if multi:
        vf_dim = config["vfeature_dims"]

    checkpoint_path = os.path.join(save_path, config["checkpoint_path"])
    checkpoint_path_best = os.path.join(save_path, config["checkpoint_path_best"])

    tokenizer_source = load_tokenizer("source", tokenizer_source_path, source_training, source_target_vocab_size)
    tokenizer_target = load_tokenizer("target", tokenizer_target_path, target_training, target_target_vocab_size)

    train_encoder_embedding = config["train_encoder_embedding"]
    train_decoder_embedding = config["train_decoder_embedding"]

    transformer = load_transformer(config, tokenizer_source, tokenizer_target,
                                   train_encoder_embedding,
                                   train_decoder_embedding)

    with open(source_training, "r", encoding="utf-8") as f_train_source:
        buffer_size = sum([1 for _ in f_train_source.readlines()])

    def encode(source, target):
        # Add start and end token
        source_tokenized = [tokenizer_source.vocab_size] + tokenizer_source.encode(
            source.numpy()) + [tokenizer_source.vocab_size + 1]

        target_tokenized = [tokenizer_target.vocab_size] + tokenizer_target.encode(
            target.numpy()) + [tokenizer_target.vocab_size + 1]

        return source_tokenized, target_tokenized

    def encode_multi(source, target, img):
        # Add start and end token to text
        source_tokenized = [tokenizer_source.vocab_size] + tokenizer_source.encode(
            source.numpy()) + [tokenizer_source.vocab_size + 1]

        target_tokenized = [tokenizer_target.vocab_size] + tokenizer_target.encode(
            target.numpy()) + [tokenizer_target.vocab_size + 1]

        return source_tokenized, target_tokenized, img

    def tf_encode(source, target):
        # encapsulate our encode function in a tf functions so it can be called on tf tensor
        result_source, result_target = tf.py_function(encode, [source, target], [tf.int64, tf.int64])
        result_source.set_shape([None])
        result_target.set_shape([None])

        return result_source, result_target

    def tf_encode_multi(source, target, img):
        # encapsulate our encode function in a tf functions so it can be called on tf tensor
        result_source, result_target, result_img = tf.py_function(encode_multi, [source, target, img], [tf.int64, tf.int64, tf.float16])
        result_source.set_shape([None])
        result_target.set_shape([None])
        # DO NOT set shape of image tensor to [None]: will create problems at padding if 3D is flattened
        #result_target.set_shape(vf_dim)

        return result_source, result_target, result_img

    if multi:
        # Multimodal adaptation based on: https://www.tensorflow.org/tutorials/text/image_captioning
        train_examples = create_transformer_multi_dataset(
            source_training, target_training, vfeat_training, num_examples)

        validation_examples = create_transformer_multi_dataset(source_validation, target_validation,
                                                               vfeat_validation)

        train_preprocessed = (
            # cache the dataset to memory to get a speedup while reading from it.
            # Shuffling will shuffle entire train set between epochs
            # Check here: https://www.tensorflow.org/tutorials/text/image_captioning
            train_examples.map(tf_encode_multi).cache().shuffle(buffer_size)
        )

        val_preprocessed = (validation_examples.map(tf_encode_multi))

        train_dataset = (train_preprocessed
                         .padded_batch(batch_size, padded_shapes=([None], [None], vf_dim))
                         .prefetch(tf.data.experimental.AUTOTUNE))

        val_dataset = (val_preprocessed
                       .padded_batch(1000, padded_shapes=([None], [None], vf_dim)))

    else:
        train_examples = create_transformer_dataset(
            source_training, target_training, num_examples)

        validation_examples = create_transformer_dataset(source_validation, target_validation)

        train_preprocessed = (
            # cache the dataset to memory to get a speedup while reading from it.
            train_examples.map(tf_encode).cache().shuffle(buffer_size)
        )

        val_preprocessed = (validation_examples.map(tf_encode))

        train_dataset = (train_preprocessed
                         .padded_batch(batch_size, padded_shapes=([None], [None]))
                         .prefetch(tf.data.experimental.AUTOTUNE))

        val_dataset = (val_preprocessed
                       .padded_batch(1000, padded_shapes=([None], [None])))

    # Use the Adam optimizer with a custom learning rate scheduler according to the formula
    # in the paper (https://arxiv.org/abs/1706.03762)
    learning_rate = CustomSchedule(d_model)
    optimizer = tf.keras.optimizers.Adam(learning_rate, beta_1=0.9, beta_2=0.98,
                                         epsilon=1e-9)

    loss_object = tf.keras.losses.SparseCategoricalCrossentropy(
        from_logits=True, reduction='none')

    def loss_function(real, pred):
        mask = tf.math.logical_not(tf.math.equal(real, 0))
        loss_ = loss_object(real, pred)
        mask = tf.cast(mask, dtype=loss_.dtype)
        loss_ *= mask

        return tf.reduce_mean(loss_)

    train_loss = tf.keras.metrics.Mean(name='train_loss')
    train_accuracy = tf.keras.metrics.SparseCategoricalAccuracy(
        name='train_accuracy')
    val_loss = tf.keras.metrics.Mean(name='val_loss')
    val_accuracy = tf.keras.metrics.SparseCategoricalAccuracy(
        name='val_accuracy')

    ckpt = tf.train.Checkpoint(transformer=transformer,
                               optimizer=optimizer)

    ckpt_manager = tf.train.CheckpointManager(ckpt, checkpoint_path, max_to_keep=10)
    ckpt_manager_best = tf.train.CheckpointManager(ckpt, checkpoint_path_best, max_to_keep=1)
    if restore_checkpoint:
        # if a checkpoint exists, restore the latest checkpoint.
        if ckpt_manager.latest_checkpoint:
            ckpt.restore(ckpt_manager.latest_checkpoint)
            tf.print(f'Latest checkpoint restored from {checkpoint_path}')


    if multi:
        im_dims = tuple([None] + vf_dim)
        #train_step_signature = [
        #    tf.TensorSpec(shape=(None, None), dtype=tf.int64),
        #    tf.TensorSpec(shape=(None, None), dtype=tf.int64),
        #    tf.TensorSpec(shape=im_dims, dtype=tf.float16)
        #]

        #@tf.function(input_signature=train_step_signature)
        def train_step(inp, tar, img):

            tar_inp = tar[:, :-1]
            tar_real = tar[:, 1:]

            # TODO: adjust mask dims for input?
            enc_padding_mask, combined_mask, dec_padding_mask = create_masks(inp, tar_inp, tuple(vf_dim))

            inp_tuple = inp, tar_inp, img
            with tf.GradientTape() as tape:
                predictions, _ = transformer(inp_tuple,
                                             True,
                                             enc_padding_mask,
                                             combined_mask,
                                             dec_padding_mask)
                loss = loss_function(tar_real, predictions)

            gradients = tape.gradient(loss, transformer.trainable_variables)
            optimizer.apply_gradients(zip(gradients, transformer.trainable_variables))

            train_loss(loss)
            train_accuracy(tar_real, predictions)

        #@tf.function(input_signature=train_step_signature)
        def validate(inp, tar, img):
            tar_inp = tar[:, :-1]
            tar_real = tar[:, 1:]

            enc_padding_mask, combined_mask, dec_padding_mask = create_masks(inp, tar_inp, tuple(vf_dim))

            inp_tuple = inp, tar_inp, img
            predictions, _ = transformer(inp_tuple,
                                         True,
                                         enc_padding_mask,
                                         combined_mask,
                                         dec_padding_mask)
            loss = loss_function(tar_real, predictions)

            val_loss(loss)
            val_accuracy(tar_real, predictions)

    else:
        #train_step_signature = [

        #    tf.TensorSpec(shape=(None, None), dtype=tf.int64),
        #    tf.TensorSpec(shape=(None, None), dtype=tf.int64)
        #]

        #@tf.function(input_signature=train_step_signature)
        def train_step(inp, tar):

            tar_inp = tar[:, :-1]
            tar_real = tar[:, 1:]

            enc_padding_mask, combined_mask, dec_padding_mask = create_masks(inp, tar_inp)

            inp_tuple = inp, tar_inp
            with tf.GradientTape() as tape:
                predictions, _ = transformer(inp_tuple,
                                             True,
                                             enc_padding_mask,
                                             combined_mask,
                                             dec_padding_mask)
                loss = loss_function(tar_real, predictions)

            gradients = tape.gradient(loss, transformer.trainable_variables)
            optimizer.apply_gradients(zip(gradients, transformer.trainable_variables))

            train_loss(loss)
            train_accuracy(tar_real, predictions)

        #@tf.function(input_signature=train_step_signature)

        def validate(inp, tar):

            tar_inp = tar[:, :-1]
            tar_real = tar[:, 1:]

            enc_padding_mask, combined_mask, dec_padding_mask = create_masks(inp, tar_inp)

            inp_tuple = inp, tar_inp
            predictions, _ = transformer(inp_tuple,
                                         True,
                                         enc_padding_mask,
                                         combined_mask,
                                         dec_padding_mask)
            loss = loss_function(tar_real, predictions)

            val_loss(loss)
            val_accuracy(tar_real, predictions)

    n_train_examples = int(tf.data.experimental.cardinality(train_examples).numpy())
    tf.print(f"Total of {n_train_examples} training examples")
    train_summary_writer, val_summary_writer = get_summary_tf(
        save_path, hparams_transformer(config, n_train_examples)
    )

    best_val_accuracy = -1
    for epoch in range(epochs):
        start = time.time()

        train_loss.reset_states()
        train_accuracy.reset_states()
        val_loss.reset_states()
        val_accuracy.reset_states()

        if multi:
            for (batch, (inp, tar, img)) in enumerate(train_dataset):
                    train_step(inp, tar, img)

                    if batch % 50 == 0:
                        tf.print(f"Epoch {epoch + 1} Batch {batch} Loss {train_loss.result():.4f} "
                                 f"Accuracy {train_accuracy.result():.4f}")

            for (batch, (inp, tar, img)) in enumerate(val_dataset):
                    validate(inp, tar, img)
                    val_accuracy_result = val_accuracy.result()
                    tf.print(f"Epoch {epoch + 1} Batch {batch} Validation Loss {val_loss.result():.4f} "
                             f"Validation Accuracy {val_accuracy_result:.4f}")
        else:
            for (batch, (inp, tar)) in enumerate(train_dataset):
                    # input_tuple = (inp, tar, img) if multi else (inp, tar)
                    train_step(inp, tar)

                    if batch % 50 == 0:
                        tf.print(f"Epoch {epoch + 1} Batch {batch} Loss {train_loss.result():.4f} "
                                 f"Accuracy {train_accuracy.result():.4f}")

            for (batch, (inp, tar)) in enumerate(val_dataset):
                    # input_tuple = (inp, tar, img) if multi else (inp, tar)
                    validate(inp, tar)
                    val_accuracy_result = val_accuracy.result()
                    tf.print(f"Epoch {epoch + 1} Batch {batch} Validation Loss {val_loss.result():.4f} "
                             f"Validation Accuracy {val_accuracy_result:.4f}")


        if val_accuracy_result > best_val_accuracy:
            best_val_accuracy = val_accuracy_result
            ckpt_save_path_best = ckpt_manager_best.save()
            tf.print(f"Saving best checkpoint for epoch {epoch + 1} at {ckpt_save_path_best}")
        if (epoch + 1) % 5 == 0:
            ckpt_save_path = ckpt_manager.save()
            tf.print(f"Saving checkpoint for epoch {epoch + 1} at {ckpt_save_path}")

        # Write loss and accuracy so that they can be loaded with tensorboard
        with train_summary_writer.as_default():
            tf.summary.scalar('loss', train_loss.result(), step=epoch)
            tf.summary.scalar('accuracy', train_accuracy.result(), step=epoch)
        with val_summary_writer.as_default():
            tf.summary.scalar('loss', val_loss.result(), step=epoch)
            tf.summary.scalar('accuracy', val_accuracy.result(), step=epoch)

        tf.print(f"Epoch {epoch + 1} Loss {train_loss.result():.4f} Accuracy {train_accuracy.result():.4f}")

        tf.print(f"Time taken for 1 epoch: {time.time() - start} secs\n")

    # Compute bleu score on best performing model
    #temp_file = os.path.join(project_root(), "temp_preds.txt")
    temp_file = os.path.join(save_path, "temp_preds.txt")
    generate_predictions(data_path, source_validation, temp_file, save_path, config_path, img_array = vfeat_validation)
    compute_bleu(temp_file, target_validation, print_all_scores)
    os.remove(temp_file)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg_path", type=str,
                        help="path to the JSON config file used to define train parameters")
    parser.add_argument('--restore_checkpoint',
                        help='will restore the latest checkpoint',
                        action='store_true')
    parser.add_argument("--data_path", type=str,
                        help="path to the directory where the data is", default=project_root())
    parser.add_argument("--save_path", type=str,
                        help="path to the directory where to save model/tokenizer", default=project_root())
    args = parser.parse_args()
    data_path = args.data_path
    save_path = args.save_path
    config_path = args.cfg_path
    restore_checkpoint = args.restore_checkpoint
    train_transformer(config_path, data_path, save_path, restore_checkpoint)


if __name__ == "__main__":
    main()

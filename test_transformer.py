"""
Test a trained transformer model to translate from source to target language
"""

import argparse
import json
import os

import tensorflow as tf
from tensorflow.compat.v1 import ConfigProto, InteractiveSession

from utils.data_utils import project_root
from evaluator import generate_predictions, compute_bleu

# The following config setting is necessary to work on my local RTX2070 GPU
# Comment if you suspect it's causing trouble
tf_config = ConfigProto()
tf_config.gpu_options.allow_growth = True
session = InteractiveSession(config=tf_config)

os.environ["TF_FORCE_GPU_ALLOW_GROWTH"] = "true"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--cfg_path", type=str,
                        help="path to the JSON config file used to define train parameters")
    parser.add_argument("--data_path", type=str,
                        help="path to the directory where the data is", default=project_root())
    parser.add_argument("--save_path", type=str,
                        help="path to the directory where to save model/tokenizer", default=project_root())

    args = parser.parse_args()

    config_path = args.cfg_path
    data_path = args.data_path
    save_path = args.save_path

    assert os.path.isfile(config_path), f"invalid config file: {config_path}"
    with open(config_path, "r") as f_in:
        config: ConfigTrainTransformer = json.load(f_in)

    target_file_path = os.path.join(data_path, config["target_test"])
    print_all_scores = config["print_all_scores"]
    do_not_run_model = config["do_not_run_model"]

    if do_not_run_model:
        input_file_path = os.path.join(data_path, config["input_file"])
        compute_bleu(input_file_path, target_file_path, print_all_scores)
    else:
        source_file_path = os.path.join(data_path, config["source_test"])
        temp_file = os.path.join(save_path, "temp_preds.txt")
        generate_predictions(source_file_path, temp_file, save_path, config_path)
        compute_bleu(temp_file, target_file_path, print_all_scores)
        #os.remove(temp_file)


if __name__ == "__main__":
    main()

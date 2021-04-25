from typing import Optional

from typing_extensions import TypedDict


class ConfigEvalTransformer(TypedDict):
    debug: bool
    num_examples: int
    multi: bool
    num_layers: int
    d_model: int
    dff: int
    num_heads: int
    dropout_rate: float
    vfeature_dims: Optional[list]
    vfeature_test: Optional[str]
    translation_batch_size: int
    source_test: str
    target_test: str
    checkpoint_path_best: str
    tokenizer_source_path: str
    tokenizer_target_path: str
    beam_size: Optional[int]
    alpha: Optional[float]
    do_not_run_model: bool
    input_file: Optional[str]
    print_all_scores: bool


class ConfigTrainTransformer(TypedDict):
    num_examples: int
    multi: bool
    num_layers: int
    d_model: int
    dff: int
    num_heads: int
    dropout_rate: float
    batch_size: int
    epochs: int
    vfeature_dims: Optional[list]
    vfeature_training: Optional[str]
    vfeature_validation: Optional[str]
    source_training: str
    source_validation: str
    source_target_vocab_size: int
    target_training: str
    target_validation: str
    target_target_vocab_size: int
    checkpoint_path: str
    checkpoint_path_best: str
    tokenizer_source_path: str
    tokenizer_target_path: str
    train_encoder_embedding: bool
    train_decoder_embedding: bool

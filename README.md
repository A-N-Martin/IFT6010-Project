# IFT6010-Project, UdeM, Winter 2021

Multimodal Machine Translation with Deep Learning

Annabelle Martin, 891129, annabelle.martin@umontreal.ca \
Marie St-Laurent, 657930, marie.st-laurent@umontreal.ca

## Summary
We contrasted multimodal and unimodal  neural  machine  translation  (NMT)  to explore whether visual features can improve  the  quality of  translation  for  textual  image  descriptions.

Our Tensorflow 2.4.1 implementation of the Transformer is based on the following tutorial: https://www.tensorflow.org/tutorials/text/transformer

We  replaced  the  encoder’s  self-attention  layer  with  a  multi-modal self-attention layer that can process text and visual information, based on an approach introduced by Yao and Wan (2020).
https://www.aclweb.org/anthology/2020.acl-main.400/

We contacted the authors via email, and they kindly shared a link to a repository that includes their implementation (https://github.com/QAQ-v/MMT; code in Pytorch). This repository has just become publicly available on https://paperswithcode.com/ \
We based ourselves on this code to integrate the multi-modal self-attention layer within our multimodal Tensorflow implementation.

Our models were trained and tested with MM-NMT benchmark dataset Multi30k (Elliot et al., 2016; http://www.aclweb.org/anthology/W16-3210), which we downloaded from the following repository: https://github.com/multi30k/dataset \
Image features are not included in the current repository due to space considerations. Visual features pre-extracted with a ResNet50 pre-trained on ImageNet can be downloaded from Google Drive (https://drive.google.com/drive/folders/1I2ufg3rTva3qeBkEc-xDpkESsGkYXgCf) and saved under ./data/images/res50_features. Raw images can be requested from the Dep. of Computer Sciences of the University of Illinois at Urbana-Champaign (https://forms.illinois.edu/sec/229675).

In our experiments, models were trained to translate from German to English to facilitate our qualitative assessment of translation quality (we are not fluent in German). We either used visual features outputted from the 4th or average pooling layers of a ResNet50 (made available with Multi30k). Our baselines included a unimodal Transformer, and a multimodal Transformer trained on randomly shuffled images that were not associated with the source and target parallel sentences.

Translation  quality was measured with the BLEU score (Papineni et al., 2002), which we computed using  the  SACREBLEU  implementation  introduced  by  Post  (2018) based  on  a  script  provided for UdeM class IFT6759 (Winter 2020; https://github.com/mila-iqia/ift6759)

## Train the model with train_transformer.py

From the project root folder, type the following command:

./train_transformer.sh config_file_name.json

Bash script `train_transformer.sh` calls train_transformer.py  to train a model. The bash script takes as its sole argument the name of the config file that specifies the experimental variables (source and target text files, model hyper-parameters, etc). Config files must be saved under ./config_files
(several examples are saved under ./config_files).

Within the config .json files, set "shuffled": true for multimodal models to randomly shuffle the order of the image features in the training batch (so that images do not correspond to the source and target text).


## Evaluate model performance on a test set with evaluator.py

From the project root folder, type the following command:

./test_transformer.sh config_file_name.json

Bash script `evaluator.sh` calls test_transformer.py to test a pretrained model on a specified test set. The bash script takes as its sole argument the name of the config file that specifies the experimental variables. Config files must be saved under ./config_files

The script calculates BLEU on the specified test set, and it saves translated output as a text file (temp_preds.txt) under ./results

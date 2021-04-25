Data source: Multi30k Data Repository
--
The following text is adapted from the Multi30k Data Repository's ReadMe
Source: https://github.com/multi30k/dataset

### Getting ready

Along with the data files, the Multi30k Data Repository also provides:
  - subword-nmt as a GIT submodule
  - A snapshot of Moses preprocessing scripts (December 2017)

Preprocessing scripts can be found under [text/scripts/](text/scripts/)
Their purpose is to minimize processing differences across users.

### Visual features

Image features are not saved in the current repository due to space considerations. Pre-extracted visual features can be [downloaded from Google Drive](https://drive.google.com/drive/folders/1I2ufg3rTva3qeBkEc-xDpkESsGkYXgCf?usp=sharing) and saved under ./data/images/res50_features. Raw images (Flickr30k) can be [requested here](https://forms.illinois.edu/sec/229675) from the Dep. of Computer Sciences of the University of Illinois at Urbana-Champaign.

### Task 1 (used for current project)

- Raw files under [data/text/task1/raw](data/text/task1/raw)
- Tokenized files under [data/text/task1/tok](data/text/task1/tok). These files were
  produced with the preprocessing script [text/scripts/task1-tokenize.sh](text/scripts/task1-tokenize.sh).

#### Statistics

```
train
 (en) 29000 sentences, 377534 words, 13.0 words/sent
 (de) 29000 sentences, 360706 words, 12.4 words/sent
val
 (en) 1014 sentences, 13308 words, 13.1 words/sent
 (de) 1014 sentences, 12828 words, 12.7 words/sent
test_2016_flickr
 (en) 1000 sentences, 12968 words, 13.0 words/sent
 (de) 1000 sentences, 12103 words, 12.1 words/sent
test_2017_flickr
 (en) 1000 sentences, 11376 words, 11.4 words/sent
 (de) 1000 sentences, 10758 words, 10.8 words/sent
test_2017_mscoco
 (en) 461 sentences, 5239 words, 11.4 words/sent
 (de) 461 sentences, 5158 words, 11.2 words/sent
```
If you use these resources in your research, please consider citing the following papers:

English and German data:
```
@InProceedings{W16-3210,
  author = 	"Elliott, Desmond
		and Frank, Stella
		and Sima'an, Khalil
		and Specia, Lucia",
  title = 	"Multi30K: Multilingual English-German Image Descriptions",
  booktitle = 	"Proceedings of the 5th Workshop on Vision and Language",
  year = 	"2016",
  publisher = 	"Association for Computational Linguistics",
  pages = 	"70--74",
  location = 	"Berlin, Germany",
  doi = 	"10.18653/v1/W16-3210",
  url = 	"http://www.aclweb.org/anthology/W16-3210"
}
```

French data, Ambiguous COCO evaluation data, and Test 2017 data:
```
@InProceedings{elliott-EtAl:2017:WMT,
  author    = {Elliott, Desmond  and  Frank, Stella  and  Barrault, Lo\"{i}c  and  Bougares, Fethi  and  Specia, Lucia},
  title     = {Findings of the Second Shared Task on Multimodal Machine Translation and Multilingual Image Description},
  booktitle = {Proceedings of the Second Conference on Machine Translation, Volume 2: Shared Task Papers},
  month     = {September},
  year      = {2017},
  address   = {Copenhagen, Denmark},
  publisher = {Association for Computational Linguistics},
  pages     = {215--233},
  url       = {http://www.aclweb.org/anthology/W17-4718}
}
```

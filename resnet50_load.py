from keras.applications.resnet50 import ResNet50
from keras.models import Model
import keras


#IMG Height and IMG WIDTH need to be given based on Multi30K image size

def load_resnet(IMG_HEIGHT, IMG_WIDTH):
    restnet = ResNet50(include_top=False, weights='imagenet', input_shape=(IMG_HEIGHT,IMG_WIDTH,3))
    output = restnet.layers[-1].output
    output = keras.layers.Flatten()(output)
    restnet = Model(restnet.input, output=output)

    for layer in restnet.layers:
        layer.trainable = False

    return restnet


## We might need to add more layers but that's a start

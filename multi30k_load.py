import tensorflow as tf

def Multi30K(path):
  data = tf.data.TextLineDataset(path)
  def content_filter(source):
    return tf.logical_not(tf.strings.regex_full_match(
        source, 
        '([[:space:]][=])+.+([[:space:]][=])+[[:space:]]*'))
  data = data.filter(content_filter)
  data = data.map(lambda x: tf.strings.split(x, ' . '))
  data = data.unbatch()
  return data

train= Multi30K('http://www.quest.dcs.shef.ac.uk/wmt16_files_mmt/training.tar.gz')

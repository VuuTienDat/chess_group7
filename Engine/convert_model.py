import tensorflow as tf
from tensorflow.python.platform import gfile

pb_path = "Engine\models\maia_1900.pb"  # Đặt đúng đường dẫn đến file

graph = tf.Graph()
with graph.as_default():
    with gfile.FastGFile(pb_path, 'rb') as f:
        graph_def = tf.compat.v1.GraphDef()
        graph_def.ParseFromString(f.read())
        tf.import_graph_def(graph_def, name="")

    for op in graph.get_operations():
        print(op.name)

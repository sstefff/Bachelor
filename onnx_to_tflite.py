import onnx
from onnx_tf.backend import prepare
import tensorflow as tf


onnx_model = onnx.load("connect4_nnue_weights.onnx")
tf_rep = prepare(onnx_model)

tf_model_dir = "./tf_model"
tf_rep.export_graph(tf_model_dir)

converter = tf.lite.TFLiteConverter.from_saved_model(tf_model_dir)
converter.optimizations = [tf.lite.Optimize.DEFAULT]

tflite_model = converter.convert()

with open("connect4_model_optimized.tflite", "wb") as f:
    f.write(tflite_model)

print("Optimized TensorFlow Lite model saved successfully!")

#https://www.geeksforgeeks.org/machine-learning/convert-pytorch-model-to-tf-lite-with-onnx-tf/
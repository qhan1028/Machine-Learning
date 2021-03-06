# ML2017 hw3 Plot Model

from sys import argv
import numpy as np
import seaborn as sb
import pandas as pd
import matplotlib.pyplot as plt
import csv
import os
os.environ['TF_CPP_MIN_LOG_LEVEL']='3'
from keras.models import load_model
from keras.utils import plot_model, np_utils
from sklearn.metrics import confusion_matrix
import keras.backend as K


READ_FROM_NPZ = 1
CATEGORY = 7
SHAPE = 48

STRUCTURE = 0
CONFUSION = 0
OLD_SALIENCY = 0
SALIENCY = 1
HISTORY = 0

def read_train(filename):
	
	X, Y = [], []
	with open(filename, "r", encoding="big5") as f:
		count = 0
		for line in list(csv.reader(f))[1:]:
			Y.append( float(line[0]) )
			X.append( [float(x) for x in line[1].split()] )
			count += 1
			print("\rX_train: " + repr(count), end="", flush=True)
		print("", flush=True)

	return np.array(X), np_utils.to_categorical(Y, CATEGORY)

# argv: [1]train.csv [2]model.h5
def main():

	X, Y = [], []
	if READ_FROM_NPZ:
		print("read from npz...")
		data = np.load("data.npz")
		X = data['arr_0']
		Y = data['arr_1']
	else:
		print("read train data...")
		X, Y = read_train(argv[1])

	X = X / 255
	X = X.reshape(X.shape[0], SHAPE, SHAPE, 1)
	
	print("load model...")
	model_name = argv[2]
	model = load_model(model_name)
	
	label = ["angry", "disgust", "fear", "happy", "sad", "suprise", "neutral"]

	if STRUCTURE:
		model.summary()
		print("plot structure...")
		#plot_model(model, show_layer_names=False, show_shapes=True, to_file=model_name[:-3] + "_struct.png")

	if CONFUSION:
		print("plot confusion matrix...")
		Y_1D = np.argmax(Y, 1)
		print("predict train data...")
		predict = model.predict(X, verbose=1, batch_size=32)
		Y_predict = np.argmax(predict, 1)
		cm = confusion_matrix(Y_1D, Y_predict)
		print(cm)

		sb.set(font_scale=1.4)
		figure = sb.heatmap(cm, annot=True, annot_kws={"size": 16 }, fmt='d', cmap='YlGnBu')
		figure.set_xticklabels(label)
		figure.set_yticklabels(label)
		plt.yticks(rotation=0)
		plt.xlabel("Predicted Label")
		plt.ylabel("True Label")
		figure.get_figure().savefig(model_name[:-3] + "_cm.png")

	if SALIENCY:
		print("print saliency map...")
		plt.figure(figsize=(16, 6))
		emotion_classifier = load_model(model_name)
		input_img = emotion_classifier.input
		img_ids = [(1, 12928), (2, 25419), (3, 7824), (4, 27865), (5, 18872), (6, 16237), (7, 1206)]
		for i, idx in img_ids:

			print("plot figure %d." % idx)
			img = X[idx].reshape(1, 48, 48, 1)
			val_proba = emotion_classifier.predict(img)
			pred = val_proba.argmax(axis=-1)
			target = K.mean(emotion_classifier.output[:, pred])
			grads = K.gradients(target, input_img)[0]
			fn = K.function([input_img, K.learning_phase()], [grads])

			heatmap = fn([img, 0])[0]
			heatmap = heatmap.reshape(48, 48)
			heatmap /= heatmap.std()

			see = img.reshape(48, 48)
			plt.subplot(3, 7, i)
			plt.imshow(see, cmap='gray')
			plt.title("%d. %s" % (idx, label[Y[idx].argmax()]) )

			thres = heatmap.std()
			see[np.where(abs(heatmap) <= thres)] = np.mean(see)

			plt.subplot(3, 7, i+7)
			plt.imshow(heatmap, cmap='jet')
			plt.colorbar()
			plt.tight_layout()

			plt.subplot(3, 7, i+14)
			plt.imshow(see,cmap='gray')
			plt.colorbar()
			plt.tight_layout()

		plt.savefig("%s_sm.png" % model_name[:-3], dpi=100)
		plt.show()

	if OLD_SALIENCY:
		fig_no = [(1, 12928), (2, 25419), (3, 7824), (4, 27865), (5, 18872), (6, 16237), (7, 1206)]
		fig_num = len(fig_no)
		plt.figure(figsize=(16, 4))
		plt.subplots_adjust(wspace=0.4)
		for i, f in fig_no:
			print("plot image " + repr(f) + "...")
			ax = plt.subplot(2, fig_num, i)
			plt.title(repr(f) + ".")
			plt.imshow(X[f].reshape(SHAPE, SHAPE), cmap='gray')
			ax.set_xticks([10, 20, 30, 40])
			ax.set_yticks([10, 20, 30, 40])
			ax.set_xticklabels([10, 20, 30, 40])
			ax.set_yticklabels([10, 20, 30, 40])

			print("plot saliency maps on image " + repr(f) + "...")
			ax = plt.subplot(2, fig_num, i+fig_num)
			X_fig = X[f].reshape(1, SHAPE, SHAPE, 1)
			Y_fig = Y[f].reshape(1, CATEGORY)
			plt.title(label[Y_fig.argmax()])

			score = model.evaluate(X_fig, Y_fig, verbose=1)
			original_loss = score[0]
			loss_matrix = np.zeros([SHAPE, SHAPE])
			for i in range(SHAPE):
				for j in range(SHAPE):
					print("\rrow: " + repr(i) + " column: " + repr(j), end="", flush=True)
					X_tmp = np.array(X_fig)
					X_tmp[0][i][j][0] += 1
					X_tmp /= 255.
					score = model.evaluate(X_tmp, Y_fig, verbose=0)
					loss_matrix[i][j] = (score[0] - original_loss) ** 2
			print("", flush=True)

			plt.imshow(loss_matrix, cmap='jet', vmin=loss_matrix.min(), vmax=loss_matrix.max())
			ax.set_xticks([10, 20, 30, 40])
			ax.set_yticks([10, 20, 30, 40])
			ax.set_xticklabels([10, 20, 30, 40])
			ax.set_yticklabels([10, 20, 30, 40])
		plt.savefig(model_name[:-3] + "_sm.png")
		plt.show()

	if HISTORY:
		plt.clf()
		history = np.load(model_name[:-3] + "_history.npz")
		acc = history['arr_0']
		val_acc = history['arr_1']
		plt.plot(acc, 'b')
		plt.plot(val_acc, 'r')
		plt.legend(["acc", "val_acc"], loc="upper left")
		plt.plot(acc, 'bo')
		plt.plot(val_acc, 'ro')
		plt.yticks(np.linspace(0.1, 0.8, 8))
		plt.xlabel("epochs")
		plt.ylabel("accuracy")
		plt.title("Training Process of %s" % model_name)
		plt.savefig(model_name[:-3] + "_his.png")
		plt.show()

if __name__ == "__main__":
	main()

import os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'

import csv
import cv2
import os
import numpy as np
import random
from random import shuffle
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from tensorflow.python.keras.models import Model
from tensorflow.python.keras.layers import Conv2D, Dense, Flatten, Lambda, Dropout
from tensorflow.python import keras
from tensorflow.python.keras import metrics, optimizers, losses
import tensorflow as tf



assert hasattr(tf, "function") # Be sure to use tensorflow 2.0
DATA_PATH = "data/"
DATA_IMG = "data/"
def load_data():
    print("search data...")
    data_df = pd.read_csv(os.path.join(os.getcwd(),DATA_PATH, 'driving_log.csv'), names=['center', 'left', 'right', 'steering', 'throttle', 'reverse', 'speed'])
    X = data_df[['center', 'left', 'right']].values
    y = data_df['steering'].values
    print(y.shape)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.15, random_state=0)
    print("data find")
    return X_train, X_test, y_train, y_test

def get_data(batch_size,imageData, rotationData):
    print("load data...")
    rotations = []
    images = []
    angle_correction = [0., 0.25, -0.25] # [Center, Left, Right]
    print("size",imageData.shape)
    for index in range(0,batch_size):
        
        i = random.choice([0, 1, 2]) # for direction
        img = cv2.imread(os.path.join(DATA_IMG,imageData[index][i]).replace(" ", ""))
        #converti la couleur de l'image
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        #recupere la rotation 
        rotation = float(rotationData[index])
        #ajou de la correction
        rotation = rotation + angle_correction[i]
        #ajou des informations a la liste
        images.append(img)
        rotations.append(rotation)

    print("il y a eu",len(images),"images de chargées")
    return np.array(images), np.array(rotations)

# création du reseaux convolutif
class ConvModel(keras.Model):

    def __init__(self):
        super(ConvModel, self).__init__()
        # Convolutions
        self.alea = tf.keras.layers.Lambda(lambda x: (x / 127.5) - 1., input_shape = (160, 320, 3))
        self.crop = tf.keras.layers.Cropping2D(cropping=((70, 25), (0, 0)), input_shape = (160, 320, 3))
        self.conv1_1 = tf.keras.layers.Conv2D(16, 9, strides=(4, 4), padding="same", activation='elu', name="conv1_1")
        self.conv1_2 = tf.keras.layers.Conv2D(32, 5, strides=(2, 2), padding="same", activation='elu', name="conv1_2")
        self.conv1_3 = tf.keras.layers.Conv2D(64, 4, strides=(1, 1), padding="same", activation='elu', name="conv1_3")
        self.pool1 = keras.layers.MaxPooling2D(pool_size=[2, 2], strides=2, padding="same")
        
        self.conv2_1 = tf.keras.layers.Conv2D(64, 3, strides=(1, 1), padding="same", activation='elu', name="conv2_1")
        self.conv2_2 = tf.keras.layers.Conv2D(64, 3, strides=(1, 1), padding="same", activation='elu', name="conv2_2")
        self.conv2_3 = tf.keras.layers.Conv2D(64, 3, strides=(1, 1), padding="same", activation='elu', name="conv2_3")
        self.pool2 = keras.layers.MaxPooling2D(pool_size=[2, 2], strides=2, padding="same")
        # Flatten the convolution
        self.flatten = keras.layers.Flatten(name="flatten")
        # Dense layers
        self.d1 = keras.layers.Dense(1024, activation='elu', name="d1")
        self.out = keras.layers.Dense(1, activation='sigmoid', name="output")

    def call(self, image):
        alea = self.alea(image)
        crop = self.crop(alea)
        conv1_1 = self.conv1_1(crop)
        conv1_2 = self.conv1_2(conv1_1)
        conv1_3 = self.conv1_3(conv1_2)
        pool1 = self.pool1(conv1_3)

        conv2_1 = self.conv2_1(pool1)
        conv2_2 = self.conv2_2(conv2_1)
        conv2_3 = self.conv2_3(conv2_2)
        pool2 = self.pool2(conv2_3)

        flatten = self.flatten(pool2)
        d1 = self.d1(flatten)
        output = self.out(d1)
        return output


data = load_data()

model = ConvModel()

x_train = data[0]
x_valid = data[1]
y_train = data[2]
y_valid = data[3]

# Peut etre a retirer next
images, rotations = get_data(2277,x_train,y_train)
images_valid, rotations_valid = get_data(402,x_valid,y_valid)

# conversion des images de float 64 en 32 car con2d veut du 32
images = images.astype(np.float32)
# conversion des images de float 64 en 32 car con2d veut du 32
images_valid = images_valid.astype(np.float32)
#affichage d'un exemple
plt.title(rotations[57])
plt.imshow(images[57]/255)
plt.show()

print("rotation shape",rotations.shape)
print("image shape",images.shape)
print("image validation shape",images_valid.shape)

# Normalisation
print("Moyenne et ecart type des images", images.mean(), images.std())
scaler = StandardScaler()
scaled_images = scaler.fit_transform(images.reshape(-1, 160*320))
scaled_images_valid = scaler.transform(images_valid.reshape(-1, 160*320))
print("Moyenne et ecart type des images normalisé", scaled_images.mean(), scaled_images.std())

scaled_images = images.reshape(-1, 160,320,3)
scaled_images_valid = images_valid.reshape(-1, 160,320,3)
print("scaled images after normalisation",scaled_images.shape)

train_dataset = tf.data.Dataset.from_tensor_slices((scaled_images, rotations))
#train_dataset = train_dataset.shuffle(buffer_size=1280)
train_dataset = train_dataset.shuffle(1280 * 50)
valid_dataset = tf.data.Dataset.from_tensor_slices((scaled_images_valid, rotations_valid))

model = ConvModel()

loss_object = tf.keras.losses.MeanSquaredError()
optimizer = tf.keras.optimizers.Adam(lr=0.000001)
#track the evolution
# Define our metrics
train_loss = tf.keras.metrics.Mean('train_loss')
train_accuracy = tf.keras.metrics.Accuracy('train_accuracy')
valid_loss = tf.keras.metrics.Mean('test_loss')
valid_accuracy = tf.keras.metrics.Accuracy('test_accuracy')

@tf.function
def train_step(image, rotations):
    
    # permet de surveiller les opérations réalisé afin de calculer le gradient
    with tf.GradientTape() as tape:
        # fait une prediction
        predictions = model(image)
        print("rotations shape after creation model",rotations)
        print("prediction shape after creation model",predictions)
        # calcul de l'erreur en fonction de la prediction et des targets
        loss = loss_object(rotations, predictions)
        print("calcul loss",loss)
    # calcul du gradient en fonction du loss
    # trainable_variables est la lst des variable entrainable dans le model
    gradients = tape.gradient(loss, model.trainable_variables)
    print("calcul gradient")
    # changement des poids grace aux gradient
    optimizer.apply_gradients(zip(gradients, model.trainable_variables))
    print("etape optimizer")
    # ajout de notre loss a notre vecteur de stockage
    train_loss(loss)
    print("etape train loss")
    train_accuracy(rotations, predictions)
    print("etape train accuracy")

@tf.function
# vérifier notre accuracy de notre model afin d'evité l'overfitting
def valid_step(image, rotations):
    predictions = model(image)
    t_loss = loss_object(rotations, predictions)
    # mets a jour les metrics
    valid_loss(t_loss)
    valid_accuracy(rotations, predictions)
        

epochs = 10
batch_size = 64

train_log_dir = 'logs/gradient_tape/' + 'v1' + '/train'
test_log_dir = 'logs/gradient_tape/' + 'V1' + '/test'
train_summary_writer = tf.summary.create_file_writer(train_log_dir)
test_summary_writer = tf.summary.create_file_writer(test_log_dir)


for epoch in range(epochs):
    # Training set
    for (images_batch, targets_batch) in train_dataset.batch(batch_size):
        train_step(images_batch, targets_batch)
        
        template = '\r Batch {}/{}, Loss: {}, Accuracy: {}'
    with train_summary_writer.as_default():
        tf.summary.scalar('loss', train_loss.result(), step=epoch)
        tf.summary.scalar('accuracy', train_accuracy.result(), step=epoch)

    # Validation set
    for images_batch, targets_batch in valid_dataset.batch(batch_size):
        valid_step(images_batch, targets_batch)

    with test_summary_writer.as_default():
        tf.summary.scalar('loss', valid_loss.result(), step=epoch)
        tf.summary.scalar('accuracy', valid_accuracy.result(), step=epoch)
    
    template = 'Epoch {}, Loss: {}, Accuracy: {}, valid Loss: {}, valid Accuracy: {}'
    print (template.format(epoch+1,
                            train_loss.result(), 
                            train_accuracy.result()*100,
                            valid_loss.result(), 
                            valid_accuracy.result()*100))

    valid_loss.reset_states()
    valid_accuracy.reset_states()
    train_accuracy.reset_states()
    train_loss.reset_states()

# serialize model to YAML
#model_yaml = model.to_yaml()
#with open("model.yaml", "w") as yaml_file:
    #yaml_file.write(model_yaml)
# serialize weights to HDF5
model.save_weights('my_model_weights.h5')
print("Saved model to disk")

# Export the model to a SavedModel
#keras.experimental.export_saved_model(model, 'saved_model.h5')


model.save('my_model.h5')
print("Saved model to disk")



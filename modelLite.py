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


from tensorflow.python.keras.models import Model
from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.layers import Conv2D, Dense, Flatten, Cropping2D, Lambda, Dropout


assert hasattr(tf, "function") # Be sure to use tensorflow 2.0
DATA_PATH = "data/"
DATA_IMG = "data/"
def load_data():
    print("search data...")
    data_df = pd.read_csv(os.path.join(os.getcwd(),DATA_PATH, 'driving_log.csv'), names=['center', 'left', 'right', 'steering', 'throttle', 'reverse', 'speed'])
    X = data_df[['center', 'left', 'right']].values
    y = data_df['steering'].values
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=0)
    return X_train, X_test, y_train, y_test

def get_data(batch_size,imageData, rotationData):
    print("load data...")
    rotations = []
    images = []
    
    angle_correction = [0., 0.25, -.25] # [Center, Left, Right]

    for index in range(0,batch_size):
        i = random.choice([0, 1, 2]) # for direction

        img = cv2.imread(os.path.join(DATA_IMG,imageData[index][i]).replace(" ", ""))
        if img is None: 
            continue

        #converti la couleur de l'image
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        #img = img.astype(np.float32)
        #recupere la rotation 
        if index%3==0:
            subIndex=index//3
            rotation = float(rotationData[subIndex])

        #ajou de la correction
        rotation = rotation + angle_correction[i]

        #ajou des informations a la liste
        images.append(img)
        rotations.append(rotation)

    print("end loading longeur image:",len(images))

    return np.array(images), np.array(rotations)

# création du reseaux convolutif
# création du reseaux convolutif
class ConvModel(keras.Model):
    def __init__(self):
        super(ConvModel, self).__init__()
        # Convolutions
        self.alea = Lambda(lambda x: (x/127)-1, input_shape=(160,320,3))
        self.crop = keras.layers.Cropping2D(cropping=((70, 25), (0, 0)), name="crop")
        self.conv1_1 = keras.layers.Conv2D(filters=64, kernel_size=[3, 3], padding="same", activation='relu', name="conv1_1")
        self.conv1_2 = keras.layers.Conv2D(filters=64, kernel_size=[3, 3], padding="same", activation='relu', name="conv1_2")
        self.pool1 = keras.layers.MaxPooling2D(pool_size=[2, 2], strides=2, padding="same")

        self.conv2_1 = keras.layers.Conv2D(filters=128, kernel_size=[3, 3], padding="same", activation='relu', name="conv2_1")
        self.conv2_2 = keras.layers.Conv2D(filters=128, kernel_size=[3, 3], padding="same", activation='relu', name="conv2_2")
        self.pool2 = keras.layers.MaxPooling2D(pool_size=[2, 2], strides=2, padding="same")

        self.conv3_1 = keras.layers.Conv2D(filters=256, kernel_size=[3, 3], padding="same", activation='relu', name="conv3_1")
        self.conv3_2 = keras.layers.Conv2D(filters=256, kernel_size=[3, 3], padding="same", activation='relu', name="conv3_2")
        self.pool3 = keras.layers.MaxPooling2D(pool_size=[2, 2], strides=2, padding="same")

        self.conv4_1 = keras.layers.Conv2D(filters=512, kernel_size=[3, 3], padding="same", activation='relu', name="conv4_1")
        self.conv4_2 = keras.layers.Conv2D(filters=512, kernel_size=[3, 3], padding="same", activation='relu', name="conv4_2")
        self.conv4_3 = keras.layers.Conv2D(filters=512, kernel_size=[3, 3], padding="same", activation='relu', name="conv4_3")
        self.pool4 = keras.layers.MaxPooling2D(pool_size=[2, 2], strides=2, padding="same")
        
        self.conv5_1 = keras.layers.Conv2D(filters=512, kernel_size=[3, 3], padding="same", activation='relu', name="conv5_1")
        self.conv5_2 = keras.layers.Conv2D(filters=512, kernel_size=[3, 3], padding="same", activation='relu', name="conv5_2")
        self.conv5_3 = keras.layers.Conv2D(filters=512, kernel_size=[3, 3], padding="same", activation='relu', name="conv5_3")
        self.pool5 = keras.layers.MaxPooling2D(pool_size=[2, 2], strides=2, padding="same")

        # Flatten the convolution
        self.flatten = keras.layers.Flatten(name="flatten")
        # Add layers
        self.d1 = keras.layers.Dense(4096, activation='relu', name="d1")
        self.d2 = keras.layers.Dense(4096, activation='relu', name="d2")
        self.d3 = keras.layers.Dense(1000, activation='relu', name="d3")
        self.out = keras.layers.Dense(1,activation='sigmoid',  name="output")
        

    def call(self, image):
        alea = self.alea(image)
        crop = self.crop(alea)
        conv1_1 = self.conv1_1(crop)
        conv1_2 = self.conv1_2(conv1_1)
        pool1 =self.pool1(conv1_2)
                
        conv2_1 = self.conv2_1(pool1)
        conv2_2 = self.conv2_2(conv2_1)
        pool2 =self.pool2(conv2_2)
        
        conv3_1 = self.conv3_1(pool2)
        conv3_2 = self.conv3_2(conv3_1)
        pool3 =self.pool3(conv3_2)
        
        conv4_1 = self.conv4_1(pool3)
        conv4_2 = self.conv4_2(conv4_1)
        conv4_3 = self.conv4_3(conv4_2)
        pool4 =self.pool4(conv4_3)
        
        conv5_1 = self.conv5_1(pool4)
        conv5_2 = self.conv5_2(conv5_1)
        conv5_3 = self.conv5_3(conv5_2)
        pool5 =self.pool5(conv5_3)

        flatten = self.flatten(pool5)
        d1 = self.d1(flatten)
        d2 = self.d2(d1)
        d3 = self.d3(d2)
        output = self.out(d3)
        return output





data = load_data()

model = ConvModel()

x_train = data[0]
x_valid = data[1]
y_train = data[2]
y_valid = data[3]

# Peut etre a retirer next
images, rotations = get_data(32,x_train,y_train)
images_valid, rotations_valid = get_data(32,x_valid,y_valid)

# conversion des images de float 64 en 32 car con2d veut du 32
images = images.astype(np.float32)
# conversion des images de float 64 en 32 car con2d veut du 32
images_valid = images_valid.astype(np.float32)
    
plt.title(rotations[10])
plt.imshow(images[10], cmap="gray")
plt.show()

images=np.array(images)
rotations = np.array(rotations)
print("rotation shape",rotations.shape)
images_valid=np.array(images_valid)
print("image before shape",images.shape)
images = np.reshape(images,(-1, 160,320,3))
images_valid = np.reshape(images_valid,(-1, 160,320,3))
print("image after shape",images.shape)

# Normalisation
print("Moyenne et ecart type des images", images.mean(), images.std())
scaler = StandardScaler()
scaled_images = scaler.fit_transform(images.reshape(-1, 160*320))
scaled_images_valid = scaler.transform(images_valid.reshape(-1, 160*320))
print("Moyenne et ecart type des images normalisé", scaled_images.mean(), scaled_images.std())
print("after normalisation",rotations.shape)
print("after normalisation",scaled_images.shape)

scaled_images = scaled_images.reshape(-1, 160,320,3)
scaled_images_valid = scaled_images_valid.reshape(-1, 160,320,3)
print("after scaled",rotations.shape)
print("after scaled",scaled_images.shape)

train_dataset = tf.data.Dataset.from_tensor_slices((scaled_images, rotations))
valid_dataset = tf.data.Dataset.from_tensor_slices((scaled_images_valid, rotations_valid))

model = ConvModel()
model.predict(scaled_images[0:1])

BATCH_SIZE = 32

#loss_object = keras.losses.binary_crossentropy()
optimizer = tf.keras.optimizers.Adam()
#track the evolution
# Loss
train_loss = metrics.Mean(name='train_loss')
valid_loss = metrics.Mean(name='valid_loss')
# Accuracy
train_accuracy = metrics.SparseCategoricalAccuracy(name='train_accuracy')
valid_accuracy = metrics.SparseCategoricalAccuracy(name='valid_accuracy')



@tf.function
def train_step(image, rotations):
    # permet de surveiller les opérations réalisé afin de calculer le gradient
    with tf.GradientTape() as tape:
        # fait une prediction
        predictions = model(image)
        #tf.reshape(rotations, [1])
        #tf.reshape(predictions, [1])
        print("after creation model rotations shape",rotations)
        print("after creation model prediction shape",predictions)
        # calcul de l'erreur en fonction de la prediction et des targets
        loss = keras.losses.mean_squared_error(rotations, predictions)
    # calcul du gradient en fonction du loss
    # trainable_variables est la lst des variable entrainable dans le model
    gradients = tape.gradient(loss, model.trainable_variables)
    # changement des poids grace aux gradient
    optimizer.apply_gradients(zip(gradients, model.trainable_variables))
    # ajout de notre loss a notre vecteur de stockage
    train_loss(loss)
    train_accuracy(rotations, predictions)

@tf.function
# vérifier notre accuracy de notre model afin d'evité l'overfitting
def valid_step(image, rotations):
    print("validstep")
    predictions = model(image)
    #tf.reshape(rotations, [1])
    #tf.reshape(predictions, [1])
    t_loss = keras.losses.mean_squared_error(rotations, predictions)
    # mets a jour les metrics
    valid_loss(t_loss)
    valid_accuracy(rotations, predictions)
        

epoch = 3
batch_size = 32
actual_batch = 0

for epoch in range(epoch):
    # Training set
    for images_batch, targets_batch in train_dataset.batch(batch_size):
        train_step(images_batch, targets_batch)
        template = '\r Batch {}/{}, Loss: {}, Accuracy: {}'
        print(template.format(actual_batch, len(rotations),
                              train_loss.result(), 
                              train_accuracy.result()*100),
                              end="")
        actual_batch += batch_size
    # Validation set
    for images_batch, targets_batch in valid_dataset.batch(batch_size):
        valid_step(images_batch, targets_batch)

    template = '\nEpoch {}, Valid Loss: {}, Valid Accuracy: {}'
    print(template.format(epoch+1,
                            valid_loss.result(), 
                            valid_accuracy.result()*100))
    valid_loss.reset_states()
    valid_accuracy.reset_states()
    train_accuracy.reset_states()
    train_loss.reset_states()


model.save("model.h5")


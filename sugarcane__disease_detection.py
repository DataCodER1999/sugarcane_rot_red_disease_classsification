# -*- coding: utf-8 -*-
"""Sugarcane _disease_detection.ipynb

Automatically generated by Colaboratory.
"""

# Mounting the google drive
from google.colab import drive
drive.mount('/content/drive')

# Here we are creating a directory in which we are storing kaggle credentials json file
!mkdir -p ~/.kaggle
!cp /content/drive/MyDrive/kaggle.json ~/.kaggle/

# Downloading data directly from kaggle
!kaggle datasets download -d alihussainkhan24/red-rot-sugarcane-disease-leaf-dataset

# Downloaded data in in zip file so we need to extract it
import zipfile
zip_ref = zipfile.ZipFile('/content/red-rot-sugarcane-disease-leaf-dataset.zip', 'r')
zip_ref.extractall('/content')
zip_ref.close()

# Importing liabraries
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten, MaxPool2D, Conv2D
from sklearn.metrics import ConfusionMatrixDisplay,confusion_matrix
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from sklearn.metrics import confusion_matrix

# Our data is not in correct folder structure to let's correct it
!mv "/content/Images/test set" "/content/test" # moving 'test set' folder to /content

!mv "/content/Images" "/content/train" # renaming Images folder to train

# renaming Healthy to healthy and Unhealthy to unhealthy in train set
!mv "/content/train/Healthy" "/content/train/healthy"

!mv "/content/train/Unhealthy" "/content/train/unhealthy"

# Defining out image shape and batch_size
input_shape = (224,224,3)
batch_size = 32

# Now we need to prepare our train, valid, test dataset variables
train = tf.keras.utils.image_dataset_from_directory('train', labels='inferred',label_mode='int'
                                                    ,class_names=None,color_mode='rgb',shuffle=True
                                                    ,batch_size=batch_size,image_size=input_shape[:2]
                                                    ,validation_split=0.3, interpolation='bilinear'
                                                    ,subset='training',seed=42)

valid = tf.keras.utils.image_dataset_from_directory('train', labels='inferred',label_mode='int'
                                                    ,class_names=None,color_mode='rgb',shuffle=True
                                                    ,batch_size=batch_size,image_size=input_shape[:2]
                                                    ,validation_split=0.3, interpolation='bilinear'
                                                    ,subset='validation',seed=42)

test = tf.keras.utils.image_dataset_from_directory('test', labels='inferred',label_mode='int'
                                                    ,class_names=None,color_mode='rgb',shuffle=True
                                                    ,batch_size=batch_size,image_size=input_shape[:2]
                                                    ,validation_split=0.0, interpolation='bilinear'
                                                    ,seed=42)

# Getting soe basic info about our dataset
print("Total images in training set : ",(train.cardinality()*32).numpy())
print("Total images in validation set : ",(valid.cardinality()*32).numpy())
print("Total images in testing set : ",(test.cardinality()*32).numpy())

# Checking shape of out images
for train_images,train_labels in train.take(1):break
for valid_images,valid_labels in valid.take(1):break
for test_images,test_labels in test.take(1):break

print("Shape of images in train set : ",train_images.shape)
print("Shape of images in valid set : ",valid_images.shape)
print("Shape of images in test set : ",test_images.shape)

# Defining out class names
class_names = ['healthy','unhealthy','unhealthy']

# Setting up figure size
plt.figure(figsize=(15,6))

# Plotting images of data
for index in range(9):
  plt.subplot(3,3,index+1)
  plt.imshow(train_images[index].numpy().astype('uint8'))
  plt.axis('off')
  plt.title(class_names[train_labels[index]])
  # plt.show()

# Now we need to perform augmetation to our data
random_flip = tf.keras.layers.RandomFlip('horizontal_and_vertical')
random_zoom = tf.keras.layers.RandomZoom(height_factor=0.1, width_factor=0.1)
random_rotate = tf.keras.layers.RandomRotation(0.3)
random_brightness = tf.keras.layers.RandomBrightness(0.3,value_range=(0.0,255.0))

augmentations = [random_flip, random_zoom, random_rotate, random_brightness]

# Applying augmentation on training data
for augmentation in augmentations:
  train = train.map(lambda images,labels:(augmentation(images),labels))

# Setting up figure size
plt.figure(figsize=(15,6))

# Plotting images of data after augmentation
for index in range(9):
  plt.subplot(3,3,index+1)
  plt.imshow(train_images[index].numpy().astype('uint8'))
  plt.axis('off')
  plt.title(class_names[train_labels[index]])
  # plt.show()

# Importing out VGG16 model
base_model = tf.keras.applications.VGG16(include_top=False,weights='imagenet',input_shape=input_shape)

# Here we are freezing our model our base_model
base_model.trainable = False

# Getting a quick summary of our model so far
base_model.summary(line_length=120,positions=None,print_fn=None,expand_nested=True,show_trainable=True,layer_range=None)

# We need to define a VGGPreprocessing class so that we can apply
class VGG16Preprocessing(tf.keras.layers.Layer):

  def call(self,inputs):

    '''
    This function receives images as input and returns processed images by scaling images
    '''
    return tf.keras.applications.vgg16.preprocess_input(inputs)

# Defining our sequential model and building it by adding base_model to it and then adding layers of Dense Map
model = Sequential()
model.add(VGG16Preprocessing())
model.add(base_model)
model.add(Flatten())
model.add(Dense(1024))
model.add(tf.keras.layers.Dropout(0.3))
model.add(Dense(3,activation='softmax'))

model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.0001),
              loss=tf.keras.losses.SparseCategoricalCrossentropy()
              ,metrics=tf.keras.metrics.SparseCategoricalAccuracy())

Early_stopping = EarlyStopping(monitor='val_loss'
                              ,patience=10
                              ,restore_best_weights=True,
                               verbose='auto')

Model_check_point = ModelCheckpoint(filepath='/content/drive/MyDrive/Sugarcane_red_rot_classification_project'
                                   ,monitor='val_loss'
                                   ,save_best_only=True)

history = model.fit(train,verbose='auto',
          epochs=10,
          callbacks=[Early_stopping, Model_check_point],
          validation_split=0, validation_data=valid
          ,shuffle=True,)

# plotting model
tf.keras.utils.plot_model(model,to_file='model.png',show_shapes=True,show_dtype=False,show_layer_names=True,rankdir='TB',
                          expand_nested=False,dpi=96,layer_range=None,show_layer_activations=False)

history.history

# Plotting our model's accuracy and loss
plt.figure(figsize=(15,4))

plt.subplot(1,2,1)
plt.plot(history.history['loss'],label='loss')
plt.plot(history.history['val_loss'],label='val_loss')
plt.title('loss vs val_loss')
plt.grid()
plt.legend()

plt.subplot(1,2,2)
plt.plot(history.history['sparse_categorical_accuracy'],label='sparse_categorical_accuracy')
plt.plot(history.history['val_sparse_categorical_accuracy'],label='val_sparse_categorical_accuracy')
plt.title('sparse_categorical_accuracy vs cal_sparse_categorical_accuracy')
plt.grid()
plt.legend()

# Now it's time to evaluate our model
loss,accuracy = model.evaluate(test)

# Displaying loss and accuracy on test data
print("Loss on test data : ",round(loss,2))
print("Accuracy on test data : ",str(round(accuracy*100,2))+" %")

# Calculating Predictions
y_pred = model.predict(test)
y_pred = np.argmax(y_pred,axis=1)
print(y_pred)

# Here we are taking out our labels from test set
y_labels=list()
for images,labels in test.as_numpy_iterator():y_labels.extend(labels)

confusionMatrix = tf.math.confusion_matrix(y_labels,y_labels)
print("Confusion Matrix")
print("*"*50)
print(confusionMatrix.numpy())

# plotting confusion matrix
plt.figure(figsize=(5,5))
sns.heatmap(data=confusionMatrix,annot=True,fmt='',linewidths=1,linecolor='white',cbar=False,cmap='Blues')
plt.xlabel('class labels'),plt.ylabel('class labels'),plt.title('Confusion Matrix')
plt.show()

# Plotting Predictions
plt.figure(figsize=(15,15))
for images,labels in test.take(1):break
for index in range(9):
  plt.subplot(3,3,index+1)
  plt.imshow(images[index].numpy().astype('uint8'))
  plt.axis('off')
  plt.title('Original:' + class_names[labels[index]] + ' Predicted:' + class_names[y_pred[index]])


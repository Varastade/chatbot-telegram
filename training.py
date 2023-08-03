import random
import json
import pickle
import numpy as np
import nltk
from nltk.stem import WordNetLemmatizer

from tensorflow import keras
import tensorflow as tf
from sklearn.model_selection import train_test_split

if __name__ == "__main__":

    lemmatizer = WordNetLemmatizer()

    intents = json.loads(open("intents.json").read())

    words = []
    classes = []
    documents = []
    ignored_letters = ["?","!",".",","]

    for intent in intents['intents']:
        for pattern in intent['patterns']:
            word_list = nltk.word_tokenize(pattern)
            words.extend(word_list)
            documents.append((word_list,intent['tag']))
            if intent['tag'] not in classes:
                classes.append(intent['tag'])


    words = sorted(set(words))

    classes = sorted(set(classes))

    pickle.dump(words,open('words.pkl', 'wb'))
    pickle.dump(classes,open('classes.pkl', 'wb'))

    training = []
    output_empty = [0] *len(classes)

    for document in documents:
        bag = []
        word_patterns = document[0]
        
        for word in words:
            bag.append(1) if word in word_patterns else bag.append(0)

        output_row = list(output_empty)
        output_row[classes.index(document[1])] = 1
        training.append([bag,output_row])

    random.shuffle(training)
    training = np.array(training)

    train_x = list(training[:,0])
    train_y = list(training[:,1])

    train_words,test_words,train_classes,test_classes = train_test_split(train_x,train_y,test_size=0.1,random_state=0)

    model = keras.Sequential()
    model.add(keras.layers.Dense(64,input_shape = (len(train_x[0]),), activation ='relu'))
    model.add(keras.layers.Dropout(0.5))
    model.add(keras.layers.Dense(32,activation='relu'))
    model.add(keras.layers.Dropout(0.5))
    model.add(keras.layers.Dense(len(train_y[0]),activation='softmax'))

    sgd = tf.keras.optimizers.SGD(momentum = 0.9, nesterov =True, learning_rate=0.01)

    model.compile(loss = 'categorical_crossentropy', optimizer=sgd, metrics=['accuracy'])

    hist = model.fit(train_words,train_classes,validation_data=(test_words,test_classes), epochs=100,batch_size=16, verbose=1)

    model.save('chatbotmodel.h5',hist)

    print("Done")
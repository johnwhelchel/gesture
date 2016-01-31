import numpy as np
import os
import pathlib

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import LinearSVC
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.multiclass import OneVsRestClassifier

import myopython.myo as libmyo

from gesturereader import GestureReader

WORDS = ["father_open", "father_closed"]
BASE_DIR = os.getcwd()
TRAINING_DIR = os.path.join(BASE_DIR, "training/John")
TESTING_DIR = os.path.join(BASE_DIR, "testing/John")
VERBOSE = False

def V(text, override = False):
    if VERBOSE or override:
        print(text + '\n') 

class GestureLearner(object):
    def __init__(self, words):
        super(GestureLearner, self).__init__()
        self.words = words
        self.classifier = None

    def classify(self, testData):
        testDataNp = np.array(testData)
        return self.classifier.predict(testData)

    def train(self):
        V("Training...")
        X_train = []
        y_train = []
        for word in self.words:
            V("Reading in training data for word " + word)
            expectedWordEnumVal = self.words.index(word)
            count = 2 #TODO FIX THIS SUCKS
            fileExists = True
            while(fileExists):    
                filename = word + str(count)
                filelocation = os.path.join(TRAINING_DIR, filename)
                filep = pathlib.Path(filelocation)
                if filep.exists():
                    V("Read file " + str(count))
                    # multilabel code
                    #y_train.append([1 if self.words[x] == word else 0 for x in range(len(self.words)))
                    y_train.append(expectedWordEnumVal)
                    with open(filelocation, mode='r') as f:
                        data = f.read()
                        X_train.append(data)
                    count += 1
                else:
                    V("No more files found for word " + word)
                    fileExists = False

        X_train_numpy = np.array(X_train)

        self.classifier = Pipeline([
            ('vectorizer', CountVectorizer()),
            ('tfidf', TfidfTransformer()),
            ('clf', OneVsRestClassifier(LinearSVC()))])

        self.classifier.fit(X_train_numpy, y_train)

        V("Training complete.")
       


if __name__ == '__main__':

    V("Running default word list " + str(WORDS))
    gestureLearner = GestureLearner(WORDS)
    gestureLearner.train()
    V("Building model...")
    X_test = []
    y_test_expected = []
    for filename in os.listdir(TESTING_DIR):
        with open(os.path.join(TESTING_DIR, filename), mode='r') as f:
            X_test.append(f.read())
            y_test_expected.append(WORDS.index("".join([i for i in filename if not i.isdigit()])))
    V("Model built...")

    # V("Validating and testing model")
    # predicted = gestureLearner.classify(X_test)
    # for idx, (item, classification) in enumerate(zip(y_test_expected, predicted)):
    #     print(str(WORDS[item]) + ' (actual) ' + str(WORDS[classification]) + ' (predicted)')

    V("Preparing to interpret gestures")
    with GestureReader() as gestureReader:
        while(True):
            # blocking
            gestureData = gestureReader.readGesture()
            if (gestureData):
                classifiedGesture = gestureLearner.classify(gestureData.as_classification_list())
                print("You signed the word " + WORDS[classifiedGesture])
                print("Trying to read gesture...")




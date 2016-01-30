import numpy as np
import os
import pathlib

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import LinearSVC
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.multiclass import OneVsRestClassifier

import myo as libmyo

WORDS = ["father", "sorry"]
BASE_DIR = os.getcwd()
TRAINING_DIR = os.path.join(BASE_DIR, "training")
TESTING_DIR = os.path.join(BASE_DIR, "testing")
VERBOSE = True

def V(text):
    if VERBOSE:
        print(text + '\n') 

class GestureReader(object):
    """docstring for GestureReader"""
    def __init__(self, arg):
        super(GestureReader, self).__init__()
        self.arg = arg

    def 
        

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
            count = 0
            fileExists = True
            while(fileExists):    
                filename = word + str(count)
                filelocation = os.path.join(TRAINING_DIR, filename)
                filep = pathlib.Path(filelocation)
                if filep.exists():
                    V("Read file " + str(count))
                    #y_train.append([1 if self.words[x] == word else 0 for x in range(len(self.words))) multilabel
                    y_train.append(expectedWordEnumVal)
                    with open(filelocation, mode='r') as f:
                        X_train.append(f.read())
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

    X_test = []
    y_test_expected = []
    for filename in os.listdir(TESTING_DIR):
        with open(os.path.join(TESTING_DIR, filename), mode='r') as f:
            X_test.append(f.read())
            y_test_expected.append(WORDS.index("".join([i for i in filename if not i.isdigit()])))

    predicted = gestureLearner.classify(X_test)
    for idx, (item, classification) in enumerate(zip(y_test_expected, predicted)):
        print(str(WORDS[item]) + ' (actual) ' + X_test[idx] + str(WORDS[classification]) + ' (predicted)')




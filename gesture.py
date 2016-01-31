import numpy as np
import os
import pathlib

from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import LinearSVC, SVC
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.multiclass import OneVsRestClassifier, OneVsOneClassifier

import myopython.myo as libmyo

from gesturereader import GestureReader

WORDS = ["I|my", "thankyou", "mom"]
BASE_DIR = os.getcwd()
TRAINING_DIR = os.path.join(BASE_DIR, "training/FINALCOUNTDOWN/")
TESTING_DIR = os.path.join(BASE_DIR, "testing/John/")
VERBOSE = True
INTERPRET = True
TEST = False

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
        word = ""
        V("Training dir is " + TRAINING_DIR)
        for dir in os.listdir(TRAINING_DIR):
            word2 = "".join([i for i in dir if not i.isdigit()])
            if word2 != word:
                V("Reading in training data for word: " + word2)
            word = word2
            expectedWordEnumVal = self.words.index(word)
            # multilabel code
            #y_train.append([1 if self.words[x] == word else 0 for x in range(len(self.words)))
            y_train.append(expectedWordEnumVal)
            with open(os.path.join(TRAINING_DIR, dir), mode='r') as f:
                data = f.read()
                X_train.append(data)
        V("No more training files")

        X_train_numpy = np.array(X_train)

        self.classifier = Pipeline([
            ('vectorizer', CountVectorizer()),
            ('tfidf', TfidfTransformer()),
            ('clf', OneVsOneClassifier(SVC(C=200.0, class_weight='balanced')))])

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
            data = f.read()
            #print(data)
            X_test.append(data)
            y_test_expected.append(WORDS.index("".join([i for i in filename if not i.isdigit()])))
    V("Model built...")

    if TEST:
        V("Validating and testing model")
        predicted = gestureLearner.classify(X_test)
        for idx, (item, classification) in enumerate(zip(y_test_expected, predicted)):
            print(str(WORDS[item]) + ' (actual) ' + str(WORDS[classification]) + ' (predicted)')

    if INTERPRET:
        V("Preparing to interpret gestures")
        with GestureReader() as gestureReader:
            gesturecount = 0
            while(True):
                # blocking
                gestureData = gestureReader.readGesture()
                if gestureData:
                    #print(gestureData.as_classification_list())
                    classifiedGesture = gestureLearner.classify([gestureData.as_classification_list()])
                    print(classifiedGesture)
                    print(gesturecount, " You signed the word " + WORDS[classifiedGesture])
                    print("Waiting to read gesture...")
                    gesturecount+=1 




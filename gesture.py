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

from gesturelistener import GestureListener

WORDS = ["father", "sorry"]
BASE_DIR = os.getcwd()
TRAINING_DIR = os.path.join(BASE_DIR, "training/Eric")
TESTING_DIR = os.path.join(BASE_DIR, "testing/Eric")
VERBOSE = True
DEFAULT_MYO_PATH = os.path.join(BASE_DIR, "sdk")

def V(text, override = False):
    if VERBOSE or override:
        print(text + '\n') 

        

class GestureReader(object):
    """
    An object for chuncking and reading gestures from the myo armband.
    Ideally, this would run in a thread. Instead, to get useful results,
    call the readGesture method repeatedly, and the class will chuck gestures
    for you. If you call it slowly, it won't do very much for you...

    Takes optional parameters
        myoPath -> a string pointing to the myo SDK
        gestureTimeCutoff -> an integer representing the time required to divide 
            gestures by stillness in units of .05 seconds. Defaults to 40 (2 seconds)
        gestureDistanceCutoff -> an integer representing the maximum distance that
            constitutes a new gesture in terms of squared unit myo quarternions # TODO calibrate

    """
    def __init__(self, myoPath=None, gestureTimeCutoff=40, gestureDistanceCutoff=30):
        super(GestureReader, self).__init__()
        libmyo.init(myoPath if myoPath is not None else DEFAULT_MYO_PATH)
        self.gestureBuffer = []
        self.timeCutoff = gestureTimeCutoff
        self.distanceCutoff = gestureDistanceCutoff
        self.listener = libmyo.DeviceListener()

    def __enter__(self):
        self.hub = libmyo.Hub()
        self.hub.set_locking_policy(libmyo.LockPolicy.none)

    def __exit__(self, type, value, traceback):
        self.hub.shutdown()

    def readGesture(self):
        hub.run(1000/20, self.listener) # 20 times per second (1000 ms)
        

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
            count = 1
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

    V("Validating and testing model")
    predicted = gestureLearner.classify(X_test)
    for idx, (item, classification) in enumerate(zip(y_test_expected, predicted)):
        print(str(WORDS[item]) + ' (actual) ' + str(WORDS[classification]) + ' (predicted)')

    V("Preparing to interpret gestures")
    reader = GestureReader();
    with gestureReader as reader:
        while(True):
            gestureData = gestureReader.readGesture()
            if (gestureData):
                classifiedGesture = gestureLearner.classify(gestureData)
                print("You signed the word " + WORDS[classifiedGesture])




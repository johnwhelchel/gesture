import numpy as np
import os
import pathlib
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.svm import LinearSVC
from sklearn.preprocessing import MultiLabelBinarizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.multiclass import OneVsRestClassifier

WORDS = ["father", "sorry"]
BASE_DIR = os.getcwd()
TRAINING_DIR = os.path.join(os.path.join(BASE_DIR, ".."), "training")
TESTING_DIR = os.path.join(os.path.join(BASE_DIR, ".."), "testing")
VERBOSE = True

def V(text):
    if VERBOSE:
        print(text + '\n') 

X_train = []
y_train = []
for word in WORDS:
    V("Reading in training data for word " + word)
    count = 0
    filename = word + count
    filelocation = os.path.join(TRAINING_DIR, filename)
    filep = pathlib.Path(filelocation)
    if filep.exists():
        V("Read file " + str(count))
        y_train.push([1 if WORDS[x] == word else 0 for x in range(len(WORDS)))
        with open(filelocation, mode='r') as f:
            X_train.push(f.read())
        count += 1
    else:
        V("No more files found for word " + word)

X_train_numpy = np.array(X_train)

X_test = []
for filename in os.listdir(TESTING_DIR):
    with open(filename, mode='r') as f:
        X_test.push(f.read())

X_test_numpy = np.array(X_test)

classifier = Pipeline([
    ('vectorizer', CountVectorizer()),
    ('tfidf', TfidfTransformer()),
    ('clf', OneVsRestClassifier(LinearSVC()))])
classifier.fit(X_train_numpy, y_train)
predicted = classifier.predict(X_test_numpy)
for item, labels in zip(X_test, predicted):
    print(str(item) + ' => ' + ', '.join(WORDS[ind] for ind, x in enumerate(labels) if x == 1))
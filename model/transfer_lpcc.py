# LPCC based Transfer Learning

import os

from keras.models import Model

import numpy as np

from sklearn.metrics import accuracy_score
from sklearn import svm
from sklearn.model_selection import train_test_split

from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.model_selection import GridSearchCV

from model_lpcc import *
from utils import *

n_lpcc = 49 # '(n_lpcc + 1)' must be divisible by 5.
window_size = 10
audio_len = 30
audio_len_nn = 600
data_dir = os.path.join('..', 'audio-train-transfer')
n_samples = 120
lpcc_shape = (10, (n_lpcc + 1) / 5, 1)

def learn_nn_features(model, X):
    X_SVM = []
    for sample in range(len(X)):
        x_exp = np.expand_dims(X[sample], axis = 0)
        transfer_features = model.predict(x_exp)
        X_SVM.append(transfer_features)
        return X_SVM

def grid_search(X, y):
    C_range = np.logspace(-2, 10, 13)
    gamma_range = np.logspace(-9, 3, 13)
    param_grid = dict(gamma = gamma_range, C = C_range)
    cv = StratifiedShuffleSplit(n_splits=5, test_size=0.25, random_state = 64)
    grid = GridSearchCV(svm.SVC(kernel='linear', class_weight='balanced'), \
                        param_grid=param_grid, cv=cv)
    grid.fit(X, y)
    print("The best parameters are %s with a score of %0.2f"
          % (grid.best_params_, grid.best_score_))

def main():
    print("Running preprocess")
    run_preprocess_lpcc(data_dir, str(audio_len), str(window_size), \
                        n_lpcc, transfer = True)

    # Build the CNN
    print("Building the model..")
    model = build_model_lpcc(lpcc_shape, n_lpcc + 1, n_samples)

    # Load saved neural network weights.
    model.load_weights(os.path.join('..', 'neural-net-weights', \
                                    'lpcc_model_weights_' + str(n_lpcc) + '_' + \
                                        str(audio_len_nn) + '_' + str(window_size) + '.h5'))

    # Get the output layer (Flatten layer).
    transfer_model = Model(inputs = model.input, outputs = model.get_layer('flatten_1').output)

    # Load saved LPCC coefficients from npy files
    print("Loading LPCC features")
    X, y = load_features_lpcc(data_dir, str(audio_len), str(window_size), n_lpcc)

    # Reshape X to add 4th dimension
    X = X.reshape(X.shape[0], 10, -1, 1)

    # Read Flatten layer features from trained neural network.
    X_SVM = learn_nn_features(transfer_model, X)
    y_enc = encode(y)

    # Split into test data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42)
    X_train_SVM = np.array(X_train).reshape(len(X_train), -1)

    # Build a linear SVM model
    model_SVM = svm.SVC(kernel='linear', class_weight='balanced')

    # Train the model
    print("Training the SVM..")
    model_SVM.fit(X_train_SVM, y_train)

    # Predict the output
    X_test = np.array(X_test).reshape(len(X_test), -1)
    pred_acc = accuracy_score(y_test, model_SVM.predict(X_test))

    print("SVM Accuracy:", pred_acc)
    print("Successfully completed.")

if __name__ == "__main__":
    main()


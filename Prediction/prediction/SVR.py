"""
Functions to do prediction with Support Vector Regression.
"""


__author__ = 'Erik Aumayr'


import pandas as pd
import numpy as np
from sklearn.svm import SVR
from sklearn.svm import LinearSVR
from sklearn.svm import NuSVR
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, explained_variance_score
from sklearn.model_selection import cross_val_score
import warnings
from sklearn.exceptions import ConvergenceWarning


def svr(dataframe, kernel='linear', target=None, drop_features=[], split=0.2, cross_val=False):

    # Remove non-numerical and undesired features from dataframe
    dataframe = dataframe.loc[:, dataframe.dtypes != 'object']
    dataframe = dataframe.drop(drop_features, axis=1)

    # Transform data into columns and define target variable
    numerical_features = dataframe.loc[:, dataframe.columns != target]
    X = np.nan_to_num(numerical_features.to_numpy())  # .reshape(numerical_features.shape)
    y = np.nan_to_num(dataframe[target].to_numpy())  # .reshape(dataframe[target].shape[0], 1)

    # Split the data into training/testing sets
    testsplit = round(split * X.shape[0])
    X_train = X[:-testsplit]
    X_test = X[-testsplit:]
    y_train = y[:-testsplit]
    y_test = y[-testsplit:]

    # Train linear regression model
    reg = SVR(kernel=kernel, C=1.0, epsilon=0.2)
    reg.fit(X_train, y_train)
    if kernel == 'linear':
        feature_importance = pd.Series(reg.coef_[0], index=numerical_features.columns)  # only with linear kernel
    else:
        feature_importance = pd.Series()

    # Prediction with trained model
    y_pred = reg.predict(X_test)

    results = pd.Series()
    if not cross_val:
        results['Train mean'] = np.mean(y_train)
        results['Train std'] = np.std(y_train)
        results['Test mean'] = np.mean(y_test)
        results['Test std'] = np.std(y_test)
        results['Prediction mean'] = np.mean(y_pred)
        results['Prediction std'] = np.std(y_pred)
        results['Mean Squared Error'] = mean_squared_error(y_test, y_pred)
        results['Mean Absolute Error'] = mean_absolute_error(y_test, y_pred)
        results['R2 score'] = r2_score(y_test, y_pred)
        results['Explained variance score'] = explained_variance_score(y_test, y_pred)
    else:
        results['Cross-val R2 score (mean)'] = np.mean(cross_val_score(reg, X, y, cv=10, scoring="r2"))
        results['Cross-val R2 scores'] = cross_val_score(reg, X, y, cv=10, scoring="r2")
        results['Cross-val explained_variance score (mean)'] = np.mean(cross_val_score(reg, X, y, cv=10, scoring="explained_variance"))
        results['Cross-val explained_variance scores'] = cross_val_score(reg, X, y, cv=10, scoring="explained_variance")

    y_result = pd.DataFrame({'y_test': y_test, 'y_pred': y_pred})
    return feature_importance, results, y_result, reg


def linear_svr(dataframe, target=None, drop_features=[], without_outliers=False, split=0.2):
    warnings.filterwarnings("ignore", category=ConvergenceWarning, message="^Liblinear failed to converge")

    # Remove non-numerical and undesired features from dataframe
    dataframe = dataframe.loc[:, dataframe.dtypes != 'object']
    dataframe = dataframe.drop(drop_features, axis=1)

    # Transform data into columns and define target variable
    numerical_features = dataframe.loc[:, dataframe.columns != target]
    X = np.nan_to_num(numerical_features.to_numpy())  # .reshape(numerical_features.shape)
    y = np.nan_to_num(dataframe[target].to_numpy())  # .reshape(dataframe[target].shape[0], 1)

    # Split the data into training/testing sets
    testsplit = round(split * X.shape[0])
    X_train = X[:-testsplit]
    X_test = X[-testsplit:]
    y_train = y[:-testsplit]
    y_test = y[-testsplit:]

    # Train linear regression model
    reg = LinearSVR(random_state=0, tol=1e-5)
    reg.fit(X_train, y_train)
    feature_importance = pd.Series(reg.coef_[0], index=numerical_features.columns)  # only with linear kernel

    # Prediction with trained model
    y_pred = reg.predict(X_test)

    results = pd.DataFrame()
    results['Train mean'] = np.mean(y_train)
    results['Train std'] = np.std(y_train)
    results['Test mean'] = np.mean(y_test)
    results['Test std'] = np.std(y_test)
    results['Prediction mean'] = np.mean(y_pred)
    results['Prediction std'] = np.std(y_pred)
    results['Mean Squared Error'] = mean_squared_error(y_test, y_pred)
    results['Mean Absolute Error'] = mean_absolute_error(y_test, y_pred)
    results['R2 score'] = r2_score(y_test, y_pred)
    results['Explained variance score'] = explained_variance_score(y_test, y_pred)
    results['Cross-val R2 score (mean)'] = np.mean(cross_val_score(reg, X, y, cv=10, scoring="r2"))
    results['Cross-val R2 scores'] = cross_val_score(reg, X, y, cv=10, scoring="r2")
    results['Cross-val explained_variance score (mean)'] = np.mean(cross_val_score(reg, X, y, cv=10, scoring="explained_variance"))
    results['Cross-val explained_variance scores'] = cross_val_score(reg, X, y, cv=10, scoring="explained_variance")

    y_result = pd.DataFrame({'y_test': y_test, 'y_pred': y_pred})
    return feature_importance, results, y_result, reg


def nu_svr(dataframe, kernel='linear', target=None, drop_features=[], without_outliers=False, split=0.2):

    # Remove non-numerical and undesired features from dataframe
    dataframe = dataframe.loc[:, dataframe.dtypes != 'object']
    dataframe = dataframe.drop(drop_features, axis=1)

    # Transform data into columns and define target variable
    numerical_features = dataframe.loc[:, dataframe.columns != target]
    X = np.nan_to_num(numerical_features.to_numpy())  # .reshape(numerical_features.shape)
    y = np.nan_to_num(dataframe[target].to_numpy())  # .reshape(dataframe[target].shape[0], 1)

    # Split the data into training/testing sets
    testsplit = round(split * X.shape[0])
    X_train = X[:-testsplit]
    X_test = X[-testsplit:]
    y_train = y[:-testsplit]
    y_test = y[-testsplit:]

    # Train linear regression model
    reg = NuSVR(kernel=kernel, C=1.0, nu=0.1)
    reg.fit(X_train, y_train)
    if kernel == 'linear':
        feature_importance = pd.Series(reg.coef_[0], index=numerical_features.columns)  # only with linear kernel
    else:
        feature_importance = pd.Series()

    # Prediction with trained model
    y_pred = reg.predict(X_test)

    results = pd.Series()
    results['Train mean'] = np.mean(y_train)
    results['Train std'] = np.std(y_train)
    results['Test mean'] = np.mean(y_test)
    results['Test std'] = np.std(y_test)
    results['Prediction mean'] = np.mean(y_pred)
    results['Prediction std'] = np.std(y_pred)
    results['Mean Squared Error'] = mean_squared_error(y_test, y_pred)
    results['Mean Absolute Error'] = mean_absolute_error(y_test, y_pred)
    results['R2 score'] = r2_score(y_test, y_pred)
    results['Explained variance score'] = explained_variance_score(y_test, y_pred)
    results['Cross-val R2 score (mean)'] = np.mean(cross_val_score(reg, X, y, cv=10, scoring="r2"))
    results['Cross-val R2 scores'] = cross_val_score(reg, X, y, cv=10, scoring="r2")
    results['Cross-val explained_variance score (mean)'] = np.mean(cross_val_score(reg, X, y, cv=10, scoring="explained_variance"))
    results['Cross-val explained_variance scores'] = cross_val_score(reg, X, y, cv=10, scoring="explained_variance")

    y_result = pd.DataFrame({'y_test': y_test, 'y_pred': y_pred})
    return feature_importance, results, y_result, reg

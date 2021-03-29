"""
Functions to do regression analysis.
"""


__author__ = 'Erik Aumayr'


import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error, explained_variance_score
from sklearn.model_selection import cross_val_score


"""
Computing linear regression
"""


def linear_regression(dataframe, target=None, drop_features=[], split=0.2, normalize=False, cross_val=False):

    # Remove non-numerical and undesired features from dataframe
    dataframe = dataframe.loc[:, dataframe.dtypes != 'object']
    dataframe = dataframe.drop(drop_features, axis=1)

    # Transform data into columns and define target variable
    numerical_features = dataframe.loc[:, dataframe.columns != target]
    X = np.nan_to_num(numerical_features.to_numpy().reshape(numerical_features.shape))
    y = np.nan_to_num(dataframe[target].to_numpy().reshape(dataframe[target].shape[0], 1))

    # Split the data into training/testing sets
    testsplit = round(split * X.shape[0])
    X_train = X[:-testsplit]
    X_test = X[-testsplit:]
    y_train = y[:-testsplit]
    y_test = y[-testsplit:]

    # Train linear regression model
    reg = LinearRegression(copy_X=True, fit_intercept=True, n_jobs=None, normalize=normalize)
    reg.fit(X_train, y_train)
    coefficients = pd.Series(reg.coef_[0], index=numerical_features.columns)
    coefficients['intercept'] = reg.intercept_[0]

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

    y_result = pd.DataFrame(np.concatenate((y_test, y_pred), axis=1), columns=['y_test', 'y_pred'])
    return coefficients, results, y_result, reg


if __name__ == '__main__':
    series1 = pd.DataFrame({
        'a': [1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2],
        'b': [1, 3, 2, 5, 4, 0, 6, 8, 7, 1e+32, 4, 5],
        'time': [12, 15, 18, 20, 22, 25, 28, 30, 33, 36, 38, 40]})
    series2 = pd.DataFrame({
        'a': [1, 3, 3, 2, 5, 7, 8, 9, 0, 6, 9, 7],
        'b': [2, 4, 2, 1, 5, 0, 9, 8, 7, 6, 7, 3],
        'time': [13, 15, 17, 20, 23, 25, 27, 30, 32, 35, 38, 40]})
    baseline = pd.DataFrame({
        'a': [1, 3, 2, 5, 4, 7, 8, 7, 9, 6, 5, 8],
        'b': [1, 2, 2, 3, 4, 8, 8, 7, 6, 9, 3, 7],
        'time': [33, 36, 38, 41, 43, 46, 49, 51, 53, 55, 58, 60]})

    print(linear_regression(series1, target='b', without_outliers=False))

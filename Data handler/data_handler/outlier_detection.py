"""
Detects and Remove outliers in a DataFrame

Three different cases available:

0: Z-score based outlier detection
1: Median Absolute Deviation (MAD)-score based outlier detection

Input: dataframe,
       mode(default=0)

Output: dataframe with a boolean column indicating if the values is either outlier or not
        dataframe composed of its outliers, index maintained
"""

__author__ = 'Erik Aumayr, SRL'

import pandas as pd


def detect(data, mode=0):

    if mode == 0:
        zscores = abs(data.select_dtypes(exclude=object) - data.mean()) / data.std()
        data['outliers'] = zscores[zscores > 3].any(axis=1)

    elif mode == 1:
        distance = abs(data - data.median())
        MAD = distance.median()
        zscores_MAD = 0.6745 * distance / MAD
        data['outliers'] = zscores_MAD[zscores_MAD > 3.5].any(axis=1)

    else:
        print(
            f'{mode} not valid. Choose 0 for Z-score and 1 for MAD based outlier detection.')
    return data


def remove(data, mode=0):
    if mode in (0, 1):
        data = detect(data, mode)
        data = data[~data['outliers']].drop('outliers', 1)
    else:
        print(
            f'{mode} not valid. Available options are: 0 for Z-score and 1 for MAD-score')
    return data


# Test input
if __name__ == '__main__':
    df = pd.DataFrame({
        'a': [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1000],
        'b': [1, 2, 3, 4, 5, 4, 3, 2, 1, 2, 3, 4, 5, 4, 3, 2, 1, 2, 3, 4]
    })
    print(detect(df, 0))

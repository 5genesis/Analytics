"""
Functions to calculate the correlation between fields and measurements. Only float and integer fields are considered.
"""


__author__ = 'Erik Aumayr'


import pandas as pd


"""
Computing the correlation between all fields of one experiment across different measurements.
"""
def correlate_fields(series, method='pearson'):
    return series.corr(method=method)


"""
Computing the correlation between two experiments that have the same measurements and fields.
"""
def correlate_experiments(series_dict, method='pearson', time_tag='time', max_lag=1e+9):
    return series_dict[list(series_dict.keys())[0]].corrwith(series_dict[list(series_dict.keys())[1]])


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
    combined_series_1_2 = pd.DataFrame({
        'a [series1]': [1, 2, 3, 4, 5, 6, 7, 8, 9, 0, 1, 2],
        'a [series2]': [1, 3, 3, 2, 5, 7, 8, 9, 0, 6, 9, 7],
        'b [series1]': [1, 3, 2, 5, 4, 0, 6, 8, 7, 1e+32, 4, 5],
        'b [series2]': [2, 4, 2, 1, 5, 0, 9, 8, 7, 6, 7, 3],
        'time [series1]': [12, 15, 18, 20, 22, 25, 28, 30, 33, 36, 38, 40],
        'time [series2]': [13, 15, 17, 20, 23, 25, 27, 30, 32, 35, 38, 40]
        })

    print( correlate_fields(combined_series_1_2, method='pearson') )
    print( correlate_experiments({'series1': series1, 'baseline': baseline}, method='pearson', time_tag='time', max_lag=1) )
    print( correlate_experiments({'series2': series2, 'baseline': baseline}, method='pearson', time_tag='time', max_lag=1) )

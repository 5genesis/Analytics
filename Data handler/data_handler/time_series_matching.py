""" Python module to match and merge (synchronise) data points from measurement time series """


__author__ = 'Erik Aumayr'


import pandas as pd


"""
Matching and merging measurement data points from different measurements that have been recorded with slightly different time values, where the maximum lag can be specified.
Input: Expects a dictionary of Pandas measurement dataframes as input, e.g. {'SMU': df1, 'Throughput Measures': df2}
Output: A Pandas data frame of matched and merged data points
Parameters:
dataframes  dictionary that contains Pandas data frames of different measurement series as specified above
max_lag     the time window in which matching data points have to lie. 1 second (1s) by default
merge       with merge=True, a merged data frame will be returned, otherwise separate dataframes will be returned
"""
def synchronize(dataframes, max_lag='1s', merge=False):
    merged_data = pd.DataFrame()
    for series_name, series in dataframes.items():
        series.index = series.index.floor(max_lag)
        dataframes[series_name] = series
        if merged_data.empty:
            merged_data = series
        else:
            # TODO: Input type is now dataframe instead of dict of dataframes
            merged_data = merged_data.merge(series, on='time')  # alternative: data.join(series.resample(max_lag).bfill(), rsuffix=f'_{series_name}')
    merged_data = merged_data[~merged_data.index.duplicated(keep='last')]
    if merge:
        return {'series': merged_data}
    else:
        for series_name, series in dataframes.items():
            dataframes[series_name] = series[series.index.isin(merged_data.index)]
        return dataframes


if __name__ == '__main__':

    # Test data
    a = [{'time': 1579768919241000000, 'data': '59.241_a'},  # 2020-01-23 08:41:59.241
        {'time': 1579768920241000000, 'data': '00.241_a'},  # 2020-01-23 08:42:00.241
        {'time': 1579768921244000000, 'data': '01.244_a'},  # 2020-01-23 08:42:01.244
        {'time': 1579768922246000000, 'data': '02.246_a'},  # 2020-01-23 08:42:02.246
        {'time': 1579768923253000000, 'data': '03.253_a'},  # 2020-01-23 08:42:03.253
        {'time': 1579768924258000000, 'data': '04.258_a'},  # 2020-01-23 08:42:04.258
        {'time': 1579768925261000000, 'data': '05.261_a'},  # 2020-01-23 08:42:05.261
        {'time': 1579768926265000000, 'data': '06.265_a'},  # 2020-01-23 08:42:06.265
        {'time': 1579768927269000000, 'data': '07.269_a'}]  # 2020-01-23 08:42:07.269
    b = [{'time': 1579768924724000000, 'data': '04.724_b'},  # 2020-01-23 08:42:04.724
        {'time': 1579768926848000000, 'data': '06.848_b'},  # 2020-01-23 08:42:06.848
        {'time': 1579768928807000000, 'data': '08.807_b'},  # 2020-01-23 08:42:08.807
        {'time': 1579768930800000000, 'data': '10.800_b'},  # 2020-01-23 08:42:10.800
        {'time': 1579768932812000000, 'data': '12.812_b'},  # 2020-01-23 08:42:12.812
        {'time': 1579768934812000000, 'data': '14.812_b'},  # 2020-01-23 08:42:14.812
        {'time': 1579768936801000000, 'data': '16.801_b'}]  # 2020-01-23 08:42:16.801
    c = [{'time': 1579768920241000000, 'data': '00.241_c'},  # 2020-01-23 08:42:00.241
        {'time': 1579768923253000000, 'data': '03.253_c'},  # 2020-01-23 08:42:03.253
        {'time': 1579768926848000000, 'data': '06.848_c'},  # 2020-01-23 08:42:06.848
        {'time': 1579768934812000000, 'data': '14.812_c'},  # 2020-01-23 08:42:14.812
        {'time': 1579768936801000000, 'data': '16.801_c'}]  #2020-01-23 08:42:16.801

    # Usage of the function parameters:
    series_a = pd.DataFrame(a).set_index('time')
    series_a.index = pd.to_datetime(series_a.index)
    series_b = pd.DataFrame(b).set_index('time')
    series_b.index = pd.to_datetime(series_b.index)
    series_c = pd.DataFrame(c).set_index('time')
    series_c.index = pd.to_datetime(series_c.index)
    print(synchronize(dataframes={'series_a': series_a, 'series_b': series_b, 'series_c': series_c}, max_lag='1s', merge=True))

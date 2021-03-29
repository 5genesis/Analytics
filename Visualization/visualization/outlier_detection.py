def detect(data, mode=0):

    if mode == 0:
        zscores = abs(data.select_dtypes(exclude=object) - data.mean()) / data.std()
        data['outliers'] = zscores[zscores > 3].any(axis=1)

    elif mode == 1:
        distance = abs(data - data.median())
        MAD = distance.median()
        zscores_MAD = 0.6745 * distance / MAD
        data['outliers'] = zscores_MAD[zscores_MAD > 4].any(axis=1)

    return data

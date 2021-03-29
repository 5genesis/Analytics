__author__ = 'SRL'


import pandas as pd
import statsmodels.api as sm
import numpy as np
from sklearn.preprocessing import StandardScaler



'''
Backward elimination
'''
def backward_elimination(df,target,drop_features=[]):

    #remove non numeric columns and undesired features from dataframe
    df=df.select_dtypes(exclude=['object'])
    const_feat=list(df.columns[df.nunique() <= 1])

    drop_features=drop_features+const_feat
    df = df.drop(drop_features, axis=1)
    df.dropna(inplace=True)

    #if target constant avoid crashing
    if target in const_feat:
        score=[0 for feat in df.columns]
        score = pd.Series(score,index = list(df.columns))

        return None, list(df.columns), score

    scaler = StandardScaler()
    scaler.fit(df)
    df[df.columns]=scaler.transform(df[df.columns])
    #
    y=df[target]
    X=df.drop(target,1)
    
    
    
    cols = list(X.columns)
    pmax = 1
    
    while (len(cols)>0):
        
        p= []
        X_1 = X[cols]
        #X_1=scaler.fit_transform(X_1)
        X_1 = sm.add_constant(X_1,has_constant='add')
        
        model = sm.OLS(y,X_1).fit()
        p = pd.Series(model.pvalues.values[1:],index = cols)      
        pmax = max(p)
        feature_with_p_max = p.idxmax()
        if(pmax>0.05):
            cols.remove(feature_with_p_max)
        else:
            break

    original_features=list(X.columns)         
    selected_features_BE = list(cols)

    score={feature:1 if feature in selected_features_BE else 0 for feature in original_features}
    coef=pd.Series(list(score.values()), index=original_features)

    return selected_features_BE,original_features,coef





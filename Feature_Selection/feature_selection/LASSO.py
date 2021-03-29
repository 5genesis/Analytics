import pandas as pd
from sklearn.preprocessing import StandardScaler
import numpy as np
from sklearn.linear_model import Lasso

def LASSO(df,target,alpha=.1,drop_features=[]):
    

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

    #scale data before using Lasso
    scaler=StandardScaler()
    
    scaler.fit(df)
    df[df.columns]=scaler.transform(df[df.columns])
    
    y=df[target]
    X=df.drop(target,1)
    
    
    #lr = LinearRegression()
    #lr.fit(X, y)
    rr = Lasso(alpha=alpha,max_iter=1e5) # higher the alpha value, more restriction on the coefficients; low alpha > more generalization, coefficients are barely
    # restricted and in this case linear and ridge regression resembles
    rr.fit(X, y)
    
    coef = pd.Series(rr.coef_, index = X.columns)
    #imp_coef = coef.sort_values()
    new_features=list(coef[coef!=0].index)
    original_features=list(X.columns)

    return new_features, original_features, coef
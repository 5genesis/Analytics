import pandas as pd
import statsmodels.api as sm
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.feature_selection import RFE



'''
RFE function to detect optimum number of features to search for
'''
def RFE_nof(df,target,normalize):
    
    y=df[target]
    X=df.drop(target,1)
    
    nof_list=np.arange(1,len(X.columns))            
    high_score=0
    #Variable to store the optimum features
    nof=0           
    score_list =[]
    
    for n in range(len(nof_list)):
        X_train, X_test, y_train, y_test = train_test_split(X,y, test_size = 0.3, random_state = 0)
        model = LinearRegression(copy_X=True, fit_intercept=True, n_jobs=None, normalize=normalize)
        rfe = RFE(model,nof_list[n])
        X_train_rfe = rfe.fit_transform(X_train,y_train)
        X_test_rfe = rfe.transform(X_test)
        model.fit(X_train_rfe,y_train)
        score = model.score(X_test_rfe,y_test)
        score_list.append(score)
        if(score>high_score):
            high_score = score
            nof = nof_list[n]
    return nof
    
    
'''
RFE Feature selector
'''
def RFE_selector(df,target,drop_features=[],normalize=False):

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

    y=df[target]
    X=df.drop(target,1)
    
    nof=RFE_nof(df,target,normalize=normalize)
    
    if nof==0:
        return None
        
    cols = list(X.columns)
    
    model = LinearRegression(copy_X=True, fit_intercept=True, n_jobs=None, normalize=normalize)#Initializing RFE model
    
    rfe = RFE(model, nof)     #Transforming data using RFE
    X_rfe = rfe.fit_transform(X,y)
    
    #Fitting the data to model
    model.fit(X_rfe,y)              
    temp = pd.Series(rfe.support_,index = cols)
    selected_features_rfe = temp[temp==True].index
    diz=dict(zip(selected_features_rfe,rfe.estimator_.coef_))
    for el in df.columns:
        if el not in selected_features_rfe:
            diz[el]=0
    score = pd.Series(list(diz.values()),index = list(diz.keys()))

    
    return list(selected_features_rfe), list(df.columns), score
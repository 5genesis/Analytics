'''
Statistical Analysis of a 5Genesis Test Case composed of several Iterations

It provides statistical indicators for each Iteration, and the final indicators (with 95% confidence interval) for the Test Case
It follows guidelines in D6.1

Data Source: InfluxDB database

'''

__author__ = 'srl'


import pandas as pd
import numpy as np
from scipy.stats import sem, t


def KPI_statistics (rawdf, it, kpi, exp_type):
    N_indicators = 9 # Mean, Sdev, Median, Min, Max, 25perc, 75perc, 5perc, 95perc (Following D6.1)

    rawdf=rawdf.dropna(subset=[kpi])

    I = len(rawdf[it].unique())

    if  I==25:
        print('******************************************\n')
        print(f'The Test Case includes {I} iterations! Statistical Analysis is performed, and results will be compliant to 5Genesis methodology')
    elif I<25:
        print('******************************************\n')
        print(f'The Test Case includes {I} iterations, less than the expected 25! Statistical Analysis is performed, but results may be not compliant to 5Genesis methodology')
    print('\n')

    df=rawdf[[kpi,it]]

    if int(exp_type)==0:

       results=pd.DataFrame(columns=['iteration','Mean','Standard Deviation','Median','Min','Max','25% Percentile','75% Percentile','5% Percentile','95% Percentile'])

       MEANS=[]
       SDEVs=[]
       MEDIANS=[]
       MINS=[]
       MAXS=[]
       P25=[]
       P75=[]
       P5=[]
       P95=[]

       for i in df[it].unique():
            MEAN=df[df[it]==i][kpi].mean()
            SDEV=df[df[it]==i][kpi].std()
            MEDIAN=df[df[it]==i][kpi].median()
            MIN=df[df[it]==i][kpi].min()
            MAX=df[df[it]==i][kpi].max()
            p25=df[df[it]==i][kpi].quantile(q=.25)
            p75=df[df[it]==i][kpi].quantile(q=.75)
            p5=df[df[it]==i][kpi].quantile(q=.05)
            p95=df[df[it]==i][kpi].quantile(q=.95)

            values=[int(i),MEAN,SDEV,MEDIAN,MIN,MAX,p25,p75,p5,p95]
            temp_series=pd.Series(values,index=results.columns)

            results=results.append(temp_series, ignore_index=True)
            MEANS.append(MEAN)
            SDEVs.append(SDEV)
            MEDIANS.append(MEDIAN)
            MINS.append(MIN)
            MAXS.append(MAX)
            P25.append(p25)
            P75.append(p75)
            P5.append(p5)
            P95.append(p95)

       results.set_index('iteration',inplace=True)
       results.index = results.index.astype(int)
        ########################## Test cases with more than one KPI sample per iteration (e.g., Throughput)

            ###test case statistics

       CI = 0.95 # Confidence Interval

        # standard errors for each indicator
       std_err = np.zeros(N_indicators)
       std_err[0] = sem(MEANS)
       std_err[1] = sem(SDEVs)
       std_err[2] = sem(MEDIANS)
       std_err[3] = sem(MINS)
       std_err[4] = sem(MAXS)
       std_err[5] = sem(P25)
       std_err[6] = sem(P75)
       std_err[7] = sem(P5)
       std_err[8] = sem(P95)
       h = std_err * t.ppf((1 + CI) / 2, I - 1) # It is evaluated on the t-distribution with I-1 degrees of freedom

       Stat=['Mean','Standard Deviation','Median','Min','Max','25% Percentile','75% Percentile','5% Percentile','95% Percentile']
       Value=[np.mean(MEANS),np.mean(SDEVs),np.mean(MEDIANS),np.mean(MINS),np.mean(MAXS),np.mean(P25),np.mean(P75),np.mean(P5),np.mean(P95)]
       CI=[item for item in h]


       results2=pd.DataFrame(([Stat[i],Value[i],CI[i]] for i in range(len(h))), columns=['Statistic','Value','Confidence Interval'])
       results2.set_index('Statistic',inplace=True)



    ########################## Test cases with one KPI sample per iteration (e.g., Service Creation Time)
    if int(exp_type)==1:

       series=df[kpi]

       MEAN = series.mean()
       SDEV = series.std()
       MEDIAN = series.median()
       MIN=series.min()
       MAX=series.max()
       p25=series.quantile(q=.25)
       p75=series.quantile(q=.75)
       p5=series.quantile(q=.05)
       p95=series.quantile(q=.95)

       stat=['Mean','Standard deviation','Median','Min','Max','25% Percentile','75% Percentile','5% Percentile','95% Percentile']

       Value=[MEAN,SDEV,MEDIAN,MIN,MAX,P25,P75,P5,P95]

       results=pd.DataFrame({'Statistic':stat,'Value':Value})

       results.set_index('Statistic',inplace=True)

       results2=None


    return results, results2


########################################################################################

# Test input
if __name__ == '__main__':


    it = "_iteration_"                  # Iteration Identifier
    kpi = "kpi1"                        # KPI Identifier
    exp_type = 0                        # 0: (default) Experiments with several KPI samples per iteration (e.g. throughput, ping) (default)
                                        # 1: Experiments with a single KPI sample per iteration (e.g. Slice /Service creation time)

    it_list=np.array(sorted(list(range(25))*10))
    values1=np.random.normal(size=250)*1000
    values2=np.random.normal(size=250)*1000

    df=pd.DataFrame({'_iteration_':it_list,'kpi1':values1,'kpi2':values2})
    # Usage in Command Line
    result=KPI_statistics(df, it, kpi, exp_type)

    print(result[0])
    print(result[1])

    #Examples of usage in command line
    # python3 Statistical_Analysis_influxdb.py 520 ADB_Ping_Agent _iteration_ "Delay (ms)" ms 0

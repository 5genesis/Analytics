
'''
Statistical Analysis of a 5Genesis Test Case composed of several Iterations

It provides statistical indicators for each Iteration (as a figure), and the final indicators (with 95% confidence interval) for the Test Case
It follows guidelines in D6.1

Data Source: TAP .csv Listener 

'''

__author__ = 'srl'

import sys
import os
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.stats import sem, t
from scipy import mean

def KPI_statistics (file, it, kpi, unit, exp_type):
    dirname = os.path.dirname(__name__)
    filename = os.path.join(dirname, file)
    N_indicators = 9 # Mean, Sdev, Median, Min, Max, 25perc, 75perc, 5perc, 95perc (Following D6.1)

    # load the dataset
    rawdf = pd.read_csv(filename)

    # How many iterations were done for the test case under analysis?
    # In this case, it is equal to...
    I = len(rawdf[it].unique())
    #print(I)

    if  I==25:
        print('******************************************\n')
        print(f'This Test Case includes {I} iterations! Statistical Analysis is performed, and results will be compliant to 5Genesis methodology (see D6.1)')
    elif I<25:
        print('******************************************\n')
        print(f'This Test Case includes {I} iterations, less than the expected 25! Statistical Analysis is performed, but results may be not compliant to 5Genesis methodology (see D6.1)')
    print('\n')

    ## NOTE: Use outliers_yes_no = 0 to be consistent with D6.1 definitions
    outliers_yes_no = 0 # set to 0 if you include the outliers, 1 if you exclude them

    # create a dataframe (putting Iterations per column) and evaluate the statistics
    # this is not optimized, but allows to reuse the following code
    df = pd.DataFrame(columns=['Iteration ' + str(m+1) for m in range(I)])
    for m in range(I):
        df.loc[:,'Iteration ' + str(m+1)] = rawdf.loc[rawdf[it]==m, kpi].reset_index(drop=True)
    #print(df.tail())

    ## Statistics per Iteration

    ########################## Test cases with more than one KPI sample per iteration (e.g., Throughput)
    if int(exp_type)==0:
        box_plot_data = [df['Iteration %d' % (m+1)].dropna() for m in range(I)]
        B=plt.boxplot(box_plot_data, notch=False, patch_artist=False, showmeans=True, showfliers=False, widths=0.8, labels=['%d' % (m+1) for m in range(I)])

        plt.ion()
        plt.title('Comparison of measurements per Iteration')
        plt.ylabel(kpi)
        plt.xlabel('Iteration')
        plt.show()
        plt.ioff()
        savepic = os.path.join(dirname, 'output.pdf')
        plt.savefig(savepic)
        
        MEANS = [item.get_ydata() for item in B['means']]
        SDEVs = [np.std(df)[m] for m in range(I)] 
        MEDIANS = [item.get_ydata() for item in B['medians']]
        MEDIANS = [MEDIANS[m][0] for m in range(I)]
        WHISKERS = [item.get_ydata() for item in B['whiskers']]
        
        if outliers_yes_no == 0: # This includes outliers
            MEDIANS = [np.percentile(df.dropna(),50,axis=0)[m] for m in range(I)] 
            MINS = [np.min(df.dropna())[m] for m in range(I)]
            MAXS = [np.max(df.dropna())[m] for m in range(I)]
        else: # This excludes outliers
            MINS = [WHISKERS[2*m][1] for m in range(I)]
            MAXS = [WHISKERS[2*m+1][1] for m in range(I)]
            
        P25 = [WHISKERS[2*m][0] for m in range(I)]
        P75 = [WHISKERS[2*m+1][0] for m in range(I)]
        P5  = [np.percentile(df.dropna(),5,axis=0)[m] for m in range(I)] 
        P95 = [np.percentile(df.dropna(),95,axis=0)[m] for m in range(I)] 

    ########################## Test cases with one KPI sample per iteration (e.g., Service Creation Time) 
    if int(exp_type)==1:
        box_plot_data = list(df.loc[0,:].dropna())
        B=plt.boxplot(box_plot_data, notch=False, patch_artist=False, showmeans=True, showfliers=False, widths=0.8)
        
        plot.ion()
        plt.title('Comparison of measurements in the Test Case')
        plt.ylabel(kpi)
        plt.xlabel('Test Case')
        plt.show()
        plt.ioff()
        savepic = os.path.join(dirname, 'Iteration_Statistics.pdf')
        plt.savefig(savepic)

        MEANS = np.mean(df, axis=1)
        SDEVs = np.std(df, axis=1)
        MEDIANS = [item.get_ydata() for item in B['medians']]
        WHISKERS = [item.get_ydata() for item in B['whiskers']]
        
        if outliers_yes_no == 0: # This includes outliers
            MEDIANS = np.percentile(df.dropna(),50,axis=1)
            MINS = np.min(df.dropna(), axis=1)
            MAXS = np.max(df.dropna(), axis=1)
        else: # This would exclude outliers
            MINS = WHISKERS[0][1]
            MAXS = WHISKERS[1][1]
            
        P25 = WHISKERS[0][0]
        P75 = WHISKERS[1][0]
        P5  = np.percentile(df.dropna(),5,axis=1)
        P95 = np.percentile(df.dropna(),95,axis=1)
    ########################################################################################

    ## Statistics of the Test Case
    if int(exp_type)==0:  
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

        # Print out the statistics of the Test Case
        print('******************************************\n')
        print('Test Case Statistics \n')
        print('Mean: %f' % np.mean(MEANS), '+/- %f' %h[0], '%s' % unit, '\n')
        print('Standard deviation: %f' % np.mean(SDEVs),  '+/- %f' %h[1], '%s' % unit, '\n')
        print('Median: %f' % np.mean(MEDIANS), '+/- %f' %h[2], '%s' % unit, '\n')
        print('Min: %f' % np.mean(MINS), '+/- %f' %h[3], '%s' % unit, '\n')
        print('Max: %f' % np.mean(MAXS), '+/- %f' %h[4], '%s' % unit, '\n')
        print('25% Percentile:', np.mean(P25),'+/- %f' %h[5], '%s' % unit, '\n')
        print('75% Percentile:', np.mean(P75), '+/- %f' %h[6], '%s' % unit, '\n')
        print('5% Percentile:', np.mean(P5),'+/- %f' %h[7], '%s' % unit, '\n')
        print('95% Percentile:', np.mean(P95), '+/- %f' %h[8], '%s' % unit, '\n')
        print('******************************************\n')

    if int(exp_type)==1:
        print('******************************************\n')
        print('Test Case Statistics \n')
        print('Mean: %f' % MEANS, '%s' % unit, '\n')
        print('Standard deviation: %f' % SDEVs, '%s' % unit, '\n')
        print('Median: %f' % MEDIANS[0], '%s' % unit, '\n')
        print('Min: %f' % MINS, '%s' % unit, '\n')
        print('Max: %f' % MAXS, '%s' % unit, '\n')
        print('25% Percentile: ', P25, '%s' % unit, '\n')
        print('75% Percentile: ', P75, '%s' % unit, '\n')
        print('5% Percentile: ', float(P5), '%s' % unit, '\n')
        print('95% Percentile: ', float(P95), '%s' % unit, '\n')
        print('******************************************\n')
    
########################################################################################

# Test input
if __name__ == '__main__':
    
    # Mandatory Input examples
    file = "2019-08-07 21-26-19-DownlinkSinkonTrafficADB.csv"
    it = "_iteration_"                  # Iteration Identifier
    kpi = "Throughput (Mbps)"           # KPI Identifier
    unit = 'Mbps'                         # Measure Unit
    exp_type = 0                        # 0: (default) Experiments with several KPI samples per iteration (e.g. throughput, ping) (default)
                                        # 1: Experiments with a single KPI sample per iteration (e.g. Slice /Service creation time)
    # Usage in python
    # KPI_statistics(file, it, kpi, unit, exp_type)

    # Usage in Command Line
    KPI_statistics(*sys.argv[1:])

    #Examples of usage in command line
    # python3 Statistical_Analysis_csv.py "2019-08-07 21-26-19-DownlinkSinkonTrafficADB.csv" _iteration_ "Throughput (Mbps)" Mbps 0
    

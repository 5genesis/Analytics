# 5Genesis Analytics

## "Statistical Analysis" Repo

#### Prerequisites
- Python 3
- InfluxDB-Python client (see documentation in Utils folder)

### "Statistical_Analysis_csv.py"
The script evaluates the KPI statistical indicators as defined in D6.1 on experimental data stored in csv files:
- average (mean), max, min, stdev, median, 25%, 75%, 5% and 95% percentiles for each Iteration (given in figure)
- the same indicators for the entire Test case (by averaging across the Iterations), presented together with a 95% confidence interval (screen printed)

### "Statistical_Analysis_influxdb.py"
The script evaluates the KPI statistical indicators as defined in D6.1 on experimental data stored in a measurement table within an InfluxDB instance:
- average (mean), max, min, stdev, median, 25%, 75%, 5% and 95% percentiles for each Iteration (given in figure)
- the same indicators for the entire Test case (by averaging across the Iterations), presented together with a 95% confidence interval (screen printed)
- NB: platforms need to update the InfluxDB access credentianls (see at the end of the file)
 
#### See at the end of the files for examples of usage (Command Line (default) or within a Python editor)

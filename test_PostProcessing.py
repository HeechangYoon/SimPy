from PostProcessing import *
import pandas as pd

file_path = './result'
file_name = '/event_log_test.csv'

log = pd.read_csv(file_path+file_name)

util, idle, work = cal_utilization(log, name='M1', type='Process', start_time=0.0, finish_time=1000.0, step=10, display=True)
print(util)
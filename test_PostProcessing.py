from PostProcessing import *
import pandas as pd

file_path = './result'
file_name = '/event_log_test.csv'

log = pd.read_csv(file_path+file_name)

util, idle, work = cal_utilization(log, name='M1', type='Process', start_time=None, finish_time=None, step=10, display=False)
print(util)

LT = cal_leadtime(log, name='M1', type='Process', mode='m', start_time=None, finish_time=None, step=None)
print('Lead time: ', LT)

TH = cal_throughput(log, name='M1', type='Process', mode='m', start_time=None, finish_time=None, step=None, display=False)
print(TH)

WIP = cal_wip(log, name='M1', type='Process', mode='m', start_time=None, finish_time=None, step=None, display=False)
print(WIP)
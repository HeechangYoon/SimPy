import pandas as pd
import numpy as np
import simpy
import random
from collections import OrderedDict
from SimComponents import Source, Sink, Process, Monitor
import time

## 코드 실행 시작
start_0 = time.time()

## data 받아오기
data_all = pd.read_excel('./data/MCM_ACTIVITY.xls')
data = data_all[['PROJECTNO', 'ACTIVITYCODE', 'LOCATIONCODE', 'PLANSTARTDATE', 'PLANFINISHDATE', 'PLANDURATION']]

## data pre-processing
data = data[data['PLANSTARTDATE'].dt.year >= 2018]
data = data[data['LOCATIONCODE'] != 'OOO']

initial_date = data['PLANSTARTDATE'].min()

data['PLANSTARTDATE'] = data['PLANSTARTDATE'].apply(lambda x: (x - initial_date).days)
data['PLANFINISHDATE'] = data['PLANFINISHDATE'].apply(lambda x: (x - initial_date).days)
data['ACTIVITY'] = data['ACTIVITYCODE'].apply(lambda x: x[5:])
data['BLOCKCODE'] = data['PROJECTNO'] + ' ' + data['LOCATIONCODE']

data_len = len(data)

process_list = list(data.drop_duplicates(['ACTIVITY'])['ACTIVITY'])
block_list = list(data.drop_duplicates(['BLOCKCODE'])['BLOCKCODE'])

print('data pre-processing : ', time.time() - start_0)

block1 = []  # 가공 전
block2 = []  # 가공 후

# raw data 저장 - block1(list)
'''for block_code in block_list:
    temp = data[data['BLOCKCODE'] == block_code]
    temp.sort_values(by=['PLANSTARTDATE'], axis=0, inplace=True)
    temp = temp.reset_index(drop=True)
    block1.append(temp)'''

print('1 : ', time.time() - start_0)
# 중복된 작업시간 가공한 데이터 저장 - df(dataframe)
# S-Module에 넣어 줄 dataframe
columns = pd.MultiIndex.from_product([[i for i in range(13)], ['start_time', 'process_time', 'process']])  # 13 : 한 블록이 거치는 공정의 최대 개수 + Sink
df = pd.DataFrame([], columns=columns) #######################
print('2 : ', time.time() - start_0)
idx = 0 #######################
time_list = []

for block_code in block_list:
    for_start = time.time()
    temp = data[data['BLOCKCODE'] == block_code]
    temp.sort_values(by=['PLANSTARTDATE'], axis=0, inplace=True)
    temp = temp.reset_index(drop=True)
    temp_list = []  #######################
    df.loc[idx] = [None for _ in range(len(df.columns))]
    n = 0  # 저장된 공정 개수

    for i in range(0, len(temp) - 1):
        activity = temp['ACTIVITY'][i]
        date1 = temp['PLANFINISHDATE'][i]  # 선행공정 종료날짜
        date2 = temp['PLANSTARTDATE'][i+1]  # 후행공정 시작날짜
        date3 = temp['PLANFINISHDATE'][i+1]  # 후행공정 종료날짜

        if date1 > date2:  #후행공정이 선행공정 종료 전에 시작할 때
            if date1 > date3:  #후행공정이 선행공정에 포함될 때
                temp['PLANDURATION'][i+1] = -1
            else:
                temp['PLANDURATION'][i+1] -= date2 - date1

        if temp['PLANDURATION'][i] > 0:  #######################
            #temp_list += [temp['PLANSTARTDATE'][i], temp['PLANDURATION'][i], activity]
            df.loc[idx][n] = [temp['PLANSTARTDATE'][i], temp['PLANDURATION'][i], activity]
            n += 1

    if temp['PLANDURATION'][len(temp)-1] > 0:
        # temp_list += [temp['PLANSTARTDATE'][len(temp)-1], temp['PLANDURATION'][len(temp)-1], temp['ACTIVITY'][len(temp)-1]]
        df.loc[idx][n] = [temp['PLANSTARTDATE'][len(temp)-1], temp['PLANDURATION'][len(temp)-1], temp['ACTIVITY'][len(temp)-1]]
        n += 1
    df.loc[idx][(n, 'process')] = 'Sink'
    #temp_list += [None, None, 'Sink']  #######################
    #temp_list += [None for _ in range(len(df.columns) - len(temp_list))]  #######################

    #if len(temp_list) == len(df.columns):
    # df.loc[idx] = temp_list  #######################

    # temp = temp[temp['PLANDURATION'] >= 0]
    idx += 1  #######################
    time_list.append(time.time() - for_start)
    #block2.append(temp)
print('3 : ', time.time() - start_0)
df.sort_values(by=[(0, 'start_time')], axis=0, inplace=True)
df = df.reset_index(drop=True)
print(time.time() - start_0)
print(np.mean(time_list))
# block2 = sorted(block2, key=lambda x: x.iloc[0]['PLANSTARTDATE'])

env = simpy.Environment()

process_dict = {}

Source = Source(env, 'Source', "df", df, process_dict, len(df))
Sink = Sink(env, 'Sink', rec_lead_time=True, rec_arrivals=True)

process = []
for i in range(len(process_list)):
    process.append(Process(env, process_list[i], 10, process_dict, 10000))
for i in range(len(process_list)):
    process_dict[process_list[i]] = process[i]

process_dict['Sink'] = Sink

# Run it
start = time.time()
env.run()
finish = time.time()

print('#' * 80)
print("Results of simulation")
print('#' * 80)

# 코드 실행 시간
print("data pre-processing : ", start - start_0)
print("simulation execution time :", finish - start)
print("total time : ", finish - start_0)

# 총 리드타임 - 마지막 part가 Sink에 도달하는 시간
print("Total Lead Time :", Sink.last_arrival)

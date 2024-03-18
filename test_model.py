from SimComponents import *
import simpy
import os


file_path = './result'
file_name = '/event_log_test.csv'
if not os.path.exists(file_path):
    os.makedirs(file_path)

env = simpy.Environment()
monitor = Monitor(file_path+file_name)

operation = dict()
operation['Ops1-1'] = Operation('Ops1-1', {'M1': 5, 'M2': 5})
operation['Ops1-2'] = Operation('Ops1-2', {'M3': 5, 'M4': 5, 'M5': 5})
operation['Ops1-3'] = Operation('Ops1-3', {'M3': 5, 'M4': 5, 'M5': 5})
operation['Ops2-1'] = Operation('Ops2-1', {'M1': 5, 'M2': 5})
operation['Ops2-2'] = Operation('Ops2-2', {'M3': 5, 'M4': 5, 'M5': 5})
operation['Ops3-1'] = Operation('Ops3-1', {'M3': 5, 'M4': 5, 'M5': 5})
operation['Ops3-2'] = Operation('Ops3-2', {'M1': 5, 'M2': 5})

model = dict()
model['M1'] = Process(env, 'M1', model, monitor, capacity=2, in_buffer=2, out_buffer=2)
model['M2'] = Process(env, 'M2', model, monitor, capacity=2, in_buffer=2, out_buffer=2)
model['M3'] = Process(env, 'M3', model, monitor, capacity=2, in_buffer=2, out_buffer=2)
model['M4'] = Process(env, 'M4', model, monitor, capacity=2, in_buffer=2, out_buffer=2)
model['M5'] = Process(env, 'M5', model, monitor, capacity=2, in_buffer=2, out_buffer=2)
model['Routing'] = Routing(env, model, monitor)
model['Sink'] = Sink(env, monitor)

jobtype1 = [operation['Ops1-1'], operation['Ops1-2'], operation['Ops1-3']]
jobtype2 = [operation['Ops2-1'], operation['Ops2-2']]
jobtype3 = [operation['Ops3-1'], operation['Ops3-2']]

source1 = Source(env, 'Source_jobtype1', model, monitor, job_name='jobtype1', jobtype=jobtype1, IAT=15)
source2 = Source(env, 'Source_jobtype2', model, monitor, job_name='jobtype2', jobtype=jobtype2, IAT=10)
source3 = Source(env, 'Source_jobtype3', model, monitor, job_name='jobtype3', jobtype=jobtype3, IAT=10)

env.run(until=50000)

monitor.save_event_tracer()
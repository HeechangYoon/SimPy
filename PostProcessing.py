import numpy as np
import pandas as pd
import datetime
import random
import matplotlib.pyplot as plt
import plotly.figure_factory as ff


def graph(x, y, title=None, display=False, save=False, filepath=None):
    fig, ax = plt.subplots()
    ax.plot(x, y)
    ax.set_title(title)
    if display:
        plt.show()
    if save:
        fig.savefig(filepath + "/" + title + ".png")
        plt.close("all")


def cal_utilization(log, name=None, type='Process', start_time=None, finish_time=None, step=1, display=False, save=False, filepath=None):
    if start_time is None:
        start_time = log["Time"].min()
    if finish_time is None:
        finish_time = log["Time"].max()

    log = log[(log[type] == name) & ~(log["Event"].str.startswith("Routing")) & ((log["Event"].str.endswith("Start")) | (log["Event"].str.endswith("Finish")))]

    iteration = step

    time = np.linspace(start_time, finish_time, num=iteration+1)
    utilization = np.array([0.0 for _ in range(iteration)])
    idle_time = np.array([0.0 for _ in range(iteration)])
    working_time = np.array([0.0 for _ in range(iteration)])

    for i in range(iteration):
        if step:
            start_time = time[i]
            finish_time = time[i + 1]
        data = log[(log["Time"] >= start_time) & (log["Time"] <= finish_time)]

        total_time = finish_time - start_time

        work_start = data[data['Event'].str.endswith("Start")]
        work_finish = data[data['Event'].str.endswith("Finish")]

        if len(work_start) == 0 and len(work_finish) == 0:
            temp = log[log[type] == name]
            if len(temp) != 0:
                idx = temp["Time"] >= start_time
                if temp[idx].iloc[0]["Event"].str.endswith("Finish"):
                    working_time[i] += (finish_time - start_time)
                    continue
            # working_time += 0.0
            # total_time += (finish_time - start_time)
            continue
        elif len(work_start) != 0 and len(work_finish) == 0:
            row = dict(work_start.iloc[0])
            row["Time"] = finish_time
            row["Event"] = "Work Finish"
            work_finish = pd.DataFrame([row])
        elif len(work_start) == 0 and len(work_finish) != 0:
            row = dict(work_finish.iloc[0])
            row["Time"] = start_time
            row["Event"] = "Work Start"
            work_start = pd.DataFrame([row])
        else:
            if work_start.iloc[0]["Part"] != work_finish.iloc[0]["Part"]:
                row = dict(work_finish.iloc[0])
                row["Time"] = start_time
                row["Event"] = "Work Start"
                work_start = pd.DataFrame([row]).append(work_start)
            if work_start.iloc[-1]["Part"] != work_finish.iloc[-1]["Part"]:
                row = dict(work_start.iloc[-1])
                row["Time"] = finish_time
                row["Event"] = "Work Finish"
                work_finish = work_finish.append(pd.DataFrame([row]))

        work_start = work_start["Time"].reset_index(drop=True)
        work_finish = work_finish["Time"].reset_index(drop=True)
        working_time[i] += np.sum(work_finish - work_start)

        idle_time[i] = total_time - working_time[i]
        utilization[i] = working_time[i] / total_time if total_time != 0.0 else 0.0

    if step:
        utilization = pd.DataFrame({"Time": time[1:], "Utilization": utilization[:]})
        idle_time = pd.DataFrame({"Time": time[1:], "Idle_time": idle_time[:]})
        working_time = pd.DataFrame({"Time": time[1:], "Working_time": working_time[:]})
        if display or save:
            title = "utilization of {0} in ({1:.2f}, {2:.2f})".format(name, start_time, finish_time)
            graph(utilization["Time"], utilization["Utilization"], title=title, display=display, save=save, filepath=filepath)
        return utilization, idle_time, working_time
    else:
        return utilization[0], idle_time[0], working_time[0]


def cal_leadtime(log, name, type, mode='m', start_time=0.0, finish_time=0.0, step=None, display=False, save=False, filepath=None):
    if start_time is None:
        start_time = log["Time"].min()
    if finish_time is None:
        finish_time = log["Time"].max()
    log = log[(log["Time"] >= start_time) & (log["Time"] <= finish_time)]

    if mode == "m":
        log = log[(log['Event'] == "Part Created") | (log['Event'] == "Part Completed")]
    else:
        log = log[(log['Event'] == "Part Entered") | (log["Event"] == "Part Transferred")]
        log = log[log[type] == name]

    if step:
        iteration = step
    else:
        iteration = 1

    time = np.linspace(start_time, finish_time, num=iteration + 1)
    lead_time = np.array([0.0 for _ in range(iteration)])

    part_list = list(np.unique(list(log["Part"])))
    event_grp = log.groupby(log["Part"])

    for i in range(iteration):
        if step:
            start_time = time[i]
            finish_time = time[i + 1]

        hanging_time = 0.0
        for part in part_list:
            each_part = event_grp.get_group(part)
            time_list = list(each_part["Time"])
            time_list = [x for x in time_list if (x >= start_time) & (x <= finish_time)]
            if len(time_list) == 2:  # Start ~ Finish 사이에 입고부터 출고까지 이루어진 경우
                hanging_time += time_list[1] - time_list[0]
            elif len(time_list) == 1:  # Start ~ Finish 사이에 입고만 된 경우 -> 아직 출고 전
                hanging_time += finish_time - time_list[0]

        lead_time[i] = hanging_time / len(part_list)

    if step:
        lead_time = pd.DataFrame({"Time": time[1:], "lead time": lead_time[:]})
        if display or save:
            title = "wip of {0} in ({1:.2f}, {2:.2f})".format(name, start_time, finish_time)
            graph(lead_time["Time"], lead_time["lead time"], title=title, display=display, save=save,
                  filepath=filepath)
        return lead_time
    else:
        return lead_time[0]


def cal_throughput(log, name, type, mode='m', start_time=0.0, finish_time=0.0, step=None, display=False, save=False, filepath=None):
    if start_time is None:
        start_time = log["Time"].min()
    if finish_time is None:
        finish_time = log["Time"].max()

    if mode == 'm':
        log = log[(log["Event"] == "Part Completed")]
    else:
        log = log[(log[type] == name) & (log["Event"] == "Part Transferred")]
    if step:
        iteration = step
    else:
        iteration = 1

    time = np.linspace(start_time, finish_time, num=iteration+1)
    throughput = np.array([0.0 for _ in range(iteration)])

    for i in range(iteration):
        if step:
            start_time = time[i]
            finish_time = time[i + 1]

        total_time = finish_time - start_time
        part_transferred = log[(log["Time"] >= start_time) & (log["Time"] <= finish_time)]
        throughput[i] = len(part_transferred) / total_time if total_time != 0.0 else 0.0

    if step:
        throughput = pd.DataFrame({"Time": time[1:], "Throughput": throughput[:]})
        if display or save:
            title = "throughput of {0} in ({1:.2f}, {2:.2f})".format(name, start_time, finish_time)
            graph(throughput["Time"], throughput["Throughput"], title=title, display=display, save=save, filepath=filepath)
        return throughput
    else:
        return throughput[0]


def cal_wip(log, name, type, mode='m', start_time=0.0, finish_time=0.0, step=None, display=False, save=False, filepath=None):
    if start_time is None:
        start_time = log["Time"].min()
    if finish_time is None:
        finish_time = log["Time"].max()
    log = log[(log["Time"] >= start_time) & (log["Time"] <= finish_time)]

    if mode == "m":
        log = log[(log['Event'] == "Part Created") | (log['Event'] == "Part Completed")]
    else:
        log = log[(log['Event'] == "Part Entered") | (log["Event"] == "Part Transferred")]
        log = log[log[type] == name]

    if step:
        iteration = step
    else:
        iteration = 1

    time = np.linspace(start_time, finish_time, num=iteration + 1)
    wip = np.array([0.0 for _ in range(iteration)])

    part_list = list(np.unique(list(log["Part"])))
    event_grp = log.groupby(log["Part"])

    for i in range(iteration):
        if step:
            start_time = time[i]
            finish_time = time[i + 1]

        hanging_time = 0.0
        for part in part_list:
            each_part = event_grp.get_group(part)
            time_list = list(each_part["Time"])
            time_list = [x for x in time_list if (x >= start_time) & (x <= finish_time)]
            if len(time_list) == 2:  # Start ~ Finish 사이에 입고부터 출고까지 이루어진 경우
                hanging_time += time_list[1] - time_list[0]
            elif len(time_list) == 1:  # Start ~ Finish 사이에 입고만 된 경우 -> 아직 출고 전
                hanging_time += finish_time - time_list[0]

        wip[i] = hanging_time / (finish_time - start_time)

    if step:
        throughput = pd.DataFrame({"Time": time[1:], "wip": wip[:]})
        if display or save:
            title = "wip of {0} in ({1:.2f}, {2:.2f})".format(name, start_time, finish_time)
            graph(throughput["Time"], throughput["Throughput"], title=title, display=display, save=save, filepath=filepath)
        return wip
    else:
        return wip[0]

def gantt(data, process_list):
    list_part = list(data["Part"][data["Event"] == "part_created"])
    start = datetime.date(2020,8,31)
    r = lambda: random.randint(0, 255)
    dataframe = []
    # print('#%02X%02X%02X' % (r(),r(),r()))
    colors = ['#%02X%02X%02X' % (r(), r(), r())]

    for part in list_part:
        part_data = data[data["Part"] == part]
        #data_by_group = part_data.groupby(part_data["Process"])
        for i in process_list:
            group = part_data[part_data["Process"] == i]
            if (i != "Sink") and (i != "Source") and len(group) != 0:
                work_start = group[group["Event"] == "work_start"]
                work_start = list(work_start["Time"].reset_index(drop=True))
                work_finish = group[group["Event"] == "work_finish"]
                work_finish = list(work_finish["Time"].reset_index(drop=True))
                dataframe.append(dict(Task=i, Start=(start + datetime.timedelta(days=work_start[0])).isoformat(),Finish=(start + datetime.timedelta(days=work_finish[0])).isoformat(), Resource=part))
                colors.append('#%02X%02X%02X' % (r(), r(), r()))
            else:
                pass

    fig = ff.create_gantt(dataframe, colors=colors, index_col='Resource', group_tasks=True)
    fig.show()
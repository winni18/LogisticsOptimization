from route_utils import PathInformation
from tqdm import tqdm
import numpy as np
import pandas as pd


def compute_savings_list(route_list, problem_data):
    save_list = []
    for i in tqdm(range(len(route_list))):
        for j in range(len(route_list)):
            if i != j:
                route_list_tmp = route_list[i].route.copy()
                route_list_tmp.extend(route_list[j].route)
                route = PathInformation(route_list_tmp, problem_data)
                if route.total_cost > 0:
                    save_cost = route_list[i].total_cost + route_list[j].total_cost - route.total_cost
                    if save_cost > 0:
                        save_list.append([(i, j), save_cost])
    save_list.sort(key=lambda x: x[1], reverse=True)
    return save_list


def find_save_list(save_list):
    find = []
    tmp = []
    find.append(save_list[0][0])
    tmp.append(save_list[0][0][0])
    tmp.append(save_list[0][0][1])
    for i in range(1, len(save_list)):
        if save_list[i][0][0] not in tmp and save_list[i][0][1] not in tmp:
            find.append(save_list[i][0])
            tmp.append(save_list[i][0][0])
            tmp.append(save_list[i][0][1])
        if len(find) == 300:
            break
    return find


def merge_list(route_list, problem_data, save_list):
    dst_list = []
    tmp_list = []
    for i in range(len(save_list)):
        tmp_list.append(save_list[i][0])
        tmp_list.append(save_list[i][1])
        route_list_tmp = route_list[save_list[i][0]].route.copy()
        route_list_tmp.extend(route_list[save_list[i][1]].route)
        tmp = [PathInformation(route_list_tmp, problem_data)]
        dst_list.extend(tmp)
    for i in range(len(route_list)):
        if i in tmp_list:
            continue
        dst_list.extend([route_list[i]])
    return dst_list


def compute_all_cost(route_list):
    total_cost = 0
    for i in range(len(route_list)):
        total_cost += route_list[i].total_cost
    return total_cost


def save_result(save_file, route_list, problem_data):
    title = ["vehicle_type", "dist_seq", "distribute_lea_tm", "distribute_arr_tm", "distance",
             "trans_cost", "charge_cost", "wait_cost", "fixed_use_cost", "total_cost", "charge_cnt"]
    tmp=[]
    for i in range(len(route_list)):
       row = i + 1
       cal_list = route_list[i].cal_all_param(problem_data)
       # cal_list.insert(0, "DP%04d"%row)
       tmp.append(cal_list)
    x = np.array(tmp)
    df = pd.DataFrame(x, index=None, columns=title)
    df.to_csv(save_file)
import os
from data_utils import ProblemData
from vrp_utils import *

charger_id = {"inputnode_1_1601": [11501, 11600],
              "inputnode_2_1501": [21401, 21500],
              "inputnode_3_1401": [31301, 31400],
              "inputnode_4_1301": [41201, 41300],
              "inputnode_5_1201": [51101, 51200]}
data_dir = 'data'
for file_name in os.listdir(data_dir):
    if file_name.endswith('xlsx'):
        show_txt = file_name.split('.')[0]
        n_file = os.path.join(data_dir, file_name)
        d_name = file_name.split('.')[0].split('_')[1:]
        d_name = "inputdistancetime_" + "_".join(d_name) + ".txt"
        d_file = os.path.join(data_dir, d_name)

        save_name = file_name.split('.')[0].split('_')[1]
        save_name = "result_" + str(save_name) + ".csv"
        print("读入{}......".format(show_txt))
        problem_data = ProblemData(d_file, n_file, charger_id[show_txt][0], charger_id[show_txt][1])
        route_list = []
        print("初始化......")
        for i in range(len(problem_data.customer_node_list)):
            route_tmp = [0, problem_data.customer_node_list[i]]
            route_list.append(PathInformation(route_tmp, problem_data))
        last_cost = compute_all_cost(route_list)

        print("开始优化")
        i = 1
        while True:
            save_list = compute_savings_list(route_list, problem_data)
            #如果没有再可以优化的路线，则跳出循环
            if len(save_list) == 0:
                break
            save_list = find_save_list(save_list)
            route_tmp = merge_list(route_list, problem_data, save_list)
            cost_tmp = compute_all_cost(route_tmp)
            save_cost = last_cost - cost_tmp
            if cost_tmp >= last_cost:
                break
            last_cost = cost_tmp
            route_list = route_tmp.copy()
            print('正在优化文件:{}, 第{}次迭代：总成本{:.3f}, 共使用{}台车辆, 节约成本{:.3f}'
                  .format(show_txt, i, last_cost, len(route_list), save_cost))
            i += 1
        if len(route_list) > 500:
            print("算法优化失败， 车辆约束不满足")
            continue
        save_result(save_name, route_list, problem_data)

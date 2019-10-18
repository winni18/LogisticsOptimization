class PathInformation(object):
    def __init__(self, route_path, problem_data):
        self.route = route_path
        self.vehicle = -1
        # 分别对两种车型优化路线,及求出总费用
        cost_1, route_1 = self._optimization(1, problem_data)
        cost_2, route_2 = self._optimization(2, problem_data)
        if cost_1 < 0:
            if cost_2 < 0:
                self.total_cost = -1
                self.route = None
            else:
                self.total_cost = cost_2
                self.route = route_2.copy()
                self.vehicle = 2
        else:
            if cost_2 < 0:
                self.total_cost = cost_1
                self.route = route_1.copy()
                self.vehicle = 1
            else:
                if cost_1 > cost_2:
                    self.total_cost = cost_2
                    self.route = route_2.copy()
                    self.vehicle = 2
                else:
                    self.total_cost = cost_1
                    self.route = route_1.copy()
                    self.vehicle = 1

    def _optimization(self, type_tmp, problem_data):
        route = self._optimization_route(problem_data, type_tmp)
        if not self._cal_state(route, type_tmp, problem_data):
            return -1, None
        cost = self._cal_cost(route, type_tmp, problem_data)
        return cost, route

    def _optimization_route(self, problem_data, vehicle_type):
        # 首先删除充电站， 及中心节点
        if len(self.route) == 2:
            return self.route
        tmp = self.route.copy()
        for x in tmp:
            if problem_data.customer[x].type == 4 or x == 0:
                tmp.remove(x)
        # 先对最早服务时间排序再对最迟服务时间排序
        tmp.sort(key=lambda x: problem_data.customer[x].st, reverse=False)
        tmp.sort(key=lambda x: problem_data.customer[x].et, reverse=False)
        tmp.insert(0, 0)  # 插入开始节点
        dst = []
        residue_distance = problem_data.vehicle[vehicle_type].maxRange
        for i in range(len(tmp)):
            dst.append(tmp[i])
            # 路径第一个节点， 即中心节点
            if i == 0:
                continue
            # 路径最后一个节点
            if i == len(tmp) - 1:
                continue
            residue_distance -= problem_data.disM[(tmp[i - 1], tmp[i])]
            distance_tmp1 = problem_data.disM[(tmp[i], tmp[i + 1])]  # 到下一个节点的距离
            distance_tmp2 = problem_data.disM[(tmp[i + 1], problem_data.customer[tmp[i + 1]].cs_id)]  # 下一个节点到充电站的距离
            distance_tmp3 = problem_data.disM[(tmp[i + 1], 0)]  # 下一个节点到中心节点的距离
            min_distance = min(distance_tmp2, distance_tmp3)  # 取最小值

            # 倒数第二个节点
            if i == len(tmp) - 2:
                # 如果到达不到下一节点到充电站或者中心点的距离则添加一个充电站 则剩余里程重置
                if residue_distance < distance_tmp1 + min_distance:
                    dst.append(problem_data.customer[tmp[i]].cs_id)
                    residue_distance = problem_data.vehicle[vehicle_type].maxRange
            else:
                # 如果到达不了下一节点到充电站的距离则添加一个充电站 则剩余里程重置
                if residue_distance < distance_tmp1 + distance_tmp2:
                    dst.append(problem_data.customer[tmp[i]].cs_id)
                    residue_distance = problem_data.vehicle[vehicle_type].maxRange
        return dst

    def _cal_state(self, route, vehicle_type, problem_data):
        w_2 = 0  # 送货总重量
        v_2 = 0  # 送货总体积
        w_3 = 0  # 揽货总重量
        v_3 = 0  # 揽货总体积

        last_leave = 480  # 上一个节点的发车时间, 初始化为， 8点
        # 第一个节点是中心站
        for i in range(1, len(route)):
            # 体积重量判断
            if problem_data.customer[route[i]].type == 2:
                w_2 += abs(problem_data.customer[route[i]].weight)
                v_2 += abs(problem_data.customer[route[i]].volume)
            if problem_data.customer[route[i]].type == 3:
                w_3 += abs(problem_data.customer[route[i]].weight)
                v_3 += abs(problem_data.customer[route[i]].volume)
            if w_2 > problem_data.vehicle[vehicle_type].maxWei or v_2 > problem_data.vehicle[vehicle_type].maxVol:
                return False
            if w_3 > problem_data.vehicle[vehicle_type].maxWei or v_3 > problem_data.vehicle[vehicle_type].maxVol:
                return False

            # 服务时间判断
            cur_arrive = last_leave + problem_data.timM[(route[i - 1], route[i])]  # 到达当前节点时间
            # 如果是客户节点，当前到站时间超过最晚服务时间， 充电站及中心无需判断最迟服务时间
            if problem_data.customer[route[i]].type == 2 or problem_data.customer[route[i]].type == 3:
                if cur_arrive > problem_data.customer[route[i]].et:
                    return False
            # 如果当前到站时间小于最早服务时间
            if cur_arrive < problem_data.customer[route[i]].st:
                cur_arrive = problem_data.customer[route[i]].st
            if problem_data.customer[route[i]].type == 4:
                last_leave = cur_arrive + problem_data.chargeT
            else:
                last_leave = cur_arrive + problem_data.unloadT
        return True

    def _cal_cost(self, route, vehicle_type, problem_data):
        _leave_time = self._optimization_leave_time(problem_data)  # 优化发车时间

        # 计算成本

        residue_distance = problem_data.vehicle[vehicle_type].maxRange
        distance = 0  # 当前路径总行驶里程
        wait_cost = 0  # 当前路径总等待时间
        leave_time = _leave_time  # 发车时间
        charge_cost = 0  # 充电成本
        for i in range(1, len(route)):
            residue_distance -= problem_data.disM[(route[i-1], route[i])]
            if problem_data.customer[route[i]].type == 4:
                residue_distance = problem_data.vehicle[vehicle_type].maxRange
                service_time = problem_data.chargeT
                # 充电成本
                charge_cost += problem_data.chargeCost
            else:
                service_time = problem_data.unloadT

            # 里程成本
            distance += problem_data.disM[(route[i-1], route[i])]
            # 计算等待成本
            arrive_time = problem_data.timM[(route[i - 1], route[i])] + leave_time
            if arrive_time < problem_data.customer[route[i]].st:
                wait_cost += (problem_data.customer[route[i]].st - arrive_time)
                leave_time = problem_data.customer[route[i]].st + service_time
            else:
                leave_time = arrive_time + service_time

        # 返回成本, 如果走到最后一点，发现当前里程数小于直接返回中心点，则需要绕道充电站
        to_charger_dist = problem_data.disM[(route[-1], problem_data.customer[route[-1]].cs_id)]
        to_ori_dist = problem_data.disM[(route[-1], 0)]
        if residue_distance < to_ori_dist:
            charger_to_ori = problem_data.disM[(problem_data.customer[route[-1]].cs_id, 0)]
            # charge_cost += problem_data.chargeCost
            return_cost = to_charger_dist + charger_to_ori
            return_cost = return_cost * problem_data.vehicle[vehicle_type].unitCost + problem_data.chargeCost
        else:
            return_cost = to_ori_dist
            return_cost = return_cost * problem_data.vehicle[vehicle_type].unitCost
        distance = distance * problem_data.vehicle[vehicle_type].unitCost
        wait_cost = wait_cost * problem_data.waitCost
        return distance + wait_cost + charge_cost + return_cost + problem_data.vehicle[vehicle_type].viechleCost

    def _optimization_leave_time(self, problem_data):
        end_time = problem_data.customer[self.route[-1]].et  # 最后一节点的最迟到达时间
        # 计算上一节点最迟到达时间
        for i in range(len(self.route)-1, 1, -1):
            # 如果最后一个节点是充电站时
            if problem_data.customer[self.route[i]].type == 4 and i == len(self.route)-1:
                end_time = problem_data.customer[self.route[i-1]].et
                continue

            # 上一站点服务时间
            if problem_data.customer[self.route[i - 1]].type == 4:
                service_time = problem_data.chargeT
            else:
                service_time = problem_data.unloadT

            # 上一站点最迟发车时间
            last_leave = end_time - problem_data.timM[(self.route[i - 1], self.route[i])]

            # 计算上一节点最迟到站时间
            if problem_data.customer[self.route[i-1]].type == 4:
                last_end_time = last_leave - service_time
            else:
                if last_leave >= problem_data.customer[self.route[i-1]].et + service_time:
                    last_end_time = problem_data.customer[self.route[i-1]].et
                else:
                    last_end_time = last_leave - service_time

            end_time = last_end_time
        _leave_time = end_time - problem_data.timM[(0, self.route[1])]
        if _leave_time < 480:
            _leave_time = 480
        return _leave_time



    def cal_all_param(self, problem_data):
        _leave_time = self._optimization_leave_time(problem_data)  # 优化首站发车时间
        distance = 0  # 当前路径总行驶里程
        wait_cost = 0  # 当前路径总等待时间
        charge_cost = 0  # 充电成本
        charge_cn = 0  # 充电次数
        leave_time = _leave_time  # 中间变量计算到站时间
        residue_distance = problem_data.vehicle[self.vehicle].maxRange
        for i in range(1, len(self.route)):
            residue_distance -= problem_data.disM[(self.route[i-1], self.route[i])]
            if problem_data.customer[self.route[i]].type == 4:
                residue_distance = problem_data.vehicle[self.vehicle].maxRange
                service_time = problem_data.chargeT
                # 充电成本
                charge_cost += problem_data.chargeCost
                charge_cn += 1
            else:
                service_time = problem_data.unloadT

            # 里程成本
            distance += problem_data.disM[(self.route[i-1], self.route[i])]
            # 计算等待成本
            arrive_time = problem_data.timM[(self.route[i - 1], self.route[i])] + leave_time

            if arrive_time < problem_data.customer[self.route[i]].st:
                wait_cost += (problem_data.customer[self.route[i]].st - arrive_time)
                leave_time = problem_data.customer[self.route[i]].st + service_time
            else:
                leave_time = arrive_time + service_time
        # 返回成本, 如果当前里程数小于直接返回中心点，则需要绕道充电站
        to_charger_dist = problem_data.disM[(self.route[-1], problem_data.customer[self.route[-1]].cs_id)]
        to_ori_dist = problem_data.disM[(self.route[-1], 0)]
        if residue_distance < to_ori_dist:
            # 计算到站时间
            leave_time += problem_data.timM[(self.route[-1], problem_data.customer[self.route[-1]].cs_id)]
            leave_time += 30
            leave_time += problem_data.timM[(problem_data.customer[self.route[-1]].cs_id, 0)]
            # 计算里程
            distance += to_charger_dist

            charge_cn += 1
            charge_cost += problem_data.chargeCost
            distance += problem_data.disM[(problem_data.customer[self.route[-1]].cs_id, 0)]
            # 添加返回节点
            self.route.append(problem_data.customer[self.route[-1]].cs_id)
            self.route.append(0)
        else:
            distance += to_ori_dist
            leave_time += problem_data.timM[(self.route[-1], 0)]
            self.route.append(0)

        hour = _leave_time // 60
        minute = _leave_time % 60
        lea_time = str(hour) + ":" + str(minute)
        hour = leave_time // 60
        minute = leave_time % 60
        arr_time = str(hour) + ":" + str(minute)
        dist_seq = [str(i) for i in self.route]
        dist_seq = ";".join(dist_seq)
        return_list = [self.vehicle, dist_seq, lea_time, arr_time, distance,
                       distance * problem_data.vehicle[self.vehicle].unitCost,
                       charge_cost, wait_cost * problem_data.waitCost, problem_data.vehicle[self.vehicle].viechleCost,
                       self.total_cost, charge_cn]
        return return_list

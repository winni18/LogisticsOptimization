import xlrd
from collections import namedtuple


class ProblemData(object):

    def __init__(self, dist_file, node_file, charger_start_id, charger_end_id):
        # 读取距离文件
        self.disM = {}
        self.timM = {}
        with open(dist_file, 'r') as file:
            file.readline()  # 跳过第一行title数据
            for line in file:
                from_node, to_node, distance, spend_tm = line.split()[0].split(',')[1:]
                self.disM[(int(from_node), int(to_node))] = int(distance)
                self.timM[(int(from_node), int(to_node))] = int(spend_tm)

        customerPoint = namedtuple('customer',
                                   ['id', 'type', 'lng', 'lat', 'weight', 'volume', 'st', 'et', 'cs_id'])
        self.customer = {}
        with xlrd.open_workbook(node_file) as xlsxdata:  # 打开excel文件
            sheet = xlsxdata.sheet_by_index(0)  # 打开excel文件的第一个worksheet
            for row in range(1, sheet.nrows):  # 从1开始剔除title行
                x_id = int(sheet.cell(row, 0).value)
                x_type = int(sheet.cell(row, 1).value)
                x_lng = float(sheet.cell(row, 2).value)
                x_lat = float(sheet.cell(row, 3).value)
                if sheet.cell(row, 4).value == '-':  # depot和charging station单独处理一下
                    x_weight = 0
                else:
                    x_weight = float(sheet.cell(row, 4).value)
                if sheet.cell(row, 5).value == '-':  # depot和charging station单独处理一下
                    x_volume = 0
                else:
                    x_volume = float(sheet.cell(row, 5).value)
                if sheet.cell(row, 6).value == '-':  # charging station单独处理一下
                    xst = 0
                else:
                    temp_tuple = xlrd.xldate_as_tuple(sheet.cell(row, 6).value, 0)
                    xst = temp_tuple[3] * 60 + temp_tuple[4]
                if sheet.cell(row, 7).value == '-':  # charging station单独处理一下
                    xet = 0
                elif sheet.cell(row, 7).value == 0:  # depot的结束时间是00:00，需要单独处理一下
                    xet = 24 * 60
                else:
                    temp_tuple = xlrd.xldate_as_tuple(sheet.cell(row, 7).value, 0)
                    xet = temp_tuple[3] * 60 + temp_tuple[4]
                if x_type == 1:  # 如果是depot
                    self.customer[x_id] = customerPoint(x_id, x_type, x_lng, x_lat, 0, 0, 8 * 60, 24 * 60, 0)
                elif x_type == 2 or x_type == 3:  # 如果是customer
                    if x_type == 2:  # 如果是送货商家
                        x_weight = -x_weight
                        x_volume = -x_volume
                    depot_charging_st = list(range(charger_start_id, charger_end_id + 1))
                    cs = min([(self.timM[x_id, i], i) for i in depot_charging_st])  # 注意这里用时间衡量
                    if (self.timM[x_id, 0] + 60) < (cs[0] + 30):  # 如果到depot充电时间完成时间更早，选择depot充电
                        self.customer[x_id] = customerPoint(x_id, x_type, x_lng, x_lat, x_weight, x_volume, xst, xet, 0)
                    self.customer[x_id] = customerPoint(x_id, x_type, x_lng, x_lat, x_weight, x_volume, xst, xet, cs[1])
                else:  # 如果是charging station 则充电节点为其自身
                    self.customer[x_id] = customerPoint(x_id, x_type, x_lng, x_lat, 0, 0, 0, 24 * 60, x_id)
        self.customer_node_list = []  # 需要服务的节点
        for key in self.customer.keys():
            if self.customer[key].type == 2 or self.customer[key].type == 3:
                self.customer_node_list.append(key)

        self.chargeCost = 50  # 充电费用100元每小时,充电时间0.5小时。只要有充电发生，成本就是50元。
        self.waitCost = 0.4  # 等待成本系数24元每小时，24/60每分钟
        self.unloadT = 30  # 卸货时间恒定为0.5h。
        self.chargeT = 30  # 充电站充电时间恒定为0.5h。
        self.depotWaitingCost = 60  # 第n次（n>1）起从配送中心出发需要在配送中心等待1h,计算等待成本
        self.vehicle = {}
        vehicleInfo = namedtuple('vehicle',
                                 ['typeid', 'name', 'maxVol', 'maxWei', 'maxNum', 'maxRange', 'chargTm', 'unitCost',
                                  'viechleCost'])
        self.vehicle[1] = vehicleInfo(1, 'IVECO', 12, 2, 500, 100000, 30, 0.012, 200)
        self.vehicle[2] = vehicleInfo(2, 'TRUCK', 16, 2.5, 500, 120000, 30, 0.014, 300)


if __name__ == '__main__':
    d_file = 'data/inputdistancetime_5_1201.txt'
    n_file = 'data/inputnode_5_1201.xlsx'

    problem_data = ProblemData(d_file, n_file,51101, 51200)
    print(problem_data.customer[50001])
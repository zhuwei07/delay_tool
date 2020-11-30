import sys
import pandas as pd
import matplotlib.pyplot as plt
from pandas import DataFrame
from openpyxl import Workbook, load_workbook

# csv文件的路径  --  需要手动修改
excel_file = 'Order.csv'

# 结果文件
result_file = 'Delay.xlsx'

# 读取的列 -- 从原始Order.csv表格中获取相关信息的列
colums = ['BrokerID', 'ExchangeID', 'OrderSysID', 'UserID', 'InstrumentID', 'TradingDay',
          'ClientID', 'SeatID', 'InsertTime', 'IPAddress', 'MacAddress', 'FTdRecvDown',
          'CoreRecvDown', 'CoreSendUp', 'CoreRecvUp', 'CoreSendDown', 'FTdSendDown']


# 核心延时 (超内模式)
def GetKernelDelay(data):
    """
    des: 获取核心延时
    param: data 获取有效列后的数据
    return: 核心延时列
    rules: CoreSendUp - CoreRecvDown 若存在任何一项为0，则忽略该行数据，并置位NULL
    """
    data["SuperDelay"] = data["CoreSendUp"] - data["CoreRecvDown"]
    data.loc[(data["CoreSendUp"] == 0) | (data["CoreRecvDown"] == 0), 'PenetrateDelayMix'] = "NULL"

    return data


# 穿透延时 (混合模式)
def GetPenetrateDelayMix(data):
    """
    des: 获取穿透延时 混合模式
    param: data 获取有效列后的数据
    return: 穿透延时列
    rules: 1.FTdRecvDown != 0: CoreSendUp - FTdRecvDown
           2.FTdRecvDown = 0: CoreSendUp - CoreRecvDown
           默认 CoreSendUp 和 CoreRecvDown不为0
    """
    data["PenetrateDelayMix"] = data["CoreSendUp"] - data["FTdRecvDown"]
    data.loc[data["FTdRecvDown"] == 0, 'PenetrateDelayMix'] = \
        data["CoreSendUp"] - data["CoreRecvDown"]

    return data


# 穿透延时 (tcp)
def GetPenetrateDelayTcp(data):
    """
    des: 获取穿透延时 tcp
    param: data 获取有效列后的数据
    return: 穿透延时列
    rules: 1.FTdRecvDown != 0: CoreSendUp - FTdRecvDown
           2.FTdRecvDown = 0: NULL
           默认 CoreSendUp 和 CoreRecvDown不为0
    """
    data["PenetrateDelayTcp"] = data["CoreSendUp"] - data["FTdRecvDown"]
    data.loc[data["FTdRecvDown"] == 0, 'PenetrateDelayTcp'] = "NULL"

    return data


def excelAddSheet(dataframe, excelWriter, sheetName):
    """
    表中新增sheet页
    """
    # book = load_workbook(excelWriter.path)
    # excelWriter.book = book
    dataframe.to_excel(excel_writer=excelWriter, sheet_name=sheetName, index=None)
    excelWriter.close()


# 计算三种延时的平均值、最大值、最小值，并区分交易所分成多个sheet页
def EvalResultAndGenSheets(data):
    # 创建ExcelWriter 对象
    excelWriter = pd.ExcelWriter(result_file, engine='openpyxl')
    # 将原始数据生成为第一个sheet页
    df = pd.DataFrame(data)
    excelAddSheet(df, excelWriter, 'Order')
    # df.to_excel(result_file, index=False, header=False)

    Exchange = data["ExchangeID"].unique()
    # 创建sheet页的内容(每个sheet页的内容一致，只有标签不一致)
    entity = ["statistics", "SuperDelay", "PenetrateDelayMix", "PenetrateDelayTcp"]
    for sheetName in Exchange:
        mean_value = ["Mean"]
        max_value = ["Maximum"]
        min_value = ["Minimum"]
        for delay in ["SuperDelay", "PenetrateDelayMix", "PenetrateDelayTcp"]:
            # 每个sheet页的内容
            # 平均值
            mean_value.append(data.loc[(data["ExchangeID"] == sheetName) & (data[delay] != "NULL"), delay].mean())
            max_value.append(data.loc[(data["ExchangeID"] == sheetName) & (data[delay] != "NULL"), delay].max())
            min_value.append(data.loc[(data["ExchangeID"] == sheetName) & (data[delay] != "NULL"), delay].min())

        dataSet = [entity, mean_value, max_value, min_value]
        df_new = pd.DataFrame(dataSet)
        excelAddSheet(df_new, excelWriter, sheetName)



def PlotDelay(data, left_vale, right_value, description):
    """
    description: 画图(内部穿透延时)
    param:  data - csv原始数据
    """
    data["Inner_penetration_delay"] = data[right_value] - data[left_vale]
    df = DataFrame(data)
    inter_delay = df.iloc[:, -1] / 1000  # 转换成微妙
    plt.figure()
    inter_delay.plot()
    plt.rcParams['font.sans-serif'] = ['SimHei']
    plt.ylabel(description)
    plt.xlabel('订单号')


def PlotAnalysisRes(data, left_vale, right_value):
    """
    description: 统计内部穿透延时平均值/中位数，大于和小于平均值/中位数的个数
    """
    data["Inner_penetration_delay"] = data[right_value] - data[left_vale]
    df = DataFrame(data)
    inter_delay = df.iloc[:, -1] / 1000  # 转换成微妙

    larger_mean = inter_delay[inter_delay > inter_delay.mean()].size
    lower_mean = inter_delay[inter_delay < inter_delay.mean()].size
    larger_median = inter_delay[inter_delay > inter_delay.median()].size
    lower_median = inter_delay[inter_delay < inter_delay.median()].size
    plt.figure()
    plt.rcParams['font.sans-serif'] = ['SimHei']
    name_list = ["平均值: %.3f" % inter_delay.mean(), "中位数: %s" % inter_delay.median()]

    num_list = [lower_mean, lower_median]
    num_list1 = [larger_mean, larger_median]
    x = list(range(len(num_list)))
    total_width, n = 0.8, 2
    width = total_width / n

    plt.bar(x, num_list, width=width, label='小于', fc='g')
    for a, b in zip(x, num_list):
        plt.text(a, b + 0.05, '%.0f' % b, ha='center', va='bottom', fontsize=11)
    for i in range(len(x)):
        x[i] = x[i] + width
    plt.bar(x, num_list1, width=width, label='大于', fc='r')
    for a, b in zip(x, num_list1):
        plt.text(a, b + 0.05, '%.0f' % b, ha='center', va='bottom', fontsize=11)

    plt.ylabel('订单数')
    plt.xticks([a - width / 2 for a in x], name_list)
    plt.legend()


if __name__ == "__main__":
    ret = pd.read_csv(excel_file, usecols=colums)
    data = GetKernelDelay(ret)
    data = GetPenetrateDelayMix(data)
    data = GetPenetrateDelayTcp(data)

    print(data)

    EvalResultAndGenSheets(data)

    # PlotDelay(ret, 'CoreRecvDown', 'CoreSendUp', '内部穿透延时/微妙')

    # PlotAnalysisRes(ret, 'CoreRecvDown', 'CoreSendUp')

    # PlotDelay(ret, 'FTdRecvDown', 'CoreRecvDown', 'QDP API延时/微妙')

    # PlotAnalysisRes(ret, 'FTdRecvDown', 'CoreRecvDown')

    # PlotDelay(ret, 'FTdRecvDown', 'CoreSendUp', 'UDP 上行总延迟/微妙')

    # PlotAnalysisRes(ret, 'FTdRecvDown', 'CoreSendUp')

    # PlotDelay(ret, 'CoreSendUp', 'CoreRecvUp', '撮合成交延迟/微妙')

    # PlotAnalysisRes(ret, 'CoreSendUp', 'CoreRecvUp')

    # plt.show()

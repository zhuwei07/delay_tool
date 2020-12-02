#!/usr/bin/env python
# -*- coding:utf-8 -*-
import matplotlib.pyplot as plt
import os
import pandas as pd
from pandas import DataFrame
import openpyxl
from openpyxl.drawing.image import Image

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
    return: 核心延时列 微秒
    rules: CoreSendUp - CoreRecvDown 若存在任何一项为0，则忽略该行数据，并置位NULL
    """
    data["SuperDelay"] = (data["CoreSendUp"] - data["CoreRecvDown"])
    data.loc[(data["CoreSendUp"] == 0) | (data["CoreRecvDown"] == 0), 'SuperDelay'] = "NULL"

    return data


# 穿透延时 (混合模式)
def GetPenetrateDelayMix(data):
    """
    des: 获取穿透延时 混合模式
    param: data 获取有效列后的数据
    return: 穿透延时列 微秒
    rules: 1.FTdRecvDown != 0: CoreSendUp - FTdRecvDown
           2.FTdRecvDown = 0: CoreSendUp - CoreRecvDown
           默认 CoreSendUp 和 CoreRecvDown不为0
    """
    data["PenetrateDelayMix"] = (data["CoreSendUp"] - data["FTdRecvDown"])
    data.loc[data["FTdRecvDown"] == 0, 'PenetrateDelayMix'] = \
        data["CoreSendUp"] - data["CoreRecvDown"]

    # 若CoreSendUp和CoreRecvDown都为0，则忽略该行数据
    data.loc[(data["CoreSendUp"] == 0) & (data["CoreRecvDown"] == 0), 'PenetrateDelayMix'] = "NULL"

    return data


# 穿透延时 (tcp)
def GetPenetrateDelayTcp(data):
    """
    des: 获取穿透延时 tcp
    param: data 获取有效列后的数据
    return: 穿透延时列 纳秒
    rules: 1.FTdRecvDown != 0: CoreSendUp - FTdRecvDown
           2.FTdRecvDown = 0: NULL
           默认 CoreSendUp 和 CoreRecvDown不为0
    """
    data["PenetrateDelayTcp"] = (data["CoreSendUp"] - data["FTdRecvDown"])
    data.loc[data["FTdRecvDown"] == 0, 'PenetrateDelayTcp'] = "NULL"

    # 若CoreSendUp和CoreRecvDown都为0，则忽略该行数据
    data.loc[(data["CoreSendUp"] == 0) & (data["CoreRecvDown"] == 0), 'PenetrateDelayTcp'] = "NULL"

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
    # entity = ["statistics", "SuperDelay", "PenetrateDelayMix", "PenetrateDelayTcp"]
    for sheetName in Exchange:
        mean_value = ["平均值(纳秒)"]
        max_value = ["最大值(纳秒)"]
        min_value = ["最小值(纳秒)"]
        std_value = ["标准差(纳秒)"]
        for delay in ["SuperDelay", "PenetrateDelayMix", "PenetrateDelayTcp"]:
            # 每个sheet页的内容
            # 平均值
            mean_value.append(data.loc[(data["ExchangeID"] == sheetName) & (data[delay] != "NULL"), delay].mean())
            max_value.append(data.loc[(data["ExchangeID"] == sheetName) & (data[delay] != "NULL"), delay].max())
            min_value.append(data.loc[(data["ExchangeID"] == sheetName) & (data[delay] != "NULL"), delay].min())
            std_value.append(data.loc[(data["ExchangeID"] == sheetName) & (data[delay] != "NULL"), delay].std())

        dataSet = [mean_value, max_value, min_value, std_value]
        df_new = pd.DataFrame(dataSet)
        df_new.rename(columns={0: '统计结果', 1: '核心延时', 2: '穿透延时-混合模式', 3: '穿透延时-tcp'}, inplace=True)
        excelAddSheet(df_new.round(), excelWriter, sheetName)   # 取了结果的整数(四舍五入)



def SubPlotDelay(data):
    """
    description: 画图(3种类型穿透延时的分布图)
    param:  data 包含新增列的3种延时数据
    rules: 按照交易所分类分别插入对应的sheet页中
    """
    # 读取结果文件xlsx的所有sheet页
    wb = openpyxl.load_workbook(result_file)

    Exchange = data["ExchangeID"].unique()
    for sheetName in Exchange:
        data1 = data.loc[(data["ExchangeID"] == sheetName) & (data["SuperDelay"] != "NULL"), "SuperDelay"]
        data2 = data.loc[(data["ExchangeID"] == sheetName) & (data["PenetrateDelayMix"] != "NULL"), "PenetrateDelayMix"]
        data3 = data.loc[(data["ExchangeID"] == sheetName) & (data["PenetrateDelayTcp"] != "NULL"), "PenetrateDelayTcp"]

        df1 = DataFrame(data1)
        df2 = DataFrame(data2)
        df3 = DataFrame(data3)
        df1['序号'] = range(len(df1))
        df2['序号'] = range(len(df2))
        df3['序号'] = range(len(df3))
        # df1.rename(columns={0: 'x', 1: 'SuperDelay'}, inplace=True)
        # df2.rename(columns={0: 'x', 1: 'PenetrateDelayMix'}, inplace=True)
        # df3.rename(columns={0: 'x', 1: 'PenetrateDelayTcp'}, inplace=True)

        # 画图保存
        fig = plt.figure(figsize=(20, 15))
        y_major_locator = plt.MultipleLocator(2000)
        # y_minor_locator = plt.MultipleLocator(1000)
        count_null = 0
        if df1.empty is True:
            count_null = count_null + 1
        if df2.empty is True:
            count_null = count_null + 1
        if df3.empty is True:
            count_null = count_null + 1
        if count_null == 3:
            print("Exchange" + sheetName + "all the result is null, no data to plot")
            continue

        # 子图的个数
        fig_num = 3 - count_null
        pos = 0  # 记录图的位置
        if df1.empty is False:
            pos = pos + 1
            ax1 = fig.add_subplot(fig_num, 1, pos)
            ax1.yaxis.set_major_locator(y_major_locator)
            # ax1.yaxis.set_minor_locator(y_minor_locator)
            df1.plot.scatter(ax=ax1, x='序号', y='SuperDelay')
            # plt.ylim((0, 100000))
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.ylabel('核心延时(纳秒)')
        if df2.empty is False:
            pos = pos + 1
            ax2 = fig.add_subplot(fig_num, 1, pos)
            ax2.yaxis.set_major_locator(y_major_locator)
            # ax2.yaxis.set_minor_locator(y_minor_locator)
            df2.plot.scatter(ax=ax2, x='序号', y='PenetrateDelayMix')
            # plt.ylim((0, 100000))
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.ylabel('穿透延时-混合模式(纳秒)')
        if df3.empty is False:
            pos = pos + 1
            ax3 = fig.add_subplot(fig_num, 1, pos)
            ax3.yaxis.set_major_locator(y_major_locator)
            # ax3.yaxis.set_minor_locator(y_minor_locator)
            df3.plot.scatter(ax=ax3, x='序号', y='PenetrateDelayTcp')
            # plt.ylim((0, 100000))
            plt.rcParams['font.sans-serif'] = ['SimHei']
            plt.ylabel('穿透延时-tcp(纳秒)')
        # plt.xlabel('序号')
        plt.savefig(sheetName + ".png", dpi=500, bbox_inches='tight')

        # 读取结果文件的sheet页，并将图片插入到对应sheet页中
        sheet = wb[sheetName]
        print(sheet)
        fig_name = sheetName + ".png"
        img = Image(fig_name)
        newsize = (1000, 750)
        img.width, img.height = newsize
        sheet.add_image(img, "A10")
    wb.save(result_file)


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


def ClearFig(dir):
    for root, dirs, files in os.walk(dir):
        for name in files:
            if name.endswith(".png"):
                os.remove(os.path.join(root, name))
                print("Delete figs: " + os.path.join(root, name))

if __name__ == "__main__":
    ret = pd.read_csv(excel_file, usecols=colums)
    data = GetKernelDelay(ret)
    data = GetPenetrateDelayMix(data)
    data = GetPenetrateDelayTcp(data)

    print(data)

    EvalResultAndGenSheets(data)

    SubPlotDelay(data)

    # PlotDelay(ret, 'CoreRecvDown', 'CoreSendUp', '内部穿透延时/微妙')

    # PlotAnalysisRes(ret, 'CoreRecvDown', 'CoreSendUp')

    # PlotDelay(ret, 'FTdRecvDown', 'CoreRecvDown', 'QDP API延时/微妙')

    # PlotAnalysisRes(ret, 'FTdRecvDown', 'CoreRecvDown')

    # PlotDelay(ret, 'FTdRecvDown', 'CoreSendUp', 'UDP 上行总延迟/微妙')

    # PlotAnalysisRes(ret, 'FTdRecvDown', 'CoreSendUp')

    # PlotDelay(ret, 'CoreSendUp', 'CoreRecvUp', '撮合成交延迟/微妙')

    # PlotAnalysisRes(ret, 'CoreSendUp', 'CoreRecvUp')
    # plt.show()

    ClearFig('.')

#!/usr/bin/env python
# -*- coding:utf-8 -*-
"""
运行此脚本，python 需要添加到本地环境变量
"""
import os


def main():
    # inpath = input('please input install packages parents path: ')
    inpath = 'packages'  # 存放所有包的总文件
    path_parent = os.listdir(inpath)
    path_parent.sort()  # install 时，path_parent 下文件夹有优先级顺序
    os.system(" python -m pip install --upgrade pip")
    for sub_parent in path_parent:
        sub_parent = os.path.join(inpath, sub_parent)
        for root1, dirs1, files1 in os.walk(sub_parent):  # 递归遍历总文件夹下所有文件（包括子文件夹下文件）
            for files2 in files1:
                # 安装'.tar.gz', '.whl', '.zip'三种格式 packages (已下载本地)
                if files2[-7:] == '.tar.gz' or files2[-4:] == '.whl' or files2[-4:] == '.zip':
                    print(files2)
                    try:
                        os.system(" pip install " + os.path.join(root1, files2))  # main code
                    except:
                        print("failed install  {}".format(files2))

                # 安装 txt 文件中 packages (未下载到本地，仅包的名及对应的版本)
                elif files2[-4:] == '.txt':
                    # 方式1：批量安装 txt 文本中的包
                    # os.system("pip install -r " + os.path.join(root1, files2))

                    # 方式2：逐行读取，打印安装信息
                    requirements_txt = open(os.path.join(root1, files2), "r")
                    for line in requirements_txt.readlines():
                        os.system("pip install " + line)


if __name__ == '__main__':
    main()
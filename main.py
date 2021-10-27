# -*- coding: utf-8 -*-
# @Time    : 2021/10/27 8:13
# @Author  : Xcy.小相
# @Site    :
# @File    : tesy.py
# @Software: PyCharm

import queue
import random
import threading
from lxml import etree
import requests
import os
import re
import ctypes, sys


agents = [
    'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.8.1.11) Gecko/20071127 Firefox/2.0.0.11',
    'Opera/9.25 (Windows NT 5.1; U; en)',
    'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; SV1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
    'Mozilla/5.0 (compatible; Konqueror/3.5; Linux) KHTML/3.5.5 (like Gecko) (Kubuntu)',
    'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.8.0.12) Gecko/20070731 Ubuntu/dapper-security Firefox/1.5.0.12',
    'Lynx/2.8.5rel.1 libwww-FM/2.14 SSL-MM/1.4.1 GNUTLS/1.2.9',
    'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.7 (KHTML, like Gecko) Ubuntu/11.04 Chromium/16.0.912.77 Chrome/16.0.912.77 Safari/535.7',
    'Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:10.0) Gecko/20100101 Firefox/10.0',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4592.0 Safari/537.36 Edg/94.0.975.1',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.159 Safari/537.36',
]

URL = "http://ping.chinaz.com/iframe.ashx?t=ping"
data = {
    'guid': '',
    'host': 'github.com',
    'ishost': 0,
    'isipv6': 0,
    'encode': 'K8DHlwTCBOt4UlXkvb|1ICGH0YcnzhQ9',
    'checktype': 0
}


def get_guid(global_url):
    headers = {"User-Agent": random.choice(agents)}
    response = requests.get(global_url, headers=headers).text
    root = etree.HTML(response)
    guid = root.xpath(
        '//div[contains(@class,"row ") and contains(@class,"listw ")and contains(@class,"tc")and contains(@class,"clearfix")]/@id')
    ping_location = root.xpath(
        '//div[contains(@class,"row ") and contains(@class,"listw ")and contains(@class,"tc")and contains(@class,"clearfix")]/div[1]/text()')
    return zip(guid, ping_location)


def speed_test(guid, location):
    """
    测量该guid对应的ip响应速度
    :param guid: guid
    :param location: guid对应的地址位置
    :return:
         - ip：guid对应的ip
         - ipaddress：该ip的实际地址位置
         - responsetime：ping值响应时间
    """
    headers = {"User-Agent": random.choice(agents)}
    data["guid"] = guid
    response = requests.post(url=URL, data=data, headers=headers).text
    if ("state:0" in response):
        print("guid错误！")
        return None, None, None
    else:
        print('\n正在ping线路======>>>' + location + ',请稍等……')
        ip = re.search(r"((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}",
                       response).group()
        print("\tip:\t" + ip)
        ipaddress = \
            re.search(r"ipaddress:'.*',responsetime", response).group().replace(",", ":").replace("'", "").split(":")[1]
        print("\tipaddress:\t" + ipaddress)
        responsetime = \
            re.search(r"responsetime:.*,ttl", response).group().replace(",", ":").replace("'", "").split(":")[1][:-2]
        try:
            responsetime = int(responsetime)
        except:
            responsetime = -1
        print("\tresponsetime:\t" + str(responsetime))

        return ip, ipaddress, responsetime


def change_host_conf(data_list):
    """
    更改（添加）当前主机的hosts文件(域名解析文件)，若原有的Host文件中已经含有关于github中的dns解析数据，那么将会删除该部分数据
    :param ip:ping值最小的ip地址
    """
    host_path = 'C:\\WINDOWS\\System32\\drivers\\etc\\hosts'
    flag = os.path.exists(host_path)
    if flag == False:
        choose = input("Hosts域名解析文件不存在，是否要创建？[YES/no]")
        if choose == "no":
            print("程序已退出！")
            input()
            exit()

    text = ""
    with open(host_path, "r+", encoding="utf-8")as f:
        for line in f:
            if "github" in line:
                continue
            text = text + line
    text = text + "#===========Add by Python script github  start=========\n"
    temp_ip = "127.0.0.1"
    for ip,ipaddress,responsetime in tuple(data_list):
        if ip != temp_ip:
            temp_ip = ip
            text = text + ip + "\tgithub.com\n"
            text = text + ip + "\tgithub.github.io\n"
    text = text + "#===========Add by Python script github  end===========\n"

    with open(host_path, "w+", encoding="utf-8")as f_new:
        f_new.write(text)

def is_admin():
    """
    判断是否具有管理员权限
    :return:
    """
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False


def speed_multithreading(dataQueue, guids_list):
    """
    对传入的guids进行ping测试,并将测试结果存入dataQueue
    :param dataQueue: 队列（线程安全）
    :guids_lists: 传入的guids列表
    """
    for guid, location in guids_list:
        ip, ipaddress, responsetime = speed_test(guid, location)
        if ip != None and responsetime != -1:
            data = [ip, ipaddress, responsetime]
            dataQueue.put(data)


def list_of_groups(init_list, childern_list_len):
    '''
    init_list为初始化的列表，childern_list_len初始化列表中的几个数据组成一个小列表
    :param init_list:
    :param childern_list_len:
    :return:
    '''
    list_of_group = zip(*(iter(init_list),) * childern_list_len)
    end_list = [list(i) for i in list_of_group]
    count = len(init_list) % childern_list_len
    end_list.append(init_list[-count:]) if count != 0 else end_list
    return end_list


if __name__ == '__main__':

    if is_admin():
        speed_max_data = list()
        dataQueue = queue.Queue()
        threadList = list()

        guids = get_guid("http://ping.chinaz.com/github.com")
        guids_lists = list_of_groups(list(guids), 5)
        for guids_list in guids_lists:
            t = threading.Thread(target=speed_multithreading, args=(dataQueue, guids_list))
            threadList.append(t)

        # 开始所有线程
        for t in threadList:
            t.start()
        # 控制主线程等待所有子线程结束后再向下执行
        for t in threadList:
            t.join()
        # best_responsetime = 10000
        # best_ip = ""
        # best_ipaddress = ""
        data_list = list()
        for _ in range(dataQueue.qsize()):
            data_list.append(dataQueue.get())
        for i in range(len(data_list)):
            for j in range(i,len(data_list)):
                if data_list[i][2]>data_list[j][2]:
                    data_list[i][2],data_list[j][2] = data_list[j][2],data_list[i][2]


        try:
            change_host_conf(data_list)
            print("\n\n==================GithubHostsHelper=========================")
            print("\n")
            print("\t线路已更换成功，欢迎再次使用！最优路线为：")
            print("\t\t*ip:" + data_list[0][0] + "\t\t\t\t")
            print("\t\t*address:" + data_list[0][1] + "\t\t\t")
            print("\t\t*responseTime:" + str(data_list[0][2]) + "毫秒\t\t\t\t")
            print("\n")
            print("\t\t\t\t\t Create By xcy.小相")
            print("\t https://github.com/xcyxiaoxiang/GithubHostsHelper")
            print("============================================================")

            input()
        except Exception as e:
            print(e)
            print("线路更改失败，请重试！")
    else:
        ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, __file__, None, 1)

import requests as req  # 发送请求的库
import bs4
from bs4 import BeautifulSoup  # 导入bs4库
import re  # 正则库
import pandas as pd


def crawler(url, id_reg=None):
    # 1. 获取url页面
    res = req.get(url)
    if res.status_code != 200:
        raise Exception(f"状态码为{res.tatus_code}，爬取失败！")
    res.encoding = "UTF-8"
    # print(res.text)

    # 2. 构造Beautiful Soup对象
    soup = BeautifulSoup(res.text, fromEncoding="UTF-8", features="lxml")
    # print(soup.prettify())

    # 3. 获取页面中id满足id_reg正则式的标签
    ret = soup.find_all(id=re.compile(id_reg))
    # soup.find_all(lambda tag : tag.get("class") == ["ds"]) # 查找class为ds的标签

    return ret


#=========================爬取重大计算机学院硕士导师信息=========================#
excel_cols = ["姓名", "职称", "研究方向", "联系方式", "导师主页"]  # 信息字段
teachers_info = pd.DataFrame(columns=excel_cols)  # 创建dataframe，存储所有导师信息

UNIVERSE_URL = "http://www.cs.cqu.edu.cn"  # 重庆大学官网主页地址
BASE_URL = "http://www.cs.cqu.edu.cn/xbwz/szdw/sssds"  # 重大硕导信息的根地址

# 分页获取导师信息
urls = [f"{BASE_URL}.htm"]  # 首页
urls.extend([f"{BASE_URL}/{x}.htm" for x in range(1, 9)])  # 其他页面
ID_REG = "line_u7_"  # 观察页面结构，发现导师信息存储在id满足正则式"line_u7_"的li标签中

for url in urls:
    result = crawler(url, ID_REG)
    for item in result:  # 每个item是一个老师的所有信息
        dsts = item.descendants  # 取出其所有子标签
        dsts = [dst for dst in dsts if not (
            dst == "" or dst == "\n")]  # 除去空串、空行
        dsts = [dst for dst in dsts if dst.name == "a" or isinstance(
            dst, bs4.element.NavigableString)]  # 除去不是a标签的标签
        """
        过滤之后，内容eg:
        <a href="../../../info/1275/4842.htm"><img src="/__local/E/CF/95/76C8EBA8C30D23154A8D2AAED6C_5613D891_8A4E6.jpg"/></a>
        <a href="../../../info/1275/3791.htm">姓名：何中市</a>
        姓名：冯磊
        职位：教授
        研究方向：机器学习，数据挖掘，人工智能
        联系方式：lfeng@cqu.edu.cn
        """
        # 解析每个导师的信息，存入dataframe。导师主页地址在a标签中，单独解析
        atag_url, other_info = dsts[1], dsts[2:]  # 解包，将a标签和其他信息分开

        teacher_info = []
        teacher_info.extend([x.split("：")[-1].strip()
                            for x in other_info])  # 取出每个信息冒号右边的部分

        # 获取a标签的href属性的统一后缀，比如../../../info/1275/3791.htm取出1275/5244.htm
        url_suffix = atag_url.get("href").split("info/")[-1]
        # 拼接统一前缀，得到导师主页地址
        teacher_home_url = f"{UNIVERSE_URL}/info/{url_suffix}"
        teacher_info.append(teacher_home_url)

        teachers_info = teachers_info.append(pd.DataFrame(
            [teacher_info], columns=excel_cols))  # 将该导师所有信息存入dataframe

teachers_info.to_excel("计算机硕导列表.xlsx", index=False)

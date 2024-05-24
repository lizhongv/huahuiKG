import os
import requests
import re
import shutil
import pandas as pd
import numpy as np

from lxml import etree
from time import sleep
from urllib.parse import urljoin, urlencode

file_dir = os.path.abspath(os.path.dirname(__file__))
os.chdir(file_dir)

# 新建文件夹，用于存储数据
data_dir = "../data"
url = 'http://www.aihuhua.com'

"""
用来模拟浏览器发送HTTP请求时的请求头部信息，可以更好地伪装成浏览器访问网站，以避免被网站封禁或限制访问。
"""
headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Cookie': 'acw_tc=6f2ab82e17015859125771363e0a206aae5bccf7f953e2803a570cbba7; cdn_sec_tc=6f2ab82e17015859125771363e0a206aae5bccf7f953e2803a570cbba7; PHPSESSID=32g5vhi8aek88fmruvcsi9ad03; T3_lang=zh-cn; Hm_lvt_2f9621f6b3c69c2c113bd7255bdaea02=1701585915; Hm_lpvt_2f9621f6b3c69c2c113bd7255bdaea02=1701586759',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0',
}

title_class = []  # '花卉类别', '花卉功能', '应用环境', '盛花期_习性', '养护难度'
page_size = [0, 12, 20, 34, 42, 46]  # 页面范围：根据每个title下，类别多少设定的
flower_class = []  # 花卉类别
belong_class = ['界', '门', '纲', '目', '科', '属', '种']

# 界门纲目科属种
Kingdom, Phylum, Class, Order, Family, Genus, Species = [], [], [], [], [], [], []


def construct_title_class(base_html):
    global title_class
    # 将 "盛花期 / 习性" -> 修改为  "盛花期_习性"
    title_class = re.findall('<h2 class="title " title="(.*?)">', base_html)
    content = re.findall(
        '<li><a href="(.*?)" class="a " title="(.*?)" target="_self">', base_html)

    if os.path.exists(data_dir):
        for root, dirs, files in os.walk(data_dir, topdown=False):
            for f in files:
                os.remove(os.path.join(root, f))
            for d in dirs:
                shutil.rmtree(os.path.join(root, d))
        print(">>> 数据文件夹清空完毕！")
    else:
        os.makedirs(data_dir)
        print(">>> 创建新的数据文件夹!")

    # 创建花卉大全文件
    with open(os.path.join(data_dir, '花卉大全.txt'), 'w', encoding='utf-8') as fw:
        id = 0
        for i in range(len(title_class)):
            title_class[i] = title_class[i].replace(
                ' / ', '_')  # 盛花期 / 习性 => 盛花期_习性
            # 创建title文件夹，其中包含各自小类别
            path = os.path.join(data_dir, title_class[i])
            if not os.path.exists(path):
                os.makedirs(path)

            # 每个title下，包含着多个类别，对应着context中位置
            for j in range(page_size[i], page_size[i + 1]):
                href, title = url + content[j][0], content[j][1]
                fw.write(str(id) + '\t' + href + '\t' + title + '\n')
                id += 1
    print(">>> title类别文件夹构建完毕!")


def crawl_page_content():
    with open(os.path.join(data_dir, '花卉大全.txt'), 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # h1 爬取每个标题
    ALL_INDEX = 0
    for i in range(len(title_class)):
        print(f">>> 开始爬取-{title_class[i]}...")

        # h2 爬取每个类别
        for j in range(page_size[i], page_size[i + 1]):
            type_examples = []
            _, url, name = lines[j].split()
            print(f">>> 开始爬取-{name}...")

            # h3 爬取每个页面
            page_idx = 1
            while True:  # NOTE 循环爬取页面，直至最后一页
                page_url = url + 'page-' + str(page_idx) + '.html'
                page_html = requests.get(page_url, headers=headers)

                if page_html.status_code == 200:
                    print(f"爬取-page-{page_url}-成功")
                    page_text = page_html.text

                    # NOTE 用于判断是否尾最后一页
                    end = re.findall('class=\'next\'>下一页</a></div>', page_text)

                    # h4 爬取每张图片
                    picture_urls = re.findall(
                        '<a class="title" target="_blank" title="(.*?)" href="(.*?)">(.*?)</a>', page_text)
                    for p_url in picture_urls:
                        res = requests.get(p_url[1], headers=headers)
                        if res.status_code == 200:
                            print(f"|-爬取-picture-{p_url[0]}-成功")
                            example = {}
                            text = res.text

                            another_name = re.findall(
                                '<label class="cate">别名：(.*?)</label>', text)
                            img = re.findall(
                                '<img width="140" alt="(.*?)" title="(.*?)" src="(.*?)"', text)
                            img_link = img[0][2] if len(
                                img) > 0 and len(img[0]) >= 2 else '无'

                            example['id'] = str(ALL_INDEX)
                            example['flower_name'] = p_url[0]
                            example['another_name'] = another_name[0] if len(
                                another_name) > 0 else "无"
                            example['img_link'] = img_link

                            # 一共有3个中心点：花卉大全、分类、科属。所以数据分别统计，而不是每个花卉统计
                            # 分类：有自己的中心点
                            flower_class_get = re.findall(
                                '<label class="cate">分类：<a href="(.*?)" title="(.*?)" target="_blank">(.*?)</a></label>', text)
                            example["type"] = flower_class_get[0][2] if len(
                                flower_class_get) > 0 and len(flower_class_get[0]) >= 2 else ""
                            if len(flower_class_get) > 0 and len(flower_class_get[0]) >= 2 and flower_class_get[0][2] not in flower_class:
                                flower_class.append(flower_class_get[0][2])

                            # 科属：有自己的中心点
                            belong = re.findall(
                                '<label class="cate">科属：(.*?)</label>', text)
                            example["belong"] = belong[0] if len(
                                belong) > 0 else ""
                            if len(belong) > 0 and len(belong[0]) > 0:
                                get_belongs(belong)

                            open_time_get = re.findall(
                                '<label class="cate">盛花期：<a title="(.*?)" target="_blank" href="(.*?)">(.*?)</a>', text)
                            open_time = open_time_get[0][-1] if len(
                                open_time_get) > 0 else "四季"
                            example['open_time'] = open_time

                            cmp = re.compile(
                                '<p class="desc">(.*?)</p>', re.DOTALL)
                            desc = ' '.join(re.findall(cmp, text)[0].split())
                            example['dsc'] = desc if len(desc) > 0 else "无"

                            type_examples.append(example)
                            ALL_INDEX += 1
                        else:
                            print(f'|-爬取-picture-{p_url[0]}-失败')
                        pass
                    # h4 爬取每张图片结束

                    # NOTE 若最后一页，退出该类别爬取
                    if len(end) <= 0:
                        break
                    pass
                else:
                    print(f'爬取-page-{page_url}-失败')
                    break  # NOTE 当爬取页面失败时，后续页面也不在爬取

                page_idx += 1
                pass
            # h3 爬取每个页面结束

            print(f'>>> 爬取-{name}-完成')
            save_pd(type_examples, title_class[i], name)
        # h2 爬取每个类别结束

        print(f">>> 爬取-{title_class[i]}-完成")
        # sleep(10)
        # break
    # h1 爬取每个标题结束

    # 保存分类
    with open(os.path.join(data_dir, '种类.txt'), 'w', encoding='utf-8') as fw:
        for key in flower_class:
            fw.write(key + '\n')
    print('>>> 成功保存花卉的分类!')

    # 保存科属
    save_belongs()
    print('>>> 成功保存花卉的科属!')


def save_pd(examples, title, name):
    data_columns = {
        'id': [d['id'] for d in examples],
        'flower_name': [d['flower_name'] for d in examples],
        'another_name': [d['another_name'] for d in examples],
        'img_link': [d['img_link'] for d in examples],
        'type': [d['type'] for d in examples],
        'belong': [d['belong'] for d in examples],
        'open_time': [d['open_time'] for d in examples],
        'dsc': [d['dsc'] for d in examples],
    }
    pd_data = pd.DataFrame(data_columns)
    pd_data.to_excel(os.path.join(data_dir, title, name + '.xlsx'))


def save_belongs():
    # 界门纲目科属种
    with open(os.path.join(data_dir, '界.txt'), 'w', encoding='utf-8') as fw:
        for l in Kingdom:
            fw.write(l + '\n')

    with open(os.path.join(data_dir, '门.txt'), 'w', encoding='utf-8') as fw:
        for l in Phylum:
            fw.write(l + '\n')

    with open(os.path.join(data_dir, '纲.txt'), 'w', encoding='utf-8') as fw:
        for l in Class:
            fw.write(l + '\n')

    with open(os.path.join(data_dir, '目.txt'), 'w', encoding='utf-8') as fw:
        for l in Order:
            fw.write(l + '\n')

    with open(os.path.join(data_dir, '科.txt'), 'w', encoding='utf-8') as fw:
        for l in Family:
            fw.write(l + '\n')

    with open(os.path.join(data_dir, '属.txt'), 'w', encoding='utf-8') as fw:
        for l in Genus:
            fw.write(l + '\n')

    with open(os.path.join(data_dir, '种.txt'), 'w', encoding='utf-8') as fw:
        for l in Species:
            fw.write(l + '\n')


def get_belongs(belongs):
    belong_line = belongs[0].split()
    for temp in belong_line:
        if '界' in temp and temp not in Kingdom:
            Kingdom.append(temp)
        elif '门' in temp and temp not in Phylum:
            Phylum.append(temp)
        elif '纲' in temp and temp not in Class:
            Class.append(temp)
        elif '目' in temp and temp not in Order:
            Order.append(temp)
        elif '科' in temp and temp not in Family:
            Family.append(temp)
        elif '属' in temp and temp not in Genus:
            Genus.append(temp)
        elif '种' in temp and temp not in Species:
            Species.append(temp)
        else:
            pass
            # if temp[-1] not in belong_class:
            #     raise ValueError("Error: Does not belong to any of them.")


def main():
    home_url = 'http://www.aihuhua.com/hua/'
    home_file = 'home_html.txt'

    if os.path.exists(home_file):
        print(f">>> 加载保存的主页源码：{home_file}")
        with open(home_file, 'r', encoding='utf-8') as f:
            home_html = f.read()
    else:
        print(f">>> 爬取主页源码：{home_url}")
        try:
            res = requests.get(home_url, headers=headers)
            res.raise_for_status()
        except Exception as e:
            print(f">>> 爬取失败，发生异常 {e}")
            raise Exception(f"爬取失败，发生异常") from e
        # if res.status_code == 200:
        #     print(">>>>>>>>爬取成功!")

        with open(home_file, 'w', encoding='utf-8') as fw:
            fw.write(res.text)
        home_html = res.text

    construct_title_class(home_html)  # 建立分类文件
    crawl_page_content()  # 爬取详细词条

    print('finish...')


if __name__ == '__main__':
    main()

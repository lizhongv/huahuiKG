# 花卉知识图谱


## 1. 爬取数据

-  打开要爬取的网页
- *ctrl+shift+I* 打开开发者工具
- 选择网络*，ctrl+R*刷新
- 选择最上面的网址进行查看：User-Agent等
- 更新代码crawler/main.py中的*headers*和*url*



## 2. 对爬取的主页面进行处理

- 使用网页的源代码对 主页html 进行解析 或 对主页html进行格式化
- 使用 正则化方法提取响应的字段
- 爬取每个页面的内容，并保存



## 3. 开启neo4j服务

- 进入bin文件，输入cmd

<img src="https://img-blog.csdnimg.cn/da79539e247d41a796f339423b8bd88e.png?x-oss-process=image/watermark,type_d3F5LXplbmhlaQ,shadow_50,text_Q1NETiBA54ix5Y-R6aOZ55qE6JyX54mb,size_20,color_FFFFFF,t_70,g_se,x_16" alt="img" style="zoom:33%;" />



<img src="https://img-blog.csdnimg.cn/1532c08dc18847c8827f8bac4d36c180.png?x-oss-process=image/watermark,type_d3F5LXplbmhlaQ,shadow_50,text_Q1NETiBA54ix5Y-R6aOZ55qE6JyX54mb,size_20,color_FFFFFF,t_70,g_se,x_16" alt="img" style="zoom:33%;" />

- 开启服务：neo4j console
- 浏览器打开输入：用户名: neo4j  密码: 123456
- 关闭服务：neo4j stop

## 4. 创建图谱

- 运行createKG.py 创建图谱

  




# Cypher查询语言




[CQL](https://www.w3cschool.cn/neo4j/neo4j_cql_introduction.html)

[b站该项目教程](https://www.bilibili.com/video/BV1s44y1J7cG/?spm_id_from=333.337.search-card.all.click&vd_source=e8d035d27ac92c90b838a94cc2862646)
[该项目的Github](https://github.com/coderLCJ/NlpPractice/tree/main/KG_demo)

[Code Github](https://github.com/jm199504/Financial-Knowledge-Graphs)
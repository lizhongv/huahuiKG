from py2neo import Graph, Node, Relationship
import os

title_class = ['花卉类别', '花卉功能', '应用环境', '盛花期_习性', '养护难度']  # 总类别
page_size = [0, 12, 20, 34, 42, 46]  # 页面范围
data_dir = "./data"

def createEntity0(graph):
    # ------------------------------------------------------
    # step 0 总节点
    # ------------------------------------------------------
    cql = "CREATE (:花卉大全 {id: '0', name: '花卉大全'})"
    graph.run(cql)
    for i, c in enumerate(title_class):
        cql = '''
            MERGE (a {name: '花卉大全'}) 
            MERGE (b:花卉大全 {id:'%d', name:'%s'})
            MERGE (a)-[:划分]-> (b)
            ''' % (i + 1, c)
        graph.run(cql)
    print('step 0 done')

    # ------------------------------------------------------
    # step 1 类细分
    # ------------------------------------------------------
    with open(os.path.join(data_dir, '花卉大全.txt'), 'r', encoding='utf8') as file:
        lines = file.readlines()
    for i in range(5):
        for j in range(page_size[i], page_size[i + 1]):
            sub_class = lines[j].split()[-1]
            cql = '''
                MERGE (a {name: '%s'}) 
                MERGE (b:%s {id:'%d', name:'%s'})
                MERGE (a)-[:划分]-> (b)
                ''' % (title_class[i], title_class[i], j, sub_class)
            graph.run(cql)
    print('step 1 done')

    # ------------------------------------------------------
    # step 2 生成品种
    # ------------------------------------------------------
    cql = "CREATE (:花卉品种{id:'0', name:'花卉品种'})"  # id=0
    graph.run(cql)
    with open(os.path.join(data_dir, '种类.txt'), 'r', encoding='utf8') as file:
        lines = file.readlines()
    for i, l in enumerate(lines):
        l = l.strip()
        if len(l):
            cql = '''
                    MERGE (a {name: '花卉品种'})
                    MERGE (b:花卉品种 {id:'%d', name:'%s'})
                    MERGE (a)-[:划分]-> (b)
                ''' % (i+1, l)
            graph.run(cql)
    print('step 2 done')

    # ------------------------------------------------------
    # step 3 分界
    # ------------------------------------------------------
    belong = ['界', '门', '纲', '目', '科', '属', '种']
    for i, name in enumerate(belong):
        cql = 'CREATE (:生物学分支{id:\'%d\', name:\'%s\'})' % (i, name)
        graph.run(cql)
        if i > 0:
            cql = '''
                MERGE (a {name: '%s'})
                MERGE (b {name: '%s'})
                MERGE (a)-[:划分]-> (b)
                ''' % (belong[i - 1], belong[i])
            graph.run(cql)
    print('step 3 done')

    # --------------------------------------------------------
    # step 4 具体分支
    # --------------------------------------------------------
    p_id = 0
    for p in belong:
        path = os.path.join(data_dir,'科属', p + '.txt')
        with open(path, 'r', encoding='utf8') as f:
            lines = f.readlines()
        for line in lines:
            line = line.strip()
            if len(line) > 0 and p[0] == line[-1]:
                cql = '''
                    MERGE (a:具体分支 {id:'%d', name: '%s'})
                    MERGE (b {name: '%s'})
                    MERGE (a)-[:属于]-> (b)
                ''' % (p_id, line, p)
                graph.run(cql)
                p_id += 1
    print('step 4 done')
    print('Entity构造完成')


def createFlower(graph):
    with open(os.path.join(data_dir, '花卉大全.txt'), 'r', encoding='utf8') as f:
        all_class = f.readlines()
    delt = ['\'', ')', '(', '{', '}']

    for i, title in enumerate(title_class):
        # **************************************
        # ---------------每个标题----------------
        # **************************************
        for j in range(page_size[i], page_size[i + 1]):
            class_name = all_class[j].split()[-1]
            flower_path = os.path.join(data_dir,title, class_name + '.txt')
            with open(flower_path, 'r', encoding='utf8') as f:
                lines = f.readlines()
            # *************************************************
            # ------------------具体花卉------------------------
            # *************************************************
            for line in lines:
                if len(line.split('\t')) != 8:
                    print('error')
                    continue

                id, name, another_name, img, class_, belong, open_time, desc = line.split('\t')
                belongs = belong.split()
                belong_to = belongs[-1]
                for d in delt:
                    desc = desc.replace(d, ' ')
                    name = name.replace(d, ' ')
                    another_name = another_name.replace(d, ' ')

                cql = '''
                    MERGE (a:花卉 {id:\'%d\', name:\'%s\', 别名:\'%s\', 图片:\'%s\', 开花季节:\'%s\', 简介:\'%s\'})
                    MERGE (b:花卉品种 {name: '%s'})
                    MERGE (a)-[:归属]-> (b)
                    
                    MERGE (c:具体分支{name: '%s'})
                    MERGE (a)-[:属于]-> (c)
                    
                    MERGE (d:%s{name: '%s'})
                    MERGE (a)-[:归于]-> (d)
                ''' % (int(id), name, another_name, img, open_time, desc, class_,
                       belong_to,
                       title, class_name)
                graph.run(cql)

                for k, b in enumerate(belongs):
                    if k > 0:
                        cql = ''' 
                            MERGE (a:具体分支{name: '%s'})
                            MERGE (b:具体分支{name: '%s'})
                            MERGE (b)-[:从属]-> (a)
                        ''' % (belongs[k - 1], belongs[k])
                        graph.run(cql)
            # *************************************************
            #--------------------具体花卉------------------------
            # *************************************************
            print(flower_path, 'done')
        # ****************************************
        # -------------每个标题--------------------
        # ****************************************
        print(title, 'done')
    print('花卉构造完成')


if __name__ == '__main__':
    graph = Graph("http://localhost:7474/", auth=("neo4j", "123456"))
    graph.run('MATCH (n) DETACH DELETE n')
    createEntity0(graph)
    createFlower(graph)

# NOTE MATCH (n) DETACH DELETE n  清空数据库中的图
# NOTE MATCH (n) RETURN n  展开所有节点
# NOTE MATCH (a)--() RETURN a # 查询所有带关系的节点
# NOTE MATCH (a)-[r]->() RETURN a.name, type(r)  查询所有对外有关系的节点，以及关系类型，返回表格



'''
CREATE (:国家{id:'1', name:'中国'})	
CREATE (:省份{id:\'1\', name:\'安徽\'})	
CREATE (:产地{id:'1', name:'宣城'})

match (a {name: 'A'}) 
match (b {name: 'B'}) 
CREATE (a)-[r:属于]-> (b)


MATCH (a:`产地`{name:\'%s\'})
MATCH (b:`省份`{name:\'%s\'})
MATCH (c:`国家`{name:\'%s\'})
CREATE (a)-[r:属于]-> (b)
CREATE (b)-[r:属于]-> (c)

match (n) detach delete n	# 删除所有数据
CREATE (n:节点{属性:‘属性值’,....})	# 创建节点
create (n)-[:r{key:'value'}]->(n)	#创建关系
match (n {name: 'value'}) return n	# 以属性值查找节点
match (n: Person) return n			# 以标签查找节点
match (n:movie) where n.released > 1990  return n.title	# 条件查找
'''

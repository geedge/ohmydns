# !coding=utf-8
import datetime
import logging
import time
from concurrent import futures
import grpc
import pytz
from neomodel import db, StringProperty, DateTimeFormatProperty, RelationshipTo, StructuredRel, IntegerProperty, \
    StructuredNode, config, BooleanProperty

import analyze_pb2
import analyze_pb2_grpc
import analyzedutil as aul

logging.basicConfig(level=logging.DEBUG,filename="./log/pythonrun.log",filemode="w",
                    format='%(asctime)s - %(filename)s[line:%(lineno)d] - %(levelname)s: %(message)s')


class node:
    ip = ""
    AS = ""
    next = ""
    isp = ""
    cou = ""
    couCode = ""
    prov = ""
    lat = ""
    lng = ""
    FindTime = ""
    dataOK = ""
    owner = ""

    def __init__(self, ip):
        self.ip = ip
        record = aul.getrecord(ip)
        if record == 1:
            self.dataOK = False
            return
        self.dataOK = True
        self.isp = aul.filterNull(record.get('isp', b'').decode("utf-8"))
        self.lat = aul.filterNull(record.get('latwgs', b'').decode("utf-8"))
        self.lng = aul.filterNull(record.get('lngwgs', b'').decode("utf-8"))
        self.prov = aul.filterNull(record.get('province', b'').decode("utf-8"))
        self.AS = aul.filterNull(record.get('asnumber', b'').decode("utf-8"))
        self.couCode = aul.filterNull(record.get('areacode', b'').decode("utf-8"))
        self.cou = aul.filterNull(record.get('country', b'').decode("utf-8"))
        self.FindTime = datetime.datetime.now(pytz.UTC)
        self.owner = aul.filterNull(record.get('owner', b'').decode("utf-8"))


# 与go之间的通信

class RequestServe(analyze_pb2_grpc.GrpcServiceServicer):
    graph_conn = ""

    def AnalyzeService(self, request, context):
        '''
        具体实现AnalyzeService服务方法
        :param request:
        :param context:
        :return:
        '''
        r = request
        if r.gtype == "neo4j":
            if self.graph_conn == "":
                url = str(r.guri).split("//")[0] + "//" + r.guser + ":" + r.gpass + "@" + str(r.guri).split("//")[1]
                self.graph_conn = neo4j_connector(url)
                logging.info("已连接到图数据库Neo4j:" + r.guri)
            result = self.graph_conn.work_with_neoj_53(r.data)
            return analyze_pb2.result(res=result)
        return analyze_pb2.result(res="not support")


working_addr = "127.0.0.1"
working_port = "56789"


def serve():
    # 启动 rpc 服务，这里可定义最大接收和发送大小(单位M)，默认只有4M
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10), options=[
        ('grpc.max_send_message_length', 100 * 1024 * 1024),
        ('grpc.max_receive_message_length', 100 * 1024 * 1024)])

    analyze_pb2_grpc.add_GrpcServiceServicer_to_server(RequestServe(), server)
    server.add_insecure_port(working_addr + ":" + working_port)
    server.start()
    logging.info("Python分析模块启动，工作在 " + working_addr + ":" + working_port)
    try:
        while True:
            time.sleep(60 * 60 * 24)  # one day in seconds
    except KeyboardInterrupt:
        server.stop(0)


class RelResolver53(StructuredRel):
    W = IntegerProperty(default=1)
    FTIME = DateTimeFormatProperty(format="%Y-%m-%d %H:%M:%S")

# 查询记录定义
class NodeResolverQuery(StructuredNode):
    QNAME=StringProperty(required=True)
    QTYPE=StringProperty()
# 解析器和查询记录的关系
class RelResolverQuery(StructuredRel):
    W = IntegerProperty()

class NodeResolver53(StructuredNode):
    IP = StringProperty(required=True, unique_index=True)
    AS = StringProperty()
    ISP = StringProperty()
    COU = StringProperty()
    CCODE = StringProperty()
    PROV = StringProperty()
    LAT = StringProperty()
    LNG = StringProperty()
    IPType = StringProperty()
    FTIME = DateTimeFormatProperty(format="%Y-%m-%d %H:%M:%S")
    W = IntegerProperty(default=0)
    ISPUBLIC = BooleanProperty(default=False)
    LINK = RelationshipTo("NodeResolver53", "IP_LINK", model=RelResolver53)
    QLINK=RelationshipTo("NodeResolverQuery","Q_LINK",model=RelResolverQuery)
    def pre_save(self):
        self.W+=1
        self.FTIME=datetime.datetime.now(pytz.UTC)
    

class neo4j_connector:
    graph = ""

    # nodematcher = ""
    # relatmatcher = ""

    def __init__(self, url):
        # 连接neo4j
        #config.ENCRYPTED = True
        config.DATABASE_URL =url
        db.set_connection(url)
#  data=[ip1,ip2,ispublic,qname,qtype]
    def work_with_neoj_53(self, data):
        # 存储节点
        nodelist=[]
        datastr=""
        for d in data:
            datastr=datastr+str(d)+" , "
        logging.debug("处理数据："+datastr+"")
        ############################################### 对解析器节点进行处理#####################################################
        for d in range(len(data) - 3):
            n = node(data[d])
            if not n.dataOK:
                return "node err because ip"
            # 查询是否存在节点,不存在则新建
            nodelist.append(NodeResolver53.get_or_create({"AS":n.AS, "COU":n.cou,
                                    "CCODE":n.couCode, "LAT":n.lat, "LNG":n.lng,
                                    "ISP":n.isp, "IPType":aul.IP46(n.ip), "PROV":n.prov, "IP":n.ip})[0])
            if data[2] == "0" and d==0:
                nodelist[d].ISPUBLIC = True
            nodelist[d].save()
        
        # 创建或更新关联
        L=nodelist[0].LINK.relationship(nodelist[1])
        if L is None:
            nodelist[0].LINK.connect(nodelist[1]).save() 
        else:
            L.W+=1
            L.FTIME=datetime.datetime.now(pytz.UTC)
            L.save()           
                
                    
                    
        ################################################ 对查询记录节点进行处理################################################
        # 查询是否存在节点
        # q,exist=self.checknode_neo4j(q=data[3],qtype=data[4])
        # # 不存在则新建
        # if not exist:
        #     q = NodeResolverQuery(QNAME=data[3],QTYPE=data[4])
        #     q.save()
        # 存在则不做处理
        

        ############################################ 查询解析器是否存在关系#############################################
        # L, lexist = self.checklink_neo4j(nodelist[0], nodelist[1])
        # # 数据存在问题则退出
        # if L == "Err":
        #     return "node err when link"
        # # 不存在则建立关联
        # if not lexist:
        

        
        
        
        # 存在则修改权重
        # else:
        #     L.W += 1
        #     L.LTIME = datetime.datetime.now(pytz.UTC)
        #     L.save()
        # 提交链接
        
        ############################################查询解析器和记录间的关系#########################################
        # QL, lexist = self.checkquerylink(data[1], data[3],data[4])
        # # 数据存在问题则退出
        # if QL == "Err":
        #     return "node err when link"
        # # 不存在则建立关联
        # if not lexist:
        #     QL[0].QLINK.connect(QL[1], {'W': 1}).save()
        # # 存在则修改权重
        # else:
        #     QL.W += 1
        #     QL.save()
            
        # 完成处理，返回
        logging.debug("完成处理数据：{"+datastr+"}")
        return "success"

    # def checknode_neo4j(self, ip=None,q=None,qtype=None):
    #     # 查询IP
    #     if ip!=None:
    #         a = NodeResolver53.nodes.get_or_none(IP=ip)
    #     # 查询记录
    #     else:
    #         a=NodeResolverQuery.nodes.get_or_none(QNAME=q,QTYPE=qtype)
    #     if a is not None:
    #         return a, True
    #     return None, False

    def checklink_neo4j(self, ip_from, ip_to):
        rel = ip_from.LINK.relationship(ip_to)
        if rel is not None:
            return rel, True
        return [ip_from, ip_to], False
    
    def checkquerylink(self,ip,qname,qtype):
        r=NodeResolver53.nodes.get_or_none(IP=ip)
        q=NodeResolverQuery.nodes.get_or_none(QNAME=qname,QTYPE=qtype)
        if r is None or q is None:
            return "Err", False
        rel=r.QLINK.relationship(q)
        if rel is not None:
            return rel, True
        return [r, q], False

if __name__ == '__main__':
    serve()

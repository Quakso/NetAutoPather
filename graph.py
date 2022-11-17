from topobase import Host,Hosts,Topo,Cluster,Device,Link

class Point:
    def __init__(self,id,port) -> None:
        self.deviceId=id
        self.devicePort=port
    
    # point will be key of weight matrix
    def __eq__(self, __o: object) -> bool:
        if not isinstance(__o,Point):
            raise TypeError('need a point')
        return (self.deviceId,self.devicePort) == (__o.deviceId,__o.devicePort)

    def __hash__(self) -> int:
        return hash((self.deviceId,self.devicePort))

class Graph:
    def __init__(self, topo:Topo) -> None:
        self.weightMatrix:dict={}
        self.pointList:list[Point]=[]
        self.defaultWeight=1
        self.maxWeight=999
        self.readTopo(topo)
    
    def readTopo(self, topo:Topo):# construct graph from topo
        for h in topo.hosts.hostList:# add endpoint of hosts' link
            p=Point(h.devId,h.devPort)
            self.pointList.append(p)
            if not self.weightMatrix.__contains__(p):
                self.weightMatrix[p]={}
        for c in topo.clusterList:
            for li in c.linkList:# add endpoint of link
                p_src=Point(li.src_devId,li.src_port)
                p_dst=Point(li.dst_devId,li.dst_port)
                if not p_src in self.pointList:# add src endpoint of link if it's not in the list
                    self.pointList.append(p_src)
                if not p_dst in self.pointList:# add dst endpoint of link if it's not in the list
                    self.pointList.append(p_dst)
                
                # add edge weight to the matrix
                if not self.weightMatrix.__contains__(p_src):
                    self.weightMatrix[p_src]={}
                self.weightMatrix[p_src][p_dst]=self.defaultWeight

                if not self.weightMatrix.__contains__(p_dst):
                    self.weightMatrix[p_dst]={}
                self.weightMatrix[p_dst][p_src]=self.defaultWeight

        for p in self.weightMatrix:
            sameDevLst,otherLst=self.getSameDevicePointList(p)
            for sp in sameDevLst:# points in the same device, edges whose weight is 0 connect them 
                self.weightMatrix[p][sp]=0
            for op in otherLst:# unreachable, their edges' weight is 999
                if not self.weightMatrix[p].__contains__(op):
                    self.weightMatrix[p][op]=self.maxWeight
        
        print(f'-----Graph Point List {len(self.pointList)}-----')
        for p in self.pointList:
            print(f'Point: id:{p.deviceId} port:{p.devicePort}')

        print(f'-----Graph Weight Matrix-----')
        for sp in self.pointList:
            print(f'Point: id:{sp.deviceId} port:{sp.devicePort} ',end='')
            for tp in self.weightMatrix[sp]:
                print(self.weightMatrix[sp][tp],end='\t')
            print('')
 
    def getSameDevicePointList(self,point:Point):
        sameDevPointLst:list[Point]=[]
        otherPointLst:list[Point]=[]
        for p in self.pointList:
            if p.deviceId==point.deviceId:
                sameDevPointLst.append(p)
            else:
                otherPointLst.append(p)
        return sameDevPointLst,otherPointLst

    def dijistra(self,point:Point):
        result={}
        unknown={}
        pre={}
        if not point in self.pointList:# check if the point is in the pointlist
            raise RuntimeError('point is not in the graph')
        result[point]=0
        pre[point]=None
        for p in self.pointList:
            if p == point:
                continue
            unknown[p]=self.weightMatrix[point][p]
            # if is connect to start point, their initial precursor point is the start point
            if not self.weightMatrix[point][p]==self.maxWeight:
                pre[p]=point

        while len(unknown)!=0:
            # get the least weight, add the corresponding point to result
            minP=self.getMinWeightPoint(unknown)
            result[minP]=unknown[minP]
            del unknown[minP]

            # refresh the weight
            for p in unknown:
                if (self.weightMatrix[minP][p]+result[minP])<unknown[p]:
                    unknown[p]=self.weightMatrix[minP][p]+result[minP]
                    pre[p]=minP # refresh the precursor point

        
        print('-----Dijistra Point-----')
        for p in result:
            print(f'Point: id:{p.deviceId} port:{p.devicePort} minWeight:{result[p]}')
        
        print('-----Dijistra View-----')
        for p in self.pointList:
            while pre[p] is not None:
                print(f'Point: id:{p.deviceId} port:{p.devicePort}',end='->')
                p=pre[p]
            print(f'Point: id:{p.deviceId} port:{p.devicePort}')
        return pre
        
    def getMinWeightPoint(self,dict:dict):
        minWeight=self.maxWeight
        minP=None
        for p in dict:
            if dict[p]<=minWeight:
                minWeight=dict[p]
                minP=p
        return minP

def printWeight(weight:dict,point1:Point,point2:Point):
    print(weight[point1][point2])


if __name__=='__main__':
    weight={}
    p1=Point('of:0000000000000001','3')
    p2=Point('de','2')
    weight[p1]={}
    weight[p1][p2]=1
    weight[p2]={}
    weight[p2][p1]=2
    print(weight.__contains__(p1))
    for item in weight:
        print(item,weight[item])
    print(weight[p1][p2])
    print(weight[p2][p1])
    px=Point('of:0000000000000001','3')
    print(weight[px][p2])
    print(len(weight))
    printWeight(weight,p1,p2)




        

            
        


from lxml import etree
import requests
import subprocess
import time

ServerLogNode = "RPRE_MMXU1"
sfc = "MX"
sp = 102

def parseXml():

	ns = {"scl" : "http://www.iec.ch/61850/2003/SCL"}
	root = etree.parse('Locamation VMU WWG_V1.0.scd')
	myroot = root.getroot()

	ServLogDevices = [ ]
	ServIedModels = [ ]
	ServerIps = [ ]
	
	CDCs = ['A.phsB','A.phsB','A.phsB','PPV.phsBC','PPV.phsBC','PPV.phsBC','TotW','TotW','TotW']
	dattribs = ['instCval.mag.f','instCval.mag.f','instCval.mag.f','cVal.mag.f','cVal.mag.f','cVal.mag.f','mag.f','mag.f','mag.f']		

	res1 = myroot.xpath('//scl:LN[@lnClass="MMXU" and @inst="1" and @prefix="RPRE_"]/scl:DOI[@name="A"]/scl:SDI[@name="phsB"]', namespaces=ns)
	res2 = myroot.xpath('//scl:LN[@lnClass="MMXU" and @inst="1" and @prefix="RPRE_"]/scl:DOI[@name="PPV"]/scl:SDI[@name="phsBC"]', namespaces=ns)
	res3 = myroot.xpath('//scl:LN[@lnClass="MMXU" and @inst="1" and @prefix="PPRE_"]/scl:DOI[@name="TotW"]', namespaces=ns)

	for sdi in res1:
		resout = sdi.xpath('.//parent::*/parent::*/parent::*/parent::*/parent::*/parent::*/@name', namespaces=ns)
		IED = resout[0]
		ip =  myroot.xpath('//scl:ConnectedAP[@iedName='+'"'+str(IED)+'"'+ ' and @apName="E"]/scl:Address/scl:P[@type="IP"]/text()', namespaces=ns)[0]
		ServIedModels.append(IED)
		ServerIps.append(ip)

	for sdi in res1:
		resout = sdi.xpath('.//parent::*/parent::*/parent::*/@inst', namespaces=ns)
		ServLogDevices.append(resout[0])

	for sdi in res2:
		resout = sdi.xpath('.//parent::*/parent::*/parent::*/parent::*/parent::*/parent::*/@name', namespaces=ns)
		IED = resout[0]
		ip =  myroot.xpath('//scl:ConnectedAP[@iedName='+'"'+str(IED)+'"'+ ' and @apName="E"]/scl:Address/scl:P[@type="IP"]/text()', namespaces=ns)[0]
		ServIedModels.append(IED)
		ServerIps.append(ip)

	for sdi in res2:
		resout = sdi.xpath('.//parent::*/parent::*/parent::*/@inst', namespaces=ns)
		ServLogDevices.append(resout[0])
		
	for sdi in res3:
		resout = sdi.xpath('.//parent::*/parent::*/parent::*/parent::*/parent::*/@name', namespaces=ns)
		IED = resout[0]
		ip =  myroot.xpath('//scl:ConnectedAP[@iedName='+'"'+str(IED)+'"'+ ' and @apName="E"]/scl:Address/scl:P[@type="IP"]/text()', namespaces=ns)[0]
		ServIedModels.append(IED)
		ServerIps.append(ip)

	for sdi in res3:
		resout = sdi.xpath('.//parent::*/parent::*/@inst', namespaces=ns)
		ServLogDevices.append(resout[0])

	return((ServLogDevices,ServIedModels,ServerIps,CDCs,dattribs))		

def configFledgeSouth(name,ip,port,IedModel,ldevice,lnode,CDC,fconstraint,dattrib):
    
    plugDict = {}
    plugDict["name"] = name
    plugDict["type"] = "south"
    plugDict["plugin"] = "iec61850"
    plugDict["enabled"] = "false"
       
    r = requests.post('http://localhost:8081/fledge/service', json=plugDict)
    print(plugDict)
    
    plugDict = {}
    plugDict["Functional Constraint"] = fconstraint
    plugDict["Data Attribute"] = dattrib
    plugDict["ip"] = ip
    plugDict["port"] = str(port)
    plugDict["IED Model"] = IedModel
    plugDict["Logical Device"] = ldevice
    plugDict["Logical Node"] = lnode
    plugDict["CDC"] = CDC
    addr = "http://localhost:8081/fledge/category/"+str(name)
    r = requests.put(addr, json=plugDict)
    print(plugDict)

def configFledgeFilter(name_filter,name_plugin):

	plugDict = {}
	plugDict["name"] = name_filter
	plugDict["plugin"] = "wma_filter"
	plugDict["enabled"] = "false"

	r = requests.post('http://localhost:8081/fledge/filter', json=plugDict)
	#print(r)
	print(plugDict)	

	plugDict = {}
	plugDict["filter_time"] = "300"
	plugDict["datapoint"] = "wma_"+ str(name_plugin)
	addr = 'http://localhost:8081/fledge/category/' + str(name_filter)
	r = requests.put(addr, json=plugDict)
	#print(r)
	#print(addr)
	print(plugDict)	
	
	plugDict = {}
	nameL = []
	nameL.append(name_filter)
	plugDict["pipeline"] = nameL
	addr = 'http://localhost:8081/fledge/filter/' +str(name_plugin) + '/pipeline'
	r = requests.put(addr, json=plugDict)
	#print(r)
	#print(addr)
	print(plugDict)	

def configFledeNorth(name,name_south):

	plugDict = {}
	plugDict["name"] = name
	plugDict["type"] = "north"
	plugDict["plugin"] = "ktp_north"
	plugDict["enabled"] = "false"
	r = requests.post('http://localhost:8081/fledge/service', json=plugDict)
	print(plugDict)

	plugDict = {}
	plugDict["wma_filter"] = "wma_"+ str(name_south)
	addr = "http://localhost:8081/fledge/category/"+str(name)
	r = requests.put(addr, json=plugDict)
	print(plugDict)

def xmltoFledge(valuesLists):

	valuesLists = parseXml()
	ServLogDevices = valuesLists[0]
	ServIedModels = valuesLists[1]
	ServerIps = valuesLists[2]
	CDCs = valuesLists[3]
	dattribs = valuesLists[4]

	#CDCs = ['A.phsB','PPV.phsBC','Totw']
	#dattribs = ['instCval.mag.f','cVal.mag.f','mag.f']


	for count in range(len(ServLogDevices)):
		name = ServIedModels[count]+"_South_"+ CDCs[count]
		ip = ServerIps[count]
		port = sp
		IedModel = ServIedModels[count]
		ldevice = ServLogDevices[count] 
		lnode = ServerLogNode
		CDC =  CDCs[count]
		fconstraint = sfc
		dattrib  = "dummy"
		configFledgeSouth(name,ip,port,IedModel,ldevice,lnode,CDC,fconstraint,dattrib)
		print(count)

	for count in range(len(ServLogDevices)):
		name_plugin = ServIedModels[count]+"_South_" +  CDCs[count]
		name_filter = ServIedModels[count]+"_Filter"
		configFledgeFilter(name_filter,name_plugin)
		print(count)
		
	for count in range(len(ServLogDevices)):
		name = ServIedModels[count]+"_North_"+  CDCs[count]
		name_south = ServIedModels[count]+"_South_"+  CDCs[count]
		configFledeNorth(name,name_south)
		print(count)
			

def startFledge():
    print("Start Fledge!")
    subprocess.call(["/usr/local/fledge/bin/fledge", "start"])
    print("Fledge started!")
    
def stopFledge():
    print("Stop Fledge!")
    subprocess.call(["/usr/local/fledge/bin/fledge", "stop"])
    print("Fledge stopped!")		
 
def main():

    valuesLists = parseXml()
	
    startFledge()
		
    xmltoFledge(valuesLists)
	
    stopFledge()

if __name__ == "__main__":
    main()

import os
import sys
import boto3
import botocore
import uuid
import time

class Server(object):
    def __init__(self, args):
        self.gname = args.gatewayname
        self.size = args.size
        self.count = args.count
        self.sgwclient = self.get_api()
        self.gatewayARN = self.get_gateway_arn()

    def _run_cmd(self, cmd):
        print cmd
        os.system(cmd)
    

    def get_api(self):
	try:
	    print "Connecting to storagegateway client using boto3 AWS SDK ..."
            sgwclient = boto3.client("storagegateway")
	except botocore.exceptions.NoRegionError:
            e = "No region configured. Either export the AWS_DEFAULT_REGION environment variable or set the region value in your ~/.aws/config file by running aws config."
            print (e)
	    sys.exit(1)

	return sgwclient
    
    def get_gateway_type(self):
       gateway_type = self.sgwclient.describe_gateway_information(GatewayARN=self.gatewayARN)['GatewayType']
       return gateway_type

    def get_gateway_arn(self): 
       response = self.sgwclient.list_gateways(Limit=10)
       for i in response['Gateways']:
          if i['GatewayName'] == self.gname:
             gatewayARN = i['GatewayARN']
             return gatewayARN
          else: 
             continue
       print (self.gname + " does not exist. Please specify a valid gateway")
       sys.exit(1)

    def _get_volume_list(self):
       volume_list = []
       r = self.sgwclient.list_volumes(GatewayARN=self.gatewayARN)
       for item in r['VolumeInfos']:
          volume_list.append(item['VolumeARN'])
       return volume_list

    def get_target_iqn_list(self):
       volume_list = self._get_volume_list()
       iqn_list = []
       r = self.sgwclient.describe_cached_iscsi_volumes(VolumeARNs=volume_list)
       return r
     
    def get_network_interface_id(self):
       ip_address = self.sgwclient.describe_gateway_information(GatewayARN=self.gatewayARN)["GatewayNetworkInterfaces"][0]["Ipv4Address"]
       return ip_address
    
    def create_cached_iscsi_volume(self):
       ip_address = self.get_network_interface_id()
       size = int(self.size)*1024*1024*1024
       
       iqn_list = []
       for i in range(1, self.count + 1):
          targetname = self.gname + "-target-" + str(int(time.time())) + "-" + str(i)
          clientToken = str(uuid.uuid4())
          r = self.sgwclient.create_cached_iscsi_volume(GatewayARN=self.gatewayARN, VolumeSizeInBytes=size, TargetName=targetname, NetworkInterfaceId=ip_address, ClientToken=clientToken) 

          target_iqn_list = r['TargetARN'].split("/")[-1]
          iqn_list.append(target_iqn_list)

       return iqn_list

    def create_nfs_file_share(self):
       pass

    def delete_volumes(self):
       volume_list = self._get_volume_list()
       for vol in volume_list:
          # add check to only delete those volumes whose target has gatewayname
          print("Deleting volume " + vol)
          self.sgwclient.delete_volume(VolumeARN = vol)
         
    def op_state_poller(self, instance):
	count = 0
	while count < 10:
	   if instance['op_state'] != 'available':
	      time.sleep(1)
	      count = count + 1
	   if count > 9:
	      print instance['name'] + " did not become available in 10s"
	      sys.exit(-1)
	   break   

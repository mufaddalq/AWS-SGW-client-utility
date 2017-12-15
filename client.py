import subprocess
import os
import platform
import multiprocessing as mp
import time

# THINGS TO DO:
# 1) Implement logging

DISK_BY_PATH = "/dev/disk/by-path"
SYS_BLOCK = "/sys/block"

class Client(object):
    def __init__(self, args):
        self.gname = args.gatewayname
        self.mkfs = args.mkfs
        self.dirprefix = args.dirprefix
    
    # Eventually replace with subprocess 
    def _run_cmd(self, cmd):
        print cmd
        os.system(cmd)

    def iqn_to_sd(self, iqn):
       count = 0
       while count < 15:
           if os.path.exists(DISK_BY_PATH):
              for item in os.listdir(DISK_BY_PATH):
                 if iqn in item:
                    if os.path.islink(DISK_BY_PATH + "/" + item) == False:
                       break
                    return os.path.basename(os.readlink(DISK_BY_PATH + "/" + item))
           time.sleep(1)
           count = count + 1
           print "Waiting for target block device to show up in /dev/disk/by-path..."
           if count > 14:
              print iqn + " did not map to block device in 10s"
              sys.exit(-1)


    def _create_fio_template(self):
	with open('fiotemplate.fio','w') as f:
	   lines = ["[global]","randrepeat=0","ioengine=libaio","iodepth=16","direct=1","numjobs=4","runtime=3600","group_reporting","time_based"]
	   for line in lines:
	      f.write(line + '\n')

    def target_login(self, iqn_list, ip):
        for iqn in iqn_list:
           print "IQN: " + iqn
           print "IP ADDRS = ", ip
           cmd = "iscsiadm -m node -T " + iqn + " --portal " + ip + " --op=new"
           cmd = cmd + " > /dev/null 2>&1"
           print cmd
           subprocess.check_output(cmd, shell=True)
           cmd = "iscsiadm -m node -T " + iqn + " --portal " + ip + " -l"
           print cmd
           subprocess.check_output(cmd, shell=True)
   
    def target_logout_and_node_cleanup(self, targets):
        for item in targets['CachediSCSIVolumes']:
           targetARN = item['VolumeiSCSIAttributes']['TargetARN']
           if self.gname in targetARN:
              targetiqn = targetARN.split('/')[-1]
              self._run_cmd("iscsiadm -m node -u -T %s" % targetiqn)
              self._run_cmd("iscsiadm -m node -T %s --op=delete" % targetiqn)
              self._run_cmd("iscsiadm -m discoverydb -t st -p %s:3260 --op=delete" % item['VolumeiSCSIAttributes']['NetworkInterfaceId'])
           
        self._run_cmd("iscsiadm -m session --rescan")
        self.restart_services()
  
    def unmount(self):
        cmd = "mount |grep %s | awk '{print $3}'" % self.gname
        for l in os.popen(cmd).readlines():
            line = l.rstrip()
            if line == "/":
               print "skipping unmount of /"
               return None
            p = os.path.basename(line)
            print p
            print line
            self._run_cmd("umount %s" % line)
            self._run_cmd("rm -rf %s" % line)
        # cleanup fio files
        self._run_cmd("rm -rf " + self.gname + "*.fio")

    # need to figure out how to handle client_cluster_map
    def mp_mkfs(self, mntmap):
        pool = mp.Pool(processes=10)
        pool.map(mkfs, mntmap)
 
    # need to figure out how to handle client_cluster_map
    def create_fio_files(self, mntmap):
        
	fio = {self.gname + '_randread.fio':{'rw':'randread', 'blocksize':'4k'},
	       self.gname + '_seqread.fio':{'rw':'read', 'blocksize':'1m'},
	       self.gname + '_randwrite.fio':{'rw':'randwrite', 'blocksize':'4k'},
	       self.gname + '_seqwrite.fio':{'rw':'write', 'blocksize':'1m'},
	       self.gname + '_randreadwrite.fio':{'rw':'randrw', 'rwmixread': '70', 'blocksize':'4k'}
	      }

	self._create_fio_template()

	for key,item in fio.items():
	   with open('fiotemplate.fio', 'r') as f:
	      with open(key, 'w') as key:
		 for line in f:
		    key.write(line)
		 for param in item:
		    key.write(param + "=" + item[param] + '\n')
		 if self.mkfs:
		    for index in range(len(mntmap)):
		       key.write("[fiofile]" + '\n')
		       key.write("directory=/" + mntmap[index][1] + '\n')
		       key.write("size=500M" + '\n')
		 else:
                     for item in mntmap['CachediSCSIVolumes']:
                        targetARN = item['VolumeiSCSIAttributes']['TargetARN']
                        if self.gname in targetARN:
                            targetiqn = targetARN.split('/')[-1]
                            key.write("[fiofile]" + '\n')
                            sd = self.iqn_to_sd(targetiqn)
                            key.write("filename=/dev/" + str(sd) + '\n')
                            key.write("size=500M" + '\n')

    def restart_services(self):
        pass

class UbuntuClient(Client):
    def __init__(self, args):
        super(UbuntuClient, self).__init__(args)
        self.os_type = platform.dist()[0]
    def restart_services(self):
        self._run_cmd("service multipath-tools reload")
    
class CentosClient(Client):
    def __init__(self, args):
        super(CentosClient, self).__init__(args)
        self.os_type = platform.dist()[0]
    def restart_services(self):
        self._run_cmd("service multipathd reload")

# helper method for client factory
def get_client(args):
    if platform.dist()[0] == "Ubuntu":
        client = UbuntuClient(args)
    elif platform.dist()[0] == "centos" or platform.dist()[0] == "redhat":
        client = CentosClient(args)
    elif "amzn" in platform.platform():
        client = CentosClient(args)
    else:
        raise ValueError("Client not supported")
   
    return client

#Creating as a helper method because otherwise mp library does not like it if called as in instance method
def mkfs(item):
    if item[2].fstype == "xfs":
	cmd = "mkfs.xfs {} ; mkdir -p /{}; mount {} /{}".format(item[0], item[1], item[0], item[1])
    else:
	cmd = "mkfs.ext4 -F -E lazy_itable_init=1 {} ; mkdir -p /{}; mount {} /{}".format(item[0], item[1], item[0], item[1])
    print cmd
    os.system(cmd)
    if item[2].chown:
	os.system("chown -R {} /{}".format(item[2].chown, item[1]))

class Utilities(object):
    def __init__(self, args):
        self.args = args

    def devicemap(self, c, s):
        mntmap = []
	#gatewayname = c.gname

	targets = s.get_target_iqn_list()

	for item in targets['CachediSCSIVolumes']:
	    targetARN = item['VolumeiSCSIAttributes']['TargetARN']
	    if s.gname in targetARN:
	       targetiqn = targetARN.split('/')[-1]
	       #iqn_list.append(targetiqn)
	       sd = c.iqn_to_sd(targetiqn)
	       sdpath = "/dev/" + str(sd)

	       print("Amazon gatewayARN: ", s.gatewayARN,
		     "   volumeARN: ", item['VolumeARN'],
		     "   IQN: ", targetiqn)

	       if c.mkfs:
	          mntpoint = s.gname + item['VolumeId']
                  if self.args.dirprefix:
  		      mntpoint = args.dirprefix + "/" + mntpoint
	          mntmap.append([sdpath, mntpoint, self.args])

	if c.mkfs:
       	    return mntmap
	else:
            return targets

#    def create_cluster_map(self, s):
#        cluster_map = {}
#        tlist = s.list_tenants()
#        ailist = s.list_ai()
#        silist = s.list_si(ailist)
#        vlist = s.list_vol(ailist, silist)
#        for t in tlist:
#	    if t["name"] != "root" :
#	        tenant = "/root/" + t["name"]
#	    else:
#		tenant = "/" + t["name"]
#	    for ai in ailist:
#		for si in ai['storage_instances']:
#		    for v in si['volumes']:
#		        vuuid = v['uuid']
#		        if not s.basename or s.basename in ai['name']:
#			    cluster_map[vuuid] = {'tname': si['ip_pool']['resolved_tenant'], 'aname': ai['name'], 'sname': si['name'],'vname': v['name'], 'id': id, 'nodename': s.si_to_snname(si) }
#			    if 'iqn' in si['access']:
#			        cluster_map[vuuid]['iqn'] = si['access']['iqn']
#         
#        #print cluster_map
#	return cluster_map 
#    
#    def create_client_cluster_map(self, cluster_map, c):
#        for k, v in cluster_map.iteritems():
#            sd = c.iqn_to_sd(v['iqn'])
#            if sd:
#                dm = c.sd_to_dm(sd)
#                v['dm'] = dm
#                #dm = uuid_to_dm(args,map[m]['id'])
#                if not dm:
#                    print "No DM for sd: ", sd + ". Please make sure that multipath service is running. Then cleanall and retry"
#                    sys.exit(-1)
#                mapper = c.dm_to_mapper(dm)
#                v['mapper'] = mapper
#                if not mapper:
#                    print "No mapper entry for dm: ", dm + ". Please make sure that multipath service is running. Then cleanall and retry"
#                    sys.exit(-1)
#                dmpath = c.mapper_to_dmpath(mapper)
#                v['dmpath'] = dmpath
#                
#                #Add mountpoints to client_cluster_map
#                if c.mkfs:
#                    # ASSUME "singleton" 1:1:1 (app_inst:storage_inst:vol)
#                    mntpoint = v['aname'] + "-" + v['vname']
#                    if c.dirprefix:
#                        mntpoint = c.dirprefix + "/" + mntpoint
#                    v['mntpoint'] = mntpoint
#                    v['mntmap'] = [dmpath, mntpoint, self.args]
#        
#        return cluster_map
#
#    def create_fs_mntmap(self, s, c):
#        mntmap = []
#	cluster_map = self.create_cluster_map(s)
#	client_cluster_map = self.create_client_cluster_map(cluster_map, c)
#        for k,v in client_cluster_map.iteritems():
#            mntmap.append(v['mntmap'])
#        
#        return mntmap
#
#    def print_server_client_map(self, s, c):
#	cluster_map = self.create_cluster_map(s)
#	client_cluster_map = self.create_client_cluster_map(cluster_map, c)
#
#        for k,v in client_cluster_map.iteritems():
#		#if not api.system.get()['sw_version'].startswith(API_VER):
#            print "HOST-DM: " + v['dm'] + \
#	          "   DATERA: " + v['tname'] + "/" + v['aname'] + "/" + v['sname']  + "/" + v['vname'] + \
#		  "   IQN: " + v['iqn'] + \
#		  "   MAPPER: /dev/mapper/" + v['mapper'] + \
#		  "   NODE:" + v['nodename']

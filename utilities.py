class Utilities(object):
    def __init__(self, args):
        self.args = args

    def devicemap(self, c, s):
        mntmap = []

	targets = s.get_target_iqn_list()

	for item in targets['CachediSCSIVolumes']:
	    targetARN = item['VolumeiSCSIAttributes']['TargetARN']
	    if s.gname in targetARN:
	       targetiqn = targetARN.split('/')[-1]
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


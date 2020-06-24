#coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: hwliang <hwl@bt.cn>
# +-------------------------------------------------------------------

import IPy
import json
filename = 'E:/ip/鸟云.txt'
ip_txt = open(filename).read().strip()
ips = ip_txt.split('\n')
ip_list = []
for i in ips:
    ip = IPy.IP(i.strip())
    ip_list.append([str(ip[0]),str(ip[-1])])

f = open(filename + '.json','w+')
f.write(json.dumps(ip_list))
f.close()
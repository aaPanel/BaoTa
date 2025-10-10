#coding: utf-8
#多用户放行端口脚本
import sys,os
os.chdir('/www/server/panel/')
sys.path.insert(0,"class/")
sys.path.insert(0,"class_v2/")
import public
import yaml
public.print_log("vhost_virtual.py")
default_yaml = '{}/vhost_virtual/manifest/config/default.yaml'.format(public.GetConfigValue('setup_path'))
not_accept_port_file = '{}/vhost_virtual/config/not_accept_port.pl'.format(public.GetConfigValue('setup_path'))
import firewalls
get = public.dict_obj()
get.ps = "vhost virtual service"
if not os.path.exists(not_accept_port_file):
    with open(default_yaml, 'r') as file:
        data=yaml.safe_load(file)
        try:
            if data["server"].get("address"):
                http_port=data["server"]["address"]
                #如果存在：用：分割端口，并取第二个端口和去除空格
                if ":" in http_port:
                    get.port=http_port.split(":")[1].strip()
                    if get.port !="" and public.M('firewall').where("port=?",(get.port,)).count()<1:
                        firewalls.firewalls().AddAcceptPort(get)
            if data["server"].get("httpsAddr"):
                https_port = data["server"]["httpsAddr"]
                #如果存在：用：分割端口，并取第二个端口和去除空格
                if ":" in https_port:
                    get.port=https_port.split(":")[1].strip()
                    if get.port !="" and public.M('firewall').where("port=?",(get.port,)).count()<1:
                        firewalls.firewalls().AddAcceptPort(get)
        except Exception as e:
            public.print_log("e111--------------:{}".format(e))

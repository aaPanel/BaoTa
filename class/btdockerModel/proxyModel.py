# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
import json
import os
import traceback
from datetime import datetime

import public
from btdockerModel import dk_public as dp
from btdockerModel.dockerBase import dockerBase

class main(dockerBase):

    # 2023/12/27 下午 2:56 创建容器反向代理
    def create_proxy(self, get):
        '''
            @name 创建容器反向代理
            @author wzz <2023/12/27 下午 2:57>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if not (os.path.exists('/etc/init.d/nginx') or os.path.exists('/etc/init.d/httpd')):
            return public.returnMsg(False, '未检测到nginx或apache服务，请先安装其中一个!')

        if not hasattr(get, 'domain'):
            return public.returnMsg(False, '参数错误,请传domain参数!')

        if not hasattr(get, 'container_port'):
            return public.returnMsg(False, '参数错误,请传container_port参数!')

        self.siteName = get.domain.strip()

        if dp.sql('docker_sites').where('container_id=?', (get.container_id,)).find():
            self.close_proxy(get)

        # 2024/2/23 下午 12:05 如果其他地方有这个域名，则禁止添加
        newpid = public.M('domain').where("name=? and port=?", (self.siteName, 80)).getField('pid')
        if newpid:
            result = public.M('sites').where("id=?", (newpid,)).find()
            if result:
                return public.returnMsg(False, '项目类型【{}】已存在域名：{}'.format(result['project_type'], self.siteName))
        newpid = dp.sql("docker_domain").where("name=? and port=?", (self.siteName, 80)).getField('pid')
        if newpid:
            result = dp.sql("docker_sites").where("id=?", (newpid,)).find()
            if result:
                return public.returnResult(False, 'docker网站项目【{}】已存在域名：{}，请勿重复添加！'.format(result['name'], self.siteName))

        self.container_port = get.container_port
        if not dp.check_socket(self.container_port):
            return public.returnMsg(False, "服务器端口[{}]未被使用，请输入正在使用的端口进行反代！".format(self.container_port))

        from mod.project.docker.sites.sitesManage import SitesManage
        site_manage = SitesManage()

        try:
            args = public.to_dict_obj({
                "name": get.container_name,
                "container_id": get.container_id,
                "type": "proxy",
                "domains": self.siteName,
                "port": self.container_port,
                "remark": "容器[{}]的反向代理".format(get.container_name),
            })
            create_result = site_manage.create_site(args)
            if not create_result['status']:
                return public.returnResult(False, create_result['msg'])

            if hasattr(get, "privateKey") and hasattr(get, "certPem") and get.privateKey != "" and get.certPem != "":
                args.site_name = self.siteName
                args.key = get.privateKey
                args.csr = get.certPem
                ssl_result = site_manage.set_ssl(args)
                if not ssl_result['status']:
                    result = public.M('sites').where("name=?", (self.siteName,)).find()
                    args.id = result['id']
                    args.site_name = self.siteName
                    args.remove_path = 1
                    site_manage.delete_site(args)
                    return public.returnResult(False, ssl_result['msg'])

            return public.returnMsg(True, '添加成功!')
        except Exception as e:
            result = public.M('sites').where("name=?", (self.siteName,)).find()
            args = public.to_dict_obj({
                "id": result['id'],
                "site_name": self.siteName,
                "remove_path": 1,
            })
            site_manage.delete_site(args)
            return public.returnMsg(True, '添加失败，错误{}!'.format(str(e)))

    # 2024/1/2 下午 5:34 获取容器的反向代理信息
    def get_proxy_info(self, get):
        '''
            @name 获取容器的反向代理信息
            @author wzz <2024/1/2 下午 5:34>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        if not hasattr(get, 'container_id'):
            return public.returnMsg(False, '参数错误,请传container_id参数!')

        container_id = get.container_id
        from btdockerModel import containerModel as dc
        get.id = container_id
        container_info = dc.main().get_container_info(get)
        proxy_port = []
        proxy_info = {
            "proxy_port": proxy_port,
            "ssl": False,
            "status": False,
        }
        if "status" in container_info and not container_info["status"]:
            proxy_port = []
        else:
            for key, value in container_info['NetworkSettings']['Ports'].items():
                if value:
                    proxy_port.append(value[0]['HostPort'])

        try:
            proxy_info_data = dp.sql('docker_sites').where('container_id=?', (container_id,)).order('id desc').find()
            if not proxy_info_data:
                return proxy_info

            proxy_info = proxy_info_data

            path = '/www/server/panel/vhost/cert/' + proxy_info['name']
            conf_file = '/www/server/panel/vhost/nginx/' + proxy_info['name'] + '.conf'
            csrpath = path + "/fullchain.pem"
            keypath = path + "/privkey.pem"
            proxy_info["ssl"] = False
            if os.path.exists(csrpath) and os.path.exists(keypath):
                try:
                    conf = public.readFile(conf_file)
                    if conf:
                        if (conf.find("ssl_certificate") != -1):
                            proxy_info["ssl"] = True
                    proxy_info['cert'] = public.readFile(csrpath)
                    proxy_info['key'] = public.readFile(keypath)
                except:
                    proxy_info['cert'] = ""
                    proxy_info['key'] = ""

            proxy_info["status"] = True
            proxy_info['proxy_port'] = proxy_port
        except:
            pass

        return proxy_info

    # 2024/1/2 下午 5:43 关闭容器的反向代理
    def close_proxy(self, get):
        '''
            @name 关闭容器的反向代理
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if not hasattr(get, 'container_id'):
                return public.returnMsg(False, '参数错误,请传container_id参数!')

            container_id = get.container_id
            proxy_info = dp.sql('docker_sites').where('container_id=?', (container_id,)).find()

            if not proxy_info:
                return public.returnMsg(False, '未检测到反向代理信息!')

            from mod.project.docker.sites.sitesManage import SitesManage
            site_manage = SitesManage()

            args = public.dict_obj()
            args.id = proxy_info['id']
            args.site_name = proxy_info['name']
            args.remove_path = 1
            delete_result = site_manage.delete_site(args)
            if not delete_result['status']:
                return public.returnMsg(False, delete_result['msg'])

            return public.returnMsg(True, '删除成功!')
        except:
            return traceback.format_exc()

    # 2024/1/2 下午 5:57 获取指定域名的证书内容
    def get_cert_info(self, get):
        '''
            @name 获取指定域名的证书内容
            @author wzz <2024/1/2 下午 5:58>
            @param "data":{"参数名":""} <数据类型> 参数描述
            @return dict{"status":True/False,"msg":"提示信息"}
        '''
        try:
            if not hasattr(get, 'cert_name'): return public.returnMsg(False, '参数错误!')
            cert_name = get.cert_name
            # 2024/1/3 下午 4:50 处理通配符域名，将*.spider.com替换成spider.com
            if cert_name.startswith('*.'):
                cert_name = cert_name.replace('*.', '')
            if not os.path.exists('/www/server/panel/vhost/ssl/{}'.format(cert_name)):
                return public.returnMsg(False, '证书不存在!')
            cert_data = {}
            cert_data['cert_name'] = cert_name
            cert_data['cert'] = public.readFile('/www/server/panel/vhost/ssl/{}/fullchain.pem'.format(cert_name))
            cert_data['key'] = public.readFile('/www/server/panel/vhost/ssl/{}/privkey.pem'.format(cert_name))
            cert_data['info'] = json.loads(
                public.readFile('/www/server/panel/vhost/ssl/{}/info.json'.format(cert_name)))
            return cert_data
        except:
            return traceback.format_exc()

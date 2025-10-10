# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn>
# -------------------------------------------------------------------
import os
import random
# ------------------------------
# Docker模型测试模块 - 容器模型
# ------------------------------
import sys
import unittest

import docker.errors

panelPath = '/www/server/panel/'
os.chdir(panelPath)
sys.path.insert(0, panelPath + "class/")
import public
from btdockerModel import dk_public as dp
from btdockerModel import containerModel as dc


class TestParamManage():
    '''
        @name 获取字典对象
        @author wzz <2023/12/1 下午 2:32>
        @param 参数名<数据类型> 参数描述
        @return 数据类型
    '''

    def get_dict_obj(self):
        return public.dict_obj()

    '''
        @name 获取所有容器列表
        @author wzz <2023/12/1 下午 2:32>
        @param 参数名<数据类型> 参数描述
        @return 数据类型
    '''

    def get_container_list(self):
        return dc.main().get_list(self.get_dict_obj())

    '''
        @name 获取随机容器id
        @author wzz <2023/12/1 下午 2:32>
        @param 参数名<数据类型> 参数描述
        @return 数据类型
    '''

    def get_container_id(self):
        return self.get_container_list()['container_list'][0]['id']

class TestContainerModel(unittest.TestCase):
    """
    创建测试用例
    """

    def test_connect_client(self):
        """
        测试docker客户端连接，判断返回值是否是docker.client.DockerClient实例
        :return:
        """
        self.assertIsInstance(dp.docker_client(), docker.client.DockerClient)

    def test_get_list(self):
        """
        测试调用containerModel中的get_list方法，获取所有容器列表
        @return:
        """
        get = TestParamManage().get_dict_obj()
        self.assertIsInstance(dc.main().get_list(get), dict)

    def test_run(self):
        """
        测试创建容器
        @return:
        """
        get = TestParamManage().get_dict_obj()
        get.image = 'nginx:latest'
        get.name = 'test_{}'.format(random.randint(10000, 65535))
        get.port = {"80/tcp": format(random.randint(10000, 65535))}
        get.volumes = {"/www/wwwroot/test": {"bind": "/usr/share/nginx/html", "mode": "rw"}}
        get.environment = ''
        get.labels = ''
        get.network = ''
        get.cpu_quota = 0
        self.assertEqual(dc.main().run(get), {"status": True, "msg": "容器创建成功！"})

    def test_run_cmd(self):
        '''
            @name 测试命令创建容器
            @author wzz <2023/11/30 下午 3:07>
            @param get.cmd 包含docker run的命令，不能含有危险字符
            @return {"status": bool, "msg": info}
        '''
        get = TestParamManage().get_dict_obj()
        get.cmd = 'docker run -d --name test_{} nginx:latest'.format(random.randint(10000, 65535))
        self.assertEqual(dc.main().run_cmd(get), {"status": True, "msg": "命令已执行完毕！"})

    def test_upgrade_container(self):
        '''
            @name 测试更新容器
            @author wzz <2023/12/1 上午 9:53>
            @param 参数名<数据类型> 参数描述
            @return 数据类型
        '''
        get = TestParamManage().get_dict_obj()
        get.image = 'latest'
        container_list = dc.main().get_list(get)

        get.id = container_list['container_list'][0]['id']
        get.upgrade = '1'
        self.assertEqual(dc.main().upgrade_container(get), {"status": True, "msg": "更新成功！"})

    def test_upgrade_container_edit(self):
        '''
            @name 测试编辑容器
            @author wzz <2023/12/1 上午 9:53>
            @param 参数名<数据类型> 参数描述
            @return 数据类型
        '''
        get = TestParamManage().get_dict_obj()
        get.id = TestParamManage().get_container_id()
        get.image = 'nginx:latest'
        get.upgrade = '0'
        get.new_name = 'test_{}'.format(random.randint(10000, 65535))
        get.new_network = 'btnet'
        get.new_ip_address = '172.18.0.{}'.format(random.randint(2, 245))
        get.new_command = ''
        get.new_entrypoint = ''
        get.new_auto_remove = '0'
        get.new_privileged = '1'
        get.new_restart_policy = {"Name": "always"}
        get.new_mem_reservation = '0'
        get.new_cpu_quota = 0
        get.new_mem_limit = '0'
        get.new_labels = 'maintainer=NGINX Docker Maintainers <docker-maint@nginx.com>,,,,,,,,,,,,,,,,,\n'
        get.new_environment = "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin,,,,,,,,,,,,,,,,,\nNGINX_VERSION=1.25.3,,,,,,,,,,,,,,,,,\nNJS_VERSION=0.8.2,,,,,,,,,,,,,,,,,\nPKG_RELEASE=1~bookworm,,,,,,,,,,,,,,,,,\n"
        get.new_port = {"80/tcp": format(random.randint(10000, 65535))}
        get.new_publish_all_ports = '0'
        get.new_volumes = {"/www/wwwroot/test": {"bind": "/usr/share/nginx/html", "mode": "rw"}}
        result = dc.main().upgrade_container(get)
        self.assertTrue(result['status'], result['msg'])

    def test_commit(self):
        '''
            @name 测试生成镜像和导出成文件
            @author wzz <2023/12/1 下午 12:03>
            @param 参数名<数据类型> 参数描述
            @return 数据类型
        '''
        get = TestParamManage().get_dict_obj()
        get.id = TestParamManage().get_container_id()
        chars = 'qwertyuiopasdfghjklzxcvbnm0123456789'
        get.repository = 'akaishuichi/test{}'.format(random.choice(chars))
        get.tag = 'latest'
        get.message = ''
        get.author = ''
        get.path = '/www/dockertest'
        get.name = 'test_{}'.format(random.randint(10000, 65535))

        result = dc.main().commit(get)
        self.assertTrue(result['status'], result['msg'])

    def test_export(self):
        '''
            @name 测试容器导出文件tar
            @author wzz <2023/12/1 下午 2:05>
            @param 参数名<数据类型> 参数描述
            @return 数据类型
        '''
        get = TestParamManage().get_dict_obj()
        get.id = TestParamManage().get_container_id()
        get.path = '/www/dockertest'
        get.name = 'test_{}'.format(random.randint(10000, 65535))
        result = dc.main().export(get)
        self.assertTrue(result['status'], result['msg'])

    def test_docker_shell(self):
        '''
            @name 获取容器执行命令
            @author wzz <2023/12/1 下午 2:10>
            @param 参数名<数据类型> 参数描述
            @return 数据类型
        '''
        get = TestParamManage().get_dict_obj()
        get.id = TestParamManage().get_container_id()
        result = dc.main().docker_shell(get)
        print(result['msg'])
        self.assertTrue(result['status'], result['msg'])

    def test_del_container(self):
        '''
            @name 测试删除指定容器
            @author wzz <2023/12/1 下午 2:12>
            @param 参数名<数据类型> 参数描述
            @return 数据类型
        '''
        get = TestParamManage().get_dict_obj()
        get.id = TestParamManage().get_container_id()
        result = dc.main().del_container(get)
        self.assertTrue(result['status'], result['msg'])

    def test_set_container_status(self):
        '''
            @name 设置容器状态
            @author wzz <2023/12/1 下午 2:14>
            @param 参数名<数据类型> 参数描述
            @return 数据类型
        '''
        get = TestParamManage().get_dict_obj()
        get.id = TestParamManage().get_container_id()
        get.status = 'stop'
        result = dc.main().set_container_status(get)
        self.assertTrue(result['status'], result['msg'])
        get.status = 'start'
        result = dc.main().set_container_status(get)
        self.assertTrue(result['status'], result['msg'])
        get.status = 'pause'
        result = dc.main().set_container_status(get)
        self.assertTrue(result['status'], result['msg'])
        get.status = 'unpause'
        result = dc.main().set_container_status(get)
        self.assertTrue(result['status'], result['msg'])
        get.status = 'reload'
        result = dc.main().set_container_status(get)
        self.assertTrue(result['status'], result['msg'])
        get.status = 'kill'
        result = dc.main().set_container_status(get)
        self.assertTrue(result['status'], result['msg'])
        get.status = 'start'
        result = dc.main().set_container_status(get)
        self.assertTrue(result['status'], result['msg'])

    # def test_get_container_info(self):
    #     '''
    #         @name 测试获取指定容器信息
    #         @author wzz <2023/12/1 下午 2:19>
    #         @param 参数名<数据类型> 参数描述
    #         @return 数据类型
    #     '''



if __name__ == '__main__':
    # unittest.main()
    # 创建测试套件
    suite = unittest.TestSuite()
    suite.addTest(TestContainerModel('test_connect_client'))
    suite.addTest(TestContainerModel('test_get_list'))
    suite.addTest(TestContainerModel('test_run'))
    suite.addTest(TestContainerModel('test_run_cmd'))
    suite.addTest(TestContainerModel('test_upgrade_container'))
    suite.addTest(TestContainerModel('test_upgrade_container_edit'))
    suite.addTest(TestContainerModel('test_commit'))
    suite.addTest(TestContainerModel('test_export'))
    suite.addTest(TestContainerModel('test_docker_shell'))
    suite.addTest(TestContainerModel('test_del_container'))
    suite.addTest(TestContainerModel('test_set_container_status'))

    # 创建测试运行器
    runner = unittest.TextTestRunner()
    runner.run(suite)

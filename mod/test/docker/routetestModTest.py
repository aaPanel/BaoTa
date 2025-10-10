# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wzz <wzz@bt.cn> 
# -------------------------------------------------------------------
# ------------------------------
# Docker模型测试模块 - 容器模型
# ------------------------------
import sys
import unittest

if "/www/server/panel" not in sys.path:
    sys.path.insert(0, '/www/server/panel')

from mod.project.docker.routetestMod import main as routetest_main

routetest = routetest_main()


#
class TestContainerModel(unittest.TestCase):
    """
    创建测试用例
    """

    def test_returnResult(self):
        """
        测试模型测试方法，检测返回结果是否为json格式数据
        @return:
        """
        result = routetest.returnResult({'data': {}})
        self.assertIsInstance(result, dict)
        self.assertIn('status', result)
        self.assertIn('msg', result)
        self.assertIn('data', result)
        self.assertIn('code', result)
        self.assertIn('timestamp', result)

    def test_wsRequest(self):
        """
        使用ws长链请求ws://127.0.0.1:8888/ws_mod
        并发送{"mod_name":"docker","sub_mod_name":"routetest","def_name":"wsRequest","ws_callback":"111"}，检测返回结果是否为True

            备注：请将__init__.py中ws模型路由的comReturn和csrf检查注释掉再测试
        @param get:
            {"mod_name":"docker","sub_mod_name":"routetest","def_name":"wsRequest","ws_callback":"111"}
            {"mod_name":"模型名称","sub_mod_name":"子模块名称","def_name":"函数名称","ws_callback":"ws必传参数，传111",其他参数接后面}
        @return:
        """
        import json
        import time
        from websocket import create_connection
        ws = create_connection("ws://127.0.0.1:8888/ws_mod")
        print("连接状态：", ws.connected)

        params = {"mod_name": "docker", "sub_mod_name": "routetest", "def_name": "wsRequest", "ws_callback": "111"}
        ws.send(json.dumps(params))

        while True:
            result = ws.recv()
            print("接收到结果：", result.strip())

            try:
                result_data = json.loads(result)
                if "result" in result_data and "callback" in result_data:
                    if result_data["result"] == True and result_data["callback"] == "111":
                        print("websocket测试成功！")
                        break
            except Exception as e:
                pass

            # 等待一段时间再继续接收消息
            time.sleep(0.1)

        ws.close()
        self.assertIn('result', result)
        self.assertIn('callback', result)


if __name__ == '__main__':
    # unittest.main()
    # 创建测试套件
    suite = unittest.TestSuite()
    suite.addTest(TestContainerModel('test_returnResult'))
    suite.addTest(TestContainerModel('test_wsRequest'))

    # 创建测试运行器
    runner = unittest.TextTestRunner()
    runner.run(suite)

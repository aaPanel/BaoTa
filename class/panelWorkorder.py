#!/www/server/coll/pyenv/bin/python
# -*- coding: utf-8 -*-
#  + -------------------------------------------------------------------
# | 宝塔Linux面板
#  + -------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http:#bt.cn) All rights reserved.
#  + -------------------------------------------------------------------
# | Author: LX
# | Date:  2020/12/29
#  + -------------------------------------------------------------------
import datetime
import selectors
import sys, os, json
import threading
import uuid

try:
    import thread
except ImportError:
    import _thread as thread

sys.path.insert(0, 'class/')
import public
import system
from BTPanel import session


try:
    import websocket
except ImportError:
    os.system('{} -m pip install websocket-client'.format(public.get_python_bin()))
    import websocket

debug = False

SERVER = "https://work.bt.cn"
WEBSOCKET_SERVER = "wss://work.bt.cn"
workorder_clients = {}
connections = {}


class panelWorkorder:
    max_retry = 3
    ping_interval = 15  # s

    unable_connect_msg = "无法连接到工单服务器。"
    user_tip = "请先绑定官网账号，再使用工单系统！"

    def find_user_info(self):
        try:
            user_data_file = "/www/server/panel/data/userInfo.json"
            if not os.path.exists(user_data_file):
                return None
            user_info = json.loads(public.ReadFile(user_data_file))
            return {
                "uid": user_info["uid"],
                "username": user_info["username"],
                "address": user_info["address"],
                "serverid": user_info["serverid"],
            }
        except Exception as e:
            pass
        return None

    def allow(self, get):
        try:
            user_info = self.find_user_info()
            args = user_info
            args["version"] = session["version"]
            server = SERVER + "/workorder/allow?uid={uid}&username={" \
                              "username}&version={version}&address={" \
                              "address}&serverid={serverid}".format(**args)
            response = public.HttpGet(server, headers=self.get_headers())
            if response:
                result = json.loads(response)
                if result["status"]:
                    return public.returnMsg(status=True, msg="授权用户。")
        except:
            pass
        return public.returnMsg(status=False, msg="非授权用户。")

    def get_error_log(self):
        return "yes"

    def get_panel_info(self):
        data = {
            "system": system.system().GetSystemVersion(),
            "version": session["version"]
        }
        return data

    def get_headers(self):
        headers = {
            "User-Agent": "BT PANEL WORKORDER LINUX CLIENT/VERSION 1.0"
        }
        return headers

    def get_user_info(self, get):
        try:
            from flask import jsonify
            import json
            user_info = self.find_user_info()
            if user_info is not None:
                user_info.update({
                    "status": True
                })
                return jsonify(user_info)
        except:
            pass
        return public.returnMsg(False, self.user_tip)

    def close(self, get):
        try:
            from flask import jsonify
            import requests
            data = get
            workorder = data.workorder
            user_info = self.find_user_info()
            if user_info:
                if debug:
                    print("用户信息：")
                    print("uid: {}".format(user_info['uid']))
                    print("user name: {}".format(user_info['username']))
                data = {
                    "workorder": workorder
                }
                data.update(user_info)

                server = SERVER + "/workorder/close"
                response = public.HttpPost(server,
                                           data,
                                           headers=self.get_headers())
                # response = requests.post(server, headers=self.get_headers(),
                #                          data=data)
                if response:
                    return jsonify(json.loads(response))
            else:
                return jsonify({
                    "status": False,
                    "msg": self.user_tip
                })
        except Exception as e:
            print(e)

        return jsonify({
            "status": False,
            "msg": "关闭工单出现错误。"
        })

    def create(self, get):
        try:
            from flask import jsonify
            data = get
            debug_path = 'data/debug.pl'
            if os.path.exists(debug_path):
                return jsonify({
                    "status": False,
                    "msg": "暂不支持在开发者模式提交工单！",
                    "error_code": 10004
                })
            contents = data.contents
            user_info = self.find_user_info()
            if not user_info:
                return jsonify({
                    "status": False,
                    "msg": "请先绑定官网账号。",
                    "error_code": 10001
                })

            uid = user_info['uid']
            user = user_info['username']
            address = user_info["address"]
            serverid = user_info["serverid"]

            collect = data.collect
            other = {}
            # if collect:
            #     other = self.get_error_log()

            data = {
                "contents": contents,
                "other": other,
                "panel_info": json.dumps(self.get_panel_info()),
                "uid": uid,
                "username": user,
                "collect": collect,
                "address": address,
                "serverid": serverid
            }

            server = SERVER + "/workorder/create"
            response = public.HttpPost(server, data, headers=self.get_headers())
            if response:
                return jsonify(json.loads(response))
            else:
                if debug:
                    print("创建工单异常：")
                    print(response)

            # import requests
            # server = SERVER + "/workorder/create"
            # response = requests.post(server, headers=self.get_headers(),
            #                          data=data)
            # if response.status_code == 200:
            #     return jsonify(response.json())
            # if response.status_code in [500, 502]:
            #     return jsonify({
            #         "status": False,
            #         "msg": "网络连接异常。",
            #         "error_code": 10001
            #     })
            # public.WriteLog("wd", response.text)
        # except requests.exceptions.ConnectionError as ce:
        #     return jsonify({
        #         "status": False,
        #         "msg": "网络连接异常。",
        #         "error_code": 10001
        #     })
        except Exception as e:
            if debug:
                print("创建工单异常：")
                print(e)
            # public.WriteLog("ws error", str(e))
        return jsonify({
            "status": False,
            "msg": "工单创建失败！",
            "error_code": 10001
        })

    def list(self, get):
        try:
            from flask import jsonify
            user_info = self.find_user_info()
            if not user_info:
                return jsonify({
                    "status": False,
                    "msg": "请先绑定官网账号。"
                })

            # import requests
            server = SERVER + \
                     "/workorder/list?uid={uid}&username={" \
                     "username}&serverid={serverid}&address={" \
                     "address}".format(**user_info)
            # response = requests.get(server, headers=self.get_headers(),
            #                         data=user_info)
            # if response.status_code == 200:
            #     return jsonify(response.json())
            response = public.HttpGet(server, headers=self.get_headers())
            if response:
                return jsonify(json.loads(response))
        except Exception as e:
            pass
        return jsonify({
            "status": False,
            "msg": "获取工单列表失败！"
        })

    def get_messages(self, get):
        try:
            data = get
            workorder = data.workorder

            from flask import jsonify
            # import requests
            server_url = SERVER + "/get_messages?workorder={}".format(workorder)
            # response = requests.get(server_url, headers=self.get_headers(),
            #                         data=data)
            # if response.status_code == 200:
            #     result = response.json()
            #     # if "error_code" not result
            #     return jsonify(result)
            response = public.HttpGet(server_url, headers=self.get_headers())
            if response:
                return json.loads(response)
        except Exception as e:
            print(e)
        return jsonify({
            "status": False,
            "msg": "获取消息列表失败！"
        })

    def start_workorder_client(self, clients, workorder, ping_interval,
                               on_message,
                               on_error,
                               on_close,
                               on_pong,
                               on_open):
        try:
            # websocket.enableTrace(True)
            if connections[workorder]:

                connected = False
                if workorder in workorder_clients \
                        and workorder_clients[workorder] \
                        and workorder_clients[workorder].sock \
                        and workorder_clients[workorder].sock.connected:
                    connected = True

                if not connected:
                    if debug:
                        print("{}开启新的websocket客户端...".format(workorder))
                    user_info = self.find_user_info()
                    if not user_info:
                        return
                    uid = user_info['uid']
                    user = user_info["username"]
                    serverid = user_info["serverid"]
                    address = user_info["address"]
                    ws = websocket.WebSocketApp(
                        WEBSOCKET_SERVER + "/workorder/client?uid={"
                                           "}&username={}&workorder={"
                                           "}&serverid={}&address={}"\
                        .format(uid, user, workorder, serverid, address),
                        on_message=on_message,
                        on_error=on_error,
                        on_close=on_close,
                        on_pong=on_pong)

                    ws.on_open = on_open

                    thread = threading.Thread(target=ws.run_forever)
                    thread.setDaemon(True)
                    thread.start()
                    clients[workorder] = ws
        except Exception as e:
            print(e)

    def check_client_status(self, workorder):
        """检查客户端连接状态"""

        if workorder in workorder_clients \
                and workorder_clients[workorder] \
                and workorder_clients[workorder].sock \
                and workorder_clients[workorder].sock.connected:
            return True
        return False

    panel_clients = {}
    ping_record = {}

    def client(self, ws, get):
        """面板端客户端通信连接"""

        data = get
        workorder = data.workorder
        if not workorder:
            return {
                "type": 6,
                "content": "未找到工单。",
            }

        if workorder not in self.panel_clients.keys():
            self.panel_clients[workorder] = {}

        if workorder not in self.ping_record.keys():
            self.ping_record[workorder] = datetime.datetime.now()

        session_id = str(uuid.uuid1()).replace("-", "")

        if debug:
            print("新标签页: {} 连接。".format(session_id))

        def _on_message(socket_bp_workorder, message):
            # public.WriteLog("DEBUG/1", "On message:")
            try:
                if not message:
                    return

                if type(message) == bytes:
                    message = message.decode("utf-8")

                if type(message) == str:
                    temp_message = json.loads(message)
                else:
                    temp_message = message

                if temp_message:
                    # 转发
                    for key, _ws in self.panel_clients.get(workorder,
                                                           {}).items():
                        if _ws and not _ws.closed:
                            _ws.send(message)

                    if temp_message:
                        if 'type' in temp_message and temp_message['type'] == 5:
                            if 'content' in temp_message and \
                                    temp_message["content"] == "close":
                                connections[workorder] = False
                                workorder_clients[workorder].close()
                                if debug:
                                    print("关闭连接5。")
                                ws.close()

                        if 'type' in temp_message and temp_message['type'] == 6:
                            connections[workorder] = False
                            workorder_clients[workorder].close()
                            ws.close()
                            if debug:
                                print("关闭连接6。")

            except Exception as e:
                if debug:
                    print(e)

        def _on_error(sock, error):
            if debug:
                print("error:")
                print(error)

        def _on_close(sock):
            if debug:
                print("close.")

            try:
                del workorder_clients[workorder]
            except Exception as e:
                if debug:
                    print("del workorder client error: " + str(e))

            try:
                self.panel_clients[workorder].pop(session_id)
            except Exception as e:
                if debug:
                    print("pop session id :" + str(e))
                pass

        def _on_pong(socket, data):
            if debug:
                print("pong")
            for key, _ws in self.panel_clients.get(workorder, {}).items():
                if _ws and not _ws.closed:
                    _ws.send("pong")

        def _on_open(socket):
            socket = workorder_clients.get(workorder)
            if socket and socket.sock and socket.sock.connected:
                socket.sock.ping()
                if debug:
                    print("首次ping.")
                self.ping_record[workorder] = datetime.datetime.now()

        try:
            connections[workorder] = True
            self.start_workorder_client(workorder_clients, workorder,
                                        self.ping_interval, _on_message,
                                        _on_error,
                                        _on_close,
                                        _on_pong, _on_open)

            def read_websocket_data(socket, mask):
                # message = socket.read()
                # while True:
                message = ws.receive()
                if not message:
                    return
                if debug:
                    print("接收到客户端消息:")
                    print(message)

                send = False
                retry = 0
                while not send and retry < self.max_retry:
                    try:
                        if self.check_client_status(workorder):
                            sock = workorder_clients.get(workorder)
                            # 限制ping间隔时间
                            if message == "ping":
                                last_ping_time = self.ping_record.get(workorder,
                                                                      None)
                                now = datetime.datetime.now()
                                if debug:
                                    print("距离上次ping: {}s".format(
                                        (now - last_ping_time).seconds))
                                interval = (
                                                   now - last_ping_time).seconds - self.ping_interval
                                if not last_ping_time or interval >= 0 or abs(
                                        interval) <= 2:
                                    sock.sock.ping()
                                    self.ping_record[workorder] = now
                                    if debug:
                                        print("ping")
                                # else:
                                #     ws.send("pong")
                                break

                            # 转发
                            sock.send(message)
                            send = True

                            # 同步到其他客户端
                            if debug:
                                print("检查客户端：")
                                print(self.panel_clients.get(workorder))
                            for key, _ws in self.panel_clients.get(workorder,
                                                                   {}).items():
                                if key != session_id:
                                    if debug:
                                        print("转发到客户端：{}".format(session_id))
                                    try:
                                        if _ws and not _ws.closed:
                                            _ws.send(message)
                                    except:
                                        pass
                            break
                    except:
                        pass
                    if connections[workorder]:
                        if debug:
                            print("重试连接websocket客户端。")
                        self.start_workorder_client(workorder_clients,
                                                    workorder,
                                                    self.ping_interval,
                                                    _on_message, _on_error,
                                                    _on_close, _on_pong,
                                                    _on_open)
                        retry += 1
                    else:
                        break

                if retry >= self.max_retry:
                    ws.send(json.dumps({
                        "type": 6,
                        "content": self.unable_connect_msg,
                        "workorder": workorder
                    }))
                    connections[workorder] = False

                if message == "ping":
                    return

                if type(message) == str:
                    temp_message = json.loads(message)
                else:
                    temp_message = message
                if temp_message:
                    if 'type' in temp_message and temp_message['type'] == 5:
                        if 'content' in temp_message and \
                                temp_message["content"] == "close":
                            if debug:
                                print("关闭连接by client。")
                            connections[workorder] = False
                            workorder_clients[workorder].close()
                            ws.close()

            retry = 0
            epoll = selectors.DefaultSelector()
            fileno = ws.handler.socket.fileno()
            epoll.register(ws.handler.socket, selectors.EVENT_READ,
                           read_websocket_data)
            if session_id not in self.panel_clients[workorder].keys():
                self.panel_clients[workorder][session_id] = ws

            while True:
                if not connections[workorder] or retry >= self.max_retry:
                    break
                if debug:
                    print("selecting...")
                try:
                    if ws.handler.socket.fileno() < 0:
                        break
                    events = epoll.select(self.ping_interval)

                    for key, mask in events:
                        callback = key.data
                        callback(key.fileobj, mask)
                except Exception as e:
                    if debug:
                        print("Read client data error:" + str(e))
                    break

                if connections[workorder]:
                    try:
                        will_retry = False
                        if workorder not in workorder_clients or not \
                                workorder_clients[workorder]:
                            will_retry = True
                        if will_retry or not workorder_clients[
                            workorder].sock or not workorder_clients[
                            workorder].sock.connected:
                            if debug:
                                print("重试连接。。。")
                            self.start_workorder_client(workorder_clients,
                                                        workorder, 3,
                                                        _on_message,
                                                        _on_error,
                                                        _on_close,
                                                        _on_pong,
                                                        _on_open)
                            retry += 1
                            if debug:
                                print("Retry count:", retry)
                    except Exception as e:
                        if debug:
                            print(e)
                        connections[workorder] = False
                        pass

            if retry >= self.max_retry:
                # public.WriteLog("Workorder", "重试次数已达到最大数2。")
                ws.send(json.dumps({
                    "type": 6,
                    "content": self.unable_connect_msg,
                    "workorder": workorder
                }))
                # public.WriteLog("Workorder", unable_connect_msg)
                connections[workorder] = False

        except Exception as e:
            # public.WriteLog("WS", str(e))
            if debug:
                print("Error:", e)
            try:
                ws.send({
                    "type": 6,
                    "content": str(e),
                    "workorder": workorder
                })
            except Exception as e:
                print(e)

        finally:
            try:
                self.panel_clients[workorder].pop(session_id)
            except Exception as e:
                pass

            try:
                epoll.unregister(fileno)
            except:
                pass

            try:
                keep_client_connect = False
                if workorder in self.panel_clients.keys():
                    for key, _ws in self.panel_clients[workorder].items():
                        if _ws and not _ws.closed:
                            keep_client_connect = True

                if not keep_client_connect:
                    if workorder in workorder_clients.keys():
                        workorder_clients[workorder].close()
                        if debug:
                            print("关闭客户端连接。")
                        # public.WriteLog("WS", "close client")
                    self.ping_record.pop(workorder)
                else:
                    if debug:
                        print("保持客户端连接。")

            except Exception as e:
                if debug:
                    print("Exception: ", str(e))
    #
    # if __name__ == "__main__":
    #     from gevent import pywsgi
    #     from geventwebsocket.handler import WebSocketHandler
    #     from flask import Flask
    #     from flask_sockets import Sockets
    #
    #     app = Flask(__name__)
    #     socket = Sockets(app)
    #
    #     app.register_blueprint(bp_workorder)
    #     socket.register_blueprint(bp_workorder_socket)
    #
    #     server = pywsgi.WSGIServer(('', 5802), app,
    #                                handler_class=WebSocketHandler)
    #     server.serve_forever()

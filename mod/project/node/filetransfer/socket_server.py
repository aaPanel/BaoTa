import json
import socket
import struct
import sys
import threading
import os
import atexit
from typing import Callable, Any, Union, Tuple, Optional, List


class StatusServer:
    def __init__(self, get_status_func: Callable[[bool], Any], server_address: Union[str, Tuple[str, int]]):
        """
        初始化服务端
        :param get_status_func: 获取状态的函数，返回当前进程状态字典, 支持一个参数 init，
                当init为True时，表示获取初始化状态，否则为更新状态
        :param server_address: 本地套接字文件路径（Unix域）或 (host, port)（TCP）
        """
        self.get_status_func = get_status_func
        self.server_address = server_address
        self.clients: List[socket.socket] = []
        self.lock = threading.Lock()  # 线程锁
        self.running = False
        self.server_socket = None

    def handle_client(self, client_socket):
        """处理客户端连接"""
        try:
            # 发送初始状态
            new_status = self.get_status_func(True)
            status_bytes = json.dumps(new_status).encode()  # 使用 JSON 更安全
            packed_data = len(status_bytes).to_bytes(4, 'little') + status_bytes  # 添加长度头

            # 添加到客户端列表
            try:
                # 分块发送
                client_socket.sendall(packed_data)  # 发送结束标志
            except Exception as e:
                print(f"Failed to send update to client: {e}")
                client_socket.close()
                return

            with self.lock:
                self.clients.append(client_socket)

            # 保持连接以支持后续更新
            while self.running:
                try:
                    # 可选：接收客户端心跳或命令
                    data = client_socket.recv(1024)
                    if not data:
                        break
                except:
                    break

        finally:
            # 关闭连接并从列表中移除
            client_socket.close()
            with self.lock:
                if client_socket in self.clients:
                    self.clients.remove(client_socket)

    def start_server(self):
        """启动本地套接字服务端"""
        self.running = True

        if isinstance(self.server_address, str):
            # Unix 域套接字
            self.server_socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            try:
                os.unlink(self.server_address)
            except OSError:
                if os.path.exists(self.server_address):
                    raise
            self.server_socket.bind(self.server_address)
        else:
            # TCP 套接字
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(self.server_address)

        self.server_socket.listen(5)
        print(f"Server is listening on {self.server_address}...")

        try:
            self.running = True
            while self.running:
                client_socket, _ = self.server_socket.accept()
                print("Client connected")

                # 启动新线程处理客户端
                client_thread = threading.Thread(target=self.handle_client, args=(client_socket,))
                client_thread.start()
        except KeyboardInterrupt:
            print("Shutting down server...")
        finally:
            self.stop()

    def stop(self):
        """停止服务端并清理资源"""
        if not self.running:
            return
        self.running = False

        with self.lock:
            for client in self.clients:
                client.close()
            self.clients.clear()

        if self.server_socket:
            self.server_socket.close()
            self.server_socket = None

        # 清理 Unix 套接字文件
        if isinstance(self.server_address, str) and os.path.exists(self.server_address):
            os.remove(self.server_address)
            print(f"Socket file removed: {self.server_address}")

    def update_status(self, update_data: Optional[dict]=None):
        """获取最新的状态并推送给所有客户端"""
        if not update_data:
            new_status = self.get_status_func(False)
        else:
            new_status = update_data
        status_bytes = json.dumps(new_status).encode()  # 使用 JSON 更安全
        packed_data = len(status_bytes).to_bytes(4, 'little') + status_bytes  # 添加长度头

        with self.lock:
            for client in self.clients:
                print("Sending update to client...")
                print(len(status_bytes), status_bytes, packed_data)
                try:
                    client.sendall(packed_data)  # 直接发送完整数据
                except Exception as e:
                    print(f"Failed to send update to client: {e}")
                    client.close()
                    if client in self.clients:
                        self.clients.remove(client)


class StatusClient:
    def __init__(self, server_address, callback=None):
        """
        初始化客户端
        :param server_address: Unix 域路径（字符串） 或 TCP 地址元组 (host, port)
        :param callback: 接收到状态更新时的回调函数，接受一个 dict 参数
        """
        self.server_address = server_address
        self.callback = callback
        self.sock: Optional[socket.socket] = None
        self.running = False
        self.receive_thread = None

    def connect(self):
        """连接到服务端"""
        if isinstance(self.server_address, str):
            print("Connecting to Unix socket...", self.server_address)
            # Unix 域套接字
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self.sock.connect(self.server_address)
        else:
            # TCP 套接字
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect(self.server_address)

        print("Connected to server.")

        # 启动接收线程
        self.running = True
        self.receive_thread = threading.Thread(target=self._receive_loop, daemon=True)
        self.receive_thread.start()

    def _receive_loop(self):
        buffer = b''
        while self.running:
            try:
                # 读取长度头
                while len(buffer) < 4:
                    data = self.sock.recv(4)
                    if not data:
                        raise ConnectionResetError("Server closed the connection")
                    buffer += data
                length = int.from_bytes(buffer[:4], 'little')
                buffer = buffer[4:]

                # 读取完整数据
                while len(buffer) < length:
                    data = self.sock.recv(length - len(buffer))
                    if not data:
                        raise ConnectionResetError("Server closed the connection")
                    buffer += data
                message = buffer[:length]
                buffer = buffer[length:]

                # 解析JSON
                status = json.loads(message.decode())
                if self.callback:
                    self.callback(status)
            except ConnectionResetError as e:
                print("连接中断:", e)
                self.disconnect()
                break
            except json.JSONDecodeError as e:
                print("JSON解析失败:", e)
                continue
            except Exception as e:
                print("接收错误:", e)
                self.disconnect()
                break

    def disconnect(self):
        """断开连接"""
        self.running = False
        if self.sock:
            self.sock.close()
            self.sock = None
        print("Disconnected from server.")

    def stop(self):
        """停止客户端"""
        self.disconnect()
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join()
        print("Client stopped.")

    def wait_receive(self):
        if self.receive_thread and self.receive_thread.is_alive():
            self.receive_thread.join()


# 注册退出清理钩子
def register_cleanup(server_instance):
    def cleanup():
        server_instance.stop()

    atexit.register(cleanup)

# # 示例使用
# if __name__ == '__main__' and "server" in sys.argv:
#
#     import time
#
#     # 模拟的状态存储
#     process_status = {
#         'process1': 'running',
#         'process2': 'stopped',
#         "big_data": "<AAAAAAAAAAAAAAAAAFFFFFFFFFFFFFFFFFFAAAAFFFFFFFFFFFFFFFAAAAAAAAAAAAAAAAAAAAAAAAA>"
#     }
#
#     def get_status():
#         return process_status
#
#     # 设置 Unix 域套接字地址
#     server_address = './socket_filetransfer.sock'
#
#     # 创建服务端实例
#     server = StatusServer(get_status, server_address)
#     register_cleanup(server)  # 注册退出时清理
#
#     # 启动服务端线程
#     server_thread = threading.Thread(target=server.start_server)
#     server_thread.daemon = True
#     server_thread.start()
#
#     # 模拟状态更新
#     try:
#         while True:
#             print(">>>>>>>change<<<<<<<<<<<<<<<")
#             time.sleep(5)
#             process_status['process1'] = 'stopped' if process_status['process1'] == 'running' else 'running'
#             server.update_status()
#
#             time.sleep(5)
#             process_status['process2'] = 'running' if process_status['process2'] == 'stopped' else 'stopped'
#             server.update_status()
#     except KeyboardInterrupt:
#         pass
#
# # 示例使用
# if __name__ == '__main__' and "client" in sys.argv:
#     # Unix 域套接字示例：
#     server_address = './socket_filetransfer.sock'
#
#     # 示例回调函数
#     def on_status_update(status_dict):
#         print("[Callback] New status received:")
#         for k, v in status_dict.items():
#             print(f" - {k}: {v}")
#
#
#     client = StatusClient(server_address, callback=on_status_update)
#     try:
#         client.connect()
#
#         # 主线程保持运行，防止程序退出
#         while client.running:
#             pass
#     except KeyboardInterrupt:
#         print("Client shutting down...")
#         client.stop()

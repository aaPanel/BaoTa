import time
import requests
import re
from typing import List, Dict, Union
from concurrent.futures import ThreadPoolExecutor, as_completed  # 引入多线程库


class DockerMirrorDetector:
    # Docker V2 协议需要的 Header
    DEFAULT_HEADERS = {
        "User-Agent": "Docker-Client/19.03.8 (linux)",
        "Accept": "application/vnd.docker.distribution.manifest.list.v2+json, application/vnd.oci.image.index.v1+json, application/vnd.docker.distribution.manifest.v2+json, application/vnd.oci.image.manifest.v1+json"
    }
    
    # ANSI 颜色代码用于美化输出
    class Colors:
        HEADER = '\033[95m'
        BLUE = '\033[94m'
        GREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
    
    def __init__(self, mirror_url: str, image: str = "library/nginx", tag: str = "latest", debug: bool = False,
                 timeout: int = 5):
        """
        初始化测试器
        :param mirror_url: 镜像站地址 (例如 hub.1panel.dev)
        :param image: 测试用的镜像 (默认 library/nginx)
        :param tag: 镜像标签 (默认 latest)
        :param debug: 是否打印详细调试信息
        :param timeout: 请求超时时间
        """
        # 自动去除 URL 末尾的斜杠和 http/https 前缀，保持纯净域名
        self.mirror_url = mirror_url.replace("https://", "").replace("http://", "").rstrip("/")
        self.image = image
        self.tag = tag
        self.debug = debug
        self.timeout = timeout
        self.base_url = f"https://{self.mirror_url}"
        
        # 禁止 urllib3 打印 InsecureRequestWarning，仅在 __init__ 执行一次
        requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)
    
    def _log(self, message: str, level: str = "INFO"):
        """内部方法：格式化打印日志"""
        if not self.debug:
            return
        
        prefix = ""
        if level == "INFO":
            prefix = f"{self.Colors.BLUE}[INFO]{self.Colors.ENDC}"
        elif level == "SUCCESS":
            prefix = f"{self.Colors.GREEN}[SUCCESS]{self.Colors.ENDC}"
        elif level == "ERROR":
            prefix = f"{self.Colors.FAIL}[ERROR]{self.Colors.ENDC}"
        elif level == "WARN":
            prefix = f"{self.Colors.WARNING}[WARN]{self.Colors.ENDC}"
        
        print(f"{prefix} {message}")
    
    def _parse_auth_header(self, header_value: str):
        """解析 WWW-Authenticate 头"""
        realm_match = re.search(r'realm="([^"]+)"', header_value)
        service_match = re.search(r'service="([^"]+)"', header_value)
        
        realm = realm_match.group(1) if realm_match else None
        service = service_match.group(1) if service_match else None
        return realm, service
    
    def check(self) -> Dict:
        """
        同步检测单个镜像站 (使用 requests)
        这个方法会被 test_batch 和 单次调用复用
        """
        result = {
            "url": self.base_url,
            "available": False,
            "latency": 0,
            "status_code": 0,
            "msg": "",
            "ts": int(time.time())
        }
        
        self._log(f"开始测试镜像站: {self.Colors.BOLD}{self.mirror_url}{self.Colors.ENDC}")
        # 在多线程环境中，每个线程应该有自己的 Session，避免竞争
        session = requests.Session()
        session.verify = False  # 忽略 SSL 证书验证
        
        try:
            # 1. 握手检查 /v2/
            v2_url = f"{self.base_url}/v2/"
            self._log(f"正在连接握手: {v2_url}")
            
            resp = session.get(v2_url, headers=self.DEFAULT_HEADERS, timeout=self.timeout)
            result['status_code'] = resp.status_code
            
            auth_headers = self.DEFAULT_HEADERS.copy()
            
            # 2. 处理认证 (如果返回 401)
            if resp.status_code == 401:
                auth_header = resp.headers.get('WWW-Authenticate', '')
                self._log(f"需要认证，解析 Header: {auth_header}", "WARN")
                
                realm, service = self._parse_auth_header(auth_header)
                if realm and service:
                    token_url = f"{realm}?service={service}&scope=repository:{self.image}:pull"
                    self._log(f"获取 Token: {token_url}")
                    
                    token_resp = session.get(token_url, verify=False, timeout=self.timeout)
                    if token_resp.status_code == 200:
                        token = token_resp.json().get('token')
                        auth_headers['Authorization'] = f"Bearer {token}"
                        self._log("Token 获取成功", "SUCCESS")
                    else:
                        raise Exception(f"获取 Token 失败: {token_resp.status_code}")
                else:
                    raise Exception("无法解析认证 Header")
            
            elif resp.status_code != 200:
                raise Exception(f"握手失败，状态码: {resp.status_code}")
            
            # 3. 拉取 Manifest 清单 (真正的可用性测试)
            manifest_url = f"{self.base_url}/v2/{self.image}/manifests/{self.tag}"
            self._log(f"尝试获取 Manifest: {manifest_url}")
            
            # 这里是主要的测速点
            req_start = time.time()
            resp = session.get(manifest_url, headers=auth_headers, timeout=self.timeout)
            req_end = time.time()
            
            if resp.status_code == 200:
                latency_ms = int((req_end - req_start) * 1000)
                result['available'] = True
                result['latency'] = latency_ms
                result['msg'] = "OK"
                self._log(f"测试通过! 延迟: {latency_ms}ms", "SUCCESS")
            else:
                result['msg'] = f"Manifest获取失败: {resp.status_code}"
                # 仅在 debug 模式下打印失败的详情
                if self.debug:
                    self._log(f"Manifest获取失败详情: {resp.status_code} \n{resp.text[:100]}", "ERROR")
        
        except requests.exceptions.Timeout:
            result['msg'] = "Timeout"
            self._log(f"请求超时 ({self.timeout}s)", "ERROR")
        except requests.exceptions.ConnectionError:
            result['msg'] = "Connection Error"
            self._log("连接错误，可能域名不存在或被防火墙拦截", "ERROR")
        except Exception as e:
            result['msg'] = str(e)
            self._log(f"发生异常: {str(e)}", "ERROR")
        
        return result
    
    @staticmethod
    def test_batch(mirror_list: List[str], image: str = "library/nginx", tag: str = "latest", max_workers: int = 10,
                   timeout: int = 5) -> List[Dict]:
        """
        批量多线程检测接口 (替换了 asyncio)
        :param mirror_list: 镜像站URL列表
        :param image: 测试用的镜像
        :param tag: 镜像标签
        :param max_workers: 最大并发线程数
        :param timeout: 请求超时时间
        :return: 结果列表
        """
        results = []
        
        # 使用 ThreadPoolExecutor 来管理并发
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 提交任务，为每个镜像站创建一个 DockerMirrorDetector 实例并调用其 check 方法
            # 注意：这里传入 debug=False，以避免多线程下日志交错打印
            future_to_url = {
                executor.submit(
                    DockerMirrorDetector(
                        mirror_url=url,
                        image=image,
                        tag=tag,
                        debug=False,  # 批量模式下通常关闭 debug
                        timeout=timeout
                    ).check
                ): url for url in mirror_list
            }
            
            # 收集结果
            for future in as_completed(future_to_url):
                try:
                    # 获取线程执行的结果（即 check 方法返回的字典）
                    result = future.result()
                    results.append(result)
                except Exception as exc:
                    # 捕获线程内部的意外异常
                    url = future_to_url[future]
                    results.append({
                        "url": url,
                        "available": False,
                        "latency": 0,
                        "status_code": 0,
                        "msg": f"ThreadPool Exception: {exc}",
                        "ts": int(time.time())
                    })
        
        return results


# ==========================================
# 使用示例
# ==========================================

if __name__ == '__main__':
    
    # print("--- 1. 单个测试模式 (Debug开启) ---")
    # 实例化：只需传入域名，image可选
    # 注意：单次调用需要自行调用 check()
    # tester = DockerMirrorDetector(mirror_url="https://docker.1ms.run", debug=False, timeout=10)
    # res = tester.check()
    # 
    # # 打印最终结果结构
    # print("\n单次测试结果:", res)
    # print("=" * 75)
    
    print("\n--- 2. 批量多线程测试模式 ---")

    mirrors = [
        "docker.m.daocloud.io",  # 可用
        "docker.nju.edu.cn",  # 可用
        # "registry-1.docker.io",  # 官方镜像站
        # "this-domain-not-exist-123.com",  # 模拟一个域名无法解析
        # "registry.aliyuncs.com"  # 阿里云等可能需要登录
    ]

    # 调用静态方法进行多线程批量测试
    start_t_batch = time.time()
    results = DockerMirrorDetector.test_batch(mirrors, max_workers=5, timeout=5)
    end_t_batch = time.time()
    
    
    # # 按延迟排序（可用在前，延迟低的在前）
    sorted_results = sorted(results,key=lambda x: (not x['available'], x['latency'] if x['available'] else float('inf')))

    for r in sorted_results:
        # 使用颜色和图标来美化输出
        if r['available']:
            status_icon = f"{DockerMirrorDetector.Colors.GREEN}✅ Available{DockerMirrorDetector.Colors.ENDC}"
            latency_str = f"{r['latency']} ms"
            msg = r['msg']
        else:
            status_icon = f"{DockerMirrorDetector.Colors.FAIL}❌ Failed{DockerMirrorDetector.Colors.ENDC}"
            latency_str = "-"
            msg = f"{DockerMirrorDetector.Colors.FAIL}{r['msg']}{DockerMirrorDetector.Colors.ENDC}"

        print(f"{r['url']:<35} | {status_icon:<20} | {latency_str:<10} | {msg}")
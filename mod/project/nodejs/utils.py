import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional, Tuple

def test_registry_url() -> Tuple[Optional[str], Optional[str]]:
    mirrors = [
        {"name": "npmmirror中国镜像", "url": "https://registry.npmmirror.com/"},
        {"name": "华为源", "url": "https://mirrors.huaweicloud.com/repository/npm/"},
        {"name": "腾讯源", "url": "https://mirrors.cloud.tencent.com/npm/"},
        {"name": "官方源", "url": "https://registry.npmjs.org/"}
    ]

    def test_mirror(mirror) -> Optional[Tuple[str, str]]:
        try:
            # 使用 -/ping 测试镜像源是否可用, 避免部分镜像源不支持web访问 如：腾讯源
            response = requests.get(mirror["url"] + "-/ping", timeout=5)
            if response.status_code == 200:
                return mirror["name"], mirror["url"]
        except Exception as e:
            pass
        return None

    executor = ThreadPoolExecutor(max_workers=4)
    futures = {executor.submit(test_mirror, mirror): mirror for mirror in mirrors}

    for future in as_completed(futures):
        result: Optional[Tuple[str, str]] = future.result()
        if result:
            executor.shutdown(wait=False)
            return result

    return None, None
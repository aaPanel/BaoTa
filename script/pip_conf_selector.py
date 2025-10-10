#!/www/server/panel/pyenv/bin/python
import requests
import subprocess
import time
from typing import List, Tuple, Optional
import concurrent.futures

# 从页面提取的pip镜像源列表
MIRRORS = [
    # 国内镜像源
    ("腾讯云", "https://mirrors.cloud.tencent.com/pypi/simple"),
    ("阿里云", "https://mirrors.aliyun.com/pypi/simple/"),
    ("清华大学", "https://pypi.tuna.tsinghua.edu.cn/simple"),
    ("中国科技大学", "https://pypi.mirrors.ustc.edu.cn/simple/"),

    # 国际镜像源
    ("PyPI官方", "https://pypi.org/simple"),
    ("Google", "https://pypi-mirrors.org/simple"),
    ("Microsoft", "https://pypi.microsoft.com/simple"),
    ("Amazon AWS", "https://pypi.aws.amazon.com/simple")
]


def test_mirror(url: str, timeout: int = 5) -> Tuple[bool, float]:
    """测试镜像源可用性并返回响应时间"""
    start_time = time.time()
    try:
        # 发送HEAD请求测试连接
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        # 检查状态码是否为200
        success = 200 <= response.status_code < 300
        response_time = time.time() - start_time
        return (success, response_time)
    except (requests.exceptions.RequestException, Exception):
        return (False, float('inf'))


def get_available_mirrors(max_workers: int = 5) -> List[Tuple[str, str, float]]:
    """获取所有可用的镜像源并按响应时间排序，支持并发测试"""
    print("正在测试镜像源可用性，请稍候...")
    available = []

    # 使用ThreadPoolExecutor实现并发测试
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_mirror = {
            executor.submit(test_mirror, url): (name, url)
            for name, url in MIRRORS
        }

        for future in concurrent.futures.as_completed(future_to_mirror):
            name, url = future_to_mirror[future]
            try:
                success, response_time = future.result()
                if success:
                    print(f"{name} 可用 (响应时间: {response_time:.2f}秒)")
                    available.append((name, url, response_time))
                else:
                    print(f"{name} 不可用")
            except Exception as exc:
                print(f"{name} 测试过程中出现异常: {exc}")

    # 按响应时间排序（最快的在前）
    return sorted(available, key=lambda x: x[2])


def extract_hostname(url: str) -> str:
    """从镜像URL中提取主机名"""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    return parsed.netloc  # 返回主机名部分


def set_pip_mirror(url: str) -> bool:
    """设置pip全局镜像源和可信主机，使用指定的pip3路径"""
    pip_path = "/www/server/panel/pyenv/bin/pip3"
    try:
        # 设置镜像源
        result = subprocess.run(
            [pip_path, "config", "set", "--user", "global.index-url", url],
            check=True,
            capture_output=True,
            text=True
        )

        # 提取主机名并设置可信主机
        hostname = extract_hostname(url)
        result_trusted = subprocess.run(
            [pip_path, "config", "set", "--user", "install.trusted-host", hostname],
            check=True,
            capture_output=True,
            text=True
        )

        print(f"\n成功设置pip镜像源为: {url}")
        print(f"成功设置可信主机为: {hostname}")
        print("配置结果:")
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n设置失败: {e.stderr}")
        return False


def show_current_config() -> None:
    """显示当前pip配置"""
    pip_path = "/www/server/panel/pyenv/bin/pip3"
    try:
        print("\n当前pip配置:")
        result = subprocess.run(
            [pip_path, "config", "list"],
            capture_output=True,
            text=True
        )
        print(result.stdout if result.stdout else "未设置任何配置")
    except Exception as e:
        print(f"获取配置失败: {e}")


def main(max_workers: int = 5, auto_mode: bool = False):
    print("===== pip镜像源管理工具 =====")

    # 获取可用镜像源
    available_mirrors = get_available_mirrors(max_workers=max_workers)

    if not available_mirrors:
        print("没有可用的镜像源，请检查网络连接")
        return

    # 显示可用镜像源排名
    print("\n===== 可用镜像源排名 (按响应速度) =====")
    for i, (name, url, response_time) in enumerate(available_mirrors, 1):
        print(f"{i}. {name}")
        print(f"   地址: {url}")
        print(f"   响应时间: {response_time:.2f}秒\n")

    # 推荐最佳镜像源
    best_name, best_url, best_time = available_mirrors[0]
    print(f"检测到最快镜像源: {best_name} ({best_time:.2f}秒)")

    # 自动模式直接设置最快镜像源
    if auto_mode:
        print("自动模式：正在设置最快镜像源...")
        if set_pip_mirror(best_url):
            print("自动设置成功！")
        else:
            print("自动设置失败！")
        show_current_config()
        return

    # 非自动模式继续交互式选择
    # 推荐最佳镜像源
    print(f"推荐使用最快的镜像源: {best_name} ({best_time:.2f}秒)")

    # 询问用户是否设置
    choice = input("是否将其设置为默认pip镜像源? (y/n): ").strip().lower()
    if choice == 'y':
        set_pip_mirror(best_url)
        show_current_config()
    else:
        # 让用户选择其他镜像源
        try:
            idx = int(input(f"请输入要设置的镜像源编号 (1-{len(available_mirrors)}): ")) - 1
            if 0 <= idx < len(available_mirrors):
                name, url, _ = available_mirrors[idx]
                set_pip_mirror(url)
                show_current_config()
            else:
                print("无效的编号")
        except ValueError:
            print("输入无效")


if __name__ == "__main__":
    import sys

    # 检查是否安装了requests
    try:
        import requests
    except ImportError:
        print("检测到未安装requests库，正在尝试安装...")
        pip_path = "/www/server/panel/pyenv/bin/pip3"
        try:
            subprocess.run([pip_path, "install", "requests"], check=True)
            import requests
        except Exception as e:
            print(f"安装requests失败，请手动安装后再运行脚本: {pip_path} install requests")
            exit(1)

    # 解析命令行参数判断是否启用自动模式
    auto_mode = False
    if len(sys.argv) > 1 and sys.argv[1] == "--auto":
        auto_mode = True
        print("启动自动模式：将自动设置最快的镜像源")

    # 默认使用5个并发线程
    main(max_workers=5, auto_mode=auto_mode)
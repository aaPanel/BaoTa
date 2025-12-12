# encoding utf-8
import subprocess
import requests
import os
import logging
import tempfile


class UpdateSiteTotal:
    # 类级别的常量定义，集中管理固定配置
    DEFAULT_USER_AGENT = "BT-Panel/10.0"
    INSTALL_SCRIPT_TIMEOUT = 600  # 安装脚本超时时间(秒)
    VERSION_CHECK_TIMEOUT = 10    # 版本检查超时时间(秒)
    SCRIPT_DOWNLOAD_TIMEOUT = 15  # 脚本下载超时时间(秒)

    site_total_path = '/www/server/site_total'
    download_url = 'https://download.bt.cn/site_total/'
    version_url = download_url + 'version.txt'
    install_sh = download_url + 'install.sh'
    site_total_bin = os.path.join(site_total_path, 'site_total')

    def __init__(self):
        """初始化更新工具
        """

        # 初始化日志配置
        self._init_logger()

    def _init_logger(self):
        """初始化日志配置（封装为独立方法，便于维护）"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )

    # ------------------------------
    # 版本相关方法
    # ------------------------------
    def get_current_version(self):
        """获取当前安装的版本号（返回字符串格式，如"1.0"）"""
        if not self.is_installed():
            self._log_warning(f"未检测到 {self.site_total_bin}，无法获取当前版本")
            return None

        try:
            # 执行版本命令
            result = subprocess.run(
                [self.site_total_bin, 'version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True,
                timeout=self.VERSION_CHECK_TIMEOUT
            )
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired, Exception) as e:
            return self._handle_version_cmd_error(e)

        # 解析版本号（调用辅助方法）
        return self._parse_version_output(result)

    def _parse_version_output(self, result):
        """解析版本命令的输出结果，提取版本号"""
        # 合并stdout和stderr，避免版本信息输出到错误流
        output_lines = result.stdout.splitlines() + result.stderr.splitlines()
        
        for line in output_lines:
            if "Version:" in line:
                # 提取版本号并格式化（确保x.y格式）
                raw_version = line.split(":")[-1].strip()
                return self._format_version(raw_version)
        
        self._log_warning(f"无法从输出中解析版本号: {output_lines}")
        return None

    def _format_version(self, raw_version):
        """将原始版本号格式化为x.y的字符串格式"""
        try:
            float_version = float(raw_version)
            return f"{float_version:.1f}"
        except ValueError:
            self._log_error(f"版本号格式异常，原始值: {raw_version}")
            return None

    def _handle_version_cmd_error(self, error):
        """处理版本命令执行中的异常（统一错误处理）"""
        if isinstance(error, subprocess.CalledProcessError):
            self._log_error(f"版本命令执行失败: {error.stderr.strip()}")
        elif isinstance(error, subprocess.TimeoutExpired):
            self._log_error("版本命令执行超时")
        else:
            self._log_error(f"获取版本号时发生错误: {str(error)}")
        return None

    def get_latest_version(self):
        """获取最新版本号（返回字符串格式）"""
        try:
            response = requests.get(
                self.version_url,
                timeout=self.VERSION_CHECK_TIMEOUT,
                headers={"User-Agent": self.DEFAULT_USER_AGENT}
            )
            response.raise_for_status()
            latest_version = response.text.strip()
            
            if not latest_version:
                self._log_warning("获取到的最新版本号为空")
                return None
            return latest_version
        except requests.RequestException as e:
            self._log_error(f"获取最新版本失败: {str(e)}")
            return None

    def check_update_available(self):
        """检查是否有可用更新（基于float格式版本号比较）"""
        current_version_str = self.get_current_version()
        latest_version_str = self.get_latest_version()

        # 检查版本号获取结果
        if not current_version_str:
            return False, "无法获取当前版本"
        if not latest_version_str:
            return False, "无法获取最新版本"

        # 版本号比较
        try:
            current_version = float(current_version_str)
            latest_version = float(latest_version_str)
        except ValueError as e:
            error_msg = f"版本号格式错误（应为x.y）: {str(e)}"
            self._log_error(f"{error_msg}（当前: {current_version_str}, 最新: {latest_version_str}）")
            return False, error_msg

        if latest_version > current_version:
            return True, f"当前版本: {current_version_str}, 最新版本: {latest_version_str}"
        else:
            return False, f"当前版本: {current_version_str}, 最新版本: {latest_version_str}"

    # ------------------------------
    # 安装/更新相关方法
    # ------------------------------
    def is_installed(self):
        """检查site_total是否已安装且可执行"""
        return os.path.exists(self.site_total_bin) and os.access(self.site_total_bin, os.X_OK)

    def install_or_update(self):
        """执行安装或更新操作"""
        # 下载安装脚本
        install_script = self._download_install_script()
        if not install_script:
            return False, "下载安装脚本失败"

        # 执行安装脚本
        return self._execute_install_script(install_script)

    def _download_install_script(self):
        """下载安装脚本（提取为独立方法，职责单一）"""
        try:
            response = requests.get(
                self.install_sh,
                timeout=self.SCRIPT_DOWNLOAD_TIMEOUT,
                headers={"User-Agent": self.DEFAULT_USER_AGENT}
            )
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            self._log_error(f"下载安装脚本失败: {str(e)}")
            return None

    def _execute_install_script(self, script_content):
        """执行安装脚本（提取为独立方法，职责单一）"""
        temp_script = None
        try:
            # 创建临时脚本文件
            temp_script = self._create_temp_script(script_content)
            
            # 执行脚本
            result = subprocess.run(
                ["bash", temp_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self.INSTALL_SCRIPT_TIMEOUT
            )

            # 检查执行结果
            if result.returncode != 0:
                error_msg = (f"安装脚本执行失败(返回码: {result.returncode})\n"
                             f"错误输出: {result.stderr.strip()[:500]}")
                self._log_error(error_msg)
                return False, error_msg

            if not self.is_installed():
                return False, "安装完成但未找到可执行文件"

            return True, "安装/更新成功"

        except subprocess.TimeoutExpired:
            return False, "安装脚本执行超时"
        except Exception as e:
            return False, f"执行安装过程中出错: {str(e)}"
        finally:
            # 清理临时文件
            self._cleanup_temp_script(temp_script)

    def _create_temp_script(self, content):
        """创建临时脚本文件（辅助方法，封装文件操作）"""
        with tempfile.NamedTemporaryFile(
            mode='w',
            suffix='.sh',
            delete=False,
            dir='/tmp'
        ) as f:
            f.write(content)
            return f.name

    def _cleanup_temp_script(self, script_path):
        """清理临时脚本文件（辅助方法，确保资源释放）"""
        if script_path and os.path.exists(script_path):
            try:
                os.remove(script_path)
            except OSError as e:
                self._log_warning(f"无法删除临时文件 {script_path}: {str(e)}")

    # ------------------------------
    # 主逻辑与工具方法
    # ------------------------------
    def update_if_needed(self):
        """有更新时执行更新，未安装时执行安装（主逻辑入口）"""
        if not self.is_installed():
            self._log_info("未检测到安装，开始执行安装")
            return self.install_or_update()

        has_update, msg = self.check_update_available()
        if not has_update:
            return False, f"无需更新: {msg}"

        self._log_info(f"检测到更新: {msg}，开始执行更新")
        return self.install_or_update()

    # 日志工具方法（封装日志调用，便于统一管理）
    @staticmethod
    def _log_info(msg):
        logging.info(msg)

    @staticmethod
    def _log_warning(msg):
        logging.warning(msg)

    @staticmethod
    def _log_error(msg):
        logging.error(msg)


if __name__ == "__main__":
    updater = UpdateSiteTotal()
    success, message = updater.update_if_needed()
    logging.info(f"操作结果: {'成功' if success else '失败'} - {message}")

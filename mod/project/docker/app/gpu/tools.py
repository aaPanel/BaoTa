import os
import sys
from typing import Tuple

from mod.project.docker.app.gpu.constants import CMD
from mod.project.docker.app.gpu.nvidia import NVIDIA

if "/www/server/panel/class" not in sys.path:
    sys.path.append('/www/server/panel/class')

import public


class GPUTool:
    gpu_option = None
    option_default = None

    @staticmethod
    def __get_linux_distribution():
        """检测系统是否为 Debian/Ubuntu 或 CentOS/Red Hat 系列"""
        try:
            # 优先解析 /etc/os-release
            with open("/etc/os-release", "r", encoding="utf-8") as f:
                os_release = {}
                for line in f:
                    line = line.strip()
                    if line and "=" in line:
                        key, value = line.split("=", 1)
                        os_release[key] = value.strip('"')

                dist_id = os_release.get("ID", "").lower()
                id_like = os_release.get("ID_LIKE", "").lower()

                # 根据 ID 或 ID_LIKE 判断
                if dist_id in ["debian", "ubuntu"]:
                    return "debian"
                elif dist_id in ["centos", "rhel", "fedora"]:
                    return "centos"
                elif "debian" in id_like:
                    return "debian"
                elif "rhel" in id_like or "fedora" in id_like:
                    return "centos"

        except FileNotFoundError:
            # 如果 /etc/os-release 不存在，检查其他文件
            if os.path.exists("/etc/debian_version"):
                return "debian"
            elif os.path.exists("/etc/redhat-release"):
                return "centos"

        except Exception:
            raise ValueError("System Distribution Is Unknown")

    @classmethod
    def __gpu_default_setting(cls) -> Tuple[bool, bool]:
        """
        检测是否开启GPU
        Returns:
            gpu_option: 返回是否开启GPU选择
            option_default: 默认GPU选择是否开启
        """
        if cls.gpu_option is not None and cls.option_default is not None:
            return cls.gpu_option, cls.option_default

        driver = NVIDIA()
        # 如果不支持直接返回
        if driver.support is None or driver.support is False:
            cls.gpu_option = False
            cls.option_default = False
            return cls.gpu_option, cls.option_default

        # 如果支持则检查显存大小
        device_info = driver.get_all_device_info()
        mem_size = 0
        for _, _device in device_info.items():
            mem_size = mem_size + _device.get('memory', {}).get('size', 0)
        if mem_size > 3:
            cls.gpu_option = True
            cls.option_default = True
        else:
            cls.gpu_option = True
            cls.option_default = False

        return cls.gpu_option, cls.option_default

    @classmethod
    def register_app_gpu_option(cls, app):
        option, default = cls.__gpu_default_setting()
        for field in app.get('field', []):
            if option == False and field.get('attr', '') == 'gpu':
                app['field'].remove(field)
            elif option == True and field.get('attr', '') == 'gpu':
                field['default'] = default
                field['suffix'] = field['suffix'] + ' | 已默认设置为{}'.format(default)
                # public.print_log("\n\n\n\n{}\n\n\n\n".format(field['suffix']))
        return app

    @staticmethod
    def is_install_ctk():
        stdout, stderr = public.ExecShell(CMD.CTK.CheckVersion)
        if len(stderr) != 0:
            return False
        if not stdout.lower().find('version'):
            public.print_log("Not Nvidia Container Toolkit")
            return False
        return True

    @classmethod
    def __ctk_install_cmd_apt(cls, app_log):
        return ("{get_gpg_key} >> {app_log};"
                "{add_sources_list} >> {app_log};"
                "{apt_update} >> {app_log};"
                "{install} >> {app_log}"
                .format(get_gpg_key=CMD.CTK.APT.GetGPGKey,
                        add_sources_list=CMD.CTK.APT.AddSourcesList,
                        apt_update=CMD.CTK.APT.APTUpdate,
                        install=CMD.CTK.APT.Install,
                        app_log=app_log
                        ))

    @classmethod
    def __ctk_install_cmd_yum(cls, app_log):
        return ("{add_repo} >> {app_log};"
                "{install} >> {app_log}"
                .format(add_repo=CMD.CTK.YUM.AddRepo,
                        install=CMD.CTK.YUM.Install,
                        app_log=app_log
                        ))

    @classmethod
    def __config_docker(cls, app_log):
        return ("{runtime} >> {app_log};"
                "{restart} >> {app_log}"
                .format(runtime=CMD.CTK.ConfigureDocker.Runtime,
                        restart=CMD.CTK.ConfigureDocker.Restart,
                        app_log=app_log))

    @classmethod
    def ctk_install_cmd(cls, app_log):
        dtb = cls.__get_linux_distribution()
        cmd = ''
        if dtb == 'debian':
            cmd = (
                "{install_cmd};"
                "{config_docker}"
                .format(
                    install_cmd=cls.__ctk_install_cmd_apt(app_log),
                    config_docker=cls.__config_docker(app_log),
                ))
        elif dtb == 'centos':
            cmd = (
                "{install_cmd};"
                "{config_docker}"
                .format(
                    install_cmd=cls.__ctk_install_cmd_yum(app_log),
                    config_docker=cls.__config_docker(app_log),
                ))
        return cmd

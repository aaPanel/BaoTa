# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: csj <csj@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# docker compose 备份脚本
# ------------------------------
import hashlib
import json
import os
import sys
import time

os.chdir('/www/server/panel/')
sys.path.insert(0, "class/")
sys.path.insert(0, "/www/server/panel/")

import public
from mod.project.docker.docker_compose.compose_utils import DockerComposeUtils as U

class DockerComposeBackup:
    __version = "11.4.0"

    def __init__(self, compose_name, compose_file_path):
        self.compose_name = compose_name
        self.compose_file_path = compose_file_path
        
        self.backup_root = "/www/dk_project/backup/compose"
        
        self.project_dir = os.path.abspath(os.path.dirname(self.compose_file_path))
        self.project_name = os.path.basename(self.project_dir)
    
        now_time = int(time.time())
        self.backup_name = f"{self.project_name}_{now_time}"
        
        self.backup_dir = os.path.join(self.backup_root, self.project_name, self.backup_name)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        self.volumes_dir = os.path.join(self.backup_dir, "volumes")
        os.makedirs(self.volumes_dir, exist_ok=True)

        self.docker_info = U.docker_info()
        #创建配置文件 config.json
        self.backup_config = {
            "project_dir": self.project_dir,
            "back_time": now_time,
            "project_name": self.project_name,
            "volumes": [],
            "networks": [],
            "versions": {
                "app_version": self.__version,
                "docker": self.docker_info.get('ServerVersion', ''),
                "docker-compose": U.compose_version(),
                "mac": public.get_mac_address()
            }
        }

    def log(self, msg, level=0):
        print(f"{' '*level}{msg}")

    def get_all_services(self):
        """
        获取Compose下所有的 services
        """
        if self.compose_data and 'services' in self.compose_data:
            return self.compose_data['services']
        return {}
    
    def get_all_volumes(self):
        """
        获取Compose下所有的 volumes
        """
        if self.compose_data and 'volumes' in self.compose_data:
            return self.compose_data['volumes']
        return None

    def get_all_networks(self):
        """
        获取Compose下所有的 networks
        """
        if self.compose_data and 'networks' in self.compose_data:
            return self.compose_data['networks']
        return None

    def parser_all_services(self):
        """
        获取所有 services 的 volumes，并判断类型
        """
        services = self.get_all_services()
        if not services:
            return None

        services_detail = {}
        for service_name, service_details in services.items():
            services_detail[service_name] = {
                "volumes": []
            }
            if 'volumes' in service_details:
                volumes_list = self._parse_services_volumes(service_details['volumes'])
                services_detail[service_name]["volumes"] = volumes_list
        return services_detail

    def _parse_services_volumes(self, volumes):
        """
        判断 volume的类型

        @return
            [{
                "type": "volume",  #volume bind tmpfs
                "source": "",      #volume 名称 or 主机路径
                "target": ""       #容器内路径
            }]
        """
        if not volumes:
            return None

        volume_list = []
        for volume_dic in volumes:
            if isinstance(volume_dic, dict):    
                if volume_dic.get("source",'') == '': 
                    #匿名卷 /app/folder5 跳过
                    # volume_dic["source"] = ''
                    # volume_dic["type"] = "volume-anonymous"
                    continue
                elif "/" in volume_dic["source"] or "$" in volume_dic["source"]:
                    #绑定挂载卷 /opt/data:/var/lib/mysql
                    volume_dic["type"] = "bind"
                else:
                    #命名卷 dify_es01_data:/usr/share/elasticsearch/data
                    volume_dic["type"] = "volume-named"
                volume_list.append(volume_dic)
        return volume_list

    def _backup_volume_bind(self, volume_dict):
        try:
            source = volume_dict["source"]
            source_abs = os.path.abspath(source)
            source_hash = hashlib.md5(source.encode()).hexdigest()
            file_attr = 0

            # 检查source是否在Compose项目目录下，如果是则跳过备份但记录配置 file_attr = 0
            if source_abs.startswith(os.path.abspath(self.project_dir)):
                self.log(f"绑定挂载卷 {source} 已在项目目录下，跳过备份", 2)
                file_attr = 3
            else:
                #检查source文件类型
                file_attr = U.check_special_file(source)
                if file_attr == 2:
                    self.log(f"绑定挂载卷 {source} 是系统性文件，跳过备份", 2)
                    return True

                volume_back_path = os.path.join(self.volumes_dir, source_hash)
                os.makedirs(volume_back_path, exist_ok=True)
                out, err = public.ExecShell(f"cp -rp {source} {volume_back_path}")
                if err:
                    return False

            self.backup_config["volumes"].append({
                "name": source_hash,
                "full_path": os.path.abspath(os.path.dirname(source)),
                "file_name": os.path.basename(source),
                "backup_path": source_hash,
                "type": "bind",
                "file_attr": file_attr,
            })
            return True
        except Exception as e:
            self.log(f"备份绑定挂载卷 {source} 失败: {e}", 2)
            return False

    def _backup_volume_named(self, volume_dict):
        try:
            source = volume_dict["source"]
            volume_info = self.docker_volumes[source]
            source = volume_info["name"]
            volume_info = U.volume_inspect(source)
            if volume_info.get("Driver") != "local":
                self.log(f"卷 {source} 不是 local 类型，跳过备份", 2)
                return True
            if not volume_info.get("Mountpoint"):
                self.log(f"卷 {source} 挂载点为空，跳过备份", 2)
                return True
            # 检查是否为绑定挂载卷
            if volume_info.get("Options") and volume_info["Options"].get("o", "") == "bind":
                return self._backup_volume_bind({
                    "source": volume_info["Options"]["device"]
                })
            volume_back_path = os.path.join(self.volumes_dir, source)
            os.makedirs(volume_back_path, exist_ok=True)
            out, err = public.ExecShell(f"cp -rp {volume_info['Mountpoint']} {volume_back_path}")
            if err:
                return False
            self.backup_config["volumes"].append({
                "name": source,
                "full_path": "{DockerRootDir}" + f"/volumes/{source}",
                "file_name": os.path.basename(volume_info["Mountpoint"]),
                "backup_path": source,
                "type": "volume",
                "file_attr": 0,
            })
            return True
        except Exception as e:
            self.log(f"备份命名卷 {source} 失败: {e}", 2)
            return False

    def _backup_compose_file(self,  ):
        self.log(f"备份compose文件目录: {self.compose_file_path}", 1)
        compose_file_dir = self.project_dir
        out, err = public.ExecShell(f"cp -rp {compose_file_dir} {self.backup_dir}")
        if err:
            self.log(f"备份compose文件目录失败: {err}", 2)
            return False
        return True
        
    def _backup_networks(self):
        try:
            networks = self.get_all_networks()
            if not networks:
                return True
                
            for net_name, net_details in networks.items():
                external = net_details.get('external', False)
                if not external:
                    continue
                real_name = net_details.get('name', net_name)
                self.log(f"备份网络 {real_name}", 1)
                try:
                    data = U.network_inspect(real_name)
                    if not data:
                        continue
                    if data.get('Driver') != 'bridge':
                        continue
                    enable_ipv6 = data.get('EnableIPv6', False)
                    ipam_cfg = data.get('IPAM', {}).get('Config', [])
                    self.backup_config['networks'].append({
                        'name': real_name,
                        'EnableIPv6': enable_ipv6,
                        'Config': ipam_cfg
                    })
                except:
                    self.log(f"备份网络 {real_name} 失败", 2)
                    return False
            return True
        except Exception as e:
            self.log(f"备份网络失败: {e}", 2)
            return False

    def backup_volumes(self, services_detail):
        try:
            success = True
            for service_name, service_details in services_detail.items():
                self.log(f"备份服务 {service_name}:", 1)
                vols = service_details.get("volumes")
                if not vols:
                    continue
                self.log("备份卷:", 2)
                for volume_dic in vols:
                    self.log(f"备份卷 {volume_dic.get('source')}", 3)
                    try:
                        volume_type = volume_dic.get("type")
                        if volume_type == "bind":
                            ok = self._backup_volume_bind(volume_dic)
                        elif volume_type == "volume-named":
                            ok = self._backup_volume_named(volume_dic)
                        else:
                            ok = True
                        if not ok:
                            success = False
                    except Exception as e:
                        self.log(f"备份卷 {volume_dic['source']} 失败: {e}", 2)
                        success = False
            return success
        except Exception as e:
            self.log(f"备份卷失败: {e}", 2)
            return False

    def backup(self, ps=""):
        self.compose_data = U.load_compose_config(self.compose_file_path)
        
        self.docker_volumes = self.get_all_volumes()
        services_detail = self.parser_all_services()
        
        if not self._backup_compose_file():
            return False
        if not self._backup_networks():
            return False
        if not self.backup_volumes(services_detail):
            return False
        public.writeFile(os.path.join(self.backup_dir, "config.json"), json.dumps(self.backup_config, indent=4))

        targrt_path = os.path.join(self.backup_root, self.project_name)
        tar_name = f"{targrt_path}/{self.backup_name}.tar"
        public.ExecShell(f"cd {targrt_path} && tar -cvf {tar_name} {self.backup_name}")
        public.ExecShell(f"rm -rf {os.path.join(targrt_path, self.backup_name)}")
        
        self.save_data(tar_name, self.compose_file_path, ps)
        self.log(f"备份完成: {tar_name}", 1)
        return tar_name

    def save_data(self, file_path, path, ps=""):
        public.M('compose_backup').insert({
            "name": self.compose_name,
            "type": "1",        #本机备份
            "path": file_path,
            "compose_path": path,
            "file_size": os.path.getsize(file_path), #单位:字节
            "time": int(time.time()),
            "ps": ps,
        })
                

if __name__ == '__main__':
    # 从命令行参数获取参数: compose_name compose_path [ps]
    if len(sys.argv) < 3:
        print("用法: python compose_backup.py <compose_name> <compose_path> [ps]")
        print("参数说明:")
        print("  compose_name: 项目名称")
        print("  compose_path: docker-compose.yml文件路径")
        print("  ps: 可选参数，备份描述")
        sys.exit(1)
    
    compose_name = sys.argv[1]
    compose_path = sys.argv[2]
    ps = sys.argv[3] if len(sys.argv) > 3 else ""
    
    # 检查compose文件是否存在
    if not os.path.exists(compose_path):
        print(f"错误: compose文件不存在: {compose_path}")
        sys.exit(1)
    
    parser = DockerComposeBackup(compose_name, compose_path)
    
    parser.log(f"开始备份项目 [{compose_name}]...")
    parser.log(f"compose文件路径: {compose_path}")
    
    result = parser.backup(ps)
    if result:
        parser.log(f"项目 [{compose_name}] 备份完成!")
        parser.log(f"bt_successful")
        parser.log(f"备份文件: {result}")
    else:
        parser.log(f"项目 [{compose_name}] 备份失败!")
        parser.log(f"bt_failed") 
        sys.exit(1)

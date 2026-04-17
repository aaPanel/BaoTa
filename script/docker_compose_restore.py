# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: csj <csj@bt.cn>
# -------------------------------------------------------------------
# ------------------------------
# docker compose 恢复脚本
# ------------------------------
import os
import sys
import json
import subprocess

os.chdir('/www/server/panel/')
sys.path.insert(0, "class/")
sys.path.insert(0, "/www/server/panel/")

import public
from mod.project.docker.docker_compose.compose_utils import DockerComposeUtils as U

class DockerComposeRestorer:
    __version = "11.4.0"

    def __init__(self, tar_file_path):
        self.tar_file_path = tar_file_path
        self.temp_dir = "/tmp"
        self.docker_info = U.docker_info()

    def log(self, msg, level=0):
        print(f"{' '*level}{msg}")

    def _extract_tar_file(self):
        """解压tar文件到临时目录"""
        try:
            tar_file_name = os.path.basename(self.tar_file_path).split('.')[0]
            self.back_path = os.path.join(self.temp_dir, tar_file_name)
            self.log(f"解压备份文件: {self.tar_file_path}", 1)
            public.ExecShell(f"tar -xf {self.tar_file_path} -C {self.temp_dir}")
            #检查文件存在
            if not os.path.exists(self.back_path):
                self.log(f"解压备份文件失败", 2)
                return False
            self.back_path_volumes = os.path.join(self.back_path, 'volumes')
            return True
        except Exception as e:
            self.log(f"解压备份文件失败: {str(e)}", 2)
            return False

    def _load_backup_config(self):
        """加载备份配置文件"""
        path = os.path.join(self.back_path, 'config.json')
        data = public.ReadFile(path)
        config = json.loads(data) if data else {}
        
        # 设置项目目录相关路径
        self.project_dir = config.get('project_dir')
        if self.project_dir:
            self.src_project_dir = os.path.join(self.back_path, os.path.basename(self.project_dir))
        
        return config

    def _check_networks_exist(self):
        """检查网络是否存在"""
        nets = self.config.get('networks', [])
        if not nets:
            return True
        all_ok = True
        for net in nets:
            name = net.get('name')
            if name and not U.network_exists(name):
                self.log(f"网络不存在: {name} ，请先创建网络", 2)
                all_ok = False
        return all_ok

    def _check_versions_ok(self):
        """检查版本是否兼容"""
        versions = self.config.get('versions', {})
        if not versions:
            return True
        app_bak = versions.get('app_version', '')
        docker_bak = versions.get('docker', '') 
        compose_bak = versions.get('docker-compose', '')

        app_cur = self.__version
        docker_cur = str(self.docker_info.get('ServerVersion', ''))
        compose_cur = U.compose_version()

        if app_bak and U.to_tuple(app_cur) < U.to_tuple(app_bak):
            self.log(f"当前应用版本低于备份版本: {app_cur} < {app_bak}", 1)
            return False
        if docker_bak and U.to_tuple(docker_cur) < U.to_tuple(docker_bak):
            self.log(f"当前Docker版本低于备份版本: {docker_cur} < {docker_bak}", 1)
            return False
        if compose_bak and U.to_tuple(compose_cur) < U.to_tuple(compose_bak):
            self.log(f"当前Compose版本低于备份版本: {compose_cur} < {compose_bak}", 1)
            return False
        return True

    def _restore_volume_bind(self, meta):
        """恢复绑定卷"""
        full_path = meta['full_path']
        file_name = meta['file_name']
        backup_path = os.path.join(self.back_path_volumes, meta['backup_path'], file_name)
        os.makedirs(full_path, exist_ok=True)
        target_path = os.path.join(full_path, file_name)
        public.ExecShell(f"rm -rf {target_path}")
        self.log(f"恢复绑定卷: {file_name} -> {full_path}", 2)
        public.ExecShell(f"cp -rp {backup_path} {full_path}")

    def _restore_volume_named(self, name, meta):
        """恢复命名卷"""
        root = self.docker_info.get('DockerRootDir', '/var/lib/docker')
        vol_dir = os.path.join(root, 'volumes', name)
        data_dir = os.path.join(vol_dir, '_data')
        src = os.path.join(self.back_path_volumes, meta['backup_path'], meta['file_name'])
        os.makedirs(data_dir, exist_ok=True)
        public.ExecShell(f"rm -rf {data_dir}/*")
        self.log(f"恢复命名卷: {name} -> {data_dir}", 2)
        public.ExecShell(f"cp -rp {src}/* {data_dir}/")

    def _restore_volumes(self, skip_volumes=[]):
        """恢复卷，支持跳过指定卷
        
        Args:
            skip_volumes: 要跳过的卷ID列表，例如 ['2c44072c2eeed91be9b0ab8c6d8a7dca']
        """
        vols = self.config.get('volumes', [])
        if not vols:
            return
        
        self.log("恢复卷:", 1)
        for vol in vols:
            # 获取卷名称/ID
            vol_name = vol.get('name')
            if not vol_name:
                continue
                
            # 如果当前卷在跳过列表中，则跳过恢复
            if vol_name in skip_volumes:
                self.log(f"跳过卷: {vol_name}", 2)
                continue
            
            # 已存在于compose项目内部 ，跳过恢复
            if vol.get('file_attr') == 3:
                continue
                
            t = vol.get('type')
            if t == 'bind':
                self._restore_volume_bind(vol)
            elif t == 'volume':
                self._restore_volume_named(vol_name, vol)

    def _run_compose_cmd(self, cmd):
        if not self.project_dir: return
        
        try:
            # 使用subprocess实时输出日志
            p = subprocess.Popen(f"docker-compose {cmd}", shell=True, cwd=self.project_dir, 
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, bufsize=1)
            
            for line in iter(p.stdout.readline, b''):
                if line:
                    try:
                        line = line.decode('utf-8').strip()
                    except:
                        line = line.decode('gbk', errors='ignore').strip()
                    if line:
                        self.log(line, 2)
                        
            p.stdout.close()
            p.wait()
            return p.returncode == 0
        except Exception as e:
            self.log(f"执行命令失败: {str(e)}", 2)
            return False

    def _stop_project(self):
        """停止项目"""
        if not self.project_dir or not os.path.exists(self.project_dir):
            return
        
        # 检查compose文件是否存在
        yml_path = os.path.join(self.project_dir, 'docker-compose.yml')
        yaml_path = os.path.join(self.project_dir, 'docker-compose.yaml')
        
        if not os.path.exists(yml_path) and not os.path.exists(yaml_path):
            return

        self.log("正在停止项目...", 1)
        self._run_compose_cmd("stop")

    def _start_project(self):
        """启动项目"""
        if not self.project_dir or not os.path.exists(self.project_dir): return True
        self.log("正在启动项目...", 1)
        return self._run_compose_cmd("up -d")

    def _restore_project(self):
        """恢复项目文件"""
        if not self.project_dir or not os.path.exists(self.src_project_dir):
            return
        os.makedirs(self.project_dir, exist_ok=True)
        public.ExecShell(f"cp -rp {self.src_project_dir}/. {self.project_dir}/")

    def restore(self, restore_volume=[]):
        """执行恢复操作
        
        Args:
            restore_volume: 跳过恢复的卷列表，如果为None则恢复所有卷
                           例如：['a742baca905d944abcee36ae2ae006fa'] 表示跳过
        """
        self.log(f"开始恢复 [{self.tar_file_path}]", 0)

        # 首先解压备份文件
        if not self._extract_tar_file():
            self.log('解压备份文件失败', 1)
            return False

        # 加载配置文件
        self.config = self._load_backup_config()
        if not self.config:
            self.log('加载配置文件失败', 1)
            self._cleanup()
            return False

        # 显示项目信息
        project_dir = self.config.get('project_dir', '')
        if project_dir:
            self.log(f"项目目录: {project_dir}", 1)

        if not self._check_versions_ok():
            self.log('当前版本低于备份版本，恢复失败', 1)
            self._cleanup()
            return False

        if not self._check_networks_exist():
            self.log('网络缺失，恢复失败', 1)
            self._cleanup()
            return False

        try:
            #停止项目
            self._stop_project()
            
            self._restore_project()
            self._restore_volumes(skip_volumes=restore_volume)
            
            # 启动项目
            if not self._start_project():
                self.log('启动项目失败', 1)
                return False
            self.log('恢复完成', 0)
            return True
        finally:
            self._cleanup()

    def _cleanup(self):
        """清理临时文件"""
        public.ExecShell(f"rm -rf {self.back_path}")
        self.log(f"清理临时目录: {self.back_path}", 1)


if __name__ == '__main__':
    # 从命令行参数获取参数: tar_file [volume_id1,volume_id2,...]
    if len(sys.argv) < 2:
        print("用法: python docker_compose_restore.py <tar_file> [volume_ids]")
        print("参数说明:")
        print("  tar_file: 备份tar文件路径")
        print("  volume_ids: 可选参数，要跳过恢复的卷ID列表，用逗号分隔")
        print("              例如: vol1,vol2,vol3")
        print("              如果不指定，则跳过恢复所有卷")
        sys.exit(1)
    
    tar_file = sys.argv[1]

    
    # 解析卷ID列表
    restore_volumes = []
    if len(sys.argv) > 2:
        volume_ids = sys.argv[2]
        restore_volumes = [vid.strip() for vid in volume_ids.split(',') if vid.strip()]
    print(f"要跳过恢复的卷ID列表: {restore_volumes}")
    
    restorer = DockerComposeRestorer(tar_file)
    
    restorer.log(f"开始恢复备份文件: {tar_file}")
    
    try:
        res = restorer.restore(restore_volume=restore_volumes)
        if not res:
            restorer.log(f"备份文件 [{tar_file}] 恢复失败!")
            restorer.log(f"bt_failed")
            sys.exit(1)
        restorer.log(f"备份文件 [{tar_file}] 恢复完成!")
        restorer.log(f"bt_successful")
    except Exception as e:
        restorer.log(f"备份文件 [{tar_file}] 恢复失败: {str(e)}")
        restorer.log(f"bt_failed")
        sys.exit(1)

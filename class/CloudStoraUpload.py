# coding: utf-8
#  + -------------------------------------------------------------------
# | 宝塔云存储上传接口
#  + -------------------------------------------------------------------
# | Copyright (c) 2015-2016 宝塔软件(http:#bt.cn) All rights reserved.
#  + -------------------------------------------------------------------
# | Author: sww
#  + -------------------------------------------------------------------

'''
增加
先添加/www/server/panel/data/libList.conf文件中的信息
增加对应存储的class --实现检测是否链接成功，实现上传接口封装  链接失败或未登录都返回false，成功返回对象 authorize权限判定函数
增加CloudStoraUpload类中cloud_obj映射
'''

import os
import sys
import time
import traceback

import public


# 七牛云
class qiniu:
    flag = True
    qc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/qiniu' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/qiniu')
        try:
            from qiniu_main import QiNiuClient as qc
            self.qc_obj = qc()
            self.qc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.qc_obj
        else:
            return False


# 上传到天翼云
class tianyiyun:
    flag = True
    tyy_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/tianyiyun' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/tianyiyun')
        try:
            from tianyiyun_main import tianyiyun_main as tyy
            self.tyy_obj = tyy()
        except:
            print(traceback.format_exc())
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.tyy_obj
        else:
            return False


# 百度云
class bos:
    flag = True
    bc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/bos' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/bos')
        try:
            from bos_main import BOSClient as bc
            self.bc_obj = bc()
            self.bc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.bc_obj
        else:
            return False


# 腾讯云
class cos:
    flag = True
    cc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/txcos' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/txcos')
        try:
            from txcos_main import COSClient as cc
            self.cc_obj = cc()
            self.cc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.cc_obj
        else:
            return False


# 又拍云
class upyun:
    flag = True
    uc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/upyun' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/upyun')
        try:
            from upyun_main import UpYunClient as uc
            self.uc_obj = uc()
            self.uc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.uc_obj
        else:
            return False


# 阿里云
class alioss:
    flag = True
    oc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/alioss' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/alioss')
        try:
            from alioss_main import OSSClient as oc
            self.oc_obj = oc()
            self.oc_obj.authorize()
        except:
            print(traceback.format_exc())
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.oc_obj
        else:
            return False


# 未测试
class gdrive:
    flag = True
    gc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/gdrive' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/gdrive')
        try:
            from gdrive_main import gdrive_main as gc
            self.gc_obj = gc()
            self.gc_obj.resumable_upload = self.resumable_upload
            self.gc_obj.delete_object=self.delete_object
            self.gc_obj.build_object_name=self.build_object_name
            self.gc_obj.__get_folder_id=self.__get_folder_id
            
            if not self.gc_obj.set_creds():
                self.flag = False
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.gc_obj
        else:
            return False

    def resumable_upload(self, file_name, object_name, *args, **kwargs):
        
        get = public.to_dict_obj(
            {
                "filename": file_name,
                "filepath": object_name
            }
        )
        return self.gc_obj.upload_file(get)
        
    def build_object_name(self, data_type, file_name):
        import re
        
        # 定义不同数据类型的前缀字典
        prefix_dict = {
            "site": "web",
            "database": "db",
            "path": "path",
        }
    
        # 确保data_type是字典中的一个键，否则使用"default"作为前缀
        data_prefix = prefix_dict.get(data_type, "other")
    
        if "database" in file_name:
            # 特别处理数据库文件的路径
            dir_path = '/'.join(file_name.split('/')[:-1])
            sub_path_name = '/'.join(dir_path.split('/')[-2:]) + '/'
            object_name = f'bt_backup/{data_prefix}/{sub_path_name}'
        else:
            # 对其他类型文件使用正则表达式进行处理
            file_regx = f"{data_prefix}_(.+)_20\\d+_\\d+(?:\\.|_)"
            sub_search = re.search(file_regx.lower(), file_name)
            sub_path_name = ""
            if sub_search:
                sub_path_name = sub_search.groups()[0] + '/'
            object_name = f'bt_backup/{data_prefix}/{sub_path_name}'
    
        if object_name[:1] == "/":
            object_name = object_name[1:]
    
        return object_name
        
    def delete_object(self,filename=None,data_type=None):
        filename = filename.split('/')[-1]
        file_id = self.gc_obj._get_file_id(filename)
        self.gc_obj._delete_file(file_id)

        
    def __get_folder_id(self, floder_name):
        service = build('drive', 'v3', credentials=self.__creds)
        results = service.files().list(pageSize=10, q="name='{}' and mimeType='application/vnd.google-apps.folder'".format(floder_name),fields="nextPageToken, files(id, name)").execute()
        items = results.get('files', [])
        if not items:
            return []
        else:
            for item in items:
                return item["id"]


# 亚马逊
class aws_s3:
    flag = True
    cc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/aws_s3' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/aws_s3')
        try:
            from s3lib.client.aws_s3 import COSClient as cc
            # from aws_s3_main import aws_s3_main as cc
            self.cc_obj = cc()
            # self.cc_obj.upload_file = self.cc_obj.upload_file1
            # self.cc_obj.resumable_upload = self.cc_obj.upload_file1
            self.cc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.cc_obj
        else:
            return False


# 未测试  未做登录确定
class gcloud_storage:
    flag = True
    gsc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/gcloud_storage' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/gcloud_storage')
        try:
            from gcloud_storage_main import gcloud_storage_main as gsc
            self.gsc_obj = gsc()
            self.gsc_obj.resumable_upload = self.resumable_upload
            self.gsc_obj.backup_path="bt_backup"
        except:
            print(traceback.format_exc())         
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.gsc_obj
        else:
            return False
            
    def resumable_upload(self, file_name, object_name, *args, **kwargs):
        get = public.to_dict_obj(
            {
                "path": object_name,
                "filename": file_name
            }
        )
        return self.gsc_obj.upload_file(get)


# 华为云
class obs:
    flag = True
    oc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/obs' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/obs')
        try:
            from obs_main import OBSClient as oc
            self.oc_obj = oc()
            self.oc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.oc_obj
        else:
            return False


# 未测试
class msonedrive:
    flag = True
    oc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/msonedrive' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/msonedrive')
        try:
            from msonedrive_main import OneDriveClient as oc
            self.oc_obj = oc()
            self.oc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.oc_obj
        else:
            return False


# ftp    未登录验证
class ftp:
    flag = True
    ftp_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/ftp' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/ftp')
        try:
            from ftp_main import get_client
            self.ftp_obj = get_client(use_sftp=None)
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.ftp_obj
        else:
            return False


# 京东云
class jdcloud:
    flag = True
    oc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/jdcloud' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/jdcloud')
        try:
            from jdcloud_main import OBSClient as oc
            self.oc_obj = oc()
            self.oc_obj.authorize()
        except:
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.oc_obj
        else:
            return False

class webdav:
    flag = True
    webdav_obj = None

    def __init__(self):
        if '/www/server/panel/plugin/webdav' not in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/webdav')
        try:
            from webdav_main import webdav_main as webdav
            self.webdav_obj = webdav()
            self.webdav_obj.backup_path = webdav().default_backup_path
            self.webdav_obj.delete_file = webdav().delete_object
            self.webdav_obj.cloud_delete_file = webdav().delete_object
        except:
            self.flag = False


    def get_obj(self):
        """返回 WebDAV 对象，如果初始化失败则返回 False"""
        return self.webdav_obj if self.flag else False

# 上传到minio
class minio:
    flag = True
    minio_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/minio' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/minio')
        try:
            from minio_main import minio_main as minio
            self.minio_obj = minio()
            self.minio_obj.backup_path = minio().default_backup_path
            self.minio_obj.delete_file = minio().delete_object
            self.minio_obj.cloud_delete_file =minio().delete_object
        except:
            print(traceback.format_exc())
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.minio_obj
        else:
            return False

# 上传到多吉云
class dogecloud:
    flag = True
    dgc_obj = None

    def __init__(self):
        if not '/www/server/panel/plugin/dogecloud' in sys.path:
            sys.path.insert(0, '/www/server/panel/plugin/dogecloud')
        try:
            from dogecloud_main import dogecloud_main as dgc
            self.dgc_obj = dgc()
            self.dgc_obj.delete_file = dgc().delete_object
            self.dgc_obj.cloud_delete_file =dgc().delete_object
        except:
            print(traceback.format_exc())
            self.flag = False

    def get_obj(self):
        if self.flag:
            return self.dgc_obj
        else:
            return False

# 总函数
class CloudStoraUpload:
    cloud_list = []
    cloud_obj = {
        'qiniu': qiniu,
        'alioss': alioss,
        'ftp': ftp,
        'bos': bos,
        'obs': obs,
        'aws_s3': aws_s3,
        'gdrive': gdrive,
        'msonedrive': msonedrive,
        'gcloud_storage': gcloud_storage,
        'upyun': upyun,
        'jdcloud': jdcloud,
        'txcos': cos,
        'tianyiyun': tianyiyun,
        'webdav':webdav,
        'minio':minio,
        'dogecloud':dogecloud
    }
    backup_path = "/backup_path/"

    __CLOUD_TITLE = {
        "qiniu": "七牛云存储",
        "alioss": "阿里云OSS",
        "ftp": "FTP",
        "bos": "百度云BOS",
        "obs": "华为云OBS",
        "aws_s3": "AWS S3对象存储",
        "gdrive": "Google Drive",
        "msonedrive": "微软OneDrive",
        "gcloud_storage": "Google Cloud",
        "upyun": "又拍云存储",
        "jdcloud": "京东云存储",
        "txcos": "腾讯云COS",
        'tianyiyun': "天翼云ZOS",
        'webdav':"WebDav",
        'minio':"MinIO存储",
        'dogecloud':"多吉云COS"
    }

    def __init__(self):
        self.obj = None
        # 获取当前云存储的安装列表
        import json
        tmp = public.readFile('/www/server/panel/data/libList.conf')
        if tmp:
            libs = json.loads(tmp)
            for lib in libs:
                if not 'opt' in lib: continue
                filename = '/www/server/panel/plugin/{}'.format(lib['opt'])
                if not os.path.exists(filename): continue
                self.cloud_list.append(lib['opt'])

    def run(self, cloud_name):
        if cloud_name not in self.cloud_list or cloud_name not in self.cloud_obj.keys():
            return False
        obj = self.cloud_obj[cloud_name]()
        if not obj.flag:
            return False
        self.obj = obj.get_obj()

        if not hasattr(self.obj, "_name"):
            self.obj._name = cloud_name
        if not hasattr(self.obj, "_title"):
            self.obj._title = self.__CLOUD_TITLE.get(cloud_name, "")
        if not hasattr(self.obj, "backup_path"):
            self.obj.backup_path = self.backup_path
        if not hasattr(self.obj, "error_msg"):
            self.obj.error_msg = ""
        if not hasattr(self.obj, "upload_file"):
            self.obj.upload_file = self.__upload_api
        if not hasattr(self.obj, "resumable_upload"):
            self.obj.resumable_upload = self.__upload_api
        if not hasattr(self.obj, "delete_object"):
            self.obj.delete_object = self.__upload_api
        if type(self.obj.backup_path) == str:
            self.backup_path = self.obj.backup_path
        return self.obj

    def __upload_api(self, *args, **kwargs):
        self.obj.error_msg = "链接云存储失败！"
        return False

    def cloud_upload_file(self, file_name: str, upload_path: str, *args, **kwargs):
        """按照数据类型上传文件

        针对 panelBackup v1.2以上调用
        :param file_name: 上传文件名称
        :param data_type: 数据类型 site/database/path
        :return: True/False
        """
        try:
            return self.obj.resumable_upload(file_name, object_name=upload_path, *args, **kwargs)
        except Exception as e:
            # print(e)
            return False

    def cloud_delete_dir(self, file_path: str, *args, **kwargs):
        """删除文件夹
        """
        try:

            dir_list = self.obj.get_list(file_path)
            for info in dir_list["list"]:
                path = os.path.join(file_path, info['name'])
                self.obj.delete_object(path, *args, **kwargs)
            return True
        except Exception as e:
            return False

    def cloud_delete_file(self, file_path: str, *args, **kwargs):
        """删除文件
        """
        try:
            return self.obj.delete_object(file_path, *args, **kwargs)
        except Exception as e:
            print(e)
            return False

    def cloud_download_file(self, clould_path, loacl_path, *args, **kwargs):
        try:
            # print(clould_path, loacl_path)
            if not self.obj:
                return False
            if self.obj.get_list(clould_path)['list']:  # 调用目录下载
                self.cloud_download_dir(clould_path, loacl_path, *args, **kwargs)
            url = self.get_file_download_url(clould_path)
            if not url['status']:
                return public.returnMsg(False, '云存储下载文件失败')
            # import panelTask
            # task_obj = panelTask.bt_task()
            # task_obj.create_task('下载文件', 1, url['msg'], loacl_path)
            exec = 'wget --no-check-certificate -T 30 -t 5 -d -O {} {} '.format(loacl_path, url['msg'])
            public.ExecShell(exec)
            time.sleep(1)
            if os.path.exists(loacl_path):
                return public.returnMsg(True, '云存储下载文件成功')
            return public.returnMsg(False, '云存储下载文件失败')
        except:
            return public.returnMsg(False, '云存储下载文件失败')

    def cloud_download_dir(self, clould_path, loacl_path, *args, **kwargs):
        try:
            if not self.obj:
                return False
            data = self.obj.get_list(clould_path)
            if not os.path.exists(loacl_path):
                os.makedirs(loacl_path)

            for i in data['list']:
                path = os.path.join(data['path'], i['name'])
                loacl_path1 = os.path.join(loacl_path, i['name'])
                if self.obj.get_list(path)['list']:  # 判断是否是文件夹
                    if not os.path.exists(loacl_path1):
                        os.makedirs(loacl_path1)
                    self.cloud_download_dir(path, loacl_path1, *args, **kwargs)
                else:
                    self.obj.download_file(path, loacl_path1, *args, **kwargs)
            return
        except:
            return public.returnMsg(False, '云存储下载文件失败')

    def get_file_download_url(self, down_load_path):
        if self.obj.get_list(down_load_path)['list']:
            return public.returnMsg(False, '不支持文件夹下载，请手动到云存储服务端下载')
        file_name = os.path.basename(down_load_path)
        down_load_path = os.path.dirname(down_load_path)
        data = self.obj.get_list(down_load_path)
        if data['list']:
            for i in data['list']:
                if i['name'] == file_name:
                    return public.returnMsg(True, i['download'])
        return public.returnMsg(False, '获取下载链接失败')




# if __name__ == '__main__':
#     c = CloudStoraUpload()
#     a = c.run('alioss')
#     x = 'bt_backup/database/test_cron_back_1_2023-10-10_02-30-03_mysql_data.sql.gz'
#     print(c.obj.backup_path)
#     c.cloud_download_file('/bt_backup/', '/xiaopacai/backup')

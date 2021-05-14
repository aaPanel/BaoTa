# coding=utf-8

from qcloud_cos import CosConfig
from qcloud_cos import CosS3Client
from qcloud_cos import CosServiceError
from qcloud_cos import CosClientError
import sys
import random
import string


class CosV5PythonSDKTest(object):
    def __init__(self, region, appid, secret_id, secret_key, end_point,
                 scheme):
        self.region = region
        self.appid = appid
        self.secret_id = secret_id
        self.secret_key = secret_key
        self.end_point = end_point
        self.scheme = scheme
        self.cos_config = CosConfig(
            Secret_id=self.secret_id,
            Secret_key=self.secret_key,
            Endpoint=self.end_point % region,
            Scheme=self.scheme)
        self.client = CosS3Client(self.cos_config)

    def create_bucket(self, bucket_name):
        # 创建存储桶
        self.client.create_bucket(Bucket=bucket_name + '-' + self.appid)
        return 0

    def create_bucket_with_ACL(self, bucket_name, acl):
        # 创建存储桶 ACL
        self.client.create_bucket(
            Bucket=bucket_name + '-' + self.appid, ACL=acl)
        return 0

    def create_bucket_with_GrantFullControl(self, bucket_name, owner_uin,
                                            sub_uin):
        # 创建存储桶 GrantFullControl
        grant_full_control = 'id="qcs::cam::uin/%s:uin/%s"' % (owner_uin,
                                                               sub_uin)
        self.client.create_bucket(
            Bucket=bucket_name + '-' + self.appid,
            GrantFullControl=grant_full_control)
        return 0

    def create_bucket_with_GrantRead(self, bucket_name, owner_uin, sub_uin):
        # 创建存储桶 GrantRead
        grant_read = 'id="qcs::cam::uin/%s:uin/%s"' % (owner_uin, sub_uin)
        self.client.create_bucket(
            Bucket=bucket_name + '-' + self.appid, GrantRead=grant_read)
        return 0

    def create_bucket_with_GrantWrite(self, bucket_name, owner_uin, sub_uin):
        # 创建存储桶 GrantRead
        grant_write = 'id="qcs::cam::uin/%s:uin/%s"' % (owner_uin, sub_uin)
        self.client.create_bucket(
            Bucket=bucket_name + '-' + self.appid, GrantRead=grant_write)
        return 0

    def delete_bucket(self, bucket_name):
        # 删除存储桶
        self.client.delete_bucket(Bucket=bucket_name + '-' + self.appid)
        return 0

    def head_bucket(self, bucket_name):
        # 判断存储桶是否存在
        self.client.head_bucket(Bucket=bucket_name + '-' + self.appid)
        return 0

    def get_bucket_location(self, bucket_name):
        # 获取存储桶地域信息
        resp = self.client.get_bucket_location(Bucket=bucket_name + '-' +
                                               self.appid)
        return resp["LocationConstraint"]

    def list_objects(self, bucket_name):
        # 获取存储桶下文件列表
        resp = self.client.list_objects(Bucket=bucket_name + '-' + self.appid)
        return resp

    def list_objects_with_prefix(self, bucket_name, prefix):
        # 获取存储桶下有prefix前缀的文件列表
        resp = self.client.list_objects(
            Bucket=bucket_name + '-' + self.appid, Prefix=prefix)
        return resp

    def list_objects_with_delimiter(self, bucket_name, delimiter):
        # 模拟文件夹结构获取存储桶下 的文件列表
        resp = self.client.list_objects(
            Bucket=bucket_name + '-' + self.appid, Delimiter=delimiter)
        return resp

    def list_objects_with_Marker(self, bucket_name, marker):
        # 获取存储桶下文件名包含marker的文件列表
        resp = self.client.list_objects(
            Bucket=bucket_name + '-' + self.appid, Marker=marker)
        return resp

    def list_objects_with_Maxkeys(self, bucket_name, maxkeys):
        # 获取存储桶下最多maxkeys个文件列表
        resp = self.client.list_objects(
            Bucket=bucket_name + '-' + self.appid, MaxKeys=maxkeys)
        return resp

    def put_bucket_acl(self, bucket_name, acl):
        # 设置存储桶访问控制权限 ACL
        self.client.put_bucket_acl(
            Bucket=bucket_name + '-' + self.appid, ACL=acl)
        return 0

    def put_bucket_acl_with_GrantFullControl(self, bucket_name, owner_uin,
                                             sub_uin):
        # 设置存储桶访问控制权限 GrantFullControl
        grant_full_control = 'id="qcs::cam::uin/%s:uin/%s"' % (owner_uin,
                                                               sub_uin)
        self.client.put_bucket_acl(
            Bucket=bucket_name + '-' + self.appid,
            GrantFullControl=grant_full_control)

    def put_bucket_acl_with_GrantRead(self, bucket_name, owner_uin, sub_uin):
        # 设置存储桶访问控制权限 GrantRead
        grant_read = 'id="qcs::cam::uin/%s:uin/%s"' % (owner_uin, sub_uin)
        self.client.put_bucket_acl(
            Bucket=bucket_name + '-' + self.appid, GrantRead=grant_read)
        return 0

    def put_bucket_acl_with_GrantWrite(self, bucket_name, owner_uin, sub_uin):
        # 设置存储桶访问控制权限 GrantWrite
        grant_write = 'id="qcs::cam::uin/%s:uin/%s"' % (owner_uin, sub_uin)
        self.client.put_bucket_acl(
            Bucket=bucket_name + '-' + self.appid, GrantRead=grant_write)

    def get_bucket_acl(self, bucket_name):
        # 获取存储桶访问控制权限
        resp = self.client.get_bucket_acl(Bucket=bucket_name + "-" +
                                          self.appid)
        return resp

    def put_bucket_cors(self, bucket_name, max_age_seconds=0):
        # 设置一条存储桶跨域访问规则
        corsconfig = {
            "CORSRule": [{
                "ID": "CORSRule 1",
                "MaxAgeSeconds": max_age_seconds,
                "AllowedOrigin": ["http://cloud.tencent.com"],
                "AllowedMethod": ["GET"]
            }]
        }
        self.client.put_bucket_cors(
            Bucket=bucket_name + '-' + self.appid,
            CORSConfiguration=corsconfig)
        return 0

    def put_bucket_multi_cors(self, bucket_name):
        # 设置多条存储桶跨域访问规则
        corsconfig = {
            "CORSRule": [{
                "ID": "CORSRule 1",
                "AllowedOrigin": ["http://cloud.tencent.com"],
                "AllowedMethod": ["GET"]
            }, {
                "ID": "CORSRule 2",
                "AllowedOrigin": ["http://cloud.tencent.com"],
                "AllowedMethod": ["POST"]
            }, {
                "ID": "CORSRule 3",
                "AllowedOrigin": ["http://cloud.tencent.com"],
                "AllowedMethod": ["PUT"]
            }]
        }
        self.client.put_bucket_cors(
            Bucket=bucket_name + '-' + self.appid,
            CORSConfiguration=corsconfig)
        return 0

    def get_bucket_cors(self, bucket_name):
        # 获取存储桶跨域访问规则
        resp = self.client.get_bucket_cors(Bucket=bucket_name + '-' +
                                           self.appid)
        return resp

    def delete_bucket_cors(self, bucket_name):
        # 删除存储桶跨域访问规则
        self.client.delete_bucket_cors(Bucket=bucket_name + '-' + self.appid)
        return 0

    def put_object_str(self, bucket_name, obj_name, str_len):
        # 上传字符串到对象
        self.client.put_object(
            Bucket=bucket_name + '-' + self.appid,
            Body="".join(
                random.choice(string.ascii_letters + string.digits)
                for i in range(str_len)),
            Key=obj_name)
        return 0

    def put_object_file(self, bucket_name, obj_name, file_name):
        # 上传文件到对象
        self.client.put_object(
            Bucket=bucket_name + '-' + self.appid,
            Body=open(file_name, "rb").read(),
            Key=obj_name)
        return 0

    def head_object(self, bucket_name, obj_name):
        # 对象是否存在，获取对象属性
        resp = self.client.head_object(
            Bucket=bucket_name + '-' + self.appid, Key=obj_name)
        return resp

    def get_object(self, bucket_name, obj_name, file_name):
        # 下载对象
        resp = self.client.get_object(
            Bucket=bucket_name + '-' + self.appid, Key=obj_name)
        resp["Body"].get_stream_to_file(file_name)
        return 0

    def delete_object(self, bucket_name, obj_name):
        # 删除对象
        self.client.delete_object(
            Bucket=bucket_name + '-' + self.appid, Key=obj_name)
        return 0

    def delete_objects(self, bucket_name, obj_list):
        # 批量删除对象
        _obj = []
        for obj in obj_list:
            _obj.append({"Key": obj})
        delete = {
            "Object": _obj,
        }
        resp = self.client.delete_objects(
            Bucket=bucket_name + '-' + self.appid, Delete=delete)
        return resp

    def delete_objects_with_quiet(self, bucket_name, obj_list, quiet):
        # 批量删除对象
        _obj = []
        for obj in obj_list:
            _obj.append({"Key": obj})
        delete = {"Object": _obj, "Quiet": quiet}
        resp = self.client.delete_objects(
            Bucket=bucket_name + '-' + self.appid, Delete=delete)
        return resp

    def copy_object_in_same_bucket(self):
        # 桶内copy对象
        bucket_name = "mainbkt"
        object_key = "obj_copy"
        copy_source = {
            "Appid": self.appid,
            "Bucket": "mainbkt",
            "Key": "obj",
            "Region": self.region
        }
        resp = self.client.copy_object(
            Bucket=bucket_name + '-' + self.appid,
            Key=object_key,
            CopySource=copy_source,
            CopyStatus="Copy")
        return resp

    def copy_object_in_different_bucket(self):
        # 桶内copy对象
        bucket_name = "wook-gao"
        object_key = "obj_copy"
        copy_source = {
            "Appid": self.appid,
            "Bucket": "burning",
            "Key": "test",
            "Region": self.region
        }
        resp = self.client.copy_object(
            Bucket=bucket_name + '-' + self.appid,
            Key=object_key,
            CopySource=copy_source)
        return resp

    def put_object_acl(self, bucket_name, obj_name, acl):
        # 设置对象访问控制权限 ACL
        self.client.put_object_acl(
            Bucket=bucket_name + '-' + self.appid, Key=obj_name, ACL=acl)
        return 0

    def put_object_acl_with_GrantFullControl(self, bucket_name, obj_name,
                                             owner_uin, sub_uin):
        # 设置对象访问控制权限 GrantFullControl
        grant_full_control = 'id="qcs::cam::uin/%s:uin/%s"' % (owner_uin,
                                                               sub_uin)
        self.client.put_object_acl(
            Bucket=bucket_name + '-' + self.appid,
            Key=obj_name,
            GrantFullControl=grant_full_control)

    def put_object_acl_with_GrantRead(self, bucket_name, obj_name, owner_uin,
                                      sub_uin):
        # 设置对象访问控制权限 GrantRead
        grant_read = 'id="qcs::cam::uin/%s:uin/%s"' % (owner_uin, sub_uin)
        self.client.put_object_acl(
            Bucket=bucket_name + '-' + self.appid,
            Key=obj_name,
            GrantRead=grant_read)
        return 0

    def put_object_acl_with_GrantWrite(self, bucket_name, obj_name, owner_uin,
                                       sub_uin):
        # 设置对象访问控制权限 GrantWrite
        grant_write = 'id="qcs::cam::uin/%s:uin/%s"' % (owner_uin, sub_uin)
        self.client.put_object_acl(
            Bucket=bucket_name + '-' + self.appid,
            Key=obj_name,
            GrantWrite=grant_write)

    def get_object_acl(self, bucket_name, obj_name):
        # 获取对象访问控制权限
        resp = self.client.get_object_acl(
            Bucket=bucket_name + '-' + self.appid, Key=obj_name)
        return resp

    def create_multipart_upload(self, bucket_name, obj_name):
        # 创建分块上传
        resp = self.client.create_multipart_upload(
            Bucket=bucket_name + '-' + self.appid, Key=obj_name)
        return resp

    def abort_multipart_upload(self, bucket_name, obj_name, upload_id):
        # 放弃分块上传
        self.client.abort_multipart_upload(
            Bucket=bucket_name + '-' + self.appid,
            Key=obj_name,
            UploadId=upload_id)
        return 0

    def upload_part(self, bucket_name, obj_name, part_number, upload_id,
                    str_len):
        # 上传分块
        resp = self.client.upload_part(
            Bucket=bucket_name + '-' + self.appid,
            Key=obj_name,
            Body="".join(
                random.choice(string.ascii_letters + string.digits)
                for i in range(str_len)),
            PartNumber=part_number,
            UploadId=upload_id)
        return resp

    def list_parts(self, bucket_name, obj_name, upload_id):
        # 列出上传分块
        resp = self.client.list_parts(
            Bucket=bucket_name + '-' + self.appid,
            Key=obj_name,
            UploadId=upload_id)
        return resp

    def complete_multipart_upload(self, bucket_name, obj_name, upload_id,
                                  multipart_upload):
        # 完成分块上传
        resp = self.client.complete_multipart_upload(
            Bucket=bucket_name + '-' + self.appid,
            Key=obj_name,
            UploadId=upload_id,
            MultipartUpload=multipart_upload)
        return resp

    def list_multipart_uploads(self, bucket_name):
        resp = self.client.list_multipart_uploads(Bucket=bucket_name + '-' +
                                                  self.appid)
        return resp

    def upload_file(self, bucket_name, obj_name, file_path):
        # 文件上传(断点续传)
        resp = self.client.upload_file(
            Bucket=bucket_name + "-" + self.appid,
            Key=obj_name,
            LocalFilePath=file_path)
        return resp


if __name__ == "__main__":

    main = CosV5PythonSDKTest(
        region="",
        appid="",
        secret_id="",
        secret_key="",
        end_point="",
        scheme="http")

    try:

        # ---------------------- 存储桶相关操作 ----------------------

        # 创建存储桶
        main.create_bucket(bucket_name="mainbkt")

        # 创建存储桶（带ACL参数）
        main.create_bucket_with_ACL(
            bucket_name="mainbkt", acl="public-read-write")

        # 创建存储桶（带GrantFullControl参数）
        main.create_bucket_with_GrantFullControl(
            bucket_name="mainbkt", owner_uin="1", sub_uin="1")

        # 创建存储桶（GrantRead）
        main.create_bucket_with_GrantRead(
            bucket_name="mainbkt", owner_uin="1", sub_uin="1")

        # 创建存储桶（GrantWrite）
        main.create_bucket_with_GrantWrite(
            bucket_name="mainbkt", owner_uin="1", sub_uin="1")

        # 获取存储桶ACL
        resp = main.get_bucket_acl(bucket_name="mainbkt")

        # head存储桶（查询存储桶是否存在）
        main.head_bucket(bucket_name="mainbkt")
        main.head_bucket(bucket_name="notexist")

        # 获取bucket地域信息
        resp = main.get_bucket_location(bucket_name="mainbkt")

        # 删除存储桶
        main.delete_bucket(bucket_name="mainbkt")

        # 列出存储桶中对象
        resp = main.list_objects(bucket_name="mainbkt")

        # 列出所有带前缀的对象
        resp = main.list_objects_with_prefix(
            bucket_name="mainbkt", prefix="obj")

        # 列出所有对象（设置“/”来模拟目录层级）
        resp = main.list_objects_with_delimiter(
            bucket_name="mainbkt", delimiter="/")

        # 列出所有对象（带Marker参数）
        resp = main.list_objects_with_Marker(bucket_name="mainbkt", marker="a")

        # 列出所有对象（最多不超过Maxkeys个）
        resp = main.list_objects_with_Maxkeys(bucket_name="mainbkt", maxkeys=2)

        # 设置存储桶跨域资源配置（CORSRule写在put_bucket_cors方法里）
        main.put_bucket_cors(bucket_name="mainbkt")

        # 设置多条存储桶跨域资源配置（CORSRule写在put_bucket_cors方法里）
        main.put_bucket_multi_cors(bucket_name="mainbkt")

        # 获取存储桶跨域资源配置
        resp = main.get_bucket_cors(bucket_name="mainbkt")

        # 删除存储桶跨域资源配置
        main.delete_bucket_cors(bucket_name="mainbkt")

        # ---------------------- 对象相关操作 ----------------------

        # 字节（字串）对象上传 1MB
        main.put_object_str(
            bucket_name="mainbkt", obj_name="str1m.txt", str_len=1024 * 1024)

        # 字节（字串）对象上传 1GB
        main.put_object_str(
            bucket_name="mainbkt",
            obj_name="str1g.txt",
            str_len=1024 * 1024 * 1024)

        # 文件对象上传 5MB
        main.put_object_file(
            bucket_name="mainbkt",
            obj_name="file5m.txt",
            file_name="f:\\test5m.txt")

        # 文件对象上传 1GB
        main.put_object_file(
            bucket_name="mainbkt",
            obj_name="file1g.txt",
            file_name="f:\\test1g.txt")

        # 下载对象 5MB
        main.get_object(
            bucket_name="mainbkt",
            obj_name="str5m.txt",
            file_name="f:\\download5m.txt")

        # 下载对象 1GB
        main.get_object(
            bucket_name="mainbkt",
            obj_name="str1g.txt",
            file_name="f:\\download1g.txt")

        # 下载不存在对象
        main.get_object(
            bucket_name="mainbkt",
            obj_name="notexist.txt",
            file_name="f:\\x.txt")

        # 删除对象
        main.delete_object(bucket_name="mainbkt", obj_name="str1m.txt")

        # 删除对象 1GB
        main.delete_object(bucket_name="mainbkt", obj_name="str1g.txt")

        # 删除多个对象，传入对象名list
        resp = main.delete_objects(
            bucket_name="mainbkt", obj_list=["obj", "obja", "objb"])

        # 删除多个对象，传入对象名list和quiet参数
        resp = main.delete_objects_with_quiet(
            bucket_name="mainbkt",
            obj_list=["obj", "obja", "objb"],
            quiet="true")

        # 获取文件属性
        resp = main.head_object(bucket_name="mainbkt", obj_name="obja")

        # 同存储桶内copy对象（相关参数在copy_object_in_same_bucket方法内修改）
        resp = main.copy_object_in_same_bucket()

        # 不同存储桶内copy对象（相关参数在copy_object_in_different_bucket方法内修改）
        resp = main.copy_object_in_different_bucket()

        # 设置文件ACL
        main.put_object_acl(
            bucket_name="mainbkt", obj_name="obj", acl="public-read")

        # 设置文件ACL（带GrantFullControl的用户ID）
        main.put_object_acl_with_GrantFullControl(
            bucket_name="mainbkt", obj_name="obj", owner_uin="1", sub_uin="1")

        # 设置文件ACL（带GrantRead的用户ID）
        main.put_object_acl_with_GrantRead(
            bucket_name="mainbkt", obj_name="obj", owner_uin="1", sub_uin="1")

        # 设置文件ACL（带GrantWrite的用户ID）
        main.put_object_acl_with_GrantWrite(
            bucket_name="mainbkt", obj_name="obj", owner_uin="1", sub_uin="1")

        # 获取对象ACL
        resp = main.get_object_acl(bucket_name="mainbkt", obj_name="obj")

        # 创建分块上传
        resp_create = main.create_multipart_upload(
            bucket_name="mainbkt", obj_name="part100m.txt")

        upload_id = resp_create["UploadId"]

        # 上传分块，每个分块2m，上传50个分块
        resp_upload_list = []
        for i in range(50):
            resp_upload = main.upload_part(
                bucket_name="mainbkt",
                obj_name="part100m.txt",
                part_number=i + 1,
                upload_id=upload_id,
                str_len=2 * 1024 * 1024)
            resp_upload_list.append(resp_upload)

        # 列出所有上传分块
        resp_list = main.list_parts(
            bucket_name="mainbkt",
            obj_name="part100m.txt",
            upload_id=upload_id)
        part_list = resp_list["Part"]

        # 完成分块上传
        main.complete_multipart_upload(
            bucket_name="mainbkt",
            obj_name="part100m.txt",
            upload_id=upload_id,
            multipart_upload={"Part": part_list})

        # 放弃分块上传
        main.abort_multipart_upload(
            bucket_name="mainbkt",
            obj_name="part100m.txt",
            upload_id=upload_id)

        # upload_file接口上传测试

        # 上传对象 5MB
        main.upload_file(
            bucket_name="mainbkt",
            obj_name="upload5m.txt",
            file_path="f:\\test5m.txt")

        # 上传对象 20MB
        main.upload_file(
            bucket_name="mainbkt",
            obj_name="upload20m.txt",
            file_path="f:\\test20m.txt")

        # 上传对象 21MB
        main.upload_file(
            bucket_name="mainbkt",
            obj_name="upload21m.txt",
            file_path="f:\\test21m.txt")

        # 上传对象 1GB
        main.upload_file(
            bucket_name="mainbkt",
            obj_name="upload1g.txt",
            file_path="f:\\test1g.txt")

        print("Succeeded")

    except Exception as e:

        # 可细化CosServiceError/CosClientError
        print("Failed")

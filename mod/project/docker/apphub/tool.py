import os
import json
import shutil
import datetime
import tarfile
import zipfile
import public


class BaseCompressHandler:
    """压缩文件处理基类"""

    def __init__(self):
        pass

    def get_files(self, sfile):
        """获取压缩包内文件列表"""
        pass

    def get_file_info(self, sfile,filename):
        """获取压缩包内文件信息"""
        pass

    def check_file_exists(self, file_path):
        """检查文件是否存在"""
        if not os.path.exists(file_path):
            return False
        return True


class GzHandler(BaseCompressHandler):
    """tar.gz压缩文件处理类"""

    def get_filename(self, item):
        """获取压缩包文件名"""
        filename = item.name
        try:
            filename = item.name.encode('cp437').decode('gbk')
        except:
            pass
        if item.isdir():
            filename += '/'
        return filename

    def check_file_type(self, file_path):
        """检查文件是否为tar文件"""
        if not tarfile.is_tarfile(file_path):
            if file_path[-3:] == ".gz":
                return False, '这不是tar.gz压缩包文件, gz压缩包文件不支持预览,仅支持解压'
            return False, '不是有效的tar.gz压缩包文件'
        return True, ''

    def get_files(self, sfile):
        """获取压缩包内文件列表"""
        if not self.check_file_exists(sfile):
            return public.returnMsg(False, 'FILE_NOT_EXISTS')

        is_valid, message = self.check_file_type(sfile)
        if not is_valid:
            return public.returnMsg(False, message)

        zip_file = tarfile.open(sfile)
        data = {}
        for item in zip_file.getmembers():
            file_name = self.get_filename(item)

            temp_list = file_name.split("/")

            sub_data = data
            for name in temp_list:
                if not name: continue
                if name not in sub_data:
                    if file_name.endswith(name) and not ".{}".format(name) in file_name:
                        sub_data[name] = {
                            'file_size': item.size,
                            'filename': name,
                            'fullpath': file_name,
                            'date_time': public.format_date(times=item.mtime),
                            'is_dir': 1 if item.isdir() else 0
                        }
                    else:
                        sub_data[name] = {}
                sub_data = sub_data[name]

        zip_file.close()
        return data

    def get_file_info(self, sfile, filename):
        """获取压缩包内文件信息"""
        if not self.check_file_exists(sfile):
            return public.returnMsg(False, 'FILE_NOT_EXISTS')

        tmp_path = '{}/tmp/{}'.format(public.get_panel_path(), public.md5(sfile + filename))
        result = {}
        result['status'] = True
        result['data'] = ''
        with tarfile.open(sfile, 'r') as zip_file:
            try:
                zip_file.extract(filename, tmp_path)
                result['data'] = public.readFile('{}/{}'.format(tmp_path, filename))
            except:
                pass
        public.ExecShell("rm -rf {}".format(tmp_path))
        return result


class ZipHandler(BaseCompressHandler):
    """zip压缩文件处理类"""

    def check_file_type(self, sfile, is_close=False):
        """检查文件是否为zip文件"""
        zip_file = None
        try:
            zip_file = zipfile.ZipFile(sfile)
        except:
            pass

        if is_close and zip_file:
            zip_file.close()

        return zip_file

    def get_filename(self, item):
        """获取压缩包文件名"""
        path = item.filename
        try:
            path_name = path.encode('cp437').decode('utf-8')
        except:
            try:
                path_name = path.encode('cp437').decode('gbk')
                path_name = path_name.encode('utf-8').decode('utf-8')
            except:
                path_name = path

        return path_name

    def get_files(self, sfile):
        """获取压缩包内文件列表"""
        if not self.check_file_exists(sfile):
            return public.returnMsg(False, 'FILE_NOT_EXISTS')

        zip_file = self.check_file_type(sfile)
        if not zip_file:
            return public.returnMsg(False, 'NOT_ZIP_FILE')

        data = {}
        for item in zip_file.infolist():
            file_name = self.get_filename(item)

            temp_list = file_name.lstrip("./").split("/")

            sub_data = data
            for name in temp_list:
                if not name: continue
                if name not in sub_data:
                    if file_name.endswith(name):
                        sub_data[name] = {
                            'file_size': item.file_size,
                            'compress_size': item.compress_size,
                            'compress_type': item.compress_type,
                            'filename': name,
                            'fullpath': file_name,
                            'date_time': datetime.datetime(*item.date_time).strftime("%Y-%m-%d %H:%M:%S"),
                            'is_dir': 1 if item.is_dir() else 0
                        }
                    else:
                        sub_data[name] = {}
                sub_data = sub_data[name]

        zip_file.close()
        return data

    def get_file_info(self, sfile,filename):
        """获取压缩包内文件信息"""
        if not self.check_file_exists(sfile):
            return public.returnMsg(False, 'FILE_NOT_EXISTS')

        result = {}
        result['status'] = True
        result['data'] = ''
        with zipfile.ZipFile(sfile, 'r') as zip_file:
            for item in zip_file.infolist():
                z_filename = self.get_filename(item)
                if z_filename == filename:
                    buff = zip_file.read(item.filename)
                    encoding, srcBody = public.decode_data(buff)
                    result['encoding'] = encoding
                    result['data'] = srcBody
                    break
        return result

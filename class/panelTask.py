#coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2019-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: hwliang <hwl@bt.cn>
# -------------------------------------------------------------------

# ------------------------------
# 消息队列
# ------------------------------
import json
import time
import public
import sys
import os
import re
import tarfile
os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')

class bt_task:
    __table = 'task_list'
    __task_tips = '/dev/shm/bt_task_now.pl'
    __task_path = '/www/server/panel/tmp/'
    down_log_total_file = '/tmp/download_total.pl'
    not_web = False
    def __init__(self):

        # 创建数据表
        sql = '''CREATE TABLE IF NOT EXISTS `task_list` (
  `id`              INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` 			TEXT,
  `type`			TEXT,
  `status` 			INTEGER,
  `shell` 			TEXT,
  `other`           TEXT,
  `exectime` 	  	INTEGER,
  `endtime` 	  	INTEGER,
  `addtime`			INTEGER
);'''
        public.M(None).execute(sql, ())

        # 创建临时目录
        if not os.path.exists(self.__task_path):
            os.makedirs(self.__task_path, 384)

    # 取任务列表
    def get_task_list(self, status=-3):
        sql = public.M(self.__table)
        if status != -3:
            sql = sql.where('status=?', (status,))
        data = sql.field(
            'id,name,type,shell,other,status,exectime,endtime,addtime').select()
        return data

    # 取任务列表前端
    def get_task_lists(self, get):
        sql = public.M(self.__table)
        where_sql = None
        where_params = []
        if 'status' in get:
            if get.status == '-3':
                where_sql = "(status=? OR status=?)"
                where_params = [-1, 0]
            else:
                where_sql = "status=?"
                where_params = [get.status]
        if "task_id" in get:
            if where_sql is None:
                where_sql = "id=?"
            else:
                where_sql += " AND id=?"
            where_params.append(get.task_id)
        data = sql.field('id,name,type,shell,other,status,exectime,endtime,addtime').where(where_sql,where_params).order('id asc').limit('10').select()
        if type(data) == str:
            public.WriteLog('任务队列', data,not_web = self.not_web)
            return []
        if not 'num' in get:
            get.num = 15
        num = int(get.num)
        for i in range(len(data)):
            data[i]['log'] = ''
            if data[i]['status'] == -1:
                data[i]['log'] = self.get_task_log(
                    data[i]['id'], data[i]['type'], num)
            elif data[i]['status'] == 1:
                data[i]['log'] = self.get_task_log(
                    data[i]['id'], data[i]['type'], 10)
            if data[i]['type'] == '3':
                data[i]['other'] = json.loads(data[i]['other'])
        return data

    # 创建任务
    def create_task(self, task_name, task_type, task_shell, other=''):
        self.clean_log()
        task_id = public.M(self.__table).add('name,type,shell,other,addtime,status',
                                   (task_name, task_type, task_shell, other, int(time.time()), 0))
        public.WriteFile(self.__task_tips, 'True')
        public.ExecShell("/etc/init.d/bt start")
        if not public.M(self.__table).where('status=?', ('-1',)).count():
            tip_file = "/dev/shm/.start_task.pl"
            tip_time = public.readFile(tip_file)
            if not tip_time or time.time() - int(tip_time) > 600:
                public.ExecShell("/www/server/panel/BT-Task")
        return task_id

    # 修改任务
    def modify_task(self, id, key, value):
        public.M(self.__table).where('id=?', (id,)).setField(key, value)
        return True

    # 删除任务
    def remove_task(self, get):
        if not hasattr(get, 'id'):
            return public.returnMsg(False, 'ID不能为空!')
        task_info = self.get_task_find(get.id)
        if not isinstance(task_info, dict):
            public.returnMsg(False, '任务不存在!')
        public.M(self.__table).where('id=?', (get.id,)).delete()
        if str(task_info['status']) == '-1':
            public.ExecShell(
                "kill -9 $(ps aux|grep 'task.py'|grep -v grep|awk '{print $2}')")
            if task_info['type'] == '1':
                public.ExecShell(
                    "kill -9 $(ps aux|grep '{}')".format(task_info['other']))
                time.sleep(1)
                if os.path.exists(task_info['other']):
                    os.remove(task_info['other'])
            elif task_info['type'] == '3':
                z_info = json.loads(task_info['other'])
                if z_info['z_type'] == 'tar.gz':
                    public.ExecShell(
                        "kill -9 $(ps aux|grep 'tar -zcvf'|grep -v grep|awk '{print $2}')")
                elif z_info['z_type'] == 'rar':
                    public.ExecShell(
                        "kill -9 $(ps aux|grep /www/server/rar/rar|grep -v grep|awk '{print $2}')")
                elif z_info['z_type'] == 'zip':
                    public.ExecShell(
                        "kill -9 $(ps aux|grep '.zip -r'|grep -v grep|awk '{print $2}')")
                    public.ExecShell(
                        "kill -9 $(ps aux|grep '.zip\' -r'|grep -v grep|awk '{print $2}')")
                if os.path.exists(z_info['dfile']):
                    os.remove(z_info['dfile'])
            elif task_info['type'] == '2':
                public.ExecShell(
                    "kill -9 $(ps aux|grep 'tar -zxvf'|grep -v grep|awk '{print $2}')")
                public.ExecShell(
                    "kill -9 $(ps aux|grep '/www/server/rar/unrar'|grep -v grep|awk '{print $2}')")
                public.ExecShell(
                    "kill -9 $(ps aux|grep 'unzip -P'|grep -v grep|awk '{print $2}')")
                public.ExecShell(
                    "kill -9 $(ps aux|grep 'gunzip -c'|grep -v grep|awk '{print $2}')")
            elif task_info['type'] == '0':
                public.ExecShell(
                    "kill -9 $(ps aux|grep '"+task_info['shell']+"'|grep -v grep|awk '{print $2}')")

            public.ExecShell("/etc/init.d/bt start")
        return public.returnMsg(True, '任务已取消!')

    # 取一条任务
    def get_task_find(self, id):
        data = public.M(self.__table).where('id=?', (id,)).field(
            'id,name,type,shell,other,status,exectime,endtime,addtime').find()
        return data

    # 执行任务
    # task_type  0.执行shell  1.下载文件  2.解压文件  3.压缩文件
    def execute_task(self, id, task_type, task_shell, other=''):
        if not os.path.exists(self.__task_path):
            os.makedirs(self.__task_path, 384)
        log_file = self.__task_path + str(id) + '.log'

        # 标记状态执行时间
        self.modify_task(id, 'status', -1)
        self.modify_task(id, 'exectime', int(time.time()))
        task_type = int(task_type)
        # 开始执行
        if task_type == 0:  # 执行命令
            public.ExecShell(task_shell + ' &> ' + log_file)
        elif task_type == 1:  # 下载文件
            if os.path.exists(self.down_log_total_file):
                os.remove(self.down_log_total_file)
            if not os.path.exists(os.path.dirname(other)):
                os.makedirs(os.path.dirname(other))

            public.ExecShell("wget -O '{}' '{}' --no-check-certificate -T 30 -t 5 -d &> {}".format(other, task_shell, log_file))
            if os.path.exists(log_file):
                os.remove(log_file)
        elif task_type == 2:  # 解压文件
            zip_info = json.loads(other)
            self._unzip(task_shell, zip_info['dfile'],
                        zip_info['password'], log_file, zip_info.get('power'), zip_info.get('user'))
        elif task_type == 3:  # 压缩文件
            zip_info = json.loads(other)
            if not 'z_type' in zip_info:
                zip_info['z_type'] = 'tar.gz'
            print(self._zip(
                task_shell, zip_info['sfile'], zip_info['dfile'], log_file, zip_info['z_type'],zip_info['volume_size'],zip_info['save_path']))
        elif task_type == 4:  # 备份数据库
            self.backup_database(task_shell, log_file)
        elif task_type == 5:  # 导入数据库
            self.input_database(task_shell, other, log_file)
        elif task_type == 6:  # 备份网站
            self.backup_site(task_shell, log_file)
        elif task_type == 7:  # 恢复网站
            pass
        elif task_type == 8:  # 复制文件
            _info = json.loads(other)
            public.ExecShell("cp -rv {} {} &> {}".format(_info['sfile'], _info['dfile'], log_file))
        elif task_type == 9:  # 清空回收站
            _info = json.loads(other)
            self.Close_Recycle_bin_new(_info["ctype"], _info["recycle_bin_list"], log_file)
        elif task_type == 10:  # 彻底删除文件
            _info = json.loads(other)
            self.Batch_Del_Recycle_bin(_info["filenames"], log_file)

        # 标记状态与结束时间
        self.modify_task(id, 'status', 1)
        self.modify_task(id, 'endtime', int(time.time()))

    def Batch_Del_Recycle_bin(self, filenames, log_file):
        import shutil
        import database
        database = database.database()
        for filename in filenames:
            with open(log_file, 'a') as f:
                f.write("正在删除：{}\n".format(filename))
            if os.path.basename(filename).startswith('BTDB_'):
                database.DeleteTo(filename)
                with open(log_file, 'a') as f:
                    f.write("{}已删除！\n".format(filename))
                continue
            public.ExecShell('chattr -R -i ' + filename)
            if os.path.isdir(filename):
                try:
                    shutil.rmtree(filename)
                except:
                    public.ExecShell('chattr -R -a ' + filename)
                    public.ExecShell("rm -rf " + filename)
            else:
                try:
                    os.remove(filename)
                except:
                    public.ExecShell("rm -f " + filename)
            with open(log_file, 'a') as f:
                f.write("{}已删除！\n".format(filename))

    def Close_Recycle_bin_new(self, ctype, recycle_bin_list, log_file):
        import shutil
        import database
        database = database.database()
        for rPath in recycle_bin_list:
            public.ExecShell('chattr -R -i ' + rPath)
            rlist = os.listdir(rPath)
            i = 0
            l = len(rlist)
            for name in rlist:
                i += 1
                path = os.path.join(rPath, name)
                try:
                    progress = int((100.0 * i / l))
                except:
                    progress = 0
                data = "正在清空：{} 正在删除：{} 共{}，已完成{}，进度{}%\n".format(rPath, name.replace("_bt_", "/").split('_t_')[0], l, i, progress)
                with open(log_file, 'a') as f:
                    f.write(data)
                if name.startswith('BTDB_') and ctype == 'db':
                    database.DeleteTo(path)
                elif not name.startswith('BTDB_') and ctype == 'files':
                    if os.path.isdir(path):
                        try:
                            shutil.rmtree(path)
                        except:
                            public.ExecShell('chattr -R -a ' + path)
                            public.ExecShell('rm -rf ' + path)
                    else:
                        try:
                            os.remove(path)
                        except:
                            public.ExecShell('rm -f ' + path)
            with open(log_file, 'a') as f:
                f.write("{}已清空完成！\n".format(rPath))

    # 开始检测任务
    def start_task(self):
        noe = False
        n = 0
        tip_file = '/dev/shm/.start_task.pl'
        while True:
            try:
                time.sleep(1)
                public.writeFile(tip_file, str(int(time.time())))
                n += 1
                if not os.path.exists(self.__task_tips) and noe and n < 60:
                    continue
                if os.path.exists(self.__task_tips):
                    os.remove(self.__task_tips)
                n = 0
                public.M(self.__table).where(
                    'status=?', ('-1',)).setField('status', 0)
                task_list = self.get_task_list(0)
                for task_info in task_list:
                    self.execute_task(
                        task_info['id'], task_info['type'], task_info['shell'], task_info['other'])
                noe = True
            except:
                print(public.get_error_info())

    # 前端通过任务ID取某一个任务的日志
    def get_task_log_by_id(self, get):
        task_id = get.id
        task_type = get.task_type
        log_data = {}
        if "num" in get:
            num = int(get.num)
            log_data = self.get_task_log(task_id, task_type, num)
        else:
            log_data = self.get_task_log(task_id, task_type)
        task_obj = self.get_task_find(task_id)
        log_data["status"] = task_obj["status"]
        return log_data

    # 取任务执行日志
    def get_task_log(self, id, task_type, num=5):
        log_file = self.__task_path + str(id) + '.log'
        if not os.path.exists(log_file):
            data = ''
            if(task_type == '1'):
                data = {'name': '下载文件', 'total': 0, 'used': 0,
                        'pre': 0, 'speed': 0, 'time': 0}
            return data

        if(task_type == '1'):
            total = 0
            if not os.path.exists(self.down_log_total_file):
                f = open(log_file, 'r')
                head = f.read(4096)
                content_length = re.findall(r"Length:\s+(\d+)", head)
                if content_length:
                    total = int(content_length[0])
                    public.writeFile(self.down_log_total_file,
                                     content_length[0])
            else:
                total = public.readFile(self.down_log_total_file)
                if not total:
                    total = 0
                total = int(total)

            filename = public.M(self.__table).where(
                'id=?', (id,)).getField('shell')

            # 当前日志行数
            row = public.ExecShell("wc -l %s | awk '{print $1}'"%(log_file))[0].strip()
            try:
                rows = public.readFile("{}{}_rows.pl".format(self.__task_path, id))
                if not rows:
                    rows = "0"
            except:
                rows = "0"
            # 从上次请求读到过的日志到最新的日志
            speed_tmp = public.ExecShell("tail -n +{} {}".format(rows, log_file))[0]
            public.writeFile("{}{}_rows.pl".format(self.__task_path, id), row)
            speed_total = re.findall(
                r"([\d\.]+[BbKkMmGg]).+\s+(\d+)%\s+([\d\.]+[KMBGkmbg])\s+(\w+[sS])", speed_tmp)
            if not speed_total:
                data = {'name': '下载文件{}'.format(
                    filename), 'total': 0, 'used': 0, 'pre': 0, 'speed': 0, 'time': 0}
            else:
                speed_list = []
                for i in speed_total:
                    if i[2][-1].lower() == 'g':
                        speed_list.append(float(i[2][:-1]) * 1024 * 1024 * 1024)
                    elif i[2][-1].lower() == 'm':
                        speed_list.append(float(i[2][:-1]) * 1024 * 1024)
                    elif i[2][-1].lower() == 'k':
                        speed_list.append(float(i[2][:-1]) * 1024)
                speed_list = sorted(speed_list)
                n = len(speed_list)
                # 取中位数
                if n % 2 == 1:
                    speed = speed_list[int((n-1)/2)] * 2
                else:
                    speed = (speed_list[int((n - 2) / 2)] + speed_list[int((n - 1) / 2)])
                speed = round(speed/(1024*1024), 2)
                used = speed_total[-1][0]
                if used.lower().find('k') != -1:
                    used = public.to_size(
                        float(speed_total[-1][0].lower().replace('k', '')) * 1024)
                u_time = speed_total[-1][3].replace(
                    'h', '小时').replace('m', '分').replace('s', '秒')
                data = {'name': '下载文件{}'.format(
                    filename), 'total': total, 'used': used, 'pre': speed_total[-1][1], 'speed': "{}M".format(speed), 'time': u_time}
        else:
            data = public.ExecShell("tail -n {} {}".format(num, log_file))[0]
            if type(data) == list:
                return ''
            if isinstance(data,bytes):
                data = data.decode('utf-8')
            data = data.replace('\x08', '').replace('\n', '<br>')
        return data

    # 清理任务日志
    def clean_log(self):
        import shutil
        s_time = int(time.time())
        timeout = 86400
        for f in os.listdir(self.__task_path):
            filename = self.__task_path + f
            c_time = os.stat(filename).st_ctime
            if s_time - c_time > timeout:
                if os.path.isdir(filename):
                    shutil.rmtree(filename)
                else:
                    os.remove(filename)
        return True

    # 文件压缩
    def _zip(self, path, sfile, dfile, log_file, z_type='tar.gz',volume_size=None,save_path=None):
        if sys.version_info[0] == 2:
            sfile = sfile.encode('utf-8')
            dfile = dfile.encode('utf-8')
        if sys.version_info[0] == 2:
            path = path.encode('utf-8')
        if sfile.find(',') == -1:
            if not os.path.exists(path+'/'+sfile):
                return public.returnMsg(False, 'FILE_NOT_EXISTS')
        # 处理多文件压缩
        sfiles = ''
        for sfile in sfile.split(','):
            if not sfile:
                continue
            sfiles += " '" + sfile + "'"
        # 根据压缩格式执行压缩命令
        if z_type == 'zip':
            if volume_size:
                self.compress_and_split_zip(path, dfile, sfiles, volume_size, log_file)
            else:
                # 创建普通压缩文件
                zip_cmd = "cd '{}' && zip -r '{}' {} &> {}".format(path, dfile, sfiles, log_file)
                public.ExecShell(zip_cmd)
        elif z_type == 'tar.gz':
            if volume_size:
                self.compress_and_split_tar(path, dfile, sfiles, volume_size, log_file)
            else:
                public.ExecShell("cd '" + path + "' && tar -zcvf '" + dfile + "' " + sfiles + " &> " + log_file)

        elif z_type == 'rar':
            rar_file = '/www/server/rar/rar'
            if not os.path.exists(rar_file):
                self.install_rar()
            public.ExecShell("cd '" + path + "' && "+rar_file +
                             " a -r '" + dfile + "' " + sfiles + " &> " + log_file)
        elif z_type == '7z':
            _7z_bin = self.get_7z_bin()
            if not _7z_bin:
                self.install_7zip()
                err_msg = 'p7zip组件未安装，无法压缩为7z压缩包，已尝试自动安装，请稍等几分钟重试!'
                public.WriteLog("文件管理","压缩文件失败，原因：{}，文件: {}".format(err_msg,sfile))
                return public.returnMsg(False, err_msg)
            public.ExecShell("cd {} && {} a -t7z {} {} -y &> {}".format(path, _7z_bin, dfile, sfiles, log_file))
        else:
            return public.returnMsg(False, '指定压缩格式不支持!')

        self.set_file_accept(dfile)
        #public.WriteLog("TYPE_FILE", 'ZIP_SUCCESS', (sfiles, dfile),not_web = self.not_web)
        public.WriteLog("TYPE_FILE", 'ZIP_SUCCESS', (sfiles, dfile))
        return public.returnMsg(True, 'ZIP_SUCCESS')

    def compress_and_split_zip(self, path, dfile, sfiles, volume_size, log_file):
        # 处理 volume_size 参数，转换为 zip 命令支持的格式
        volume_size = volume_size.upper().replace("KB", "K").replace("MB", "M").replace("GB", "G")
        dfile_dir = os.path.dirname(dfile)
        dfile_base = os.path.basename(dfile)
        # 构造分卷文件的名称，存放在相同目录
        split_dfile = os.path.join(dfile_dir, "{}/{}_split_".format(os.path.splitext(dfile_base)[0],os.path.splitext(dfile_base)[0]))
        # 创建分卷压缩文件
        zip_cmd = "cd '{}' && zip -r '{}' {} &> {}".format(path, dfile, sfiles, log_file)
        zip_cmd +=" && mkdir -p {} &> {}".format(os.path.splitext(dfile_base)[0], log_file)
        zip_cmd +=" && split -b {} {} {} &> {}".format(volume_size, dfile,split_dfile, log_file)
        delete_cmd = " && find {} -type f -name '{}' -exec rm -f {} \; &> {}".format(path, os.path.basename(dfile), "{}", log_file)
        zip_cmd += delete_cmd
        public.ExecShell(zip_cmd)

        json_dir = os.path.dirname(split_dfile)
        json_file_path = os.path.join(os.path.dirname(split_dfile), "{}.split_json".format(os.path.splitext(dfile_base)[0]))
        split_dfile=split_dfile
        json_content = {"split_file_path": split_dfile}
        self.generate_json(json_file_path,json_content)

    def compress_and_split_tar(self, path, dfile, sfiles, volume_size, log_file):
        volume_size = volume_size.upper().replace("KB", "K").replace("MB", "M").replace("GB", "G")
        dfile_dir = os.path.dirname(dfile)
        dfile_base = os.path.basename(dfile).replace(".tar.gz", "")

        # 构建没有扩展名的目录路径
        split_dfile_dir = os.path.join(dfile_dir, dfile_base)
        # 构建最终的分卷文件名，包括路径
        split_dfile = os.path.join(split_dfile_dir, dfile_base + ".tar.gz")

        # 确保目标目录存在
        if not os.path.exists(split_dfile_dir):
            os.makedirs(split_dfile_dir)

        # 构建并执行 tar 和 split 命令
        tar_cmd = "cd '{}' && tar cvzf - {} | split -b {} -d - {}  &> {} ".format(path, sfiles,volume_size, split_dfile, log_file)
        public.ExecShell(tar_cmd)

        json_dir = os.path.dirname(split_dfile)
        json_file_path = os.path.join(os.path.dirname(split_dfile), "{}.split_json".format(os.path.splitext(dfile_base)[0]))
        json_content = {"split_file_path": split_dfile}
        self.generate_json(json_file_path,json_content)


    def generate_json(self, json_file_path, content):
        try:
            with open(json_file_path, 'w') as json_file:
                json.dump(content, json_file)
            print("JSON文件生成成功")
        except Exception as e:
            # os.makedirs(json_file_path)
            print(f"生成JSON文件时发生错误: {e}")

    def get_path_access(self, path):
        '''
            @name 获取文件或目录的权限信息
            @param path<string> 文件或目录路径
            @return dict
        '''
        access_list = {}
        try:

            for d in os.listdir(path):
                d_path = os.path.join(path,d)
                access_list[d] = public.get_mode_and_user(d_path)
                if not access_list[d]:
                    access_list[d] = {"mode":755,"user":"www"}
        except:
           pass
        return access_list


    def set_path_access(self, path,old_access_list):
        '''
            @name 设置文件或目录的权限信息
            @param path<string> 文件或目录路径
            @param old_access_list<dict> 旧的权限信息
            @return bool
        '''
        try:
            new_access_list = self.get_path_access(path)
            for d in new_access_list:
                d_path = os.path.join(path,d)
                if d in old_access_list:
                    if new_access_list[d] != old_access_list[d]:
                        self.set_file_accept(d_path)
                else:
                    self.set_file_accept(d_path)
        except:
            return False

        return True

    # 文件解压
    def _unzip(self, sfile, dfile, password, log_file, power=None, user=None):
        if sys.version_info[0] == 2:
            sfile = sfile.encode('utf-8')
            dfile = dfile.encode('utf-8')
        if not os.path.exists(sfile):
            return public.returnMsg(False, 'FILE_NOT_EXISTS')

        if not os.path.isfile(sfile):
            return public.returnMsg(False, '目录无法解压')
        sfile = os.path.abspath(sfile)
        old_dpath_list = self.get_path_access(dfile)

        # 从日志文件获取解压后的文件名
        split_log = None
        # 判断压缩包格式
        if sfile[-4:] == '.zip':
            public.ExecShell("unzip -X -P '"+password+"' -o '" + sfile + "' -d '" + dfile + "' &> " + log_file)
            split_log = lambda x: x[len(dfile)+13 if dfile[-1] == '/' else len(dfile)+14:].split('/')[0].strip() if not x.startswith('Archive') else ""
        elif sfile[-7:] == '.tar.gz' or sfile[-4:] == '.tgz' or (tarfile.is_tarfile(sfile) and sfile[-3:] == '.gz'):
            public.ExecShell("tar zxvf '" + sfile +
                             "' -C '" + dfile + "' &> " + log_file)
            split_log = lambda x: x.strip().split('/')[0]
        elif sfile[-4:] == '.rar':
            rar_file = '/www/server/rar/unrar'
            if not os.path.exists(rar_file):
                self.install_rar()
            pass_opt = '-p-'
            if password:
                password = password.replace("&","\&").replace('"','\"')
                pass_opt = '-p"{}"'.format(password)

            public.ExecShell(rar_file + ' x '+ pass_opt +' -u -y "' + sfile + '" "' + dfile + '" &> ' + log_file)
            split_log = lambda x: re.search(r"/[^\s]+", x).group().strip()[len(dfile) if dfile[-1] == '/' else len(dfile)+1:].split('/')[0] if x.strip().endswith('OK') and re.search(r"/[^\s]+", x) else ""

        elif sfile[-4:] == '.war':
            public.ExecShell("unzip -X -P '"+password+"' -o '" +
                             sfile + "' -d '" + dfile + "' &> " + log_file)
            split_log = lambda x: x[len(dfile)+13 if dfile[-1] == '/' else len(dfile)+14:].split('/')[0].strip() if not x.startswith('Archive') else ""
        elif sfile[-4:] == '.bz2':
            public.ExecShell("tar jxvf '" + sfile +
                             "' -C '" + dfile + "' &> " + log_file)
            split_log = lambda x: x.strip().split('/')[0]
        elif sfile[-3:] == '.7z':
            _7zbin = self.get_7z_bin()
            if not _7zbin:
                self.install_7zip()
                err_msg = 'p7zip组件未安装，无法解压7z文件，已尝试自动安装，请稍等几分钟重试!'
                public.WriteLog("文件管理","解压文件失败，原因：{}，文件: {}".format(err_msg,sfile))
                return public.returnMsg(False, err_msg)
            pass_opt = ""
            if password:
                pass_opt = '-p"{}"'.format(password)
            public.ExecShell('{} x "{}" -o"{}" -bb3 -y {} &> {}'.format(_7zbin,sfile,dfile,pass_opt,log_file))
            split_log = lambda x: x.strip()[1:].split('/')[0].strip() if x.startswith('-') and not x.startswith('--') else ""
        else:
            public.ExecShell("gunzip -c " + sfile + " > " + sfile[:-3])
        # 获取解压后的文件
        # 判断是否能获取解压后的文件名
        if split_log:
            file_list = self.get_unzip_files(log_file, split_log)
            # 解压后设置权限
            for file in file_list:
                try:
                    path = os.path.join(dfile, file)
                except:
                    continue
                if not file.strip() or not os.path.exists(path) or path == dfile:
                    continue
                if power:
                    public.ExecShell("chmod -R {} '{}'".format(power, path))
                if user:
                    public.ExecShell("chown -R {}:{} '{}'".format(user, user, path))

        # 异常处理
        log_msg = public.readFile(log_file)
        err_msg = None
        if log_msg:
            if log_msg.find("incorrect password") != -1 \
                or log_msg.find("The specified password is incorrect.") != -1 \
                or log_msg.find("Data Error in encrypted file. Wrong password") != -1:
                err_msg = '解压密码错误!'
                public.WriteLog("文件管理","解压文件失败，原因：{}，文件: {}".format(err_msg,sfile))
            elif log_msg.find("unsupported compression method 99") != -1:
                err_msg = '不支持的Zip加密压缩方式，对于ZIP压缩包只支持ZIP传统加密方式!'
                public.WriteLog("文件管理","解压文件失败，原因：{}，文件: {}".format(err_msg,sfile))
            elif log_msg.find("is not RAR archive") != -1:
                err_msg = "不是rar压缩包,检查是否为其它压缩格式修改扩展名为rar的文件!"
                public.WriteLog("文件管理","解压文件失败，原因：{}，文件: {}".format(err_msg,sfile))
            elif log_msg.find("gzip: stdin") != -1:
                public.ExecShell("tar xvf '" + sfile + "' -C '" + dfile + "' &> " + log_file)

        if err_msg: return public.returnMsg(False, err_msg)

        # 检查是否设置权限
        if self.check_dir(dfile):
            sites_path = public.M('config').where(
                'id=?', (1,)).getField('sites_path')
            if dfile.find('/www/wwwroot') != -1 or dfile.find(sites_path) != -1:
                # 只设置新的目录权限
                self.set_path_access(dfile,old_dpath_list)
            else:
                try:
                    import pwd
                    user = pwd.getpwuid(os.stat(dfile).st_uid).pw_name
                    public.ExecShell("chown %s:%s %s" % (user, user, dfile))
                except KeyError:
                    return public.ReturnMsg(False, 'SET_FILE_ACCEPT_ERROR')

        public.WriteLog("TYPE_FILE", 'UNZIP_SUCCESS', (sfile, dfile))
        return public.returnMsg(True, 'UNZIP_SUCCESS')

    def get_unzip_files(self, log_file, split_log):
        '''
            @name 获取解压后的文件
            @param log_file<string> 解压日志文件路径
            @return set
        '''
        files = []
        try:
            with open(log_file, 'r') as f:
                while True:
                    data = f.readlines(1024 * 1024 * 30)
                    if data:
                        for x in data:
                            file = split_log(x)
                            if file and file not in files:
                                files.append(file)
                    else:
                        break
                return set(files)
        except:
            return set(files)

    def get_7z_bin(self):
        '''
            @name 获取7z命令路径
            @author hwliang
            @return {string} 7z命令路径
        '''
        _7z_bins = ["/usr/bin/7z","/usr/bin/7za","/usr/bin/7zr"]
        for _7z_bin in _7z_bins:
            if os.path.exists(_7z_bin):
                return _7z_bin
        return None

    def install_7zip(self):
        '''
            @name 安装7zip
            @author hwliang
            @return {bool} True/False
        '''
        _7z_bin = self.get_7z_bin()
        if _7z_bin:
            return True

        # 是否已经尝试安装过
        install_tip = '{}/data/7z_install.pl'.format(public.get_panel_path())
        if os.path.exists(install_tip):
            return False

        if os.path.exists("/usr/bin/apt-get"):
            public.ExecShell("nohup apt-get -y install p7zip-full &> /dev/null &")
        elif os.path.exists("/usr/bin/yum"):
            public.ExecShell("nohup yum -y install p7zip &> /dev/null &")
        elif os.path.exists("/usr/bin/dnf"):
            public.ExecShell("nohup dnf -y install p7zip &> /dev/null &")
        else:
            return False
        return True

    # 备份网站
    def backup_site(self, id, log_file):
        find = public.M('sites').where(
            "id=?", (id,)).field('name,path,id').find()
        fileName = find['name']+'_' + \
            time.strftime('%Y%m%d_%H%M%S', time.localtime())+'.zip'
        backupPath = public.M('config').where(
            'id=?', (1,)).getField('backup_path') + '/site'

        zipName = backupPath + '/'+fileName
        if not (os.path.exists(backupPath)):
            os.makedirs(backupPath)

        execStr = "cd '" + find['path'] + "' && zip '" + \
            zipName + "' -x .user.ini -r ./ &> " + log_file
        public.ExecShell(execStr)

        sql = public.M('backup').add('type,name,pid,filename,size,addtime',
                                     (0, fileName, find['id'], zipName, 0, public.getDate()))
        public.WriteLog('TYPE_SITE', 'SITE_BACKUP_SUCCESS', (find['name'],),not_web = self.not_web)
        return public.returnMsg(True, 'BACKUP_SUCCESS')

    # 备份数据库
    def backup_database(self, id, log_file):
        name = public.M('databases').where("id=?", (id,)).getField('name')
        find = public.M('config').where('id=?', (1,)).field(
            'mysql_root,backup_path').find()

        if not os.path.exists(find['backup_path'] + '/database'):
            public.ExecShell('mkdir -p ' + find['backup_path'] + '/database')
        self.mypass(True, find['mysql_root'])

        fileName = name + '_' + \
            time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.sql.gz'
        backupName = find['backup_path'] + '/database/' + fileName
        public.ExecShell("/www/server/mysql/bin/mysqldump --force --opt \"" +
                         name + "\" | gzip > " + backupName)
        if not os.path.exists(backupName):
            return public.returnMsg(False, 'BACKUP_ERROR')

        self.mypass(False, find['mysql_root'])

        sql = public.M('backup')
        addTime = time.strftime('%Y-%m-%d %X', time.localtime())
        sql.add('type,name,pid,filename,size,addtime',
                (1, fileName, id, backupName, 0, addTime))
        public.WriteLog("TYPE_DATABASE", "DATABASE_BACKUP_SUCCESS", (name,),not_web = self.not_web)
        return public.returnMsg(True, 'BACKUP_SUCCESS')

    # 导入数据库
    def input_database(self, id, file, log_file):
        name = public.M('databases').where("id=?", (id,)).getField('name')
        root = public.M('config').where('id=?', (1,)).getField('mysql_root')
        tmp = file.split('.')
        exts = ['sql', 'gz', 'zip']
        ext = tmp[len(tmp) - 1]
        if ext not in exts:
            return public.returnMsg(False, 'DATABASE_INPUT_ERR_FORMAT')

        isgzip = False
        if ext != 'sql':
            tmp = file.split('/')
            tmpFile = tmp[len(tmp)-1]
            tmpFile = tmpFile.replace('.sql.' + ext, '.sql')
            tmpFile = tmpFile.replace('.' + ext, '.sql')
            tmpFile = tmpFile.replace('tar.', '')
            backupPath = public.M('config').where(
                'id=?', (1,)).getField('backup_path') + '/database'

            if ext == 'zip':
                public.ExecShell("cd " + backupPath + " && unzip " + file)
            else:
                public.ExecShell("cd " + backupPath + " && tar zxf " + file)
                if not os.path.exists(backupPath + "/" + tmpFile):
                    public.ExecShell("cd " + backupPath +
                                     " && gunzip -q " + file)
                    isgzip = True

            if not os.path.exists(backupPath + '/' + tmpFile) or tmpFile == '':
                return public.returnMsg(False, 'FILE_NOT_EXISTS', (tmpFile,))
            self.mypass(True, root)
            public.ExecShell(public.GetConfigValue('setup_path') + "/mysql/bin/mysql -uroot -p" +
                             root + " --force \"" + name + "\" < " + backupPath + '/' + tmpFile)
            self.mypass(False, root)
            if isgzip:
                public.ExecShell('cd ' + backupPath +
                                 ' && gzip ' + file.split('/')[-1][:-3])
            else:
                public.ExecShell("rm -f " + backupPath + '/' + tmpFile)
        else:
            self.mypass(True, root)
            public.ExecShell(public.GetConfigValue(
                'setup_path') + "/mysql/bin/mysql -uroot -p" + root + " --force \"" + name + "\" < " + file)
            self.mypass(False, root)

        public.WriteLog("TYPE_DATABASE", 'DATABASE_INPUT_SUCCESS', (name,),not_web = self.not_web)
        return public.returnMsg(True, 'DATABASE_INPUT_SUCCESS')

    # 配置
    def mypass(self, act, root):
        my_cnf = '/etc/my.cnf'
        public.ExecShell("sed -i '/user=root/d' " + my_cnf)
        public.ExecShell("sed -i '/password=/d' " + my_cnf)
        if act:
            mycnf = public.readFile(my_cnf)
            rep = "\[mysqldump\]\nuser=root"
            sea = "[mysqldump]\n"
            subStr = sea + "user=root\npassword=\"" + root + "\"\n"
            mycnf = mycnf.replace(sea, subStr)
            if len(mycnf) > 100:
                public.writeFile(my_cnf, mycnf)

    # 设置权限
    def set_file_accept(self, filename):
        public.ExecShell('chown -R www:www ' + filename)
        public.ExecShell('chmod -R 755 ' + filename)

    # 检查敏感目录
    def check_dir(self, path):
        path = path.replace('//', '/')
        if path[-1:] == '/':
            path = path[:-1]

        nDirs = ('',
                 '/',
                 '/*',
                 '/www',
                 '/root',
                 '/boot',
                 '/bin',
                 '/etc',
                 '/home',
                 '/dev',
                 '/sbin',
                 '/var',
                 '/usr',
                 '/tmp',
                 '/sys',
                 '/proc',
                 '/media',
                 '/mnt',
                 '/opt',
                 '/lib',
                 '/srv',
                 '/selinux',
                 '/www/server',
                 '/www/server/data',
                 public.GetConfigValue('logs_path'),
                 public.GetConfigValue('setup_path'))

        return not path in nDirs

    # 安装rar组件
    def install_rar(self):
        unrar_file = '/www/server/rar/unrar'
        rar_file = '/www/server/rar/rar'
        bin_unrar = '/usr/local/bin/unrar'
        bin_rar = '/usr/local/bin/rar'
        if os.path.exists(unrar_file) and os.path.exists(bin_unrar):
            try:
                import rarfile
            except:
                public.ExecShell("pip install rarfile")
            return True

        import platform

        os_bit = ''
        if platform.machine() == 'x86_64':
            os_bit = '-x64'
        download_url = public.get_url() + '/src/rarlinux'+os_bit+'-5.6.1.tar.gz'

        tmp_file = '/tmp/bt_rar.tar.gz'
        public.ExecShell('wget -O ' + tmp_file + ' ' + download_url)
        if os.path.exists(unrar_file):
            public.ExecShell("rm -rf /www/server/rar")
        public.ExecShell("tar xvf " + tmp_file + ' -C /www/server/')
        if os.path.exists(tmp_file):
            os.remove(tmp_file)
        if not os.path.exists(unrar_file):
            return False

        if os.path.exists(bin_unrar):
            os.remove(bin_unrar)
        if os.path.exists(bin_rar):
            os.remove(bin_rar)

        public.ExecShell('ln -sf ' + unrar_file + ' ' + bin_unrar)
        public.ExecShell('ln -sf ' + rar_file + ' ' + bin_rar)
        #public.ExecShell("pip install rarfile")
        return True


if __name__ == '__main__':
    p = bt_task()
    #p.create_task('测试执行SHELL',0,'yum install wget -y','')
    # print(p.get_task_list())
    # p.modify_task(3,'status',0)
    #p.modify_task(3,'shell','bash /www/server/panel/install/install_soft.sh 0 update php 5.6')
    # p.modify_task(1,'other','{"sfile":"BTPanel","dfile":"/www/test.rar","z_type":"rar"}')
    p.start_task()
    # p._zip(sys.argv[1],sys.argv[2],sys.argv[3],sys.argv[4],sys.argv[5])

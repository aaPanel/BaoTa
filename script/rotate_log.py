import os ,sys 
import glob  
import time  
import shutil
import json
os.chdir("/www/server/panel")
if '/www/server/panel' not in sys.path:
    sys.path.insert(0,'/www/server/panel')
if '/www/server/panel/class' not in sys.path:
    sys.path.insert(0,'class/')

import public


class LogSplit():
    def __init__(self, split_type="day", log_size=1024*1024*10, limit=180, compress=False):
        # 初始化LogSplit对象
        self.stype = split_type  # 设置切割类型（每天或按大小）
        self.log_size = log_size  # 设置日志文件的切割大小阈值
        self.limit = limit  # 设置保留的日志文件数量
        self.compress = compress  # 设置是否压缩日志文件
        self._time = time.strftime("%Y-%m-%d_%H%M%S")  # 获取当前时间，用于生成文件名

    def split_logs(self, directory):
        self._start()
        self._show()
        # 切割指定目录下的所有日志文件
        counter=0
        for logfile in glob.glob(os.path.join(directory, '*.log')):
            task_name = '[勿删]切割计划任务日志'
            echo=public.M('crontab').where('name=?', (task_name,)).find()['echo']
            cron_file="/www/server/cron/{}.log".format(echo)
            if logfile!=cron_file:
                self.process_log_file(logfile)  # 处理每一个日志文件
                counter+=1
        if counter==0:
            print()
            print("|---暂无日志文件可以处理")
        self._stop()

    def process_log_file(self, logfile):
        print()
        print(f"|---开始处理日志文件：{logfile}")
        if os.path.getsize(logfile) < self.log_size and self.stype == 'size':
            print(f"|---跳过文件 {logfile}，文件大小未达到设定的切割阈值{public.to_size(self.log_size)}")
            return

        base_path, filename = os.path.split(logfile)
        log_identifier = filename.split('.')[0]+"_log"
        new_directory = os.path.join(base_path, log_identifier)

        # 检查同名文件是否存在，如果存在且不是目录，则删除
        if os.path.exists(new_directory):
            if not os.path.isdir(new_directory):
                # print(f"存在同名文件，正在删除：{new_directory}")
                os.remove(new_directory)
        
        # 确保目录存在
        if not os.path.exists(new_directory):
            # print(f"创建目录：{new_directory}")
            os.makedirs(new_directory)
        else:
            # print(f"目录已存在：{new_directory}")
            pass

        # 创建新的日志文件路径
        new_log_file = os.path.join(new_directory, f"{self._time}.log")
        # print(f"新日志文件将被创建于：{new_log_file}")

        # 移动日志文件
        try:


            shutil.move(logfile, new_log_file)
            print(f"|---日志文件 {logfile} 已被切割并移动到 {new_log_file}")

            # 压缩日志文件
            if self.compress:
                os.system(f'gzip "{new_log_file}"')
                print(f"|---日志文件已被压缩：{new_log_file}.gz")
            self.manage_old_logs(new_directory)
        except Exception as e:
            print(f"|---在移动或压缩文件时发生错误：{e}")

    def _start(self):
        print('==================================================================')
        print('★[' + time.strftime("%Y/%m/%d %H:%M:%S") + ']切割计划任务日志')
        print('==================================================================')

    def _show(self):
        if self.stype == "day":
            print('|---切割方式: 每天切割1份')
        else:
            print('|---切割方式: 按文件大小切割，文件超过{}开始切割'.format(public.to_size(self.log_size)))
        print('|---当前保留最新的[{}]份'.format(self.limit))

    def _stop(self):
        print()
        print('=================已完成所有日志切割任务==================')

    def manage_old_logs(self, directory):
        # 获取目录中所有的日志文件
        files = sorted(glob.glob(os.path.join(directory, '*')),
                    key=os.path.getmtime,
                    reverse=True)
        
        # 如果文件数量超过限制，则删除最旧的文件
        if len(files) > self.limit:
            print("|---检测到旧文件数量超过限制，开始删除旧的文件.....")
            for old_file in files[self.limit:]:
                os.remove(old_file)
                # print(f"删除旧日志文件：{old_file}")
            print("|---删除旧文件成功")




def load_config(config_path):
    if not os.path.exists(config_path):
        default_config = {
            "log_size": 0,
            "hour": "2",
            "minute": "0",
            "num": 10,
            "compress": False,
            "stype": "day"
        }
        with open(config_path, 'w') as config_file:
            json.dump(default_config, config_file, indent=4)
        return default_config

    with open(config_path, 'r') as config_file:
        config = json.load(config_file)

    if not config:
        config = {
            "log_size": 0,
            "hour": "2",
            "minute": "0",
            "num": 10,
            "compress": False,
            "stype": "day"
        }
    return config

def main():
    config_path = '/www/server/panel/data/crontab_log_split.conf'  # 配置文件路径
    config = load_config(config_path)  # 加载配置
    
    log_splitter = LogSplit(
        split_type='day' if config['log_size'] == 0 else 'size',  # 根据配置决定切割类型
        log_size=float(config['log_size']),  # 设置日志大小阈值
        limit=int(config['num']),  # 设置文件保留数量
        compress=config['compress']  # 设置是否压缩
    )
    
    log_directory = '/www/server/cron'  # 日志文件目录
    log_splitter.split_logs(log_directory)  # 执行日志切割

if __name__ == '__main__':
    main()  # 程序入口

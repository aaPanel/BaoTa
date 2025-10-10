#!/usr/bin/python
# coding: utf-8
# -----------------------------
# 宝塔Linux面板网站运行日志切割脚本
# -----------------------------
import sys
import os
import shutil
import time
import glob

os.chdir("/www/server/panel")
if '/www/server/panel' not in sys.path:
    sys.path.insert(0,'/www/server/panel')
if '/www/server/panel/class' not in sys.path:
    sys.path.insert(0,'class/')

import public, json

try:
    from projectModel.javaModel import main as javaMod
    from projectModel.pythonModel import main as pythonMod
    from projectModel.nodejsModel import main as nodejsMod
    from projectModel.otherModel import main as otherMod
    from projectModel.goModel import main as goMod
    from projectModel.netModel import main as netMod

    mods = {
        "java": javaMod(),
        "python": pythonMod(),
        "node": nodejsMod(),
        "other": otherMod(),
        "go": goMod(),
        "net": netMod(),
    }
except Exception as e:
    print(str(e))
    print("******面板项目日志切割任务出错******")

print('==================================================================')
print('★[' + time.strftime("%Y/%m/%d %H:%M:%S") + '] 切割日志')
print('==================================================================')


class LogSplit():
    __slots__ = ("stype", "log_size", "limit", "_time", "compress", "exclude_sites")

    @classmethod
    def build_log_split(cls, name):
        logsplit = cls()
        path = '{}/data/run_log_split.conf'.format(public.get_panel_path())
        if os.path.exists(path):
            try:
                data = json.loads(public.readFile(path))
            except:
                return
        _clean(data)
        public.writeFile(path, json.dumps(data))
        target = data.get(name)
        if not target :            
            return  "文件为空"
        else:
            for i in cls.__slots__:
                if i in target:
                    setattr(logsplit, i, target[i])
            logsplit._show()
            return logsplit

    def __init__(self, split_type: str = "day", limit: int = 180, log_size: int = 1024, compress: bool = False) -> None:
        self.stype = split_type
        self.log_size = log_size
        self.limit = limit
        self._time = time.strftime("%Y-%m-%d_%H%M%S")
        self.compress = compress
        self.exclude_sites = []

    def _show(self):
        if self.stype == "day":
            print('|---切割方式: 每天切割1份')
        else:
            print('|---切割方式: 按文件大小切割，文件超过{}开始切割'.format(public.to_size(self.log_size)))
        print('|---当前保留最新的[{}]份'.format(self.limit))

    def _to_zip(self, file_path):
        os.system('gzip {}'.format(file_path))

    def _del_surplus_log(self, history_log_path, log_prefix):
        if not os.path.exists(history_log_path):
            os.makedirs(history_log_path, mode=0o755)
        logs = sorted(glob.glob(history_log_path + '/' + log_prefix + "*_log.*"))

        count = len(logs)
        if count >= self.limit:
            for i in logs[:count - self.limit + 1]:
                if os.path.exists(i):
                    os.remove(i)
                    print('|---多余日志[' + i + ']已删除!')

    def __call__(self, pjanme: str, sfile: str, log_prefix: str):
        base_path, filename = sfile.rsplit("/", 1)
        history_log_path = '{}/{}-history_logs'.format(base_path, pjanme)

        if self.stype == 'size' and os.path.getsize(sfile) < self.log_size:
            print('|---文件大小未超过[{}]，跳过!'.format(public.to_size(self.log_size)))
            return

        self._del_surplus_log(history_log_path, log_prefix)

        if os.path.exists(sfile):
            history_log_file = history_log_path + '/' + log_prefix + '_' + self._time + '_log.log'
            if not os.path.exists(history_log_file):
                with open(history_log_file, 'wb') as hf, open(sfile, 'r+b') as lf:
                    while True:
                        chunk_data = lf.read(1024*100)
                        if not chunk_data:
                            break
                        hf.write(chunk_data)
                    lf.seek(0)
                    lf.truncate()
            if self.compress:
                self._to_zip(history_log_file)

            print('|---已切割日志到:' + history_log_file + (".gz" if self.compress else ""))
        else:
            print('|---项目{}的目标日志文件:{}已丢失，请注意'.format(pjanme, sfile))



def main(name):
    logsplit = LogSplit.build_log_split(name)
    if logsplit=="文件为空":
       print("******检测到的面板项目日志切割任务配置为空，请重新设置项目日志切割任务******")
       return 
    if not logsplit:
        print("******面板项目日志切割任务配置文件丢失******")
        return
    project = public.M('sites').where("project_type <> ?  and name = ?", ("PHP", name)).find()
    project['project_config'] = json.loads(project['project_config'])
    for_split_func = getattr(mods.get(project["project_type"].lower()), "for_split")
    if callable(for_split_func):
        print('|---开始对{}项目[{}]的日志进行操作'.format(project["project_type"], project["name"]))
        try:
            for_split_func(logsplit, project)
            print('|---已完成对{}项目[{}]的日志分割任务'.format(project["project_type"], project["name"]))
        except:
            import  traceback
            print(traceback.format_exc())
            print('|---{}项目[{}]的日志分割任务出错'.format(project["project_type"], project["name"]))
    else:
        print("******面板项目日志切割任务出错******")
    print('=================已完成所有日志切割任务==================')


def _clean(data):
    res = public.M('crontab').field('name').select()
    del_config = []
    for i in data.keys():
        for j in res:
            if j["name"].find(i) != -1 and j["name"].find("运行日志切"):
                break
        else:
            del_config.append(i)

    for i in del_config:
        del data[i]


if __name__ == '__main__':
    if len(sys.argv) == 2:
        name = sys.argv[1].strip()
        main(name)
    else:
        print("******面板项目日志切割任务配置参数出错******")

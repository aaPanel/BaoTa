# coding: utf-8
# +-------------------------------------------------------------------
# | 宝塔Linux面板
# +-------------------------------------------------------------------
# | Copyright (c) 2015-2099 宝塔软件(http:#bt.cn) All rights reserved.
# +-------------------------------------------------------------------
# | Author: sww <hwl@bt.cn>
# +-------------------------------------------------------------------
import warnings
warnings.filterwarnings("ignore", message=r".*doesn't\s+match\s+a\s+supported\s+version", module="requests")

import json
import os
import re
import time
import traceback
import public
import json
from flask import request

try:
    from BTPanel import cache
    import requests
except:
    pass



class crontab:
    field = 'id,name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sName,sBody,sType,urladdress,save_local,notice,notice_channel,db_type,split_type,split_value,type_id,rname,keyword,post_param,flock,time_set,backup_mode,db_backup_path,time_type,special_time,log_cut_path,user_agent,version,table_list,result,second,stop_site,params'
    
    def __init__(self):
        try:
            cront = public.M('crontab').order("id desc").field(self.field).select()
        except Exception as e:
            try:
                public.check_database_field("crontab.db", "crontab")
            except Exception as e:
                pass
        
        # cront = public.M('crontab').order("id desc").field(self.field).select()
        # if type(cront) == str:
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'status' INTEGER DEFAULT 1", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save' INTEGER DEFAULT 3", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'backupTo' TEXT DEFAULT off", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sName' TEXT", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sBody' TEXT", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'sType' TEXT", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'urladdress' TEXT", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'save_local' INTEGER DEFAULT 0", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'notice' INTEGER DEFAULT 0", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'notice_channel' TEXT DEFAULT ''", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'db_type' TEXT DEFAULT ''", ())
        #     public.M('crontab').execute("UPDATE 'crontab' SET 'db_type'='mysql' WHERE sType='database' and db_type=''", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'split_type' TEXT DEFAULT ''", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'split_value' INTEGER DEFAULT 0", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'rname' TEXT DEFAULT ''", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'type_id' INTEGER", ())
        #     public.M('crontab').execute("PRAGMA foreign_keys=on", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD CONSTRAINT 'fk_type_id' FOREIGN KEY ('type_id') REFERENCES 'crontab_types' ('id')", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'keyword' TEXT DEFAULT ''", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'post_param' TEXT DEFAULT ''", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'flock' INTEGER DEFAULT 0", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'time_set' TEXT DEFAULT ''", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'backup_mode' TEXT DEFAULT ''", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'db_backup_path' TEXT DEFAULT ''", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'time_type' TEXT DEFAULT ''", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'special_time' TEXT DEFAULT ''", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'log_cut_path' TEXT DEFAULT ''", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'user_agent' TEXT DEFAULT ''", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'version' TEXT DEFAULT ''", ())
        #     public.M('crontab').execute("ALTER TABLE 'crontab' ADD 'table_list' TEXT DEFAULT ''", ())
        #     cront = public.M('crontab').order("id desc").field(self.field).select()
        
        public.check_table('crontab_types',
                           '''CREATE TABLE "crontab_types" (
                                            "id" INTEGER PRIMARY KEY AUTOINCREMENT,
                                            "name" VARCHAR DEFAULT '',
                                            "ps" VARCHAR DEFAULT '');''')
        
        # try:
        #     self.check_crontab_service()
        #     # self.check_and_delete_mysql_backup_task()
        # except:
        #     pass
    
    def check_and_delete_mysql_backup_task(self):
        import subprocess
        # 标记文件路径
        flag_file = '{}/data/mysql_backup_check.flag'.format(public.get_panel_path())
        # 检查标记文件是否存在，如果存在则不执行任务
        if os.path.exists(flag_file):
            return
        
        try:
            # 查找数据库中名为 '自动备份mysql数据库[所有]' 的任务
            task_name = '自动备份mysql数据库[所有]'
            
            # 查询数据库任务信息
            crontab_task = public.M('crontab').where('name=?', (task_name,)).find()
            # 如果没有找到此任务，返回消息
            if not crontab_task:
                return
                # 如果找到任务，检查其 status 是否为 0
            if crontab_task['status'] == 0:
                # 检查系统中是否存在该任务的 echo 值
                result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
                echo= crontab_task['echo']
                if echo in result.stdout:
                    data={"id":crontab_task['id']}
                    crontab().DelCrontab(public.to_dict_obj(data))
            # 创建标记文件，防止任务重复执行
            with open(flag_file, 'w') as f:
                f.write('')
            return
        
        except Exception as e:
            # print(e)
            return
    
    def get_zone(self, get):
        try:
            try:
                import pytz
            except:
                import os
                os.system("btpip install pytz")
                import pytz
            areadict = {}
            for i in pytz.all_timezones:
                if i.find('/') != -1:
                    area, zone = i.split('/')[0], i.split('/')[1]
                    if area not in areadict:
                        areadict[area] = [zone]
                    areadict[area].append(zone)
            for k, v in areadict.items():
                if k == 'status': continue
                areadict[k] = sorted(list(set(v)))
            # 取具体时区地区
            result = public.ExecShell('ls -l /etc/localtime')
            area = result[0].split('/')[-2].strip()
            zone = result[0].split('/')[-1].strip()
            # areadict['status'] = [area, zone]
            return areadict
        except:
            return public.returnMsg(False, '获取时区失败!')
    
    # 获取所有domain
    def get_domain(self, get=None):
        try:
            domains = public.M('domain').field('name').select()
            domains = ['http://' + i['name'] for i in domains]
            return domains
        except:
            return traceback.format_exc()
    
    # 设置置顶
    def set_task_top(self, get=None):
        """
        设置任务置顶，不传参数查询设置的计划任务列表
        :param get: task_id
        :return:
        """
        cron_task_top_path = '/www/server/panel/data/cron_task_top'
        if os.path.exists(cron_task_top_path):
            task_top = json.loads(public.readFile(cron_task_top_path))
        else:
            task_top = {'list': []}
        if get and hasattr(get, 'task_id'):
            task_top['list'] = [i for i in task_top['list'] if i != get['task_id']]
            task_top['list'].append(get['task_id'])
            public.writeFile(cron_task_top_path, json.dumps(task_top))
            return public.returnMsg(True, '设置置顶成功！')
        return task_top
    
    # 取消置顶
    def cancel_top(self, get):
        """
        取消任务置顶
        :param get:task_id
        :return:
        """
        cron_task_top_path = '/www/server/panel/data/cron_task_top'
        if os.path.exists(cron_task_top_path):
            task_top = json.loads(public.readFile(cron_task_top_path))
        else:
            return public.returnMsg(True, '取消置顶成功！')
        if hasattr(get, 'task_id'):
            if get.task_id in task_top['list']:
                task_top['list'].remove(get.task_id)
                public.writeFile(cron_task_top_path, json.dumps(task_top))
                return public.returnMsg(True, '取消置顶成功！')
            else:
                return public.returnMsg(False, '该计划任务已不在置顶列表中，请刷新页面确认最新状态。')
        else:
            return public.returnMsg(False, '请传入取消置顶ID！')
    
    # 取计划任务列表
    def GetCrontab(self, get):
        try:
            self.check_crontab_service()
            self.check_and_delete_mysql_backup_task()
            self.checkBackup()
            self.__clean_log()
            type_id = get.type_id if (hasattr(get, 'type_id') and get.type_id is not None) else ""
            db_obj = public.M('crontab')
            query = db_obj.order("id desc").field(self.field)
            
            if type_id:
                query=self._filter_by_type_id(query,type_id)
            
            # 获取所有任务数据
            all_tasks = query.select()

            # 获取置顶任务列表
            top_list = self.set_task_top()['list']
            top_data, other_data = self._partition_tasks(all_tasks, top_list)
            top_data=self._sort_tasks(top_data,get)
            other_data=self._sort_tasks(other_data,get)
            # 重新组织任务顺序
            data = top_data + other_data
            
            # 搜索过滤
            if hasattr(get, 'search') and get.search:
                data = self.search_tasks(data, get.search)
            
            # 应用分页
            paged_data, page_data = self._paginate(data, get)
            # 格式化任务数据
            self._format_task(paged_data, top_list)
            result = self._construct_result(db_obj, page_data, paged_data)
            return result
        
        except Exception as e:
            # print(traceback.format_exc())
            return public.returnMsg(False, '查询失败: ' + str(e))
    
    
    def _filter_by_type_id(self,query,type_id):
        filters={
            '-1':('name like ?','%勿删%'),
            '0':('name not like ?','%勿删%'),
            '-2':('status=?',1),
            '-3':('status=?',0)
        }
        if type_id in filters:
            return query.where(*filters[type_id])
        return query.where('type_id=?',type_id)
    
    
    
    def _partition_tasks(self, all_tasks, top_list):
        # 使用 set 加速查找
        top_set = set(top_list)
        # 获取 top_data
        top_data = [task for task in all_tasks if str(task['id']) in top_set]
        # 按照 top_list 的顺序对 top_data 进行排序
        top_data = sorted(top_data, key=lambda x: top_list.index(str(x['id'])))
        # 获取 other_data
        other_data = [task for task in all_tasks if str(task['id']) not in top_set]
        return top_data, other_data
    
    def get_type_name(self, task):
        rname = task.get('rname', '')
        type_id = task.get('type_id', '')
        type_names = []
        
        # if '勿删' in rname:
        #     type_names.append('系统任务')
        if  type_id == 0:
            if '勿删' in rname:
                type_names.append('系统任务')
            else:
                type_names.append('默认分类')
        type_name = public.M('crontab_types').where("id=?", (type_id,)).getField('name')
        if type_name:
            type_names.append(type_name)
        
        return ', '.join(type_names)
    
    def _sort_tasks(self,tasks,get):
        order_param=getattr(get,'order_param',None)
        if order_param:
            sort_key,order=order_param.split(' ')
            reverse_order=order=='desc'
            if "rname" in order_param:
                for task in tasks:
                    if not task.get('rname'):
                        task['rname'] = task['name']  # 将没有值的 rname 设置为 name 的值
            if "addtime" in order_param:
                for task in tasks:
                    task['addtime']=self.get_addtime(task)
                    task['addtime_calculated'] = True
            return sorted(tasks,key=lambda x:x[sort_key],reverse=reverse_order)
        return tasks
    
    def _paginate(self,data,get):
        
        total_count=len(data)
        p=int(get.p) if hasattr(get,'p')else None
        count=int(get.count) if hasattr(get,'count')else None
        if p and count:
            start=(p-1)*count
            end=start+count
            page_data=public.get_page(total_count,p,count)
            paged_data=data[start:end]
        else:
            page_data=None
            paged_data=data
        return paged_data,page_data
    
    def _format_task(self,paged_data,top_list):
        top_set=set(top_list)
        for task in paged_data:
            task['type_zh']=self._get_task_type_zh(task)
            task['cycle']=self.generate_cycle(task['type'],task['where1'],task['where_hour'],task['where_minute'],task['sType'],task['second'])
            if not task.get('addtime_calculated'):
                task['addtime'] = self.get_addtime(task)
            task['backup_mode']=1 if task['backup_mode']=="1" else 0
            db_backup_path = public.M('config').where("id=?", ('1',)).getField('backup_path')
            task['db_backup_path']=task.get('db_backup_path') or db_backup_path
            task['rname'] = task.get('rname') or task['name']
            task['sort'] = 1 if str(task["id"]) in top_set else 0
            task['user'] = self.parse_user_from_sbody(task['sBody'])
            # 从sBody中移除sudo -u部分，只显示实际命令
            if task['sBody'] is not None and 'sudo -u' in task['sBody']:
                task['sBody'] = task['sBody'].split("bash -c '", 1)[-1].rstrip("'")
            self.get_mysql_increment_save(task)
            self.format_cycle(task)
            if not task['type_id']:
                task['type_id']=0
            task['type_name'] = self.get_type_name(task)  # 添加分类名称
            if len(task['params']) > 3: #确保{}不会被解析 前端会识别错误
                try:
                    task['params'] = json.loads(task['params'])
                    if 'user' in task['params']:
                        task['user'] = task['params']['user']
                except:
                    pass
    def get_mysql_increment_save(self,task):
        if task['sType']=="mysql_increment_backup":
            save = public.M("mysql_increment_backup").where("cron_id=?", (task['id'],)).count()
            if save>=0:
                task['save']=save
            else:
                save=""
    def get_log_path(self,get):
        id = get['id']
        echo = public.M('crontab').where("id=?", (id,)).getField('echo')
        if not echo:
            return public.returnMsg(False, "未找到对应计划任务的数据，请刷新页面查看该计划任务是否存在！")
        import math
        
        def convert_size(size_bytes):
            if size_bytes == 0:
                return "0B"
            size_name = ("B", "KB", "MB", "GB")
            i = int(math.floor(math.log(size_bytes, 1024)))
            p = math.pow(1024, i)
            s = round(size_bytes / p, 2)
            return "{} {}".format(s,size_name[i])
        
        cronPath = public.GetConfigValue('setup_path') + '/cron'
        log_path = cronPath + '/' + echo + '.log'
        if os.path.exists(log_path):
            size_bytes = os.path.getsize(log_path)
            size = convert_size(size_bytes)
        else:
            data={"log_path":"无","size":"0B"}
            return public.returnMsg(True, data)
        # return log_path, size
        data={"log_path":log_path,"size":size}
        return public.returnMsg(True, data)
    
    def _get_task_type_zh(self,task):
        if task['type'] == "day":
            return public.getMsg('CRONTAB_TODAY')
        elif task['type'] == "day-n":
            return public.getMsg('CRONTAB_N_TODAY', (str(task['where1']),))
        elif task['type'] == "hour":
            return public.getMsg('CRONTAB_HOUR')
        elif task['type'] == "hour-n":
            return public.getMsg('CRONTAB_N_HOUR', (str(task['where1']),))
        elif task['type'] == "minute-n":
            if task['second']:
                task['type'] ="second-n"
                return public.getMsg('CRONTAB_N_SECOND', (str(task['where1']),))
            return public.getMsg('CRONTAB_N_MINUTE', (str(task['where1']),))
        elif task['type'] == "week":
            task['type_zh'] = public.getMsg('CRONTAB_WEEK')
            if not task['where1']: task['where1'] = '0'
            return task['type_zh']
        elif task['type'] == "month":
            return public.getMsg('CRONTAB_MONTH')
    
    def get_addtime(self,task):
        log_file='/www/server/cron/{}.log'.format(task['echo'])
        if os.path.exists(log_file):
            return self.get_last_exec_time(log_file)
        else:
            return " "

    def search_tasks(self, data, search_term):
        return [
            item for item in data
            if search_term.lower() in item.get('rname', '').lower()
               or search_term.lower() in item['name'].lower()
               or search_term.lower() in item.get('sName', '').lower()
               or search_term.lower() in item.get('addtime', '').lower()
               or search_term.lower() in item.get('echo', '').lower()
               or search_term.lower() in item.get('sBody', '').lower()
        ]
    
    def generate_cycle(self, type, where1, where_hour, where_minute,sType,second:None):
        try:
            if where1:
                where1 = int(where1)
            cycle = ""
            week_days = ["一", "二", "三", "四", "五", "六", "日"]
            
            if type == "day":
                cycle = "每天的{:02d}:{:02d}执行一次".format(where_hour, where_minute)
            elif type == "day-n":
                cycle = "每隔{}天的{:02d}:{:02d}执行一次".format(where1, where_hour, where_minute)
            elif type == "hour":
                cycle = "每小时的第{}分钟执行一次".format(where_minute)
            elif type == "hour-n":
                # start_time = "{:02d}:{:02d}".format(where_hour, where_minute)
                # cycle = "从每天从00:00开始，每隔{}小时执行一次，直到1天结束（例如：{}".format(where1, start_time)
                cycle = "每天0点开始，每隔{}小时的第{}分钟执行一次".format(where1, where_minute)
            elif type == "minute-n":
                # start_time = "0，{}等分钟）".format(where_minute)
                # cycle = "每小时的第0分钟开始，每隔{}分钟执行一次，直到1小时结束（例如：{}".format(where_minute, start_time)
                cycle = "每小时的第0分钟开始，每隔{}分钟执行一次".format(where1)
                # current_minute = where_minute
            elif type == "week":
                cycle = "每周{}的{:02d}:{:02d}执行一次".format(week_days[where1-1], where_hour, where_minute)
            elif type == "month":
                cycle = "每月{}号的{:02d}:{:02d}执行一次".format(where1, where_hour, where_minute)
            elif type == "second-n":
                cycle = "每隔{}秒执行一次".format(second)
            if sType == "startup_services":
                cycle = "开机执行一次"
            return cycle
        except:
            # print(traceback.format_exc())
            pass
    
    def parse_user_from_sbody(self,sBody):
        if isinstance(sBody, str):
            # 使用正则表达式提取 sudo -u 后面的用户名
            match = re.search(r'^sudo\s+-u\s+(\S+)', sBody)
            return match.group(1) if match else 'root'
        else:
            return 'root'
    
    def format_cycle(self,item):
        week_str = ''
        if item['time_type'] in ['sweek', 'sday', 'smonth']:
            item['type'] = 'sweek'  # 对于这三种情况，类型都统一处理为 'sweek'
            if item['time_type'] == 'sweek':
                week_str = self.toweek(item['time_set'])  # 假设 self.toweek() 方法存在且能正常工作
            cycle_prefix = "每天" if item['time_type'] == 'sday' else "每月" + item['time_set'] + "号" if item['time_type'] == 'smonth' else "每" + week_str
            item['type_zh'] = item['special_time'] if item['time_type'] in ['sday', 'smonth'] else week_str
            item['cycle'] = cycle_prefix + item['special_time'] + "执行"
        elif item['sType'] == 'site_restart':
            item['cycle'] = "每天" + item['special_time'] + "执行"
    
    def toweek(self, days):
        week_days = {
            '1': '周一',
            '2': '周二',
            '3': '周三',
            '4': '周四',
            '5': '周五',
            '6': '周六',
            '7': '周日'
        }
        day_list = str(days).split(',')
        for day in day_list:
            if day not in week_days:
                print('Invalid day:', day)
                return ''
        return ','.join(week_days[day] for day in day_list)
    def _construct_result(self, db_obj, page_data, paged_data):
        if page_data:
            result =  {'page': page_data, 'data': paged_data}
            if db_obj.ERR_INFO:
                result['error']=db_obj.ERR_INFO
        else:
            result =paged_data
            if db_obj.ERR_INFO:
                return []
        return result
    def get_backup_list(self, args):
        '''
            @name 获取指定备份任务的备份文件列表
            @author hwliang
            @param args<dict> 参数{
                cron_id<int> 任务ID 必填
                p<int> 页码 默认1
                rows<int> 每页显示条数 默认10
                callback<string> jsonp回调函数  默认为空
            }
            @return <dict>{
                page<str> 分页HTML
                data<list> 数据列表
            }
        '''
        
        p = args.get('p/d', 1)
        rows = args.get('rows/d', 10)
        tojs = args.get('tojs/s', '')
        callback = args.get('callback/s', '') if tojs else tojs
        cron_id = args.get('cron_id/d')
        
        # 首先检查计划任务的类型
        crontab = public.M('crontab').where('id=?', (cron_id,)).select()
        if not crontab:
            return public.returnMsg(False, "未找到对应计划任务的数据，请刷新页面查看该计划任务是否存在！")
        if "数据库增量备份" in crontab[0]['name']:
            data = self.get_backup_data('mysql_increment_backup', cron_id, p, rows, callback)
        else:
            data = self.get_backup_data('backup', cron_id, p, rows, callback)
        
        return data
    
    def get_backup_data(self, table, cron_id, p, rows, callback):
        count = public.M(table).where('cron_id=?', (cron_id,)).count()
        data = public.get_page(count, p, rows, callback)
        data['data'] = public.M(table).where('cron_id=?', (cron_id,)).limit(data['row'], data['shift']).select()
        if table=="mysql_increment_backup":
            # 更新filename字段
            if data['data']:
                cloud_storage_fields = [
                    'localhost', 'ftp', 'alioss', 'txcos', 'qiniu',
                    'aws_s3', 'upyun', 'obs', 'bos', 'gcloud_storage',
                    'gdrive', 'msonedrive', 'jdcloud',"tianyiyun","webdav","minio","dogecloud"
                ]
                for i in data['data']:
                    for field in cloud_storage_fields:
                        if i[field]:
                            i['filename'] = i[field]
                            break
        return data
    
    def get_last_exec_time(self, log_file):
        '''
            @name 获取上次执行时间
            @author hwliang
            @param log_file<string> 日志文件路径
            @return format_date
        '''
        exec_date = ''
        # try:
        #     log_body = public.GetNumLines(log_file, 20)
        #     if log_body:
        #         log_arr = log_body.split('\n')
        #         date_list = []
        #         for i in log_arr:
        #             if i.find('★') != -1 and i.find('[') != -1 and i.find(']') != -1:
        #                 date_list.append(i)
        #         if date_list:
        #             exec_date = date_list[-1].split(']')[0].split('[')[1]
        # except:
        #     pass
        
        # finally:
        if not exec_date:
            exec_date = public.format_date(times=int(os.path.getmtime(log_file)))
        return exec_date
    
    
    # 清理日志
    def __clean_log(self):
        if cache.get('__clean_log'): return None
        
        try:
            log_file = '/www/server/cron'
            if not os.path.exists(log_file): return False
            for f in os.listdir(log_file):
                if f[-4:] != '.log': continue
                filename = log_file + '/' + f
                if os.path.getsize(filename) < 1024*1024*10: continue
                tmp = public.GetNumLines(filename, 100)
                public.writeFile(filename, tmp)
            cache.set('__clean_log', True, 3600)
        except:
            pass
    
    # 转换大写星期
    def toWeek(self, num):
        wheres = {
            0: public.getMsg('CRONTAB_SUNDAY'),
            1: public.getMsg('CRONTAB_MONDAY'),
            2: public.getMsg('CRONTAB_TUESDAY'),
            3: public.getMsg('CRONTAB_WEDNESDAY'),
            4: public.getMsg('CRONTAB_THURSDAY'),
            5: public.getMsg('CRONTAB_FRIDAY'),
            6: public.getMsg('CRONTAB_SATURDAY')
        }
        try:
            return wheres[num]
        except:
            return ''
    
    def check_crontab_service(self):
        # 检查缓存中是否有结果
        if cache.get('check_crontab_service'): return None
        
        # 调用检查脚本
        try:
            # result = subprocess.run(['python3', '/path/to/crontab_check.py'], capture_output=True, text=True)
            public.ExecShell('nohup btpython  /www/server/panel/script/crontab_check.py > /dev/null 2>&1 &')
            cache.set('check_crontab_service', True, 3600)
        except:
            pass
    
    def get_crontab_service(self,get):
        status=1
        try:
            status=int(public.readFile("/tmp/crontab_service_status.flag"))
        except:
            status=1
        if not os.path.exists("/tmp/crontab_service_status.flag"):
            status=1
        data={'status':status}
        return {"status":True,"msg":"","data":data}
    
    def repair_crontab_service(self, get):
        if '_ws' not in get:
            return False
        
        exec_result = public.ExecShell("nohup stdbuf -oL btpython /www/server/panel/script/crontab_repair.py > /tmp/repair_crontab.txt 2>&1 &")
        
        if exec_result:  # 假设ExecShell返回的第一个元素是成功与否的标志
            # 以只读模式打开日志文件，并移动到文件末尾
            if not os.path.exists("/tmp/repair_crontab.txt"):
                public.writeFile("/tmp/repair_crontab.txt","")
            
            with open("/tmp/repair_crontab.txt", "r") as log_file:
                while True:
                    line = log_file.readline()
                    if not line:
                        time.sleep(0.1)  # 如果没有新内容，则稍等片刻再尝试读取
                        continue
                    get._ws.send(public.getJson({
                        "callback":"repair_crontab_service",
                        "result":line.strip()
                        
                    }))
                    if line.strip() == "服务修复完成！":
                        break
            return True
        else:
            get._ws.send("脚本执行失败")
            return False
    
    
    # 检查环境
    def checkBackup(self):
        if cache.get('check_backup'): return None
        
        # 检查备份表是否正确
        if not public.M('sqlite_master').where('type=? AND name=? AND sql LIKE ?',
                                               ('table', 'backup', '%cron_id%')).count():
            public.M('backup').execute("ALTER TABLE 'backup' ADD 'cron_id' INTEGER DEFAULT 0", ())
        
        # 检查备份脚本是否存在
        filePath = public.GetConfigValue('setup_path') + '/panel/script/backup'
        if not os.path.exists(filePath):
            public.downloadFile(public.GetConfigValue('home') + '/linux/backup.sh', filePath)
        # 检查日志切割脚本是否存在
        filePath = public.GetConfigValue('setup_path') + '/panel/script/logsBackup'
        if not os.path.exists(filePath):
            public.downloadFile(public.GetConfigValue('home') + '/linux/logsBackup.py', filePath)
        # 检查计划任务服务状态
        import system
        sm = system.system()
        if os.path.exists('/etc/init.d/crond'):
            if not public.process_exists('crond'): public.ExecShell('/etc/init.d/crond start')
        elif os.path.exists('/etc/init.d/cron'):
            if not public.process_exists('cron'): public.ExecShell('/etc/init.d/cron start')
        elif os.path.exists('/usr/lib/systemd/system/crond.service'):
            if not public.process_exists('crond'): public.ExecShell('systemctl start crond')
        cache.set('check_backup', True, 3600)
    
    # 设置计划任务状态
    def set_cron_status(self, get):
        id = get['id']
        cronInfo = public.M('crontab').where('id=?', (id,)).field(self.field).find()
        if not cronInfo:
            return public.returnMsg(False, "未找到对应计划任务的数据，请刷新页面查看该计划任务是否存在！")
        status_msg = ['停用', '启用']
        status = 1
        if cronInfo['status'] == status:
            status = 0
            remove_res=self.remove_for_crond(cronInfo['echo'])
            if not remove_res['status']:
                return public.returnMsg(False, remove_res['msg'])
        else:
            cronInfo['status'] = 1
            sync_res=self.sync_to_crond(cronInfo)
            if not sync_res['status']:
                return public.returnMsg(False, sync_res['msg'])
        
        public.M('crontab').where('id=?', (id,)).setField('status', status)
        public.WriteLog('计划任务', '修改计划任务[' + cronInfo['name'] + ']状态为[' + status_msg[status] + ']')
        cronPath = '/www/server/cron'
        cronName = cronInfo['echo']
        if_stop = get.get('if_stop', '')
        if if_stop:
            self.stop_cron_task(cronPath, cronName, if_stop)
        return public.returnMsg(True, '设置成功')
    
    def set_cron_status_all(self, get):
        """
        批量设置计划任务状态
        :param get: type:stop, start, del, exec    id_list:[1,2,3]
        :return:
        """
        if not hasattr(get, 'type'):
            return public.returnMsg(False, '参数错误')
        if not hasattr(get, 'id_list'):
            return public.returnMsg(False, '参数错误')
        # 停止或开启
        if get.type not in ['stop', 'start', 'del', 'exec']:
            return public.returnMsg(False, '参数错误')
        if get.type == 'stop' or get.type == 'start':
            id_list = json.loads(get['id_list'])
            status = 1 if get.type == 'start' else 0
            status_msg = ['停止', '开启']
            data = []
            for id in id_list:
                try:
                    name = public.M('crontab').where('id=?', (id,)).field('name').find().get('name', '')
                    cronInfo = public.M('crontab').where('id=?', (id,)).field(self.field).find()
                    if not cronInfo:
                        data.append({id: '此id计划任务不存在', 'status': False})
                        continue
                    if status == 1:
                        sync_res=self.sync_to_crond(cronInfo)
                        if not sync_res['status']:
                            return public.returnMsg(False, sync_res['msg'])
                    else:
                        remove_res=self.remove_for_crond(cronInfo['echo'])
                        if not remove_res['status']:
                            return public.returnMsg(False, remove_res['msg'])
                    public.M('crontab').where('id=?', (id,)).setField('status', status)
                    cronPath = '/www/server/cron'
                    cronName = cronInfo['echo']
                    if_stop = get.if_stop
                    self.stop_cron_task(cronPath, cronName, if_stop)
                except:
                    data.append({name: "{}设置失败".format(status_msg[status]), 'status': False})
                else:
                    data.append({name: "{}设置成功".format(status_msg[status]), 'status': True})
            return data
        # 删除
        if get.type == 'del':
            id_list = json.loads(get['id_list'])
            data = []
            for id in id_list:
                try:
                    name = public.M('crontab').where('id=?', (id,)).field('name').find().get('name', '')
                    if not name:
                        data.append({id: '此id计划任务不存在', 'status': False})
                        continue
                    get = public.to_dict_obj({'id': id})
                    res = self.DelCrontab(get)
                except:
                    pass
                data.append({name: "删除{}".format("成功" if res['status'] else "失败"), 'status': res['status']})
            return data
        # 执行
        if get.type == 'exec':
            id_list = json.loads(get['id_list'])
            data = []
            for id in id_list:
                try:
                    name = public.M('crontab').where('id=?', (id,)).field('name').find().get('name', '')
                    if not name:
                        data.append({id: '此id计划任务不存在', 'status': False})
                        continue
                    get = public.to_dict_obj({'id': id})
                    res = self.StartTask(get)
                except:
                    pass
                data.append({name: "执行{}".format("成功" if res['status'] else "失败"), 'status': res['status']})
            return data
    
    # 修改计划任务
    def modify_crond(self, get):
        try:
            # if get['sType'] == 'startup_services':
            #     return self.ensure_execute_commands_script(get)  # 检查并创建脚本
            if get['name']=="[勿删]切割计划任务日志":
                return public.returnMsg(False, "此处不支持直接修改该条计划任务,请到日志切割处进行修改！")
            if "拔测" in get['name'] and "/www/server/panel/class/monitorModel/boceModel.py" in get['sBody']:
                if get['type']=="minute-n":
                    if int(get['where1'])<10:
                        return public.returnMsg(False, "拔测周期最短不能少于10分钟！")
                if get['type']=="second-n":
                    return public.returnMsg(False, "网站拔测任务不支持设置为秒级任务！")
            if re.search('<.*?>', get['name']):
                return public.returnMsg(False, "分类名称不能包含HTML语句")
            if get['sType'] == 'toShell':
                sBody = get['sBody']
                get['sBody'] = sBody.replace('\r\n', '\n')
                # 如果user有值，则修改sBody
                user = get.get('user', 'root')
                if user and user!='root':
                    get['sBody'] = "sudo -u {0} bash -c '{1}'".format(user, get['sBody'])
                if get.get('version',''):
                    version = get['version'].replace(".", "")
                    get['sBody'] = get['sBody'].replace("${1/./}", version)
            if len(get['name']) < 1:
                return public.returnMsg(False, 'CRONTAB_TASKNAME_EMPTY')
            id = get['id']
            cronInfo = public.M('crontab').where('id=?', (id,)).field(self.field).find()
            
            
            if get['type']=='sweek':
                self.modify_values(cronInfo['echo'],get['time_type'],get['special_time'],get['time_set'])
                get['type']='minute-n'
            
            if get['type']=="second-n":
                get['type']="minute-n"
                get['where1']= "1"
                get['hour']=1
                get['minute']=1
                get['flock']=0
            cuonConfig, get, name = self.GetCrondCycle(get)
            
            projectlog = self.modify_project_log_split(cronInfo, get)
            if projectlog.modify():
                return public.returnMsg(projectlog.flag, projectlog.msg)
            if not get['where1']: get['where1'] = get['week']
            del (cronInfo['id'])
            del (cronInfo['addtime'])
            cronInfo['name'] = get['name']
            if cronInfo['sType'] == "sync_time": cronInfo['sName'] = get['sName']
            cronInfo['type'] = get['type']
            cronInfo['where1'] = get['where1']
            cronInfo['where_hour'] = get['hour']
            cronInfo['where_minute'] = get['minute']
            cronInfo['save'] = get['save']
            cronInfo['backupTo'] = get['backupTo']
            cronInfo['sBody'] = get['sBody']
            cronInfo['urladdress'] = get['urladdress']
            cronInfo['time_type']=get.get('time_type','')
            cronInfo['special_time']=get.get('special_time','')
            cronInfo['time_set']=get.get('time_set','')
            cronInfo['second']=get.get('second','')
            cronInfo['log_cut_path']=get.get('log_cut_path','')
            cronInfo['user'] = get.get('user', 'root')
            cronInfo['flock'] = get.get('flock', 0)
            cronInfo['params'] = get.get('params', '{}')
            db_backup_path = public.M('config').where("id=?", ('1',)).getField('backup_path')
            if get.get('db_backup_path')==db_backup_path:
                db_backup_path=""
            else:
                db_backup_path=get.get('db_backup_path','')
            if cronInfo['status'] != 0:
                remove_res=self.remove_for_crond(cronInfo['echo'])
                if not remove_res['status']:
                    return public.returnMsg(False, remove_res['msg'])
                if cronInfo['status'] == 0: return public.returnMsg(False, '当前任务处于停止状态,请开启任务后再修改!')
                if get.get("post_param", ""):
                    cronInfo["post_param"] = get["post_param"]
                if get.get("user_agent", ""):
                    cronInfo["user_agent"] = get["user_agent"]
                sync_res=self.sync_to_crond(cronInfo)
                if not sync_res['status']:
                    return public.returnMsg(False, sync_res['msg'])
            columns = 'type,where1,where_hour,where_minute,save,backupTo,sName,sBody,urladdress,db_type,split_type,split_value,rname,post_param,flock,time_set,backup_mode,db_backup_path,time_type,special_time,log_cut_path,user_agent,version,table_list,second,stop_site,params'
            values = (get['type'], get['where1'], get['hour'],
                      get['minute'], get['save'], get['backupTo'], cronInfo['sName'], get['sBody']
                      , get['urladdress'], get.get("db_type"), get.get("split_type"), get.get("split_value"), get['name'], get.get('post_param', ''), get.get('flock', 0),get.get('time_set',''),get.get('backup_mode', ''),db_backup_path,get.get('time_type',''),get.get('special_time',''),get.get('log_cut_path',''),get.get('user_agent',''),get.get('version',''),get.get('table_list',''),get.get('second',''),get.get('stop_site',''),cronInfo['params'])
            if 'save_local' in get:
                columns += ",save_local, notice, notice_channel"
                values = (get['type'], get['where1'], get['hour'],
                          get['minute'], get['save'], get['backupTo'], cronInfo['sName'], get['sBody'],
                          get['urladdress'], get.get("db_type"), get.get("split_type"), get.get("split_value"), get['name'], get.get('post_param', ''), get.get('flock', 0),get.get('time_set',''),get.get('backup_mode', ''),db_backup_path,get.get('time_type',''),get.get('special_time',''),get.get('log_cut_path',''),get.get('user_agent',''),get.get('version',''),get.get('table_list',''),get.get('second',''),get.get('stop_site',''),cronInfo['params'],
                          get['save_local'], get["notice"],get["notice_channel"])
            public.M('crontab').where('id=?', (id,)).save(columns, values)
            public.WriteLog('计划任务', '修改计划任务[' + cronInfo['name'] + ']成功')
            return public.returnMsg(True, '修改成功')
        except:
            print(traceback.format_exc())
            return public.returnMsg(False,traceback.format_exc())
    
    # 获取指定任务数据
    def get_crond_find(self, get):
        id = int(get.id)
        data = public.M('crontab').where('id=?', (id,)).field(self.field).find()
        return data
    
    # 同步到crond
    def sync_to_crond(self, cronInfo):
        if not 'status' in cronInfo: return False
        if 'where_hour' in cronInfo:
            cronInfo['hour'] = cronInfo['where_hour']
            cronInfo['minute'] = cronInfo['where_minute']
            cronInfo['week'] = cronInfo['where1']
        cuonConfig, cronInfo, name = self.GetCrondCycle(cronInfo)
        cronPath = public.GetConfigValue('setup_path') + '/cron'
        cronName = self.GetShell(cronInfo)
        if type(cronName) == dict: return cronName

        cronJob = cronPath + '/' + cronName
        cronLog = cronJob + '.log'

        if int(cronInfo.get('flock', 0)) == 1:
            flock_name = cronJob + '.lock'
            public.writeFile(flock_name, '')
            os.system('chmod 777'.format(flock_name))
            # cuonConfig += ' flock -xn {flock_name} -c {cronJob}  >> {cronLog} 2>&1 || echo "上次任务正在执行中,本次跳过..." >> {cronLog}'.format(flock_name = flock_name,cronJob=cronJob,cronLog=cronLog)
            cuonConfig += ' flock -xn {flock_name} -c {cronJob}  >> {cronLog} 2>&1'.format(flock_name = flock_name,cronJob=cronJob,cronLog=cronLog)
        else:
            cuonConfig += ' {cronJob} >> {cronLog} 2>&1'.format(cronJob=cronJob, cronLog=cronLog)
        wRes = self.WriteShell(cuonConfig)
        if not wRes['status'] : return wRes
        self.CrondReload()
        return public.returnMsg(True, '迁移成功!')
    
    def ensure_execute_commands_script(self,get):
        cronName = public.md5(public.md5(str(time.time()) + '_bt'))
        script_path = '/etc/init.d/execute_commands'
        systemd_service_path = '/etc/systemd/system/execute_commands.service'
        
        # For systemd systems
        if os.path.exists('/bin/systemctl') or os.path.exists('/usr/bin/systemctl'):
            if not os.path.exists(systemd_service_path):
                with open(systemd_service_path, 'w') as service_file:
                    service_content = """[Unit]
    Description=Custom Service to execute commands at startup
    After=network.target

    [Service]
    Type=simple
    ExecStart=btpython /www/server/panel/script/execute_commands.py
    Restart=on-failure

    [Install]
    WantedBy=multi-user.target
    """
                    service_file.write(service_content)
                
                os.system('systemctl daemon-reload')
                os.system('systemctl start execute_commands.service')
                os.system('systemctl enable execute_commands.service')
                print("Systemd service created and enabled successfully.")
        
        # For SysVinit systems
        else:
            if not os.path.exists(script_path):
                with open(script_path, 'w') as script_file:
                    script_content = """#! /bin/sh
    # chkconfig: 2345 55 25

    ### BEGIN INIT INFO
    # Provides:          custom_service
    # Required-Start:    $all
    # Required-Stop:     $all
    # Default-Start:     2 3 4 5
    # Default-Stop:      0 1 6
    # Short-Description: Custom Service
    # Description:       Executes user-defined shell commands at startup
    ### END INIT INFO

    # Author:   Your Name
    # website:  Your Website

    PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

    case "$1" in
        start)
            echo -n "Starting custom_service... "
            if [ -f /var/run/custom_service.pid ];then
                mPID=$(cat /var/run/custom_service.pid)
                isStart=`ps ax | awk '{ print $1 }' | grep -e "^${mPID}$"`
                if [ "$isStart" != "" ];then
                    echo "custom_service (pid $mPID) already running."
                    exit 1
                fi
            fi
            nohup btpython /www/server/panel/script/execute_commands.py > /dev/null 2>&1 &
            pid=$!
            echo $pid > /var/run/custom_service.pid
            echo " done"
            ;;
        stop)
            echo "Custom Service does not support stop operation."
            ;;
        status)
            if [ -f /var/run/custom_service.pid ];then
                mPID=`cat /var/run/custom_service.pid`
                isStart=`ps ax | awk '{ print $1 }' | grep -e "^${mPID}$"`
                if [ "$isStart" != '' ];then
                    echo "custom_service is running with PID $mPID."
                    exit 0
                else
                    echo "custom_service is stopped"
                    exit 0
                fi
            else
                echo "custom_service is stopped"
                exit 0
            fi
            ;;
        *)
            echo "Usage: $0 {start|status}"
            exit 1
            ;;
    esac

    exit 0"""
                    script_file.write(script_content)
                    os.chmod(script_path, 0o755)  # Set execute permission
                print("Init script created successfully.")
                
                if os.path.exists('/usr/sbin/update-rc.d'):
                    os.system('update-rc.d -f execute_commands defaults')
                print("Service configured for SysVinit successfully.")
        
        db_backup_path = public.M('config').where("id=?", ('1',)).getField('backup_path')
        if get.get('db_backup_path') == db_backup_path:
            db_backup_path = ""
        else:
            db_backup_path = get.get('db_backup_path', '')
        columns = 'name,type,where1,where_hour,where_minute,echo,addtime,\
                status,save,backupTo,sType,sName,sBody,urladdress,db_type,split_type,split_value,keyword,post_param,flock,time_set,backup_mode,db_backup_path,time_type,special_time,user_agent,version,table_list'
        values = (public.xssencode2(get['name']), get['type'], get['where1'], get['hour'],
                  get['minute'], cronName, time.strftime('%Y-%m-%d %X', time.localtime()),
                  1, get['save'], get['backupTo'], get['sType'], get['sName'], get['sBody'],
                  get['urladdress'], get.get("db_type"), get.get("split_type"), get.get("split_value"), get.get('keyword', ''), get.get('post_param', ''), get.get('flock', 0), get.get('time_set', ''),
                  get.get('backup_mode', ''), db_backup_path, get.get('time_type', ''), get.get('special_time', ''), get.get('user_agent', ''), get.get('verison', ''), get.get('table_list', ''))
        if "save_local" in get:
            columns += ",save_local,notice,notice_channel"
            values = (public.xssencode2(get['name']), get['type'], get['where1'], get['hour'],
                      get['minute'], cronName, time.strftime('%Y-%m-%d %X', time.localtime()),
                      1, get['save'], get['backupTo'], get['sType'], get['sName'], get['sBody'],
                      get['urladdress'], get.get("db_type"), get.get("split_type"), get.get("split_value"), get.get('keyword', ''), get.get('post_param', ''), get.get('flock', 0),
                      get.get('time_set', ''), get.get('backup_mode', ''), db_backup_path, get.get('time_type', ''), get.get('special_time', ''), get.get('user_agent', ''), get.get('verison', ''),
                      get.get('table_list', ''),
                      get["save_local"], get['notice'], get['notice_channel'])
        addData = public.M('crontab').add(columns, values)
        public.add_security_logs('计划任务', '添加计划任务[' + get['name'] + ']成功' + str(values))
        if type(addData) == str:
            return public.returnMsg(False, addData)
        public.WriteLog('计划任务', '添加计划任务[' + get['name'] + ']成功')
        if addData > 0:
            result = public.returnMsg(True, 'ADD_SUCCESS')
            result['id'] = addData
            return result
        return public.returnMsg(False, 'ADD_ERROR')
    
    # 添加计划任务
    def AddCrontab(self, get):
        
        try:
            if "拔测" in get['name'] and "/www/server/panel/class/monitorModel/boceModel.py" in get['sBody']:
                if get['type']=="minute-n":
                    if int(get['where1'])<10:
                        return public.returnMsg(False, "拔测周期最短不能少于10分钟！")
                if get['type']=="second-n":
                    return public.returnMsg(False, "网站拔测任务不支持设置为秒级任务！")
            if get['name']=="[勿删]切割计划任务日志":
                if public.M('crontab').where("name=?", ('[勿删]切割计划任务日志',)).select():
                    return public.returnMsg(False, '该任务不支持直接复制！')
            if "网站增量备份" in get['name']:
                if public.M('crontab').where("name=?", (get['name'],)).select():
                    return public.returnMsg(False, '该任务不支持直接复制！')
            if get['type']=="second-n":
                get['type']="minute-n"
                get['where1']= "1"
                get['hour']=1
                get['minute']=1
                get['flock']=0
            if len(get['name']) < 1:
                return public.returnMsg(False, 'CRONTAB_TASKNAME_EMPTY')
            if get['sType'] == 'toShell':
                get['sBody'] = get['sBody'].replace('\r\n', '\n')
                # 如果user有值，则修改sBody
                user = get.get('user', 'root')
                if user and user!='root':
                    get['sBody'] = "sudo -u {0} bash -c '{1}'".format(user, get['sBody'])
                # 如果get中有version键，就替换sBody中的版本号占位符
                if get.get('version',''):
                    version = get['version'].replace(".", "")
                    get['sBody'] = get['sBody'].replace("${1/./}", version)
            if get['sType'] == 'startup_services':
                return self.ensure_execute_commands_script(get)  # 检查并创建脚本
            
            if get['type']=='sweek':
                get['type']='minute-n'
            cuonConfig, get, name = self.GetCrondCycle(get)
            cronPath = public.GetConfigValue('setup_path') + '/cron'
            cronName = self.GetShell(get)

            cronJob = cronPath + '/' + cronName
            cronLog = cronJob + '.log'

            if type(cronName) == dict: return cronName
            if int(get.get('flock', 0)) == 1:
                flock_name = cronJob + '.lock'
                public.writeFile(flock_name, '')
                os.system('chmod 777 {}'.format(flock_name))
                cuonConfig += ' flock -xn {flock_name} -c {cronJob}  >> {cronLog} 2>&1'.format(flock_name=flock_name, cronJob=cronJob, cronLog=cronLog)
            else:
                cuonConfig += ' {cronJob} >> {cronLog} 2>&1'.format(cronJob=cronJob, cronLog=cronLog)
            wRes = self.WriteShell(cuonConfig)
            if not wRes['status']: return wRes
            self.CrondReload()
            
            db_backup_path = public.M('config').where("id=?", ('1',)).getField('backup_path')
            if get.get('db_backup_path') == db_backup_path:
                db_backup_path=""
            else:
                db_backup_path=get.get('db_backup_path','')
            columns = 'name,type,where1,where_hour,where_minute,echo,addtime,status,save,backupTo,sType,sName,sBody,urladdress,db_type,split_type,split_value,keyword,post_param,flock,time_set,backup_mode,db_backup_path,time_type,special_time,log_cut_path,user_agent,version,table_list,result,second,stop_site,rname,params'
            values = (public.xssencode2(get['name']), get['type'], get['where1'], get['hour'],
                      get['minute'], cronName, time.strftime('%Y-%m-%d %X', time.localtime()),
                      1, get['save'], get['backupTo'], get['sType'], get['sName'], get['sBody'],
                      get['urladdress'], get.get("db_type"), get.get("split_type"), get.get("split_value"), get.get('keyword', ''), get.get('post_param', ''), get.get('flock', 0),get.get('time_set', ''),get.get('backup_mode',''),db_backup_path,get.get('time_type',''),get.get('special_time',''),get.get('log_cut_path',''),get.get('user_agent',''),get.get('verison',''),get.get('table_list',''),get.get('result',1),get.get('second',''),get.get('stop_site',''), get.get('rname',get['name']),get.get('params','{}'))
            if "save_local" in get:
                columns += ",save_local,notice,notice_channel"
                values = (public.xssencode2(get['name']), get['type'], get['where1'], get['hour'],
                          get['minute'], cronName, time.strftime('%Y-%m-%d %X', time.localtime()),
                          1, get['save'], get['backupTo'], get['sType'], get['sName'], get['sBody'],
                          get['urladdress'], get.get("db_type"), get.get("split_type"), get.get("split_value"), get.get('keyword', ''), get.get('post_param', ''), get.get('flock', 0),get.get('time_set', ''),get.get('backup_mode', ''),db_backup_path,get.get('time_type',''),get.get('special_time',''),get.get('log_cut_path',''),get.get('user_agent',''),get.get('verison',''),get.get('table_list',''),get.get('result',1),get.get('second',''),get.get('stop_site',''), get.get('rname',get['name']),get.get('params','{}'),
                          get["save_local"], get['notice'], get['notice_channel'])
            addData = public.M('crontab').add(columns, values)
            public.add_security_logs('计划任务', '添加计划任务[' + get['name'] + ']成功' + str(values))
            if type(addData) == str:
                return public.returnMsg(False, addData)
            public.WriteLog('计划任务', '添加计划任务[' + get['name'] + ']成功')
            if addData > 0:
                result = public.returnMsg(True, 'ADD_SUCCESS')
                result['id'] = addData
                return result
            return public.returnMsg(False, 'ADD_ERROR')
        except Exception as e:
            return public.returnMsg(False, str(e))
    
    # 构造周期
    def GetCrondCycle(self, params):
        cuonConfig = ""
        name = ""
        if params['type'] == "day":
            cuonConfig = self.GetDay(params)
            name = public.getMsg('CRONTAB_TODAY')
        elif params['type'] == "day-n":
            cuonConfig = self.GetDay_N(params)
            name = public.getMsg('CRONTAB_N_TODAY', (params['where1'],))
        elif params['type'] == "hour":
            cuonConfig = self.GetHour(params)
            name = public.getMsg('CRONTAB_HOUR')
        elif params['type'] == "hour-n":
            cuonConfig = self.GetHour_N(params)
            name = public.getMsg('CRONTAB_HOUR')
        elif params['type'] == "minute-n":
            cuonConfig = self.Minute_N(params)
        elif params['type'] == "week":
            params['where1'] = params['week']
            cuonConfig = self.Week(params)
        elif params['type'] == "month":
            cuonConfig = self.Month(params)
        return cuonConfig, params, name
    
    # 取任务构造Day
    def GetDay(self, param):
        cuonConfig = "{0} {1} * * * ".format(param['minute'], param['hour'])
        return cuonConfig
    
    # 取任务构造Day_n
    def GetDay_N(self, param):
        cuonConfig = "{0} {1} */{2} * * ".format(param['minute'], param['hour'], param['where1'])
        return cuonConfig
    
    # 取任务构造Hour
    def GetHour(self, param):
        cuonConfig = "{0} * * * * ".format(param['minute'])
        return cuonConfig
    
    # 取任务构造Hour-N
    def GetHour_N(self, param):
        cuonConfig = "{0} */{1} * * * ".format(param['minute'], param['where1'])
        return cuonConfig
    
    # 取任务构造Minute-N
    def Minute_N(self, param):
        cuonConfig = "*/{0} * * * * ".format(param['where1'])
        return cuonConfig
    
    # 取任务构造week
    def Week(self, param):
        cuonConfig = "{0} {1} * * {2}".format(param['minute'], param['hour'], param['week'])
        return cuonConfig
    
    # 取任务构造Month
    def Month(self, param):
        cuonConfig = "{0} {1} {2} * * ".format(param['minute'], param['hour'], param['where1'])
        return cuonConfig
    
    # 取数据列表
    def GetDataList(self, get):
        data = {}
        if get['type'] == 'databases':
            data['data'] = public.M(get['type']).where("type=?", "MySQL").field('name,ps').select()
        else:
            data['data'] = public.M(get['type']).field('name,ps').select()
        for i in data['data']:
            if 'ps' in i:
                try:
                    if i['ps'] is None: continue
                    i['ps'] = public.xsssec(i['ps'])  # 防止数据库为空时，xss防御报错  2020-11-25
                except:
                    pass
        data['orderOpt'] = []
        configured = []
        not_configured = []
        import json
        tmp = public.readFile('data/libList.conf')
        if not tmp: return data
        libs = json.loads(tmp)
        for lib in libs:
            if not 'opt' in lib: continue
            filename = 'plugin/{}'.format(lib['opt'])
            if not os.path.exists(filename):
                continue
            else:
                plugin_path = '/www/server/panel/plugin/{}/aes_status'.format(lib['opt'])
                status = 0  # 默认值为0，表示未配置
                if os.path.exists(plugin_path):
                    with open(plugin_path, 'r') as f:
                        status_content = f.read().strip()
                        if status_content.lower() == 'true':
                            status = 1  # 如果 aes_status 文件内容为 'True' 则设置为1
                if lib['opt']=="msonedrive":
                    status = 1
            tmp = {}
            tmp['name'] = lib['name']
            tmp['value'] = lib['opt']
            tmp['status'] =status
            if status == 1:
                configured.append(tmp)
            else:
                not_configured.append(tmp)
        
        # 先添加已配置的，再添加未配置的
        data['orderOpt'].extend(configured)
        data['orderOpt'].extend(not_configured)
        
        return data
    
    # 取任务日志
    def GetLogs(self, get):
        id = get['id']
        
        # 从数据库中查询任务类型
        sType = public.M('crontab').where("id=?", (id,)).getField('sType')
        # count=int(get.count) if hasattr(get,'count')else None
        start_timestamp = get.start_timestamp if hasattr(get,'start_timestamp') else None
        end_timestamp = get.end_timestamp if hasattr(get,'end_timestamp') else None
        if not start_timestamp and end_timestamp:
            # 如果任务类型是 'webshell'，处理特定类型的任务日志
            if sType == 'webshell':
                try:
                    logs = self.GetWebShellLogs(get)
                    return logs
                except Exception as e:
                    pass
        
        # 获取任务的 echo 字段
        echo = public.M('crontab').where("id=?", (id,)).field('echo').find()
        
        if not echo:
            return public.returnMsg(False, "未找到对应计划任务的数据，请刷新页面查看该计划任务是否存在！")
        
        # 构造日志文件路径
        logFile = public.GetConfigValue('setup_path') + '/cron/' + echo['echo'] + '.log'
        
        if not os.path.exists(logFile):
            return public.returnMsg(False, 'CRONTAB_TASKLOG_EMPTY')
        
        # 正则表达式匹配时间戳格式
        timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
        # 如果有时间戳，根据时间戳筛选日志内容
        if start_timestamp and end_timestamp:
            start_timestamp = float(start_timestamp)
            end_timestamp = float(end_timestamp)
            log = self.ReadLogsByTime(logFile, start_timestamp, end_timestamp)
            # filtered_logs = []
            # within_range = False
            # with open(logFile, 'r', encoding='utf-8', errors='ignore') as f:  # 使用 errors='ignore' 避免解码错误
            #     for line in f:
            
            #         # print(line)
            #         # 查找日志行中的时间戳
            #         match = timestamp_pattern.search(line)
            #         if match:
            #             log_time_str = match.group()
            #             log_time = time.strptime(log_time_str, '%Y-%m-%d %H:%M:%S')
            #             log_timestamp = time.mktime(log_time)
            #             if start_timestamp <= log_timestamp <= end_timestamp:
            #                 within_range = True
            #             else:
            #                 within_range = False
            
            #         if within_range:
            #             filtered_logs.append(line)
            
            # log = ''.join(filtered_logs)
        else:
            # 如果没有时间戳，读取最后 8196字节
            log = self.ReadLastBytesByChunks(logFile, 8196)
        
        return public.returnMsg(True, public.xsssec2(log))
    def ReadLogsByTime(self, path, start_timestamp, end_timestamp):
        """
        按时间范围读取日志，确保起始行前包含完整的 `Successful` 块。
        """
        if not os.path.exists(path):
            return ""
        
        timestamp_pattern = re.compile(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}')
        filtered_logs = []
        extra_logs = []  # 用于保存补充读取的内容
        
        try:
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                within_range = False
                all_lines = f.readlines()  # 读取所有行
            
            # 正向遍历所有行，查找符合时间范围的日志
            for index, line in enumerate(all_lines):
                match = timestamp_pattern.search(line)
                if match:
                    log_time_str = match.group()
                    log_time = time.strptime(log_time_str, '%Y-%m-%d %H:%M:%S')
                    log_timestamp = time.mktime(log_time)
                    
                    # 检查时间范围
                    within_range = start_timestamp <= log_timestamp <= end_timestamp
                
                if within_range:
                    filtered_logs.append(line)
            
            # 检查起始行前一行是否包含 `Successful`
            if filtered_logs:
                first_line_index = all_lines.index(filtered_logs[0])
                while first_line_index > 0:
                    first_line_index -= 1
                    previous_line = all_lines[first_line_index]
                    filtered_logs.insert(0, previous_line)
                    if "Successful" in previous_line:
                        break
            
            return ''.join(filtered_logs)
        
        except Exception as e:
            return "日志读取失败: {}".format(e)
    
    def ReadLastBytesByChunks(self, path, buffer_size=8196):
        """
        按字节读取日志文件的最后 buffer_size 字节内容
        :param path: 日志文件路径
        :param buffer_size: 每次读取的字节数，默认为 8196
        :return: 日志的最后 buffer_size 字节内容
        """
        if not os.path.exists(path):
            return ""
        
        try:
            # 打开文件进行按字节读取
            with open(path, 'rb') as f:
                f.seek(0, os.SEEK_END)  # 移动到文件末尾
                file_size = f.tell()    # 获取文件大小
                remaining_bytes = min(buffer_size, file_size)  # 确保不读取超过文件大小的字节数
                
                # 移动文件指针，读取最后 buffer_size 字节
                f.seek(file_size - remaining_bytes, os.SEEK_SET)
                buffer = f.read(remaining_bytes)
                
                # 将读取的字节转为字符串，并返回
                return buffer.decode('utf-8', errors='ignore')
        
        except Exception as e:
            return ""
    
    # 清理任务日志
    def DelLogs(self, get):
        try:
            id = get['id']
            echo = public.M('crontab').where("id=?", (id,)).getField('echo')
            logFile = public.GetConfigValue('setup_path') + '/cron/' + echo + '.log'
            # os.remove(logFile)
            public.writeFile(logFile,"")
            return public.returnMsg(True, 'CRONTAB_TASKLOG_CLOSE')
        except:
            return public.returnMsg(False, 'CRONTAB_TASKLOG_CLOSE_ERR')
    
    # 删除计划任务
    def DelCrontab(self, get):
        try:
            id = get['id']
            # 尝试删除数据库备份表中的数据
            
            public.M("mysql_increment_settings").where("cron_id=?", (id)).delete()
            find = public.M('crontab').where("id=?", (id,)).field('name,echo').find()
            if not find: return public.returnMsg(False, '指定任务不存在!')
            if not self.remove_for_crond(find['echo'])['status']: return public.returnMsg(False, self.remove_for_crond(find['echo'])['msg'])
            cronPath = public.GetConfigValue('setup_path') + '/cron/' + find['echo']
            public.ExecShell("rm -rf {cronPath}*".format(cronPath=cronPath))
            
            public.M('crontab').where("id=?", (id,)).delete()
            public.add_security_logs("删除计划任务", "删除计划任务:" + find['name'])
            public.WriteLog('TYPE_CRON', 'CRONTAB_DEL', (find['name'],))
            return public.returnMsg(True, 'DEL_SUCCESS')
        except:
            return public.returnMsg(False, 'DEL_ERROR')
    
    # 从crond删除
    def remove_for_crond(self, echo):
        try:
            
            # if not self.is_cron_installed():
            #     print(3333333333)
            #     return public.returnMsg(False, '检测到cron服务异常，请先修复cron服务！')
            file = self.get_cron_file()
            if not os.path.exists(file):
                return self.check_cron_file_status(file)
            conf = public.readFile(file)
            if not conf:
                return self.check_cron_file_status(file)
            if conf.find(str(echo)) == -1: return public.returnMsg(True, '文件写入成功')
            rep = ".+" + str(echo) + ".+\n"
            conf = re.sub(rep, "", conf)
            try:
                if not public.writeFile(file, conf):
                    return self.check_cron_file_status(file)
            except Exception as e:
                print(e)
                return self.check_cron_file_status(file)
            self.CrondReload()
            return public.returnMsg(True, '文件写入成功')
        except Exception as e:
            print(e)
    
    # 取执行脚本
    def GetShell(self, param):
        type = param['sType']
        if not 'echo' in param:
            cronName = public.md5(public.md5(str(time.time()) + '_bt'))
        else:
            cronName = param['echo']

        cronPath = public.GetConfigValue('setup_path') + '/cron'
        cronjobPath = '{cronPath}/{cronName}'.format(cronPath=cronPath,cronName=cronName)
        cronFile = '{cronjobPath}.pl'.format(cronjobPath=cronjobPath)
        logname='{cronjobPath}.log'.format(cronjobPath=cronjobPath)
        if type == 'toFile':
            shell = param.sFile
        else:
            head = "#!/bin/bash\nPATH=/bin:/sbin:/usr/bin:/usr/sbin:/usr/local/bin:/usr/local/sbin:~/bin\nexport PATH\n"
            head += "echo $$ > " + cronFile + "\n"  # 将PID保存到文件中
            
            second = param.get('second', "")
            time_type=param['type']
            if second:
                time_type="second-n"
                head += 'if [[ $1 != "start" ]]; then\n'
                head += ' btpython /www/server/panel/script/second_task.py {} {} \n'.format(second,cronName)
                head += ' exit 0\n'
                head += 'fi\n'
            public.ExecShell("chmod +x /www/server/panel/script/modify_second_cron.sh")
            public.ExecShell("nohup /www/server/panel/script/modify_second_cron.sh {} {} {} &".format(time_type,second,cronName) )
            
            time_type = param.get('time_type', '')
            if time_type:
                time_list=param.get('time_set', '')
                special_time=param.get('special_time', '')
                # if time_type == "sweek":
                # 调用 Python 脚本进行时间检查
                head += 'if [[ $1 != "start" ]]; then\n'
                head += ' if ! btpython /www/server/panel/script/time_check.py time_type={} special_time={} time_list={}; then\n'.format(time_type, ",".join(special_time.split(",")), ",".join(time_list.split(",")))
                head += '   exit 1\n'
                head += ' fi\n'
                head += 'fi\n'
            if param['sType']=="site_restart":
                special_time=param.get('special_time', '')
                # 调用 Python 脚本进行时间检查
                head +='force_start=""\n'
                head +='if [[ $1 == "start" ]]; then\n'
                head +=' force_start="start"\n'
                head +='fi\n'
                head += 'if [[ $1 != "start" ]]; then\n'
                head += ' if ! btpython /www/server/panel/script/special_time.py special_time={} ; then\n'.format(",".join(special_time.split(",")))
                head += '   exit 1\n'
                head += ' fi\n'
                head += 'fi\n'
            log = '-access_log'
            python_bin = "{} -u".format(public.get_python_bin())
            if public.get_webserver() == 'nginx':
                log = '.log'
            if type in ['site', 'path'] and param['sBody'] != 'undefined' and len(param['sBody']) > 1:
                exclude_files = ','.join([n.strip() for n in param['sBody'].split('\n') if n.strip()])
                head += f'export BT_EXCLUDE="{exclude_files}"\n'
            attach_param = " " + cronName
            log_cut_path = param['log_cut_path'] if hasattr(param,'log_cut_path') else '/www/wwwlogs/'
            if 'log_cut_path' in param:
                log_cut_path = param['log_cut_path']
            special_time= param['special_time'] if hasattr(param,'special_time') else ''
            if 'special_time' in param:
                special_time = param['special_time']

            setup_path = public.GetConfigValue('setup_path')
            wheres = {
                'path':                     head + "{python_bin} {setup_path}/panel/script/backup.py path {sName} {save}{attach_param}".format(python_bin=python_bin,setup_path=setup_path, sName=param['sName'], save=str(param['save']), attach_param=attach_param),
                'site':                     head + "{python_bin} {setup_path}/panel/script/backup.py site {sName} {save}{attach_param}".format(python_bin=python_bin, setup_path=setup_path, sName=param['sName'], save=str(param['save']), attach_param=attach_param),
                'database':                 head + "{python_bin} {setup_path}/panel/script/backup.py database {sName} {save}{attach_param}".format(python_bin=python_bin, setup_path=setup_path, sName=param['sName'], save=str(param['save']), attach_param=attach_param),
                'logs':                     head + "{python_bin} {setup_path}/panel/script/logsBackup {sName} {save} {log_cut_path}".format(python_bin=python_bin, setup_path=setup_path, sName=param['sName'], save=str(param['save']), log_cut_path=log_cut_path),
                'rememory':                 head + "/bin/bash {setup_path}/panel/script/rememory.sh".format(setup_path=setup_path),
                'sync_time':                head + "{python_bin} {setup_path}/panel/script/sync_time.py {sName}".format(python_bin=python_bin, setup_path=setup_path, sName=param['sName']),
                'webshell':                 head + "{python_bin} {setup_path}/panel/class/webshell_check.py site {sName} {urladdress}".format(python_bin=python_bin, setup_path=setup_path, sName=param['sName'], urladdress=param['urladdress']),
                'mysql_increment_backup':   head + "{python_bin} {setup_path}/panel/script/loader_binlog.py --echo_id={cronName}".format(python_bin=python_bin, setup_path=setup_path, cronName=cronName),
                'special_log':              head + "{python_bin} {setup_path}/panel/script/rotate_log_special.py {save} {sName}".format(python_bin=python_bin, setup_path=setup_path, save=str(param['save']), sName=param['sName']),
                'site_restart':             head + "{python_bin} {setup_path}/panel/script/move_config.py {sName} {special_time} $force_start".format(python_bin=python_bin, setup_path=setup_path, sName=param['sName'], special_time=special_time),
                'log_cleanup':              head + "{python_bin} {setup_path}/panel/script/log_cleanup.py all {sName} {log_cut_path}".format(python_bin=python_bin, setup_path=setup_path, sName=param['sName'], log_cut_path=log_cut_path),
            }
            try:
                shell = wheres[type]

            except:
                if type=="site_restart":
                    lines = shell.split('\n')
                    last_line = lines[-1]
                    new_command = '''

if [[ $1 == "start" ]]; then
        {} start
else
        {}
        
fi
'''.format(last_line, last_line)
                    
                    shell = shell.replace(last_line, new_command)
                # 设置 User-Agent 头
                if hasattr(param, 'user_agent'):
                    user_agent_value = getattr(param, 'user_agent', '')
                elif isinstance(param, dict) and 'user_agent' in param:
                    user_agent_value = param.get('user_agent', '')
                else:
                    user_agent_value = ''
                
                user_agent = "-H 'User-Agent: {}'".format(user_agent_value) if user_agent_value else ''
                
                if type == 'toUrl':
                    # shell = head + "curl -sS --connect-timeout 10 -m 3600 '" + param['urladdress'] + "'"
                    shell = head + "curl -sS -L {} --connect-timeout 10 -m 3600 '{}'".format(user_agent, param['urladdress'])
                elif type == 'to_post':
                    param1 = {}
                    for i in json.loads(param['post_param']):
                        param1[i['paramName']] = i['paramValue']
                    # shell = head + '''curl -sS -X POST --connect-timeout 10 -m 3600 -H "Content-Type: application/json"  -d '{}' {} '''.format(json.dumps(param1),
                    #                                                                                                                            param['urladdress'])
                    public.print_log(param1)
                    shell = head + '''curl -sS -L -X POST {} --connect-timeout 10 -m 3600 -H "Content-Type: application/json"  -d '{}' {} '''.format(user_agent, json.dumps(param1), param['urladdress'])
                elif type == 'toPython':
                    job_params = json.loads(param.get('params','{}'))
                    python_env = job_params.get('python_env', 'python3')
                    python_param = param['version'] #脚本中有参数的会被放到version中传递

                    script_path = "{cronjobPath}.py".format(cronjobPath = cronjobPath)
                    public.writeFile(script_path, param['sBody'].replace("\r\n", "\n"))
                    public.ExecShell('chmod o+x {cronPath};chmod 777 {script_path}'.format(cronPath=cronPath,script_path=script_path))

                    command = "{python_bin} {script_path} {python_param}".format(python_bin=python_env, script_path=script_path,python_param=python_param)

                    exec_user = param.get('user', 'root')
                    if exec_user != 'root':
                        command = '''
                        sudo -u {exec_user} `cat <<EOF 
                        {command}
                        EOF`
                        '''.format(exec_user=exec_user,command=command)
                        import textwrap
                        command = textwrap.dedent(command)
                        # 保存执行用户
                        job_params['user'] = exec_user
                        param['params'] = json.dumps(job_params)

                    shell = head + command
                else:
                    #toShell
                    shell = head + param['sBody'].replace("\r\n", "\n")
            shell += f'''
echo "----------------------------------------------------------------------------"
endDate=`date +"%Y-%m-%d %H:%M:%S"`
echo "★[$endDate] Successful"
echo "----------------------------------------------------------------------------"
if [[ "$1" != "start" ]]; then
    btpython /www/server/panel/script/log_task_analyzer.py {logname}
fi
rm -f {cronFile}
'''
        if type == 'toShell' and param.get('notice') and param['notice_channel'] and param['notice_channel'] and len(param.get('keyword', '')):
            shell += "btpython /www/server/panel/script/shell_push.py {} {} {} {} &".format(cronName, param['notice_channel'], param['keyword'], param['name'])

        if not os.path.exists(cronPath): public.ExecShell('mkdir -p {cronPath};chmod o+x {cronPath}'.format(cronPath=cronPath) )
        public.writeFile(cronjobPath, self.CheckScript(shell))
        public.ExecShell('chmod 750 ' + cronjobPath)
        return cronName
        # except Exception as ex:
        # return public.returnMsg(False, 'FILE_WRITE_ERR' + str(ex))


    
    # 检查脚本
    def CheckScript(self, shell):
        keys = ['shutdown', 'init 0', 'mkfs', 'passwd', 'chpasswd', '--stdin', 'mkfs.ext', 'mke2fs']
        for key in keys:
            shell = shell.replace(key, '[***]')
        return shell
    
    # 重载配置
    def CrondReload(self):
        if os.path.exists('/etc/init.d/crond'):
            public.ExecShell('/etc/init.d/crond reload')
        elif os.path.exists('/etc/init.d/cron'):
            public.ExecShell('service cron restart')
        else:
            public.ExecShell("systemctl reload crond")
    
    def is_cron_hardened(self,safe_status):
        """
        判断系统是否启用了对 cron 的加固功能。

        参数:
        safe_status (dict): 安全状态信息，来自 get_safe_status() 函数的返回结果

        返回:
        bool: 如果 cron 加固开启，返回 True，否则返回 False
        """
        
        if not safe_status.get('open', False):
            return False  # 如果整体的加固功能关闭，直接返回 False
        # 遍历返回的加固项目列表
        for item in safe_status.get('list', []):
            if item.get('key') == 'cron':
                return item.get('open', False)  # 如果找到了 cron 相关的加固项，返回其状态
        
        return False  # 如果没有找到 cron 相关的加固项，默认返回 False
    
    def check_cron_file_status(self,file):
        
        
        import PluginLoader
        # 检查cron服务是否安装
        
        if os.path.exists("/etc/init.d/bt_syssafe"):
            # syssafe_main().get_safe_status(None)
            safe_status = PluginLoader.plugin_run("syssafe", "get_safe_status", "")
            # 检查 cron 是否加固
            if self.is_cron_hardened(safe_status):
                return public.returnMsg(False, '文件写入失败,请检查是否开启系统加固功能!')
        
        
        # 检查文件是否被加锁
        result = public.ExecShell("lsattr {}".format(file))
        if 'i' in result[0]:
            return public.returnMsg(False, '{} 文件被加锁。请检查是否用了其他云锁产品，您可以使用命令 `chattr -i {}` 解锁！'.format(file, file))
        
        return public.returnMsg(True, "文件正常")
    
    
    # 将Shell脚本写到文件
    def WriteShell(self, config):
        # if not self.is_cron_installed():
        #     print(3333333333)
        #     return public.returnMsg(False, '检测到cron服务异常，请先修复cron服务！')
        u_file = '/var/spool/cron/crontabs/root'
        file = self.get_cron_file()
        if not os.path.exists(file):
            if not public.writeFile(file, ''):
                return self.check_cron_file_status(file)
        
        conf = public.readFile(file)
        if type(conf) == bool: return public.returnMsg(False, '读取文件失败!')

        # 在配置文件开头添加规定utf-8
        if not any(line.startswith(('LANG=', 'LC_ALL=')) for line in conf.split('\n')):
            conf = "LANG=en_US.UTF-8\nLC_ALL=en_US.UTF-8\n" + conf

        conf += config + "\n"
        if public.writeFile(file, conf):
            if not os.path.exists(u_file):
                public.ExecShell("chmod 600 '" + file + "' && chown root.root " + file)
            else:
                public.ExecShell("chmod 600 '" + file + "' && chown root.crontab " + file)
            return public.returnMsg(True, '文件写入成功')
        return self.check_cron_file_status(file)
    
    def is_cron_installed(self):
        import os
        
        # 检查是否存在 yum 或 dnf（适用于 CentOS、RHEL、Fedora）
        if os.path.exists("/bin/yum") or os.path.exists("/bin/dnf"):
            # 使用 rpm 检查 cronie 是否已安装
            result = public.ExecShell("rpm -q cronie")
            if "not installed" in result[0]:
                return False
            
            # 进一步检查 cron 服务是否正在运行
            service_status = public.ExecShell("systemctl is-active crond")
            return "active" in service_status[0]
        
        # 检查是否存在 apt（适用于 Debian 和 Ubuntu）
        elif os.path.exists("/usr/bin/apt"):
            # 使用 dpkg 检查 cron 是否安装（只检查是否为ii状态）
            result = public.ExecShell("dpkg -l | grep cron")
            if "ii" not in result[0]:
                return False
            
            # 进一步检查 cron 服务是否正在运行
            service_status = public.ExecShell("systemctl is-active cron")
            return "a1ctive" in service_status[0]
        
        else:
            # 对于其他系统返回不支持的提示
            return False
    
    
    # 立即执行任务
    def StartTask(self, get):
        echo = public.M('crontab').where('id=?', (get.id,)).getField('echo')
        if not echo:
            return public.returnMsg(False, "未找到对应计划任务的数据，请刷新页面查看该计划任务是否存在！")
        execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
        public.ExecShell('chmod +x ' + execstr)
        public.ExecShell('nohup ' + execstr +' start >> ' + execstr + '.log 2>&1 &')
        return public.returnMsg(True, 'CRONTAB_TASK_EXEC')
    
    # 获取计划任务文件位置
    def get_cron_file(self):
        u_path = '/var/spool/cron/crontabs'
        u_file = u_path + '/root'
        c_file = '/var/spool/cron/root'
        cron_path = c_file
        if not os.path.exists(u_path):
            cron_path = c_file
        
        if os.path.exists("/usr/bin/apt-get"):
            cron_path = u_file
        elif os.path.exists('/usr/bin/yum'):
            cron_path = c_file
        
        if cron_path == u_file:
            if not os.path.exists(u_path):
                os.makedirs(u_path, 472)
                public.ExecShell("chown root:crontab {}".format(u_path))
        if not os.path.exists(cron_path):
            public.writeFile(cron_path, "")
        return cron_path
    
    def modify_project_log_split(self, cronInfo, get):
        
        def _test_project_type(self, project_type):
            if project_type == "Node项目":
                return "nodojsModel"
            elif project_type == "Java项目":
                return "javaModel"
            elif project_type == "GO项目":
                return "goModel"
            elif project_type == "其他项目":
                return "otherModel"
            elif project_type == "Python项目":
                return "pythonModel"
            else:
                return None
        
        def the_init(self, cronInfo, get: dict):
            self.get = get
            self.cronInfo = cronInfo
            self.msg = ""
            self.flag = False
            name = get["name"]
            if name.find("运行日志切割") != -1:
                try:
                    project_type, project_name = name.split("]", 2)[1].split("[", 1)
                    project_type = self._test_project_type(project_type)
                except:
                    self.project_type = None
                    return
            else:
                self.project_type = None
                return
            
            self.project_type = project_type
            self.project_name = project_name
            conf_path = '{}/data/run_log_split.conf'.format(public.get_panel_path())
            data = json.loads(public.readFile(conf_path))
            self.log_size = int(data[self.project_name]["log_size"]) / 1024 / 1024
        
        def modify(self):
            from importlib import import_module
            if not self.project_type:
                return False
            if self.cronInfo["type"] != self.get['type']:
                self.msg = "运行日志切割不能修改执行周期的方式"
                return True
            get = public.dict_obj()
            get.name = self.project_name
            get.log_size = self.log_size
            if get.log_size != 0:
                get.hour = "2"
                get.minute = str(self.get['where1'])
            else:
                get.hour = str(self.get['hour'])
                get.minute = str(self.get['minute'])
            get.num = str(self.get["save"])
            
            model = import_module(".{}".format(self.project_type), package="projectModel")
            
            res = getattr(model.main(), "mamger_log_split")(get)
            self.msg = res["msg"]
            self.flag = res["status"]
            
            return True
        
        attr = {
            "__init__": the_init,
            "_test_project_type": _test_project_type,
            "modify": modify,
        }
        return type("ProjectLog", (object,), attr)(cronInfo, get)
    
    # 检查指定的url是否通
    def check_url_connecte(self, get):
        if 'url' not in get or not get['url']:
            return public.returnMsg(False, '请传入url!')
        
        try:
            start_time = time.time()
            response = requests.get(get['url'], timeout=30)
            response.encoding = 'utf-8'
            end_time = time.time()
            
            response_time = "{}ms".format(int(round(end_time - start_time, 2) * 1000))
            result = {'status': response.status_code == 200,
                      'status_code': response.status_code,
                      'txt': public.xsssec(response.text),
                      'time': response_time}
            return result
        
        except requests.exceptions.Timeout as err:
            end_time = time.time()
            response_time = "{}ms".format(int(round(end_time - start_time, 2) * 1000))
            return {'status': False, 'status_code': '', 'txt': '请求超时: {}'.format(err), 'time': response_time}
        except requests.exceptions.ConnectionError as err:
            end_time = time.time()
            response_time = "{}ms".format(int(round(end_time - start_time, 2) * 1000))
            return {'status': False, 'status_code': '', 'txt': '连接错误: {}'.format(err), 'time': response_time}
        except requests.exceptions.HTTPError as err:
            end_time = time.time()
            response_time = "{}ms".format(int(round(end_time - start_time, 2) * 1000))
            return {'status': False, 'status_code': err.response.status_code, 'txt': 'HTTP错误: {}'.format(err), 'time': response_time}
        except requests.exceptions.RequestException as err:
            end_time = time.time()
            response_time = "{}ms".format(int(round(end_time - start_time, 2) * 1000))
            return {'status': False, 'status_code': '', 'txt': '请求异常: {}'.format(err), 'time': response_time}
    
    # 获取各个类型数据库
    def GetDatabases(self, get):
        from panelMysql import panelMysql
        db_type = getattr(get, "db_type", "mysql")
        
        crontab_databases = public.M("crontab").field("id,sName").where("LOWER(type)=LOWER(?)", (db_type)).select()
        for db in crontab_databases:
            db["sName"] = set(db["sName"].split(","))
            # table_list = panelMysql().query("show tables from `{db_name}`;".format(db_name=database["name"]))
        
        if db_type == "redis":
            database_list = []
            cron_id = None
            for db in crontab_databases:
                if db_type in db["sName"]:
                    cron_id = db["id"]
                    break
            database_list.append({"name": "本地数据库", "ps": "", "cron_id": cron_id})
            return database_list
        
        databases = public.M("databases").field("name,ps").where("LOWER(type)=LOWER(?)", (db_type)).select()
        
        for database in databases:
            try:
                if database.get("name") is None: continue
                table_list = panelMysql().query("show tables from `{db_name}`;".format(db_name=database["name"]))
                if not isinstance(table_list, list):
                    continue
                cron_id = public.M("mysql_increment_settings").where("tb_name == ''", ()).getField("cron_id")
                database["table_list"] = [{"tb_name": "所有", "value": "", "cron_id": cron_id if cron_id else None}]
                for tb_name in table_list:
                    cron_id = public.M("mysql_increment_settings").where("tb_name in (?)", (tb_name[0])).getField("cron_id")
                    database["table_list"].append({"tb_name": tb_name[0], "value": tb_name[0], "cron_id": cron_id if cron_id else None})
                
                database["cron_id"] = []
                for db in crontab_databases:
                    if database["name"] in db["sName"]:
                        database["cron_id"].append(db["id"])
            except Exception as e:
                print(e)
        return databases
    
    # 取任务日志
    def GetWebShellLogs(self, get):
        id = get['id']
        echo = public.M('crontab').where("id=?", (id,)).field('echo').find()
        logFile = public.GetConfigValue('setup_path') + '/cron/' + echo['echo'] + '.log'
        if not os.path.exists(logFile): return public.returnMsg(False, 'CRONTAB_TASKLOG_EMPTY')
        logs = self.ReadLastBytesByChunks(logFile, 8196)  # 读取最后 8196字节
        logs = public.xsssec(logs)
        logs = logs.split('\n')
        if hasattr(get, 'time_search') and get.time_search != '' and get.time_search != '[]':
            time_logs = []
            time_search = json.loads(get.time_search)
            start_time = int(time_search[0])
            end_time = int(time_search[1])
            for i in range(len(logs) - 1, -1, -1):
                infos = re.findall(r'【(.+?)】', logs[i])
                try:
                    infos_time = time.strptime(infos[0], "%Y-%m-%d %H:%M:%S")
                    infos_time = time.mktime(infos_time)
                    if infos_time > start_time and infos_time < end_time:
                        time_logs.append(logs[i])
                except:
                    pass
            time_logs.reverse()
            logs = time_logs
        
        if hasattr(get, 'type') and get.type != '':
            if get.type == 'warring':
                warring_logs = []
                for i in range(len(logs)):
                    if '【warring】' in logs[i]:
                        warring_logs.append(logs[i])
                logs = warring_logs
        
        for i in range(len(logs)):
            if '【warring】' in logs[i]:
                logs[i] = '<span style="background-color:rgba(239, 8, 8, 0.8)">{}</span>'.format(logs[i])
        logs = '\n'.join(logs)
        if logs:
            return public.returnMsg(True, logs)
        else:
            return public.returnMsg(False, 'CRONTAB_TASKLOG_EMPTY')
    
    def download_logs(self, get):
        try:
            id = int(get['id'])
            echo = public.M('crontab').where("id=?", (id,)).field('echo').find()
            logFile = public.GetConfigValue('setup_path') + '/cron/' + echo['echo'] + '.log'
            if not os.path.exists(logFile): public.writeFile(logFile, "")
            logs = public.readFile(logFile)
            logs = logs.split('\n')
            if hasattr(get, 'day') and get.day != '':
                day = int(get.day)
                time_logs = []
                end_time = int(time.time())
                start_time = end_time - day * 86400
                for i in range(len(logs), 0, -1):
                    try:
                        infos = re.findall(r'【(.+?)】', logs[i])
                        infos_time = time.strptime(infos[0], "%Y-%m-%d %H:%M:%S")
                        infos_time = time.mktime(infos_time)
                        if infos_time > start_time and infos_time < end_time:
                            time_logs.append(logs[i])
                        if infos_time < start_time:
                            break
                    except:
                        pass
                time_logs.reverse()
                logs = time_logs
            if hasattr(get, 'type') and get.type != '':
                if get.type == 'warring':
                    warring_logs = []
                    for i in range(len(logs)):
                        if '【warring】' in logs[i]:
                            warring_logs.append(logs[i])
                    logs = warring_logs
            logs = '\n'.join(logs)
            public.writeFile('/tmp/{}.log'.format(echo['echo']), logs)
            return public.returnMsg(True, '/tmp/{}.log'.format(echo['echo']))
        except:
            return public.returnMsg(False, '下载失败！')
    
    def clear_logs(self, get):
        try:
            id = int(get['id'])
            echo = public.M('crontab').where("id=?", (id,)).field('echo').find()
            logFile = public.GetConfigValue('setup_path') + '/cron/' + echo['echo'] + '.log'
            if not os.path.exists(logFile): return public.returnMsg(False, 'CRONTAB_TASKLOG_EMPTY')
            logs = public.readFile(logFile)
            logs = logs.split('\n')
            if hasattr(get, 'day') and get.day != '':
                day = int(get.day)
                end_time = int(time.time())
                start_time = end_time - day * 86400
                
                last_idx = len(logs) - 1
                for i in range(len(logs) - 1, -1, -1):
                    info_obj = re.search(r'[【\[](\d+-\d+-\d+\s+\d+:\d+:\d+)[】\]]', logs[i])
                    if info_obj:
                        add_info_time = info_obj.group(1)
                        add_info_time = time.strptime(add_info_time, "%Y-%m-%d %H:%M:%S")
                        add_info_time = time.mktime(add_info_time)
                        if int(add_info_time) < start_time:
                            break
                        last_idx = i
                logs = logs[last_idx:]
            else:
                logs = []
            public.writeFile(logFile, '\n'.join(logs))
            return public.returnMsg(True, '清除成功！')
        except:
            return public.returnMsg(False, '清除失败！')
    
    def cloud_backup_download(self, get):
        if not hasattr(get, 'filename'):
            return public.returnMsg(False, '请传入filename!')
        if get.filename:
            if "|webdav|" in get.filename:
                import sys
                if '/www/server/panel/plugin/webdav' not in sys.path:
                    sys.path.insert(0, '/www/server/panel/plugin/webdav')
                try:
                    from webdav_main import webdav_main as webdav
                    path=webdav().cloud_download_file(get)['msg']
                except:
                    return public.returnMsg(False, '请先安装webdav存储插件！')
            else:
                path = get.filename.split('|')[0]
            if os.path.exists(path):
                return {'status': True, 'is_loacl': True, 'path': path}
        if not hasattr(get, 'cron_id'):
            return public.returnMsg(False, '请传入cron_id!')
        if "|" not in get.filename:
            return public.returnMsg(False, '文件不存在！')
        cron_data = public.M('crontab').where('id=?', (get.cron_id,)).field('sType,sName,db_type').find()
        if not cron_data:
            return public.returnMsg(False, "未找到对应计划任务的数据，请刷新页面查看该计划任务是否存在！")
        cloud_name = get.filename.split('|')[1]
        file_name = get.filename.split('|')[-1]
        names = cron_data['sName'].split(',')
        if names == ['ALL']:
            table = ''
            if cron_data['sType'] == 'site':
                table = 'sites'
            if cron_data['sType'] == 'database':
                table = 'databases'
            if not table:
                return public.returnMsg(False, '数据错误！')
            names = public.M(table).field('name').select()
            names = [i.get('name') for i in names]
        
        if cron_data['sType']=="path":
            names = [os.path.basename(i) for i in list(names) if os.path.basename(i) in file_name]
        else:
            names = [i for i in list(names) if i in file_name]
        
        if not names:
            public.returnMsg(False, '未找到对应的文件，请手动去云存储下载')
        if  cron_data['db_type']=="redis":
            name=""
        else:
            name = names[-1]
        import CloudStoraUpload
        c = CloudStoraUpload.CloudStoraUpload()
        c.run(cloud_name)
        url = ''
        backup_path = c.obj.backup_path
        if cron_data['sType'] == 'site':
            path = os.path.join(backup_path, 'site', name)
            data = c.obj.get_list(path)
            for i in data['list']:
                if i['name'] == file_name:
                    url = i['download']
            
            if not url:
                path = os.path.join(backup_path, 'site')
                data = c.obj.get_list(path)
                for i in data['list']:
                    if i['name'] == file_name:
                        url = i['download']
                        break
        elif cron_data['sType'] == 'database':
            path = os.path.join(backup_path, 'database', cron_data['db_type'], name)
            data = c.obj.get_list(path)
            for i in data['list']:
                if i['name'] == file_name:
                    url = i['download']
                    break
            if not url:
                if cron_data['db_type'] == "redis":
                    name = "redis"
                    path = os.path.join(backup_path, 'database', 'redis', name)
                else:
                    path = os.path.join(backup_path, 'database')
                    data = c.obj.get_list(path)
                    for i in data['list']:
                        if i['name'] == file_name:
                            url = i['download']
                            break
        elif cron_data['sType'] == 'path':
            path = os.path.join(backup_path, 'path', file_name.split('_')[1])
            data = c.obj.get_list(path)
            for i in data['list']:
                if i['name'] == file_name:
                    url = i['download']
                    break
        elif cron_data['sType'] == 'mysql_increment_backup':
            # path = os.path.join(backup_path, 'mysql_bin_log', file_name.split('_')[1],'databases')
            if "full" in get.filename:
                path = os.path.join(backup_path, 'mysql_bin_log', file_name.split('_')[2],'databases')
            else:
                path = os.path.join(backup_path, 'mysql_bin_log', file_name.split('_')[1],'databases')
            data = c.obj.get_list(path)
            for i in data['list']:
                if i['name'] == file_name:
                    url = i['download']
                    break
        if url == '':
            return public.returnMsg(False, '在云存储中未发现该文件!')
        return {'status': True, 'is_loacl': False, 'path': url}
    
    def get_crontab_types(self, get):
        data = public.M("crontab_types").field("id,name,ps").order("id asc").select()
        return {'status': True, 'msg': data}
    
    def add_crontab_type(self, get):
        # get.name =  html.escape(get.name.strip())
        get.name = public.xsssec(get.name.strip())
        if re.search('<.*?>', get.name):
            return public.returnMsg(False, "分类名称不能包含HTML语句")
        if not get.name:
            return public.returnMsg(False, "分类名称不能为空")
        if len(get.name) > 16:
            return public.returnMsg(False, "分类名称长度不能超过16位")
        
        crontab_type_sql = public.M('crontab_types')
        
        if get.name in {"Shell脚本", "备份网站", "备份数据库", "数据库增量备份", "日志切割", "备份目录", "木马查杀", "同步时间", "释放内存", "访问URL", "系统任务"}:
            return public.returnMsg(False, "指定分类名称已存在")
        
        if crontab_type_sql.where('name=?', (get.name,)).count() > 0:
            return public.returnMsg(False, "指定分类名称已存在")
        
        # 添加新的计划任务分类
        crontab_type_sql.add("name", (get.name,))
        
        return public.returnMsg(True, '添加成功')
    
    def remove_crontab_type(self, get):
        crontab_type_sql = public.M('crontab_types')
        crontab_sql = public.M('crontab')
        crontab_type_id = get.id
        
        if crontab_type_sql.where('id=?', (crontab_type_id,)).count() == 0:
            return public.returnMsg(False, "指定分类不存在")
        
        name = crontab_type_sql.where('id=?', (crontab_type_id,)).field('name').find().get('name', '')
        # if name in {"toShell", "site", "database", "enterpriseBackup", "logs", "path", "webshel", "syncTime", "rememory", "toUrl", "系统任务"}:
        #     return public.returnMsg(False, "这是默认类型，无法删除")
        
        # 删除指定的计划任务分类
        crontab_type_sql.where('id=?', (crontab_type_id,)).delete()
        
        # 找到 crontab 表中的相关数据，并设置其 sType 和 type_id 字段为空
        crontab_sql.where('type_id=?', (crontab_type_id,)).save('type_id', (0))
        
        return public.returnMsg(True, "分类已删除")
    
    def modify_crontab_type_name(self, get):
        get.name = public.xsssec(get.name.strip())
        # get.name =  html.escape(get.name.strip())
        if re.search('<.*?>', get.name):
            return public.returnMsg(False, "分类名称不能包含HTML语句")
        if not get.name:
            return public.returnMsg(False, "分类名称不能为空")
        if len(get.name) > 16:
            return public.returnMsg(False, "分类名称长度不能超过16位")
        
        crontab_type_sql = public.M('crontab_types')
        crontab_type_id = get.id
        
        if crontab_type_sql.where('id=?', (crontab_type_id,)).count() == 0:
            return public.returnMsg(False, "指定分类不存在")
        
        if get.name in {"Shell脚本", "备份网站", "备份数据库", "数据库增量备份", "日志切割", "备份目录", "木马查杀", "同步时间", "释放内存", "访问URL", "系统任务"}:
            return public.returnMsg(False, "名字不能修改为系统默认的任务分类名")
        
        if crontab_type_sql.where('name=? AND id!=?', (get.name, crontab_type_id)).count() > 0:
            return public.returnMsg(False, "指定分类名称已存在")
        
        # 修改指定的计划任务分类名称
        crontab_type_sql.where('id=?', (crontab_type_id,)).setField('name', get.name)
        
        return public.returnMsg(True, "修改成功")
    
    def set_crontab_type(self, get):
        try:
            crontab_ids = json.loads(get.crontab_ids)
            crontab_sql = public.M("crontab")
            crontab_type_sql = public.M("crontab_types")
            
            # sType= public.M('crontab_types').where('id=?', (get['type_id'],)).field('name').find().get('name', '')
            crontab_type_id = get.id
            if crontab_type_id=="-1" or crontab_type_id=="0":
                return public.returnMsg(False,"不能设置为系统分类或者默认分类!")
            if crontab_type_sql.where('id=?', (crontab_type_id,)).count() == 0:
                return public.returnMsg(False, "指定分类不存在")
            for s_id in crontab_ids:
                crontab_sql.where("id=?", (s_id,)).save('type_id', (crontab_type_id))
            
            return public.returnMsg(True, "设置成功")
        except Exception as e:
            return public.returnMsg(False, "设置失败" + str(e))
    
    
    def export_crontab_to_json(self, get):
        try:
            # 获取前端发送的id值，可以是逗号分隔的字符串
            task_ids = get.get('ids', None)
            
            if task_ids:
                # 去除方括号和多余的空格
                task_ids = task_ids.strip('[]').replace(' ', '')
                # 将逗号分隔的字符串转换为列表
                task_id_list = task_ids.split(',')
                # 使用where条件和in语句选择对应的计划任务
                crontab_data = public.M('crontab').where('id in ({})'.format(','.join('?' * len(task_id_list))), tuple(task_id_list)).field(self.field).select()
            else:
                crontab_data = public.M('crontab').order("id asc").field(self.field).select()
            
            # 遍历 crontab_data 列表
            # print(crontab_data)
            for task in crontab_data:
                # 将每个任务的 type_id 字段设置为空
                task['type_id'] = ""
                # # 删除 echo 字段
                # if 'echo' in task:
                #     del task['echo']
            
            # 将数据转换为 JSON 格式
            json_data = json.dumps(crontab_data)
            
            # 将 JSON 数据写入文件
            with open('/tmp/计划任务数据.json', 'w') as f:
                f.write(json_data)
            
            return public.returnMsg(True, "/tmp/计划任务数据.json")
        except Exception as e:
            return public.returnMsg(False, "导出失败：" + str(e))
    
    
    def import_crontab_from_json(self, get):
        try:
            file = request.files['file']
            overwrite = get.get('overwrite') == '1'
            if file:
                json_data = file.read().decode('utf-8')
                
                try:
                    crontab_data = json.loads(json_data)
                except ValueError as e:
                    return public.returnMsg(False, "无法解析的JSON文件！")
                
                if not isinstance(crontab_data, list):
                    return public.returnMsg(False, "JSON文件内容格式不正确！")
                
                existing_tasks = public.M('crontab').order("id desc").field(self.field).select()
                existing_names = {task['name'] for task in existing_tasks} if overwrite else set()
                
                successful_imports = 0
                failed_tasks = []
                skipped_tasks = []
                successful_tasks = []
                required_keys = [
                    'name', 'type', 'where1', 'where_hour', 'where_minute', 'addtime', 'status', 'save', 'backupTo',
                    'sName', 'sBody', 'sType', 'urladdress', 'save_local', 'notice', 'notice_channel', 'db_type', 'split_type',
                    'split_value', 'keyword', 'post_param', 'flock', 'time_set', 'backup_mode', 'db_backup_path', 'time_type',
                    'special_time', 'user_agent', 'version', 'table_list', 'result', 'log_cut_path', 'rname', 'type_id', 'second','stop_site'
                ]
                
                for task in crontab_data:
                    if overwrite and task['name'] in existing_names:
                        skipped_tasks.append(task['name'])
                        continue
                        
                        # 创建新任务字典时，特别处理 where_hour 和 where_minute
                    new_task = {}
                    for key in required_keys:
                        if key == 'where_hour':
                            key='hour'
                            new_task[key] = task.get('where_hour', '')
                        elif key == 'where_minute':
                            key='minute'
                            new_task[key] = task.get('where_minute', '')
                        else:
                            new_task[key] = task.get(key, '')
                    new_task['result'] = 1  # 设置默认 result 为 1
                    result = self.AddCrontab(new_task)
                    if result.get('status', False):
                        successful_imports += 1
                        successful_tasks.append(task['name'])
                    else:
                        failed_tasks.append(task['name'])
                
                message = "成功导入{}条计划任务".format(successful_imports)
                result = {
                    "status": True,
                    "msg": message,
                    "skipped_tasks": skipped_tasks,
                    "failed_tasks": failed_tasks,
                    "successful_tasks": successful_tasks
                }
                return result
            
            else:
                return public.returnMsg(False, "请选择导入文件!")
        except Exception as e:
            return public.returnMsg(False, "导入失败！{0}".format(str(e)))
    
    
    
    def stop_cron_task(self, cronPath, cronName, if_stop):
        cronFile = '{}/{}.pl'.format(cronPath,cronName)
        if if_stop == "True":
            if os.path.exists(cronFile):
                try:
                    # 读取文件内容，获取 PID
                    with open(cronFile, 'r') as file:
                        pid = file.read().strip()
                    os.system('kill -9 {}'.format(pid))
                    os.remove(cronFile)
                except:
                    pass
    
    def set_atuo_start_syssafe(self, get):
        try:
            if not hasattr(get, 'time'):
                return public.returnMsg(False, "请传入time参数！")
            time = int(get.time)
            public.ExecShell('/etc/init.d/bt_syssafe stop')
            data = {
                'type': 2,
                'time': time,
                'name': 'syssafe',
                'title': '宝塔系统加固',
                'fun': 'set_open',
                'args': {
                    'status': 1
                }
            }
            public.set_tasks_run(data)
            return public.returnMsg(True, "临时关闭系统加固成功！")
        except Exception as e:
            public.ExecShell('/etc/init.d/bt_syssafe start')
            return public.returnMsg(False, "临时关闭系统加固失败！" + str(e))
    
    # def set_atuo_start_syssafe(self, get):
    #     try:
    #         if not hasattr(get, 'time'):
    #             return public.returnMsg(False, "请传入time参数！")
    #         time = int(get.time)
    #         public.ExecShell('/etc/init.d/bt_syssafe stop')
    #         data = {
    #             'type': 2,
    #             'time': time,
    #             'name': 'syssafe',
    #             'title': '宝塔系统加固',
    #             'fun': 'set_open',
    #             'args': {
    #                 'status': 1
    #             }
    
    #         }
    #         public.set_tasks_run(data)
    #         return public.returnMsg(True, "临时关闭系统加固成功！")
    #     except Exception as e:
    #         return public.returnMsg(False, "临时关闭系统加固失败！" + str(e))
    
    def get_task_name_and_body(self,model_name, project_name):
        task_name = '[勿删]定时重启{}项目{}'.format(model_name, project_name)
        sBody = 'btpython /www/server/panel/script/restart_project.py {} {}'.format(model_name, project_name)
        return task_name, sBody
    
    def get_restart_project_config(self, get):
        try:
            task_name, sBody = self.get_task_name_and_body(get.model_name, get.project_name)
            crontab_data_list = public.M('crontab').where('name=?', (task_name,)).select()
            
            if crontab_data_list:
                crontab_data = crontab_data_list[0]
                return public.returnMsg(True, crontab_data)
            else:
                # 创建一个默认的 crontab 数据
                crontab_data = {
                    "name": task_name,
                    "type": "day",
                    "where1": "",
                    "where_hour": "0",
                    "where_minute": "0",
                    "week": "",
                    "sType": "toShell",
                    "sName": "",
                    "backupTo": "",
                    "save": "10",
                    "sBody": sBody,
                    "urladdress": "",
                    "status": 0
                }
            return public.returnMsg(True, crontab_data)
        except Exception as e:
            return public.returnMsg(False, "获取失败"+str(e))
    
    def set_restart_project(self, get):
        try:
            task_name, sBody = self.get_task_name_and_body(get.model_name, get.project_name)
            hour = get.get('hour', 0)
            minute = get.get('minute', 0)
            status = get.get('status', 0)
            
            # 查找是否已经存在任务
            crontab_data_list = public.M('crontab').where('name=?', (task_name,)).select()
            
            task = {
                "name": task_name,
                "type": "day",
                "where1": "",
                "hour": hour,
                "minute": minute,
                "week": "",
                "sType": "toShell",
                "sName": "",
                "backupTo": "",
                "save": "10",
                "sBody": sBody,
                "urladdress": ""
            }
            
            if not crontab_data_list:
                # 如果不存在任务，则创建新任务
                res=self.AddCrontab(task)
                if res.get('status'):
                    return public.returnMsg(True, "设置成功")
                else:
                    return public.returnMsg(False, res.get('msg', '设置失败'))
            
            
            else:
                # 如果存在任务，则修改任务
                task['id'] = crontab_data_list[0]['id']
                if int(status)==crontab_data_list[0]['status']:
                    res = self.modify_crond(task)
                    if res.get('status'):
                        return public.returnMsg(True, "设置成功")
                    else:
                        return public.returnMsg(False, res.get('msg', '设置失败'))
                else:
                    data={"id":task['id']}
                    return self.set_cron_status(data)
        
        except Exception as e:
            return public.returnMsg(False, "设置失败"+str(e))
    
    def modify_values(self, cronName, new_time_type, new_special_time, new_time_list):
        cronName = cronName
        cronPath = '/www/server/cron'
        cronFile = '{}/{}'.format(cronPath, cronName)
        # 打开文件
        with open(cronFile, 'r') as file:
            # 读取文件内容
            lines = file.readlines()
        
        # 进行你的修改
        for i, line in enumerate(lines):
            if "btpython /www/server/panel/script/time_check.py" in line:
                lines[i] = 'if ! btpython /www/server/panel/script/time_check.py time_type={} special_time={} time_list={}; then\n'.format(new_time_type, new_special_time, new_time_list)
        
        # 保存修改
        with open(cronFile, 'w') as file:
            file.writelines(lines)
    
    def set_execute_script(self, get):
        
        if '_ws' not in get:
            return False
        
        public.ExecShell("chmod +x /www/server/panel/script/check_crontab.sh")
        # 使用nohup运行脚本，并将输出重定向到/www/test.txt，同时确保命令在后台运行
        exec_result=public.ExecShell("nohup /www/server/panel/script/check_crontab.sh > /tmp/check_crontab.txt 2>&1 &")
        
        if exec_result:  # 假设ExecShell返回的第一个元素是成功与否的标志
            # 以只读模式打开日志文件，并移动到文件末尾
            if not os.path.exists("/tmp/check_crontab.txt"):
                public.writeFile("/tmp/check_crontab.txt","")
            
            with open("/tmp/check_crontab.txt", "r") as log_file:
                while True:
                    # 读取新的一行                   
                    line = log_file.readline()
                    if not line:
                        time.sleep(1)  # 如果没有新内容，则稍等片刻再尝试读取
                        continue
                    get._ws.send(public.getJson({
                        "callback":"set_execute_script",
                        "result":line.strip()
                        
                    }))
                    if line.strip()=="successful":
                        break
            return True
        else:
            get._ws.send("脚本执行失败")
            return False
    
    def get_system_user_list(self, get):
        all_user = False
        if get is not None:
            if hasattr(get, "all_user"):
                all_user = True
        root_and_www = []  # 新增列表存储root和www用户
        other_users = []   # 新增列表存储其他用户
        try:
            import pwd
            for tmp_uer in pwd.getpwall():
                if tmp_uer.pw_name == 'www':
                    root_and_www.append(tmp_uer.pw_name)
                elif tmp_uer.pw_uid == 0:
                    root_and_www.append(tmp_uer.pw_name)
                elif tmp_uer.pw_uid >= 1000:
                    other_users.append(tmp_uer.pw_name)
                elif all_user:
                    other_users.append(tmp_uer.pw_name)
        except Exception:
            pass
        return root_and_www + other_users
    
    def set_status(self,get):
        task_name = '自动备份mysql数据库[所有]'
        data={"id":public.M('crontab').where("name=?", (task_name,)).getField('id')}
        return crontab().set_cron_status(public.to_dict_obj(data))
    
    def get_auto_config(self, get):
        try:
            
            name=get.name
            if name=="mysql":
                task_name = '自动备份mysql数据库[所有]'
            #    sType='database'
            if name=="site":
                task_name = '自动备份网站[所有]'
            #    sType='site'
            
            public.M('crontab').where('name=?', (task_name,)).select()
            # if public.M('crontab').where('name=?', (task_name,)).count() == 0:
            #     task = {
            #         "name": task_name,
            #         "type": "day",
            #         "where1":"" ,
            #         "hour": "4",
            #         "minute":"0",
            #         "week": "",
            #         "sType": sType,
            #         "sName": "ALL",
            #         "backupTo": "localhost",
            #         "save": "3",
            #         "sBody": "",
            #         "urladdress": "",
            #         "db_type":name
            #     }
            #     crontab().AddCrontab(task)
            #     self.set_status(get)
            crontab_data_list = public.M('crontab').where('name=?', (task_name,)).select()
            if crontab_data_list:
                crontab_data = crontab_data_list[0]
            else:
                crontab_data={"status":0}
            return public.returnMsg(True, crontab_data)
        
        except Exception as e:
            return public.returnMsg(False, "获取失败"+str(e))
    
    def set_auto_config(self,get):
        try:
            # status=get.status
            name=get.name
            if name=="mysql":
                task_name = '自动备份mysql数据库[所有]'
                sType='database'
            if name=="site":
                task_name = '自动备份网站[所有]'
                sType='site'
            if public.M('crontab').where('name=?', (task_name,)).count() == 0:
                task = {
                    "name": task_name,
                    "type": "day",
                    "where1":"" ,
                    "hour": "4",
                    "minute":"0",
                    "week": "",
                    "sType": sType,
                    "sName": "ALL",
                    "backupTo": "localhost",
                    "save": "3",
                    "sBody": "",
                    "urladdress": "",
                    "db_type":name,
                    "table_list": "ALL",
                }
                res=crontab().AddCrontab(task)
                if res['status']:
                    return public.returnMsg(True,"设置成功！")
                else:
                    return public.returnMsg(False, res['msg'])
            else:
                return self.set_status(get)
        
        except Exception as e:
            return public.returnMsg(False, "开启失败"+str(e))
    
    def set_rotate_log(self, get):
        try:
            
            
            try:
                log_size = float(get.log_size) if float(get.log_size) >= 0 else 0
                hour = get.hour.strip() if 0 <= int(get.hour) < 24 else "2"
                minute = get.minute.strip() if 0 <= int(get.minute) < 60 else '0'
                num = int(get.num) if 0 < int(get.num) <= 1800 else 10
                compress = int(get.compress) == 1
            except (ValueError, AttributeError, KeyError):
                log_size = 0
                hour = "2"
                minute = "0"
                num = 10
                compress = False
            
            if log_size != 0:
                log_size = log_size * 1024 * 1024
                hour = 0
                minute = 5
            
            log_conf = {
                "log_size": log_size,
                "hour": hour,
                "minute": minute,
                "num": num,
                "compress": compress
            }
            flag, msg = self.change_cronta(log_conf)
            if flag:
                conf_path = '{}/data/crontab_log_split.conf'.format(public.get_panel_path())
                if os.path.exists(conf_path):
                    try:
                        data = json.loads(public.readFile(conf_path))
                    except:
                        data = {}
                else:
                    data = {}
                data= {
                    "stype": "size" if bool(log_size) else "day",
                    "log_size": log_size,
                    "num": num,
                    "compress": compress
                }
                public.writeFile(conf_path, json.dumps(data))
            return public.returnMsg(flag, msg)
        except Exception as e:
            return public.returnMsg(False, str(e))
    
    def change_cronta(self, log_conf):
        
        python_path = "btpython"
        cronInfo = public.M('crontab').where('name=?', ('[勿删]切割计划任务日志',)).find()
        if not cronInfo:
            return self.add_crontab(log_conf, python_path)
        id = cronInfo['id']
        del (cronInfo['id'])
        del (cronInfo['addtime'])
        cronInfo['sBody'] = '{pyenv} {script_path}'.format(
            pyenv=python_path,
            script_path="/www/server/panel/script/rotate_log.py",
        )
        cronInfo['where_hour'] = log_conf['hour']
        cronInfo['where_minute'] = log_conf['minute']
        cronInfo['save'] = log_conf['num']
        cronInfo['type'] = 'day' if log_conf["log_size"] == 0 else "minute-n"
        cronInfo['where1'] = '' if log_conf["log_size"] == 0 else log_conf['minute']
        
        columns = 'where_hour,where_minute,sBody,save,type,where1'
        values = (cronInfo['where_hour'], cronInfo['where_minute'], cronInfo['sBody'], cronInfo['save'], cronInfo['type'], cronInfo['where1'])
        self.remove_for_crond(cronInfo['echo'])
        if cronInfo['status'] == 0: return False, '当前任务处于停止状态,请开启任务后再修改!'
        sync_res=self.sync_to_crond(cronInfo)
        if not sync_res['status']:
            return False,sync_res['msg']
        public.M('crontab').where('id=?', (id,)).save(columns, values)
        public.WriteLog('计划任务', '修改计划任务[' + cronInfo['name'] + ']成功')
        return True, '修改成功'
    
    def add_crontab(self,log_conf, python_path):
        
        cron_name = '[勿删]切割计划任务日志'
        if not public.M('crontab').where('name=?', (cron_name,)).count():
            cmd = '{pyenv} {script_path}'.format(
                pyenv=python_path,
                script_path="/www/server/panel/script/rotate_log.py",
            )
            args = {
                "name": cron_name,
                "type": 'day' if log_conf["log_size"] == 0 else "minute-n",
                "where1": "" if log_conf["log_size"] == 0 else log_conf["minute"],
                "hour": log_conf["hour"],
                "minute": log_conf["minute"],
                "sType": 'toShell',
                "notice": '0',
                "sName":cron_name,
                "notice_channel": '',
                "save": str(log_conf["num"]),
                "save_local": '1',
                "backupTo": '',
                "sBody": cmd,
                "urladdress": ''
            }
            res = self.AddCrontab(args)
            if res and "id" in res.keys():
                return True, "新建任务成功"
            return False, res["msg"]
        return True
    
    def get_rotate_log_config(self, get):
        try:
            p = crontab()
            task_name = '[勿删]切割计划任务日志'
            config_path = '{}/data/crontab_log_split.conf'.format(public.get_panel_path())
            
            log_size = 0
            hour = "0"
            minute = "0"
            num = 10
            compress = False
            stype="day"
            
            default_config = {
                "log_size": log_size,
                "hour": hour,
                "minute": minute,
                "num":  num,
                "compress": compress,
                "stype": stype,
            }
            
            if os.path.exists(config_path):
                try:
                    data = json.loads(public.readFile(config_path))
                    data['log_size']=data['log_size']
                    cron_info=public.M('crontab').where('name=?', (task_name,)).find()
                    data['status']=cron_info['status']
                    data['hour']=cron_info['where_hour']
                    data['minute']=cron_info['where_minute']
                
                except:
                    data = default_config
            else:
                data=default_config
                data['status']=0
                with open(config_path, 'w') as config_file:
                    json.dump(default_config, config_file)
            
            
            return public.returnMsg(True, data)
        except Exception as e:
            return public.returnMsg(False, "获取失败" + str(e))
    
    
    def set_rotate_log_status(self,get):
        task_name = '[勿删]切割计划任务日志'
        cronInfo = public.M('crontab').where('name=?', (task_name,)).find()
        if not cronInfo:
            hour = "0"
            minute = "0"
            num = 10
            if public.M('crontab').where('name=?', (task_name,)).count() == 0:
                task = {
                    "name": task_name,
                    "type": "day",
                    "where1": "1",
                    "hour": hour,
                    "minute": minute,
                    "week": "",
                    "sType": "toShell",
                    "sName": "",
                    "backupTo": "",
                    "save": num,
                    "sBody": "btpython /www/server/panel/script/rotate_log.py",
                    "urladdress": "",
                    "status": "1"
                }
                return self.AddCrontab(task)
        status = 1
        
        if cronInfo['status'] == status:
            status = 0
            remove_res=self.remove_for_crond(cronInfo['echo'])
            if not remove_res['status']:
                return public.returnMsg(False, remove_res['msg'])
        else:
            cronInfo['status'] = 1
            sync_res=self.sync_to_crond(cronInfo)
            if not sync_res['status']:
                return public.returnMsg(False, sync_res['msg'])
        
        public.M('crontab').where('id=?', (cronInfo["id"],)).setField('status', status)
        return public.returnMsg(True, '设置成功')    # 增量备份获取数据库信息
    def get_databases(self, get):
        from panelMysql import panelMysql
        # try:
        #     import PluginLoader
        #     return PluginLoader.module_run('binlog', 'get_databases', get)
        # except Exception as err:
        #     return {"status":False, "msg": err}
        try:
            database_list = public.M("databases").field("name").where("sid=0 and LOWER(type)=LOWER(?)", ("mysql")).select()
            for database in database_list:
                database["value"] = database["name"]
                cron_id = public.M("mysql_increment_settings").where("db_name=?", (database["name"])).getField("cron_id")
                database["cron_id"] = cron_id if cron_id else None
                
                table_list = panelMysql().query("show tables from `{db_name}`;".format(db_name=database["name"]))
                if not isinstance(table_list, list):
                    continue
                cron_id = public.M("mysql_increment_settings").where("tb_name == ''", ()).getField("cron_id")
                database["table_list"] = [{"tb_name": "所有", "value": "", "cron_id": cron_id if cron_id else None}]
                for tb_name in table_list:
                    cron_id = public.M("mysql_increment_settings").where("tb_name in (?)", (tb_name[0])).getField("cron_id")
                    database["table_list"].append({"tb_name": tb_name[0], "value": tb_name[0], "cron_id": cron_id if cron_id else None})
            return {"status": True, "msg": "ok", "data": database_list}
        except Exception as err:
            return {"status":False, "msg": err}
    def get_local_backup_path(self,get):
        try:
            
            from  panelBackup import backup
            id = get['id']
            query = public.M('crontab').where("id=?", (id,))
            data=query.select()[0]
            sType=data['sType']
            sName=data['sName']
            db_backup_path=data['db_backup_path']
            save_local=data['save_local']
            
            if sType=="site":
                base_backup_dir=backup().get_site_backup_dir(data['backupTo'],data['save_local'],db_backup_path,sName)
                if sName=="ALL":
                    local_backup_path = os.path.join(base_backup_dir, 'site')
                else:
                    local_backup_path = os.path.join(base_backup_dir, 'site', sName)
            elif sType=="database":
                db_type=data['db_type']
                args = {"backup_mode": data['backup_mode'], "db_backup_path": db_backup_path, "save_local":save_local}
                base_backup_dir=backup().get_backup_dir(data,args,db_type)
                if sName=="ALL" or db_type=="redis":
                    local_backup_path = base_backup_dir
                else:
                    local_backup_path = os.path.join(base_backup_dir,sName)
            elif sType=="path":
                
                base_backup_dir=backup()._BACKUP_DIR
                local_backup_path = os.path.join(base_backup_dir,"path",os.path.basename(sName))
                if not os.path.exists(local_backup_path):
                    local_backup_path = os.path.join(base_backup_dir,"path")
            elif sType=="mysql_increment_backup":
                base_backup_dir=public.M("config").where("id=?", (1,)).getField("backup_path")
                local_backup_path = os.path.join(base_backup_dir, "mysql_bin_log/",sName)
            return public.returnMsg(True, local_backup_path)
        except Exception as e:
            return public.returnMsg(False, str(e))


import os,sys,json
os.chdir('/www/server/panel')
if not 'class/' in sys.path:
    sys.path.insert(0,'class/')
import public


# 标记文件路径
CHECK_MOD_PUSH_FILE = "/www/server/panel/data/mod_push_data/check_mod_push_file.pl"
OLD_PUSH_DATA_PATH = "/www/server/panel/class/push/push.json"
NEW_PUSH_DATA_PATH = "/www/server/panel/data/mod_push_data/task.json"



def check_and_delete_old_tasks(old_push_data: dict, new_push_data: dict):
    for task_group_key, task_group_value in old_push_data.items():
        if not task_group_value:
            continue
        tasks_to_delete = []
        for old_task_key, old_task_value in task_group_value.items():

            # old_task_type = old_task_value.get("type")
            # old_task_title = old_task_value.get("title")
            # print(f"处理具体任务: {old_task_key}, type: {old_task_type}, title: {old_task_title}")

            # if old_task_type is None or old_task_title is None:
            #     print(f"具体任务 {old_task_key} 的 type 或 title 字段为 None，跳过该任务")
            #     continue
            for new_task in new_push_data:
                if compare_tasks(old_task_value, new_task):
                    tasks_to_delete.append(old_task_key)
                    print(f"迁移成功，删除具体任务: {old_task_key}")
                    break

        
        # 打印要删除的任务列表
        print("tasks_to_delete:", tasks_to_delete)
        print("task_group_value before deletion:", task_group_value)

        # 删除任务
        for task_key in tasks_to_delete:
            if task_key in task_group_value:
                del task_group_value[task_key]
                print(f"实际删除任务: {task_key}")
        old_push_data[task_group_key] = task_group_value

    # 更新旧任务数据文件
    public.writeFile(OLD_PUSH_DATA_PATH, json.dumps(old_push_data, ensure_ascii=False, indent=4))

               

def compare_tasks(old_task, new_task):
    try:
        """
        比较旧任务和新任务是否相同
        第一种情况：只比较类型，但类型名改变了
        第二种情况：比较类型和项目名，但类型改变了
        第三种情况：类型名不变，比较类型
        """
        old_task_type = old_task['type']
        old_project = old_task.get('project', '')

        if 'task_data' not in new_task:
            return False

        new_task_type = new_task['task_data'].get('type', '')
        new_project = new_task['task_data'].get('project', '')

        # 第一种情况：只比较类型，类型名改变了
        type_mapping = {
            'site_endtime': 'site_end_time',
            'panel_pwd_endtime': 'panel_pwd_end_time',
            'disk': 'system_disk',
            'cpu': 'system_cpu',
            'load': 'system_load',
            'mem': 'system_mem',
            'ssl': 'site_ssl',
            'mysql_pwd_endtime': 'mysql_pwd_end'
        }

        if old_task_type in type_mapping and new_task_type == type_mapping[old_task_type]:
            return True
        # print(new_project)
        # print(old_project)
        # 第二种情况：比较类型和项目名，类型改变了
        if old_task_type == 'ssl' and new_task.get('source')  == 'site_ssl' and old_project == new_project:
            return True

        if old_task_type == 'project_status' and new_task_type == 'project_status' and old_project == new_project:
            return True

        if old_task_type == 'services' and new_task_type == 'services' and old_project == new_project:
            return True

        # 第三种情况：类型名不变，直接比较类型
        if old_task_type == new_task_type: 

            return True
        # 处理特殊情况，比如 "panel_update、 ssh_login" 的关键字匹配
        if new_task.get('source') == old_task_type:
            return True
        if new_task.get('keyword') ==  type_mapping[old_task_type]:
            return True

        if new_task.get('source') ==  type_mapping[old_task_type]:
                return True

        return False
    except Exception as e:
        print(e)

           

def main():
    try:
        old_push_data=json.loads(public.readFile(OLD_PUSH_DATA_PATH))
        # print("old_push_data:",old_push_data)
    except:
        return 
    
    try:
        new_push_data=json.loads(public.readFile(NEW_PUSH_DATA_PATH))
        # print("new_push_data:",new_push_data)
    except:
        return 

    if  old_push_data and  new_push_data:
        try:
            check_and_delete_old_tasks(old_push_data,new_push_data)
        except:
            pass 
    # 写入标记文件，表明处理完成
    public.writeFile(CHECK_MOD_PUSH_FILE,"")

if __name__=="__main__":
    main()

import os, sys, shutil, time

os.chdir('/www/server/panel')
sys.path.insert(0,"class/")
import public
import json, glob
from projectModel import pythonModel


def main(name, mode, num):
    #获取数据库信息
    python_model = pythonModel.main()
    project = public.M('sites').where('project_type=? AND name=?',('Python',name)).field('name,path,project_config').find()
    if not project:
        return
    conf = json.loads(project['project_config'])
    project_name = project['name']
    if mode == "create":
        for i in _get_log_names(conf):
            log_sqlit_by_create(conf["logpath"], i, num)
        if python_model.get_project_run_state(conf):
            get= public.dict_obj()
            get.name = project_name
            python_model.RestartProject(get)
    elif mode == "copy":
        for i in _get_log_names(conf):
            log_sqlit_by_copy(conf["logpath"], i, num)
 
    return 

def _get_log_names(conf):
    if conf["stype"]=="python":
        log_file = ["error", ]
    elif conf["stype"]=="gunicorn":
        log_file = ["gunicorn_error", "gunicorn_acess"]
    else:
        log_file = ["uwsgi", ]
    
    return log_file

def _del_surplus_log(log_path, log_name, num):
    history_log_path = log_path + '/history_logs'
    logs=sorted(glob.glob(history_log_path + '/' + log_name + "*_log.log"))

    count=len(logs)
    if count > num:
        for i in logs[:count-num]:
            if os.path.exists(i):
                os.remove(i)
                print('|---多余日志['+i+']已删除!')

     

def log_sqlit_by_create(log_path, log_name, num):
    _del_surplus_log(log_path, log_name, num)
    his_date = time.strftime("%Y-%m-%d_%H%M%S")
    history_log_path = log_path + '/history_logs'
    if not os.path.exists(history_log_path):
        os.makedirs(history_log_path, mode=0o755)

    log_file = os.path.join(log_path, log_name + '.log')
    if os.path.exists(log_file):
        history_log_file = history_log_path + '/' + log_name +'_'+ his_date + '_log.log'
        if not os.path.exists(history_log_file):
            shutil.move(log_file, history_log_file)

            print('|---已切割日志到:'+history_log_file)
            


def log_sqlit_by_copy(log_path, log_name, num):
    _del_surplus_log(log_path, log_name, num)
    his_date = time.strftime("%Y-%m-%d_%H%M%S")

    history_log_path = log_path + '/history_logs'
    if not os.path.exists(history_log_path):
        os.makedirs(history_log_path, mode=0o755)

    log_file = os.path.join(log_path, log_name + '.log')
    if os.path.exists(log_file):
        history_log_file = history_log_path + '/' + log_name +'_'+ his_date + '_log.log'
        if not os.path.exists(history_log_file):
            with open(history_log_file, 'w', encoding='utf-8') as hf:
                with open(log_file, 'r+', encoding='utf-8') as lf:
                    logs = lf.read()
                    lf.seek(0)
                    lf.truncate()
                hf.write(logs)
            print('|---已切割日志到:'+history_log_file)



    
if __name__ == "__main__":
    if len(sys.argv) == 4:   
        name = sys.argv[1]
        mode = sys.argv[2]
        try:
            num = int(sys.argv[3])
        except ValueError:
            print("配置参数出现问题")
        else:
            main(name, mode, num)
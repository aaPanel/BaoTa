import time
import os, sys
panelPath = '/www/server/panel/'
os.chdir(panelPath)
needed_paths=['/www/server/panel', '/www/server/panel/class']
for path in needed_paths:
    if path not in sys.path:
        sys.path.insert(0,path)
import public

def task(echo):
    execstr = public.GetConfigValue('setup_path') + '/cron/' + echo
    public.ExecShell('chmod +x ' + execstr)
    public.ExecShell('nohup ' + execstr + ' start >> ' + execstr + '.log 2>&1 &')


def run_task(echo, interval):
    timestamp_file = '{}/data/{}.timestamp'.format(panelPath,echo)
    start_time = time.time() 

    while time.time() - start_time <= 60:  
        try:
            with open(timestamp_file, 'r') as file:
                last_executed = float(file.read().strip())
        except (FileNotFoundError, ValueError):
            last_executed = 0

        current_time = time.time()
        if current_time - last_executed >= interval:
            # print("任务开始执行时间： {}".format(time.strftime('%H:%M:%S')))
            task(echo)
            with open(timestamp_file, 'w') as file:
                file.write(str(time.time()))
        # 计算需要等待的时间，避免过频繁的检查
        time_to_wait = interval - (current_time - last_executed)
        time.sleep(max(0, time_to_wait))

if __name__ == '__main__':
    if len(sys.argv) != 3:
        sys.exit(1)

    interval = int(sys.argv[1])
    echo = sys.argv[2]

    run_task(echo, interval)

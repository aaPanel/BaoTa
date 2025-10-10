import time
# 每秒往文件中写入一条数据，模拟测试
_rCmd_log = '/tmp/dockerRun.log'

while True:
    with open(_rCmd_log, 'a+') as f:
        f.write(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()) + '\n')
    time.sleep(1)
import sys

sys.path.insert(0, "/www/server/panel/class/")
import PluginLoader
print("开始执行同步站点任务...")
syncsite = PluginLoader.module_run("syncsite", "run_task",{})
print(syncsite)
print("同步站点任务执行完毕!")
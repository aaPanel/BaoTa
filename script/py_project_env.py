#!/www/sererv/panel/penv/bin/python3
# coding: utf-8
# -----------------------------
# 宝塔Linux面板Python项目准备脚本
# -----------------------------
import json
import sys
import os

os.chdir("/www/server/panel")
if "/www/server/panel" not in sys.path:
    sys.path.insert(0, "/www/server/panel")
if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")


import public
from projectModel.pythonModel import main as pythonMod


def main(pj_id):
    project_info = public.M('sites').where('id=? ', (pj_id,)).find()
    if not isinstance(project_info, dict):
        print("项目不存在")
    values = json.loads(project_info["project_config"])
    pythonMod().simple_prep_env(values)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        project_id = sys.argv[1]
        try:
            project_id = int(project_id)
        except:
            exit(1)
        else:
            main(project_id)

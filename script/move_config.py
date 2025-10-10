# -*- coding: utf-8 -*-
import sys
import os
import datetime
import time
sys.path.insert(0, '/www/server/panel/class')
from panelSite import panelSite
from data import data
import public

def get_website_status(website):
    web = public.M('sites').where('name=?', (website,)).find()
    if not web:
        return None  
    if web['project_type'] == "PHP":
        if web['status'] != "1":
            return False

    panelPath = '/www/server/panel/'
    os.chdir(panelPath)
    sys.path.insert(0, panelPath)
    if web['project_type'] == "Java":
        from mod.project.java.projectMod import main as java
        if not java().get_project_stat(web)['pid']:
            return False
    if web['project_type'] == "Node":
        from projectModel.nodejsModel import main as nodejs
        if not nodejs().get_project_run_state(project_name=web['name']):
            return False
    if web['project_type'] == "Go":
        from projectModel.goModel import main as go
        if not go().get_project_run_state(project_name=web['name']):
            return False
    if web['project_type'] == "Python": 
        from projectModel.pythonModel import main as python
        if not python().get_project_run_state(project_name=web['name']):
            return False
    if web['project_type'] == "Other":  
        from projectModel.otherModel import main as other
        if not other().get_project_run_state(project_name=web['name']):
            return False
    return True

def stop_website(website):
    get = public.dict_obj()

    panelPath = '/www/server/panel/'
    os.chdir(panelPath)
    sys.path.insert(0, panelPath)

    web = public.M('sites').where('name=?', (website,)).find()
    if web['project_type'] == "Java":
        from mod.project.java.projectMod import main as java
        get.project_name = website
        return java().stop_project(get)
    if web['project_type'] == "Node":
        from projectModel.nodejsModel import main as nodejs
        get.project_name = website
        return nodejs().stop_project(get)
    if web['project_type'] == "Go":
        from projectModel.goModel import main as go
        get.project_name = website
        return go().stop_project(get)
    if web['project_type'] == "Python":
        from projectModel.pythonModel import main as python
        get.project_name = website
        return python().StopProject(get)
    if web['project_type'] == "Other":
        from projectModel.otherModel import main as other
        get.project_name = website
        return other().stop_project(get)

    id = public.M('sites').where("name=?", (website,)).getField('id')
    if web['project_type'] == "PHP":
        get.id = id
        get.name = website
        return panelSite().SiteStop(get)

def start_website(website):
    panelPath = '/www/server/panel/'
    os.chdir(panelPath)
    sys.path.insert(0, panelPath)

    web = public.M('sites').where('name=?', (website,)).find()
    get = public.dict_obj()
    if web['project_type'] == "Java":
        from mod.project.java.projectMod import main as java
        get.project_name = website
        return java().start_project(get)
    if web['project_type'] == "Node":
        from projectModel.nodejsModel import main as nodejs
        get.project_name = website
        return nodejs().start_project(get)
    if web['project_type'] == "Go":
        from projectModel.goModel import main as go
        get.project_name = website
        return go().start_project(get)
    if web['project_type'] == "Python":
        from projectModel.pythonModel import main as python
        get.project_name = website
        return python().start_project(get)
    if web['project_type'] == "Other":
        from projectModel.otherModel import main as other
        get.project_name = website
        return other().start_project(get)
    if web['project_type'] == "PHP":
        id = public.M('sites').where("name=?", (website,)).getField('id')
        get.id = id
        get.name = website
        return panelSite().SiteStart(get)

def manage_website(website, times, force_start=False):
    current_time = datetime.datetime.now().strftime('%H:%M')
    
    # 如果 website 为 "ALL"，则获取所有网站名称
    if website == "ALL":
        websites = public.M('sites').field('name').select()
        websites = [site['name'] for site in websites]
    else:
        websites = [website]

    start_time, stop_time = times.split(',')

    if current_time == start_time or current_time == stop_time or force_start:

        print('==================================================================')
        print('★开始执行网站启停操作[' + time.strftime("%Y/%m/%d %H:%M:%S") + ']')
        # print("|-开始对网站{}执行启停操作[{}]".format(website,datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        # if website=="ALL":
        #     print("|-开始对全部网站执行启停操作[{}]".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        # else:
        #     print("|-开始对网站{}执行启停操作[{}]".format(website,datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))  
        for site in websites:
            web = public.M('sites').where('name=?', (site,)).find()
            if web['project_type'] not in ["PHP", "Java", "Node", "Go", "Python", "Other"]:
                print("|-网站{}为不支持操作的项目类型，跳过".format(web['name']))
                continue
            
            status = get_website_status(site)
            if status is None:
                print("|-网站 {} 不存在.".format(web['name']))
                continue

            if current_time == start_time:
                if not status:
                    result = start_website(site)
                    if result['status']:
                        print("|-网站 {} 已在 {} 启动.".format(site, start_time))
                    else:
                        print("|-启动网站 {} 失败,请去网站页面手动尝试是否能启动网站！".format(site))

            elif current_time == stop_time:
                if status:
                    result = stop_website(site)
                    if result['status']:
                        print("|-网站 {} 已在 {} 停止.".format(site, stop_time))
                    else:
                        print("|-停止网站 {} 失败,请去网站页面手动尝试是否能停止网站！".format(site))
            elif force_start:
                if status:
                    result = stop_website(site)
                    if result['status']:
                        print("|-网站 {} 已停止.".format(site))
                    else:
                        print("|-停止网站 {} 失败,请去网站页面手动尝试是否能停止网站！".format(site))

                else:
                    result = start_website(site)
                    if result['status']:
                        print("|-网站 {} 已启动.".format(site))
                    else:
                        print("|-启动网站 {} 失败,请去网站页面手动尝试是否能启动网站！".format(site))

        # print("============================================================================")
        # print("|-结束执行[{}]".format(datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        # print("----------------------------------------------------------------------------")

# 获取命令行参数作为网站名称
if len(sys.argv) < 3:
    print("用法: python manage_website.py <网站名称> <停止时间,启动时间> [start]")
    sys.exit(1)

website = sys.argv[1]
times = sys.argv[2]
force_start = len(sys.argv) > 3 and sys.argv[3] == "start"
manage_website(website, times, force_start)

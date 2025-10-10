# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: sww <sww@bt.cn>
# -------------------------------------------------------------------
import json
import os
# ------------------------------
# 用户模型
# ------------------------------
import sys
import traceback
import psutil

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

os.chdir("/www/server/panel")
import public
from typing import List, Dict, Any, Union


class RealUser:
    def __init__(self):
        self.groupList = self.get_group_list()['data']
        print(self.groupList)

    # --------------------获取用户列表 Start--------------------
    def get_user_list(self, search: str = '') -> Dict[str, Union[bool, str, List[Dict[str, Any]]]]:
        """
        获取用户列表
        :param search: 搜索关键词 可搜索 用户名、备注、shell、home、用户组
        :return: list
        """
        try:
            import pwd, grp
            ret_user_list = []
            user_list = pwd.getpwall()
            for u in user_list:
                try:
                    gp = grp.getgrgid(u.pw_gid).gr_name
                except:
                    gp = ''
                ret_user_list.append({
                    'username': u.pw_name,
                    'uid': u.pw_uid,
                    'gid': u.pw_gid,
                    'group': gp,
                    'ps': self._get_user_ps(u.pw_name, u.pw_gecos),
                    'home': u.pw_dir,
                    'login_shell': u.pw_shell
                })

            if search != '':
                ret_user_list = self._search_user(ret_user_list, search)
            return public.returnResult(code=1, data=ret_user_list, msg='获取用户列表成功!', status=True)
        except Exception as e:
            print(traceback.format_exc())
            return public.returnResult(code=0, data=[], msg='获取用户列表失败!错误：' + str(e), status=False)

    def _get_user_ps(self, name: str, ps: str) -> str:
        """
        获取用户备注
        :param name: 用户名
        :param ps: 备注
        :return: str
        """
        userPs = {'www': '宝塔面板', 'root': '超级管理员', 'mysql': '用于运行MySQL的用户',
                  'mongo': '用于运行MongoDB的用户',
                  'git': 'git用户', 'mail': 'mail', 'nginx': '第三方nginx用户', 'postfix': 'postfix邮局用户',
                  'lp': '打印服务帐号',
                  'daemon': '控制后台进程的系统帐号', 'nobody': '匿名帐户', 'bin': '管理大部分命令的帐号',
                  'adm': '管理某些管理文件的帐号', 'smtp': 'smtp邮件'}
        if name in userPs: return userPs[name]
        if not ps: return name
        return ps

    def _get_group_name(self, gid: str) -> str:
        """
        获取用户组名称
        :param gid: 用户组ID
        :return: str
        """
        for g in self.groupList:
            if g['gid'] == gid: return g['group']
        return ''

    def _search_user(self, data: List[Dict[str, Any]], search: str) -> List[Dict[str, Union[str, Any]]]:
        """
        搜索用户
        :param data: 用户列表
        :param search: 搜索关键词
        :return: list
        """
        try:
            ldata = []
            for i in data:
                if search in i['username'] or search in i['ps'] or search in i['login_shell'] or search in i['home'] or search in i['group']:
                    ldata.append(i)
            return ldata
        except:
            return data

    def get_group_list(self):
        """
        获取用户组列表
        :return:list

        """
        tmpList = public.readFile('/etc/group').split("\n")
        groupList = []
        for gl in tmpList:
            tmp = gl.split(':')
            if len(tmp) < 3: continue
            groupInfo = {}
            groupInfo['group'] = tmp[0]
            groupInfo['gid'] = tmp[2]
            groupList.append(groupInfo)
        return public.returnResult(code=1, data=groupList, msg='获取用户组列表成功!', status=True)

    # --------------------获取用户列表 End----------------------

    # --------------------删除用户 Start------------------------
    def remove_user(self, user: str) -> Dict[str, Any]:
        users = ['www', 'root', 'mysql', 'shutdown', 'postfix', 'smmsp', 'sshd', 'systemd-network', 'systemd-bus-proxy',
                 'avahi-autoipd', 'mail', 'sync', 'lp', 'adm', 'bin', 'mailnull', 'ntp', 'daemon', 'sys']
        if user in users: return public.returnResult(code=0, msg='系统用户或关键用户不能删除!', status=False)
        r = public.ExecShell("userdel " + user)
        if r[1].find('process') != -1:
            try:
                pid = r[1].split()[-1]
                p = psutil.Process(int(pid))
                pname = p.name()
                p.kill()
                public.ExecShell("pkill -9 " + pname)
                r = public.ExecShell("userdel " + user)
                public.ExecShell("rm -rf /home/" + user)
            except:
                pass
        if r[1].find('userdel:') != -1: return public.returnMsg(False, r[1])
        return public.returnResult(code=1, msg='删除成功!', status=True)

    # --------------------删除用户 End------------------------

    # --------------------添加用户 Start------------------------
    def add_user(self, user: str, pwd: str, group: str) -> Dict[str, Any]:
        try:
            if not user: return public.returnResult(code=0, msg='用户名不能为空!', status=False)
            if not pwd: return public.returnResult(code=0, msg='密码不能为空!', status=False)
            if not self._check_user(user): return public.returnResult(code=1, msg='用户已存在!', status=True)
            if not self._check_group(group): self.add_group(group)
            r = public.ExecShell("useradd -g " + group + " -m " + user + ' -p' + pwd)
            if r[1].find('useradd:') != -1 and r[1].find('already exists') == 1: return public.returnResult(code=0, msg=r[1], status=False)
            # public.ExecShell("echo \"" + user + ":" + pwd + "\" | chpasswd")
            return public.returnResult(code=1, msg='添加成功!', status=True)
        except:
            print(traceback.format_exc())
            return public.returnResult(code=0, msg='添加失败!', status=False)

    def _check_user(self, user: str) -> bool:
        """
        检查用户是否存在
        :param user: 用户名
        :return: bool
        """
        tmpList = public.readFile('/etc/passwd').split("\n")
        for ul in tmpList:
            tmp = ul.split(':')
            if len(tmp) < 6: continue
            if tmp[0] == user: return False
        return True

    def _check_group(self, group: str) -> bool:
        """
        检查用户组是否存在
        :param group: 用户组
        :return: bool
        """
        tmpList = public.readFile('/etc/group').split("\n")
        for gl in tmpList:
            tmp = gl.split(':')
            if len(tmp) < 3: continue
            if tmp[0] == group: return True
        return False

    # --------------------添加用户 End------------------------

    # --------------------修改用户密码 Start------------------------
    def edit_user_pwd(self, user: str, pwd: str) -> Dict[str, Any]:
        try:
            if not user: return public.returnResult(code=0, msg='用户名不能为空!', status=False)
            if not pwd: return public.returnResult(code=0, msg='密码不能为空!', status=False)
            if self._check_user(user): return public.returnResult(code=0, msg='用户不存在!', status=False)
            public.ExecShell("echo \"" + user + ":" + pwd + "\" | chpasswd")
            return public.returnResult(code=1, msg='修改成功!', status=True)
        except:
            return public.returnResult(code=0, msg='修改失败!', status=False)

    # --------------------修改用户密码 End------------------------

    # --------------------修改用户组 Start------------------------
    def edit_user_group(self, user: str, group: str) -> Dict[str, Any]:
        try:
            if not user: return public.returnMsg(False, '用户名不能为空!')
            if not group: return public.returnMsg(False, '用户组不能为空!')
            if self._check_user(user): return public.returnMsg(False, '用户不存在!')
            if not self._check_group(group): self.add_group(group)
            r = public.ExecShell("usermod -g " + group + " " + user)
            if r[1].find('usermod:') != -1: return public.returnMsg(False, r[1])
            return public.returnResult(code=1, msg='修改成功!', status=True)
        except:
            return public.returnResult(code=0, msg='修改失败!', status=False)

    # --------------------修改用户组 End------------------------

    # --------------------修改用户备注 Start------------------------
    def edit_user_ps(self, user: str, ps: str) -> Dict[str, Any]:
        try:
            if not user: return public.returnResult(code=0, msg='用户名不能为空!', status=False)
            if self._check_user(user): return public.returnResult(code=0, msg='用户不存在!', status=False)
            r = public.ExecShell("usermod -c " + ps + " " + user)
            if r[1].find('usermod:') != -1: return public.returnResult(code=0, msg=r[1], status=False)
            return public.returnResult(code=1, msg='修改成功!', status=True)
        except:
            return public.returnResult(code=0, msg='修改失败!', status=False)

    # --------------------修改用户备注 End------------------------

    # --------------------修改用户备注 Start------------------------
    def edit_user_status(self, user: str, status: int):
        try:
            if not user: return public.returnResult(code=0, msg='用户名不能为空!', status=False)
            if self._check_user(user): return public.returnResult(code=0, msg='用户不存在!', status=False)
            if int(status) == 1:
                r = public.ExecShell("usermod -L " + user)
            else:
                r = public.ExecShell("usermod -U " + user)
            if r[1].find('usermod:') != -1: return public.returnResult(code=0, msg=r[1], status=False)
            return public.returnResult(code=1, msg='修改成功!', status=True)
        except:
            return public.returnResult(code=0, msg='修改失败!', status=False)

    # --------------------修改用户备注 End------------------------

    # --------------------修改用户登录Shell Start------------------------
    def edit_user_login_shell(self, user: str, login_shell: str) -> Dict[str, Any]:
        try:
            if not user: return public.returnResult(code=0, msg='用户名不能为空!', status=False)
            if self._check_user(user): return public.returnResult(code=0, msg='用户不存在!', status=False)
            r = public.ExecShell("usermod -s " + login_shell + " " + user)
            if r[1].find('usermod:') != -1: return public.returnResult(code=0, msg=r[1], status=False)
            return public.returnResult(code=1, msg='修改成功!', status=True)
        except:
            return public.returnResult(code=0, msg='修改失败!', status=False)

    # --------------------修改用户登录Shell End------------------------

    # --------------------修改用户家目录 Start------------------------
    def edit_user_home(self, user: str, home: str) -> Dict[str, Any]:
        try:
            if not user: return public.returnResult(code=0, msg='用户名不能为空!', status=False)
            if self._check_user(user): return public.returnResult(code=0, msg='用户不存在!', status=False)
            r = public.ExecShell("usermod -d " + home + " " + user)
            if r[1].find('usermod:') != -1: return public.returnResult(code=0, msg=r[1], status=False)
            return public.returnResult(code=1, msg='修改成功!', status=True)
        except:
            return public.returnResult(code=0, msg='修改失败!', status=False)

    # --------------------修改用户家目录 End------------------------

    # --------------------获取用户信息 Start------------------------
    def get_user_info(self, user: str) -> Dict[str, Any]:
        try:
            user = user.strip()
            tmpList = public.readFile('/etc/passwd').split("\n")
            userInfo = {}
            for ul in tmpList:
                tmp = ul.split(':')
                if len(tmp) < 6: continue
                if tmp[0] == user:
                    userInfo['username'] = tmp[0]
                    userInfo['uid'] = tmp[2]
                    userInfo['gid'] = tmp[3]
                    userInfo['group'] = self._get_group_name(tmp[3])
                    userInfo['ps'] = self._get_user_ps(tmp[0], tmp[4])
                    userInfo['home'] = tmp[5]
                    userInfo['login_shell'] = tmp[6]
                    break
            return public.returnResult(code=1, data=userInfo, msg='获取用户信息成功!', status=True)
        except:
            print(traceback.format_exc())
            return public.returnResult(code=0, msg='获取用户信息失败!', status=False)

    # --------------------添加用户组 Start------------------------
    def add_group(self, group: str) -> Dict[str, Any]:
        """
        添加用户组
        :param group: 用户组
        :return: dict
        """
        try:
            if not group: return public.returnResult(code=0, msg='用户组不能为空!', status=False)
            if self._check_group(group): return public.returnResult(code=0, msg='用户组已存在!', status=False)
            r = public.ExecShell("groupadd " + group)
            if r[1].find('groupadd:') != -1: return public.returnResult(code=0, msg=r[1], status=False)
            return public.returnResult(code=1, msg='添加成功!', status=True)
        except:
            return public.returnResult(code=0, msg='添加失败!', status=False)

    # --------------------添加用户组 End------------------------

    # --------------------删除用户组 Start------------------------
    def remove_group(self, group: str) -> Dict[str, Any]:
        """
        删除用户组
        :param group: 用户组
        :return: dict
        """
        try:
            if not group: return public.returnResult(code=0, msg='用户组不能为空!', status=False)
            if not self._check_group(group): return public.returnResult(code=0, msg='用户组不存在!', status=False)
            r = public.ExecShell("groupdel " + group)
            if r[1].find('groupdel:') != -1: return public.returnResult(code=0, msg=r[1], status=False)
            return public.returnResult(code=1, msg='删除成功!', status=True)
        except:
            return public.returnResult(code=0, msg='删除失败!', status=False)

    # --------------------删除用户组 End------------------------

    # --------------------修改用户组名称 Start------------------------
    def edit_group_name(self, group: str, new_group: str) -> Dict[str, Any]:
        """
        修改用户组名称
        :param group: 用户组
        :param new_group: 新用户组
        :return: dict
        """
        try:
            if not group: return public.returnResult(code=0, msg='用户组不能为空!', status=False)
            if not new_group: return public.returnResult(code=0, msg='新用户组不能为空!', status=False)
            if not self._check_group(group): return public.returnResult(code=0, msg='用户组不存在!', status=False)
            if self._check_group(new_group): return public.returnResult(code=0, msg='新用户组已存在!', status=False)
            r = public.ExecShell("groupmod -n " + new_group + " " + group)
            if r[1].find('groupmod:') != -1: return public.returnResult(code=0, msg=r[1], status=False)
            return public.returnResult(code=1, msg='修改成功!', status=True)
        except:
            return public.returnResult(code=0, msg='修改失败!', status=False)

    # --------------------获取用户组列表 End------------------------

    # --------------------获取用户组信息 Start------------------------
    def get_group_info(self, group) -> Dict[str, Any]:
        """
        获取用户组信息
        :param group: 用户组
        :return: dict
        """
        try:
            group = group.strip()
            tmpList = public.readFile('/etc/group').split("\n")
            groupInfo = {}
            for gl in tmpList:
                tmp = gl.split(':')
                if len(tmp) < 3: continue
                if tmp[0] == group:
                    groupInfo['group'] = tmp[0]
                    groupInfo['gid'] = tmp[2]
                    break
            return public.returnResult(code=1, data=groupInfo, msg='获取用户组信息成功!', status=True)
        except:
            return public.returnResult(code=0, msg='获取用户组信息失败!', status=False)

    # --------------------获取用户组信息 End------------------------

    # --------------------获取用户组信息 Start------------------------
    def get_group_user(self, group: str) -> Dict[str, Any]:
        """
        获取用户组用户
        :param group: 用户组
        :return: dict
        """
        try:
            group = group.strip()
            tmpList = self.get_user_list()['data']
            userList = []
            for ul in tmpList:
                if ul['group'] == group:
                    userList.append(ul['username'])
            return public.returnResult(code=1, data=userList, msg='获取用户组用户成功!', status=True)
        except:
            return public.returnResult(code=0, msg='获取用户组用户失败!', status=False)

    # --------------------获取用户组信息 End------------------------

    # --------------------获取用户组信息 Start------------------------
    def get_user_group(self, user: str) -> Dict[str, Any]:
        """
        获取用户组用户
        :param user: 用户
        :return: dict
        """
        try:
            user = user.strip()
            tmpList = self.get_user_list()['data']
            groupList = []
            for gl in tmpList:
                if gl['username'] == user:
                    groupList.append(gl['group'])
            return public.returnResult(code=1, data=groupList, msg='获取用户组用户成功!', status=True)
        except:
            return public.returnResult(code=0, msg='获取用户组用户失败!', status=False)

    # --------------------获取用户组信息 End------------------------

    # --------------------修改用户权限 Start------------------------
    def edit_user_permission(self, user: str, permission: str) -> Dict[str, Any]:
        """
        修改用户权限
        :param user:
        :param permission:
        :return:
        """
        try:
            if not user: return public.returnResult(code=0, msg='用户名不能为空!', status=False)
            if self._check_user(user): return public.returnResult(code=0, msg='用户不存在!', status=False)
            r = public.ExecShell("chmod -R " + permission + " /home/" + user)
            if r[1].find('chmod:') != -1: return public.returnResult(code=0, msg=r[1], status=False)
            return public.returnResult(code=1, msg='修改成功!', status=True)
        except:
            return public.returnResult(code=0, msg='修改失败!', status=False)

    # --------------------修改用户权限 End------------------------

    # --------------------修改用户组权限 Start------------------------
    def edit_group_permission(self, group: str, permission: str) -> Dict[str, Any]:
        """
        修改用户组权限
        :param group:
        :param permission:
        :return:
        """
        try:
            if not group: return public.returnResult(code=0, msg='用户组不能为空!', status=False)
            if not self._check_group(group): return public.returnResult(code=0, msg='用户组不存在!', status=False)
            r = public.ExecShell("chmod -R " + permission + " /home/" + group)
            if r[1].find('chmod:') != -1: return public.returnResult(code=0, msg=r[1], status=False)
            return public.returnResult(code=1, msg='修改成功!', status=True)
        except:
            return public.returnResult(code=0, msg='修改失败!', status=False)

    def edit_user_name(self, user: str, new_user: str) -> Dict[str, Any]:
        try:
            user = user.strip()
            new_user = new_user.strip()
            r = public.ExecShell("usermod -l " + new_user + " " + user)
            if r[1].find('usermod:') != -1: return public.returnResult(code=0, msg=r[1], status=False)
            return public.returnResult(code=1, msg='修改成功!', status=True)
        except:
            return public.returnResult(code=0, msg='修改失败!', status=False)


class User(object):
    def __init__(self):
        self.real_user = RealUser()

    # 获取用户列表
    def get_user_list(self, get):
        search = ''
        if hasattr(get, 'search'):
            search = get.search
        return self.real_user.get_user_list(search)

    # 删除用户
    def remove_user(self, get):
        if not hasattr(get, 'user'):
            return public.returnMsg(False, '用户不存在!')
        user = get.user.strip()
        return self.real_user.remove_user(user)

    # 添加用户
    def add_user(self, get):
        if not hasattr(get, 'user'):
            return public.returnMsg(False, '用户名不能为空!')
        if not hasattr(get, 'pwd'):
            return public.returnMsg(False, '密码不能为空!')
        if not hasattr(get, 'group'):
            return public.returnMsg(False, '用户组不能为空!')
        user = get.user.strip()
        pwd = get.pwd.strip()
        group = get.group.strip()
        return self.real_user.add_user(user, pwd, group)

    # 修改用户密码
    def edit_user_pwd(self, get):
        if not hasattr(get, 'user'):
            return public.returnMsg(False, '用户名不能为空!')
        if not hasattr(get, 'pwd'):
            return public.returnMsg(False, '密码不能为空!')
        user = get.user.strip()
        pwd = get.pwd.strip()
        return self.real_user.edit_user(user, pwd)

    # 修改用户的用户组
    def edit_user_group(self, get):
        if not hasattr(get, 'user'):
            return public.returnMsg(False, '用户名不能为空!')
        if not hasattr(get, 'group'):
            return public.returnMsg(False, '用户组不能为空!')
        user = get.user.strip()
        group = get.group.strip()
        return self.real_user.edit_group(user, group)

    # 修改用户备注
    def edit_user_ps(self, get):
        if not hasattr(get, 'user'):
            return public.returnMsg(False, '用户名不能为空!')
        user = get.user.strip()
        return self.real_user.edit_user_ps(user)

    # 添加用户组
    def add_group(self, get):
        if not hasattr(get, 'group'):
            return public.returnMsg(False, '用户组不能为空!')
        group = get.group.strip()
        return self.real_user.add_group(group)

    # 删除用户组
    def remove_group(self, get):
        if not hasattr(get, 'group'):
            return public.returnMsg(False, '用户组不能为空!')
        group = get.group.strip()
        return self.real_user.remove_group(group)

    # 修改用户组名称
    def edit_group_name(self, get):
        if not hasattr(get, 'group'):
            return public.returnMsg(False, '用户组不能为空!')
        if not hasattr(get, 'new_group'):
            return public.returnMsg(False, '新用户组不能为空!')
        group = get.group.strip()
        new_group = get.new_group.strip()
        return self.real_user.edit_group_name(group, new_group)

    # 获取用户组列表
    def get_group_list(self, get):
        return self.real_user.get_group_list()

    # 获取用户组信息
    def get_group_info(self, get):
        if not hasattr(get, 'group'):
            return public.returnMsg(False, '用户组不能为空!')
        group = get.group.strip()
        return self.real_user.get_group_info(group)

    # 获取用户组用户
    def get_group_user(self, get):
        if not hasattr(get, 'group'):
            return public.returnMsg(False, '用户组不能为空!')
        group = get.group.strip()
        return self.real_user.get_group_user(group)

    # 获取用户组用户
    def get_user_group(self, get):
        if not hasattr(get, 'user'):
            return public.returnMsg(False, '用户不能为空!')
        user = get.user.strip()
        return self.real_user.get_user_group(user)

    # 修改用户备注
    def edit_ps(self, get):
        if not hasattr(get, 'user'):
            return public.returnMsg(False, '用户名不能为空!')
        if not hasattr(get, 'ps'):
            return public.returnMsg(False, '备注不能为空!')
        user = get.user.strip()
        ps = get.ps.strip()
        return self.real_user.edit_ps(user, ps)

    # 修改用户登录Shell
    def edit_user_login_shell(self, get):
        if not hasattr(get, 'user'):
            return public.returnMsg(False, '用户名不能为空!')
        if not hasattr(get, 'login_shell'):
            return public.returnMsg(False, '登录Shell不能为空!')
        user = get.user.strip()
        login_shell = get.login_shell.strip()
        return self.real_user.edit_login_shell(user, login_shell)

    # 修改用户家目录
    def edit_user_home(self, get):
        if not hasattr(get, 'user'):
            return public.returnMsg(False, '用户名不能为空!')
        if not hasattr(get, 'home'):
            return public.returnMsg(False, '家目录不能为空!')
        user = get.user.strip()
        home = get.home.strip()
        return self.real_user.edit_home(user, home)

    # 修改用户权限
    def edit_user_permission(self, get):
        if not hasattr(get, 'user'):
            return public.returnMsg(False, '用户名不能为空!')
        if not hasattr(get, 'permission'):
            return public.returnMsg(False, '权限不能为空!')
        user = get.user.strip()
        permission = get.permission.strip()
        return self.real_user.edit_user_permission(user, permission)

    #   修改用户组权限
    def edit_group_permission(self, get):
        if not hasattr(get, 'group'):
            return public.returnMsg(False, '用户组不能为空!')
        if not hasattr(get, 'permission'):
            return public.returnMsg(False, '权限不能为空!')
        group = get.group.strip()
        permission = get.permission.strip()
        return self.real_user.edit_group_permission(group, permission)

    def edit_user_name(self, get):
        if not hasattr(get, 'user'):
            return public.returnMsg(False, '用户名不能为空!')
        if not hasattr(get, 'new_user'):
            return public.returnMsg(False, '新用户名不能为空!')
        user = get.user.strip()
        new_user = get.new_user.strip()
        return self.real_user.edit_user_name(user, new_user)


if __name__ == "__main__":
    user = User()
    print(user.get_user_list(public.to_dict_obj({})))

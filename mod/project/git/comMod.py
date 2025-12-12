# coding: utf-8
# -------------------------------------------------------------------
# Git管理器
# -------------------------------------------------------------------
# Author: csj <csj@bt.cn>
# -------------------------------------------------------------------
import sys,base64,os

if "/www/server/panel/class" not in sys.path:
    sys.path.insert(0, "/www/server/panel/class")

if '/www/server/panel' not in sys.path:
    sys.path.insert(0, '/www/server/panel')

import public


#------------------------------
# git管理工具
#------------------------------
class main():
    _ssh_pub = '/root/.ssh/id_ed25519.pub'
    _ssh_key = '/root/.ssh/id_ed25519'

    def __init__(self):
        pass

    def get_ssh_key(self, get=None):
        """
        获取ssh key 公钥，不存在即创建
        
        :param get: 请求参数对象（可选）
        :return: 成功返回SSH公钥，失败返回错误信息
        """
        # 缺失密钥则创建新的
        if not os.path.exists(self._ssh_key) or not os.path.exists(self._ssh_pub):
            result = public.ExecShell(
                f"ssh-keygen -t ed25519 "
                f"-f {self._ssh_key} "
                f"-N \"\" "
                f"-C \"\" "
            )[0]

            if "The key's randomart image is:" not in result:
                return public.ReturnMsg(False,"The aapanel_key key generation failed. Please try again: {} ".format(result))

            # 修正密钥文件权限
            os.chmod(self._ssh_key, 0o600)
            os.chmod(self._ssh_pub, 0o644)

            ssh_pub = public.readFile(self._ssh_pub)

            # 添加到authorized_keys
            if ssh_pub:
                public.writeFile('/root/.ssh/authorized_keys', ssh_pub, 'a+')
        else:
            ssh_pub = public.readFile(self._ssh_pub)

        ssh_pub = ssh_pub.strip()
        return public.ReturnMsg(True,ssh_pub)

    def get_site_git(self, get):
        """
        获取网站绑定的git仓库信息
        """
        site_name = get.get('site_name',"")
        if not site_name:
            return public.ReturnMsg(False,"网站名称不能为空")
        
        # 查询git仓库信息
        git_manager = public.M('git_manager').where("type = 'site' and type_parm = ?", (site_name,)).find()
        if not git_manager:
            return public.ReturnMsg(False,"git仓库不存在")
        
        return public.return_data(True,data=git_manager)

    def get_git_info(self, get):
        """
        获取本机git信息
        """
        res_data = {
            "ssh_key": self.get_ssh_key(),
            "webhook_install": self._check_webhook_install(),
        }

        return public.return_data(True,data=res_data)
    def _check_webhook_install(self):
        """
        检查webhook插件是否已安装
        
        :param get: 请求参数对象（可选）
        :return: 已安装返回True，未安装返回False
        """
        import panelPlugin
        plu_obj = panelPlugin.panelPlugin()

        webhook_status = plu_obj.get_soft_find(public.to_dict_obj({'sName':'webhook'}))
        if not webhook_status['status']:
            return False
        return True

    def add_gitmanager_site(self, get):
        """
        SSH KEY克隆git仓库并创建网站绑定
        
        :param get: 请求参数，包含site_id, site_path, repo, branch, coverage_data, deploy_script, site_name
        :return: 成功返回创建成功信息，失败返回错误信息
        """
        # 校验参数
        site_id = get.get('site_id',"")
        site_path = get.get('site_path',"")
        repo = get.get('repo',"")
        branch = get.get('branch',"")
        coverage_data = get.get('coverage_data',"")
        deploy_script = get.get('deploy_script',"")
        site_name = get.get('site_name',"")

        if not site_id or not site_path or not repo or not branch:
            return public.ReturnMsg(False,"所需参数不能为空")

        # 统一预处理Git仓库
        success, error_msg = self._prepare_git_repo(repo)
        if not success:
            return public.ReturnMsg(False, f"仓库预处理失败: {error_msg}")

        try:
            # 克隆
            clone_cmd = (
                f"git clone -b {get.branch} "
                f"{get.repo} "
                f"{get.site_path} "
            )
            clone_result = public.ExecShell(clone_cmd, timeout=180)
            if clone_result == "Timed out":
                return public.ReturnMsg(False,f"git克隆操作超时，请检查仓库地址和ssh密钥状态！")

            # 处理权限
            self._fix_file_permission(site_path)

            webhookname,webhook_url = self._create_webhook(get.site_id, site_name, branch)
            if not webhookname or not webhook_url:
                return public.ReturnMsg(False,f"为项目创建webhook失败,若您是卸载webhook后重装，请到首页重启面板后再！")
            # 记录git仓库信息
            public.M('git_manager').insert({
                "repo_url": repo,
                "branch": branch,
                "type": "site",
                "type_parm": site_name,
                "webhook_name": webhookname,
                "deploy_script": deploy_script,
                "webhook_url": webhook_url,
                "args": "{}"
            })

            public.set_module_logs(f'Git-Tools', 'git_create_website')
            return public.ReturnMsg(True,"项目创建成功!")
        except Exception as e:
            return public.ReturnMsg(False,f"项目创建失败: {str(e)}")

    def update_gitmanager_site(self,get):
        """
        更新git网站部署脚本和分支
        注意：如果修改了分支，会重新部署一次新分支
        
        :param git_manager_id: git网站id
        :param deploy_script: 部署脚本（可选）
        :param branch: 分支名称（可选）
        :return: 
        """
        git_manager_id = get.get('git_manager_id','')
        if not git_manager_id:
            return public.ReturnMsg(False,'git_manager_id参数不能为空.')
        
        # 获取现有的git管理记录
        git_manager = public.M('git_manager').where("id=?", (git_manager_id,)).find()
        if not git_manager:
            return public.ReturnMsg(False,'找不到对应的git管理记录.')
        
        # 获取要更新的参数
        deploy_script = get.get('deploy_script','')
        branch = get.get('branch','')
        
        # 判断是否需要更新
        if branch == git_manager['branch'] and deploy_script == git_manager['deploy_script']:
            return public.ReturnMsg(True,'保存成功.')

        # 构建更新数据
        update_data = {
            'deploy_script': deploy_script,
            'branch': branch
        }
        
        public.M('git_manager').where("id=?", (git_manager_id,)).update(update_data)
        # 执行分支切换
        switch_result = self.git_rollback(public.to_dict_obj({
            'git_manager_id': git_manager_id,
            'branch': branch,
            'commit': ''  # 只切换分支，不指定commit
        }))
        # 如果切换失败，直接返回失败信息
        if not switch_result['status']:
            return switch_result
        
        return public.ReturnMsg(True,'修改成功.')

    def git_rollback(self, get):
        """
        切换到 指定分支、或者回滚至 指定commit
        
        :param git_manager_id: git网站id
        :param branch: 指定分支
        :param commit: 指定commit（可选）
        :return: 
        """
        # 参数验证
        git_manager_id = get.get('git_manager_id', '')
        if not git_manager_id:
            return public.ReturnMsg(False, 'git_manager_id参数不能为空.')
        
        branch = get.get('branch', '')
        if not branch:
            return public.ReturnMsg(False, 'branch参数不能为空.')
        
        commit = get.get('commit', '')  # commit 是可选参数
        
        # 获取git管理记录
        git_manager = public.M('git_manager').where("id=?", (git_manager_id,)).find()
        if not git_manager:
            return public.ReturnMsg(False, '找不到对应的git管理记录.')
        
        #对webhook_name进行base64编码
        webhook_name = base64.b64encode(git_manager['webhook_name'].encode('utf-8')).decode('utf-8')
        
        # 调用部署脚本
        deploy_script = f"btpython /www/server/panel/mod/project/git/scripts/deploy.py {webhook_name} {branch} {commit}"
        
        # 执行命令
        public.ExecShell(deploy_script)
        return public.ReturnMsg(True, '切换分支任务已执行.')

    def _create_webhook(self, site_id,site_name, branch):
        """
        创建git项目的webhook
        
        :param site_id: 项目id
        :param site_name: 项目名称
        :param branch: 分支名称
        :return: webhook_name,webhook_url
        """
        webhook_name = f"{site_name}_{site_id}_{branch}_deploy"
        webhook_param = base64.b64encode(webhook_name.encode('utf-8')).decode('utf-8')
        

        try:
            from plugin.webhook.webhook_main import webhook_main
        except Exception as e:
            return "",""
        webhook_obj = webhook_main()

        # 绑定git部署脚本
        ok = webhook_obj.AddHook(public.to_dict_obj({'title':f"{webhook_name}","shell": "btpython /www/server/panel/mod/project/git/scripts/deploy.py $@"}))
        if not ok['status']:
            return "",""
        hook_list = webhook_obj.GetList(public.to_dict_obj({'p':1,'limit':1000}))
        for hook in hook_list['list']:
            if hook['title'] == webhook_name:
                webhook_url = f"{public.getPanelAddr()}/hook?access_key={hook['access_key']}&param={webhook_param}"
                return webhook_name,webhook_url
        
        return "",""

    # 统一的Git仓库预处理方法（正则表达式优化版）
    def _prepare_git_repo(self, repo_url):
        """
        统一的Git仓库预处理方法 - 使用正则表达式优化SSH解析
        
        1. 验证仓库地址格式
        2. 如果是SSH仓库，添加主机到known_hosts
        3. 返回处理结果和错误信息
        
        :param repo_url: Git仓库地址
        :return: (success, error_msg)
        """
        import re
        from urllib.parse import urlparse
        
        if not repo_url:
            return False, "仓库地址不能为空"
        
        # HTTP/HTTPS仓库 - 使用urlparse专业解析
        if repo_url.startswith(("http://", "https://")):
            try:
                parsed = urlparse(repo_url)
                if not parsed.hostname or '.' not in parsed.hostname:
                    return False, "HTTP格式的仓库地址需要包含有效的域名"
                return True, None
            except Exception as e:
                return False, f"HTTP仓库地址解析失败: {str(e)}"
        
        # SSH仓库 - 使用正则表达式智能解析
        elif repo_url.startswith(("ssh://", "git@")):
            try:
                host, port = None, 22
                
                # ssh:// 格式：使用urlparse解析
                if repo_url.startswith("ssh://"):
                    parsed = urlparse(repo_url)
                    host = parsed.hostname
                    port = parsed.port or 22
                
                # git@ 格式：使用正则表达式解析
                elif repo_url.startswith("git@"):
                    # 验证基本格式
                    if ':' not in repo_url:
                        return False, "SSH格式的仓库地址需要包含冒号分隔符"
                    
                    # 强大的正则表达式统一处理所有git@格式
                    # 匹配：git@host:path, git@host:port/path, git@host:port:path
                    # 核心模式：捕获主机名，然后检查后面是否有端口
                    pattern = r'^git@([^:]+):(?:(\d+)(?::|/))?(.+)$'
                    match = re.search(pattern, repo_url)
                    
                    if match:
                        host = match.group(1)  # 主机地址
                        port_str = match.group(2)  # 端口（可选）
                        if port_str and port_str.isdigit():
                            port = int(port_str)
                    
                if not host:
                    return False, "无法解析SSH仓库地址中的主机信息"
                
                if port != 22:
                    check_cmd = f'ssh-keygen -F "[{host}]:{port}" 2>/dev/null'
                else:
                    check_cmd = f'ssh-keygen -F "{host}" 2>/dev/null'

                result = public.ExecShell(check_cmd)
                if not result or not result[0].strip():
                    keyscan_cmd = f"ssh-keyscan -p {port} {host} >> ~/.ssh/known_hosts 2>/dev/null"
                    public.ExecShell(keyscan_cmd)
                return True, None
                
            except Exception as e:
                public.print_log(f"处理SSH仓库地址失败: {str(e)}")
                return False, f"SSH仓库地址处理失败: {str(e)}"
        
        else:
            return False, "不支持的仓库地址格式，请使用SSH或HTTP(S)格式"

    def test_ssh(self,repo_host):
        """
        SSH密钥测试连接
        
        :param repo_host: 仓库主机地址
        :return: 连接成功返回True，失败返回False
        """
        # 首先预处理仓库（添加SSH主机到known_hosts）
        success, error_msg = self._prepare_git_repo(repo_host)
        if not success:
            return False

        PLATFORM_DOMAINS = ["github.com", "gitlab.com", "gitee.com", "bitbucket.org", "coding.net"]
        repo_url = repo_host

        if repo_url.startswith("ssh://"):
            core_part = repo_url.lstrip("ssh://")
        elif repo_url.startswith("git@"):
            core_part = repo_url
        else:
            return False

        try:
            # 区分仓库类型
            is_platform_repo = False # 默认为自建仓库
            for repo in PLATFORM_DOMAINS:
                if repo in repo_url:
                    repo_url = repo_url.split(':')[0]
                    is_platform_repo = True
                    break

            # 处理自建仓库
            port = None
            if not is_platform_repo:
                host_port_part = core_part.split("git@")[1].split("/")[0]
                base_host = host_port_part.split(":")[0]

                # 分离端口和地址，保留 git@ 前缀
                repo_url = f"git@{base_host}"
                if ":" in host_port_part:
                    _, port = host_port_part.split(":", 1)
                    if not port.isdigit():
                        return False
        except Exception:
            return False

        cmd_parts = ["ssh -T", "-o BatchMode=yes","-o ConnectTimeout=5","-o PasswordAuthentication=no"]
        if port:
            cmd_parts.append(f"-p {port}")
        cmd_parts.append(repo_url)
        test_cmd = " ".join(cmd_parts)

        stdout, stderr = public.ExecShell(test_cmd)
        combined = (stdout + stderr).lower()

        return any(s in combined for s in [
            "successfully authenticated",
            "welcome to gitlab",
            "welcome to bitbucket",
            "you've successfully authenticated",
            "Welcome"
        ])
    
    def get_repo_branch(self,get):
        """
        获取仓库分支列表
        
        :param get: 请求参数，包含repo参数
        :param force: 是否强制刷新，默认False
        :return: 成功返回分支列表，失败返回错误信息
        """
        # 检查参数
        repo = get.get('repo','')
        if not repo:
            return public.ReturnMsg(False,'repo参数不能为空.')  
        
        # 统一预处理Git仓库
        success, error_msg = self._prepare_git_repo(repo)
        if not success:
            return public.ReturnMsg(False, f"仓库预处理失败: {error_msg}")
        
        #缓存分支列表，默认缓存1天
        cache_key = f"git_branch_{repo}"
        from BTPanel import cache
        if get.get('force',0) != 1:
            data = cache.get(cache_key)
            if data:
                return public.return_data(True,data=data)

        branch_cmd = f"git ls-remote --heads {repo}"
        branch_result = public.ExecShell(branch_cmd)
        if branch_result == "Timed out":
            return public.ReturnMsg(False,f"git分支列表操作超时，请检查仓库地址和ssh密钥状态！")

        branches = []
        for line in branch_result[0].splitlines():
            branch = line.split('/')[-1]
            branches.append(branch)

        cache.set(cache_key, branches, 86400)
        
        return public.return_data(True,data=branches)

    # 获取当前网站的部署记录
    def get_deploy_records(self, get):
        """
        获取当前网站的部署记录，支持分页和查询
        
        :param git_manager_id: git网站id
        :param p: 页码，默认为1
        :param limit: 每页记录数，默认为15
        :param query: 查询关键字，可选，支持搜索站点名称、分支、commit等
        :return: 分页后的部署记录
        """
        try:
            git_manager_id = get.get('git_manager_id','')
            if not git_manager_id:
                return public.ReturnMsg(False,'git_manager_id参数不能为空.')

            # 分页参数
            p = 1
            limit = 15
            if 'p' in get: p = int(get.p)
            if 'limit' in get: limit = int(get.limit)

            where = 'git_manager_id=?'
            params = (git_manager_id,)

            sql = public.M('git_deploy_logs')
            
            # 获取分页信息
            page_data = public.get_page(sql.where(where, params).count(), p, limit)
            
            # 获取分页后的记录
            records = sql.where(where, params).order('id desc').limit('{},{}'.format(page_data['shift'], page_data['row'])).select()
            page_data['data'] = records
            public.set_module_logs(f'Git-Tools', 'get_deploy_records')
            return page_data
            
        except Exception as e:
            public.print_log(f"获取部署记录失败: {str(e)}")
            return public.ReturnMsg(False, f'获取部署记录失败: {str(e)}')

    def get_gitmanager(self,get):
        """
        获取git信息
        
        :param get: 请求参数，包含git_manager_id
        :return: 成功返回git管理信息，失败返回错误信息
        """
        git_manager_id = get.get('git_manager_id','')
        if not git_manager_id:
            return public.ReturnMsg(False,'git_manager_id参数不能为空.')

        sites = public.M('git_manager').where("id=?", (git_manager_id,)).find()
        if not sites:
            return public.ReturnMsg(False,'查询脚本信息失败.')

        return public.return_data(True,data=sites)

    def del_site_git(self, get):
        """
        删除Git网站
        
        :param get: 请求参数，包含site_name
        :return: 成功返回删除成功信息，失败返回错误信息
        """
        site_name = get.get('site_name','')
        if not site_name:
            return public.ReturnMsg(False,'site_name不能为空')

        # 删除数据库中的记录, 暂时不删除配置
        git_manager = public.M('git_manager').where("type_parm=?", (site_name,)).find()
        if not git_manager:
            return public.ReturnMsg(False,'查询git网站信息失败.')   

        public.M('git_manager').where("type_parm=?", (site_name,)).delete()
        public.M('git_deploy_logs').where("site_name=?", (site_name,)).delete()

        #删除webhook
        try:
            from plugin.webhook.webhook_main import webhook_main
        except Exception as e:
            return public.ReturnMsg(False,'webhook插件未安装.')
        webhook_obj = webhook_main()
        hook_list = webhook_obj.GetList(public.to_dict_obj({'p':1,'limit':1000}))['list']
        for hook in hook_list:
            if hook['title'] == git_manager['webhook_name']:
                del_res = webhook_obj.DelHook(public.to_dict_obj({'access_key': hook['access_key']}))
                if not del_res['status']:
                    return public.ReturnMsg(False,'移除webhook失败.')
        return public.ReturnMsg(True,"删除成功")

    def _fix_file_permission(self, path):
        """
        修正指定路径的文件权限
        - 所有目录设置为 755 权限，所有者为 www:www
        - 所有文件设置为 644 权限，所有者为 www:www
        
        :param path: 要处理的根目录路径
        :return: 成功返回True，失败返回False
        """
        if not os.path.exists(path):
            return False

        try:
            chown_cmd = f"chown -R www:www {path}"
            public.ExecShell(chown_cmd)

            for root, dirs, files in os.walk(path):
                # 处理目录权限（755）
                for dir_name in dirs:
                    dir_path = os.path.join(root, dir_name)
                    os.chmod(dir_path, 0o755)

                # 处理文件权限（644）
                for file_name in files:
                    file_path = os.path.join(root, file_name)
                    os.chmod(file_path, 0o644)

            return True
        except Exception as e:
            return False

    def get_webhook_log(self,get):
        """
        获取网站webhook日志
        
        :param get: 请求参数，包含git_manager_id
        :return: 成功返回日志内容，失败返回错误信息
        """
        git_manager = public.M('git_manager').where('id=?', (get.git_manager_id,)).find()
        if not git_manager:
            return public.ReturnMsg(False,'"git_manager_id"不能为空.')

        # 获取webhook url
        try:
            from plugin.webhook.webhook_main import webhook_main
        except Exception as e:
            return public.ReturnMsg(False,'webhook插件未安装.')
        webhook_obj = webhook_main()

        # 判断是否存在
        hook_list = webhook_obj.GetList(public.to_dict_obj({'p':1,'limit':1000}))
        for hook in hook_list['list']:
            if hook['title'] == git_manager['webhook_name']:
                log_content = public.readFile(hook['log_path'])
                if not log_content:
                    log_content = '暂无日志记录'
                return public.ReturnMsg(True,log_content)
        return public.ReturnMsg(True,'')

    # 清除部署日志
    def clear_webhook_log(self,get):
        """
        清除指定git_manager_id的webhook日志
        :param get: 请求参数，包含git_manager_id
        :return: 成功返回True，失败返回False
        """
        git_manager_id = get.get('git_manager_id','')
        if not git_manager_id:
            return public.ReturnMsg(False,'git_manager_id参数不能为空.')

        git_manager = public.M('git_manager').where('id=?', (git_manager_id,)).find()
        if not git_manager:
            return public.ReturnMsg(False,'"git_manager_id"不能为空.')

        # 获取webhook url
        try:
            from plugin.webhook.webhook_main import webhook_main
        except Exception as e:
            return public.ReturnMsg(False,'webhook插件未安装.')
        webhook_obj = webhook_main()

        # 判断是否存在
        hook_list = webhook_obj.GetList(public.to_dict_obj({'p':1,'limit':1000}))['list']
        for hook in hook_list:
            if hook['title'] == git_manager['webhook_name']:
                public.writeFile(hook['log_path'], '')
                return public.ReturnMsg(True,"清除成功!")
        return public.ReturnMsg(True,"未找到对应的webhook日志文件")
    
    def refresh_webhook(self, get):
        """
        刷新指定git_manager_id的webhook url
        :param get: 请求参数，包含git_manager_id
        :return: 成功返回True，失败返回False
        """
        git_manager_id = get.get('git_manager_id','')
        if not git_manager_id:
            return public.ReturnMsg(False,'git_manager_id参数不能为空.')

        git_manager = public.M('git_manager').where('id=? and type="site"', (git_manager_id,)).find()
        if not git_manager:
            return public.ReturnMsg(False,'git_manager获取失败.')

        try:
            from plugin.webhook.webhook_main import webhook_main
        except Exception as e:
            return public.ReturnMsg(False,'webhook插件未安装.')
        webhook_obj = webhook_main()
        hook_list = webhook_obj.GetList(public.to_dict_obj({'p':1,'limit':1000}))['list']
        for hook in hook_list:
            if hook['title'] == git_manager['webhook_name']:
                # 删除旧hook
                del_res = webhook_obj.DelHook(public.to_dict_obj({'access_key': hook['access_key']}))
                if not del_res['status']:
                    return public.ReturnMsg(False,'移除webhook失败.')

        #重新添加webhook
        # webhook_name格式: {site_name}_{site_id}_{branch}_deploy
        webhook_name_parts = git_manager['webhook_name'].split('_')
        if len(webhook_name_parts) >= 3:
            site_name = git_manager['type_parm']
            site_id = webhook_name_parts[-3]
            branch = webhook_name_parts[-2]
        
        # 使用_create_webhook方法重新创建webhook
        new_webhook_name, new_webhook_url = self._create_webhook(site_id, site_name, branch)
        
        if not new_webhook_name or not new_webhook_url:
            return public.ReturnMsg(False,'创建webhook失败.')
        
        # 更新数据库中的webhook信息
        update_data = {
            'webhook_name': new_webhook_name,
            'webhook_url': new_webhook_url
        }
        public.M('git_manager').where('id=?', (git_manager_id,)).update(update_data)
        
        public.set_module_logs(f'Git-Tools','refresh_webhook')
        return public.return_data(True,data=update_data)

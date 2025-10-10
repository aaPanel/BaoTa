# 网站管理公共模块
# @author Zhj<2024/06/15>
import os
import re
import json
import typing

import public
from .common import M, aap_t_simple_result, to_dict_obj, dict_obj, get_msg_gettext, get_setup_path, readFile
from .exceptions import HintException


import collections


# 简单网站信息
aap_t_simple_site_info = collections.namedtuple('aap_t_simple_site_info', ['site_id', 'database_id'])


# 获取当前部署的Web服务器
def get_webserver():
    nginxSbin = '{}/nginx/sbin/nginx'.format(get_setup_path())
    apacheBin = '{}/apache/bin/apachectl'.format(get_setup_path())
    olsBin = '/usr/local/lsws/bin/lswsctrl'

    if os.path.exists(nginxSbin) and (os.path.exists(apacheBin) or os.path.exists(olsBin)):
        return 'nginx'

    if os.path.exists(apacheBin):
        webserver = 'apache'
    elif os.path.exists(olsBin):
        webserver = 'openlitespeed'
    else:
        webserver = 'nginx'

    return webserver


# 查询网站对应的PHP版本
def get_site_php_version(siteName: str) -> str:
    try:
        webserver = get_webserver()
        setup_path = get_setup_path()

        conf = readFile(
            '{setup_path}/panel/vhost/{webserver}/{siteName}.conf'.format(setup_path=setup_path, webserver=webserver,
                                                                          siteName=siteName))
        if webserver == 'openlitespeed':
            conf = readFile(setup_path + '/panel/vhost/' + webserver + '/detail/' + siteName + '.conf')
        if webserver == 'nginx':
            rep = r"enable-php-(\w{2,5})[-\w]*\.conf"
        elif webserver == 'apache':
            rep = r"php-cgi-(\w{2,5})\.sock"
        else:
            rep = r"path\s*/usr/local/lsws/lsphp(\d+)/bin/lsphp"

        tmp = re.search(rep, conf).groups()

        if tmp[0] == '00':
            return 'Static'

        if tmp[0] == 'other':
            return 'Other'

        return tmp[0][0] + '.' + tmp[0][1]
    except:
        return 'Static'


# 修复网站文件权限
def fix_permissions(site_root_path_or_site_file: str) -> aap_t_simple_result:
    """
    :param site_root_path_or_site_file: str 网站根目录或者单一网站文件
    :return:
    """
    from files_v2 import files
    data = files().fix_permissions(to_dict_obj({'path': site_root_path_or_site_file}))

    if int(data.get('status', 0)) != 0:
        return aap_t_simple_result(False, data.get('msg', 'Failed to fix permission'))

    return aap_t_simple_result(True, data.get('msg', 'Fix permission successfully'))


# 备份网站文件
def backup_files(site_id: int) -> aap_t_simple_result:
    from panel_site_v2 import panelSite
    data = panelSite().ToBackup(to_dict_obj({'id': site_id}))

    if int(data.get('status', 0)) != 0:
        return aap_t_simple_result(False, data.get('message', {})['result'])

    return aap_t_simple_result(True, M('backup').where('type = 0 and pid=?', (site_id,)).order('id desc').getField('filename'))


# 还原网站文件
def restore_files(site_id: int, bak_file: str) -> aap_t_simple_result:
    from panel_restore_v2 import panel_restore
    data = panel_restore().restore_website_backup(to_dict_obj({'site_id': site_id, 'file_name': os.path.basename(bak_file)}))
    return aap_t_simple_result(int(data.get('status', 0)) == 0, data.get('message', {})['result'])


# 删除网站备份文件
def del_bak(bak_file: str) -> aap_t_simple_result:
    # aapanel内部备份
    bak_id_dict = M('backup').where('`type`=0 and `filename` = ?', (bak_file,)).field('id').find()

    if isinstance(bak_id_dict, dict):
        from panel_site_v2 import panelSite
        data = panelSite().DelBackup(to_dict_obj({'id': int(bak_id_dict['id'])}))
        return aap_t_simple_result(int(data.get('status', 0)) == 0, data.get('message', {})['result'])

    # 其它途径备份
    if not os.path.exists(bak_file):
        return aap_t_simple_result(False, get_msg_gettext('File not exists'))

    os.remove(bak_file)

    return aap_t_simple_result(True, get_msg_gettext('Remove backup successfully'))


# 创建PHP站点
def create_php_site_with_mysql(domain: str, site_path: str, php_ver_short: str, db_user: str, db_pwd: str, another_domains: typing.List = ()) -> aap_t_simple_site_info:
    """
    :param domain: str              网站主域名
    :param site_path: str           网站根目录（绝对路径）
    :param php_ver_short: str       PHP版本号缩写 54、74、80、81...
    :param db_user: str             数据库用户名
    :param db_pwd: str              数据库用户密码
    :param another_domains: list    网站其它解析域名
    :return: aap_t_simple_site_info
    """
    from panel_site_v2 import panelSite
    data = panelSite().AddSite(to_dict_obj({
        'webname': json.dumps({
            'domain': domain,
            'domainlist': list(another_domains),
            'count': 0,
        }),
        'type': 'PHP',
        'version': php_ver_short,
        'port': '80',
        'path': site_path,
        'sql': 'MySQL',
        'datauser': db_user,
        'datapassword': db_pwd,
        'codeing': 'utf8mb4',
        'ps': domain.replace('.', '_').replace('-', '_'),
    }))

    if int(data.get('status', 0)) != 0:
        raise HintException(data.get('message', {})['result'])

    data = data.get('message', {})

    if int(data.get('databaseStatus', 0)) != 1:
        raise HintException(public.lang('Database creation failed. Please check mysql running status and try again.'))

    return aap_t_simple_site_info(data['siteId'], data['d_id'])


# 删除站点
def remove_site(site_id: int) -> public.aap_t_simple_result:
    site_info = M('sites').where('`id` = ?', (site_id,)).field('name').find()

    if not isinstance(site_info, dict):
        return public.aap_t_simple_result(False, public.lang('No found site-info with id {}',site_id))

    from panel_site_v2 import panelSite
    data = panelSite().DeleteSite(to_dict_obj({
        'id': site_id,
        'webname': site_info['name'],
        'ftp': '1',
        'path': '1',
        'database': '1',
    }))

    return aap_t_simple_result(int(data.get('status', 0)) == 0, data.get('message', {})['result'])


# 获取可用的PHP版本列表
def get_available_php_ver_shorts(without_static: bool = True) -> typing.List[str]:
    from panel_site_v2 import panelSite
    lst = panelSite().GetPHPVersion(to_dict_obj({}), False)

    if without_static:
        lst = filter(lambda x: x['version'] != '00', lst)

    return list(map(lambda x: x['version'], lst))

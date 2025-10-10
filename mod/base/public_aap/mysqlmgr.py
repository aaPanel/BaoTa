# MySQL管理公共模块
# @author Zhj<2024/07/01>
import os
import json
import time
import typing

from .common import M, aap_t_simple_result, aap_t_mysql_dump_info, to_dict_obj, get_msg_gettext, get_mysqldump_bin, MysqlConn, get_database_character, ExecShell
from .exceptions import HintException


# 备份MySQL数据库
def backup(database_id: int) -> aap_t_simple_result:
    from database_v2 import database
    data = database().ToBackup(to_dict_obj({'id': database_id}))

    if int(data.get('status', 0)) != 0:
        return aap_t_simple_result(False, data.get('message', {})['result'])

    return aap_t_simple_result(True, M('backup').where('type = 1 and pid=?', (database_id,)).order('id desc').getField('filename'))


# 还原MySQL数据库
def restore(db_name: str, bak_file: str) -> aap_t_simple_result:
    from database_v2 import database
    data = database().InputSql(to_dict_obj({'name': db_name, 'file': bak_file}))
    return aap_t_simple_result(int(data.get('status', 0)) == 0, data.get('message', {})['result'])


# 删除MySQL数据库备份文件
def del_bak(bak_file: str) -> aap_t_simple_result:
    # aapanel内部备份
    bak_id_dict = M('backup').where('`type`=1 and `filename`=?', (bak_file,)).field('id').find()

    if isinstance(bak_id_dict, dict):
        from database_v2 import database
        data = database().DelBackup(to_dict_obj({'id': int(bak_id_dict['id'])}))
        return aap_t_simple_result(int(data.get('status', 0)) == 0, data.get('message', {})['result'])

    # 其它途径备份
    if not os.path.exists(bak_file):
        return aap_t_simple_result(False, get_msg_gettext('File not exists'))

    os.remove(bak_file)

    return aap_t_simple_result(True, get_msg_gettext('Remove backup successfully'))


# 数据库导出
def dumpsql_with_aap(database_id: int, backup_path: typing.Optional[str] = None) -> aap_t_mysql_dump_info:
    import shlex
    db_find = M('databases').where("id=?", (database_id,)).find()

    if not isinstance(db_find, dict):
        raise HintException(get_msg_gettext('Table {} has been corrupted', ('databases',)))

    if backup_path is None:
        backup_path_tmp = M('config').order('`id` desc').limit(1).field('backup_path').find()

        if not isinstance(backup_path_tmp, dict):
            raise HintException(get_msg_gettext('Table {} has been corrupted', ('config',)))

        backup_path = os.path.join(str(backup_path_tmp['backup_path']), 'database')

    name = db_find['name']
    fileName = name + '_' + time.strftime('%Y%m%d_%H%M%S', time.localtime()) + '.sql.gz'
    backupName = os.path.join(backup_path, fileName)
    mysqldump_bin = get_mysqldump_bin()

    from database_v2 import database
    database_obj = database()

    if db_find['db_type'] in ['0', 0]:
        # 本地数据库
        # 测试数据库连接
        with MysqlConn() as conn:
            conn.execute("show databases")

        root = M('config').where('id=?', (1,)).getField('mysql_root')
        if not os.path.exists(backup_path):
            os.makedirs(backup_path, 0o600)

        if not database_obj.mypass(True, root):
            raise HintException(get_msg_gettext("Database configuration file failed to get checked, please check "
                                                "if MySQL configuration file exists [/etc/my.cnf]"))

        try:
            password = M('config').where('id=?', (1,)).getField('mysql_root')
            if not password:
                raise HintException(get_msg_gettext("Database password cannot be empty"))

            password = shlex.quote(str(password))
            os.environ["MYSQL_PWD"] = password
            ExecShell(mysqldump_bin + " -R -E --triggers=false --default-character-set=" + get_database_character(name) + " --force --opt \"" + name + "\"  -u root -p" + password + " | gzip > " + backupName)
        finally:
            os.environ["MYSQL_PWD"] = ""

        database_obj.mypass(False, root)

    elif db_find['db_type'] in ['1', 1]:
        # 远程数据库
        try:
            conn_config = json.loads(db_find['conn_config'])
            res = database_obj.CheckCloudDatabase(conn_config)
            if isinstance(res, dict):
                raise HintException(res.get('msg', get_msg_gettext('Cannot connect to remote MySQL')))

            password = shlex.quote(str(conn_config['db_password']))
            os.environ["MYSQL_PWD"] = password
            ExecShell(mysqldump_bin + " -h " + conn_config['db_host'] + " -P " + str(int(conn_config['db_port'])) + " -R -E --triggers=false --default-character-set=" + get_database_character(name) + " --force --opt \"" + str(db_find['name']) + "\"  -u " + str(conn_config['db_user']) + " -p" + password + " | gzip > " + backupName)
        finally:
            os.environ["MYSQL_PWD"] = ""

    elif db_find['db_type'] in ['2', 2]:
        try:
            conn_config = M('database_servers').where('id=?', db_find['sid']).find()
            res = database_obj.CheckCloudDatabase(conn_config)
            if isinstance(res, dict):
                raise HintException(res.get('msg', get_msg_gettext('Cannot connect to remote MySQL')))

            password = shlex.quote(str(conn_config['db_password']))
            os.environ["MYSQL_PWD"] = password
            ExecShell(mysqldump_bin + " -h " + conn_config['db_host'] + " -P " + str(int(conn_config['db_port'])) + " -R -E --triggers=false --default-character-set=" + get_database_character(name) + " --force --opt \"" + str(db_find['name']) + "\"  -u " + str(conn_config['db_user']) + " -p" + str(conn_config['db_password']) + " | gzip > " + backupName)
        finally:
            os.environ["MYSQL_PWD"] = ""

    else:
        raise HintException(get_msg_gettext("Unsupported database type"))

    if not os.path.exists(backupName):
        raise HintException(get_msg_gettext("Backup error"))

    # # 将备份信息添加到数据库中
    # bak_id = M('backup').add('type,name,pid,filename,size,addtime', (1, fileName, id, backupName, 0, time.strftime('%Y-%m-%d %X', time.localtime())))

    return aap_t_mysql_dump_info(db_name=str(db_find['name']), file=backupName, dump_time=int(time.time()))

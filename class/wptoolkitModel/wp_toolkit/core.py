# WP Toolkit core
# author: Zhj<2024-06-24>
import contextlib
import html
import os
import time
import json
import public_wp as public
import re
import requests
import threading
import typing
import collections
from urllib.parse import urlparse
# from public.authorization import only_pro_members
from wptoolkitModel import base


# WP核心库 结构体
# WP数据库信息
wp_db_info = collections.namedtuple('wp_db_info', ['id', 'name', 'prefix', 'user', 'password'])
wp_mem_info = collections.namedtuple('wp_mem_info', ['total', 'free', 'buffers', 'cached'])
wp_bak_info = collections.namedtuple('wp_bak_info', ['id', 'bak_file', 'bak_type', 'site_id', 'bak_time'])


# 检查 /var/spool/postfix/maildrop 目录是否存在
if not os.path.exists('/var/spool/postfix/maildrop'):
    # 不存在则创建
    os.makedirs('/var/spool/postfix/maildrop', 0o777)


# WP备份元数据
class wp_bak_meta_info:
    __slots__ = ['domain', 'another_domains', 'site_path', 'php_ver_short', 'db_name', 'db_user', 'db_pwd', 'db_prefix']

    def __init__(self, domain: str, site_path: str, php_ver_short: str, db_name: str, db_user: str, db_pwd: str, db_prefix: str, another_domains: list = ()):
        self.domain = domain
        self.site_path = site_path
        self.php_ver_short = php_ver_short
        self.db_name = db_name
        self.db_user = db_user
        self.db_pwd = db_pwd
        self.db_prefix = db_prefix
        self.another_domains = list(another_domains)

    @staticmethod
    def parse(meta_json_file: str):
        if not os.path.exists(meta_json_file):
            raise RuntimeError(public.get_msg_gettext('File {} not found', (meta_json_file,)))

        # 解析meta.json
        with open(meta_json_file, 'r') as fp:
            metadata = json.loads(fp.read())

        # 校验metadata
        public.to_dict_obj(metadata).validate([
            public.Param('domain').Require().Host(),
            public.Param('another_domains').Require(),
            public.Param('site_path').Require().SafePath(),
            public.Param('php_ver_short').Require().Integer(),
            public.Param('db_name').Require().Regexp(r'^\w+$'),
            public.Param('db_user').Require().Regexp(r'^\w+$'),
            public.Param('db_pwd').Require(),
            public.Param('db_prefix').Require().String(r'^\w+$'),
        ])

        return wp_bak_meta_info(domain=metadata['domain'],
                                site_path=metadata['site_path'],
                                php_ver_short=metadata['php_ver_short'],
                                db_name=metadata['db_name'],
                                db_user=metadata['db_user'],
                                db_pwd=metadata['db_pwd'],
                                db_prefix=metadata['db_prefix'],
                                another_domains=metadata['another_domains'])

    # 转换成字典
    def to_dict(self) -> typing.Dict:
        return {
            'domain': self.domain,
            'site_path': self.site_path,
            'php_ver_short': self.php_ver_short,
            'db_name': self.db_name,
            'db_user': self.db_user,
            'db_pwd': self.db_pwd,
            'db_prefix': self.db_prefix,
            'another_domains': self.another_domains,
        }


# WP版本管理类
class wp_version:

    def __init__(self):
        # 用宝塔官网的
        self.__API_URL = 'https://download.bt.cn/wordpress/version-check.json'
        self.__CACHE_KEY = 'SHM_:_CACHED_WP_VERSIONS'
        self.__PACKAGE_STORAGE = '{}/data/wp_packages'.format(public.get_panel_path())
        self.__PACKAGE_SAVE_TIMEOUT = 30 * 86400
        self.__PACKAGE_MD5 = None

        self.__makesure_package_storage_exists()

    # 确保安装包保存目录已创建
    def __makesure_package_storage_exists(self):
        if not os.path.exists(self.__PACKAGE_STORAGE):
            os.makedirs(self.__PACKAGE_STORAGE, 0o700)

    # 检查是否需要重新下载对应版本的安装包
    def __package_re_download_check(self, package_version: str) -> bool:
        # 检查安装包命名格式
        from public_wp import match_general_version_format
        m = match_general_version_format.match(package_version)

        if m is None:
            return True

        # 检查安装包是否存在
        package_path = '{}/wordpress-{}.zip'.format(self.__PACKAGE_STORAGE, package_version)

        if not os.path.exists(package_path):
            return True

        # 检查安装包上一次下载时间是否距现在太久，需要重新下载
        if os.path.getmtime(package_path) + self.__PACKAGE_SAVE_TIMEOUT <= int(time.time()):
            return True

        # 对比安装包的MD5值
        if self.__retrieve_package_md5(package_version) != public.FileMd5(package_path):
            return True

        return False

    # 获取安装包的md5值
    def __retrieve_package_md5(self, package_version: str) -> str:
        if self.__PACKAGE_MD5 is not None:
            return self.__PACKAGE_MD5

        # 检查安装包与MD5文件是否存在
        package_path = '{}/wordpress-{}-zh_CN.zip'.format(self.__PACKAGE_STORAGE, package_version)
        md5_file = '{}.md5'.format(package_path)

        from public_wp import match_md5_format

        # 当安装包与MD5文件同时存在，并且安装包在有效保存时间内，读取本地的MD5值
        if os.path.exists(package_path) and os.path.exists(md5_file) and os.path.getmtime(package_path) + self.__PACKAGE_SAVE_TIMEOUT > int(time.time()):
            with open(md5_file, 'r') as fp:
                package_md5 = fp.read()

            # 当md5格式正确则返回
            if match_md5_format.match(package_md5):
                self.__PACKAGE_MD5 = package_md5
                return package_md5

        # 请求Wordpress官网的文件校验值
        # 用宝塔官网的
        package_md5 = requests.get('https://download.bt.cn/wordpress/wordpress-{}-zh_CN.zip.md5'.format(package_version)).text

        # 检查接口是否正常响应了md5值
        if not match_md5_format.match(package_md5):
            raise public.HintException(public.get_msg_gettext('Could not get wordpress-{}.zip.md5 from wordpress.org.', (package_version,)))

        # 将安装包的md5值保存到本地
        with open(md5_file, 'w') as fp:
            fp.write(package_md5)

        self.__PACKAGE_MD5 = package_md5

        return package_md5

    # 获取历史版本信息，新 -> 旧
    def latest_versions(self) -> typing.List:
        cached = public.cache_get(self.__CACHE_KEY)

        if cached:
            return cached

        try:
            resp = requests.get(self.__API_URL)

            if not resp.ok:
                raise public.HintException(public.get_msg_gettext('Failed to retrieve wordpress latest versions.'))

            offers = resp.json().get('offers', [])

            if len(offers) < 1:
                return []

            cached = offers[1:18]

            public.cache_set(self.__CACHE_KEY, cached, 7200)

            return cached
        except:
            return []

    # 获取最新版本信息
    def latest_version(self) -> typing.Dict:
        versions = self.latest_versions()

        if len(versions) < 1:
            raise public.HintException(public.get_msg_gettext('Failed to retrieve wordpress latest version information.'))

        return versions[0]

    # 下载安装包
    def download_package(self, package_version: str) -> str:
        cache_key = 'DOWNLOAD_PROGRESS__wordpress-{}.zip'.format(package_version)

        filename = '{}/wordpress-{}.zip'.format(self.__PACKAGE_STORAGE, package_version)
        # 检查是否需要重新下载安装包
        if not self.__package_re_download_check(package_version):
            fsize = os.path.getsize(filename)
            public.cache_set(cache_key, '{}/{}/{}'.format(fsize, fsize, 0), 60)
            return filename

        # 获取安装包MD5值
        package_md5 = self.__retrieve_package_md5(package_version)

        # 安装包下载URL
        # 用宝塔官网的
        download_url = 'https://download.bt.cn/wordpress/wordpress-{}-zh_CN.zip'.format(package_version)
        try:
            download_res = requests.get(
                download_url,
                headers=public.get_requests_headers(),
                timeout=(60, 1800),
                stream=True)
        except Exception as ex:
            str_ex = str(ex)
            if 'Name or service not known' in str_ex:
                raise public.HintException(public.get_msg_gettext(
                    'Name or service not known, please check whether the server network configuration is normal.'))

            elif 'Failed to establish a new connection' in str_ex:
                raise public.HintException(public.get_msg_gettext(
                    'Failed to establish a new connection, please check whether the server network configuration is normal.'))

            elif 'Read timed out' in str_ex:
                raise public.HintException(public.get_msg_gettext('Read timed out.'))

            elif 'Connection refused' in str_ex:
                raise public.HintException(public.get_msg_gettext('Connection refused.'))

            elif 'Remote end closed connection without response' in str_ex:
                raise public.HintException(public.get_msg_gettext('Remote end closed connection without response.'))

            raise ex

        headers_total_size = int(download_res.headers['Content-Length'])

        res_down_size = 0
        res_chunk_size = 8192
        last_time = time.time()
        try:
            with open(filename, 'wb+') as with_res_f:
                for download_chunk in download_res.iter_content(chunk_size=res_chunk_size):
                    if download_chunk:
                        with_res_f.write(download_chunk)
                        speed_last_size = len(download_chunk)
                        res_down_size += speed_last_size
                        res_start_time = time.time()
                        res_timeout = (res_start_time - last_time)
                        res_sec_speed = int(res_down_size / res_timeout)
                        pre_text = '{}/{}/{}'.format(res_down_size,
                                                     headers_total_size,
                                                     res_sec_speed)
                        public.cache_set(cache_key, pre_text, 60)

            # 文件完整性校验
            if public.FileMd5(filename) != package_md5:
                raise public.HintException(public.get_msg_gettext('Download failed: File is corrupted.'))
        except Exception as ex:
            ex_str = str(ex)
            if "Read timed out" in ex_str:
                raise public.HintException(
                    public.get_msg_gettext('Download timeout, please try again later: {}'.format(ex_str)))

            if "No space left on device" in ex_str:
                raise public.HintException(public.get_msg_gettext(
                    'Download failed: No space left on device, please try again after the cleaning up the disk.'))

            raise ex

        # 安装包下载完成后，启动一个线程计算文件校验值
        threading.Thread(target=self.update_checksums, args=(package_version, filename), daemon=True).start()

        return filename

    # 获取安装包下载进度
    def get_download_progress(self, package_version: str) -> typing.Dict:
        cache_key = 'DOWNLOAD_PROGRESS__wordpress-{}.zip'.format(package_version)
        pre_text = public.cache_get(cache_key, '0/0/0')

        result = {}

        pre_tmp = pre_text.split('/')
        result['down_size'], result['total_size'] = (int(pre_tmp[0]), int(pre_tmp[1]))
        result['down_pre'] = 0
        result['sec_speed'] = int(float(pre_tmp[2]))
        result['need_time'] = 0

        if result['total_size'] > 0:
            result['down_pre'] = round(result['down_size'] / result['total_size'] * 100, 1)

        if result['sec_speed'] > 0:
            result['need_time'] = int((result['total_size'] - result['down_size']) / result['sec_speed'])

        return result

    # 解压安装包
    def unpack(self, package_file: str, dst: str, excludes: typing.Union[typing.Tuple, typing.List] = ()):
        # 检查安装包格式是否正确
        if len(package_file) < 5 or package_file[-4:] != '.zip':
            raise public.HintException(public.get_msg_gettext('Invalid wordpress package: {}', (package_file,)))

        # 检查安装包是否存在
        if not os.path.exists(package_file):
            raise public.HintException(public.get_msg_gettext('No such file: {}', (package_file,)))

        # 检查目标目录是否存在
        if not os.path.exists(dst):
            raise public.HintException(public.get_msg_gettext('No such directory: {}', (dst,)))

        # 目标目录不能是系统核心目录
        if dst in ('/', '/etc', '/boot', '/sys', '/dev'):
            raise public.HintException(public.get_msg_gettext('Cannot use system core directory: {}', (dst,)))

        # excludes统一转换为list类型
        if isinstance(excludes, tuple):
            excludes = list(excludes)

        import shutil

        # 创建临时目录
        with public.make_panel_tmp_path_with_context() as tmp_path:
            shutil.unpack_archive(package_file, tmp_path, 'zip')

            # 检查是否存在wordpress目录
            sub_dir_wordpress = os.path.join(tmp_path, 'wordpress')

            from glob import glob

            if os.path.exists(sub_dir_wordpress):
                # 将wordpress目录下的所有文件移动到临时目录的根路径下
                for fname in glob('{}/*'.format(sub_dir_wordpress)):
                    shutil.move(fname, tmp_path)

                # 删除wordpress目录
                shutil.rmtree(sub_dir_wordpress)

            # 将目录下所有文件移动到目标目录下
            for fname in glob('{}/*'.format(tmp_path)):
                # 目录处理
                if os.path.isdir(fname):
                    # 移动所有文件到目标目录下
                    for fname2 in glob('{}/**'.format(fname), recursive=True):
                        # 获取文件相对路径
                        path_rel = fname2.replace(tmp_path + '/', '')

                        # 检查是否是目录
                        dst_sub = os.path.join(dst, path_rel)

                        # 检查是否为目录
                        is_dir = os.path.isdir(fname2)

                        if is_dir:
                            # 目录已存在，跳过目录的mv操作
                            if os.path.exists(dst_sub):
                                continue

                        skip = False

                        # 检查是否需要跳过该文件
                        for exclude_f in excludes:
                            if path_rel.startswith(exclude_f):
                                skip = True
                                break

                        if skip:
                            continue

                        # 移动目录或文件
                        shutil.move(fname2, dst_sub)

                        # 当本次移动整个目录时，跳过接下来的该目录下的所有子目录以及文件
                        if is_dir:
                            excludes.append(path_rel.rstrip('/') + '/')

                    continue

                path_rel = fname.replace(tmp_path + '/', '')

                skip = False

                # 检查是否需要跳过该文件
                for exclude_f in excludes:
                    if path_rel.startswith(exclude_f):
                        skip = True
                        break

                if skip:
                    continue

                # 移动文件
                shutil.move(fname, os.path.join(dst, path_rel))

    # 完整性校验
    def checksums(self, package_version: str, site_path: str) -> public.aap_t_simple_result:
        # 跳过检验框架核心文件列表
        without_core_files = (
            'wp-config.php',
        )

        # 下载或者从本地获取对应版本的WP框架源码
        local_wp_checksums_file = '{}/data/wp_package_checksums/wordpress-{}.json'.format(public.get_panel_path(), package_version)

        # 没有生成过校验码时，重新下载并生成校验码
        if not os.path.exists(local_wp_checksums_file):
            self.update_checksums(package_version)

        # 获取站点根路径
        wp_root_path = site_path

        # 加载checksums
        with open(local_wp_checksums_file, 'r') as fp:
            checksums = json.loads(fp.read())

        # 没有通过校验的文件列表
        check_fails = []

        # 对比源码MD5
        for file_rel, cks in checksums:
            fmd5 = public.FileMd5(wp_root_path + '/' + file_rel)
            flag = False
            for ck in cks:
                ck = ck.strip()
                if ck == '':
                    continue

                if fmd5 == ck:
                    flag = True
                    break

            if not flag:
                check_fails.append(file_rel)

        # 完整性校验不通过，返回未通过校验的文件列表
        if len(check_fails) > 0:
            s = ''.join(map(lambda x: '''<br/>警告：以下文件未通过WordPress.org的参考校验验证: {}'''.format(x), check_fails))
            return public.aap_t_simple_result(False, public.lang("WordPress核心文件与WordPress.org的参考校验不匹配。{}", s))

        # 完成完整性校验
        return public.aap_t_simple_result(True, public.lang("WordPress核心文件已成功通过WordPress.org的参考校验。"))

    # 更新文件校验码
    def update_checksums(self, package_version: str, package_zip: typing.Optional[str] = None) -> public.aap_t_simple_result:
        local_wp_integrity_path = '{}/data/wp_package_checksums'.format(public.get_panel_path())

        if not os.path.exists(local_wp_integrity_path):
            os.makedirs(local_wp_integrity_path, 0o700)

        # 当安装包未指定或者安装包丢失时，重新下载
        if package_zip is None or not os.path.exists(package_zip) or len(package_zip) < 5 or package_zip[-4:] != '.zip':
            package_zip = self.download_package(package_version)

        # 不进行计算校验值的文件和目录
        ignore_regexp = re.compile(r'''wp-config\.php|wp-content/''')

        checksums_file = '{}/wordpress-{}.json'.format(local_wp_integrity_path, package_version)
        checksums = []

        with public.make_panel_tmp_path_with_context() as tmp_path:
            # 解压
            self.unpack(package_zip, tmp_path)

            from glob import glob
            for fname in glob('{}/**'.format(tmp_path), recursive=True):
                # 跳过目录
                if os.path.isdir(fname):
                    continue

                # 获取文件相对路径
                file_rel = fname.replace(tmp_path + '/', '')

                # 特定文件与目录不计算校验值
                if ignore_regexp.match(file_rel):
                    continue

                # 计算文件校验码
                cks = [public.FileMd5(fname)]

                # 当计算到wp-includes/default-filters.php时，多计算一次被aapanel修改后的校验值
                if file_rel == 'wp-includes/default-filters.php':
                    with open(fname, 'r') as fp:
                        tmp_str = fp.read()

                    tmp_str += r'''
// ---- AAPANEL AUTO-LOGIN BEGIN ----
require_once ABSPATH . 'wp-admin/includes/auto-login.php';
// ---- AAPANEL AUTO-LOGIN END ----
'''
                    # 多计算一个校验值
                    cks.append(public.Md5(tmp_str))

                # 保存校验值
                checksums.append((file_rel, cks))

            # 将校验值列表写入本地文件存储
            with open(checksums_file, 'w') as fp:
                fp.write(json.dumps(checksums))

        return public.aap_t_simple_result(True, public.lang("更新wordpress校验码成功"))


# WP插件、主题管理抽象类
class _abstract_wp_themes_and_plugins:

    def __init__(self, api_type: str, api_version: str = '1.2'):
        self.__API_URL = 'https://api.wordpress.org/{api_type}/info/{api_version}/'.format(api_type=api_type, api_version=api_version)
        self.__ERR_LOG = '{}/logs/wp_api_error.log'

    # 写日志
    def __log(self, content: str):
        with open(self.__ERR_LOG, 'a') as fp:
            fp.write('{} {}\n'.format(int(time.time()), content))

    # 通用请求方法
    def _request(self, action: str,
                page: int = 1,
                per_page: int = 20,
                search: typing.Optional[str] = None,
                slug: typing.Optional[str] = None,
                browse: typing.Optional[str] = None,
                fields: typing.Optional[typing.Dict[str, bool]] = None) -> typing.Dict[str, typing.Any]:
        params = {
            'action': action,
            'per_page': per_page,
            'page': page,
            "locale": "zh_CN",
            'fields': {
                'description': True,
                'sections': False,
                'tested': True,
                'requires': True,
                'rating': True,
                'downloaded': True,
                'downloadlink': True,
                'last_updated': True,
                'homepage': True,
                'tags': True,
                'num_ratings': True,
            },
        }

        if browse is not None:
            params['browse'] = browse

        if fields is not None:
            params['fields'].update(fields)

        if slug is not None:
            params['slug'] = slug.strip()

        if search is not None:
            params['search'] = search.strip()

        params['fields'] = list(filter(lambda x: params['fields'][x], params['fields']))

        resp = requests.get(self.__API_URL, params=params)

        if not resp.ok:
            self.__log(resp.text)
            raise public.HintException(public.get_msg_gettext('Wordpress APIs error: {}'.format(resp.text)))

        return resp.json()


# WP插件管理
class wp_plugins(_abstract_wp_themes_and_plugins):

    def __init__(self):
        _abstract_wp_themes_and_plugins.__init__(self, 'plugins')

    # 查询插件列表
    def query(self, page: int = 1,
              per_page: int = 20,
              search: typing.Optional[str] = None,
              browse: typing.Optional[str] = None,
              fields: typing.Optional[typing.Dict[str, bool]] = None):
        ret = self._request('query_plugins', page=page, per_page=per_page, search=search, browse=browse, fields=fields)

        return {
            'page': ret['info']['page'],
            'pages': ret['info']['pages'],
            'total': ret['info']['results'],
            'list': ret['plugins'],
        }

    # 查询插件详情
    def info(self, slug: str, fields: typing.Optional[typing.Dict[str, bool]] = None):
        return self._request('plugin_information', slug=slug, fields=fields)


# WP主题管理
class wp_themes(_abstract_wp_themes_and_plugins):

    def __init__(self):
        _abstract_wp_themes_and_plugins.__init__(self, 'themes')

    # 查询插件列表
    def query(self, page: int = 1,
              per_page: int = 20,
              search: typing.Optional[str] = None,
              browse: typing.Optional[str] = None,
              fields: typing.Optional[typing.Dict[str, bool]] = None):
        ret = self._request('query_themes', page=page, per_page=per_page, search=search, browse=browse,
                            fields=fields)

        return {
            'page': ret['info']['page'],
            'pages': ret['info']['pages'],
            'total': ret['info']['results'],
            'list': ret['themes'],
        }

    def info(self, slug: str, fields: typing.Optional[typing.Dict[str, bool]] = None):
        return self._request('theme_information', slug=slug, fields=fields)


# WP插件&主题安装整合包管理
class wp_sets:
    __TABLE_NAME = 'wordpress_sets'
    __TABLE_NAME_SET_ITEMS = 'wordpress_set_items'

    def __init__(self):
        self.__init_tables()

    # 初始化数据表
    def __init_tables(self):
        # 初始化sets表
        if not public.S('sqlite_master').where('type=? AND name=?', ('table', self.__TABLE_NAME)).count():
            public.S('').execute(r'''CREATE TABLE IF NOT EXISTS `{table_name}` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`create_time` INTEGER NOT NULL DEFAULT (strftime('%s')),
`update_time` INTEGER NOT NULL DEFAULT (strftime('%s')),
`name` TEXT NOT NULL DEFAULT '');'''.format(table_name=self.__TABLE_NAME))

        # 初始化set_items表
        if not public.S('sqlite_master').where('type=? and name=?', ('table', self.__TABLE_NAME_SET_ITEMS)).count():
            public.S('').execute(r'''CREATE TABLE IF NOT EXISTS `{table_name}` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`set_id` INTEGER NOT NULL DEFAULT 0,
`type` INTEGER NOT NULL DEFAULT 1, -- 1 插件、2 主题
`state` INTEGER NOT NULL DEFAULT 0, -- 插件or主题的启用状态 0 禁用、1 启用
`create_time` INTEGER NOT NULL DEFAULT (strftime('%s')),
`update_time` INTEGER NOT NULL DEFAULT (strftime('%s')),
`slug` TEXT NOT NULL DEFAULT '',
`title` TEXT NOT NULL DEFAULT '',
`description` TEXT NOT NULL DEFAULT '');'''.format(table_name=self.__TABLE_NAME_SET_ITEMS))

    def __query(self, table_name: typing.Optional[str] = None):
        if table_name is None:
            table_name = self.__TABLE_NAME
        return public.S(table_name)

    # 获取整合包列表
    def fetch_list(self, keyword: str = '', p: int = 1, p_size: int = 20) -> typing.Dict[str, typing.Any]:
        query = self.__query()

        keyword = keyword.strip()

        if keyword != '':
            query.where('name like ? escape \'\\\'', ('%{}%'.format(public.escape_sql_str(keyword)),))

        total = query.fork().count()

        lst = query.field('id', 'name').limit(p_size, (p-1)*p_size).select()

        # 查询整合包下的插件&主题
        for item in lst:
            item['plugins'] = []
            item['themes'] = []

            set_items = self.__query(self.__TABLE_NAME_SET_ITEMS).where('set_id', item['id']).field('id', 'type', 'slug', 'state', 'title', 'description').select()

            if not isinstance(set_items, list):
                continue

            for set_item in set_items:
                if int(set_item['type']) == 1:
                    # 插件
                    item['plugins'].append(set_item)
                elif int(set_item['type']) == 2:
                    # 主题
                    item['themes'].append(set_item)

        return {
            'total': total,
            'list': lst,
        }

    # 新建整合包
    def create_set(self, name: str) -> int:
        # 不允许创建相同名称的集合包
        if self.__query().where('name=?', name).find():
            return 0

        set_id = self.__query().insert({
            'name': name,
        })

        # 写操作日志
        wpmgr.log_opt('Created Set [{}]', (name,))

        return set_id

    # 删除整合包
    def remove_set(self, set_ids: typing.Union[typing.List[int], typing.Tuple[int]]) -> bool:
        if len(set_ids) == 0:
            return True

        # 查询要删除的整合包名称列表
        titles = self.__query().where_in('id', set_ids).column('name')

        if len(titles) == 0:
            return True

        # 删除整合包
        self.__query().where_in('id', set_ids).delete()

        # 删除整合包下所有插件&主题
        self.__query(self.__TABLE_NAME_SET_ITEMS).where_in('set_id', set_ids).delete()

        # 写操作日志
        wpmgr.log_opt('Removed Sets [{}]', (', '.join(list(titles)),))

        return True

    # 获取整合包中特定类型的Items
    def get_items(self, set_id: int, item_type: typing.Optional[int] = None) -> typing.List:
        query = self.__query(self.__TABLE_NAME_SET_ITEMS).where('set_id', set_id)

        if item_type is not None:
            query.where('type', item_type)

        query.field('id', 'slug', 'type', 'state', 'title', 'description')

        return query.select()

    # 添加插件到整合包中
    def add_plugins(self, set_id: int, plugins: typing.List[typing.Dict]) -> public.aap_t_simple_result:
        # 检查整合包是否存在
        if not self.__query().where('id', (set_id,)).exists():
            return public.aap_t_simple_result(False, public.lang("Set not found with id: {}", set_id))

        # 查询整合包名称
        set_name = self.__query().where('id', set_id).value('name')

        # 校验插件列表数据结构
        from public_wp import Validator, Param
        validator = Validator([
            Param('slug').Require(),
            Param('title').Require(),
            Param('description').Require(),
        ])

        insert_data = []
        plugin_titles = []
        slugs = []

        for item in plugins:
            validator.check(item)
            insert_data.append({
                'set_id': set_id,
                'type': 1,
                'slug': item['slug'],
                'title': item['title'],
                'description': item['description'],
                'state': 1,
            })
            plugin_titles.append(item['title'])
            slugs.append(item['slug'])

        # 连接数据库
        with public.SqliteConn() as db:
            # 关闭事务自动提交
            db.autocommit(False)

            # 在数据库中删除本次属于重复添加的插件
            db.query()\
                .table(self.__TABLE_NAME_SET_ITEMS)\
                .where('set_id', set_id)\
                .where('type', 1)\
                .where_in('slug', slugs)\
                .delete()

            # 写入数据
            db.query().table(self.__TABLE_NAME_SET_ITEMS).insert_all(insert_data)

            # 提交事务
            db.commit()

        # 写操作日志
        wpmgr.log_opt('Add plugins [{}] to Set [{}]', (', '.join(plugin_titles), set_name))

        return public.aap_t_simple_result(True, public.lang('Success'))

    # 将插件从整合包中删除
    def remove_plugins(self, item_ids: typing.Union[typing.List[int], typing.Tuple[int]]) -> bool:
        # 创建查询构造器
        query = self.__query(self.__TABLE_NAME_SET_ITEMS).where('type', 1).where_in('id', item_ids)

        # 查询出整合包ID
        set_ids = self.__query(self.__TABLE_NAME_SET_ITEMS).where('type', 1).where_in('id', item_ids).column('distinct set_id')

        if len(set_ids) == 0:
            return True

        # 查询出整合包名称列表
        set_titles = self.__query().where_in('id', set_ids).column('name')

        if len(set_titles) == 0:
            return True

        # 查询出当前删除的插件名称列表
        titles = query.fork().column('title')

        if len(titles) == 0:
            return True

        # 将插件从整合包中删除
        query.delete()

        # 写操作日志
        wpmgr.log_opt('Removed plugins [{}] from Set [{}]', (', '.join(list(titles)), ', '.join(list(set_titles))))

        return True

    # 设置插件激活状态
    def update_plugins_state(self, state: int, item_ids: typing.Union[typing.List[int], typing.Tuple[int]]) -> bool:
        # 创建查询构造器
        query = self.__query(self.__TABLE_NAME_SET_ITEMS).where('type', 1).where_in('id', item_ids)

        # 查询出整合包ID
        set_ids = self.__query(self.__TABLE_NAME_SET_ITEMS).where('type', 1).where_in('id', item_ids).column(
            'distinct set_id')

        if len(set_ids) == 0:
            return True

        # 查询出整合包名称列表
        set_titles = self.__query().where_in('id', set_ids).column('name')

        if len(set_titles) == 0:
            return True

        # 查询出当前操作的插件名称列表
        titles = query.fork().column('title')

        if len(titles) == 0:
            return True

        # 更新状态
        query.update({
            'state': state,
            'update_time': int(time.time()),
        })

        state_name = 'activated'

        if state == 0:
            state_name = 'deactivated'

        # 写操作日志
        wpmgr.log_opt('Change plugins [{}] state to [{}] from Set [{}]', (', '.join(list(titles)), state_name, ', '.join(list(set_titles))))

        return True

    # 添加主题到整合包中
    def add_themes(self, set_id: int, themes: typing.List[typing.Dict]) -> public.aap_t_simple_result:
        # 检查整合包是否存在
        if not self.__query().where('id', (set_id,)).exists():
            return public.aap_t_simple_result(False, public.lang("Set not found with id: {}",set_id))

        # 查询整合包名称
        set_name = self.__query().where('id', set_id).value('name')

        # 校验主题列表数据结构
        from public_wp import Validator, Param
        validator = Validator([
            Param('slug').Require(),
            Param('title').Require(),
            Param('description').Require(),
        ])

        insert_data = []
        titles = []
        slugs = []

        for item in themes:
            validator.check(item)
            insert_data.append({
                'set_id': set_id,
                'type': 2,
                'slug': item['slug'],
                'title': item['title'],
                'description': item['description'],
                'state': 0,
            })
            titles.append(item['title'])
            slugs.append(item['slug'])

        # 连接数据库
        with public.SqliteConn() as db:
            # 关闭事务自动提交
            db.autocommit(False)

            # 在数据库中删除本次属于重复添加的主题
            db.query() \
                .table(self.__TABLE_NAME_SET_ITEMS) \
                .where('set_id', set_id) \
                .where('type', 2) \
                .where_in('slug', slugs) \
                .delete()

            # 写入数据
            db.query().table(self.__TABLE_NAME_SET_ITEMS).insert_all(insert_data)

            # 提交事务
            db.commit()

        # 写操作日志
        wpmgr.log_opt('Add themes [{}] to Set [{}]', (', '.join(titles), set_name))

        return public.aap_t_simple_result(True, public.lang('Success'))

    # 将主题从整合包中删除
    def remove_themes(self, item_ids: typing.Union[typing.List[int], typing.Tuple[int]]):
        # 创建查询构造器
        query = self.__query(self.__TABLE_NAME_SET_ITEMS).where('type', 2).where_in('id', item_ids)

        # 查询出整合包ID
        set_ids = self.__query(self.__TABLE_NAME_SET_ITEMS).where('type', 2).where_in('id', item_ids).column(
            'distinct set_id')

        if len(set_ids) == 0:
            return True

        # 查询出整合包名称列表
        set_titles = self.__query().where_in('id', set_ids).column('name')

        if len(set_titles) == 0:
            return True

        # 查询出当前删除的主题名称列表
        titles = query.fork().column('title')

        if len(titles) == 0:
            return True

        # 将主题从整合包中删除
        query.delete()

        # 写操作日志
        wpmgr.log_opt('Removed themes [{}] from Set [{}]', (', '.join(list(titles)), ', '.join(list(set_titles))))

        return True

    # 设置主题启用状态
    def update_theme_state(self, state: int, item_id: int) -> bool:
        # 创建查询构造器
        query = self.__query(self.__TABLE_NAME_SET_ITEMS).where('type', 2).where('id', item_id)

        # 查询出当前操作的主题名称
        title = query.fork().value('title')

        if title is None:
            return False

        # 查询出整合包ID
        set_id = self.__query(self.__TABLE_NAME_SET_ITEMS).where('type', 2).where('id', item_id).value('set_id')

        if set_id is None:
            return True

        # 查询出整合包名称列表
        set_title = self.__query().where('id', set_id).column('name')

        if set_title is None:
            return True

        cur_time = int(time.time())

        # 更新状态
        query.update({
            'state': state,
            'update_time': cur_time,
        })

        # 当为启用状态时，需要关闭该包下其它主题的启用状态
        if state == 1:
            self.__query(self.__TABLE_NAME_SET_ITEMS).where('type', 2).where_not_in('id', [item_id]).where('state', 1).update({
                'state': 0,
                'update_time': cur_time,
            })

        state_name = 'activated'

        if state == 0:
            state_name = 'deactivated'

        # 写操作日志
        wpmgr.log_opt('Change plugins [{}] state to [{}] from Set [{}]', (title, state_name, set_title))

        return True

    # 通过整合包安装插件&主题
    def install(self, set_id: int, site_ids: typing.Union[typing.List[int], typing.Tuple[int]] = ()) -> public.aap_t_simple_result:
        # 检查WP站点ID
        for site_id in site_ids:
            if not public.S('sites', 'site').where('id', site_id).exists():
                return public.aap_t_simple_result(False, public.lang("没有找到对应的站点: {}",site_id))

        # 查询出整合包下所有插件&主题
        items = self.__query(self.__TABLE_NAME_SET_ITEMS).where('set_id', set_id).field('type', 'slug', 'state').select()

        if not isinstance(items, list):
            return public.aap_t_simple_result(False, public.lang('没有需要安装的插件或主题。'))

        # 逐个站点安装
        for site_id in site_ids:
            wpmgr_obj = wpmgr(site_id)

            # 开始安装插件&主题
            for item in items:
                if int(item['type']) == 1:
                    # 安装插件
                    ok, msg = wpmgr_obj.install_plugin(item['slug'])

                    if ok and int(item['state']) == 1:
                        wpmgr_obj.activate_plugins(item['slug'])
                elif int(item['type']) == 2:
                    # 安装主题
                    ok, msg = wpmgr_obj.install_theme(item['slug'])

                    if ok and int(item['state']) == 1:
                        wpmgr_obj.switch_theme(item['slug'])

        # TODO 写操作日志

        return public.aap_t_simple_result(True, public.lang('插件和主题安装成功。'))


# WP管理类
class wpmgr:
    __LOCK = threading.RLock()
    __WP_API_BASE = 'https://api.wordpress.org/'

    def __init__(self, site_id: int):
        self.__SITE_ID = int(site_id)
        self.__TABLE_PREFIX = None
        self.__VERSION_MGR = wp_version()
        self.__WP_ADMIN_ID = None
        self.__WP_ROOT_PATH = None
        self.__ANOTHER_DOMAINS = []
        self.__FIRST_DOMAIN = None
        self.__DB_INFO = None
        self.__PLUGIN_API = wp_plugins()
        self.__THEME_API = wp_themes()

        self.repair_assoc()

    # 尝试修复网站关联
    def repair_assoc(self):
        try:
            assoc_info = public.M('wordpress_onekey').where('s_id=?', (self.__SITE_ID,)).field('prefix').find()

            if not isinstance(assoc_info, dict):
                db_info = public.M('databases').where('pid=?', (self.__SITE_ID,)).field('id').find()

                if isinstance(db_info, dict):
                    public.M('wordpress_onekey').insert({
                        's_id': self.__SITE_ID,
                        'd_id': db_info['id'],
                        'prefix': self.__get_table_prefix_by_config_file(),
                    })
        except:
            pass

    # 写面板操作日志
    @classmethod
    def log_opt(cls, msg: str, args: typing.Tuple = ()):
        public.WriteLog('WP Toolkit', public.get_msg_gettext(msg, args))

    # 获取site_id
    def get_site_id(self) -> int:
        return self.__SITE_ID

    # 查询管理员ID
    def retrieve_administrator_id(self) -> int:
        # 优先读取缓存
        if self.__WP_ADMIN_ID is not None:
            return self.__WP_ADMIN_ID

        # 查询到对应的数据库信息
        db_info = self.retrieve_database_info()
        import pymysql
        try:
            # 连接数据库进行查询
            with public.MysqlConn(db_info.name) as conn:
                data = conn.find(
                    r"select `user_id` from `{prefix}usermeta` where `meta_key` = '{prefix}capabilities' and `meta_value` like '%s:13:\"administrator\";b:1;%'".format(
                        prefix=db_info.prefix))
        except pymysql.OperationalError as e:
            # 数据库连接失败，用户名或密码错误
            if str(e).startswith('(1045, '):
                return public.aap_t_simple_result(False, "Mysql数据库连接失败，用户名或密码错误，您可以尝试修改或更新对应数据的密码")

            # 数据库连接失败，无法建立连接
            if str(e).startswith('(2003, '):
                raise public.HintException("Mysql数据库连接失败，无法建立连接，请检查数据库服务器是否正常启动")
        else:
            if not data:
                raise public.HintException(public.get_msg_gettext('未查询到管理员ID信息，请尝试手动登录'))

        # 缓存本次查询到的管理员ID
        self.__WP_ADMIN_ID = int(data['user_id'])

        return self.__WP_ADMIN_ID

    # 查询Wordpress站点根目录
    def retrieve_wp_root_path(self, check_dir_exists: bool = True) -> str:
        # 优先读取缓存
        if self.__WP_ROOT_PATH is not None:
            return self.__WP_ROOT_PATH

        # 查询网站根目录
        site_info = public.M('sites').where('id=?', (self.__SITE_ID,)).field('path').find()

        if not isinstance(site_info, dict):
            raise public.HintException(public.get_msg_gettext('Sorry. Not found Wordpress running path. -1'))

        if check_dir_exists and not os.path.exists(site_info['path']):
            raise public.HintException(public.get_msg_gettext('Sorry. Not found Wordpress running path. -2'))

        self.__WP_ROOT_PATH = str(site_info['path'])

        return self.__WP_ROOT_PATH

    # 查询Wordpress数据库信息
    def retrieve_database_info(self) -> wp_db_info:
        if self.__DB_INFO is not None:
            return self.__DB_INFO

        # 查询到对应的数据库信息
        mysql_db_info = public.M('databases').where('pid=?', (self.__SITE_ID,)).field('id,name,username,password').find()
        # print("mysql_db_info", mysql_db_info)

        if not isinstance(mysql_db_info, dict):
            # 开始数据库关联检测修复机制
            db_info_from_wp_config = self.__get_db_config_by_config_file()

            # 仅处理db_host为localhost、127.0.0.1的情况
            if db_info_from_wp_config is not None and db_info_from_wp_config.get('db_host', '') in ('localhost', '127.0.0.1'):
                mysql_db_info = public.M('databases').where('name=?', db_info_from_wp_config.get('db_name', '')).field('id,name,username,password').find()
                public.print_log(mysql_db_info)

                if isinstance(mysql_db_info, dict) and mysql_db_info.get('id'):
                    # 更新数据库信息
                    public.M('wordpress_onekey').where('s_id=?', self.__SITE_ID).update({
                        'd_id': int(mysql_db_info['id']),
                    })

            if not isinstance(mysql_db_info, dict):
                raise public.HintException(public.get_msg_gettext('没有找到指定的数据库'))


        # 查询数据库表前缀
        wp_info = public.M('wordpress_onekey').where('s_id=?', (self.__SITE_ID,)).field('prefix').find()

        if not isinstance(wp_info, dict):
            raise public.HintException(public.get_msg_gettext('抱歉.没有找到指定的wp站点.'))

        # 检查表前缀是否合法
        if not re.match(r'^\w+$', wp_info['prefix']):
            raise public.HintException(
                public.get_msg_gettext('对不起。指定的wordpress数据库前缀格式不合法。'))

        # 从配置文件中读取表前缀
        table_prefix = self.__get_table_prefix_by_config_file()

        # 对比表前缀，不同则更新数据库中的表前缀
        if wp_info['prefix'] != table_prefix:
            with public.M('wordpress_onekey') as query:
                query.where('d_id', mysql_db_info['id']).update({
                    'prefix': table_prefix,
                })

        self.__DB_INFO = wp_db_info(id=int(mysql_db_info['id']),
                                    name=mysql_db_info['name'],
                                    prefix=table_prefix,
                                    user=str(mysql_db_info['username']),
                                    password=str(mysql_db_info['password']))

        return self.__DB_INFO

    # 读取wp-config.php中的$table_prefix
    def __get_table_prefix_by_config_file(self) -> str:
        if self.__TABLE_PREFIX is not None:
            return self.__TABLE_PREFIX

        wp_config_file = '{}/wp-config.php'.format(self.retrieve_wp_root_path())

        if not os.path.exists(wp_config_file):
            raise public.HintException('站点的wp-config.php配置文件丢失')

        with open(wp_config_file, 'r') as fp:
            for line in fp:
                if line.strip().startswith('$table_prefix') and line.find('=') > -1:
                    self.__TABLE_PREFIX = line.strip().split('=')[1].strip(' \'";')
                    return self.__TABLE_PREFIX

        raise public.HintException('无法在wp-config.php文件中读取到table_prefix')

    # 读取wp-config.php中的数据库连接信息
    def __get_db_config_by_config_file(self) -> typing.Dict[str, str]:
        db_config = {}
        wp_config_file = '{}/wp-config.php'.format(self.retrieve_wp_root_path())

        with open(wp_config_file, 'r') as fp:
            for line in fp:
                if line.strip().startswith('define(') and line.find('\'DB_') > -1:
                    key = line.strip().split(',')[0].strip('define(\'').strip('\' ').lower()
                    value = line.strip().split(',')[1].strip(' )\'";')
                    db_config[key] = value

        return db_config

    # 查询Wordpress加载库目录
    def retrieve_wp_inc(self) -> str:
        wpinc = 'wp-includes'

        with open('{}/wp-settings.php'.format(self.retrieve_wp_root_path()), 'r') as fp:
            m = re.search(r"define\(\s*'WPINC',\s*'([\w\-]+)'\s*\);", fp.read(512))

            if m:
                wpinc = m.group(1)

        return wpinc

    # 查询WP站点绑定的PHP版本号 x.x
    def retrieve_php_version(self) -> str:
        import public

        php_ver = public.get_site_php_version(self.retrieve_site_name())

        if php_ver == 'Static' or php_ver == 'Other':
            raise public.HintException(public.get_msg_gettext('对不起，指定的wordpress没有设置PHP。'))

        return str(php_ver)

    # 查询WP站点对应的PHP执行文件
    def retrieve_php_bin(self) -> str:
        # 获取WP站点绑定的PHP可执行文件
        php_ver = self.retrieve_php_version()

        phpbin = '{}/php/{}/bin/php'.format(public.get_setup_path(), str(php_ver).replace('.', ''))

        if not os.path.exists(phpbin):
            raise public.HintException(public.get_msg_gettext('对不起. PHP{} 不存在.', (php_ver,)))

        return phpbin

    # 生成WP网站访问地址
    def build_site_url(self, sub_path: str = '') -> str:
        from data import data
        site_name = self.retrieve_first_domain()
        has_ssl = data().get_site_ssl_info(site_name) != -1
        return 'http{}://{}{}'.format('s' if has_ssl else '', site_name, os.path.join('/', sub_path.strip()) if len(sub_path.strip()) > 0 else '')

    # 查询站点绑定的首个域名
    def retrieve_first_domain(self) -> str:
        if self.__FIRST_DOMAIN is not None:
            return self.__FIRST_DOMAIN

        domain_info_list = public.M('domain').where('pid=?', (self.__SITE_ID,)).field('name,port').order('id asc').select()

        if isinstance(domain_info_list, list) and len(domain_info_list) > 0:
            for domain_info in domain_info_list:
                if self.__FIRST_DOMAIN is None and int(domain_info['port']) in (80, 443):
                    self.__FIRST_DOMAIN = str(domain_info['name']).strip()
                    continue

                self.__ANOTHER_DOMAINS.append(str(domain_info['name']).strip())

            if self.__FIRST_DOMAIN is not None:
                return self.__FIRST_DOMAIN

        # 没有查询到域名，直接读取网站根目录名称作为域名
        self.__FIRST_DOMAIN = os.path.basename(self.retrieve_wp_root_path())
        return self.__FIRST_DOMAIN

    # 查询站点其它解析域名
    def retrieve_another_domains(self) -> typing.List[str]:
        self.retrieve_first_domain()
        return self.__ANOTHER_DOMAINS

    # 查询网站名称
    def retrieve_site_name(self) -> str:
        return public.M('sites').where('id=?', self.__SITE_ID).field('name').find()['name']

    # 使用命令行执行Wordpress特定模块
    def run_wp_with_cli(self, php_code: str, extra_data: typing.Union[typing.Dict, typing.List] = (),
                        without_auth: bool = False) -> str:
        # PHP代码
        s = r'''<?php

define('AAP_CLI', true);
define('AAP_ABSPATH', '{wp_root_path}/');
define('DOING_AJAX', true);

// Set common headers, to prevent warnings from plugins.
$_SERVER['SERVER_PROTOCOL'] = 'HTTP/1.0';
$_SERVER['HTTP_USER_AGENT'] = '';
$_SERVER['HTTP_HOST'] = '{http_host}';
$_SERVER['REQUEST_METHOD']  = 'GET';
$_SERVER['REMOTE_ADDR']     = '127.0.0.1';

// JSON输出函数
function _aap_echo($res, $success = true) {{
    ob_end_clean();
    echo \json_encode([
        'success'   => $success,
        'res'       => $res,
    ], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
    exit;
}}

// 成功输出
function _aap_success($res) {{
    _aap_echo($res);
}}

// 失败输出
function _aap_fail($res) {{
    _aap_echo($res, false);
}}
{php_code_auth}
// 只报告运行时错误、解释器错误
error_reporting(E_ERROR | E_PARSE);

$_aap_extra_data = \json_decode('{aap_extra_data}', 1);

$_REQUEST = [];

if (!empty($_aap_extra_data['get'])) {{
    $_GET = (array)$_aap_extra_data['get'];
    $_REQUEST = array_merge($_REQUEST, $_GET);
}}

if (!empty($_aap_extra_data['post'])) {{
    $_POST = (array)$_aap_extra_data['post'];
    $_REQUEST = array_merge($_REQUEST, $_POST);
}}

// 兼容php8.1+ mysqli默认错误报告设置
\mysqli_report(MYSQLI_REPORT_OFF);

ob_start();

{php_code}

echo ob_get_clean();
'''.format(
            wp_root_path=self.retrieve_wp_root_path(),
            php_code=php_code,
            aap_extra_data=json.dumps(extra_data, ensure_ascii=False),
            http_host=self.retrieve_first_domain(),
            php_code_auth=r'''
require AAP_ABSPATH . 'wp-load.php';
require ABSPATH . 'wp-admin/includes/admin.php';

add_action('set_auth_cookie', function($auth_cookie) {{
    $_COOKIE[SECURE_AUTH_COOKIE] = $auth_cookie;
    $_COOKIE[AUTH_COOKIE] = $auth_cookie;
    $_COOKIE[LOGGED_IN_COOKIE] = $auth_cookie;
}});

$_user = wp_set_current_user({admin_id});
wp_set_auth_cookie({admin_id});

do_action('wp_login', $_user->user_login, $_user);
'''.format(admin_id=self.retrieve_administrator_id()) if not without_auth else ''
        )

        # 生成临时文件
        tmp_file = '/tmp/wp-cli-{}'.format(public.GetRandomString(16))

        with open(tmp_file, 'w', encoding='utf8') as fp:
            fp.write(s)

        try:
            # 没有安装sudo时，尝试安装
            if not os.path.exists('/usr/bin/sudo'):
                if os.path.exists('/usr/bin/apt'):
                    public.ExecShell("apt install sudo -y >> /tmp/schedule.log")
                else:
                    public.ExecShell("yum install sudo -y >> /tmp/schedule.log")

            # 优先使用sudo
            if os.path.exists('/usr/bin/sudo'):
                # 使用www用户执行
                res, err = public.ExecShell('sudo -u www {} -f {}'.format(self.retrieve_php_bin(), tmp_file))
            else:
                # 否则使用root用户执行
                res, err = public.ExecShell('{} -f {}'.format(self.retrieve_php_bin(), tmp_file))

                # 重新更新网站目录权限
                os.system('chmod -R 755 ' + self.retrieve_wp_root_path())
                os.system('chown -R www.www ' + self.retrieve_wp_root_path())

            # 记录错误信息
            if err:
                public.print_log('aap-wp-cli running error: {}'.format(err))

                # 检索PHP Fatal Error
                m = public.search_php_first_fatal_error.search(err)

                if m:
                    # 出现PHP Fatal error时，抛出提示异常
                    raise public.HintException(public.get_msg_gettext('PHP运行出错: {}. 请修改PHP版本后重试', (m.group(1),)))

            # 返回执行结果
            if isinstance(res, str):
                try:
                    pattern_check = r"PHP version \d+\.\d+\.\d+.*WordPress \d+\.\d+\.\d+.*at least \d+\.\d+\.\d+"
                    if re.search(pattern_check, res):
                        pattern_extract = r"PHP version (\d+\.\d+\.\d+)|WordPress (\d+\.\d+\.\d+)|at least (\d+\.\d+\.\d+)"
                        matches = re.findall(pattern_extract, res)
                        res = "您站点当前运行的是 PHP 版本 {php_version}，但 WordPress {wp_version} 至少需要 PHP 版本 {required_php_version}。".format(
                            php_version=matches[0][0],
                            wp_version=matches[1][1],
                            required_php_version=matches[2][2]
                        )
                except:
                    pass
            return res

        finally:
            # 确保最后删除临时文件
            os.remove(tmp_file)

    # 完成WP站点配置
    def setup_config(self, dbname: str, uname: str, pwd: str, dbhost: str, prefix: str) -> public.aap_t_simple_result:
        res = self.run_wp_with_cli(r'''
/**
 * We are installing.
 */
define( 'WP_INSTALLING', true );

/**
 * We are blissfully unaware of anything.
 */
define( 'WP_SETUP_CONFIG', true );

if ( ! defined( 'ABSPATH' ) ) {
	define( 'ABSPATH',  AAP_ABSPATH );
}

require ABSPATH . 'wp-settings.php';

/** Load WordPress Administration Upgrade API */
require_once ABSPATH . 'wp-admin/includes/upgrade.php';

/** Load WordPress Translation Installation API */
require_once ABSPATH . 'wp-admin/includes/translation-install.php';

// Support wp-config-sample.php one level up, for the develop repo.
if ( file_exists( ABSPATH . 'wp-config-sample.php' ) ) {
	$config_file = file( ABSPATH . 'wp-config-sample.php' );
} elseif ( file_exists( dirname( ABSPATH ) . '/wp-config-sample.php' ) ) {
	$config_file = file( dirname( ABSPATH ) . '/wp-config-sample.php' );
} else {
	_aap_fail(
		sprintf(
			/* translators: %s: wp-config-sample.php */
			__( 'Sorry, I need a %s file to work from. Please re-upload this file to your WordPress installation.' ),
			'wp-config-sample.php'
		)
	);
}

// Check if wp-config.php has been created.
if ( file_exists( ABSPATH . 'wp-config.php' ) ) {
	_aap_fail(
		sprintf(
			/* translators: 1: wp-config.php, 2: install.php */
			__( 'The file %1$s already exists. If you need to reset any of the configuration items in this file, please delete it first. You may try <a href="%2$s">installing now</a>.' ),
			'wp-config.php',
			'install.php'
		)
	);
}

// Check if wp-config.php exists above the root directory but is not part of another installation.
if ( @file_exists( ABSPATH . '../wp-config.php' ) && ! @file_exists( ABSPATH . '../wp-settings.php' ) ) {
	_aap_fail(
		sprintf(
			/* translators: 1: wp-config.php, 2: install.php */
			__( 'The file %1$s already exists one level above your WordPress installation. If you need to reset any of the configuration items in this file, please delete it first. You may try <a href="%2$s">installing now</a>.' ),
			'wp-config.php',
			'install.php'
		)
	);
}

$dbname = trim( wp_unslash( $_POST['dbname'] ) );
$uname  = trim( wp_unslash( $_POST['uname'] ) );
$pwd    = trim( wp_unslash( $_POST['pwd'] ) );
$dbhost = trim( wp_unslash( $_POST['dbhost'] ) );
$prefix = trim( wp_unslash( $_POST['prefix'] ) );

// Test the DB connection.
/**#@+
 *
 * @ignore
 */
define( 'DB_NAME', $dbname );
define( 'DB_USER', $uname );
define( 'DB_PASSWORD', $pwd );
define( 'DB_HOST', $dbhost );
/**#@-*/

// Re-construct $wpdb with these new values.
unset( $wpdb );
require_wp_db();

/*
* The wpdb constructor bails when WP_SETUP_CONFIG is set, so we must
* fire this manually. We'll fail here if the values are no good.
*/
$wpdb->db_connect();

if ( ! empty( $wpdb->error ) ) {
    _aap_fail( $wpdb->error->get_error_message() . $tryagain_link );
}

$errors = $wpdb->suppress_errors();
$wpdb->query( "SELECT `".$prefix."`" );
$wpdb->suppress_errors( $errors );

if ( ! $wpdb->last_error ) {
    // MySQL was able to parse the prefix as a value, which we don't want. Bail.
    _aap_fail( __( '<strong>Error:</strong> "Table Prefix" is invalid.' ) );
}

// Generate keys and salts using secure CSPRNG; fallback to API if enabled; further fallback to original wp_generate_password().
try {
    $chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_ []{}<>~`+=,.;:/?|';
    $max   = strlen( $chars ) - 1;
    for ( $i = 0; $i < 8; $i++ ) {
        $key = '';
        for ( $j = 0; $j < 64; $j++ ) {
            $key .= substr( $chars, random_int( 0, $max ), 1 );
        }
        $secret_keys[] = $key;
    }
} catch ( Exception $ex ) {
    $no_api = isset( $_POST['noapi'] );

    if ( ! $no_api ) {
        $secret_keys = wp_remote_get( 'https://api.wordpress.org/secret-key/1.1/salt/' );
    }

    if ( $no_api || is_wp_error( $secret_keys ) ) {
        $secret_keys = array();
        for ( $i = 0; $i < 8; $i++ ) {
            $secret_keys[] = wp_generate_password( 64, true, true );
        }
    } else {
        $secret_keys = explode( "\n", wp_remote_retrieve_body( $secret_keys ) );
        foreach ( $secret_keys as $k => $v ) {
            $secret_keys[ $k ] = substr( $v, 28, 64 );
        }
    }
}

$key = 0;
foreach ( $config_file as $line_num => $line ) {
    if ( str_starts_with( $line, '$table_prefix =' ) ) {
        $config_file[ $line_num ] = '$table_prefix = \'' . addcslashes( $prefix, "\\'" ) . "';\r\n";
        continue;
    }

    if ( ! preg_match( '/^define\(\s*\'([A-Z_]+)\',([ ]+)/', $line, $match ) ) {
        continue;
    }

    $constant = $match[1];
    $padding  = $match[2];

    switch ( $constant ) {
        case 'DB_NAME':
        case 'DB_USER':
        case 'DB_PASSWORD':
        case 'DB_HOST':
            $config_file[ $line_num ] = "define( '" . $constant . "'," . $padding . "'" . addcslashes( constant( $constant ), "\\'" ) . "' );\r\n";
            break;
        case 'DB_CHARSET':
            if ( 'utf8mb4' === $wpdb->charset || ( ! $wpdb->charset && $wpdb->has_cap( 'utf8mb4' ) ) ) {
                $config_file[ $line_num ] = "define( '" . $constant . "'," . $padding . "'utf8mb4' );\r\n";
            }
            break;
        case 'AUTH_KEY':
        case 'SECURE_AUTH_KEY':
        case 'LOGGED_IN_KEY':
        case 'NONCE_KEY':
        case 'AUTH_SALT':
        case 'SECURE_AUTH_SALT':
        case 'LOGGED_IN_SALT':
        case 'NONCE_SALT':
            $config_file[ $line_num ] = "define( '" . $constant . "'," . $padding . "'" . $secret_keys[ $key++ ] . "' );\r\n";
            break;
    }
}
unset( $line );

/*
 * If this file doesn't exist, then we are using the wp-config-sample.php
 * file one level up, which is for the develop repo.
 */
if ( file_exists( ABSPATH . 'wp-config-sample.php' ) ) {
    $path_to_wp_config = ABSPATH . 'wp-config.php';
} else {
    $path_to_wp_config = dirname( ABSPATH ) . '/wp-config.php';
}

$error_message = '';
$handle        = fopen( $path_to_wp_config, 'w' );
/*
 * Why check for the absence of false instead of checking for resource with is_resource()?
 * To future-proof the check for when fopen returns object instead of resource, i.e. a known
 * change coming in PHP.
 */
if ( false !== $handle ) {
    foreach ( $config_file as $line ) {
        fwrite( $handle, $line );
    }
    fclose( $handle );
} else {
    $wp_config_perms = fileperms( $path_to_wp_config );
    if ( ! empty( $wp_config_perms ) && ! is_writable( $path_to_wp_config ) ) {
        $error_message = sprintf(
            /* translators: 1: wp-config.php, 2: Documentation URL. */
            __( 'You need to make the file %1$s writable before you can save your changes. See <a href="%2$s">Changing File Permissions</a> for more information.' ),
            '<code>wp-config.php</code>',
            __( 'https://wordpress.org/documentation/article/changing-file-permissions/' )
        );
    } else {
        $error_message = sprintf(
            /* translators: %s: wp-config.php */
            __( 'Unable to write to %s file.' ),
            '<code>wp-config.php</code>'
        );
    }

    _aap_fail($error_message);
}

chmod( $path_to_wp_config, 0666 );

_aap_success('ok');
''', {
            'post': {
                'dbname': dbname,
                'uname': uname,
                'pwd': pwd,
                'dbhost': dbhost,
                'prefix': prefix,
            }
        }, without_auth=True).strip()

        res_json = json.loads(res)

        return public.aap_t_simple_result(res_json['success'], res_json['res'])

    # 完成WP站点初始化
    def wp_install(self, weblog_title: str, user_name: str, user_email: str, user_password: str,
                   language: str) -> public.aap_t_simple_result:
        res = self.run_wp_with_cli(r'''
/**
 * We are installing.
 */
define( 'WP_INSTALLING', true );

/**
* Set site url.
*/
define('WP_SITEURL', $_aap_extra_data['site_url']);

/** Load WordPress Bootstrap */
require_once AAP_ABSPATH . 'wp-load.php';

/** Load WordPress Administration Upgrade API */
require_once ABSPATH . 'wp-admin/includes/upgrade.php';

/** Load WordPress Translation Install API */
require_once ABSPATH . 'wp-admin/includes/translation-install.php';

if (!function_exists('sanitize_locale_name')) {
    /**
     * Strips out all characters not allowed in a locale name.
     *
     * @since 6.2.1
     *
     * @param string $locale_name The locale name to be sanitized.
     * @return string The sanitized value.
     */
    function sanitize_locale_name( $locale_name ) {
        // Limit to A-Z, a-z, 0-9, '_', '-'.
        $sanitized = preg_replace( '/[^A-Za-z0-9_-]/', '', $locale_name );

        /**
         * Filters a sanitized locale name string.
         *
         * @since 6.2.1
         *
         * @param string $sanitized   The sanitized locale name.
         * @param string $locale_name The locale name before sanitization.
         */
        return apply_filters( 'sanitize_locale_name', $sanitized, $locale_name );
    }
}

$weblog_title = trim( wp_unslash($_aap_extra_data['weblog_title']) );
$user_name = trim( wp_unslash($_aap_extra_data['user_name']) );
$admin_email = trim( wp_unslash($_aap_extra_data['user_email']) );
$user_password = trim( wp_unslash($_aap_extra_data['user_password']) );
$language = sanitize_locale_name($_aap_extra_data['language']);
$is_public = 1;

$loaded_language = '';

// 下载语言包
if ( ! empty( $language ) ) {
    $loaded_language = wp_download_language_pack( $language );
    if ( $loaded_language ) {
        load_default_textdomain( $loaded_language );
        $GLOBALS['wp_locale'] = new WP_Locale();
    }
}

_aap_echo(wp_install( $weblog_title, $user_name, $admin_email, $is_public, '', wp_slash( $user_password ), $loaded_language ));
''', {
            'site_url': self.build_site_url(),
            'weblog_title': weblog_title,
            'user_name': user_name,
            'user_email': user_email,
            'user_password': user_password,
            'language': language,
        }, without_auth=True).strip()

        res_json = json.loads(res)

        if 'user_id' in res_json:
            self.__WP_ADMIN_ID = int(res_json['user_id'])

        # 上报WP站点安装成功
        if res_json['success']:
            threading.Thread(target=lambda: requests.post('{}/api/panel/wp_installed'.format(public.OfficialApiBase()))).start()

        return public.aap_t_simple_result(res_json['success'], res_json['res'])

    # 获取Wordpress当前设置的语言
    def get_local_language(self) -> str:
        return self.run_wp_with_cli(r'echo get_locale();').strip()

    # 获取Wordpress可安装的语言列表
    @classmethod
    def get_available_install_languages(cls) -> typing.Dict:
        cache_key = 'SHM_:_CACHED_WP_AVAILABLE_INSTALL_LANGUAGES'

        cached = public.cache_get(cache_key)

        if cached:
            return cached

        cached = requests.get(cls.__WP_API_BASE + '/translations/core/1.0').json()
        public.cache_set(cache_key, cached, 86400)

        return cached

    # 获取Wordpress已安装的语言列表
    def get_installed_languages(self) -> typing.List:
        return json.loads(self.run_wp_with_cli(r'''
/** WordPress Translation Installation API */
require_once ABSPATH . 'wp-admin/includes/translation-install.php';

_aap_success(get_available_languages());
''').strip())['res']

    # 更新语言
    def update_language(self, language: str) -> bool:
        res = self.run_wp_with_cli(r'''
require_once ABSPATH . 'wp-admin/includes/translation-install.php';

$user_language_old = get_user_locale();

$language = trim($_POST['WPLANG']);

if (in_array($language, ['en', 'en_US'], true)) {
    $language = '';
}

if (!empty($language)) {
    $language = wp_download_language_pack( $language );

    if ( empty($language) ) {
        _aap_fail('Install language failed');
    }
}

update_option('WPLANG', $language);

/*
 * Switch translation in case WPLANG was changed.
 * The global $locale is used in get_locale() which is
 * used as a fallback in get_user_locale().
 */
unset( $GLOBALS['locale'] );
$user_language_new = get_user_locale();
if ( $user_language_old !== $user_language_new ) {
    load_default_textdomain( $user_language_new );
}

_aap_success('ok');
''', {
            'post': {
                'WPLANG': language,
            }
        }).strip()

        res_json = json.loads(res)

        return res_json['success']

    # 获取本地Wordpress版本
    def get_local_version(self) -> str:
        wp_version_file = '{}/{}/version.php'.format(self.retrieve_wp_root_path(), self.retrieve_wp_inc())

        if not os.path.exists(wp_version_file):
            return '0.0.0'

        with open(wp_version_file, 'r') as fp:
            m = re.search(r'\$wp_version\s*=\s*([\'"])(\d+(?:\.\d+)+)\1\s*;', fp.read(512))

            if m:
                return m.group(2)

        return '0.0.0'

    # 获取最新Wordpress版本
    def get_latest_version(self, available: bool = False) -> typing.Dict:
        """
        :param available: 是否只获取最新且可用的版本
        :return: dict
        """
        if available:
            latest_versions = self.latest_versions()
            php_ver = self.retrieve_php_version()
            lst = list(filter(lambda x: php_ver >= '.'.join(str(x['php_version']).split('.')[:2]), latest_versions))
            if len(lst) < 1:
                return {}
            return lst[0]

        return self.__VERSION_MGR.latest_version()

    # 获取Wordpress可安装版本列表
    def latest_versions(self) -> typing.List:
        return self.__VERSION_MGR.latest_versions()

    # 下载Wordpress安装包
    def download_package(self, package_version: str) -> str:
        return self.__VERSION_MGR.download_package(package_version)

    # 获取Wordpress安装包下载进度
    def get_download_progress(self, package_version: str) -> typing.Dict:
        return self.__VERSION_MGR.get_download_progress(package_version)

    # 更新本地Wordpress到指定版本
    def update_version(self, upgrade_to: str, language: str = None, reinstall: bool = False) -> typing.Tuple:
        res = self.run_wp_with_cli(r'''
require_once ABSPATH . 'wp-admin/includes/class-wp-upgrader.php';

$upgrade_to = !empty($_aap_extra_data['version']) ? $_aap_extra_data['version'] : false;
$locale = !empty($_aap_extra_data['locale']) ? $_aap_extra_data['locale'] : 'en_US';

$update  = find_core_update( $upgrade_to, $locale );
if ( ! $update ) {
    _aap_fail('升级Wordpress版本失败');
}

$reinstall = !empty($_app_extra_data['reinstall']);

if ( $reinstall ) {
    $update->response = 'reinstall';
}

$skin     = new WP_Ajax_Upgrader_Skin();
$upgrader = new Core_Upgrader($skin);
$result   = $upgrader->upgrade($update);

if ( is_wp_error( $result ) ) {
    _aap_fail($result->get_error_message());
}

_aap_success($result);
''', {
            'reinstall': reinstall,
            'version': upgrade_to,
            'locale': language if language is not None else self.get_local_language(),
        }).strip()

        res_json = json.loads(res)

        return res_json['success'], res_json['res']

    # 查询管理员信息
    def get_admin_info(self) -> typing.Dict:
        return json.loads(self.run_wp_with_cli(r'_aap_success(wp_get_current_user()->to_array());').strip())['res']

    # 获取WP Toolkit要用到的配置信息
    def get_wp_toolkit_config_data(self):
        res = self.run_wp_with_cli(r'''
$locale = get_locale();

// 检查site_url的HTTP协议，如果与当前的site_url不一致则更新
$site_url = get_option('siteurl');

$raw_site_url_parse = wp_parse_url($site_url);
$cur_site_url_parse = wp_parse_url($_aap_extra_data['site_url']);

// 当HTTP协议不一致时更新siteurl
if (!empty($raw_site_url_parse) && !empty($cur_site_url_parse) && $raw_site_url_parse['scheme'] !== $cur_site_url_parse['scheme']) {
    if ( ! isset( $raw_site_url_parse['path'] ) ) {
        $raw_site_url_parse['path'] = '';
    }
    
    $site_url = $cur_site_url_parse['scheme'] . '://' . $raw_site_url_parse['host'] . $raw_site_url_parse['path'];

    update_option('siteurl', $site_url);
    update_option('home', $site_url);
}

_aap_success([
    'site_url'      => $site_url,
    'login_url'     => add_query_arg(['wp_lang' => $locale], wp_login_url()),
    'locale'        => $locale,
    'admin_info'    => wp_get_current_user()->to_array(),
    'whl_config'    => [
        'activated'             => is_plugin_active('wps-hide-login/wps-hide-login.php'),
        'whl_page'              => get_site_option( 'whl_page', 'login' ),
        'whl_redirect_admin'    => get_site_option( 'whl_redirect_admin', '404' ),
    ],
]);
''', {'site_url': self.build_site_url()}).strip()
        try:
            return json.loads(res.strip()).get('res', [])
        except:
            return res

    # 将Wordpress Ajax响应转换成aap_t_simple_result
    def __wp_ajax_response_to_aap_t_simple_result(self, wp_ajax_response_raw: str, default_success_msg: str = public.get_msg_gettext('Success'), default_fail_msg: str = public.get_msg_gettext('Failed')) -> public.aap_t_simple_result:
        res = json.loads(wp_ajax_response_raw.strip())

        if not res.get('success', False):
            errmsg = res.get('data', {}).get('error', None)

            if errmsg is None:
                errmsg = res.get('data', {}).get('errorMessage', default_fail_msg)

            return public.aap_t_simple_result(False, errmsg)

        return public.aap_t_simple_result(True, res.get('data', default_success_msg))

    # 命令行调用Wordpress Ajax Api
    def __wp_ajax(self, ajax_name: str, args: typing.Dict[str, typing.Any]) -> public.aap_t_simple_result:
        return self.__wp_ajax_response_to_aap_t_simple_result(self.run_wp_with_cli(r'''
require_once ABSPATH . 'wp-admin/includes/ajax-actions.php';

$_REQUEST['_wpnonce'] = wp_create_nonce('updates');

wp_ajax_{ajax_name}();
'''.format(ajax_name=ajax_name), {'post': args}))

    # 切换插件/主题自动更新设置
    def __toggle_auto_updates(self, wp_type: str, asset: str, state: str) -> public.aap_t_simple_result:
        return self.__wp_ajax_response_to_aap_t_simple_result(self.run_wp_with_cli(r'''
require_once ABSPATH . 'wp-admin/includes/ajax-actions.php';

$_REQUEST['_wpnonce'] = wp_create_nonce('updates');

wp_ajax_toggle_auto_updates();
''', {'post': {'type': wp_type, 'asset': asset, 'state': state}}),
                                                              default_success_msg=public.get_msg_gettext('Toggle wordpress plugin/theme auto-update setting successfully'),
                                                              default_fail_msg=public.get_msg_gettext('Toggle wordpress plugin/theme auto-update setting failed'))

    # 检查已安装主题的最新版本信息
    def check_update_for_themes(self) -> bool:
        self.run_wp_with_cli(r'''wp_update_themes();''')
        return True

    # 获取已安装的主题列表
    def installed_themes(self, force_check: bool = False) -> typing.List:
        res = self.run_wp_with_cli(r'''
require ABSPATH . WPINC . '/version.php';        

if ($_aap_extra_data['force_check']) {
    wp_update_themes();
}

$themes = wp_get_themes();
$current_theme = get_stylesheet();
$auto_updates = (array) get_site_option( 'auto_update_themes', [] );
$theme_update = get_site_transient('update_themes');
$theme_update_response = empty($theme_update->response) ? [] : $theme_update->response;

$res = [];

foreach($themes as $theme_name => $theme) {
    $stylesheet = $theme->get_stylesheet();
    $update_info = empty($theme_update_response[$stylesheet]) ? null : (array)$theme_update_response[$stylesheet];
    $cur_version = $theme->get('Version');
    $latest_version = $cur_version;
    $can_update = false;
    
    if (!empty($update_info)) {
        $latest_version = $update_info['new_version'];
        
        if (version_compare(PHP_VERSION, $update_info['requires_php'], '>=') && version_compare($wp_version, $update_info['requires'], '>=')) {
            $can_update = true;
        }
    }

    $res[] = [
        'name' => $theme_name,
        'version' => $cur_version,
        'title' => $theme_name.' '.$cur_version,
        'latest_version' => $latest_version,
        'can_update' => $can_update,
        // 'update_info' => $update_info,
        'is_theme_activate' => $stylesheet === $current_theme,
        'stylesheet' => $stylesheet,
        'author' => $theme->get('Author'),
        'theme_uri' => $theme->get('ThemeURI'),
        'author_uri' => $theme->get('AuthorURI'),
        'description' => $theme->get('Description'),
        'auto_update' => in_array($stylesheet, $auto_updates),
    ];
}

_aap_success($res);
''', {'force_check': force_check})
        try:
            return json.loads(res.strip()).get('res', [])
        except:
            return res

    # 搜索主题（类方法）
    @classmethod
    def query_themes(cls, keywords: str = '', p: int = 1, p_size: int = 20, set_id: typing.Optional[int] = None) -> public.aap_t_simple_result:
        res = wp_themes().query(p, p_size, keywords)

        # 检查搜索到的主题中是否存在于Set中
        if set_id is not None:
            slugs = public.S('wordpress_set_items').where('set_id', set_id).where('type', 2).column('slug')

            for item in res['list']:
                item['is_in_set'] = item['slug'] in slugs

        return public.aap_t_simple_result(True, res)

    # 搜索主题（列表）
    def search_themes(self, keywords: str = '', p: int = 1, p_size: int = 20) -> public.aap_t_simple_result:
        # 获取已安装的主题列表
        installed_themes = self.installed_themes()

        # 取出所有stylesheet
        installed_stylesheets = set(map(lambda x: x['stylesheet'], installed_themes))

        # 搜索主题
        queried_themes = self.__THEME_API.query(p, p_size, keywords)

        # 检查获取到的主题列表中是否存在已安装的主题
        for item in queried_themes['list']:
            item['installed'] = False

            if item['slug'] in installed_stylesheets:
                item['installed'] = True

        return public.aap_t_simple_result(True, queried_themes)

    # TODO 查询主题详细信息
    def theme_information(self, slug: str) -> public.aap_t_simple_result:
        pass

    # 安装主题
    def install_theme(self, slug: str) -> public.aap_t_simple_result:
        return self.__wp_ajax_response_to_aap_t_simple_result(self.run_wp_with_cli(r'''
require_once ABSPATH . 'wp-admin/includes/ajax-actions.php';

$_REQUEST['_wpnonce'] = wp_create_nonce('updates');

wp_ajax_install_theme();
''', {'post': {'slug': slug}}))

    # 更新主题
    def update_theme(self, stylesheet: str) -> public.aap_t_simple_result:
        return self.__wp_ajax_response_to_aap_t_simple_result(self.run_wp_with_cli(r'''
require_once ABSPATH . 'wp-admin/includes/ajax-actions.php';

$_REQUEST['_wpnonce'] = wp_create_nonce('updates');

wp_ajax_update_theme();
''', {'post': {'slug': stylesheet}}))

    # 切换主题
    def switch_theme(self, stylesheet: str) -> bool:
        self.run_wp_with_cli(r'''switch_theme($_aap_extra_data['stylesheet']);''', {'stylesheet': stylesheet})
        return True

    # 卸载主题
    def uninstall_theme(self, stylesheet: str) -> public.aap_t_simple_result:
        return self.__wp_ajax_response_to_aap_t_simple_result(self.run_wp_with_cli(r'''
$current_theme = get_stylesheet();

// 正在应用中主题不能删除
if ($current_theme === $_POST['slug']) {
	wp_send_json_error( array( 'error' => __( 'You cannot delete a theme while it is active on the main site.' ) ) );
}

require_once ABSPATH . 'wp-admin/includes/ajax-actions.php';

$_REQUEST['_wpnonce'] = wp_create_nonce('updates');

wp_ajax_delete_theme();
''', {'post': {'slug': stylesheet}}))

    # 开启主题自动更新
    def enable_theme_auto_update(self, stylesheet: str) -> public.aap_t_simple_result:
        return self.__toggle_auto_updates('theme', stylesheet, 'enable')

    # 关闭主题自动更新
    def disable_theme_auto_update(self, stylesheet: str) -> public.aap_t_simple_result:
        return self.__toggle_auto_updates('theme', stylesheet, 'disable')

    # 搜索插件（类方法）
    @classmethod
    def query_plugins(cls, keywords: str, p: int = 1, p_size: int = 20, set_id: typing.Optional[int] = None) -> public.aap_t_simple_result:
        res = wp_plugins().query(p, p_size, keywords)

        # 检查搜索到的插件中是否存在于Set中
        if set_id is not None:
            slugs = public.S('wordpress_set_items').where('set_id', set_id).where('type', 1).column('slug')

            for item in res['list']:
                item['is_in_set'] = item['slug'] in slugs

        return public.aap_t_simple_result(True, res)

    # 搜索插件（列表）
    def search_plugins(self, keywords: str, p: int = 1, p_size: int = 20) -> public.aap_t_simple_result:
        # 获取所有已安装的插件
        installed_plugins = self.installed_plugins()

        # # 取出所有name
        # installed_names = set(map(lambda x: x['name'], installed_plugins))
        # 取出所有的slug
        installed_slugs = set(map(lambda x: x['slug'], installed_plugins))

        # 搜索插件列表
        queried_plugins = self.__PLUGIN_API.query(p, p_size, keywords)

        # 检查获取的插件中是否存在已安装的插件
        for item in queried_plugins['list']:
            item['installed'] = False

            # if item['name'] in installed_names:
            #     item['installed'] = True
            if item['slug'] in installed_slugs:
                item['installed'] = True

        return public.aap_t_simple_result(True, queried_plugins)

    # 查询插件详细信息
    def plugin_information(self, slug: str) -> public.aap_t_simple_result:
        return public.aap_t_simple_result(True, self.__PLUGIN_API.info())

    # 检查已安装插件的最新版本信息
    def check_update_for_plugins(self) -> bool:
        self.run_wp_with_cli(r'''wp_update_plugins();''')
        return True

    # 获取已安装的插件列表
    def installed_plugins(self, force_check: bool = False) -> typing.Dict:
        res = self.run_wp_with_cli(r'''
require ABSPATH . WPINC . '/version.php';

if ($_aap_extra_data['force_check']) {
    wp_update_plugins();
}

$plugins = get_plugins();
$auto_updates = (array) get_site_option( 'auto_update_plugins', [] );
$plugin_update = get_site_transient('update_plugins');
$plugin_update_response = empty($plugin_update->response) ? [] : $plugin_update->response;

$res = [];

foreach($plugins as $k => $item) {
    $update_info = empty($plugin_update_response[$k]) ? null : (array)$plugin_update_response[$k];
    $cur_version = $item['Version'];
    $latest_version = $cur_version;
    $can_update = false;
    
    if (!empty($update_info)) {
        $latest_version = $update_info['new_version'];
        
        if (version_compare(PHP_VERSION, $update_info['requires_php'], '>=') && version_compare($wp_version, $update_info['requires'], '>=')) {
            $can_update = true;
        }
    }

    $res[] = [
        'name'                  => $item['Name'],
        'slug'                  => explode('/', $k)[0],
        'version'               => $cur_version,
        'latest_version'        => $latest_version,
        'can_update'            => $can_update,
        // 'update_info'        => $update_info,
        'title'                 => $item['Name'].' '.$cur_version,
        'description'           => $item['Description'],
        'author'                => $item['Author'],
        'author_uri'            => $item['AuthorURI'],
        'plugin_uri'            => $item['PluginURI'],
        'is_plugin_activate'    => is_plugin_active($k),
        'plugin_file'           => $k,
        'auto_update'           => in_array($k, $auto_updates),
    ];
}

_aap_success($res);
''', {'force_check': force_check}).strip()
        try:
            return json.loads(res.strip()).get('res', [])
        except:
            return res

    # 激活插件
    def activate_plugins(self, plugins: typing.Union[str, typing.List]) -> bool:
        if isinstance(plugins, str):
            plugins = [plugins]

        res = self.run_wp_with_cli(r'var_dump(activate_plugins($_aap_extra_data));', plugins).strip()

        if res == 'bool(true)':
            return True

        return False

    # 停用插件
    def deactivate_plugins(self, plugins: typing.Union[str, typing.List]) -> bool:
        if isinstance(plugins, str):
            plugins = [plugins]

        res = self.run_wp_with_cli(r'var_dump(deactivate_plugins($_aap_extra_data));', plugins).strip()

        if res == 'NULL':
            return True

        return False

    # 安装插件
    def install_plugin(self, slug: str) -> public.aap_t_simple_result:
        return self.__wp_ajax_response_to_aap_t_simple_result(self.run_wp_with_cli(r'''
require_once ABSPATH . 'wp-admin/includes/ajax-actions.php';

$_REQUEST['_wpnonce'] = wp_create_nonce('updates');

wp_ajax_install_plugin();
''', {'post': {'slug': slug}}))

    # 卸载插件
    def uninstall_plugin(self, plugin_file: str) -> public.aap_t_simple_result:
        p, _ = os.path.splitext(plugin_file)

        return self.__wp_ajax_response_to_aap_t_simple_result(self.run_wp_with_cli(r'''
require_once ABSPATH . 'wp-admin/includes/ajax-actions.php';

$_REQUEST['_wpnonce'] = wp_create_nonce('updates');

wp_ajax_delete_plugin();
''', {'post': {'slug': os.path.basename(p), 'plugin': plugin_file}}))

    # 开启插件自动更新
    def enable_plugin_auto_update(self, plugin_file: str) -> public.aap_t_simple_result:
        return self.__toggle_auto_updates('plugin', plugin_file, 'enable')

    # 关闭插件自动更新
    def disable_plugin_auto_update(self, plugin_file: str) -> public.aap_t_simple_result:
        return self.__toggle_auto_updates('plugin', plugin_file, 'disable')

    # 更新指定插件到最新版本
    def update_plugin(self, plugin_file: str) -> public.aap_t_simple_result:
        p, _ = os.path.splitext(plugin_file)

        return self.__wp_ajax_response_to_aap_t_simple_result(self.run_wp_with_cli(r'''
require_once ABSPATH . 'wp-admin/includes/ajax-actions.php';

$_REQUEST['_wpnonce'] = wp_create_nonce('updates');

wp_ajax_update_plugin();
''', {'post': {'slug': os.path.basename(p), 'plugin': plugin_file}}))

    # 检查插件是否安装
    def is_plugin_installed(self, slug: str) -> bool:
        return os.path.exists(
            r'{root_path}/wp-content/plugins/{slug}/{slug}.php'.format(root_path=self.retrieve_wp_root_path(),
                                                                       slug=slug))

    # 检查插件是否处于激活状态
    def is_plugin_activate(self, slug: str) -> bool:
        res = self.run_wp_with_cli(r'''var_dump(is_plugin_active($_aap_extra_data['plugin']));''',
                                   {'plugin': '{slug}/{slug}.php'.format(slug=slug)}).strip()

        if res == 'bool(true)':
            return True

        return False

    # 一键登录管理后台
    # @only_pro_members
    def auto_login(self):
        # 使用线程锁来避免并发访问导致的BUG
        with self.__LOCK:
            # 通过在default-filters.php中添加hook完实现登录状态与Cookie的设置
            default_filter_php = '{}/{}/default-filters.php'.format(self.retrieve_wp_root_path(),
                                                                    self.retrieve_wp_inc())

            with open(default_filter_php, 'r') as fp:
                php_code = fp.read()

            if re.search(r"require_once\s*ABSPATH\s*\.\s*'wp-admin/includes/auto-login\.php'\s*;", php_code) is None:
                with open(default_filter_php, 'a') as fp:
                    fp.write(r'''
// ---- AAPANEL AUTO-LOGIN BEGIN ----
require_once ABSPATH . 'wp-admin/includes/auto-login.php';
// ---- AAPANEL AUTO-LOGIN END ----
''')

            mark_file_name = public.GetRandomString(16)
            mark_file = '{}/wp-admin/includes/aap-login-{}.mark'.format(self.retrieve_wp_root_path(), mark_file_name)

            # 删除掉多余的mark文件
            from glob import glob
            for tmp_mark_file in glob('{}/wp-admin/includes/aap-login-*.mark'.format(self.retrieve_wp_root_path())):
                os.remove(tmp_mark_file)

            with open(mark_file, 'w') as fp:
                fp.write('True')

            token_key = public.GetRandomString(16)
            token = public.GetRandomString(32)

            auto_login_wp = r'''<?php

add_action('wp_loaded', function() {{
    if (!empty($_REQUEST['{token_key}']) && $_REQUEST['{token_key}'] === '{token_value}' && is_file(ABSPATH . 'wp-admin/includes/aap-login-{mark_file_name}.mark')) {{
        add_action('set_auth_cookie', function($auth_cookie) {{
            $_COOKIE[SECURE_AUTH_COOKIE] = $auth_cookie;
            $_COOKIE[AUTH_COOKIE] = $auth_cookie;
            $_COOKIE[LOGGED_IN_COOKIE] = $auth_cookie;
        }});
        
        add_action('admin_init', function() {{
            @unlink(ABSPATH . 'wp-admin/includes/aap-login-{mark_file_name}.mark');
        }});

        $user = wp_set_current_user({user_id});
        wp_set_auth_cookie({user_id});
        
        do_action('wp_login', $user->user_login, $user);
        
        wp_redirect(admin_url());
    }}
}});
'''.format(token_key=token_key, token_value=token, user_id=self.retrieve_administrator_id(),
           mark_file_name=mark_file_name)

            with open('{}/wp-admin/includes/auto-login.php'.format(self.retrieve_wp_root_path()), 'w') as fp:
                fp.write(auto_login_wp)

            from BTPanel import redirect

            return '{}/wp-admin/?{}={}'.format(self.get_site_url(), token_key, token)

    # 获取WP站点URL
    def get_site_url(self) -> str:
        return self.run_wp_with_cli(r'''
$site_url = get_option('siteurl');

$raw_site_url_parse = wp_parse_url($site_url);
$cur_site_url_parse = wp_parse_url($_aap_extra_data['site_url']);

// 当HTTP协议不一致时更新siteurl
if (!empty($raw_site_url_parse) && !empty($cur_site_url_parse) && $raw_site_url_parse['scheme'] !== $cur_site_url_parse['scheme']) {
    if ( ! isset( $raw_site_url_parse['path'] ) ) {
        $raw_site_url_parse['path'] = '';
    }
    
    $site_url = $cur_site_url_parse['scheme'] . '://' . $raw_site_url_parse['host'] . $raw_site_url_parse['path'];

    update_option('siteurl', $site_url);
    update_option('home', $site_url);
}

echo $site_url;
''', {'site_url': self.build_site_url()}).strip()

    # 设置WP站点URL
    def set_site_url(self, site_url: str) -> bool:
        self.run_wp_with_cli(r'''
update_option('siteurl', $_aap_extra_data['site_url']);
update_option('home', $_aap_extra_data['site_url']);
''', {'site_url': site_url})

        return True

    # 获取WP管理后台登录URL
    def get_login_url(self) -> str:
        return self.run_wp_with_cli(r'echo wp_login_url();').strip()

    # 更新管理员密码
    def set_admin_password(self, admin_password: str) -> bool:
        self.run_wp_with_cli(r'''wp_set_password($_aap_extra_data['admin_password'], get_current_user_id());''',
                             {'admin_password': admin_password})

        return True

    # 更新管理员邮箱
    def set_admin_email(self, admin_email: str) -> bool:
        self.run_wp_with_cli(r'''
global $wpdb;

$wpdb->update(
    $wpdb->users,
    array(
        'user_email' => $_aap_extra_data['admin_email'],
    ),
    array( 'ID' => get_current_user_id() )
);

clean_user_cache( get_current_user_id() );

update_option('admin_email', $_aap_extra_data['admin_email']);
delete_option('adminhash');
delete_option('new_admin_email');
''', {'admin_email': admin_email})

        return True

    # 更新wp-config.php配置文件
    def update_wp_config(self, update_config: typing.Dict[str, typing.Union[str, int, float, bool]]) -> public.aap_t_simple_result:
        return wpdeployment.update_wp_config('{}/wp-config.php'.format(self.retrieve_wp_root_path()), update_config)

    # 安装、开启并配置nginx-helper插件
    def init_plugin_nginx_helper(self) -> bool:
        slug = 'nginx-helper'

        if not self.is_plugin_installed(slug):
            # 安装nginx-helper插件
            self.install_plugin(slug)

        # 插件已激活时，不继续下面的激活操作
        if self.is_plugin_activate(slug):
            return True

        self.run_wp_with_cli(r'''
// 激活插件
if (!is_plugin_active($_aap_extra_data['activate_plugin'])) {
    activate_plugin($_aap_extra_data['activate_plugin']);
}

// 配置插件
$_POST['smart_http_expire_form_nonce'] = wp_create_nonce('smart-http-expire-form-nonce');

require ABSPATH.'wp-content/plugins/nginx-helper/admin/partials/nginx-helper-general-options.php';
''', {
            'activate_plugin': '{slug}/{slug}.php'.format(slug=slug),
            'post': {
                "enable_purge": "1",
                "is_submit": "1",
                "cache_method": "enable_fastcgi",
                "purge_method": "unlink_files",
                "redis_hostname": "127.0.0.1",
                "redis_port": "6379",
                "redis_prefix": "nginx-cache",
                "purge_homepage_on_edit": "1",
                "purge_homepage_on_del": "1",
                "purge_page_on_mod": "1",
                "purge_page_on_new_comment": "1",
                "purge_page_on_deleted_comment": "1",
                "purge_archive_on_edit": "1",
                "purge_archive_on_del": "1",
                "purge_archive_on_new_comment": "1",
                "purge_archive_on_deleted_comment": "1",
                "purge_url": "",
                "log_level": "INFO",
                "log_filesize": "5",
                "smart_http_expire_form_nonce": '',
                "smart_http_expire_save": "Save All Changes",
            },
        })

        wpdeployment_obj = wpdeployment()
        wpdeployment_obj.set_wpmgr(self)

        # 设置fastcgi缓存目录
        self.update_wp_config({'RT_WP_NGINX_HELPER_CACHE_PATH': '/dev/shm/nginx-cache/wp'})

        # 修改.user.ini
        with wpdeployment_obj.modify_user_ini_with_context() as user_ini_file:
            with open(user_ini_file, 'r') as fp:
                content = fp.read()

            # 更新.user.ini
            if content.find(':/dev/shm/nginx-cache/wp') < 0:
                content = re.sub(r'open_basedir\s*=\s*([^:]+(?::[^:]+)*)', r'open_basedir=\g<1>:/dev/shm/nginx-cache/wp', content)
                with open(user_ini_file, 'w') as fp:
                    fp.write(content)

        return True

    # 调用nginx-helper插件清理fastcgi缓存
    def purge_cache_with_nginx_helper(self) -> bool:
        # 确保nginx-helper插件已安装并处于激活状态
        self.init_plugin_nginx_helper()

        # 清理缓存
        self.run_wp_with_cli(r'''
global $nginx_purger;

$nginx_purger->purge_them_all();
''')

        try:
            # 清理WordPress自带缓存
            self.run_wp_with_cli(r'''
            // 清理对象缓存
            wp_cache_flush();
    
            // 清理Transient缓存
            global $wpdb;
            $wpdb->query("DELETE FROM $wpdb->options WHERE option_name LIKE '_transient_%' OR option_name LIKE '_site_transient_%'");
    
            echo "WordPress内置缓存清理成功";
            ''')

            # 清理常见缓存插件缓存
            plugins = {
                'wp-super-cache': r'''
                       if (function_exists('wp_cache_clear_cache')) {
                           wp_cache_clear_cache();
                           echo "WP Super Cache清理成功";
                       } else {
                           echo "WP Super Cache未激活";
                       }
                   ''',
                'w3-total-cache': r'''
                       if (class_exists('W3_Plugin_TotalCacheAdmin')) {
                           $w3tc = W3_Plugin_TotalCacheAdmin::instance();
                           $w3tc->flush_all();
                           echo "W3 Total Cache清理成功";
                       } else {
                           echo "W3 Total Cache未激活";
                       }
                   ''',
                'wp-rocket': r'''
                       if (function_exists('rocket_clean_domain')) {
                           rocket_clean_domain();
                           echo "WP Rocket清理成功";
                       } else {
                           echo "WP Rocket未激活";
                       }
                   '''
            }

            for plugin, code in plugins.items():
                self.run_wp_with_cli(code)
        except Exception as e:
            pass

        return True

    # 安装、开启并配置wps-hide-login插件
    def init_plugin_wps_hide_login(self, whl_page: str, whl_redirect_admin: str) -> bool:
        slug = 'wps-hide-login'

        if self.is_plugin_installed(slug):
            return True

        # 安装wps-hide-login插件
        self.install_plugin(slug)

        self.run_wp_with_cli(r'''
// 激活插件
if (!is_plugin_active($_aap_extra_data['activate_plugin'])) {
    activate_plugin($_aap_extra_data['activate_plugin']);
}

// 配置插件
$_REQUEST['_wpnonce'] = wp_create_nonce('siteoptions');

\WPS\WPS_Hide_Login\Plugin::get_instance()->update_wpmu_options();
''', {
            'activate_plugin': '{slug}/{slug}.php'.format(slug=slug),
            'post': {
                'whl_page': whl_page,
                'whl_redirect_admin': whl_redirect_admin,
            },
        })
        return True

    # 配置wps-hide-login插件
    def config_plugin_wps_hide_login(self, whl_page: str, whl_redirect_admin: str) -> bool:
        slug = 'wps-hide-login'

        # 插件未安装时，进行插件初始化操作
        if not self.is_plugin_installed(slug):
            return self.init_plugin_wps_hide_login(whl_page, whl_redirect_admin)

        self.run_wp_with_cli(r'''
// 激活插件
if (!is_plugin_active($_aap_extra_data['activate_plugin'])) {
    activate_plugin($_aap_extra_data['activate_plugin']);
}

$_REQUEST['_wpnonce'] = wp_create_nonce('siteoptions');

\WPS\WPS_Hide_Login\Plugin::get_instance()->update_wpmu_options();
''', {
            'activate_plugin': '{slug}/{slug}.php'.format(slug=slug),
            'post': {
                'whl_page': whl_page,
                'whl_redirect_admin': whl_redirect_admin,
            },
        })
        return True

    # 获取wps-hide-login插件的配置信息
    def get_config_wps_hide_login(self) -> typing.Dict:
        slug = 'wps-hide-login'

        # 插件未安装时，返回默认配置
        if not self.is_plugin_installed(slug):
            return {
                'activated': False,
                'whl_page': 'login',
                'whl_redirect_admin': '404',
            }

        res = self.run_wp_with_cli(r'''
echo \json_encode([
    'activated' => is_plugin_active($_aap_extra_data['plugin']),
    'whl_page' => get_site_option( 'whl_page', 'login' ),
    'whl_redirect_admin' => get_site_option( 'whl_redirect_admin', '404' ),
], JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES);
''', {'plugin': '{slug}/{slug}.php'.format(slug=slug)}).strip()

        return json.loads(res)

    # 框架文件完整性校验
    def integrity_check(self) -> public.aap_t_simple_result:
        try:
            return self.__VERSION_MGR.checksums(self.get_local_version(), self.retrieve_wp_root_path())
        except Exception as e:
            return False, str(e)

    # 重新下载并安装框架文件
    # @only_pro_members
    def reinstall_package(self) -> public.aap_t_simple_result:
        package_file = self.__VERSION_MGR.download_package(self.get_local_version())

        # 获取网站目录
        site_path = self.retrieve_wp_root_path()

        # 解压wordpress框架文件并覆盖到网站目录下
        self.__VERSION_MGR.unpack(package_file, site_path, ('wp-content/',))

        # 修正网站文件权限与目录权限
        wpdeployment_obj = wpdeployment()
        wpdeployment_obj.set_wpmgr(self)
        wpdeployment_obj.fix_permissions(site_path)

        return public.aap_t_simple_result(True, public.lang('WordPress核心文件已从wordpress.org重新安装'))

    # 获取所有WP站点
    @classmethod
    def all_sites(cls):
        data = public.S('sites', 'site')\
            .where('project_type', 'WP2')\
            .field('id', 'name')\
            .order('id', 'desc')\
            .select()

        if not isinstance(data, list):
            return []

        return data


# WP-Nginx-FastCGI-cache配置管理
class wpfastcgi_cache:

    # 构造函数
    def __init__(self):
        self.__LOG_FILE = '/tmp/schedule.log'
        self.__CACHE_PATH = '/dev/shm/nginx-cache/wp'

    # 输出日志
    def __log(self, content: str):
        with open(self.__LOG_FILE, 'a') as fp:
            fp.write(content + '\n')

    # 确保缓存目录创建
    def __ensure_cache_path_exists(self):
        if not os.path.exists(self.__CACHE_PATH):
            os.makedirs(self.__CACHE_PATH)
            cache_path_parent = os.path.dirname(self.__CACHE_PATH)
            os.system('chmod -R 755 ' + cache_path_parent)
            os.system('chown -R www.www ' + cache_path_parent)

    # 获取nginx-fastcgi配置文件内容
    def get_fastcgi_conf(self, php_v: str) -> str:
        if php_v.find('.') > -1:
            php_v = php_v.replace('.', '')

        return r"""
set $skip_cache 0;

if ($request_method = POST) {
    set $skip_cache 1;
}  

if ($query_string != "") {
    set $skip_cache 1;
} 

if ($request_uri ~* "/wp-admin/|/xmlrpc.php|wp-.*.php|/feed/|index.php|sitemap(_index)?.xml") {
    set $skip_cache 1;
}

if ($http_cookie ~* "comment_author|wordpress_[a-f0-9]+|wp-postpass|wordpress_no_cache|wordpress_logged_in") {
    set $skip_cache 1;
}

location ~ (^.+?\.php)(/|$) {
    if ( !-f $document_root$1 ) {
        return 404;
    }

    fastcgi_pass unix:/tmp/php-cgi-%s.sock;
    fastcgi_index index.php;
    include fastcgi.conf;  
    add_header Strict-Transport-Security "max-age=63072000; includeSubdomains; preload";
    fastcgi_cache_bypass $skip_cache;
    fastcgi_no_cache $skip_cache;
    add_header X-Cache "$upstream_cache_status From $host";
    fastcgi_cache WORDPRESS;
    add_header Cache-Control  max-age=0;
    add_header Nginx-Cache "$upstream_cache_status";
    add_header Last-Modified $date_gmt;
    add_header X-Frame-Options SAMEORIGIN;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    etag  on;
    fastcgi_cache_valid 200 301 302 1d;
}

location ~ /purge(/.*) {
    allow 127.0.0.1;
    deny all;
    fastcgi_cache_purge WORDPRESS "$scheme$request_method$host$1";
}
""" % php_v

    # 检查fastcgi-cache开启状态
    def get_fast_cgi_status(self, sitename: str, php_v: str) -> bool:
        # 仅支持nginx
        if public.get_webserver() != "nginx":
            return False

        if php_v.find('.') > -1:
            php_v = php_v.replace('.', '')

        conf_path = "{}/vhost/nginx/{}.conf".format(public.get_panel_path(), sitename)
        content = public.readFile(conf_path)

        if not content:
            raise public.HintException(public.get_msg_gettext('Site nginx config not exists'))

        fastcgi_conf = "include enable-php-{}-wpfastcgi.conf;".format(php_v)

        return str(content).find(fastcgi_conf) > -1

    # 设置nginx主配置文件
    def set_nginx_conf(self) -> bool:
        self.__ensure_cache_path_exists()
        wp_conf = "/www/server/panel/vhost/nginx/wp_fastcgi.conf"
        conf = r"""
#BTPANEL_FASTCGI_CONF_BEGIN
fastcgi_cache_key "$scheme$request_method$host$request_uri";
fastcgi_cache_path /dev/shm/nginx-cache/wp levels=1:2 keys_zone=WORDPRESS:100m inactive=60m max_size=1g;
fastcgi_cache_use_stale error timeout invalid_header http_500;
fastcgi_ignore_headers Cache-Control Expires Set-Cookie;
#BTPANEL_FASTCGI_CONF_END
"""
        if not os.path.exists(wp_conf):
            public.writeFile(wp_conf, conf)
            conf_pass = public.checkWebConfig()
            if conf_pass != True:
                os.remove(wp_conf)
                self.__log("|-Nginx FastCgi 配置错误! {}".format(conf_pass))
                return False
            self.__log("|-Nginx FastCgi 配置文件创建成功")
            return True
        else:
            if "#BTPANEL_FASTCGI_CONF_BEGIN" in public.readFile(wp_conf):
                self.__log("|-Nginx FastCgi 缓存配置已存在")
                return True
            else:
                self.__log("|-wp默认缓存配置文件已被占用")
                return False


    # 设置 /etc/init.d/nginx
    def set_nginx_init(self) -> bool:
        # if not os.path.exists("/dev/shm/nginx-cache/wp"):
        #     os.makedirs("/dev/shm/nginx-cache/wp")
        #     one_key_wp().set_permission("/dev/shm/nginx-cache")
        conf2 = """
     #AAPANEL_FASTCGI_CONF_BEGIN
     mkdir -p /dev/shm/nginx-cache/wp
     #AAPANEL_FASTCGI_CONF_END
 """

        init_path = "/etc/init.d/nginx"
        public.back_file(init_path)
        content_init = public.readFile(init_path)

        if not content_init:
            return False

        if "#AAPANEL_FASTCGI_CONF_BEGIN" in content_init:
            self.__log("|-Nginx init FastCgi cache configuration already exists")
            print("Nginx init FastCgi cache configuration already exists")
            return True

        rep2 = r"\$NGINX_BIN -c \$CONFIGFILE"
        content_init = re.sub(rep2, conf2 + "        $NGINX_BIN -c $CONFIGFILE", content_init)
        public.writeFile(init_path, content_init)

        # 如果配置出错恢复
        public.ExecShell("/etc/init.d/nginx restart")
        conf_pass = public.is_nginx_process_exists()
        if conf_pass == False:
            public.restore_file(init_path)
            self.__log("|-Nginx init FastCgi configuration error! {}".format(conf_pass))
            print("Nginx init FastCgi configuration error! {}".format(conf_pass))
            return False

        self.__log("|-Nginx init FastCgi cache configuration complete...")
        print("Nginx init FastCgi cache configuration complete")
        return True

    # 更新fastcgi-cache配置文件
    def set_fastcgi_php_conf(self, php_v: str) -> bool:
        if php_v.find('.') > -1:
            php_v = php_v.replace('.', '')

        conf_path = "{}/nginx/conf/enable-php-{}-wpfastcgi.conf".format(public.get_setup_path(), php_v)
        fastcgi_conf = self.get_fastcgi_conf(php_v)

        if not os.path.exists(conf_path):
            self.__log("|-Nginx FastCgi PHP configuration is not generated, generate it...")
            print("|-Nginx FastCgi PHP configuration is not generated, generate it...")
            public.writeFile(conf_path, fastcgi_conf)
            return True

        if public.FileMd5(conf_path) != public.md5(fastcgi_conf):
            self.__log("|-Nginx FastCgi PHP configuration is not well, update it...")
            print("|-Nginx FastCgi PHP configuration is not well, update it...")
            public.writeFile(conf_path, self.get_fastcgi_conf(php_v))
            return True

        self.__log("|-Nginx FastCgi PHP configuration is fine, skip it...")
        print("|-Nginx FastCgi PHP configuration is fine, skip it...")
        return True

    # 更新站点nginx配置文件，设置fastcgi-cache
    def set_website_conf(self, php_v: str, sitename: str, act: str = 'enable', immediate: bool = False) -> public.aap_t_simple_result:
        conf_path = "{}/vhost/nginx/{}.conf".format(public.get_panel_path(), sitename)
        public.back_file(conf_path)
        conf = public.readFile(conf_path)

        if not conf:
            print("Website configuration file does not exist {}".format(conf_path))
            self.__log("|-Website configuration file does not exist: {}".format(conf_path))

            return public.aap_t_simple_result(False, public.lang('网站配置文件不存在'))

        if php_v.find('.') > -1:
            php_v = php_v.replace('.', '')

        if act == 'disable':
            fastcgi_conf = "include enable-php-{}-wpfastcgi.conf;".format(php_v)

            if fastcgi_conf not in conf:
                print("FastCgi configuration does not exist in website configuration")
                self.__log("|-FastCgi configuration does not exist in website configuration, skip")

                return public.aap_t_simple_result(False, public.lang("网站配置中没有FastCgi配置"))

            rep = r"include\s+enable-php-{}-wpfastcgi.conf;".format(php_v)
            conf = re.sub(rep, "include enable-php-{}.conf;".format(php_v), conf)

        elif act == 'enable':
            # 设置nginx启动文件
            self.set_nginx_init()
            # 设置nginx全局配置
            self.set_nginx_conf()
            # 确保fastcgi-cache配置文件存在
            self.set_fastcgi_php_conf(php_v)

            fastcgi_conf = "include enable-php-{}-wpfastcgi.conf;".format(php_v)

            if fastcgi_conf in conf:
                self.__log("|-The FastCgi configuration already exists in the website configuration, skip it")

                return public.aap_t_simple_result(True, public.lang("“FastCgi配置已经存在于网站配置中”"))

            rep = r"include\s+enable-php-{}.conf;".format(php_v)
            conf = re.sub(rep, fastcgi_conf, conf)


        else:
            return public.aap_t_simple_result(False, public.lang('invalid act {}', act))
        public.writeFile(conf_path, conf)
        conf_pass = public.checkWebConfig()

        if not conf_pass:
            public.restore_file(conf_path)

            print("Website FastCgi configuration error {}".format(conf_pass))
            self.__log("|-Website FastCgi configuration error: {}".format(conf_pass))

            return public.aap_t_simple_result(False, public.lang("网站FastCgi配置错误!"))

        # 是否立即重载Nginx配置
        if immediate:
            public.ServiceReload()


        print("Website FastCgi configuration complete")
        self.__log("|-Website FastCgi configuration complete...")

        return public.aap_t_simple_result(True, public.lang("网站FastCgi配置完成"))

    # 开启fastcgi-cache
    def set_fastcgi(self, sitepath: str, sitename: str, php_v: str):
        """
        get.version
        get.name
        """
        # 设置nginx启动文件
        self.set_nginx_init()

        # 设置nginx全局配置
        self.set_nginx_conf()

        # 设置fastcgi location
        self.set_fastcgi_php_conf(php_v)

        # 设置网站配置文件
        self.set_website_conf(php_v, sitename)

        # 设置wp的变量用于nginx-helper插件清理缓存
        self.set_wp_nginx_helper(sitepath)

        # 设置.user.ini允许访问 /dev/shm/nginx-cache/wp 目录
        self.set_userini(sitepath)

    # 配置nginx-helper的缓存路径
    def set_wp_nginx_helper(self, site_path: str) -> bool:
        wpdeployment.update_wp_config("{}/wp-config.php".format(site_path), {'RT_WP_NGINX_HELPER_CACHE_PATH': self.__CACHE_PATH})
        return True

    # 更新.user.ini文件
    def set_userini(self, site_path: str) -> bool:
        conf_file = "{}/.user.ini".format(site_path)
        conf = public.readFile(conf_file)
        if not conf:
            print("Anti-cross-site configuration file does not exist: {}".format(conf_file))
            self.__log("|-Anti-cross-site configuration file does not exist: {}".format(conf_file))
            return False

        if self.__CACHE_PATH in conf:
            print("Anti-cross-site configuration is successful")
            self.__log("|-Anti-cross-site configuration is successful...")
            return True

        public.ExecShell('chattr -i {}'.format(conf_file))
        conf += ":{}".format(self.__CACHE_PATH)
        public.writeFile(conf_file, conf)
        public.ExecShell('chattr +i {}'.format(conf_file))
        self.__log("|-Anti-cross-site configuration is successful...")

        return True


# WP备份类
class wpbackup(wpmgr):
    __TABLE_NAME = 'wordpress_backups'
    __BACKUP_PATH = '/www/backup/wordpress'

    def __init__(self, site_id: int):
        wpmgr.__init__(self, site_id)
        self.__ensure_wp_backup_table_exists()
        self.__ensure_wp_backup_path_exists()

    # 创建WP Toolkit备份文件数据表
    def __ensure_wp_backup_table_exists(self):
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', self.__TABLE_NAME)).count():
            public.M('').execute(r'''CREATE TABLE `{table_name}` (
 `id` INTEGER PRIMARY KEY AUTOINCREMENT,
 `s_id` INTEGER NOT NULL DEFAULT 0,
 `extra` TEXT NOT NULL DEFAULT '{{}}',
 `bak_type` INTEGER NOT NULL DEFAULT 0,
 `bak_file` TEXT NOT NULL DEFAULT '',
 `bak_time` INTEGER NOT NULL DEFAULT (strftime('%s')));'''.format(table_name=self.__TABLE_NAME))

    # 确保备份目录存在
    def __ensure_wp_backup_path_exists(self):
        if not os.path.exists(self.__BACKUP_PATH):
            os.makedirs(self.__BACKUP_PATH, 0o755)

    # sqlite查询帮助函数
    @classmethod
    def __query(cls):
        return public.M(cls.__TABLE_NAME)

    # 通过备份ID查询站点ID
    @classmethod
    def retrieve_site_id_with_bak_id(cls, bak_id: int) -> int:
        data = cls.__query().where('id=?', (bak_id,)).field('s_id').find()

        if not isinstance(data, dict):
            raise public.HintException(public.get_msg_gettext('Invalid bak_id {}', (bak_id,)))

        return int(data['s_id'])

    # 备份文件统计(数量)
    def backup_count(self) -> int:
        return self.__query().where('s_id=?', (self.get_site_id(),)).count()

    # 备份列表
    def backup_list(self, args: public.dict_obj) -> typing.Dict:
        # 参数验证
        args.validate([
            public.Param('p').Integer('>', 0),
            public.Param('limit').Integer('>', 0),
            public.Param('tojs').Regexp(r"^[\w\.\-]+$"),
            public.Param('result').Regexp(r"^[\d\,]+$"),
        ])

        count = self.__query().where('s_id=?', (self.get_site_id(),)).count()

        import page

        # 实例化分页类
        page = page.Page()

        info = {}
        info['count'] = count
        info['row'] = int(args.get('limit', 20))
        info['p'] = int(args.get('p', 1))

        try:
            from flask import request
            info['uri'] = public.url_encode(request.full_path)
        except:
            info['uri'] = ''

        info['return_js'] = args.get('tojs', '')

        pagination = page.GetPage(info, args.get('result', '1,2,3,4,5,8'))
        data = self.__query().where('s_id=?', (self.get_site_id(),)).order('`id` desc').limit(str(page.SHIFT)+','+str(page.ROW)).field('id,bak_type,bak_file,bak_time').select()

        for item in data:
            if not os.path.exists(item['bak_file']):
                continue
            item['filename'] = os.path.basename(item['bak_file'])
            item['size'] = os.path.getsize(item['bak_file'])

        return {
            'page': pagination,
            'data': data,
        }

    # 仅备份网站文件
    def backup_files(self) -> public.aap_t_simple_result:

        ok, msg = public.backup_files(self.get_site_id())
        if ok:
            self.__query().insert({
                's_id': self.get_site_id(),
                'bak_type': 1,
                'bak_file': msg,
                'bak_time': int(time.time()),
            })

            msg = public.get_msg_gettext('备份完成')

        return public.aap_t_simple_result(ok, msg)

    # 仅备份数据库
    def backup_database(self) -> public.aap_t_simple_result:
        from public import mysqlmgr
        db_info = self.retrieve_database_info()
        ok, msg = mysqlmgr.backup(db_info.id)
        if ok:
            self.__query().insert({
                's_id': self.get_site_id(),
                'bak_type': 2,
                'bak_file': msg,
                'bak_time': int(time.time()),
            })

            msg = public.get_msg_gettext('备份完成')

        return public.aap_t_simple_result(ok, msg)

    # 备份网站文件+数据库+数据库连接信息
    def backup_full(self) -> public.aap_t_simple_result:
        # 开始备份
        self.backup_full_get_data()

        # 写操作日志
        wpmgr.log_opt('Backup [{}] successfully', (self.retrieve_first_domain(),))

        return public.aap_t_simple_result(True, public.lang('备份完成'))

    # 备份网站文件+数据库+数据库连接信息，并返回备份信息
    def backup_full_get_data(self) -> wp_bak_info:
        # 获取WP网站根目录
        site_root_path = self.retrieve_wp_root_path()

        # 创建临时目录
        tmp_path = public.make_panel_tmp_path()

        import shutil

        try:
            # 备份数据库
            db_info = self.retrieve_database_info()
            mysql_dump_info = public.dumpsql_with_aap(db_info.id, tmp_path)

            # 数据库备份文件改名
            shutil.move(mysql_dump_info.file, '{}/database.sql.gz'.format(tmp_path))

            # 备份网站文件
            shutil.make_archive('{}/files'.format(tmp_path), 'zip', site_root_path)

            meta_json_file = '{}/meta.json'.format(tmp_path)

            # 写入WP网站配置信息
            with open(meta_json_file, 'w') as fp:
                fp.write(json.dumps({
                    'domain': self.retrieve_first_domain(),
                    'another_domains': self.retrieve_another_domains(),
                    'site_path': self.retrieve_wp_root_path(),
                    'php_ver_short': self.retrieve_php_version().replace('.', ''),
                    'db_name': db_info.name,
                    'db_user': db_info.user,
                    'db_pwd': db_info.password,
                    'db_prefix': db_info.prefix,
                }, ensure_ascii=False))

            import datetime
            zipName = '{}/{}__{}.zip'.format(self.__BACKUP_PATH, self.retrieve_first_domain(),
                                             datetime.datetime.now().replace(microsecond=0,
                                                                             tzinfo=datetime.timezone.utc).strftime(
                                                 '%Y-%m-%dT%H_%M_%S%z'))

            # 压缩
            shutil.make_archive(os.path.splitext(zipName)[0], 'zip', tmp_path)

            bak_time = int(time.time())

            bak_id = self.__query().insert({
                's_id': self.get_site_id(),
                'bak_type': 3,
                'bak_file': zipName,
                'bak_time': bak_time,
            })

            return wp_bak_info(id=bak_id,
                               bak_file=zipName,
                               bak_type=3,
                               site_id=self.get_site_id(),
                               bak_time=bak_time)
        finally:
            # 删除临时目录
            shutil.rmtree(tmp_path)

    # 通过备份还原站点
    def restore_with_backup(self, bak_id: int) -> public.aap_t_simple_result:
        bak = self.__query().where('id=?', (bak_id,)).field('id,bak_type,bak_file').find()
        if not isinstance(bak, dict):
            return public.aap_t_simple_result(False, public.lang('备份不存在'))

        bak_type = int(bak['bak_type'])
        bak_file = bak['bak_file']

        # 还原网站文件
        if bak_type == 1:

            return public.restore_files(self.get_site_id(), bak_file)

        # 还原数据库
        if bak_type == 2:
            from public import mysqlmgr
            db_info = self.retrieve_database_info()
            return mysqlmgr.restore(db_info.name, bak_file)

        # 还原网站文件+数据库
        if bak_type == 3:
            if not os.path.exists(bak_file):
                return public.aap_t_simple_result(False, public.lang('备份文件不存在'))

            if os.path.splitext(bak_file)[1] != '.zip' or os.path.getsize(bak_file) < 10:
                return public.aap_t_simple_result(False, public.lang('备份文件已损坏'))

            site_root_path = self.retrieve_wp_root_path(False)

            import shutil
            tmp_path = public.make_panel_tmp_path()

            # 将站点现有文件移动到临时目录下暂时存放
            shutil.move(site_root_path, tmp_path)

            try:
                # 解压备份文件到临时目录下
                shutil.unpack_archive(bak_file, tmp_path, 'zip')

                # 解压网站备份文件到网站目录下
                shutil.unpack_archive('{}/files.zip'.format(tmp_path), site_root_path, 'zip')

                # 修改目录权限
                public.fix_permissions(site_root_path)

                # 导入数据库
                db_info = self.retrieve_database_info()
                ok, msg = public.restore(db_info.name, '{}/database.sql.gz'.format(tmp_path))
                if not ok:
                    raise public.HintException(msg)
            except:
                # 还原网站文件
                if os.path.exists(site_root_path):
                    user_ini_file = '{}/.user.ini'.format(site_root_path)
                    if os.path.exists(user_ini_file):
                        public.ExecShell('chattr -i {}'.format(user_ini_file))
                    shutil.rmtree(site_root_path)
                shutil.move('{}/{}'.format(tmp_path, os.path.basename(site_root_path)), os.path.dirname(site_root_path))
                raise
            finally:
                # 删除临时目录
                user_ini_file = '{}/{}/.user.ini'.format(tmp_path, os.path.basename(site_root_path))
                if os.path.exists(user_ini_file):
                    public.ExecShell('chattr -i {}'.format(user_ini_file))
                shutil.rmtree(tmp_path)

            # 写操作日志
            wpmgr.log_opt('Restore [{}] with [{}] successfully', (self.retrieve_first_domain(), bak_file))

            return public.aap_t_simple_result(True, public.lang('恢复成功'))

        return public.aap_t_simple_result(False, public.lang('不支持的备份类型'))

    # 删除备份文件
    def remove_backup(self, bak_id: int) -> public.aap_t_simple_result:
        bak = self.__query().where('id=?', (bak_id,)).field('id,bak_type,bak_file').find()
        if not isinstance(bak, dict):
            return public.aap_t_simple_result(False, public.lang('Backup not exists'))

        bak_type = int(bak['bak_type'])
        bak_file = bak['bak_file']

        ok = False
        msg = public.get_msg_gettext('No supported backup file')

        # 删除网站文件备份
        if bak_type == 1:

            ok, msg = public.del_bak(bak_file)

        # 删除数据库备份
        elif bak_type == 2:
            from public import mysqlmgr
            ok, msg = mysqlmgr.del_bak(bak_file)

        # 删除网站文件+数据库 备份
        elif bak_type == 3:
            if os.path.exists(bak_file):
                os.remove(bak_file)

            ok = True
            msg = public.get_msg_gettext('删除备份成功')

        if ok:
            self.__query().where('id=?', (bak_id,)).delete()

            # 写操作日志
            wpmgr.log_opt('Remove backup [{}] successfully', (bak_file,))

        return public.aap_t_simple_result(ok, msg)

    # 检查备份文件
    @classmethod
    def bak_file_check(cls, bak_file: str) -> public.aap_t_simple_result:
        # 检查备份文件
        if len(bak_file) < 5:
            return public.aap_t_simple_result(False, public.lang('Invalid backup file: filename too short'))

        # 检查文件后缀
        if bak_file[-4:] != '.zip':
            return public.aap_t_simple_result(False, public.lang('Invalid backup file: must be a zip file'))

        # 检查文件是否存在
        if not os.path.exists(bak_file):
            return public.aap_t_simple_result(False, public.lang('Invalid backup file: not exists'))

        return public.aap_t_simple_result(True, public.lang('Backup file is well'))

    # aapanel WP备份包完整性校验
    @classmethod
    def aap_bak_integrity_check(cls, tmp_path: str) -> public.aap_t_simple_result:
        if not os.path.exists(tmp_path):
            return public.aap_t_simple_result(False, public.lang('Path {} not found', tmp_path))

        meta_json_file = '{}/meta.json'.format(tmp_path)
        site_bak_file = '{}/files.zip'.format(tmp_path)
        db_bak_file = '{}/database.sql.gz'.format(tmp_path)

        # 检查目录结构是否符合预期
        if not os.path.exists(meta_json_file):
            return public.aap_t_simple_result(False, public.lang('缺失文件: {}', 'meta.json'))

        if not os.path.exists(site_bak_file):
            return public.aap_t_simple_result(False, public.lang('缺失文件: {}', 'files.zip'))

        if not os.path.exists(db_bak_file):
            return public.aap_t_simple_result(False, public.lang('缺失文件: {}', 'database.sql.gz'))

        # 校验meta.json数据格式
        wp_bak_meta_info.parse(meta_json_file)

        return public.aap_t_simple_result(True, public.lang('Backup file is well formed'))

    # 从aapanel WP备份文件中读取网站元信息
    @classmethod
    def get_metadata_with_aap_bak(cls, bak_file: str) -> public.aap_t_simple_result:
        # 检查备份文件
        ok, msg = cls.bak_file_check(bak_file)

        if not ok:
            return public.aap_t_simple_result(False, msg)

        # 创建临时目录
        tmp_path = public.make_panel_tmp_path()

        import shutil

        try:
            # 解压备份文件到临时目录下
            shutil.unpack_archive(bak_file, tmp_path, 'zip')

            # 检验备份文件完整性
            ok, msg = cls.aap_bak_integrity_check(tmp_path)

            if not ok:
                return public.aap_t_simple_result(False, msg)

            # 读取元数据
            metadata = wp_bak_meta_info.parse('{}/meta.json'.format(tmp_path))

            return public.aap_t_simple_result(True, metadata.to_dict())
        finally:
            # 删除临时目录
            shutil.rmtree(tmp_path)

    # 通过aapanel WP备份文件部署WP站点
    @classmethod
    def wp_deploy_with_aap_bak(cls, args: public.dict_obj) -> public.aap_t_simple_result:
        #

        # 校验参数
        args.validate([
            public.Param('bak_file').Require(),
            public.Param('domain').Require().Host(),
            public.Param('sub_path').SafePath(),
            public.Param('php_ver_short').Integer('in', list(map(lambda x: int(x), public.get_available_php_ver_shorts()))),
            public.Param('db_name').Regexp(r'^\w+$'),
            public.Param('db_pwd').String('>', 7),
            public.Param('enable_cache').Integer(),
        ])

        # 域名暂不支持自定义端口号
        if args.domain.find(':') > -1:
            return public.aap_t_simple_result(False, public.lang('不支持自定义端口'))

        bak_file = args.bak_file

        # 检验备份包
        # 检查备份文件
        ok, msg = cls.bak_file_check(bak_file)

        if not ok:
            return public.aap_t_simple_result(False, msg)

        # 创建临时目录
        tmp_path = public.make_panel_tmp_path()

        import shutil

        simple_site_info = None

        try:
            # 解压备份文件到临时目录下
            shutil.unpack_archive(bak_file, tmp_path, 'zip')

            # 检查aapanel WP备份包完整性
            ok, msg = cls.aap_bak_integrity_check(tmp_path)

            if not ok:
                return public.aap_t_simple_result(False, msg)

            meta_json_file = '{}/meta.json'.format(tmp_path)
            site_bak_file = '{}/files.zip'.format(tmp_path)
            db_bak_file = '{}/database.sql.gz'.format(tmp_path)

            # 解析meta.json
            metadata = wp_bak_meta_info.parse(meta_json_file)

            # 设置参数默认值
            if 'php_ver_short' not in args:
                args.php_ver_short = metadata.php_ver_short

            if 'db_name' not in args:
                args.db_name = str(args.domain).replace('.', '_').replace('-', '_')[:16].lower()

            if 'db_pwd' not in args:
                args.db_pwd = public.gen_password(16)

            site_path = '{}/{}'.format(public.get_site_path(), args.domain)

            # 新增空站点

            simple_site_info = public.create_php_site_with_mysql(args.domain, site_path, args.php_ver_short, args.db_name, args.db_pwd, metadata.another_domains)

            # 当设置了子目录时
            if 'sub_path' in args and args.sub_path != '':
                # 更新网站根目录到子目录下
                site_path += os.path.join('/', args.sub_path)

                # 创建目录
                if not os.path.exists(site_path):
                    os.makedirs(site_path, 0o755)
                    shutil.chown(site_path, 'www')

                public.M('sites').where('`id` = ?', (simple_site_info.site_id,)).update({
                    'path': site_path,
                })

            # 导入数据库
            ok, msg = public.restore(args.db_name, db_bak_file)

            if not ok:
                raise public.HintException(msg)

            # 测试数据库连接
            ok, msg = wpdeployment.test_mysql_connection(args.db_name, args.db_name, args.db_pwd, metadata.db_prefix)

            if not ok:
                raise public.HintException(msg)

            # WP站点初始化
            wpmgr_obj = wpmgr(simple_site_info.site_id)

            wpdeployment_obj = wpdeployment()
            wpdeployment_obj.set_wpmgr(wpmgr_obj)

            # 去除.user.ini特殊权限i
            wpdeployment_obj.strip_attr_i_with_user_ini()

            # 解压网站文件
            shutil.unpack_archive(site_bak_file, site_path, 'zip')

            # 恢复.user.ini
            wpdeployment_obj.fix_user_ini()

            # 更新WP配置文件
            wpdeployment.update_wp_config('{}/wp-config.php'.format(site_path), {
                'DB_NAME': args.db_name,
                'DB_USER': args.db_name,
                'DB_PASSWORD': args.db_pwd,
                'DB_HOST': 'localhost',
                'DB_CHARSET': 'utf8mb4',
                'table_prefix': metadata.db_prefix,
                'AUTH_KEY': wpdeployment.generate_salt(),
                'SECURE_AUTH_KEY': wpdeployment.generate_salt(),
                'LOGGED_IN_KEY': wpdeployment.generate_salt(),
                'NONCE_KEY': wpdeployment.generate_salt(),
                'AUTH_SALT': wpdeployment.generate_salt(),
                'SECURE_AUTH_SALT': wpdeployment.generate_salt(),
                'LOGGED_IN_SALT': wpdeployment.generate_salt(),
                'NONCE_SALT': wpdeployment.generate_salt(),
            })

            # 更新站点project_type=WP2
            public.M('sites').where('`id` = ?', (simple_site_info.site_id,)).update({
                'project_type': 'WP2',
            })

            # 添加Wordpress站点记录
            ok, msg = wpdeployment_obj.upsert_wp_info_to_wordpress_onekey('admin', 'admin_password', simple_site_info.database_id, metadata.db_prefix)

            if not ok:
                raise public.HintException(msg)

            # 添加本地hosts
            ok, msg = wpdeployment_obj.add_hosts()

            if not ok:
                raise public.HintException(msg)

            # 优化PHP-FPM
            wpdeployment_obj.optimize_php_fpm(args.php_ver_short)

            # 优化MySQL
            # wpdeployment_obj.optimize_mysql()

            # 设置伪静态
            wpdeployment_obj.setup_url_rewrite(args.get('sub_path', None))

            # 更新网站URL
            wpdeployment_obj.fix_site_url(args.get('sub_path', ''))

            # 检查是否需要启用fastcgi
            if 'enable_cache' in args and int(args.enable_cache) == 1:
                wpfastcgi_cache().set_fastcgi(site_path, args.domain, args.php_ver_short)

            # 调整网站文件与目录权限
            wpdeployment_obj.fix_permissions()

            # 重启网站服务
            public.serviceReload()

            # 备份部署完成
            # 删除临时备份包
            if not str(bak_file).startswith(cls.__BACKUP_PATH):
                os.remove(bak_file)
        except:
            # 删除站点
            if simple_site_info is not None:

                public.remove_site(simple_site_info.site_id)

            raise
        finally:
            # 删除临时目录
            shutil.rmtree(tmp_path)

        # 写操作日志
        wpmgr_obj = wpmgr(simple_site_info.site_id)
        wpmgr.log_opt('Create [{}] with backup file [{}]', (wpmgr_obj.retrieve_first_domain(), bak_file))

        return public.aap_t_simple_result(True, '已完成')

    # plesk/cpanel Wordpress备份包完整性校验
    @classmethod
    def plesk_or_cpanel_bak_integrity_check(cls, tmp_path: str) -> public.aap_t_simple_result:
        if not os.path.exists(tmp_path):
            return public.aap_t_simple_result(False, public.lang('Path {} not found', tmp_path))

        meta_json_file = '{}/meta.json'.format(tmp_path)
        site_bak_file = '{}/files'.format(tmp_path)
        db_bak_file = '{}/sqldump.sql'.format(tmp_path)

        # 检查目录结构是否符合预期
        if not os.path.exists(meta_json_file):
            return public.aap_t_simple_result(False, public.lang('该文件不是一个格式良好的Plesk/cPanel备份。丢失文件：{}','meta json'))

        if not os.path.exists(site_bak_file):
            return public.aap_t_simple_result(False, public.lang('该文件不是一个格式良好的Plesk/cPanel备份。丢失目录：{}', 'files/'))

        if not os.path.exists(db_bak_file):
            return public.aap_t_simple_result(False, public.lang('该文件不是一个格式良好的Plesk/cPanel备份。丢失目录：{}', 'sqldump.sql'))

        return public.aap_t_simple_result(True, public.lang('Backup file is well formed'))

    # 从plesk/cpanel Wordpress备份包中读取网站元信息
    @classmethod
    def get_metadata_with_plesk_or_cpanel_bak(cls, bak_file: str) -> public.aap_t_simple_result:
        # 检查备份文件
        ok, msg = cls.bak_file_check(bak_file)

        if not ok:
            return public.aap_t_simple_result(False, msg)

        # 创建临时目录
        tmp_path = public.make_panel_tmp_path()

        import shutil

        try:
            # 解压备份文件到临时目录下
            shutil.unpack_archive(bak_file, tmp_path, 'zip')

            # 检验备份文件完整性
            ok, msg = cls.plesk_or_cpanel_bak_integrity_check(tmp_path)

            if not ok:
                return public.aap_t_simple_result(False, msg)

            try:
                # 读取元数据
                with open('{}/meta.json'.format(tmp_path), 'r') as fp:
                    metadata = json.loads(fp.read())
            except:
                raise public.HintException(public.get_msg_gettext('File {} is malformed', ('meta.json',)))

            return public.aap_t_simple_result(True, {
                'db_predix': metadata['dbPrefix'],
            })
        finally:
            # 删除临时目录
            shutil.rmtree(tmp_path)

    # 通过plesk/cpanel Wordpress备份完成WP站点安装
    @classmethod
    def wp_deploy_with_plesk_or_cpanel_bak(cls, args: public.dict_obj) -> public.aap_t_simple_result:


        # 校验参数
        args.validate([
            public.Param('bak_file').Require(),
            public.Param('domain').Require().Host(),
            public.Param('sub_path').SafePath(),
            public.Param('php_ver_short').Require().Integer('in', list(map(lambda x: int(x), public.get_available_php_ver_shorts()))),
            public.Param('db_name').Regexp(r'^\w+$'),
            public.Param('db_pwd').String('>', 7),
            public.Param('enable_cache').Integer(),
        ])

        # 域名暂不支持自定义端口号
        if args.domain.find(':') > -1:
            return public.aap_t_simple_result(False, public.lang('Not supported customize port yet.'))

        bak_file = args.bak_file

        # 检验备份包
        # 检查备份文件
        ok, msg = cls.bak_file_check(bak_file)

        if not ok:
            return public.aap_t_simple_result(False, msg)

        # 创建临时目录
        tmp_path = public.make_panel_tmp_path()

        import shutil

        simple_site_info = None

        try:
            # 解压备份文件到临时目录下
            shutil.unpack_archive(bak_file, tmp_path, 'zip')

            # 检查备份包完整性
            ok, msg = cls.plesk_or_cpanel_bak_integrity_check(tmp_path)

            if not ok:
                return public.aap_t_simple_result(False, msg)

            meta_json_file = '{}/meta.json'.format(tmp_path)
            site_bak_file = '{}/files'.format(tmp_path)
            db_bak_file = '{}/sqldump.sql'.format(tmp_path)

            # 解析meta.json
            with open(meta_json_file, 'r') as fp:
                metadata = json.loads(fp.read())

            # 设置参数默认值
            if 'db_name' not in args:
                args.db_name = str(args.domain).replace('.', '_').replace('-', '_')[:16].lower()

            if 'db_pwd' not in args:
                args.db_pwd = public.gen_password(16)

            site_path = '{}/{}'.format(public.get_site_path(), args.domain)

            # 新增空站点

            simple_site_info = public.create_php_site_with_mysql(args.domain, site_path, args.php_ver_short,
                                                                     args.db_name, args.db_pwd)

            # 当设置了子目录时
            if 'sub_path' in args and args.sub_path != '':
                # 更新网站根目录到子目录下
                site_path += os.path.join('/', args.sub_path)

                # 创建目录
                if not os.path.exists(site_path):
                    os.makedirs(site_path, 0o755)
                    shutil.chown(site_path, 'www')

                public.M('sites').where('`id` = ?', (simple_site_info.site_id,)).update({
                    'path': site_path,
                })

            # 导入数据库
            from public import mysqlmgr
            ok, msg = mysqlmgr.restore(args.db_name, db_bak_file)

            if not ok:
                raise public.HintException(msg)

            # 测试数据库连接
            ok, msg = wpdeployment.test_mysql_connection(args.db_name, args.db_name, args.db_pwd, metadata['dbPrefix'])

            if not ok:
                raise public.HintException(msg)

            # WP站点初始化
            wpmgr_obj = wpmgr(simple_site_info.site_id)

            wpdeployment_obj = wpdeployment()
            wpdeployment_obj.set_wpmgr(wpmgr_obj)

            # 去除.user.ini特殊权限i
            wpdeployment_obj.strip_attr_i_with_user_ini()

            # 将网站文件移动到站点目录下
            from glob import glob
            for fname in glob('{}/*'.format(site_bak_file)):
                shutil.move(fname, site_path)

            # 恢复.user.ini
            wpdeployment_obj.fix_user_ini()

            # 更新WP配置文件
            wpdeployment.update_wp_config('{}/wp-config.php'.format(site_path), {
                'DB_NAME': args.db_name,
                'DB_USER': args.db_name,
                'DB_PASSWORD': args.db_pwd,
                'DB_HOST': 'localhost',
                'DB_CHARSET': 'utf8mb4',
                'table_prefix': metadata['dbPrefix'],
                'AUTH_KEY': wpdeployment.generate_salt(),
                'SECURE_AUTH_KEY': wpdeployment.generate_salt(),
                'LOGGED_IN_KEY': wpdeployment.generate_salt(),
                'NONCE_KEY': wpdeployment.generate_salt(),
                'AUTH_SALT': wpdeployment.generate_salt(),
                'SECURE_AUTH_SALT': wpdeployment.generate_salt(),
                'LOGGED_IN_SALT': wpdeployment.generate_salt(),
                'NONCE_SALT': wpdeployment.generate_salt(),
            })

            # 更新站点project_type=WP2
            public.M('sites').where('`id` = ?', (simple_site_info.site_id,)).update({
                'project_type': 'WP2',
            })

            # 添加Wordpress站点记录
            ok, msg = wpdeployment_obj.upsert_wp_info_to_wordpress_onekey('admin', 'admin_password',
                                                                          simple_site_info.database_id,
                                                                          metadata['dbPrefix'])

            if not ok:
                raise public.HintException(msg)

            # 添加本地hosts
            ok, msg = wpdeployment_obj.add_hosts()

            if not ok:
                raise public.HintException(msg)

            # 优化PHP-FPM
            wpdeployment_obj.optimize_php_fpm(args.php_ver_short)

            # 优化MySQL
            wpdeployment_obj.optimize_mysql()

            # 设置伪静态
            wpdeployment_obj.setup_url_rewrite(args.get('sub_path', None))

            # 更新网站URL
            wpdeployment_obj.fix_site_url(args.get('sub_path', ''))

            # 检查是否需要启用fastcgi
            if 'enable_cache' in args and int(args.enable_cache) == 1:
                wpfastcgi_cache().set_fastcgi(site_path, args.domain, args.php_ver_short)

            # 调整网站文件与目录权限
            wpdeployment_obj.fix_permissions()

            # 重启网站服务
            public.serviceReload()

            # 备份部署完成
            # 删除临时备份包
            if not str(bak_file).startswith(cls.__BACKUP_PATH):
                os.remove(bak_file)
        except:
            # 删除站点
            if simple_site_info is not None:

                public.remove_site(simple_site_info.site_id)

            raise
        finally:
            # 删除临时目录
            shutil.rmtree(tmp_path)

        # 写操作日志
        wpmgr_obj = wpmgr(simple_site_info.site_id)
        wpmgr.log_opt('Create [{}] with backup file [{}]', (wpmgr_obj.retrieve_first_domain(), bak_file))

        return public.aap_t_simple_result(True, public.lang('Success'))

    # 克隆WP站点
    # @only_pro_members
    def clone(self, args: public.dict_obj) -> public.aap_t_simple_result:
        # 完全备份本站点
        bak_info = self.backup_full_get_data()

        try:
            args.bak_file = bak_info.bak_file

            # 调用aap备份部署API
            # 完成站点克隆
            ok, msg = self.wp_deploy_with_aap_bak(args)

            if ok:
                # 写操作日志
                wpmgr.log_opt('克隆 [{}] 到 [{}] 成功', (self.retrieve_first_domain(), args.domain))

            return public.aap_t_simple_result(ok, msg)
        finally:
            # 删除备份
            self.remove_backup(bak_info.id)

    # TODO 复制WP站点数据
    def copy(self):
        pass


# WP迁移类
class wpmigration(wpmgr):

    def __init__(self, site_id: int):
        wpmgr.__init__(self, site_id)

    # 迁移 [网站管理] 中的单个WP网站到WP Toolkit中
    def migrate_site_to_wptoolkit(self, get):
        data = self.can_migrations_of_aap_website()
        if not data:
            return public.aap_t_simple_result(False, "此网站不支持迁移到WP")
        site_data = None
        for site in data:
            if site['id'] == int(get.site_id):
                site_data = site
                break
        if not site_data:
            return public.aap_t_simple_result(False, "此网站不支持迁移到WP")

        # 判断wp站点是否已完成初始化
        config_file = os.path.join(site_data['path'], "wp-config.php")
        if not os.path.exists(config_file):
            return public.aap_t_simple_result(False, "此网站还未完成初始化，请先完成初始化后再进行迁移")
        else:
            if "prefix" in get and get.prefix:
                prefix = get.prefix
            else:
                config_content = public.readFile(config_file)
                match = re.search(r"\$table_prefix\s*=\s*'([^']+)';", config_content)
                if match:
                    prefix = match.group(1)
                else:
                    return public.aap_t_simple_result(False, "获取wp数据表前缀失败，请手动输入wp数据表前缀")

        # 修改网站type为WP2
        public.M('sites').where('`id` = ?', (get.site_id,)).update({
            'project_type': 'WP2',
        })

        # 校验wordpress_onekey表数据
        wp_info = public.M('sites').where('`s_id` = ?', (get.site_id,)).field('id').find()
        if not wp_info:
            public.M('wordpress_onekey').add('s_id,d_id,prefix,user,pass', (get.site_id, 0, prefix, "", ""))
        else:
            public.M('wordpress_onekey').where('`s_id` = ?', (get.site_id,)).update({
                'prefix': prefix,
            })

        return public.aap_t_simple_result(True, public.lang('迁移成功'))

    # 迁移 [网站管理] 中的WP网站到WP Toolkit中
    @classmethod
    def migrate_aap_from_website_to_wptoolkit(cls) -> public.aap_t_simple_result:
        public.M('sites').where('`project_type` = ?', ('WP',)).update({
            'project_type': 'WP2',
        })

        # 写操作日志
        wpmgr.log_opt('将所有wordpress网站从[Website]迁移到[WP Toolkit].')

        return public.aap_t_simple_result(True, public.lang('迁移成功'))

    # 查询可迁移的 [网站管理] WP网站
    @classmethod
    def can_migrations_of_aap_website(cls) -> typing.List[str]:
        data = public.M('sites').where('`project_type` = ?', ('PHP',)).field('name,path,id').order('id asc').select()
        _return = []
        for item in data:
            path = os.path.join(item['path'], "wp-includes/version.php")
            if os.path.exists(path) and "wp_version" in public.readFile(path) and public.M('databases').where('pid = ?', (item['id'],)).find():
                _return.append(item)
        return _return


# WP部署类
class wpdeployment:
    __TABLE_NAME = 'wordpress_onekey'

    def __init__(self):
        self.__LOG_FILE = '/tmp/schedule.log'
        self.__MEM_INFO: typing.Optional[wp_mem_info] = None
        self.__WPMGR: typing.Optional[wpmgr] = None
        self.__ensure_wordpress_onekey_table_exists()

    # 创建wordpress_onekey数据表
    def __ensure_wordpress_onekey_table_exists(self):
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', self.__TABLE_NAME)).count():
            public.M('').execute(r'''CREATE TABLE  IF NOT EXISTS `{table_name}` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`s_id` INTEGER NOT NULL DEFAULT 0,
`d_id` INTEGER NOT NULL DEFAULT 0,
`prefix` TEXT NOT NULL DEFAULT 'wp_',
`user` TEXT NOT NULL DEFAULT '',
`pass` TEXT NOT NULL DEFAULT '');'''.format(table_name=self.__TABLE_NAME))

    # 输出日志
    def __log(self, content: str):
        with open(self.__LOG_FILE, 'a') as fp:
            fp.write(content + '\n')

    # sqlite查询帮助函数
    @classmethod
    def __query(cls):
        return public.M(cls.__TABLE_NAME)

    # 添加/更新Wordpress站点信息到wordpress_onekey数据表中
    def upsert_wp_info_to_wordpress_onekey(self, wp_admin_user: str, wp_admin_pwd: str, database_id: int, db_prefix: str) -> public.aap_t_simple_result:
        """
        :param wp_admin_user: str   Wordpress管理员用户名
        :param wp_admin_pwd: str    Wordpress管理员用户密码
        :param database_id: int     MySQL数据库ID
        :param db_prefix: str       Wordpress数据库前缀
        :return: public.aap_t_simple_result
        """
        upsert_data = {
            's_id': self.wpmgr().get_site_id(),
            'd_id': database_id,
            'prefix': db_prefix,
            'user': wp_admin_user,
            'pass': wp_admin_pwd,
        }

        data = self.__query().where('`s_id` = ?', (self.wpmgr().get_site_id(),)).field('id').find()

        # 数据库可能损坏
        if isinstance(data, str):
            return public.aap_t_simple_result(False, public.lang('Aapanel database file has been corrupted'))

        # 存在记录，更新信息
        if isinstance(data, dict):
            self.__query().where('`id` = ?', (int(data['id']),)).update(upsert_data)
            return public.aap_t_simple_result(True, public.lang('Wordpress_onekey was updated'))

        # 不存在记录，新增一条记录
        self.__query().insert(upsert_data)

        return public.aap_t_simple_result(True, public.lang('Wordpress_onekey was created'))

    # 设置WP管理类实例
    def set_wpmgr(self, wpmgr_obj: wpmgr):
        self.__WPMGR = wpmgr_obj
        return self

    # 获取WP管理类实例
    def wpmgr(self) -> wpmgr:
        if self.__WPMGR is None:
            raise RuntimeError(public.get_msg_gettext('Please set wpmgr instance before'))

        return self.__WPMGR

    # 获取系统内存信息
    def mem_total(self) -> int:
        if self.__MEM_INFO is not None:
            return self.__MEM_INFO.total

        import psutil
        mem = psutil.virtual_memory()
        self.__MEM_INFO = wp_mem_info(
            total=mem.total >> 20,
            free=mem.free >> 20,
            buffers=mem.buffers >> 20,
            cached=mem.cached >> 20)

        return self.__MEM_INFO.total

    # PHP-FPM性能调优
    def optimize_php_fpm(self, php_ver_short: str) -> public.aap_t_simple_result:
        args = public.to_dict_obj({
            'version': php_ver_short,
        })

        self.__log("|-Start tuning PHP FPM parameters...")

        mem_total = self.mem_total()
        if mem_total <= 1024:
            args.max_children = '30'
            args.start_servers = '5'
            args.min_spare_servers = '5'
            args.max_spare_servers = '20'
        elif 1024 < mem_total <= 2048:
            args.max_children = '50'
            args.start_servers = '5'
            args.min_spare_servers = '5'
            args.max_spare_servers = '30'
        elif 2048 < mem_total <= 4098:
            args.max_children = '80'
            args.start_servers = '10'
            args.min_spare_servers = '10'
            args.max_spare_servers = '30'
        elif 4098 < mem_total <= 8096:
            args.max_children = '120'
            args.start_servers = '10'
            args.min_spare_servers = '10'
            args.max_spare_servers = '30'
        elif 8096 < mem_total <= 16192:
            args.max_children = '200'
            args.start_servers = '15'
            args.min_spare_servers = '15'
            args.max_spare_servers = '50'
        elif 16192 < mem_total <= 32384:
            args.max_children = '300'
            args.start_servers = '20'
            args.min_spare_servers = '20'
            args.max_spare_servers = '50'
        elif 32384 < mem_total:
            args.max_children = '500'
            args.start_servers = '20'
            args.min_spare_servers = '20'
            args.max_spare_servers = '50'

        from config import config
        current_conf = config().getFpmConfig(args)

        args.pm = current_conf['pm']
        args.listen = current_conf['unix']

        self.__log("""
===================PHP FPM parameters=======================

 max_children: {}
 start_servers: {}
 min_spare_servers: {}
 max_spare_servers: {}
 Running mode: {}
 Connection: {}

===================PHP FPM parameters=======================


""".format(args.max_children, args.start_servers, args.min_spare_servers, args.max_spare_servers, args.pm, args.listen))

        result = config().setFpmConfig(args)
        if not result['status']:
            self.__log("|-PHP FPM Optimization failed: {}".format(result))
            return public.aap_t_simple_result(False, public.lang("PHP FPM Optimization failed: {}", result))

        self.__log("|-PHP FPM optimization succeeded")

        return public.aap_t_simple_result(True, public.lang("PHP FPM optimization succeeded"))

    # MySQL性能调优
    def optimize_mysql(self) -> public.aap_t_simple_result:
        args = public.to_dict_obj({})

        self.__log("|-Start optimizing Mysql")

        mem_total = self.mem_total()
        if mem_total <= 2048:
            args.key_buffer_size = '128'
            args.tmp_table_size = '64'
            args.innodb_buffer_pool_size = '256'
            args.innodb_log_buffer_size = '16'
            args.sort_buffer_size = '768'
            args.read_buffer_size = '768'
            args.read_rnd_buffer_size = '512'
            args.join_buffer_size = '1024'
            args.thread_stack = '256'
            args.binlog_cache_size = '64'
            args.thread_cache_size = '64'
            args.table_open_cache = '128'
            args.max_connections = '100'
            args.max_heap_table_size = '64'
        elif 2048 < mem_total <= 4096:
            args.key_buffer_size = '256'
            args.tmp_table_size = '384'
            args.innodb_buffer_pool_size = '384'
            args.innodb_log_buffer_size = '16'
            args.sort_buffer_size = '768'
            args.read_buffer_size = '768'
            args.read_rnd_buffer_size = '512'
            args.join_buffer_size = '2048'
            args.thread_stack = '256'
            args.binlog_cache_size = '64'
            args.thread_cache_size = '96'
            args.table_open_cache = '192'
            args.max_connections = '200'
            args.max_heap_table_size = '384'
        elif 4096 < mem_total <= 8192:
            args.key_buffer_size = '384'
            args.tmp_table_size = '512'
            args.innodb_buffer_pool_size = '512'
            args.innodb_log_buffer_size = '16'
            args.sort_buffer_size = '1024'
            args.read_buffer_size = '1024'
            args.read_rnd_buffer_size = '768'
            args.join_buffer_size = '2048'
            args.thread_stack = '256'
            args.binlog_cache_size = '128'
            args.thread_cache_size = '128'
            args.table_open_cache = '384'
            args.max_connections = '300'
            args.max_heap_table_size = '512'
        elif 8192 < mem_total <= 16384:
            args.key_buffer_size = '512'
            args.tmp_table_size = '1024'
            args.innodb_buffer_pool_size = '1024'
            args.innodb_log_buffer_size = '16'
            args.sort_buffer_size = '2048'
            args.read_buffer_size = '2048'
            args.read_rnd_buffer_size = '1024'
            args.join_buffer_size = '4096'
            args.thread_stack = '384'
            args.binlog_cache_size = '192'
            args.thread_cache_size = '192'
            args.table_open_cache = '1024'
            args.max_connections = '400'
            args.max_heap_table_size = '1024'
        elif 16384 < mem_total <= 32768:
            args.key_buffer_size = '1024'
            args.tmp_table_size = '2048'
            args.innodb_buffer_pool_size = '4096'
            args.innodb_log_buffer_size = '16'
            args.sort_buffer_size = '4096'
            args.read_buffer_size = '4096'
            args.read_rnd_buffer_size = '2048'
            args.join_buffer_size = '8192'
            args.thread_stack = '512'
            args.binlog_cache_size = '256'
            args.thread_cache_size = '256'
            args.table_open_cache = '2048'
            args.max_connections = '500'
            args.max_heap_table_size = '2048'
        elif 32768 < mem_total:
            args.key_buffer_size = '2048'
            args.tmp_table_size = '4096'
            args.innodb_buffer_pool_size = '8192'
            args.innodb_log_buffer_size = '16'
            args.sort_buffer_size = '8192'
            args.read_buffer_size = '8192'
            args.read_rnd_buffer_size = '4096'
            args.join_buffer_size = '16384'
            args.thread_stack = '1024'
            args.binlog_cache_size = '512'
            args.thread_cache_size = '512'
            args.table_open_cache = '2048'
            args.max_connections = '1000'
            args.max_heap_table_size = '4096'

        self.__log("""
=====================Mysql parameters=======================

 key_buffer_size: {}
 tmp_table_size: {}
 innodb_buffer_pool_size: {}
 innodb_log_buffer_size: {}
 sort_buffer_size: {}
 read_buffer_size: {}
 read_rnd_buffer_size: {}
 join_buffer_size: {}
 thread_stack: {}
 binlog_cache_size: {}
 thread_cache_size: {}
 table_open_cache: {}
 max_connections: {}
 max_heap_table_size: {}

=====================Mysql parameters=======================

""".format(args.key_buffer_size, args.tmp_table_size, args.innodb_buffer_pool_size, args.innodb_log_buffer_size,
        args.sort_buffer_size, args.read_buffer_size, args.read_rnd_buffer_size, args.join_buffer_size,
        args.thread_stack, args.binlog_cache_size, args.thread_cache_size, args.table_open_cache,
        args.max_connections, args.max_heap_table_size))

        from database import database
        result = database().SetDbConf(args)

        if int(result.get('status', 0)) != 0:
            self.__log("|-Mysql optimization failed {}".format(result))
            return public.aap_t_simple_result(False, public.lang("Mysql optimization failed {}", result))

        public.ExecShell("/etc/init.d/mysqld restart")

        self.__log("|-Mysql optimization succeeded")

        return public.aap_t_simple_result(True, public.lang("Mysql optimization succeeded"))

    # 配置伪静态规则
    def setup_url_rewrite(self, sub_path: typing.Optional[str] = None) -> public.aap_t_simple_result:
        # 获取网站首选域名
        site_name = self.wpmgr().retrieve_first_domain()

        # 获取
        site_root_path = self.wpmgr().retrieve_wp_root_path()

        # 获取当前启用的WEB服务器类型
        webserver = public.get_webserver()

        if webserver == 'openlitespeed':
            webserver = 'apache'

        # 仅支持nginx、apache
        if webserver.lower() not in ('nginx', 'apache'):
            return public.aap_t_simple_result(False, public.lang('Wordpress URL-rewrite not yet support {}', webserver))

        # 获取默认的Wordpress伪静态规则
        swfile = '{}/rewrite/{}/wordpress.conf'.format(public.get_panel_path(), webserver)
        if not os.path.exists(swfile):
            return public.aap_t_simple_result(False, public.lang('Default wordpress URL-rewrite rules not found'))

        rewrite_conf = public.readFile(swfile)

        if webserver == 'nginx':
            dwfile = '{}/vhost/rewrite/{}.conf'.format(public.get_panel_path(), site_name)

            # 当设置了子目录时，需要修改伪静态重写规则
            if sub_path is not None and sub_path not in ('', '/'):
                rewrite_conf = re.sub(r'''try_files[^;]+;''', r'try_files $uri $uri/ /{}/index.php?$args;'.format(sub_path.lstrip('/')), rewrite_conf, 1)
        else:
            dwfile = '{}/.htaccess'.format(site_root_path)

            # 当设置了子目录时，需要修改伪静态重写规则
            # if sub_path is not None and sub_path not in ('', '/'):
            #     rewrite_conf = re.sub(r'''RewriteRule\s+(?:\.|\^\.[*+]\$)[^\r\n]+''', r'RewriteRule ^.*$ /{}/index.php [NC,L,QSA]'.format(sub_path.lstrip('/')), rewrite_conf, 1)

        public.writeFile(dwfile, rewrite_conf)

        return public.aap_t_simple_result(True, public.lang('Setup wordpress URL-rewrite successfully'))

    # 修正权限
    def fix_permissions(self, target_path: typing.Optional[str] = None) -> public.aap_t_simple_result:
        # 默认修改整个网站目录下的所有目录以及文件权限
        if target_path is None:
            target_path = self.wpmgr().retrieve_wp_root_path()

        # 
        return public.fix_permissions(target_path)

    # 将WP安装包或者WP备份包解包到网站根目录下
    def unpack_package(self, package_file: str) -> public.aap_t_simple_result:
        self.__log('|-Unpacking package {}...'.format(package_file))

        if len(package_file) < 5:
            self.__log('|-Unpack package {} failed: package name too short'.format(package_file))
            return public.aap_t_simple_result(False, public.lang('Package name too short'))

        if package_file[-4:] != '.zip':
            self.__log('|-Unpack package {} failed: package must be a zip file'.format(package_file))
            return public.aap_t_simple_result(False, public.lang('Package must be a zip file'))

        if not os.path.exists(package_file):
            self.__log('|-Unpack package {} failed: package file not exists'.format(package_file))
            return public.aap_t_simple_result(False, public.lang('Package file not exists'))

        import shutil

        # 解压到WP网站根目录下
        shutil.unpack_archive(package_file, self.wpmgr().retrieve_wp_root_path(), 'zip')

        self.__log('|-Fixing website directories and files permissions...')

        # 设置网站目录权限与文件权限
        ok, msg = self.fix_permissions()

        if not ok:
            self.__log('|-Fix website directories and files permissions failed: {}'.format(msg))
            return public.aap_t_simple_result(False, msg)

        self.__log('|-Fix website directories and files permissions succeeded')

        self.__log('|-Unpack package {} succeeded'.format(package_file))

        return public.aap_t_simple_result(True, public.lang('Unpack package successfully'))

    # 添加Hosts
    def add_hosts(self) -> public.aap_t_simple_result:
        hosts_file = '/etc/hosts'

        if not os.path.exists(hosts_file):
            return public.aap_t_simple_result(False, public.lang('Failed to add hosts, because hosts file not found'))

        if re.search(r'127\.0\.0\.1\s+{}'.format(self.wpmgr().retrieve_first_domain().replace('.', r'\.')), public.readFile(hosts_file)):
            return public.aap_t_simple_result(True, public.lang('Hosts has been exists'))

        public.writeFile(hosts_file, '\n127.0.0.1 {}'.format(self.wpmgr().retrieve_first_domain()), 'a')

        return public.aap_t_simple_result(True, public.lang('Hosts was add successfully'))

    # 初始化Wordpress配置文件
    def setup_wp_config(self, dbname: str, uname: str, pwd: str, dbhost: str, prefix: str) -> public.aap_t_simple_result:
        wp_config_file = '{}/wp-config.php'.format(self.wpmgr().retrieve_wp_root_path())
        wp_config_sample_file = '{}/wp-config-sample.php'.format(self.wpmgr().retrieve_wp_root_path())

        # 检查模板文件是否存在
        if not os.path.exists(wp_config_sample_file) or os.path.getsize(wp_config_sample_file) < 10:
            return public.aap_t_simple_result(False, public.lang('Sorry, I need a {} file to work from. Please re-upload this file to your WordPress installation.', 'wp-config-sample.php'))

        # 检查配置文件是否已经生成
        if os.path.exists(wp_config_file) and os.path.getsize(wp_config_file) > 10:
            return public.aap_t_simple_result(False, public.lang('The file {} already exists. If you need to reset any of the configuration items in this file, please delete it first.', 'wp_config.php'))

        with open(wp_config_file, 'w') as fp:
            with open(wp_config_sample_file, 'r') as fp_2:
                fp.write(fp_2.read())

        # 更新配置信息
        return self.update_wp_config(wp_config_file, {
            'DB_NAME': dbname,
            'DB_USER': uname,
            'DB_PASSWORD': pwd,
            'DB_HOST': dbhost,
            'table_prefix': prefix,
            'AUTH_KEY': self.generate_salt(),
            'SECURE_AUTH_KEY': self.generate_salt(),
            'LOGGED_IN_KEY': self.generate_salt(),
            'NONCE_KEY': self.generate_salt(),
            'AUTH_SALT': self.generate_salt(),
            'SECURE_AUTH_SALT': self.generate_salt(),
            'LOGGED_IN_SALT': self.generate_salt(),
            'NONCE_SALT': self.generate_salt(),
        })

    # 修改Wordpress配置文件（用于新增、修改、删除）
    @classmethod
    def update_wp_config(cls, wp_config_file: str, update_config: typing.Dict[str, typing.Union[str, int, float, bool]]) -> public.aap_t_simple_result:
        # 检查文件是否存在
        if not os.path.exists(wp_config_file):
            return public.aap_t_simple_result(False, public.lang('File {} not found', wp_config_file))

        lines = []

        # Wordpress默认配置项
        wp_inner_configs = (
            'table_prefix',
            'DB_NAME',
            'DB_USER',
            'DB_PASSWORD',
            'DB_HOST',
            'DB_CHARSET',
            'DB_COLLATE',
            'AUTH_KEY',
            'SECURE_AUTH_KEY',
            'LOGGED_IN_KEY',
            'NONCE_KEY',
            'AUTH_SALT',
            'SECURE_AUTH_SALT',
            'LOGGED_IN_SALT',
            'NONCE_SALT',
            'WP_DEBUG',
            'ABSPATH',
        )

        # 配置项下标
        wp_config_index = {}

        # 初始化配置项下标
        for k in wp_inner_configs:
            wp_config_index[k] = 0

        # 预编译正则表达式
        constant_regexp = re.compile(r'^define\(\s*\'([A-Z0-9_]+)\',([ ]+)?')
        constant_padding = None

        # 匹配多行注释结尾
        multi_comment_end_regexp = re.compile(r'^\*+/')

        # 读取现有的配置文件
        with open(wp_config_file, 'r') as fp:
            i = 0
            for line in fp:
                # 查找数据库前缀
                if line.strip().startswith('$table_prefix') and line.find('=') > -1:
                    wp_config_index['table_prefix'] = i
                else:
                    # 查找配置项
                    m = constant_regexp.match(line.strip())

                    if m is not None:
                        wp_config_index[m.group(1)] = i

                        if constant_padding is None:
                            constant_padding = m.group(2)

                lines.append(line)
                i += 1

        if constant_padding is None:
            constant_padding = ' '

        # 待删除的行
        remove_idx_set = set()

        # 增加的配置项
        add_configs = []

        # 开始更新配置项
        for k, v in update_config.items():
            # 标记是否进入配置删除分支
            is_remove = False

            if v is None:
                is_remove = True
            elif isinstance(v, bool):
                v = 'true' if v else 'false'
            elif isinstance(v, int):
                v = int(v)
            elif public.is_number(v):
                v = float(v)
            elif isinstance(v, str):
                v = "'{}'".format(str(v).replace("'", r"\'"))
            else:
                raise RuntimeError(public.get_msg_gettext('Invalid wp-config value {} {}', (type(v), v)))

            # 修改表前缀
            if k.lower() in ('table_prefix', 'db_prefix', 'prefix'):
                # 不能删除表前缀
                if is_remove:
                    raise RuntimeError(public.get_msg_gettext('Cannot remove config table_prefix on wordpress'))

                lines[wp_config_index['table_prefix']] = '''$table_prefix = {};\r\n'''.format(v)
                continue

            # 配置名称转大写
            k = k.upper()

            # 进入配置删除分支
            if is_remove:
                # 不能删除WP默认的配置项
                if k in wp_inner_configs:
                    raise RuntimeError(public.get_msg_gettext('Cannot remove config {} on wordpress', (k,)))

                # 删除已存在的配置项（记录删除的行下标）
                if k in wp_config_index:
                    remove_idx_set.add(wp_config_index[k])

                    i = wp_config_index[k] - 1
                    next_striped_line = lines[i].strip()

                    multi_comment = False
                    single_comment = False

                    # Wordpress固有注释
                    if next_striped_line.startswith('/* Add any custom values between this line and the "stop editing" line. */'):
                        pass

                    # 多行注释
                    elif multi_comment_end_regexp.match(next_striped_line):
                        multi_comment = True

                    # 单行注释
                    elif next_striped_line.startswith('//') or next_striped_line.startswith('/*'):
                        single_comment = True

                    # 检索该配置的注释信息，一起删除
                    if multi_comment or single_comment:
                        while i > 0:
                            remove_idx_set.add(i)
                            i -= 1

                            next_striped_line = lines[i].strip()

                            # 多行注释
                            if multi_comment:
                                # 多行注释结束
                                if next_striped_line.startswith('/*'):
                                    multi_comment = False

                                continue

                            # 单行注释结束
                            if not next_striped_line.startswith('//') or next_striped_line.startswith('/*'):
                                break

                continue

            # 修改现有配置
            if k in wp_config_index:
                lines[wp_config_index[k]] = '''define( '{}',{}{} );\r\n'''.format(k, constant_padding, v)
                continue

            # 新增自定义配置
            add_configs.append('''define( '{}',{}{} );\r\n'''.format(k, constant_padding, v))

        # 新的内容
        new_lines = []
        inserted_flag = len(add_configs) == 0

        # 开始更新配置文件内容
        for i in range(len(lines)):
            # 过滤已被标记删除的行
            if i in remove_idx_set:
                continue

            new_lines.append(lines[i])

            # 寻找新配置插入位置
            if not inserted_flag:
                striped_line = lines[i].strip()

                # 理想位置
                if striped_line.startswith(r'/* Add any custom values between this line and the "stop editing" line. */'):
                    inserted_flag = True
                    new_lines.append('\r\n')
                    new_lines.extend(add_configs)
                    continue

                # 比较合理的位置
                if striped_line.startswith('require ') or striped_line.startswith('require_once '):
                    inserted_flag = True

                    stack = []
                    stack.append(new_lines.pop())

                    # 检索require的注释，将新配置插入到注释的上方位置
                    if len(new_lines) > 0:
                        next_line = new_lines.pop()
                        next_striped_line = next_line.strip()

                        multi_comment = False
                        single_comment = False

                        # 多行注释
                        if multi_comment_end_regexp.match(next_striped_line):
                            multi_comment = True

                        # 单行注释
                        elif next_striped_line.startswith('//') or next_striped_line.startswith('/*'):
                            single_comment = True

                        # 检索该配置的注释信息
                        if multi_comment or single_comment:
                            while len(new_lines) > 0:
                                stack.append(next_line)

                                next_line = new_lines.pop()
                                next_striped_line = next_line.strip()

                                # 多行注释
                                if multi_comment:
                                    # 多行注释结束
                                    if next_striped_line.startswith('/*'):
                                        multi_comment = False

                                    continue

                                # 单行注释结束
                                if not next_striped_line.startswith('//') or next_striped_line.startswith('/*'):
                                    break

                    new_lines.extend(add_configs)
                    new_lines.append('\r\n')

                    while len(stack) > 0:
                        new_lines.append(stack.pop())

                    continue

        # 检查是否有以<?php开头的行
        if len(new_lines) > 0:
            flag = False
            for line in new_lines:
                if line.strip().startswith('<?php'):
                    flag = True
                    break

            if not flag:
                new_lines.insert(0, '<?php\r\n')

        # 更新WP配置文件
        with open(wp_config_file, 'w') as fp:
            fp.write(''.join(new_lines))

        return public.aap_t_simple_result(True, public.lang('Update successfully'))

    # 生成WP配置项的盐
    @classmethod
    def generate_salt(cls) -> str:
        chars = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789!@#$%^&*()-_ []{}<>~`+=,.;:/?|'
        max = len(chars) - 1

        from random import randint

        result = ''

        for i in range(64):
            result += chars[randint(0, max)]

        return result

    # 测试MySQL数据库连接
    @classmethod
    def test_mysql_connection(cls, db_name: str, db_user: str, db_pwd: str, prefix: str = 'wp_', db_host: str = 'localhost') -> public.aap_t_simple_result:
        import pymysql

        try:
            with public.MysqlConn(db_name, db_user, db_pwd, db_host) as conn:
                conn.execute('select `{}`'.format(prefix))
        except pymysql.OperationalError as e:
            # 数据库连接失败，用户名或密码错误
            if str(e).startswith('(1045, '):
                return public.aap_t_simple_result(False, "Mysql数据库连接失败，用户名或密码错误，您可以尝试修改或更新对应数据的密码")

            # 数据库连接失败，无法建立连接
            if str(e).startswith('(2003, '):
                return public.aap_t_simple_result(False, "Mysql数据库连接失败，无法建立连接，请检查数据库服务器是否正常启动")

            # 查询错误，字段或表不存在（当出现这个错误时，说明测试通过）
            if str(e).startswith('(1054, '):
                return public.aap_t_simple_result(True, public.lang('MySQL connection is well'))

            raise
        except pymysql.InternalError as e:
            # 查询错误，字段或表不存在（当出现这个错误时，说明测试通过）
            if str(e).startswith('(1054, '):
                return public.aap_t_simple_result(True, public.lang('MySQL connection is well'))

            raise

        return public.aap_t_simple_result(False, public.lang('Table prefix {} has been used as the table name', prefix))

    # 更新网站URL
    def fix_site_url(self, sub_path: str = '') -> public.aap_t_simple_result:
        site_url = self.wpmgr().build_site_url(sub_path)

        old_site_url = self.wpmgr().get_site_url()

        if site_url != old_site_url:
            self.wpmgr().set_site_url(site_url)

        return public.aap_t_simple_result(True, public.lang('Fix wordpress siteurl successfully'))

    # 移除.user.ini特殊权限
    def strip_attr_i_with_user_ini(self) -> public.aap_t_simple_result:
        user_ini_file = '{}/.user.ini'.format(self.wpmgr().retrieve_wp_root_path())

        if not os.path.exists(user_ini_file):
            return public.aap_t_simple_result(True, public.lang('Noting to change'))

        public.ExecShell('chattr -i {}'.format(user_ini_file))

        return public.aap_t_simple_result(True, public.lang('Strip file {} attribute i successfully', '.user.ini'))

    # 更新.user.ini
    def fix_user_ini(self) -> public.aap_t_simple_result:
        user_ini_file = '{}/.user.ini'.format(self.wpmgr().retrieve_wp_root_path())

        if not os.path.exists(user_ini_file):
            return public.aap_t_simple_result(True, public.lang('Noting to change'))

        with open(user_ini_file, 'r') as fp:
            content = fp.read()

        content = re.sub(r'open_basedir\s*=\s*([^:]+)', 'open_basedir={}'.format(self.wpmgr().retrieve_wp_root_path()), content)

        public.ExecShell('chattr -i {}'.format(user_ini_file))

        with open(user_ini_file, 'w') as fp:
            fp.write(content)

        public.ExecShell('chattr +i {}'.format(user_ini_file))

        return public.aap_t_simple_result(True, public.lang('Update file {} successfully', '.user.ini'))

    # 修改.user.ini文件（context）
    @contextlib.contextmanager
    def modify_user_ini_with_context(self):
        try:
            user_ini_file = '{}/.user.ini'.format(self.wpmgr().retrieve_wp_root_path())

            # 没有user_ini文件时,创建一个
            if not os.path.exists(user_ini_file):
                with open(user_ini_file, 'w') as fp:
                    fp.write('open_basedir={}'.format(self.wpmgr().retrieve_wp_root_path()))

            self.strip_attr_i_with_user_ini()
            yield user_ini_file
        finally:
            self.fix_user_ini()


# WP远程管理类
class wpmgr_remote:
    __TABLE_NAME = 'wordpress_remote'

    def __init__(self, remote_id: int = 0):
        self.__remote_id = int(remote_id)
        self.__wp_site_url = None
        self.__wp_login_url = None
        self.__wp_username = None
        self.__wp_password = None
        self.__security_key = None
        self.__security_token = None
        self.__ensure_table_exists()
        self.__request_session = requests.Session()
        self.__init()

    # debug日志
    @classmethod
    def _log(cls, s: str):
        log_path = '/tmp/wpmgr_remote.log'
        with open(log_path, 'a') as fp:
            fp.write('[{}] {}\n'.format(time.strftime('%Y-%m-%d %X'), s))

    # 写面板操作日志
    @classmethod
    def log_opt(cls, msg: str, args: typing.Tuple = ()):
        public.WriteLog('WP Toolkit Remote', public.get_msg_gettext(msg, args))

    # 确保数据表已创建
    def __ensure_table_exists(self):
        if not public.M('sqlite_master').where('type=? AND name=?', ('table', self.__TABLE_NAME)).count():
            public.M('').execute(r'''CREATE TABLE  IF NOT EXISTS `{table_name}` (
`id` INTEGER PRIMARY KEY AUTOINCREMENT,
`create_time` INTEGER NOT NULL DEFAULT (strftime('s')),
`site_url` TEXT NOT NULL DEFAULT '',
`login_url` TEXT NOT NULL DEFAULT '',
`username` TEXT NOT NULL DEFAULT '',
`password` TEXT NOT NULL DEFAULT '',
`security_key` TEXT NOT NULL DEFAULT '',
`security_token` TEXT NOT NULL DEFAULT '',
`env_info` TEXT NOT NULL DEFAULT '{{}}'
);'''.format(table_name=self.__TABLE_NAME))

    # 查询帮助函数
    @classmethod
    def __query(cls):
        return public.S(cls.__TABLE_NAME)

    # 加载数据
    def __init(self):
        if self.__remote_id > 0:
            ret = self.__query().where('id', self.__remote_id).find()

            if ret is None:
                return

            self.__wp_site_url = ret['site_url']
            self.__wp_login_url = ret['login_url']
            self.__wp_username = ret['username']
            self.__wp_password = ret['password']
            self.__security_key = ret['security_key']
            self.__security_token = ret['security_token']

    # 解析WP登录地址（获取WP首页地址）
    def __parse_login_url(self, login_url: str):
        parse_ret = urlparse(login_url)
        self.__wp_site_url = parse_ret.scheme + '://' + parse_ret.netloc

    # 添加WP远程站点
    def add(self, login_url: str, username: str, password: str) -> bool:
        try:
            # 尝试登录并添加远程站点
            if not self.login_with_credentials(login_url, username, password):
                raise public.HintException(public.lang('无法登录wordpress'))

            # 安装远程管理插件
            self.setup_aapenel_wp_toolkit()

            # 获取WP信息
            self.environment_info()

            # 提交安装统计
            threading.Thread(target=requests.post, kwargs={
                'url': '{}/api/panel/panel_count_daily'.format(public.OfficialApiBase()),
                'data': {
                    'name': 'wp_toolkit_remote',
                }}).start()
        except:
            self.remove()
            raise

        return True

    # 添加WP远程站点（手动安装）
    def add_manually(self, login_url: str, security_key: str, security_token: str) -> bool:
        try:
            self.__security_key = security_key
            self.__security_token = security_token

            # 解析WP登录地址（获取WP首页地址）
            self.__parse_login_url(login_url)

            # 获取WP信息
            env_info = self.environment_info()

            # 新增WP远程站点
            self.__remote_id = self.__query().insert({
                'create_time': int(time.time()),
                'site_url': self.__wp_site_url,
                'login_url': login_url,
                'security_key': security_key,
                'security_token': security_token,
                'env_info': json.dumps(env_info),
            })

            # 提交安装统计
            threading.Thread(target=requests.post, kwargs={
                'url': '{}/api/panel/panel_count_daily'.format(public.OfficialApiBase()),
                'data': {
                    'name': 'wp_toolkit_remote',
                }}).start()
        except:
            self.remove()
            raise

        return True

    # 删除WP远程站点
    def remove(self) -> bool:
        return self.__query().where('id', self.__remote_id).delete() > 0

    # 获取WP远程站点列表
    @classmethod
    def list(cls, keyword: str = '', p: int = 1, p_size: int = 20) -> typing.Dict[str, any]:
        query = cls.__query()

        keyword = keyword.strip()

        if keyword != '':
            query.where('site_url like ? escape \'\\\'', '%{}%'.format(public.escape_sql_str(keyword)))

        if p < 1:
            p = 1

        if p_size < 1:
            p_size = 20

        query_2 = query.fork()

        lst = query.skip((p-1) * p_size)\
            .limit(p_size)\
            .field('id', 'site_url', 'login_url', 'username', 'env_info', 'create_time')\
            .order('id', 'desc')\
            .select()

        for item in lst:
            try:
                item['env_info'] = json.loads(item['env_info'])
            except:
                item['env_info'] = {
                    'wordpress_version': '',
                    'php_version': '',
                    'mysql_version': '',
                    'plugin_version': '',
                    'locale': '',
                }

        # 启动一个线程去更新WP信息
        threading.Thread(target=cls._update_env_info, args=(list(map(lambda x: x['id'], lst)),)).start()

        return {
            'total': query_2.count(),
            'list': lst,
        }

    # 使用账号密码登录WP站点
    def login_with_credentials(self, login_url: str, username: str, password: str, retry_count: int = 0) -> bool:
        # 解析WP登录地址（获取WP首页地址）
        self.__parse_login_url(login_url)

        # 首先使用GET请求登录页面，设置test_cookie
        resp = self.__request_session.get(login_url, verify=False, timeout=60)

        # 访问登录页失败，提示无法访问URL
        if not resp.ok:
            # 响应403，尝试重新请求一遍
            if resp.status_code == 403 and retry_count < 1:
                return self.login_with_credentials(login_url, username, password, retry_count + 1)

            raise public.HintException(public.lang('Cannot connect to site: {}', resp.status_code))

        # 请求登录
        resp = self.__request_session.post(login_url, data={
            'log': username,
            'pwd': password,
            'wp-submit': 'login',
            'testcookie': 1,
        }, verify=False, timeout=60)

        # 登录成功时，插入一条数据记录或更新记录
        if resp.ok:
            # 检查是否登录失败
            m = re.search(r'<div id="login_error"[^>]*>([\s\S]+?)</div>', resp.text)

            if m:
                # 提示错误信息
                raise public.HintException(m.group(1))

            # 检查是否登录成功，还是跳转了https
            m = re.search(r'<form name="loginform" id="loginform" action="([^"]+)" method="post">', resp.text)

            # 匹配到了登录表单，说明可能跳转了https站点
            # 使用匹配到的登录url再次尝试登录
            if m and retry_count < 3:
                self._log('login retry: {}'.format(m.group(1)))
                return self.login_with_credentials(m.group(1), username, password, retry_count + 1)

            if self.__remote_id < 1:
                self.__remote_id = self.__query().insert({
                    'create_time': int(time.time()),
                    'site_url': self.__wp_site_url,
                    'login_url': login_url,
                    'username': username,
                    'password': password,
                })
                self.__init()
            else:
                self.__query().where('id', self.__remote_id).update({
                    'site_url': self.__wp_site_url,
                    'login_url': login_url,
                    'username': username,
                    'password': password,
                })

        if not resp.ok:
            with open('/tmp/wp_login.html', 'w') as fp:
                fp.write(resp.text)

            # 当响应码为403时，尝试再次请求登录
            if resp.status_code == 403 and retry_count < 1:
                return self.login_with_credentials(login_url, username, password, retry_count + 1)

        seps = resp.url.split('/wp-admin/')

        if len(seps) > 1:
            self.__wp_site_url = seps[0]

        return resp.ok

    # 远程安装并激活aapanel-wp-toolkit
    def setup_aapenel_wp_toolkit(self):
        # 下载插件
        self._log('Downloading plugin...')

        plugin_file_path = '{}/temp/aapanel-wp-toolkit.zip'.format(public.get_panel_path())

        if not os.path.exists(plugin_file_path):
            resp = requests.get('{}/install/src/aapanel-wp-toolkit.zip'.format(public.OfficialDownloadBase()), verify=False, timeout=120)

            if not resp.ok:
                # public.print_log(resp.text)
                self._log('Download plugin failed: {}'.format(resp.status_code))
                raise public.HintException('Not found aapanel-wp-toolkit')

            with open(plugin_file_path, 'wb') as fp:
                fp.write(resp.content)

        self._log('Plugin downloaded, uploading to site...')
        self._log('Getting _wpnonce and _wp_http_referer from /plugin-install page')

        # 访问插件安装页面，获取_wpnonce与_wp_http_referer
        _wpnonce, _wp_http_referer = self.invite_page_and_get_wpnonce('{}/wp-admin/plugin-install.php'.format(self.__wp_site_url))

        self._log('Get _wpnonce={} and _wp_http_referer={}'.format(_wpnonce, _wp_http_referer))

        # 构造formdata
        formdata = {
            '_wpnonce': _wpnonce,
            '_wp_http_referer': _wp_http_referer,
            'install-plugin-submit': 'Immediately',
        }

        with open(plugin_file_path, 'rb') as fp:
            formdata['pluginzip'] = (fp.read(), os.path.basename(plugin_file_path))

        # 将插件上传到对应Wordpress站点
        headers, body = public.build_multipart(formdata)
        headers['Referer'] = '{}{}'.format(self.__wp_site_url, _wp_http_referer)

        self._log('Headers {}'.format(headers))

        resp = self.__request_session.post('{}/wp-admin/update.php?action=upload-plugin'.format(self.__wp_site_url), data=body, headers=headers, verify=False, timeout=600)

        if not resp.ok:
            self._log('Plugin upload failed: {}'.format(resp.status_code))
            # public.print_log('{} {}'.format(resp.status_code, resp.text))
            raise public.HintException(public.lang('Setup aapanel-wp-toolkit failed: {}', resp.status_code))

        self._log('Plugin uploaded to site, start activating...')
        self._log('Finding activation url in page...')

        # 用于标记是否跳过插件激活操作
        skip_activation = False

        # 匹配插件激活url
        m = re.search(r'href="(plugins\.php\?action=activate&amp;plugin=[^"]+)"', resp.text)

        if not m:
            # 未匹配到插件激活url时，可能插件已安装，尝试匹配插件覆盖安装url
            m = re.search(r'href="(update\.php\?action=upload-plugin&amp;package=\d+&amp;overwrite=update-plugin&amp;[^"]+)"', resp.text)

            if not m:
                self._log('Activation url not found in page')
                with open('/tmp/wp_upload_plugin.html', 'w') as fp:
                    fp.write(resp.text)
                raise public.HintException(public.lang('Setup aapanel-wp-toolkit failed: not found activation url'))

            override_url = '{}/wp-admin/{}'.format(self.__wp_site_url, html.unescape(m.group(1)))

            self._log('Plugin has installed, try overriding with {}'.format(override_url))

            # 覆盖安装
            resp = self.__request_session.get(override_url, verify=False, timeout=60)

            if not resp.ok:
                self._log('overriding plugin failed: {}'.format(resp.status_code))
                with open('/tmp/wp_upload_plugin.html', 'w') as fp:
                    fp.write(resp.text)
                raise public.HintException(public.lang('Setup aapanel-wp-toolkit failed: failed to override plugin'))

            # 覆盖安装成功，再次尝试匹配插件激活url
            m = re.search(r'href="(plugins\.php\?action=activate&amp;plugin=[^"]+)"', resp.text)

            # 匹配不到插件激活url，说明插件已经处于激活状态
            if not m:
                skip_activation = True
                self._log('Plugin has been activated, skip the activation')

        # 激活插件
        if not skip_activation:
            activation_url = '{}/wp-admin/{}'.format(self.__wp_site_url, html.unescape(m.group(1)))

            self._log('Find activation url {}, now activate it...'.format(activation_url))

            resp = self.__request_session.get(activation_url, verify=False, timeout=60)

            if not resp.ok:
                self._log('Plugin activation failed: {}'.format(resp.status_code))
                # public.print_log('{} {}'.format(resp.status_code, resp.text))
                raise public.HintException(public.lang('Activate aapanel-wp-toolkit failed: {}', resp.status_code))

            self._log('Plugin activation success, getting wordpress information...')

        # 通过访问aapanel-wp-toolkit插件，获取security_key并存储
        resp = self.__request_session.get(self.__wp_site_url, params={
            '_aap_action': 'security_key_info',
        }, verify=False, timeout=60)

        if not resp.ok or resp.headers.get('content-type', '').find('application/json') < 0:
            self._log('Get wordpress information failed: {}'.format(resp.status_code))
            # public.print_log('{} {}'.format(resp.status_code, resp.text))
            raise public.HintException(public.lang('Setup aapanel-wp-toolkit failed: activate failed'))

        ret = resp.json()

        if not ret.get('success', False):
            public.print_log(ret)
            raise public.HintException(public.lang('Cannot get security key from aapanel-wp-toolkit'))

        security_key_info = ret.get('data', {})
        self.__security_key = security_key_info.get('security_key')
        self.__security_token = security_key_info.get('security_token')

        # 更新到数据库中
        if self.__remote_id > 0 and self.__security_key and self.__security_token:
            self.__query().where('id', self.__remote_id).update({
                'security_key': self.__security_key,
                'security_token': self.__security_token,
            })

        self._log('WP Remote Site is added')

    # 通过security_key发起请求
    def request_with_security_key(self, action: str, data: typing.Dict = {}):
        data['_aap_action'] = action

        resp = requests.post(self.__wp_site_url.rstrip('/') + '/', json=data, headers={
            'AAP-WP-TOOLKIT-{}'.format(self.__security_key): self.__security_token,
        }, verify=False, timeout=120)

        if not resp.ok or resp.headers.get('content-type', '').find('application/json') < 0:
            # public.print_log('{} {}'.format(resp.status_code, resp.text))
            raise public.HintException('Request to aapanel-wp-toolkit failed: {}'.format(self.get_error_message(resp)))

        return resp.json().get('data')

    # 从Response中获取错误提示信息
    def get_error_message(self, resp: requests.Response) -> typing.Optional[str]:
        try:
            res = resp.json()

            if not res.get('success', False):
                errmsg = res.get('data', {}).get('error', None)

                if errmsg is None:
                    errmsg = res.get('data', {}).get('errorMessage')

                return errmsg
        except:
            return 'invalid action'

        return str(resp.status_code)

    # 访问指定页面并读取_wpnonce和_wp_http_referer
    def invite_page_and_get_wpnonce(self, url: str) -> typing.Tuple:
        resp = self.__request_session.get(url, verify=False, timeout=120)

        if not resp.ok:
            # public.print_log('{} {}'.format(resp.status_code, resp.text))
            raise public.HintException('Load page failed: {}'.format(resp.status_code))

        m = re.search(r'<input type="hidden" id="_wpnonce" name="_wpnonce" value="([^"]+)"[^>]*>[^<]*<input type="hidden" name="_wp_http_referer" value="([^"]+)"[^>]*>', resp.text)

        if not m:
            # public.print_log('{} {}'.format(resp.status_code, resp.text))
            raise public.HintException('Not found _wpnonce in page: {}'.format(resp.request.url))

        return (m.group(1), m.group(2))

    # 一键登录
    def auto_login(self):
        from BTPanel import redirect
        return '{}/?{}={}&_aap_action=auto_login'.format(self.__wp_site_url, self.__security_key, self.__security_token)

    # 获取Wordpres版本信息
    def environment_info(self):
        ret = self.request_with_security_key('environment_info')

        # 更新数据
        if self.__remote_id > 0:
            self.__query().where('id', self.__remote_id).update({
                'env_info': json.dumps(ret),
            })

        self._log('environment_info {}'.format(ret))

        return ret

    # 更新Wordpress信息
    @classmethod
    def _update_env_info(cls, remote_ids: typing.List):
        for remote_id in remote_ids:
            try:
                cls(remote_id).environment_info()
            except: pass




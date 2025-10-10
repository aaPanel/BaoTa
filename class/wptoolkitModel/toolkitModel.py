import json
import os
from types import MethodType

from flask import request
from wptoolkitModel.base import wpbase
import requests
import panelSite
import public_wp as public
from wptoolkitModel import one_key_wp_v2, base

class main(wpbase):
    def __init__(self, get=None):
        super(main, self).__init__(get)

    #  入口函数 处理dict_obj
    def api(self, get):
        query = request.args
        if not query.get("action"):
            return public.returnMsg(False, "参数错误")
        action = query['action']
        get = public.to_dict_obj(vars(get))
        method = getattr(self, action)
        return method(get)

    # 新增站点
    def AddWPSite(self, get):
        public.set_module_logs('wp_toolkit', 'AddWPSite', 1)
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().AddWPSite(get)

    # 重置Wordpress管理员账号密码
    def reset_wp_password(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().reset_wp_password(get)

    # 检查Wordpress版本更新
    def is_update(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().is_update(get)

    # 清除Wordpress Nginx fastcgi cache
    def purge_all_cache(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().purge_all_cache(get)

    # 设置Wordpress Nginx fastcgi cache
    def set_fastcgi_cache(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().set_fastcgi_cache(get)

    # 更新Wordpress到最新版本
    def update_wp(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().update_wp(get)

    # 获取可用的语言列表
    def get_language(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().get_language(get)

    # 获取可用的WP安装版本
    def get_wp_versions(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().get_wp_available_versions(get)

    # 获取WP Toolkit配置信息
    def get_wp_configurations(self, args):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().get_wp_configurations(args)

    # 保存WP Toolkit配置
    def save_wp_configurations(self, args):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().save_wp_configurations(args)

    # 获取wp 安全模块配置
    def get_wp_security_info(self, get):
        from wp_toolkit import wp_security
        result = wp_security().get_security_info(get)
        get.name = get.site_name
        # 取防盗链配置
        from panelSite import panelSite
        hotlink = panelSite().GetSecurity(get)
        print(hotlink)
        try:
            result['msg']['hotlink_status'] = 1 if hotlink['status'] else 0
        except:
            pass
        return result

    # 开启WP 文件防护
    def open_wp_file_protection(self, get):
        from wp_toolkit import wp_security
        return wp_security().open_file_protection(get)

    # 关闭WP 文件防护
    def close_wp_file_protection(self, get):
        from wp_toolkit import wp_security
        return wp_security().close_file_protection(get)

    # 获取WP 文件防护
    def get_wp_file_info(self, get):
        from wp_toolkit import wp_security
        return wp_security().get_file_info(get)

    # 开启WP 防火墙防护
    def open_wp_firewall_protection(self, get):
        from wp_toolkit import wp_security
        return wp_security().open_firewall_protection(get)

    # 关闭WP 防火墙防护
    def close_wp_firewall_protection(self, get):
        from wp_toolkit import wp_security
        return wp_security().close_firewall_protection(get)

    def deploy_wp(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().deploy_wp(get)

    def get_wp_username(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().get_wp_username(get)

    def reset_wp_db(self, get):
        import one_key_wp_v2 as one_key_wp
        return one_key_wp.one_key_wp().reset_wp_db(get)

    # 备份WP站点
    def wp_backup(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('bak_type').Require().Integer('>', 0),
        ])

        from wp_toolkit import wpbackup

        bak_obj = wpbackup(args.s_id)
        bak_type = int(args.bak_type)

        if bak_type == 1:
            ok, msg = bak_obj.backup_files()
        elif bak_type == 2:
            ok, msg = bak_obj.backup_database()
        elif bak_type == 3:
            ok, msg = bak_obj.backup_full()
        else:
            return public.fail_v2('备份类型无效 {}', (bak_type,))

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 还原WP站点
    def wp_restore(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('bak_id').Require().Integer('>', 0),
        ])

        from wp_toolkit import wpbackup

        bak_id = int(args.bak_id)
        bak_obj = wpbackup(wpbackup.retrieve_site_id_with_bak_id(bak_id))
        ok, msg = bak_obj.restore_with_backup(bak_id)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # WP备份列表
    def wp_backup_list(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('p').Integer('>', 0),
            public.Param('limit').Integer('>', 0),
            public.Param('tojs').Regexp(r"^[\w\.\-]+$"),
            public.Param('result').Regexp(r"^[\d\,]+$"),
        ])

        from wp_toolkit import wpbackup

        bak_obj = wpbackup(args.s_id)

        return public.success_v2(bak_obj.backup_list(args))

    # 删除WP站点备份
    def wp_remove_backup(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('bak_id').Require().Integer('>', 0),
        ])

        from wp_toolkit import wpbackup

        bak_id = int(args.bak_id)
        bak_obj = wpbackup(wpbackup.retrieve_site_id_with_bak_id(bak_id))
        ok, msg = bak_obj.remove_backup(bak_id)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    def migrate_site_to_wptoolkit(self, args: public.dict_obj):
        public.set_module_logs('wp_toolkit', 'migrate_site_to_wptoolkit', 1)
        from wp_toolkit import wpmigration
        ok, msg = wpmigration(args.site_id).migrate_site_to_wptoolkit(args)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 从 [网站管理] 迁移到 [WP Toolkit]
    def wp_migrate_from_website_to_wptoolkit(self, args: public.dict_obj):
        from wp_toolkit import wpmigration
        ok, msg = wpmigration.migrate_aap_from_website_to_wptoolkit()

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 查询可从 [网站管理] 迁移到 [WP Toolkit] 的网站列表
    def wp_can_migrate_from_website_to_wptoolkit(self, args: public.dict_obj):
        from wp_toolkit import wpmigration
        return public.success_v2(wpmigration.can_migrations_of_aap_website())

    # 从aapanel WP备份中创建WP站点
    def wp_create_with_aap_bak(self, args: public.dict_obj):
        from wp_toolkit import wpbackup
        ok, msg = wpbackup.wp_deploy_with_aap_bak(args)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 从plesk/cpanel WP备份中创建WP站点
    def wp_create_with_plesk_or_cpanel_bak(self, args: public.dict_obj):
        from wp_toolkit import wpbackup
        ok, msg = wpbackup.wp_deploy_with_plesk_or_cpanel_bak(args)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 克隆WP站点
    def wp_clone(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
        ])

        from wp_toolkit import wpbackup

        ok, msg = wpbackup(args.s_id).clone(args)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # Wordpress完整性校验
    def wp_integrity_check(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
        ])

        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.s_id).integrity_check()

        if not ok:
            _return = public.fail_v2(msg)
        else:
            _return = public.success_v2(msg)
        _return['data'] = {}
        _return['data']['msg'] = _return['msg']
        return _return

    # 重新下载并安装Wordpress（仅限框架文件，不会删除新文件）
    def wp_reinstall_files(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
        ])

        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.s_id).reinstall_package()

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 获取可安装的插件列表
    def wp_plugin_list(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Integer('>', 0).Filter(int),
            public.Param('keyword'),
            public.Param('p').Integer('>', 0).Filter(int),
            public.Param('p_size').Integer('>', 0).Filter(int),
            public.Param('set_id').Integer('>', 0).Filter(int),
        ])

        from wp_toolkit import wpmgr

        if 's_id' in args:
            ok, msg = wpmgr(args.s_id).search_plugins(args.get('keyword', ''), args.get('p', 1), args.get('p_size', 20))
        else:
            ok, msg = wpmgr.query_plugins(args.get('keyword', ''), args.get('p', 1), args.get('p_size', 20),
                                          args.get('set_id', None))

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 安装插件
    def wp_install_plugin(self, args: public.dict_obj):
        public.set_module_logs('wp_toolkit', 'wp_install_plugin', 1)
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('slug').Require().SafePath(),
        ])

        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.s_id).install_plugin(args.slug)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 已安装插件列表
    def wp_installed_plugins(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('force_check_updates').Integer('in', [0, 1]),
        ])

        from wp_toolkit import wpmgr

        res = wpmgr(args.s_id).installed_plugins(bool(int(args.get('force_check_updates', 0))))
        if isinstance(res, str):
            return public.fail_v2(res)

        return public.success_v2(res)

    # 更新插件
    def wp_update_plugin(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('plugin_file').Require().SafePath(),
        ])

        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.s_id).update_plugin(args.plugin_file)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2('更新成功')

    # 开启/关闭插件自动更新
    def wp_set_plugin_auto_update(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('plugin_file').Require().SafePath(),
            public.Param('enable').Require().Integer('in', [0, 1]),
        ])

        from wp_toolkit import wpmgr

        wpmgr_obj = wpmgr(args.s_id)

        if int(args.enable) == 1:
            fn = wpmgr_obj.enable_plugin_auto_update
        else:
            fn = wpmgr_obj.disable_plugin_auto_update

        ok, msg = fn(args.plugin_file)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2('自动更新设置修改成功')

    # 激活/禁用插件
    def wp_set_plugin_status(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('plugin_file').Require().SafePath(),
            public.Param('activate').Require().Integer('in', [0, 1]),
        ])

        from wp_toolkit import wpmgr

        wpmgr_obj = wpmgr(args.s_id)

        if int(args.activate) == 1:
            fn = wpmgr_obj.activate_plugins
            errmsg = public.lang("激活失败，请稍后重试。")
        else:
            fn = wpmgr_obj.deactivate_plugins
            errmsg = public.lang("禁用失败，请稍后重试。")

        if not fn(args.plugin_file):
            return public.fail_v2(errmsg)

        return public.success_v2('插件状态修改成功')

    # 卸载插件
    def wp_uninstall_plugin(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('plugin_file').Require().SafePath(),
        ])

        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.s_id).uninstall_plugin(args.plugin_file)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2('卸载成功')

    # 获取可安装的主题列表
    def wp_theme_list(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Integer('>', 0).Filter(int),
            public.Param('keyword'),
            public.Param('p').Integer('>', 0).Filter(int),
            public.Param('p_size').Integer('>', 0).Filter(int),
            public.Param('set_id').Integer('>', 0).Filter(int),
        ])

        from wp_toolkit import wpmgr

        if 's_id' in args:
            ok, msg = wpmgr(args.s_id).search_themes(args.get('keyword', ''), args.get('p', 1), args.get('p_size', 20))
        else:
            ok, msg = wpmgr.query_themes(args.get('keyword', ''), args.get('p', 1), args.get('p_size', 20),
                                         args.get('set_id', None))

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 安装主题
    def wp_install_theme(self, args: public.dict_obj):
        public.set_module_logs('wp_toolkit', 'wp_install_theme', 1)
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('slug').Require(),
        ])

        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.s_id).install_theme(args.slug)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2(msg)

    # 已安装主题列表
    def wp_installed_themes(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('force_check_updates').Integer('in', [0, 1]),
        ])

        from wp_toolkit import wpmgr

        res = wpmgr(args.s_id).installed_themes(bool(int(args.get('force_check_updates', 0))))
        if isinstance(res, str):
            return public.fail_v2(res)

        return public.success_v2(res)

    # 更新主题
    def wp_update_theme(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('stylesheet').Require(),
        ])

        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.s_id).update_theme(args.stylesheet)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2('更新成功')

    # 开启/关闭主题自动更新
    def wp_set_theme_auto_update(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('stylesheet').Require(),
            public.Param('enable').Require().Integer('in', [0, 1]),
        ])

        from wp_toolkit import wpmgr

        wpmgr_obj = wpmgr(args.s_id)

        if int(args.enable) == 1:
            fn = wpmgr_obj.enable_theme_auto_update
        else:
            fn = wpmgr_obj.disable_theme_auto_update

        ok, msg = fn(args.stylesheet)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2('自动更新设置修改成功')

    # 切换主题
    def wp_switch_theme(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('stylesheet').Require(),
        ])

        from wp_toolkit import wpmgr

        if not wpmgr(args.s_id).switch_theme(args.stylesheet):
            return public.fail_v2('主题切换失败请稍后重试')

        return public.success_v2('切换成功')

    # 卸载主题
    def wp_uninstall_theme(self, args: public.dict_obj):
        # 参数校验
        args.validate([
            public.Param('s_id').Require().Integer('>', 0),
            public.Param('stylesheet').Require(),
        ])

        from wp_toolkit import wpmgr

        ok, msg = wpmgr(args.s_id).uninstall_theme(args.stylesheet)

        if not ok:
            return public.fail_v2(msg)

        return public.success_v2('卸载成功')

    # 获取所有WP站点
    def wp_all_sites(self, args: public.dict_obj):
        from wp_toolkit import wpmgr
        return public.success_v2(wpmgr.all_sites())

    # 获取WP整合包列表
    def wp_set_list(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('keyword'),
            public.Param('p').Filter(int),
            public.Param('p_size').Filter(int),
        ])

        from wp_toolkit import wp_sets
        return public.success_v2(
            wp_sets().fetch_list(args.get('keyword', ''), args.get('p', 1), args.get('p_size', 20)))

    # 新建WP整合包
    def wp_create_set(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('name').Require(),
        ])

        from wp_toolkit import wp_sets

        if wp_sets().create_set(args.name) < 1:
            raise public.HintException(public.lang("创建失败"))

        return public.success_v2('创建成功')

    # 删除WP整合包
    def wp_remove_set(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Regexp(r'^\d+(?:,\d+)*$'),
        ])

        from wp_toolkit import wp_sets

        if not wp_sets().remove_set(list(map(lambda x: int(x), str(args.set_id).split(',')))):
            raise public.HintException(public.lang("删除失败"))

        return public.success_v2('删除成功')

    # 获取WP整合包中的插件列表or主题列表
    def wp_get_items_from_set(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Integer('>', 0).Filter(int),
            public.Param('type').Require().Integer('in', [1, 2]).Filter(int),
        ])

        from wp_toolkit import wp_sets

        return public.success_v2(wp_sets().get_items(args.set_id, args.type))

    # 添加插件or主题到WP整合包中
    def wp_add_items_to_set(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Integer('>', 0).Filter(int),
            public.Param('items').Require().Array(),
            public.Param('type').Require().Integer('in', [1, 2]).Filter(int),
        ])

        from wp_toolkit import wp_sets

        typ = int(args.type)

        # 添加插件
        if typ == 1:
            ok, msg = wp_sets().add_plugins(int(args.set_id), json.loads(args.items))

        # 添加主题
        elif typ == 2:
            ok, msg = wp_sets().add_themes(int(args.set_id), json.loads(args.items))

        # 无效类型
        else:
            raise public.HintException(public.lang("无效类型"))

        if not ok:
            raise public.HintException(msg)

        return public.success_v2('添加成功')

    # 将插件or主题从WP整合包中移除
    def wp_remove_items_from_set(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('item_ids').Require().Regexp(r'^\d+(?:,\d+)*$'),
            public.Param('type').Require().Integer('in', [1, 2]).Filter(int),
        ])

        from wp_toolkit import wp_sets

        item_ids = list(map(lambda x: int(x), str(args.item_ids).split(',')))
        typ = int(args.type)

        # 删除插件
        if typ == 1:
            ok = wp_sets().remove_plugins(item_ids)

        # 删除主题
        elif typ == 2:
            ok = wp_sets().remove_themes(item_ids)

        # 无效类型
        else:
            raise public.HintException(public.lang("无效类型"))

        if not ok:
            raise public.HintException(public.lang("删除失败"))

        return public.success_v2('删除成功')

    # 更改WP整合包中插件or主题的激活状态
    def wp_update_item_state_with_set(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('item_ids').Require().Regexp(r'^\d+(?:,\d+)*$'),
            public.Param('state').Require().Integer('in', [0, 1]),
            public.Param('type').Require().Integer('in', [1, 2]).Filter(int),
        ])

        from wp_toolkit import wp_sets

        item_ids = list(map(lambda x: int(x), str(args.item_ids).split(',')))
        state = int(args.state)
        typ = int(args.type)

        # 删除插件
        if typ == 1:
            ok = wp_sets().update_plugins_state(state, item_ids)

        # 删除主题
        elif typ == 2:
            ok = wp_sets().update_theme_state(state, item_ids[0])

        # 无效类型
        else:
            raise public.HintException(public.lang("无效类型"))

        if not ok:
            raise public.HintException(public.lang("修改失败"))

        return public.success_v2('修改成功')

    # 通过WP整合包安装插件&主题
    def wp_install_with_set(self, args: public.dict_obj):
        public.set_module_logs('wp_toolkit', 'wp_install_with_set', 1)
        # 校验参数
        args.validate([
            public.Param('set_id').Require().Integer('>', 0),
            public.Param('site_ids').Require().Regexp(r'^\d+(?:,\d+)*$'),
        ])

        from wp_toolkit import wp_sets

        set_id = int(args.set_id)
        site_ids = list(map(lambda x: int(x), str(args.site_ids).split(',')))

        ok, msg = wp_sets().install(set_id, site_ids)

        if not ok:
            return public.returnMsg(False, msg)

        return public.success_v2(msg)

    # *********** WP Toolkit Remote --Begin-- *************

    # TODO 新增远程WP站点
    def wp_remote_add(self, args: public.dict_obj):
        public.set_module_logs('wp_toolkit', 'wp_remote_add', 1)

        # 校验参数
        args.validate([
            public.Param('login_url').Require().Url(),
            public.Param('username').Require(),
            public.Param('password').Require(),
        ])
        try:
            from wp_toolkit import wpmgr_remote
            wpmgr_remote().add(args.login_url, args.username, args.password)
        except Exception as e:
            return public.returnMsg(False, str(e))

        return public.success_v2('Success')

    # TODO 新增远程WP站点（手动安装）
    def wp_remote_add_manually(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('login_url').Require().Url(),
            public.Param('security_key').Require(),
            public.Param('security_token').Require(),
        ])

        from wp_toolkit import wpmgr_remote
        wpmgr_remote().add_manually(args.login_url, args.security_key, args.security_token)

        return public.success_v2('添加成功')

    # TODO 删除远程WP站点
    def wp_remote_remove(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('remote_id').Require().Integer('>', 0),
        ])

        from wp_toolkit import wpmgr_remote
        if not wpmgr_remote(args.remote_id).remove():
            raise public.HintException(public.lang('Remove wordpress remote site failed'))

        return public.success_v2('Success')

    # TODO 获取远程WP站点列表
    def wp_remote_sites(self, args: public.dict_obj):
        # 校验参数
        args.validate([
            public.Param('keyword'),
            public.Param('p').Filter(int),
            public.Param('p_size').Filter(int),
        ])

        from wp_toolkit import wpmgr_remote
        return public.success_v2(wpmgr_remote().list(args.get('keyword', ''), args.get('p', 1), args.get('p_size', 20)))

    # *********** WP Toolkit Remote --End-- *************

    @staticmethod
    def test_domains_api(get):
        try:
            domains = json.loads(get.domains.strip())
        except (json.JSONDecodeError, AttributeError, KeyError):
            return public.return_message(-1, 0, public.lang("参数错误"))
        try:
            from panel_dns_api_v2 import DnsMager
            public.print_log("开始测试域名解析---- {}")
            # public.print_log("开始测试域名解析---- {}".format(domains[0]))

            return DnsMager().test_domains_api(domains)
        except:
            pass
        public.return_message(0, 0, "")

    def site_rname(self, get):
        try:
            if not (hasattr(get, "id") and hasattr(get, "rname")):
                return public.return_message(-1, 0, public.lang("parameter error"))
            id = get.id
            rname = get.rname
            data = public.M('sites').where("id=?", (id,)).select()
            if not data:
                return public.return_message(-1, 0, public.lang("The site does not exist!"))
            data = data[0]
            name = data['rname'] if 'rname' in data.keys() and data.get('rname', '') else data['name']
            if 'rname' not in data.keys():
                public.M('sites').execute("ALTER TABLE 'sites' ADD 'rname' text DEFAULT ''", ())
            public.M('sites').where('id=?', data['id']).update({'rname': rname})
            # public.write_log_gettext('Site manager', 'Website [{}] renamed: [{}]'.format(name, rname))
            return public.return_message(0, 0, public.lang("Website [{}] renamed: [{}]", name, rname))
        except:
            return public.return_message(-1, 0, traceback.format_exc())

    # Wordpress 漏洞扫描
    def wordpress_vulnerabilities_scan(self, get):
        from wp_toolkit import wordpress_scan
        if 'path' not in get: public.return_message(0, 0, public.lang("Parameter error"))
        return public.return_message(0, 0, wordpress_scan.wordpress_scan().scan(get.path))

    def wordpress_vulnerabilities_time(self, get):
        from wp_toolkit import wordpress_scan
        return public.return_message(0, 0, wordpress_scan.wordpress_scan().get_vlu_time())

    def ignore_vuln(self, get):
        from wp_toolkit import wordpress_scan
        return wordpress_scan.wordpress_scan().ignore_vuln(get)

    def get_ignore_vuln(self, get):
        from wp_toolkit import wordpress_scan
        return wordpress_scan.wordpress_scan().get_ignore_vuln(get)

    def set_auth_scan(self, get):
        if 'path' not in get: public.return_message(0, 0, public.lang("Parameter error"))
        from wp_toolkit import wordpress_scan
        return wordpress_scan.wordpress_scan().set_auth_scan(get.path)

    def get_auth_scan_status(self, get):
        if 'path' not in get: public.return_message(0, 0, public.lang("Parameter error"))
        from wp_toolkit import wordpress_scan
        return wordpress_scan.wordpress_scan().get_auth_scan_status(get.path)

    def auto_login(self, get):
        if get.site_type == "local":
            from wp_toolkit import wpmgr
            return wpmgr(get.site_id).auto_login()
        elif get.site_type.lower() == 'remote':
            from wp_toolkit import wpmgr_remote
            return wpmgr_remote(get.site_id).auto_login()
        else:
            return public.returnMsg(False, "错误的类型")
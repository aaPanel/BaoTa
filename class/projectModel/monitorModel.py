# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板-基础网站数据统计模块
# 该模块用于统计基础网站数据，包括IP数量、流量、访问量、PV、UV等数据。
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: wpl <wpl@bt.cn>
# -------------------------------------------------------------------
import json
import os
import re
import sys

from datetime import datetime, timedelta
from safeModel.base import safeBase
os.chdir("/www/server/panel")
sys.path.append("class/")
import db
import public

class main(safeBase):
        # ------------------------ 常量设置 ------------------------
    TOTAL_DIR = '/www/server/site_total/data/total'
    SUMMARY_DIR = '/www/server/site_total/data/summary'
    def __init__(self):
        pass

    # ------------------------ 对外接口 ------------------------
    def get_overview(self, get=None):
        """
        @name 总概览接口（全站三日总览 + 网站排名TOP5 + 全站近7天趋势）
        @return public.return_data(True, data)
        安全与约束：
          - Top5站点，固定按pv升序排序（用户确认：默认升序，指标需传参，支持traffic/req_count/ip_count/uv/pv）
          - 日期以服务器本地时间为准：今日/昨日/前日
          - 近7天包含今日在内的连续7个自然日
        """
        public.set_module_logs('site_total', 'get_overview', 1)
        today, yesterday, day_before = self._get_three_days()
        # 三日总览（全站）
        today_total = self._get_all_sites_total_for_date(today)
        yesterday_total = self._get_all_sites_total_for_date(yesterday)
        day_before_total = self._get_all_sites_total_for_date(day_before)
        compare = self._compute_compare(today_total, yesterday_total)
        overview_three_days = {
            'today': self._format_daily_stat(today_total, include_compare=compare),
            'yesterday': self._format_daily_stat(yesterday_total),
            'day_before': self._format_daily_stat(day_before_total)
        }
        # Top5排序参数（支持传递，默认 pv/asc）
        metric = 'pv'
        order = 'asc'
        if get:
            try:
                gm = getattr(get, 'metric', None)
                go = getattr(get, 'order', None)
                if gm is None and isinstance(get, dict):
                    gm = get.get('metric')
                if go is None and isinstance(get, dict):
                    go = get.get('order')
                if gm:
                    metric = str(gm)
                if go:
                    order = str(go)
            except Exception:
                pass
        valid_metrics = ['traffic', 'req_count', 'ip_count', 'uv', 'pv']
        valid_orders = ['asc', 'desc']
        if metric not in valid_metrics:
            metric = 'pv'
        if order not in valid_orders:
            order = 'asc'

        # Top5 当天（支持传递 metric/order，默认 pv/asc）
        top5 = self._get_top_sites_for_date(today, metric=metric, order=order, limit=5)
        # 近7天趋势（全站）
        trend_points = self._build_trend_7days_all()
        rec_status, detail_id = self._get_rec_status_detail()
        data = {
            'date_range': {
                'today': today,
                'yesterday': yesterday,
                'day_before': day_before
            },
            'overview_three_days': overview_three_days,
            'top5_sites': {
                'metric': metric,
                'order': order,
                'timeframe': 'today',
                # 'range': {'date': today},
                'items': top5
            },
            'trend_7days': {
                'timeframe': 'last_7_days',
                'points': trend_points
            },
            'rec_status': rec_status,
            'detail_id': detail_id
        }
        return public.return_data(True, data)

    def get_site_overview(self, get):
        """
        @name 指定站点数据概览接口（单站三日总览 + 单站近7天趋势）
        @param get.site_name 站点名（必填，校验：仅允许字母、数字、点、短横线、下划线）
        @return public.return_data(True, data)
        """
        public.set_module_logs('site_total', 'get_site_overview', 1)
        site_name = getattr(get, 'site_name', None)
        if not site_name:
            return public.returnMsg(False, '站点名非法或缺失')
        today, yesterday, day_before = self._get_three_days()
        # 三日总览（单站）
        today_total = self._get_site_total_for_date(site_name, today)
        yesterday_total = self._get_site_total_for_date(site_name, yesterday)
        day_before_total = self._get_site_total_for_date(site_name, day_before)
        compare = self._compute_compare(today_total, yesterday_total)
        overview_three_days = {
            'today': self._format_daily_stat(today_total, include_compare=compare),
            'yesterday': self._format_daily_stat(yesterday_total),
            'day_before': self._format_daily_stat(day_before_total)
        }
        # 近7天趋势（单站）
        trend_points = self._build_trend_7days_site(site_name)

        # 检查config配置是否需要更新
        self._check_config()
        
        data = {
            'site': site_name,
            'date_range': {
                'today': today,
                'yesterday': yesterday,
                'day_before': day_before
            },
            'overview_three_days': overview_three_days,
            'trend_7days': {
                'site': site_name,
                'timeframe': 'last_7_days',
                'points': trend_points
            }
        }
        return public.return_data(True, data)

    def receive_products(self, get):
        """
        @name 领取产品接口
        @param get.detail_id 活动详情ID（必填）
        @return public.return_data(True, data)
        """
        try:
            u = public.get_user_info()
            if not isinstance(u, dict):
                return public.returnMsg(False, '用户信息获取失败')
            serverid = u.get('serverid')
            access_key = u.get('access_key')
            uid = u.get('uid')
            if not serverid or not access_key or uid is None:
                return public.returnMsg(False, '参数缺失')
            detail_id = None
            try:
                detail_id = getattr(get, 'detail_id', None)
            except Exception:
                detail_id = None
            if detail_id is None and isinstance(get, dict):
                detail_id = get.get('detail_id')
            if detail_id is None:
                return public.returnMsg(False, '缺少detail_id')
            mac = public.get_mac_address()
            payload = {
                'serverid': serverid,
                'access_key': access_key,
                'uid': uid,
                'detail_id': detail_id,
                'mac': mac
            }
            url = 'https://www.bt.cn/newapi/activity/panelapi/receive_products'
            res = public.httpPost(url, payload)
            if not res:
                return public.returnMsg(False, '接口请求失败')
            try:
                obj = json.loads(res)
            except Exception:
                return public.returnMsg(False, '响应解析失败')
            status = obj.get('status')
            success = bool(status)
            # 刷新软件列表状态,确保最新软件列表信息获取
            public.flush_plugin_list()
            return public.returnMsg(success, obj)
        except Exception:
            return public.returnMsg(False, '领取失败')
    
    # ------------------------ 内部工具方法 ------------------------
    def _get_three_days(self):
        """返回今日、昨日、前日的日期字符串(YYYY-MM-DD)"""
        now = datetime.now()
        today = now.strftime('%Y-%m-%d')
        yesterday = (now - timedelta(days=1)).strftime('%Y-%m-%d')
        day_before = (now - timedelta(days=2)).strftime('%Y-%m-%d')
        return today, yesterday, day_before

    def _get_7day_dates(self):
        """返回近7天日期列表(包含今日), 每项格式YYYY-MM-DD"""
        base = datetime.now()
        dates = []
        for i in range(6, -1, -1):
            dates.append((base - timedelta(days=i)).strftime('%Y-%m-%d'))
        return dates

    def _get_7day_range(self):
        """返回近7天范围的字典: {start_date, end_date}"""
        base = datetime.now()
        start_date = (base - timedelta(days=6)).strftime('%Y-%m-%d')
        end_date = base.strftime('%Y-%m-%d')
        return {'start_date': start_date, 'end_date': end_date}

    def _validate_site_name(self, site):
        """校验站点名，仅允许字母、数字、点、短横线、下划线，长度<=128"""
        if not isinstance(site, str):
            return False
        if len(site) == 0 or len(site) > 128:
            return False
        return re.match(r'^[A-Za-z0-9._-]+$', site) is not None

    def _safe_read_json(self, path):
        """安全读取JSON文件，失败返回None"""
        try:
            if not os.path.exists(path):
                return None
            body = public.readFile(path)
            if not body:
                return None
            return json.loads(body)
        except Exception:
            return None

    def _ensure_metrics(self, data):
        """规范化指标字典，缺失字段按0处理，类型转为int"""
        keys = ['traffic', 'requests', 'ip', 'uv', 'pv']
        result = {}
        for k in keys:
            try:
                v = int((data or {}).get(k, 0)) if isinstance(data, dict) else 0
            except Exception:
                v = 0
            result[k] = v
        return result

    def _humanize_bytes(self, n):
        """按1024换算返回人类可读格式"""
        try:
            n = int(n)
        except Exception:
            n = 0
        units = ['B', 'KB', 'MB', 'GB', 'TB']
        size = float(n)
        idx = 0
        while size >= 1024 and idx < len(units) - 1:
            size /= 1024.0
            idx += 1
        # 保留两位小数
        if idx == 0:
            return f"{int(size)} {units[idx]}"
        return f"{round(size, 2)} {units[idx]}"

    def _format_daily_stat(self, metrics, include_compare=None):
        """将指标格式化为返回结构，include_compare用于today对比昨日"""
        m = self._ensure_metrics(metrics or {})
        formatted = {
            'traffic_bytes': m['traffic'],
            'traffic_human': self._humanize_bytes(m['traffic']),
            'req_count': m['requests'],
            'ip_count': m['ip'],
            'uv': m['uv'],
            'pv': m['pv']
        }
        if include_compare is not None:
            formatted['compare_vs_yesterday'] = include_compare
        return formatted

    def _compute_compare(self, today_metrics, yesterday_metrics):
        """计算与昨日的对比，返回各指标的abs/pct/trend，pct保留两位小数"""
        t = self._ensure_metrics(today_metrics or {})
        y = self._ensure_metrics(yesterday_metrics or {})
        result = {}
        for src_k, out_k in [('traffic','traffic'), ('requests','req_count'), ('ip','ip_count'), ('uv','uv'), ('pv','pv')]:
            abs_change = t[src_k] - y[src_k]
            pct = 0.0
            if y[src_k] > 0:
                pct = round((abs_change / y[src_k]) * 100.0, 2)
            else:
                # 昨日为0，无法计算百分比，按规则返回0
                pct = 0.0
            trend = 'flat'
            if abs_change > 0:
                trend = 'up'
            elif abs_change < 0:
                trend = 'down'
            result[out_k] = {'abs': abs_change, 'pct': pct, 'trend': trend}
        return result

    def _monitor_enabled(self):
        """检测是否启用监控报表数据源。存在 /www/server/panel/plugin/monitor 且配置中的 data_save_path 可用时返回 True"""
        try:
            if not os.path.exists('/www/server/panel/plugin/monitor'):
                return False
            db_path = self._get_monitor_db_path()
            return bool(db_path and os.path.isdir(db_path))
        except Exception as e:
            return False

    def _get_monitor_db_path(self):
        """读取监控报表配置，获取 data_save_path。结果缓存到实例属性以减少IO"""
        try:
            if hasattr(self, '_monitor_db_path') and self._monitor_db_path:
                return self._monitor_db_path
            conf_file = '/www/server/panel/plugin/monitor/monitor/config/config.json'
            conf_data = None
            try:
                conf_str = public.readFile(conf_file)
                conf_data = json.loads(conf_str) if conf_str else None
            except Exception:
                conf_data = None
            db_path = None
            if isinstance(conf_data, dict):
                db_path = conf_data.get('data_save_path')
            self._monitor_db_path = db_path
            return db_path
        except Exception:
            return None

    def _list_sites_monitor(self):
        """从监控报表数据目录枚举站点子目录（仅合法站点名且存在 request_total.db）"""
        sites = []
        try:
            base = self._get_monitor_db_path()
            if not base or not os.path.isdir(base):
                return sites
            for name in os.listdir(base):
                full = os.path.join(base, name)
                db_file = os.path.join(full, 'request_total.db')
                if os.path.isdir(full) and self._validate_site_name(name) and os.path.isfile(db_file):
                    sites.append(name)
        except Exception:
            pass
        return sites

    def _read_site_day_from_monitor(self, site, date_str):
        """从监控报表 request_total.db 读取单站某日指标，异常或缺失返回0集"""
        result = {'traffic': 0, 'requests': 0, 'ip': 0, 'uv': 0, 'pv': 0}
        try:
            base = self._get_monitor_db_path()
            if not base:
                return result
            db_file = os.path.join(base, site, 'request_total.db')
            if not os.path.isfile(db_file):
                return result
            # 日期转换为YYYYMMDD
            ymd = date_str.replace('-', '')
            ts = db.Sql()
            ts._Sql__DB_FILE = db_file
            fields = 'SUM(sent_bytes) as traffic, SUM(uv_number) as uv, SUM(ip_number) as ip, SUM(pv_number) as pv, SUM(request) as requests'
            row = ts.table('request_total').where("date=?", (ymd,)).field(fields).find()
            ts.close()
            if isinstance(row, dict) and row:
                for k in result.keys():
                    try:
                        result[k] = int(row.get(k, 0) or 0)
                    except Exception:
                        result[k] = 0
        except Exception:
            pass
        return result

    def _ensure_summary_dir(self):
        """确保SUMMARY_DIR存在"""
        try:
            if not os.path.isdir(self.SUMMARY_DIR):
                os.makedirs(self.SUMMARY_DIR, exist_ok=True)
        except Exception:
            pass

    def _safe_write_json_atomic(self, path, data):
        """原子写入JSON：先写临时文件，再替换为目标文件"""
        try:
             dir_name = os.path.dirname(path)
             try:
                 os.makedirs(dir_name, exist_ok=True)
             except Exception:
                 pass
             base_name = os.path.basename(path)
             tmp_path = os.path.join(dir_name, '.' + base_name + '.tmp')
             with open(tmp_path, 'w', encoding='utf-8') as f:
                 json.dump(data, f, ensure_ascii=False)
             os.replace(tmp_path, path)
             return True
        except Exception:
            try:
                # 回滚临时文件
                if 'tmp_path' in locals() and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass
            return False

    def _list_sites(self):
        """枚举站点列表：优先使用监控报表数据源，否则遍历TOTAL_DIR下的目录"""
        try:
            if self._monitor_enabled():
                return self._list_sites_monitor()
        except Exception:
            # 监控数据源异常时回退旧方式
            pass
        sites = []
        base = self.TOTAL_DIR
        try:
            if not os.path.exists(base):
                return sites
            for name in os.listdir(base):
                full = os.path.join(base, name)
                if os.path.isdir(full) and self._validate_site_name(name):
                    sites.append(name)
        except Exception:
            pass
        return sites

    def _site_day_path(self, site, date_str):
        """拼接单站点某日JSON路径：/total/{site}/{YYYY-MM-DD}.json"""
        return os.path.join(self.TOTAL_DIR, site, f"{date_str}.json")

    def _load_summary_for_date(self, date_str):
        """读取全站汇总持久文件 /summary/{YYYY-MM-DD}.json，返回指标或None"""
        path = os.path.join(self.SUMMARY_DIR, f"{date_str}.json")
        data = self._safe_read_json(path)
        if data is None:
            return None
        return self._ensure_metrics(data)

    def _aggregate_all_sites_for_date(self, date_str):
        """聚合全站在某日的指标（遍历站点逐一读取），缺失文件按0处理"""
        total = {'traffic': 0, 'requests': 0, 'ip': 0, 'uv': 0, 'pv': 0}
        for site in self._list_sites():
            m = self._aggregate_site_for_date(site, date_str)
            for k in total.keys():
                total[k] += m.get(k, 0)
        return total

    def _aggregate_site_for_date(self, site, date_str):
        """读取单站点某日指标（优先监控报表DB，失败回退旧文件），缺失或异常返回全部0"""
        # 优先从监控报表数据源读取
        try:
            if self._monitor_enabled():
                return self._ensure_metrics(self._read_site_day_from_monitor(site, date_str))
        except Exception:
            # 数据源异常时回退旧方式
            pass
        # 旧文件方式
        path = self._site_day_path(site, date_str)
        data = self._safe_read_json(path)
        m = self._ensure_metrics(data or {})
        return m

    def _get_all_sites_total_for_date(self, date_str):
        """优先读取summary；不存在则回退聚合原始站点文件"""
        summary = self._load_summary_for_date(date_str)
        if summary is not None:
            return summary
        return self._aggregate_all_sites_for_date(date_str)

    def _get_site_total_for_date(self, site, date_str):
        """读取单站某日指标（直接读取原始文件）"""
        return self._aggregate_site_for_date(site, date_str)

    def _build_trend_7days_all(self):
        """构建全站近7天趋势points数组（历史6天缺失则计算并写入缓存，今日实时不写缓存）"""
        points = []
        today = datetime.now().strftime('%Y-%m-%d')
        for d in self._get_7day_dates():
            if d == today:
                # 今日实时统计，跳过summary缓存
                m = self._aggregate_all_sites_for_date(d)
            else:
                # 历史天优先读取summary，缺失则实时计算并写入缓存
                summary = self._load_summary_for_date(d)
                if summary is None:
                    m = self._aggregate_all_sites_for_date(d)
                    # 写入SUMMARY_DIR/{YYYY-MM-DD}.json
                    try:
                        self._safe_write_json_atomic(os.path.join(self.SUMMARY_DIR, f"{d}.json"), self._ensure_metrics(m))
                    except Exception:
                        pass
                else:
                    m = summary
            points.append({
                'date': d,
                'traffic_bytes': m['traffic'],
                'traffic_human': self._humanize_bytes(m['traffic']),
                'req_count': m['requests'],
                'ip_count': m['ip'],
                'uv': m['uv'],
                'pv': m['pv']
            })
        return points

    def _build_trend_7days_site(self, site):
        """构建单站近7天趋势points数组（历史天缺失则计算并写入 /total/{site}/{YYYY-MM-DD}.json；今日实时不写缓存）"""
        points = []
        today = datetime.now().strftime('%Y-%m-%d')
        for d in self._get_7day_dates():
            if d == today:
                m = self._aggregate_site_for_date(site, d)
            else:
                path = self._site_day_path(site, d)
                data = self._safe_read_json(path)
                if data is None:
                    m = self._aggregate_site_for_date(site, d)
                    try:
                        self._safe_write_json_atomic(path, self._ensure_metrics(m))
                    except Exception:
                        pass
                else:
                    m = self._ensure_metrics(data)
            points.append({
                'date': d,
                'traffic_bytes': m['traffic'],
                'traffic_human': self._humanize_bytes(m['traffic']),
                'req_count': m['requests'],
                'ip_count': m['ip'],
                'uv': m['uv'],
                'pv': m['pv']
            })
        return points

    def _get_top_sites_for_date(self, date_str, metric='pv', order='asc', limit=5):
        """计算指定日期的站点当天排行"""
        if metric not in ['traffic', 'req_count', 'ip_count', 'uv', 'pv']:
            metric = 'pv'
        if order not in ['asc', 'desc']:
            order = 'asc'
        result = []
        for site in self._list_sites():
            m = self._aggregate_site_for_date(site, date_str)
            result.append({
                'site': site,
                'traffic_bytes': m['traffic'],
                'traffic_human': self._humanize_bytes(m['traffic']),
                'req_count': m['requests'],
                'ip_count': m['ip'],
                'uv': m['uv'],
                'pv': m['pv']
            })
        # 映射排序字段
        metric_alias = {'traffic': 'traffic_bytes', 'req_count': 'req_count', 'ip_count': 'ip_count', 'uv': 'uv', 'pv': 'pv'}
        sort_key = metric_alias.get(metric, 'pv')
        reverse = (order == 'desc')
        result.sort(key=lambda x: int(x.get(sort_key, 0)), reverse=reverse)
        if isinstance(limit, int):
            if limit <= 0:
                limit = 5
            if limit > 50:
                limit = 50
        else:
            limit = 5
        return result[:limit]

    def _get_top_sites_last_7_days(self, metric='pv', order='asc', limit=5):
        """计算近7天累计的站点排行（固定metric=pv，order=asc）"""
        if metric not in ['traffic', 'req_count', 'ip_count', 'uv', 'pv']:
            metric = 'pv'
        if order not in ['asc', 'desc']:
            order = 'asc'
        dates = self._get_7day_dates()
        result = []
        for site in self._list_sites():
            agg = {'traffic': 0, 'requests': 0, 'ip': 0, 'uv': 0, 'pv': 0}
            for d in dates:
                m = self._aggregate_site_for_date(site, d)
                for k in agg.keys():
                    agg[k] += m.get(k, 0)
            result.append({
                'site': site,
                'traffic_bytes': agg['traffic'],
                'traffic_human': self._humanize_bytes(agg['traffic']),
                'req_count': agg['requests'],
                'ip_count': agg['ip'],
                'uv': agg['uv'],
                'pv': agg['pv']
            })
        # 排序字段映射
        metric_alias = {'traffic': 'traffic_bytes', 'req_count': 'req_count', 'ip_count': 'ip_count', 'uv': 'uv', 'pv': 'pv'}
        sort_key = metric_alias.get(metric, 'pv')
        reverse = (order == 'desc')
        result.sort(key=lambda x: int(x.get(sort_key, 0)), reverse=reverse)
        if isinstance(limit, int):
            if limit <= 0:
                limit = 5
            if limit > 50:
                limit = 50
        else:
            limit = 5
        return result[:limit]

    def _get_rec_status(self):
        try:
            u = public.get_user_info()
            if not isinstance(u, dict):
                return False
            serverid = u.get('serverid')
            access_key = u.get('access_key')
            uid = u.get('uid')
            if not serverid or not access_key or uid is None:
                return False
            payload = {
                'serverid': serverid,
                'access_key': access_key,
                'uid': uid,
                'activity_id': 44
            }
            url = 'https://www.bt.cn/newapi/activity/panelapi/get_free_activity_info'
            res = public.httpPost(url, payload)
            if not res:
                return False
            try:
                obj = json.loads(res)
            except Exception:
                return False
            data = obj.get('data')
            if isinstance(data, dict):
                s = data.get('status')
                detail = data.get('detail')
                buy_status = None
                if isinstance(detail, list) and len(detail) > 0:
                    buy_status = detail[0].get('buy_status')
                elif isinstance(detail, dict):
                    buy_status = detail.get('buy_status')
                return (s == 1 or str(s) == '1') and (buy_status == 1 or str(buy_status) == '1')
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                s = item.get('status')
                detail = item.get('detail')
                buy_status = None
                if isinstance(detail, list) and len(detail) > 0:
                    buy_status = detail[0].get('buy_status')
                elif isinstance(detail, dict):
                    buy_status = detail.get('buy_status')
                return (s == 1 or str(s) == '1') and (buy_status == 1 or str(buy_status) == '1')
            return False
        except Exception:
            return False

    def _get_rec_status_detail(self):
        try:
            u = public.get_user_info()
            if not isinstance(u, dict):
                return False, None
            serverid = u.get('serverid')
            access_key = u.get('access_key')
            uid = u.get('uid')
            if not serverid or not access_key or uid is None:
                return False, None
            payload = {
                'serverid': serverid,
                'access_key': access_key,
                'uid': uid,
                'activity_id': 44
            }
            url = 'https://www.bt.cn/newapi/activity/panelapi/get_free_activity_info'
            res = public.httpPost(url, payload)
            if not res:
                return False, None
            try:
                obj = json.loads(res)
            except Exception:
                return False, None
            data = obj.get('data')
            detail_id = None
            if isinstance(data, dict):
                s = data.get('status')
                detail = data.get('detail')
                buy_status = None
                if isinstance(detail, list) and len(detail) > 0:
                    buy_status = detail[0].get('buy_status')
                    detail_id = detail[0].get('id')
                elif isinstance(detail, dict):
                    buy_status = detail.get('buy_status')
                    detail_id = detail.get('id')
                return (s == 1 or str(s) == '1') and (buy_status == 1 or str(buy_status) == '1'), detail_id
            if isinstance(data, list) and len(data) > 0:
                item = data[0]
                s = item.get('status')
                detail = item.get('detail')
                buy_status = None
                if isinstance(detail, list) and len(detail) > 0:
                    buy_status = detail[0].get('buy_status')
                    detail_id = detail[0].get('id')
                elif isinstance(detail, dict):
                    buy_status = detail.get('buy_status')
                    detail_id = detail.get('id')
                return (s == 1 or str(s) == '1') and (buy_status == 1 or str(buy_status) == '1'), detail_id
            return False, None
        except Exception:
            return False, None

    def _check_config(self):
        """
        @description 检查config配置是否需要更新,修复统计数量不显示问题
        @return None
        """
        header_file = "{}/data/table_header_conf.json".format(public.get_panel_path())
        try:
            if os.path.exists(header_file):
                raw = public.readFile(header_file)
                file_data = json.loads(raw)
                if isinstance(file_data, dict):
                    updated = False
                    val = file_data.get("phpTableColumn", '')
                    if val:
                        try:
                            cols = json.loads(val) or []
                            has_day = False
                            for c in cols:
                                if c.get("label") == "日流量":
                                    has_day = True
                                    if c.get("isCustom") is not True:
                                        c["isCustom"] = True
                                    if c.get("isLtd") is not True:
                                        c["isLtd"] = True
                                    break
                            if not has_day:
                                cols.append({"label": "日流量", "width": 80, "isCustom": True, "isLtd": True})
                            file_data["phpTableColumn"] = json.dumps(cols)
                            updated = True
                        except Exception:
                            pass
                    if updated:
                        public.writeFile(header_file, json.dumps(file_data))
        except Exception:
            pass
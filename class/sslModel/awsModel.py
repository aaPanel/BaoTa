# coding: utf-8
# -------------------------------------------------------------------
# 宝塔Linux面板
# -------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
# -------------------------------------------------------------------
# Author: cjxin <cjxin@bt.cn>
# -------------------------------------------------------------------
# AWS Route53 DNS解析接口
# ------------------------------

import hashlib
import hmac
import json
import time
from datetime import datetime
from urllib.parse import quote, urlparse

import public
import requests
from sslModel.base import sslBase


class main(sslBase):
    dns_provider_name = "aws"
    _type = 0

    def __init__(self):
        super().__init__()
        self.endpoint = "https://route53.amazonaws.com"
        self.api_version = "2013-04-01"

    def __init_data(self, data):
        self.access_key_id = data["AccessKey"]
        self.secret_access_key = data["SecretKey"]
        self.region = data.get("region", "us-east-1")

    def _sign(self, key, msg):
        """HMAC SHA256 签名"""
        return hmac.new(key, msg.encode('utf-8'), hashlib.sha256).digest()

    def _get_signature_key(self, key, date_stamp, region_name, service_name):
        """生成AWS签名密钥"""
        k_date = self._sign(('AWS4' + key).encode('utf-8'), date_stamp)
        k_region = self._sign(k_date, region_name)
        k_service = self._sign(k_region, service_name)
        k_signing = self._sign(k_service, 'aws4_request')
        return k_signing

    def _make_request(self, dns_id, method, path, body="", query_params=None):
        """构造AWS签名请求"""
        self.__init_data(self.get_dns_data(None)[dns_id])

        service = 'route53'
        host = 'route53.amazonaws.com'

        # 时间戳
        t = datetime.utcnow()
        amz_date = t.strftime('%Y%m%dT%H%M%SZ')
        date_stamp = t.strftime('%Y%m%d')

        # 构造规范请求
        canonical_uri = path
        canonical_querystring = ""
        if query_params:
            canonical_querystring = '&'.join(
                f'{quote(k, safe="")}={quote(str(v), safe="")}' for k, v in sorted(query_params.items())
            )

        payload_hash = hashlib.sha256(body.encode('utf-8')).hexdigest()

        # 规范头部
        canonical_headers = f'host:{host}\nx-amz-date:{amz_date}\n'
        signed_headers = 'host;x-amz-date'

        canonical_request = '\n'.join([
            method,
            canonical_uri,
            canonical_querystring,
            canonical_headers,
            signed_headers,
            payload_hash
        ])

        # 待签名字符串
        credential_scope = f'{date_stamp}/{self.region}/{service}/aws4_request'
        string_to_sign = '\n'.join([
            'AWS4-HMAC-SHA256',
            amz_date,
            credential_scope,
            hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
        ])

        # 计算签名
        signing_key = self._get_signature_key(self.secret_access_key, date_stamp, self.region, service)
        signature = hmac.new(signing_key, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()

        # 授权头部
        authorization_header = (
            f'AWS4-HMAC-SHA256 Credential={self.access_key_id}/{credential_scope}, '
            f'SignedHeaders={signed_headers}, Signature={signature}'
        )

        headers = {
            'X-Amz-Date': amz_date,
            'Authorization': authorization_header,
            'Content-Type': 'application/xml'
        }

        url = f'{self.endpoint}{path}'
        if canonical_querystring:
            url += f'?{canonical_querystring}'

        response = requests.request(method, url, headers=headers, data=body, timeout=60)
        return response

    def _get_hosted_zone_id(self, dns_id, domain_name):
        """获取域名对应的Hosted Zone ID"""
        response = self._make_request(dns_id, 'GET', f'/{self.api_version}/hostedzone')
        if response.status_code != 200:
            return None

        # 解析XML响应
        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)

        # 定义命名空间
        ns = {'aws': 'https://route53.amazonaws.com/doc/2013-04-01/'}

        for zone in root.findall('.//aws:HostedZone', ns):
            name = zone.find('aws:Name', ns).text.rstrip('.')
            if name == domain_name:
                zone_id = zone.find('aws:Id', ns).text
                return zone_id.split('/')[-1]  # 返回不带 /hostedzone/ 前缀的ID

        return None

    def _get_all_hosted_zones(self, dns_id):
        """获取所有Hosted Zone"""
        response = self._make_request(dns_id, 'GET', f'/{self.api_version}/hostedzone')
        if response.status_code != 200:
            return {}

        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        ns = {'aws': 'https://route53.amazonaws.com/doc/2013-04-01/'}

        zones = {}
        for zone in root.findall('.//aws:HostedZone', ns):
            name = zone.find('aws:Name', ns).text.rstrip('.')
            zone_id = zone.find('aws:Id', ns).text.split('/')[-1]
            zones[name] = zone_id

        return zones

    def _parse_record_values(self, domain_dns_value, record_type, mx=None):
        """解析记录值，支持单值字符串或JSON数组"""
        values = []

        # 尝试解析为JSON数组
        try:
            parsed = json.loads(domain_dns_value)
            if isinstance(parsed, list):
                values = parsed
            else:
                values = [domain_dns_value]
        except (json.JSONDecodeError, TypeError):
            values = [domain_dns_value]

        # TXT记录需要加引号
        if record_type == 'TXT':
            values = [f'"{v}"' if not v.startswith('"') else v for v in values]

        # MX记录处理：优先级 + 邮件服务器
        elif record_type == 'MX':
            processed_values = []
            for v in values:
                # 检查值中是否已包含MX优先级（格式: "10 mail.example.com"）
                parts = str(v).strip().split(None, 1)
                if len(parts) == 2 and parts[0].isdigit():
                    # 已包含MX值，直接使用
                    processed_values.append(f'{parts[0]} {parts[1]}')
                elif mx is not None:
                    # 使用传入的mx参数
                    processed_values.append(f'{mx} {v}')
                else:
                    # 默认MX优先级为10
                    processed_values.append(f'10 {v}')
            values = processed_values

        return values

    def _build_resource_records_xml(self, values):
        """构建多个ResourceRecord的XML"""
        xml_parts = []
        for value in values:
            # XML转义特殊字符
            escaped_value = str(value).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            xml_parts.append(f'''                        <ResourceRecord>
                            <Value>{escaped_value}</Value>
                        </ResourceRecord>''')
        return '\n'.join(xml_parts)

    def create_dns_record(self, get):
        domain_name = get.domain_name
        domain_dns_value = get.domain_dns_value
        record_type = 'TXT'
        if 'record_type' in get:
            record_type = get.record_type
        ttl = 300
        if 'ttl' in get:
            ttl = int(get.ttl)

        # MX类型获取优先级
        mx = None
        if record_type == 'MX':
            if 'mx' in get and get.mx:
                mx = int(get.mx)

        # 是否追加模式
        is_append = get.get('is_append', False)
        if isinstance(is_append, str):
            is_append = is_append.lower() in ('true', '1', 'yes')

        root_domain, sub_domain, _ = self.extract_zone(domain_name)
        if sub_domain == "@":
            sub_domain = ""

        try:
            zone_id = self._get_hosted_zone_id(get.dns_id, root_domain)
            if not zone_id:
                return public.returnMsg(False, '此域名不在AWS Route53账号下，请检查DNS接口配置')

            # 构造记录名称
            record_name = f'{sub_domain}.{root_domain}.' if sub_domain else f'{root_domain}.'

            # 解析记录值（支持JSON数组和MX优先级）
            new_values = self._parse_record_values(domain_dns_value, record_type, mx)

            # 追加模式：检查记录是否存在
            action = 'CREATE'
            if is_append:
                record_info = self._get_record_info(get.dns_id, zone_id, record_name, record_type)
                if record_info:
                    # 记录已存在，合并值
                    existing_values = record_info.get('values', [])
                    if not existing_values:
                        existing_values = [record_info.get('value', '')] if record_info.get('value') else []

                    # 合并新旧值（去重）
                    for val in new_values:
                        if val not in existing_values:
                            existing_values.append(val)
                    new_values = existing_values
                    ttl = record_info.get('ttl', ttl)
                    action = 'UPSERT'

            # 构建ResourceRecords XML
            resource_records_xml = self._build_resource_records_xml(new_values)

            # 构造变更XML
            change_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<ChangeResourceRecordSetsRequest xmlns="https://route53.amazonaws.com/doc/2013-04-01/">
    <ChangeBatch>
        <Changes>
            <Change>
                <Action>{action}</Action>
                <ResourceRecordSet>
                    <Name>{record_name}</Name>
                    <Type>{record_type}</Type>
                    <TTL>{ttl}</TTL>
                    <ResourceRecords>
{resource_records_xml}
                    </ResourceRecords>
                </ResourceRecordSet>
            </Change>
        </Changes>
    </ChangeBatch>
</ChangeResourceRecordSetsRequest>'''

            path = f'/{self.api_version}/hostedzone/{zone_id}/rrset'
            response = self._make_request(get.dns_id, 'POST', path, body=change_xml)

            if response.status_code == 200 or response.status_code == 201:
                return public.returnMsg(True, '添加成功')
            else:
                return public.returnMsg(False, self.get_error(response.content))
        except Exception as e:
            return public.returnMsg(False, self.get_error(str(e)))

    def delete_dns_record(self, get):
        domain_name = get.domain_name
        record_type = get.record_type if 'record_type' in get else 'TXT'
        record_value = get.domain_dns_value if 'domain_dns_value' in get else ''

        root_domain, sub_domain, _ = self.extract_zone(domain_name)
        if sub_domain == "@":
            sub_domain = ""

        try:
            zone_id = self._get_hosted_zone_id(get.dns_id, root_domain)
            if not zone_id:
                return public.returnMsg(False, '此域名不在AWS Route53账号下')

            record_name = f'{sub_domain}.{root_domain}.' if sub_domain else f'{root_domain}.'

            # 获取记录详细信息用于删除
            record_info = self._get_record_info(get.dns_id, zone_id, record_name, record_type)
            if not record_info:
                return public.returnMsg(False, '解析记录不存在')

            ttl = record_info.get('ttl', 300)

            # 如果传入了值，使用传入的值；否则使用记录中的所有值
            if record_value:
                # 删除时mx参数不影响，因为值中应该已包含优先级
                values = self._parse_record_values(record_value, record_type)
            else:
                values = record_info.get('values', [])
                if not values:
                    values = [record_info.get('value', '')]

            # 构建ResourceRecords XML
            resource_records_xml = self._build_resource_records_xml(values)

            # 构造删除XML
            delete_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<ChangeResourceRecordSetsRequest xmlns="https://route53.amazonaws.com/doc/2013-04-01/">
    <ChangeBatch>
        <Changes>
            <Change>
                <Action>DELETE</Action>
                <ResourceRecordSet>
                    <Name>{record_name}</Name>
                    <Type>{record_type}</Type>
                    <TTL>{ttl}</TTL>
                    <ResourceRecords>
{resource_records_xml}
                    </ResourceRecords>
                </ResourceRecordSet>
            </Change>
        </Changes>
    </ChangeBatch>
</ChangeResourceRecordSetsRequest>'''

            path = f'/{self.api_version}/hostedzone/{zone_id}/rrset'
            response = self._make_request(get.dns_id, 'POST', path, body=delete_xml)

            if response.status_code == 200:
                return public.returnMsg(True, '删除成功')
            else:
                return public.returnMsg(False, self.get_error(response.content))
        except Exception as e:
            return public.returnMsg(False, self.get_error(str(e)))

    def _get_record_info(self, dns_id, zone_id, record_name, record_type):
        """获取单个记录信息（包含所有值）"""
        path = f'/{self.api_version}/hostedzone/{zone_id}/rrset'
        response = self._make_request(dns_id, 'GET', path)

        if response.status_code != 200:
            return None

        import xml.etree.ElementTree as ET
        root = ET.fromstring(response.content)
        ns = {'aws': 'https://route53.amazonaws.com/doc/2013-04-01/'}

        for record in root.findall('.//aws:ResourceRecordSet', ns):
            name = record.find('aws:Name', ns).text
            rtype = record.find('aws:Type', ns).text
            if name == record_name and rtype == record_type:
                ttl_elem = record.find('aws:TTL', ns)
                ttl = int(ttl_elem.text) if ttl_elem is not None else 300

                # 获取所有值
                values = []
                for value_elem in record.findall('.//aws:Value', ns):
                    values.append(value_elem.text)

                return {'ttl': ttl, 'values': values, 'value': values[0] if values else ''}

        return None

    def get_dns_record(self, get):
        domain_name = get.domain_name
        root_domain, sub_domain, _ = self.extract_zone(domain_name)
        data = {}

        try:
            zone_id = self._get_hosted_zone_id(get.dns_id, root_domain)
            if not zone_id:
                return data

            path = f'/{self.api_version}/hostedzone/{zone_id}/rrset'
            response = self._make_request(get.dns_id, 'GET', path)

            if response.status_code != 200:
                return data
            public.print_log(response.content)

            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            ns = {'aws': 'https://route53.amazonaws.com/doc/2013-04-01/'}
            public.print_log(root)

            record_list = []
            search = get.get('search', '')

            for record in root.findall('.//aws:ResourceRecordSet', ns):
                name = record.find('aws:Name', ns).text.rstrip('.')
                rtype = record.find('aws:Type', ns).text

                # 搜索过滤
                if search and search.lower() not in name.lower():
                    continue

                ttl_elem = record.find('aws:TTL', ns)
                ttl = int(ttl_elem.text) if ttl_elem is not None else 300

                # 获取所有值
                values = []
                mx_priority = 0
                for value_elem in record.findall('.//aws:Value', ns):
                    val = value_elem.text
                    if rtype == 'TXT':
                        val = val.strip('"')
                    elif rtype == 'MX':
                        # MX格式: "10 mail.example.com"，解析出优先级但保留原值
                        parts = val.split(None, 1)
                        if len(parts) == 2 and parts[0].isdigit():
                            mx_priority = int(parts[0])
                    values.append(val)

                record_list.append({
                    'RecordId': f'{name}|{rtype}',
                    'name': name,
                    'value': values,
                    'line': '默认',
                    'ttl': ttl,
                    'type': rtype,
                    'status': '启用',
                    'mx': mx_priority,
                    'updated_on': '',
                    'remark': ''
                })

            # 分页处理
            limit = int(get.get('limit', 100))
            page = int(get.get('p', 1))
            start_idx = (page - 1) * limit
            end_idx = start_idx + limit

            data['list'] = record_list[start_idx:end_idx]
            data['info'] = {'record_total': len(record_list)}

        except Exception as e:
            pass

        self.set_record_data({root_domain: data})
        return data

    def update_dns_record(self, get):
        """使用UPSERT更新记录，不存在则创建"""
        domain_name = get.domain_name
        domain_dns_value = get.domain_dns_value
        record_type = get.record_type
        ttl = 300
        if 'ttl' in get:
            ttl = int(get.ttl)

        # MX类型获取优先级
        mx = None
        if record_type == 'MX':
            if 'mx' in get and get.mx:
                mx = int(get.mx)

        root_domain, sub_domain, _ = self.extract_zone(domain_name)
        if sub_domain == "@":
            sub_domain = ""

        try:
            zone_id = self._get_hosted_zone_id(get.dns_id, root_domain)
            if not zone_id:
                return public.returnMsg(False, '此域名不在AWS Route53账号下')

            # 构造记录名称
            record_name = f'{sub_domain}.{root_domain}.' if sub_domain else f'{root_domain}.'

            # 解析记录值（支持JSON数组和MX优先级）
            values = self._parse_record_values(domain_dns_value, record_type, mx)

            # 构建ResourceRecords XML
            resource_records_xml = self._build_resource_records_xml(values)

            # 使用UPSERT操作：存在则更新，不存在则创建
            change_xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<ChangeResourceRecordSetsRequest xmlns="https://route53.amazonaws.com/doc/2013-04-01/">
    <ChangeBatch>
        <Changes>
            <Change>
                <Action>UPSERT</Action>
                <ResourceRecordSet>
                    <Name>{record_name}</Name>
                    <Type>{record_type}</Type>
                    <TTL>{ttl}</TTL>
                    <ResourceRecords>
{resource_records_xml}
                    </ResourceRecords>
                </ResourceRecordSet>
            </Change>
        </Changes>
    </ChangeBatch>
</ChangeResourceRecordSetsRequest>'''

            path = f'/{self.api_version}/hostedzone/{zone_id}/rrset'
            response = self._make_request(get.dns_id, 'POST', path, body=change_xml)

            if response.status_code == 200:
                return public.returnMsg(True, '修改成功')
            else:
                return public.returnMsg(False, self.get_error(response.content))
        except Exception as e:
            return public.returnMsg(False, self.get_error(str(e)))

    def set_dns_record_status(self, get):
        # AWS Route53 不支持直接启用/禁用记录，需要删除/重新创建
        return public.returnMsg(False, 'AWS Route53不支持设置解析记录状态，请使用删除/添加功能')

    def get_domain_list(self, get):
        try:
            path = f'/{self.api_version}/hostedzone'
            response = self._make_request(get.dns_id, 'GET', path)

            if response.status_code != 200:
                return public.returnMsg(False, self.get_error(response.content))

            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            ns = {'aws': 'https://route53.amazonaws.com/doc/2013-04-01/'}

            local_domain_list = [d['domain'] for d in public.M('ssl_domains').field('domain').select()]

            domain_list = []
            for zone in root.findall('.//aws:HostedZone', ns):
                name = zone.find('aws:Name', ns).text.rstrip('.')
                zone_id = zone.find('aws:Id', ns).text.split('/')[-1]
                record_count_elem = zone.find('aws:ResourceRecordSetCount', ns)
                record_count = int(record_count_elem.text) if record_count_elem is not None else 0

                domain_list.append({
                    'id': zone_id,
                    'name': name,
                    'remark': '',
                    'record_count': record_count,
                    'sync': 0 if name in local_domain_list else 1
                })

            return {'status': True, 'msg': '获取成功', 'data': domain_list}
        except Exception as e:
            return {'status': False, 'msg': self.get_error(str(e)), 'data': []}

    def get_error(self, error):
        """错误信息处理"""
        error_str = str(error)
        if isinstance(error, bytes):
            error_str = error.decode('utf-8')

        if 'InvalidClientTokenId' in error_str:
            return 'AWS Access Key 无效'
        elif 'SignatureDoesNotMatch' in error_str:
            return 'AWS Secret Key 无效'
        elif 'NoSuchHostedZone' in error_str:
            return 'Hosted Zone 不存在'
        elif 'InvalidChangeBatch' in error_str:
            if 'Tried to create resource record set' in error_str:
                return '解析记录已存在'
            elif 'Tried to delete resource record set' in error_str:
                return '解析记录不存在'
            return '记录变更失败'
        elif 'AccessDenied' in error_str:
            return '没有权限访问此资源'
        elif 'InvalidInput' in error_str:
            return '输入参数无效'
        else:
            # 尝试从XML中提取错误消息
            try:
                import xml.etree.ElementTree as ET
                root = ET.fromstring(error_str.encode('utf-8') if isinstance(error_str, str) else error_str)
                msg_elem = root.find('.//{https://route53.amazonaws.com/doc/2013-04-01/}Message')
                if msg_elem is not None:
                    return msg_elem.text
            except:
                pass
            return error_str
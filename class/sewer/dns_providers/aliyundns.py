import json

try:
    aliyun_dependencies = True
    from aliyunsdkcore import client
    from aliyunsdkalidns.request.v20150109 import DescribeDomainRecordsRequest
    from aliyunsdkalidns.request.v20150109 import AddDomainRecordRequest
    from aliyunsdkalidns.request.v20150109 import DeleteDomainRecordRequest
except ImportError:
    aliyun_dependencies = False

from . import common


class _ResponseForAliyun(object):
    """
    wrapper aliyun resp to the format sewer wanted.
    """

    def __init__(self, status_code=200, content=None, headers=None):
        self.status_code = status_code
        self.headers = headers or {}
        self.content = content or {}
        self.content = json.dumps(content)
        super(_ResponseForAliyun, self).__init__()

    def json(self):
        return json.loads(self.content)


class AliyunDns(common.BaseDns):
    def __init__(self, key, secret, endpoint="cn-beijing", debug=False):
        """
        aliyun dns client
        :param str key: access key
        :param str secret: access sceret
        :param str endpoint: endpoint
        :param bool debug: if debug?
        """
        super(AliyunDns, self).__init__()
        if not aliyun_dependencies:
            raise ImportError(
                """You need to install aliyunDns dependencies. run; pip3 install sewer[aliyun]"""
            )
        self._key = key
        self._secret = secret
        self._endpoint = endpoint
        self._debug = debug
        self.clt = client.AcsClient(self._key, self._secret, self._endpoint, debug=self._debug)

    def _send_reqeust(self, request):
        """
        send request to aliyun
        """
        request.set_accept_format("json")
        try:
            status, headers, result = self.clt.implementation_of_do_action(request)
            result = json.loads(result)
            if "Message" in result or "Code" in result:
                result["Success"] = False
        except Exception as exc:
            status, headers, result = 502, {}, '{"Success": false}'
            result = json.loads(result)

        return _ResponseForAliyun(status, result, headers)

    def query_recored_items(self, host, zone=None, tipe=None, page=1, psize=200):
        request = DescribeDomainRecordsRequest.DescribeDomainRecordsRequest()
        request.get_action_name()
        request.set_DomainName(host)
        request.set_PageNumber(page)
        request.set_PageSize(psize)
        if zone:
            request.set_RRKeyWord(zone)
        if tipe:
            request.set_TypeKeyWord(tipe)
        resp = self._send_reqeust(request)
        body = resp.json()
        return body

    def query_recored_id(self, root, zone, tipe="TXT"):
        """
        find recored
        :param str root: root host, like example.com
        :param str zone: sub zone, like menduo.example.com
        :param str tipe: record tipe, TXT, CNAME, IP. we use TXT
        :return str:
        """
        record_id = None
        recoreds = self.query_recored_items(root, zone, tipe=tipe)
        recored_list = recoreds.get("DomainRecords", {}).get("Record", [])
        recored_item_list = [i for i in recored_list if i["RR"] == zone]
        if len(recored_item_list):
            record_id = recored_item_list[0]["RecordId"]
        return record_id

    @staticmethod
    def extract_zone(domain_name):
        """
        extract domain to root, sub, acme_txt
        :param str domain_name: the value sewer client passed in, like *.menduo.example.com
        :return tuple: root, zone, acme_txt
        """
        # if we have been given a wildcard name, strip wildcard
        domain_name = domain_name.lstrip("*.")
        if domain_name.count(".") > 1:
            zone, middle, last = str(domain_name).rsplit(".", 2)
            root = ".".join([middle, last])
            acme_txt = "_acme-challenge.%s" % zone
        else:
            zone = ""
            root = domain_name
            acme_txt = "_acme-challenge"
        return root, zone, acme_txt

    def create_dns_record(self, domain_name, domain_dns_value):
        """
        create a dns record
        :param str domain_name: the value sewer client passed in, like *.menduo.example.com
        :param str domain_dns_value: the value sewer client passed in.
        :return _ResponseForAliyun:
        """
        root, _, acme_txt = self.extract_zone(domain_name)

        request = AddDomainRecordRequest.AddDomainRecordRequest()
        request.set_DomainName(root)
        request.set_TTL(600)
        request.set_RR(acme_txt)
        request.set_Type("TXT")
        request.set_Value(domain_dns_value)
        resp = self._send_reqeust(request)

        try:
            request = AddDomainRecordRequest.AddDomainRecordRequest()
            request.set_DomainName(root)
            request.set_TTL(600)
            request.set_RR('@')
            request.set_Type("CAA")
            request.set_Value('1 issue letsencrypt.org')
            resp = self._send_reqeust(request)
        except:
            pass

        try:
            tmp = acme_txt.split('.')
            if len(tmp) > 1:
                request = AddDomainRecordRequest.AddDomainRecordRequest()
                request.set_DomainName(root)
                request.set_TTL(600)
                request.set_RR(tmp[-1])
                request.set_Type("CAA")
                request.set_Value('1 issue letsencrypt.org')
                resp = self._send_reqeust(request)
        except:
            pass


        return resp

    def delete_dns_record(self, domain_name, domain_dns_value):
        """
        delete a txt record we created just now.
        :param str domain_name: the value sewer client passed in, like *.menduo.example.com
        :param str domain_dns_value: the value sewer client passed in. we do not use this.
        :return _ResponseForAliyun:
        :return:
        """
        root, _, acme_txt = self.extract_zone(domain_name)

        record_id = self.query_recored_id(root, acme_txt)
        if not record_id:
            return


        request = DeleteDomainRecordRequest.DeleteDomainRecordRequest()
        request.set_RecordId(record_id)
        resp = self._send_reqeust(request)

        try:
            record_id = self.query_recored_id(root, '@','CAA')
            if record_id:
                request = DeleteDomainRecordRequest.DeleteDomainRecordRequest()
                request.set_RecordId(record_id)
                self._send_reqeust(request)
        except:
            pass

        try:
            tmp = acme_txt.split('.')
            if len(tmp) > 1:
                record_id = self.query_recored_id(root, tmp[-1],'CAA')
                if record_id:
                    request = DeleteDomainRecordRequest.DeleteDomainRecordRequest()
                    request.set_RecordId(record_id)
                    self._send_reqeust(request)
        except:
            pass

        return resp

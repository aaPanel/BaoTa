# -*- coding: utf-8 -*-
from qiniu import http
from .config import KIRK_HOST


class QcosClient(object):
    """资源管理客户端

    使用应用密钥生成资源管理客户端，可以进一步：
    1、部署服务和容器，获得信息
    2、创建网络资源，获得信息

    属性：
        auth: 应用密钥对，QiniuMacAuth对象
        host: API host，在『内网模式』下使用时，auth=None，会自动使用 apiproxy 服务，只能管理当前容器所在的应用资源。

    接口：
        list_stacks()
        create_stack(args)
        delete_stack(stack)
        get_stack(stack)
        start_stack(stack)
        stop_stack(stack)

        list_services(stack)
        create_service(stack, args)
        get_service_inspect(stack, service)
        start_service(stack, service)
        stop_service(stack, service)
        update_service(stack, service, args)
        scale_service(stack, service, args)
        delete_service(stack, service)
        create_service_volume(stack, service, volume, args)
        extend_service_volume(stack, service, volume, args)
        delete_service_volume(stack, service, volume)

        list_containers(args)
        get_container_inspect(ip)
        start_container(ip)
        stop_container(ip)
        restart_container(ip)

        list_aps()
        create_ap(args)
        search_ap(mode, query)
        get_ap(apid)
        update_ap(apid, args)
        set_ap_port(apid, port, args)
        delete_ap(apid)
        publish_ap(apid, args)
        unpublish_ap(apid)
        get_ap_port_healthcheck(apid, port)
        set_ap_port_container(apid, port, args)
        disable_ap_port(apid, port)
        enable_ap_port(apid, port)
        get_ap_providers()
        get_web_proxy(backend)
    """

    def __init__(self, auth, host=None):
        self.auth = auth
        if auth is None:
            self.host = KIRK_HOST['APIPROXY']
        else:
            self.host = host

    def list_stacks(self):
        """获得服务组列表

        列出当前应用的所有服务组信息。

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回服务组列表[<stack1>, <stack2>, ...]，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks'.format(self.host)
        return self.__get(url)

    def create_stack(self, args):
        """创建服务组

        创建新一个指定名称的服务组，并创建其下的服务。

        Args:
            - args:  服务组描述，参考 http://kirk-docs.qiniu.com/apidocs/

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks'.format(self.host)
        return self.__post(url, args)

    def delete_stack(self, stack):
        """删除服务组

        删除服务组内所有服务并销毁服务组。

        Args:
            - stack:  服务所属的服务组名称

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks/{1}'.format(self.host, stack)
        return self.__delete(url)

    def get_stack(self, stack):
        """获取服务组

        查看服务组的属性信息。

        Args:
            - stack:  服务所属的服务组名称

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回stack信息，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks/{1}'.format(self.host, stack)
        return self.__get(url)

    def start_stack(self, stack):
        """启动服务组

        启动服务组中的所有停止状态的服务。

        Args:
            - stack:  服务所属的服务组名称

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks/{1}/start'.format(self.host, stack)
        return self.__post(url)

    def stop_stack(self, stack):
        """停止服务组

        停止服务组中所有运行状态的服务。

        Args:
            - stack:  服务所属的服务组名称

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks/{1}/stop'.format(self.host, stack)
        return self.__post(url)

    def list_services(self, stack):
        """获得服务列表

        列出指定名称的服务组内所有的服务, 返回一组详细的服务信息。

        Args:
            - stack:  服务所属的服务组名称

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result        成功返回服务信息列表[<ervice1>, <service2>, ...]，失败返回{"error": "<errMsg string>"}
            - ResponseInfo  请求的Response信息
        """
        url = '{0}/v3/stacks/{1}/services'.format(self.host, stack)
        return self.__get(url)

    def create_service(self, stack, args):
        """创建服务

        创建一个服务，平台会异步地按模板分配资源并部署所有容器。

        Args:
            - stack:  服务所属的服务组名称
            - args:   服务具体描述请求参数(json)，参考 http://kirk-docs.qiniu.com/apidocs/

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks/{1}/services'.format(self.host, stack)
        return self.__post(url, args)

    def delete_service(self, stack, service):
        """删除服务

        删除指定名称服务，并自动销毁服务已部署的所有容器和存储卷。

        Args:
            - stack:    服务所属的服务组名称
            - service:  服务名

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks/{1}/services/{2}'.format(self.host, stack, service)
        return self.__delete(url)

    def get_service_inspect(self, stack, service):
        """查看服务

        查看指定名称服务的属性。

        Args:
            - stack:    服务所属的服务组名称
            - service:  服务名

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回服务信息，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks/{1}/services/{2}/inspect'.format(self.host, stack, service)
        return self.__get(url)

    def start_service(self, stack, service):
        """启动服务

        启动指定名称服务的所有容器。

        Args:
            - stack:    服务所属的服务组名称
            - service:  服务名

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks/{1}/services/{2}/start'.format(self.host, stack, service)
        return self.__post(url)

    def stop_service(self, stack, service):
        """停止服务

        停止指定名称服务的所有容器。

        Args:
            - stack:    服务所属的服务组名称
            - service:  服务名

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks/{1}/services/{2}/stop'.format(self.host, stack, service)
        return self.__post(url)

    def update_service(self, stack, service, args):
        """更新服务

        更新指定名称服务的配置如容器镜像等参数，容器被重新部署后生效。
        如果指定manualUpdate参数，则需要额外调用 部署服务 接口并指定参数进行部署；处于人工升级模式的服务禁止执行其他修改操作。
        如果不指定manualUpdate参数，平台会自动完成部署。

        Args:
            - stack:    服务所属的服务组名称
            - service:  服务名
            - args:     服务具体描述请求参数(json)，参考 http://kirk-docs.qiniu.com/apidocs/

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks/{1}/services/{2}'.format(self.host, stack, service)
        return self.__post(url, args)

    def scale_service(self, stack, service, args):
        """扩容/缩容服务

        更新指定名称服务的配置如容器镜像等参数，容器被重新部署后生效。
        如果指定manualUpdate参数，则需要额外调用 部署服务 接口并指定参数进行部署；处于人工升级模式的服务禁止执行其他修改操作。
        如果不指定manualUpdate参数，平台会自动完成部署。

        Args:
            - stack:    服务所属的服务组名称
            - service:  服务名
            - args:     请求参数(json)，参考 http://kirk-docs.qiniu.com/apidocs/

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks/{1}/services/{2}/scale'.format(self.host, stack, service)
        return self.__post(url, args)

    def create_service_volume(self, stack, service, args):
        """创建存储卷

        为指定名称的服务增加存储卷资源，并挂载到部署的容器中。

        Args:
            - stack:    服务所属的服务组名称
            - service:  服务名
            - args:     请求参数(json)，参考 http://kirk-docs.qiniu.com/apidocs/

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks/{1}/services/{2}/volumes'.format(self.host, stack, service)
        return self.__post(url, args)

    def extend_service_volume(self, stack, service, volume, args):
        """扩容存储卷

        为指定名称的服务增加存储卷资源，并挂载到部署的容器中。

        Args:
            - stack:    服务所属的服务组名称
            - service:  服务名
            - volume:   存储卷名
            - args:     请求参数(json)，参考 http://kirk-docs.qiniu.com/apidocs/

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks/{1}/services/{2}/volumes/{3}/extend'.format(self.host, stack, service, volume)
        return self.__post(url, args)

    def delete_service_volume(self, stack, service, volume):
        """删除存储卷

        从部署的容器中移除挂载，并销毁指定服务下指定名称的存储卷, 并重新启动该容器。

        Args:
            - stack:    服务所属的服务组名称
            - service:  服务名
            - volume:   存储卷名

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/stacks/{1}/services/{2}/volumes/{3}'.format(self.host, stack, service, volume)
        return self.__delete(url)

    def list_containers(self, stack=None, service=None):
        """列出容器列表

        列出应用内所有部署的容器, 返回一组容器IP。

        Args:
            - stack:    要列出容器的服务组名(可不填，表示默认列出所有)
            - service:  要列出容器服务的服务名(可不填，表示默认列出所有)

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回容器的ip数组，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/containers'.format(self.host)
        params = {}
        if stack is not None:
            params['stack'] = stack
        if service is not None:
            params['service'] = service
        return self.__get(url, params or None)

    def get_container_inspect(self, ip):
        """查看容器

        查看指定IP的容器，返回容器属性。

        Args:
            - ip:   容器ip

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回容器的信息，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/containers/{1}/inspect'.format(self.host, ip)
        return self.__get(url)

    def start_container(self, ip):
        """启动容器

        启动指定IP的容器。

        Args:
            - ip:   容器ip

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/containers/{1}/start'.format(self.host, ip)
        return self.__post(url)

    def stop_container(self, ip):
        """停止容器

        停止指定IP的容器。

        Args:
            - ip:   容器ip

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/containers/{1}/stop'.format(self.host, ip)
        return self.__post(url)

    def restart_container(self, ip):
        """重启容器

        重启指定IP的容器。

        Args:
            - ip:   容器ip

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/containers/{1}/restart'.format(self.host, ip)
        return self.__post(url)

    def list_aps(self):
        """列出接入点

        列出当前应用的所有接入点。

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回接入点列表，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/aps'.format(self.host)
        return self.__get(url)

    def create_ap(self, args):
        """申请接入点

        申请指定配置的接入点资源。

        Args:
            - args:   请求参数(json)，参考 http://kirk-docs.qiniu.com/apidocs/

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回申请到的接入点信息，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/aps'.format(self.host)
        return self.__post(url, args)

    def search_ap(self, mode, query):
        """搜索接入点

        查看指定接入点的所有配置信息，包括所有监听端口的配置。

        Args:
            - mode:     搜索模式，可以是domain、ip、host
            - query:    搜索文本

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回搜索结果，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/aps/search?{1}={2}'.format(self.host, mode, query)
        return self.__get(url)

    def get_ap(self, apid):
        """查看接入点

        给出接入点的域名或IP，查看配置信息，包括所有监听端口的配置。

        Args:
            - apid:   接入点ID

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回接入点信息，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/aps/{1}'.format(self.host, apid)
        return self.__get(url)

    def update_ap(self, apid, args):
        """更新接入点

        更新指定接入点的配置，如带宽。

        Args:
            - apid:   接入点ID
            - args:   请求参数(json)，参考 http://kirk-docs.qiniu.com/apidocs/

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/aps/{1}'.format(self.host, apid)
        return self.__post(url, args)

    def set_ap_port(self, apid, port, args):
        """更新接入点端口配置

        更新接入点指定端口的配置。

        Args:
            - apid: 接入点ID
            - port: 要设置的端口号
            - args: 请求参数(json)，参考 http://kirk-docs.qiniu.com/apidocs/

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/aps/{1}/{2}'.format(self.host, apid, port)
        return self.__post(url, args)

    def delete_ap(self, apid):
        """释放接入点

        销毁指定接入点资源。

        Args:
            - apid: 接入点ID

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/aps/{1}'.format(self.host, apid)
        return self.__delete(url)

    def publish_ap(self, apid, args):
        """绑定自定义域名

        绑定用户自定义的域名，仅对公网域名模式接入点生效。

        Args:
            - apid: 接入点ID
            - args: 请求参数(json)，参考 http://kirk-docs.qiniu.com/apidocs/

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/aps/{1}/publish'.format(self.host, apid)
        return self.__post(url, args)

    def unpublish_ap(self, apid, args):
        """解绑自定义域名

        解绑用户自定义的域名，仅对公网域名模式接入点生效。

        Args:
            - apid: 接入点ID
            - args: 请求参数(json)，参考 http://kirk-docs.qiniu.com/apidocs/

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/aps/{1}/unpublish'.format(self.host, apid)
        return self.__post(url, args)

    def get_ap_port_healthcheck(self, apid, port):
        """查看健康检查结果

        检查接入点的指定端口的后端健康状况。

        Args:
            - apid: 接入点ID
            - port: 要设置的端口号

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回健康状况，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/aps/{1}/{2}/healthcheck'.format(self.host, apid, port)
        return self.__get(url)

    def set_ap_port_container(self, apid, port, args):
        """调整后端实例配置

        调整接入点指定后端实例（容器）的配置，例如临时禁用流量等。

        Args:
            - apid: 接入点ID
            - port: 要设置的端口号

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/aps/{1}/{2}/setcontainer'.format(self.host, apid, port)
        return self.__post(url, args)

    def disable_ap_port(self, apid, port):
        """临时关闭接入点端口

        临时关闭接入点端口，仅对公网域名，公网ip有效。

        Args:
            - apid: 接入点ID
            - port: 要设置的端口号

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/aps/{1}/{2}/disable'.format(self.host, apid, port)
        return self.__post(url)

    def enable_ap_port(self, apid, port):
        """开启接入点端口

        开启临时关闭的接入点端口，仅对公网域名，公网ip有效。

        Args:
            - apid: 接入点ID
            - port: 要设置的端口号

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回空dict{}，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/aps/{1}/{2}/enable'.format(self.host, apid, port)
        return self.__post(url)

    def get_ap_providers(self):
        """列出入口提供商

        列出当前支持的入口提供商，仅对申请公网IP模式接入点有效。
        注：公网IP供应商telecom=电信，unicom=联通，mobile=移动。

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回接入商列表，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/aps/providers'.format(self.host)
        return self.__get(url)

    def get_web_proxy(self, backend):
        """获取一次性代理地址

        对内网地址获取一个一次性的外部可访问的代理地址

        Args:
            - backend: 后端地址，如："10.128.0.1:8080"

        Returns:
            返回一个tuple对象，其格式为(<result>, <ResponseInfo>)
            - result          成功返回代理地址信息，失败返回{"error": "<errMsg string>"}
            - ResponseInfo    请求的Response信息
        """
        url = '{0}/v3/webproxy'.format(self.host)
        return self.__post(url, {'backend': backend})

    def __post(self, url, data=None):
        return http._post_with_qiniu_mac(url, data, self.auth)

    def __get(self, url, params=None):
        return http._get_with_qiniu_mac(url, params, self.auth)

    def __delete(self, url):
        return http._delete_with_qiniu_mac(url, None, self.auth)

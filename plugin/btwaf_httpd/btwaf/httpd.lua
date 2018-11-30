--[[
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: 黄文良 <287962566@qq.com>
#-------------------------------------------------------------------

#----------------------
# WAF防火墙 for apache
#----------------------
]]--
require 'apache2'
local cpath = "/www/server/btwaf/"
local jpath = cpath .. "rule/"
local json = require "cjson"
local memcached = require "memcached"
local uri,ip,ipn,request_uri,method,request_user_agent,localtime,today,cycle,endtime,limit,retry,retry_time,cache
local retry_cycle,site_cc,port_request_args,uri_request_args,server_name,site_config,config,error_rule,httpd

function read_file(name)
    fbody = read_file_body(jpath .. name .. '.json')
    if fbody == nil then
        return {}
    end
    return json.decode(fbody)
end

function read_file_body(filename)
	fp = io.open(filename,'r')
	if fp == nil then
        return nil
    end
	fbody = fp:read("*a")
    fp:close()
    if fbody == '' then
        return nil
    end
	return fbody
end

function read_file_body_test(filename)
	fp = io.open(filename,'r')
	return filename
	
end

function write_file(filename,body)
	fp = io.open(filename,'w')
	if fp == nil then
        return nil
    end
	fp:write(body)
	fp:flush()
	fp:close()
	return true
end

function is_ipaddr(client_ip)
	local cipn = split(client_ip,'.')
	if arrlen(cipn) < 4 then return false end
	for _,v in ipairs({1,2,3,4})
	do
		local ipv = tonumber(cipn[v])
		if ipv == nil then return false end
		if ipv > 255 or ipv < 0 then return false end
	end
	return true
end

function get_client_ip()
	local client_ip = "unknown"
	if site_config[server_name] then
		if site_config[server_name]['cdn'] then
			for _,v in ipairs(site_config[server_name]['cdn_header'])
			do
				if httpd.headers_in[v] ~= nil and httpd.headers_in[v] ~= "" then
					client_ip = split(httpd.headers_in[v],',')[1]
					break;
				end
			end	
		end
	end
	if string.match(client_ip,"%d+%.%d+%.%d+%.%d+") == nil or not is_ipaddr(client_ip) then
		client_ip = httpd.useragent_ip
		if client_ip == nil then
			client_ip = "unknown"
		end
	end
	return client_ip
end

function split( str,reps )
    local resultStrList = {}
    string.gsub(str,'[^'..reps..']+',function(w)
        table.insert(resultStrList,w)
    end)
    return resultStrList
end

function arrip(ipstr)
	if ipstr == 'unknown' then return {0,0,0,0} end
	iparr = split(ipstr,'.')
	iparr[1] = tonumber(iparr[1])
	iparr[2] = tonumber(iparr[2])
	iparr[3] = tonumber(iparr[3])
	iparr[4] = tonumber(iparr[4])
	return iparr
end

config = json.decode(read_file_body(cpath .. 'config.json'))
site_config = json.decode(read_file_body(cpath .. 'site.json'))

function join(arr,e)
	result = ''
	length = arrlen(arr)
	for k,v in ipairs(arr)
	do
		if length == k then e = '' end
		result = result .. v .. e
	end
	return result
end

function arrlen(arr)
	if not arr then return 0 end
	count = 0
	for _,v in ipairs(arr)
	do
		count = count + 1
	end
	return count
end

function select_rule(rules)
	if not rules then return {} end
	new_rules = {}
	for i,v in ipairs(rules)
	do 
		if v[1] == 1 then
			table.insert(new_rules,v[2])
		end
	end
	return new_rules
end

function is_site_config(cname)
	if site_config[server_name] ~= nil then
		if cname == 'cc' then
			return site_config[server_name][cname]['open']
		else
			return site_config[server_name][cname]
		end
	end
	return true
end

function get_boundary()
    local header = httpd.headers_in["content-type"]
    if not header then return nil end
    if type(header) == "table" then
        header = header[1]
    end

    local m = string.match(header, ";%s*boundary=\"([^\"]+)\"")
    if m then
        return m
    end
    return string.match(header, ";%s*boundary=([^\",;]+)")
end

function http_status(status)
	if status == 444 then status = 416 end
	httpd.status = status
end

function is_min(ip1,ip2)
	
	n = 0
	for _,v in ipairs({1,2,3,4})
	do
		if ip1[v] == ip2[v] then
			n = n + 1
		elseif ip1[v] > ip2[v] then
			break
		else
			return false
		end
	end
	return true
end

function is_max(ip1,ip2)
	n = 0
	for _,v in ipairs({1,2,3,4})
	do
		if ip1[v] == ip2[v] then
			n = n + 1
		elseif ip1[v] < ip2[v] then
			break
		else
			return false
		end
	end
	return true
end

function compare_ip(ips)
	if ip == 'unknown' then return true end
	if not is_max(ipn,ips[2]) then return false end
	if not is_min(ipn,ips[1]) then return false end
	return true
end


function write_log(name,rule)
	if not cache then cache = memcached.Connect("localhost", 11211) end
	local count = cache:get('safe_sum_'..ip)
	if count then
		cache:incr('safe_sum_'..ip,1)
	else
		cache:set('safe_sum_'..ip,1,retry_cycle)
	end
	if config['log'] ~= true or is_site_config('log') ~= true then return false end
	if error_rule then 
		rule = error_rule
		error_rule = nil
	end
	
	local logtmp = {localtime,ip,method,request_uri,request_user_agent,name,rule}
	local logstr = json.encode(logtmp) .. "\n"
	local count = cache:get('safe_sum_'..ip)
	
	if count > retry and name ~= 'cc' then
		local safe_count = cache:get('drop_sum_'..ip)
		if not safe_count then
			cache:set('drop_sum_'..ip,1,86400)
			safe_count = 1
		else
			cache:incr('drop_sum_'..ip,1)
		end
		local lock_time = retry_time * safe_count
		if lock_time > 86400 then lock_time = 86400 end
		logtmp = {localtime,ip,method,request_uri,request_user_agent,name,retry_cycle .. '秒以内累计超过'..tostring(retry)..'次以上非法请求,封锁'.. tostring(lock_time) ..'秒'}
		logstr = logstr .. json.encode(logtmp) .. "\n"
		cache:set('drop_ip_'..ip,retry + 1,lock_time)
		write_drop_ip('inc',lock_time)
	end
	write_to_file(logstr)
	inc_log(name,rule)
end

function write_drop_ip(is_drop,drop_time)
	local filename = cpath .. 'drop_ip.log'
	local fp = io.open(filename,'ab')
	if fp == nil then return false end
	local logtmp = {os.time(),ip,server_name,request_uri,drop_time,is_drop}
	local logstr = json.encode(logtmp) .. "\n"
	fp:write(logstr)
	fp:flush()
	fp:close()
	return true
end

function inc_log(name,rule)
	local total_path = cpath .. 'total.json'
	local tbody = cache:get(total_path)
	if not tbody then
		tbody = read_file_body(total_path)
		if not tbody then return false end
	end
	local total = json.decode(tbody)
	if not total['sites'] then total['sites'] = {} end
	if not total['sites'][server_name] then total['sites'][server_name] = {} end
	if not total['sites'][server_name][name] then total['sites'][server_name][name] = 0 end
	if not total['rules'] then total['rules'] = {} end
	if not total['rules'][name] then total['rules'][name] = 0 end
	if not total['total'] then total['total'] = 0 end
	total['total'] = total['total'] + 1
	total['sites'][server_name][name] = total['sites'][server_name][name] + 1
	total['rules'][name] = total['rules'][name] + 1
	local total_log = json.encode(total)
	if not total_log then return false end
	cache:set(total_path,total_log)
	if not cache:get('b_btwaf_timeout') then
		write_file(total_path,total_log)
		cache:set('b_btwaf_timeout',1,5)
	end
end

function write_to_file(logstr)
	local filename = config["logs_path"] .. '/' .. server_name .. '_' .. today .. '.log'
	local fp = io.open(filename,'ab')
	if fp == nil then return false end
	fp:write(logstr)
	fp:flush()
	fp:close()
	return true
end

function drop_abroad()
	if ip == 'unknown' then return false end
	if not config['drop_abroad']['open'] or not is_site_config('drop_abroad') then return false end
	local cnlist = json.decode(read_file_body(cpath .. '/rule/cn.json'))
	for _,v in ipairs(cnlist)
	do
		if compare_ip(v) then return false end
	end
	http_status(config['drop_abroad']['status'])
	return true
end

function drop()
	local count = cache:get('drop_ip_'..ip)
	if not count then return false end
	if count > retry then
		http_status(config['cc']['status'])
		return true
	end
	return false
end

function cc()
	if not config['cc']['open'] or not site_cc then return false end
	local token = httpd:md5(ip .. '_' .. httpd.the_request)
	local count = cache:get(token)
	if count then
		if count > limit then
			local safe_count = cache:get('drop_sum_'..ip)
			if not safe_count then
				cache:set('drop_sum_'..ip,1,86400)
				safe_count = 1
			else
				cache:incr('drop_sum_'..ip,1)
			end
			local lock_time = (endtime * safe_count)
			if lock_time > 86400 then lock_time = 86400 end
			cache:set('drop_ip_'..ip,retry+1,lock_time)
			write_log('cc',cycle..'秒内累计超过'..limit..'次请求,封锁' .. lock_time .. '秒')
			write_drop_ip('cc',lock_time)
			http_status(config['cc']['status'])
			return true
		else
			cache:incr(token,1)
		end
	else
		cache:set(token,1,cycle)
	end
	return false
end

function cc2()
	if not config['cc']['open'] or not site_cc then return false end
	if not site_config[server_name] then return false end
	if not site_config[server_name]['cc']['increase'] then return false end
	if httpd:regex(uri,"\\.(jpg|png|gif|css|js|swf|ts)$",0x01) then return false end
	sv = cache:get(ip)
	if sv == 666 then return false end
	local token2 = httpd:md5(method .. server_name .. tostring(httpd.headers_in['user-agent']) .. tostring(httpd.headers_in['host']) .. tostring(httpd.headers_in['accept-language']) .. tostring(httpd.headers_in['connection']) .. tostring(httpd.headers_in['accept']) .. tostring(httpd.headers_in['accept-encoding']) .. tostring(httpd.headers_in['upgrade-insecure-requests']) .. tostring(httpd.headers_in['cache-control'])) .. '_' .. 'cc2'
	local cc2_limit = limit * 3
	local count = cache:get(token2)
	if count then
		if count > cc2_limit then
			local safe_count = cache:get('drop_sum_'..ip)
			if not safe_count then
				cache:set('drop_sum_'..ip,1,86400)
				safe_count = 1
			else
				cache:incr('drop_sum_'..ip,1)
			end
			if safe_count > retry then 
				local lock_time = (endtime * safe_count)
				if lock_time > 86400 then lock_time = 86400 end
				cache:set('drop_ip_'..ip,retry+1,lock_time)
				write_log('cc',cycle..'秒内累计超过'..limit..'次请求,封锁' .. lock_time .. '秒')
				write_drop_ip('cc',lock_time)
				http_status(config['cc']['status'])
				return true
			end
			security_verification()
		else
			cache:incr(token2,1)
		end
	else
		cache:safe_set(token2,1,cycle)
	end
	return false
end

function security_verification()
	if uri_request_args['btwaf'] then
		vn3 = cache:get(ip)
		if tostring(vn3) == uri_request_args['btwaf'] then
			cache:delete(ip)
			cache:delete(httpd:md5(ip .. '_' .. uri))
			cache:set(ip,666,3600)
			return false
		end
	end
	math.randomseed(tostring(os.time()):reverse():sub(1, 6))
	local n1 = math.random(0,20)
	local n2 = math.random(0,20)
	local n3 = n1 + n2
	cache:set(ip,n3,300)
	local vargs = '&btwaf='
	sargs = string.gsub(request_uri,'.?btwaf=.*','')
	if not string.find(sargs,'?',1,true) then vargs = '?btwaf=' end
	local jsbody = string.format([[
<script type="text/javascript">var pre = prompt("检测到您的请求异常!\n请输入右边的计算结果: %s = ?");window.location.href='%s'+pre</script>
	]],tostring(n1) .. ' + ' .. tostring(n2),sargs .. vargs)
	httpd.content_type = "text/html;charset=utf8"
	httpd.write(jsbody)
	httpd.status = 403
end

function scan_black()
	if not config['scan']['open'] or not is_site_config('scan') then return false end
	local scan_black_rules = read_file('scan_black')
	if is_match(scan_black_rules['cookie'],httpd.headers_in['cookie'],false) then
		write_log('scan','regular')
		http_status(config['scan']['status'])
		return true
	end
	if is_match(scan_black_rules['args'],request_uri,false) then
		write_log('scan','regular')
		http_status(config['scan']['status'])
		return true
	end

	if is_match(scan_black_rules['header'],httpd.headers_in['user-agent'],false) then
		write_log('scan','regular')
		http_status(config['scan']['status'])
		return true
	end
	return false
end

function ip_black()
	local ip_black_rules = read_file('ip_black')
	for _,rule in ipairs(ip_black_rules)
	do
		if compare_ip(rule) then 
			http_status(config['cc']['status'])
			return true 
		end
	end
	return false
end

function ip_white()
	local ip_white_rules = read_file('ip_white')
	for _,rule in ipairs(ip_white_rules)
	do
		if compare_ip(rule) then 
			return true 
		end
	end
	return false
end

function url_white()
	local url_white_rules = read_file('url_white')
	if is_match(url_white_rules,request_uri,false) then
		return true
	end
	if site_config[server_name] ~= nil then
		if is_match(site_config[server_name]['url_white'],request_uri,false) then
			return true
		end
	end
	return false
end

function url_black()
	local url_black_rules = read_file('url_black')
	if is_match(url_black_rules,request_uri,false) then
		http_status(config['get']['status'])
		return true
	end
	return false
end

function head()
	if method ~= 'HEAD' then return false end
	local head_white_rules = read_file('head_white')
	for _,v in ipairs(head_white_rules)
	do
		if httpd:regex(uri,v,0x01) then
			return false
		end
	end
	spiders = {'spider','bot'}
	for _,v in ipairs(spiders)
	do
		if httpd:regex(httpd.headers_in['user-agent'],v,0x01) then
			return false
		end
	end
	write_log('head','禁止HEAD请求')
	cache:set(ip,retry,endtime)
	write_drop_ip('head',endtime)
	http_status(416)
end

function user_agent()
	if not config['user-agent']['open'] or not is_site_config('user-agent') then return false end
	local user_agent_rules = select_rule(read_file('user_agent'))
	if is_match(user_agent_rules,httpd.headers_in['user-agent'],'user_agent') then
		write_log('user_agent','regular')
		return_html(config['user-agent']['status'],'user-agent')
		return true
	end
	return false
end

function post()
	if not config['post']['open'] or not is_site_config('post') then return false end	
	if method ~= "POST" then return false end
	local post_rules = select_rule(read_file('post'))
	if is_match(post_rules,port_request_args,'post') then
		write_log('post','regular')
		return_html(config['post']['status'],'post')
		return true
	end
	return false
end

function disable_upload_ext(ext)
	if not ext then return false end
	ext = string.lower(ext)
	if is_key(site_config[server_name]['disable_upload_ext'],ext) then
		write_log('upload_ext','上传扩展名黑名单')
		return_html(config['other']['status'],'other')
		return true
	end
end

function post_data()
	if method ~= "POST" then return false end
	content_length=tonumber(httpd.headers_in['content-length'])
	if not content_length then return false end
	max_len = 256 * 1024
	if content_length > max_len then return false end
	local boundary = get_boundary()
	if boundary then
		if not port_request_args then return false end
		local tmp = httpd:regex(port_request_args,[[filename=\"(.+)\.(.*)\"]],0x01)
		if not tmp then return false end
		if not tmp[2] then return false end
		disable_upload_ext(tmp[2])
	end
	return false
end

function cookie()
	if not config['cookie']['open'] or not is_site_config('cookie') then return false end
	if not httpd.headers_in['cookie'] then return false end
	local cookie_rules = select_rule(read_file('cookie'))
	request_cookie = string.lower(httpd.headers_in['cookie'])
	if is_match(cookie_rules,request_cookie,'cookie') then
		write_log('cookie','regular')
		return_html(config['cookie']['status'],'cookie')
		return true
	end
	return false
end

function args()
	if not config['get']['open'] or not is_site_config('get') then return false end
	local args_rules = select_rule(read_file('args'))
	if is_match(args_rules,uri_request_args,'args') then
		write_log('args','regular')
		return_html(config['get']['status'],'get')
		return true
	end
	return false
end

function url()
	if not config['get']['open'] or not is_site_config('get') then return false end
	local url_rules = select_rule(read_file('url'))
	if is_match(url_rules,uri,'url') then
		write_log('url','regular')
		return_html(config['get']['status'],'get')
		return true
	end
	return false
end

function php_path()
	if site_config[server_name] == nil then return false end
	for _,rule in ipairs(site_config[server_name]['disable_php_path'])
	do
		if httpd:regex(uri,rule .. "/.*\\.php$",0x01) then
			write_log('php_path','regular')
			return_html(config['other']['status'],'other')
			return true
		end
	end
	return false
end

function url_path()
	if site_config[server_name] == nil then return false end
	for _,rule in ipairs(site_config[server_name]['disable_path'])
	do
		if httpd:regex(uri,rule,0x01) then
			write_log('path','regular')
			return_html(config['other']['status'],'other')
			return true
		end
	end
	return false
end

function url_ext()
	if site_config[server_name] == nil then return false end
	for _,rule in ipairs(site_config[server_name]['disable_ext'])
	do
		if httpd:regex(uri,"\\."..rule.."$",0x01) then
			write_log('url_ext','regular')
			return_html(config['other']['status'],'other')
			return true
		end
	end
	return false
end

function url_rule_ex()
	if site_config[server_name] == nil then return false end
	for _,rule in ipairs(site_config[server_name]['url_rule'])
	do
		if httpd:regex(uri,rule[1],0x01) then
			if is_match(rule[2],uri_request_args,false) then
				write_log('url_rule','regular')
				return_html(config['other']['status'],'other')
				return true
			end
			
			if method == "POST" and port_request_args ~= nil then 
				if is_match(rule[2],port_request_args,'post') then
					write_log('post','regular')
					return_html(config['other']['status'],'other')
					return true
				end
			end
		end
	end
	return false
end

function url_tell()
	if site_config[server_name] == nil then return false end
	for _,rule in ipairs(site_config[server_name]['url_tell'])
	do
		if httpd:regex(uri,rule[1],0x01) then
			if uri_request_args[rule[2]] ~= rule[3] then
				write_log('url_tell','regular')
				return_html(config['other']['status'],'other')
				return true
			end
		end
	end
	return false
end

 
function continue_key(key)
	key = tostring(key)
	if string.len(key) > 64 then return false end;
	local keys = {"content","contents","body","msg","file","files","img",""}
	for _,k in ipairs(keys)
	do
		if k == key then return false end;
	end
	return true;
end

function is_match(rules,sbody,rule_name)
	if rules == nil or sbody == nil or type(sbody) == "boolean" then return false end
	if type(sbody) == "string" then
		sbody = {sbody}
	end
	
	if type(rules) == "string" then
		rules = {rules}
	end
	
	for k,body in pairs(sbody)
	do
		if continue_key(k) then
			for i,rule in ipairs(rules)
			do
				if site_config[server_name] and rule_name then
					local n = i - 1
					for _,j in ipairs(site_config[server_name]['disable_rule'][rule_name])
					do
						if n == j then
							rule = ""
						end
					end
				end
				
				if body and rule ~="" then
					if type(body) == "string" then
						if httpd:regex(body,rule,0x01) then
							error_rule = rule .. ' >> ' .. k .. ':' .. body
							return true
						end
					end
					if type(k) == "string" then
						if httpd:regex(httpd:unescape(k),rule,0x01) then
							error_rule = rule .. ' >> ' .. k
							return true
						end
					end
				end
			end
		end
	end
	return false
end


function is_key(keys,values)
	if keys == nil or values == nil then return false end
	if type(values) == "string" then
		values = {values}
	end
	
	if type(keys) == "string" then
		keys = {keys}
	end
	
	for _,value in pairs(values)
	do
		if type(value) == "boolean" or value == "" then return false end
		sval = string.lower(httpd:unescape(value))
		for _,v in ipairs(keys)
        do
			if v == sval then
				return true
			end
        end
	end
	return false
end

function get_return_state(rstate,rmsg)
	result = {}
	result['status'] = rstate
	result['msg'] = rmsg
	return result
end

function get_btwaf_drop_ip()
	if not uri_request_args['ip'] or not is_ipaddr(uri_request_args['ip']) then return get_return_state(true,'格式错误') end
	local data =  cache:get('drop_ip_'..uri_request_args['ip'])
	return data
end

function remove_btwaf_drop_ip()
	if not uri_request_args['ip'] or not is_ipaddr(uri_request_args['ip']) then return get_return_state(true,'格式错误') end
	cache:delete('drop_ip_'..uri_request_args['ip'])
	cache:delete('safe_sum_'..uri_request_args['ip'])
	cache:delete('drop_sum_'..uri_request_args['ip'])
	return get_return_state(true,uri_request_args['ip'] .. '已解封')
end

function min_route()
	if httpd.useragent_ip ~= '127.0.0.1' then return false end
	if uri == '/get_btwaf_drop_ip' then
		return_message(200,get_btwaf_drop_ip())
		return true
	elseif uri == '/remove_btwaf_drop_ip' then
		return_message(200,remove_btwaf_drop_ip())
		return true
	end
	return false
end
  
function return_message(status,msg)
	httpd.content_type = "application/json;charset=utf-8"
	httpd.status = status
	httpd:write(json.encode(msg))
    return apache2.DONE
end


function return_html(status,rname)
	local html = read_file_body(config["reqfile_path"] .. '/' .. config[rname]["reqfile"])
	httpd.content_type = "text/html;charset=utf-8"
	httpd.status = status
	httpd:write(html)
    return apache2.DONE
end

function get_server_name()
	local c_name = httpd.server_name
	local my_name = cache:get(c_name)
	if my_name then return my_name end
	local tmp = read_file_body(cpath .. '/domains.json')
	if not tmp then return c_name end
	local domains = json.decode(tmp)
	for _,v in ipairs(domains)
	do
		for _,d_name in ipairs(v['domains'])
		do
			if c_name == d_name then
				cache:set(c_name,v['name'],3600)
				return v['name']
			end
		end
	end

	local tconf = httpd:activeconfig()
	if not tconf then return c_name end
	local tmp = split(tconf[1].file,'/')
	return string.gsub(tmp[arrlen(tmp)],'.conf$','')
end

function init_mem()
	method = httpd.method
	uri = httpd.uri
	ip = get_client_ip()
	ipn = arrip(ip)
	request_uri = httpd:unescape(httpd.unparsed_uri)
	method = httpd.method
	request_user_agent = tostring(httpd.headers_in['user-agent'])
	localtime = os.date("%Y-%m-%d %X")
	today = os.date("%Y-%m-%d")
	error_rule = nil
	
	cycle = config['cc']['cycle']
	endtime = config['cc']['endtime']
	limit = config['cc']['limit']
	retry = config['retry']
	retry_time = config['retry_time']
	retry_cycle = config['retry_cycle']
	site_cc = is_site_config('cc')
	if site_config[server_name] and site_cc then
		cycle = site_config[server_name]['cc']['cycle']
		endtime = site_config[server_name]['cc']['endtime']
		limit = site_config[server_name]['cc']['limit']
	end

	if site_config[server_name] then
		retry = site_config[server_name]['retry']
		retry_time = site_config[server_name]['retry_time']
		retry_cycle = site_config[server_name]['retry_cycle']
	end
end

function post_c(body)
	local post_rules = select_rule(read_file('post'))
	if is_match(post_rules,body,'post') then
		write_log('post','regular')
		return true
	end
	return false
end

function input_filter(request_httpd)
	if request_httpd.method ~= 'POST' then return end
	httpd = request_httpd
	server_name = get_server_name()
	if not cache then return end
	if not config['open'] or not is_site_config('open') then return end
	if not config['post']['open'] or not is_site_config('post') then return end
	init_mem()
    coroutine.yield()
    while bucket do
		if post_c(bucket) then
			coroutine.yield("")
		else
			coroutine.yield(bucket)
		end
    end
    coroutine.yield("")
end

function run_btwaf(request_httpd)
	httpd = request_httpd
	cache = memcached.Connect("127.0.0.1", 11211)
	if not cache then return apache2.DECLINED end
	server_name = get_server_name()
	if not config['open'] or not is_site_config('open') then return apache2.DECLINED end
	uri_request_args = httpd:parseargs();
	init_mem()
	if min_route() then return apache2.DONE end
	if ip_white() then return apache2.DECLINED end
	if ip_black() then return apache2.DONE end
	if url_white() then return apache2.DECLINED end
	if url_black() then return apache2.DONE end
	if drop() then return apache2.DONE end
	if drop_abroad() then return apache2.DONE end
	if cc() then return apache2.DONE end
	if cc2() then return apache2.DONE end
	if user_agent() then return apache2.DONE end
	if url() then return apache2.DONE end
	if args() then return apache2.DONE end
	if cookie() then return apache2.DONE end
	if scan_black() then return apache2.DONE end
	if site_config[server_name] then
		if php_path() then return apache2.DONE end
		if url_path() then return apache2.DONE end
		if url_ext() then return apache2.DONE end
		if url_rule_ex() then return apache2.DONE end
		if url_tell() then return apache2.DONE end
	end
	
	if cache then cache:disconnect_all() end
	return apache2.DECLINED
end


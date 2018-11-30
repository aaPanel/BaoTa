--[[
#-------------------------------------------------------------------
# 宝塔Linux面板
#-------------------------------------------------------------------
# Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
#-------------------------------------------------------------------
# Author: 黄文良 <287962566@qq.com>
#-------------------------------------------------------------------

#----------------------
# WAF防火墙 for nginx
#----------------------
]]--
local cpath = "/www/server/btwaf/"
local jpath = cpath .. "rule/"
local json = require "cjson"
local ngx_match = ngx.re.find
error_rule = nil

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

local config = json.decode(read_file_body(cpath .. 'config.json'))
local site_config = json.decode(read_file_body(cpath .. 'site.json'))

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
				if request_header[v] ~= nil and request_header[v] ~= "" then
					client_ip = request_header[v]
					break;
				end
			end	
		end
	end
	if string.match(client_ip,"%d+%.%d+%.%d+%.%d+") == nil or not is_ipaddr(client_ip) then
		client_ip = ngx.var.remote_addr
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
    local header = request_header["content-type"]
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

local get_html = read_file_body(config["reqfile_path"] .. '/' .. config["get"]["reqfile"])
local post_html = read_file_body(config["reqfile_path"] .. '/' .. config["post"]["reqfile"])
local cookie_html = read_file_body(config["reqfile_path"] .. '/' .. config["cookie"]["reqfile"])
local user_agent_html = read_file_body(config["reqfile_path"] .. '/' .. config["user-agent"]["reqfile"])
local other_html = read_file_body(config["reqfile_path"] .. '/' .. config["other"]["reqfile"])
local cnlist = json.decode(read_file_body(cpath .. '/rule/cn.json'))
local scan_black_rules = read_file('scan_black')
local ip_black_rules = read_file('ip_black')
local ip_white_rules = read_file('ip_white')
local url_white_rules = read_file('url_white')
local url_black_rules = read_file('url_black')
local user_agent_rules = select_rule(read_file('user_agent'))
local post_rules = select_rule(read_file('post'))
local cookie_rules = select_rule(read_file('cookie'))
local args_rules = select_rule(read_file('args'))
local url_rules = select_rule(read_file('url'))
local head_white_rules = read_file('head_white')

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
	local count,_ = ngx.shared.drop_ip:get(ip)
	if count then
		ngx.shared.drop_ip:incr(ip,1)
	else
		ngx.shared.drop_ip:set(ip,1,retry_cycle)
	end
	if config['log'] ~= true or is_site_config('log') ~= true then return false end
	local method = ngx.req.get_method()
	if error_rule then 
		rule = error_rule
		error_rule = nil
	end
	
	local logtmp = {ngx.localtime(),ip,method,request_uri,ngx.var.http_user_agent,name,rule}
	local logstr = json.encode(logtmp) .. "\n"
	local count,_ = ngx.shared.drop_ip:get(ip)	
	if count > retry and name ~= 'cc' then
		local safe_count,_ = ngx.shared.drop_sum:get(ip)
		if not safe_count then
			ngx.shared.drop_sum:set(ip,1,86400)
			safe_count = 1
		else
			ngx.shared.drop_sum:incr(ip,1)
		end
		local lock_time = retry_time * safe_count
		if lock_time > 86400 then lock_time = 86400 end
		logtmp = {ngx.localtime(),ip,method,request_uri,ngx.var.http_user_agent,name,retry_cycle .. '秒以内累计超过'..retry..'次以上非法请求,封锁'.. lock_time ..'秒'}
		logstr = logstr .. json.encode(logtmp) .. "\n"
		ngx.shared.drop_ip:set(ip,retry+1,lock_time)
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
	local tbody = read_file_body(total_path)
	if not tbody then return false end
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
	write_file(total_path,total_log)
end

function write_to_file(logstr)
	local filename = config["logs_path"] .. '/' .. server_name .. '_' .. ngx.today() .. '.log'
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
	for _,v in ipairs(cnlist)
	do
		if compare_ip(v) then return false end
	end
	ngx.exit(config['drop_abroad']['status'])
	return true
end

function drop()
	local count,_ = ngx.shared.drop_ip:get(ip)
	if not count then return false end
	if count > retry then
		ngx.exit(config['cc']['status'])
		return true
	end
	return false
end

function cc()
	if not config['cc']['open'] or not site_cc then return false end
	local token = ngx.md5(ip .. '_' .. request_uri)
	local count,_ = ngx.shared.btwaf:get(token)
	if count then
		if count > limit then
			local safe_count,_ = ngx.shared.drop_sum:get(ip)
			if not safe_count then
				ngx.shared.drop_sum:set(ip,1,86400)
				safe_count = 1
			else
				ngx.shared.drop_sum:incr(ip,1)
			end
			local lock_time = (endtime * safe_count)
			if lock_time > 86400 then lock_time = 86400 end
			ngx.shared.drop_ip:set(ip,retry+1,lock_time)
			write_log('cc',cycle..'秒内累计超过'..limit..'次请求,封锁' .. lock_time .. '秒')
			write_drop_ip('cc',lock_time)
			ngx.exit(config['cc']['status'])
			return true
		else
			ngx.shared.btwaf:incr(token,1)
		end
	else
		ngx.shared.btwaf:set(token,1,cycle)
	end
	return false
end

function cc2()
	if not config['cc']['open'] or not site_cc then return false end
	if not site_config[server_name] then return false end
	if not site_config[server_name]['cc']['increase'] then return false end
	if ngx_match(uri,"\\.(jpg|png|gif|css|js|swf|ts)$","isjo") then return false end
	sv,_ = ngx.shared.btwaf:get(ip)
	if sv == 666 then return false end
	local token2 = ngx.md5(method .. server_name .. tostring(request_header['user-agent']) .. tostring(request_header['host']) .. tostring(request_header['accept-language']) .. tostring(request_header['connection']) .. tostring(request_header['accept']) .. tostring(request_header['accept-encoding']) .. tostring(request_header['upgrade-insecure-requests']) .. tostring(request_header['cache-control'])) .. '_' .. 'cc2'
	local cc2_limit = limit * 3
	local count,_ = ngx.shared.btwaf:get(token2)
	if count then
		if count > cc2_limit then
			local safe_count,_ = ngx.shared.drop_sum:get(ip)
			if not safe_count then
				ngx.shared.drop_sum:set(ip,1,86400)
				safe_count = 1
			else
				ngx.shared.drop_sum:incr(ip,1)
			end
			if safe_count > retry then 
				local lock_time = (endtime * safe_count)
				if lock_time > 86400 then lock_time = 86400 end
				ngx.shared.drop_ip:set(ip,retry+1,lock_time)
				write_log('cc',cycle..'秒内累计超过'..limit..'次请求,封锁' .. lock_time .. '秒')
				write_drop_ip('cc',lock_time)
				ngx.exit(config['cc']['status'])
				return true
			end
			security_verification()
		else
			ngx.shared.btwaf:incr(token2,1)
		end
	else
		ngx.shared.btwaf:safe_set(token2,1,cycle)
	end
	return false
end

function security_verification()
	if uri_request_args['btwaf'] then
		vn3,_ = ngx.shared.btwaf:get(ip)
		if tostring(vn3) == uri_request_args['btwaf'] then
			ngx.shared.btwaf:delete(ip)
			ngx.shared.btwaf:delete(ngx.md5(ip .. '_' .. uri))
			ngx.shared.btwaf:set(ip,666,3600)
			return false
		end
	end
	math.randomseed(tostring(os.time()):reverse():sub(1, 6))
	local n1 = math.random(0,20)
	local n2 = math.random(0,20)
	local n3 = n1 + n2
	ngx.shared.btwaf:set(ip,n3,300)
	local vargs = '&btwaf='
	sargs = string.gsub(request_uri,'.?btwaf=.*','')
	if not string.find(sargs,'?',1,true) then vargs = '?btwaf=' end
	ngx.header.charset = 'utf-8'
	local jsbody = string.format([[
<script type="text/javascript">var pre = prompt("检测到您的请求异常!\n请输入右边的计算结果: %s = ?");window.location.href='%s'+pre</script>
	]],tostring(n1) .. ' + ' .. tostring(n2),sargs .. vargs)
	ngx.header.content_type = "text/html;charset=utf8"
	ngx.say(jsbody)
	ngx.exit(403)
end

function scan_black()
	if not config['scan']['open'] or not is_site_config('scan') then return false end
	if is_ngx_match(scan_black_rules['cookie'],request_header['cookie'],false) then
		write_log('scan','regular')
		ngx.exit(config['scan']['status'])
		return true
	end
	if is_ngx_match(scan_black_rules['args'],request_uri,false) then
		write_log('scan','regular')
		ngx.exit(config['scan']['status'])
		return true
	end
	for key,value in pairs(request_header)
	do
		if is_ngx_match(scan_black_rules['header'],key,false) then
			write_log('scan','regular')
			ngx.exit(config['scan']['status'])
			return true
		end
	end
	return false
end

function ip_black()
	for _,rule in ipairs(ip_black_rules)
	do
		if compare_ip(rule) then 
			ngx.exit(config['cc']['status'])
			return true 
		end
	end
	return false
end

function ip_white()
	for _,rule in ipairs(ip_white_rules)
	do
		if compare_ip(rule) then 
			return true 
		end
	end
	return false
end

function url_white()
	if is_ngx_match(url_white_rules,request_uri,false) then
		return true
	end
	if site_config[server_name] ~= nil then
		if is_ngx_match(site_config[server_name]['url_white'],request_uri,false) then
			return true
		end
	end
	return false
end

function url_black()
	if is_ngx_match(url_black_rules,request_uri,false) then
		ngx.exit(config['get']['status'])
		return true
	end
	return false
end

function head()
	if method ~= 'HEAD' then return false end
	for _,v in ipairs(head_white_rules)
	do
		if ngx_match(uri,v,"isjo") then
			return false
		end
	end
	spiders = {'spider','bot'}
	for _,v in ipairs(spiders)
	do
		if ngx_match(request_header['user-agent'],v,"isjo") then
			return false
		end
	end
	write_log('head','禁止HEAD请求')
	ngx.shared.btwaf:set(ip,retry,endtime)
	write_drop_ip('head',endtime)
	ngx.exit(444)
end

function user_agent()
	if not config['user-agent']['open'] or not is_site_config('user-agent') then return false end	
	if is_ngx_match(user_agent_rules,request_header['user-agent'],'user_agent') then
		write_log('user_agent','regular')
		return_html(config['user-agent']['status'],user_agent_html)
		return true
	end
	return false
end

function post()
	if not config['post']['open'] or not is_site_config('post') then return false end	
	if method ~= "POST" then return false end
	content_length=tonumber(request_header['content-length'])
	max_len = 64 * 1024
	if content_length > max_len then return false end
	if get_boundary() then return false end
	ngx.req.read_body()
	request_args = ngx.req.get_post_args()
	if not request_args then
		return false
	end
	
	if is_ngx_match(post_rules,request_args,'post') then
		write_log('post','regular')
		return_html(config['post']['status'],post_html)
		return true
	end
	return false
end

function disable_upload_ext(ext)
	if not ext then return false end
	ext = string.lower(ext)
	if is_key(site_config[server_name]['disable_upload_ext'],ext) then
		write_log('upload_ext','上传扩展名黑名单')
		return_html(config['other']['status'],other_html)
		return true
	end
end

function post_data()
	if method ~= "POST" then return false end
	content_length=tonumber(request_header['content-length'])
	if not content_length then return false end
	max_len = 256 * 1024
	if content_length > max_len then return false end
	local boundary = get_boundary()
	if boundary then
		ngx.req.read_body()
		local data = ngx.req.get_body_data()
		if not data then return false end
		local tmp = ngx.re.match(data,[[filename=\"(.+)\.(.*)\"]])
		if not tmp then return false end
		if not tmp[2] then return false end
		disable_upload_ext(tmp[2])
	end
	return false
end

function cookie()
	if not config['cookie']['open'] or not is_site_config('cookie') then return false end
	if not request_header['cookie'] then return false end
	request_cookie = string.lower(request_header['cookie'])
	if is_ngx_match(cookie_rules,request_cookie,'cookie') then
		write_log('cookie','regular')
		return_html(config['cookie']['status'],cookie_html)
		return true
	end
	return false
end

function args()
	if not config['get']['open'] or not is_site_config('get') then return false end	
	if is_ngx_match(args_rules,uri_request_args,'args') then
		write_log('args','regular')
		return_html(config['get']['status'],get_html)
		return true
	end
	return false
end

function url()
	if not config['get']['open'] or not is_site_config('get') then return false end

	--正则--
	if is_ngx_match(url_rules,uri,'url') then
		write_log('url','regular')
		return_html(config['get']['status'],get_html)
		return true
	end
	return false
end

function php_path()
	if site_config[server_name] == nil then return false end
	for _,rule in ipairs(site_config[server_name]['disable_php_path'])
	do
		if ngx_match(uri,rule .. "/.*\\.php$","isjo") then
			write_log('php_path','regular')
			return_html(config['other']['status'],other_html)
			return true
		end
	end
	return false
end

function url_path()
	if site_config[server_name] == nil then return false end
	for _,rule in ipairs(site_config[server_name]['disable_path'])
	do
		if ngx_match(uri,rule,"isjo") then
			write_log('path','regular')
			return_html(config['other']['status'],other_html)
			return true
		end
	end
	return false
end

function url_ext()
	if site_config[server_name] == nil then return false end
	for _,rule in ipairs(site_config[server_name]['disable_ext'])
	do
		if ngx_match(uri,"\\."..rule.."$","isjo") then
			write_log('url_ext','regular')
			return_html(config['other']['status'],other_html)
			return true
		end
	end
	return false
end

function url_rule_ex()
	if site_config[server_name] == nil then return false end
	if method == "POST" and not request_args then
		content_length=tonumber(request_header['content-length'])
		max_len = 64 * 1024
		request_args = nil
		if content_length < max_len then
			ngx.req.read_body()
			request_args = ngx.req.get_post_args()
		end
	end
	for _,rule in ipairs(site_config[server_name]['url_rule'])
	do
		if ngx_match(uri,rule[1],"isjo") then
			if is_ngx_match(rule[2],uri_request_args,false) then
				write_log('url_rule','regular')
				return_html(config['other']['status'],other_html)
				return true
			end
			
			if method == "POST" and request_args ~= nil then 
				if is_ngx_match(rule[2],request_args,'post') then
					write_log('post','regular')
					return_html(config['other']['status'],other_html)
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
		if ngx_match(uri,rule[1],"isjo") then
			if uri_request_args[rule[2]] ~= rule[3] then
				write_log('url_tell','regular')
				return_html(config['other']['status'],other_html)
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

function is_ngx_match(rules,sbody,rule_name)
	if rules == nil or sbody == nil then return false end
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
						if ngx_match(ngx.unescape_uri(body),rule,"isjo") then
							error_rule = rule .. ' >> ' .. k .. ':' .. body
							return true
						end
					end
					if type(k) == "string" then
						if ngx_match(ngx.unescape_uri(k),rule,"isjo") then
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
		sval = ngx.unescape_uri(string.lower(ngx.unescape_uri(value)))
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
	local data =  ngx.shared.drop_ip:get_keys(0)
	return data
end

function remove_btwaf_drop_ip()
	if not uri_request_args['ip'] or not is_ipaddr(uri_request_args['ip']) then return get_return_state(true,'格式错误') end
	ngx.shared.drop_ip:delete(uri_request_args['ip'])
	return get_return_state(true,uri_request_args['ip'] .. '已解封')
end

function clean_btwaf_drop_ip()
	local data = get_btwaf_drop_ip()
	for _,value in ipairs(data)
	do
		ngx.shared.drop_ip:delete(value)
	end
	return get_return_state(true,'已解封所有封锁IP')
end

function min_route()
	if ngx.var.remote_addr ~= '127.0.0.1' then return false end
	if uri == '/get_btwaf_drop_ip' then
		return_message(200,get_btwaf_drop_ip())
	elseif uri == '/remove_btwaf_drop_ip' then
		return_message(200,remove_btwaf_drop_ip())
	elseif uri == '/clean_btwaf_drop_ip' then
		return_message(200,clean_btwaf_drop_ip())
	end
end

function return_message(status,msg)
	ngx.header.content_type = "application/json;"
	ngx.status = status
	ngx.say(json.encode(msg))
    ngx.exit(status)
end

function return_html(status,html)
	ngx.header.content_type = "text/html"
    ngx.status = status
    ngx.say(html)
    ngx.exit(status)
end


function run_btwaf()
	server_name = ngx.var.server_name
	if not config['open'] or not is_site_config('open') then return false end
	error_rule = nil
	request_header = ngx.req.get_headers()
	method = ngx.req.get_method()
	ip = get_client_ip()
	ipn = arrip(ip)
	request_uri = ngx.var.request_uri
	uri = ngx.unescape_uri(ngx.var.uri)
	uri_request_args = ngx.req.get_uri_args()
	cycle = config['cc']['cycle']
	endtime = config['cc']['endtime']
	limit = config['cc']['limit']
	retry = config['retry']
	retry_time = config['retry_time']
	retry_cycle = config['retry_cycle']
	min_route()
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
	
	if ip_white() then return true end
	ip_black()

	if url_white() then return true end
	url_black()
	--head()
	drop()
	drop_abroad()
	cc()
	cc2()
	user_agent()
	url()
	args()
	cookie()
	scan_black()
	post()
	if site_config[server_name] then
		php_path()
		url_path()
		url_ext()
		url_rule_ex()
		url_tell()
		post_data()
	end
end

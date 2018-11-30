local cpath = "/www/server/total/"
local json = require "cjson"
local memcached = require "memcached"
local server_name,ip,today,body_length,localtime,localhour,ipn,config,is_write,method,area_ip,config,httpd,cache

function write_file_bylog(filename,body,mode)
	local fp = io.open(filename,mode)
	if fp == nil then
        return nil
    end
	fp:write(body)
	fp:flush()
	fp:close()
	return true
end

function read_file_body_bylog(filename)
	local fp = io.open(filename,'rb')
	if not fp then
        return nil
    end
	fbody = fp:read("*a")
    fp:close()
    if fbody == '' then
        return nil
    end
	return fbody
end

function is_ipaddr_bylog(client_ip)
	local cipn = split_bylog(client_ip,'.')
	if arrlen_bylog(cipn) < 4 then return false end
	for _,v in ipairs({1,2,3,4})
	do
		local ipv = tonumber(cipn[v])
		if ipv == nil then return false end
		if ipv > 255 or ipv < 0 then return false end
	end
	return true
end

function get_client_ip_bylog()
	local client_ip = "unknown"
	if config['sites'][server_name] then
		if config['sites'][server_name]['cdn'] then
			for _,v in ipairs(config['sites'][server_name]['cdn_headers'])
			do
				if request_header[v] ~= nil and request_header[v] ~= "" then
					client_ip = split_bylog(httpd.headers_in[v],',')[1]
					break;
				end
			end
		end
	end
	if string.match(client_ip,"%d+%.%d+%.%d+%.%d+") == nil or not is_ipaddr_bylog(client_ip) then
		client_ip = httpd.useragent_ip
		if client_ip == nil then
			client_ip = "unknown"
		end
	end
	return client_ip
end

function split_bylog( str,reps )
    local resultStrList = {}
    string.gsub(str,'[^'..reps..']+',function(w)
        table.insert(resultStrList,w)
    end)
    return resultStrList
end

function arrip_bylog(ipstr)
	if ipstr == 'unknown' then return {0,0,0,0} end
	iparr = split_bylog(ipstr,'.')
	iparr[1] = tonumber(iparr[1])
	iparr[2] = tonumber(iparr[2])
	iparr[3] = tonumber(iparr[3])
	iparr[4] = tonumber(iparr[4])
	return iparr
end


function arrlen_bylog(arr)
	if not arr then return 0 end
	count = 0
	for _,v in ipairs(arr)
	do
		count = count + 1
	end
	return count
end

function is_min_bylog(ip1,ip2)
	
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

function is_max_bylog(ip1,ip2)
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

function compare_ip_bylog(ips)
	if ip == 'unknown' then return true end
	if not is_max_bylog(ipn,ips[2]) then return false end
	if not is_min_bylog(ipn,ips[1]) then return false end
	return true
end

function get_length(k)
	local clen  = httpd.headers_out['Content-Length']
	if clen == nil then clen = 0 end
	if clen == 0 and httpd.filename then
		tmp = httpd:stat(httpd.filename)
      	if tmp then clen = tmp.size end
    end
	return tonumber(clen)
end

function write_logs_bylog()
	local logline = {localtime , ip , server_name , method , httpd.status , httpd.unparsed_uri , body_length , httpd.headers_in['referer'] , httpd.headers_in['user-agent'] , httpd.protocol}
	local path = cpath .. '/logs/' .. server_name
	if not check_dir(path) then create_dir(path) end
	write_file_bylog(path .. '/' .. today .. '.log',json.encode(logline) .. "\n",'ab')
end

function check_dir(path)
	local file = io.open(path, "rb")
	if file then file:close() end
	return file ~= nil
end

function create_dir(path)
	httpd:mkrdir(path)
end

function get_end_time()
	local s_time = os.time()
    local n_date = os.date("*t",s_time + 86400)
	n_date.hour = 0
	n_date.min = 0
	n_date.sec = 0
	d_time = os.time(n_date)
    return d_time - s_time
end

function get_data_on(filename)
	local data = cache:get(filename)
	if not data then
		data = read_file_body_bylog(filename)
		if not data then 
			data = {}
		else
			data = json.decode(data)
		end
	else
		data = json.decode(data)
	end
	return data
end

function save_data_on(filename,data)
	local newdata = json.encode(data)
	local extime = 0;
	if string.find(filename,"%d+-%d+-%d+") then extime = 88400 end
	cache:set(filename,newdata,extime)
	if not cache:get(filename..'_lock') then
		cache:set(filename..'_lock',1,10)
		write_file_bylog(filename,newdata,'wb')
	end
end

function total_net()
	local path = cpath .. '/total/' .. server_name .. '/network'
	if not check_dir(path) then create_dir(path) end
	local filename = path .. '/' .. today .. '.json'
	local data = get_data_on(filename)
	if not data[localhour] then data[localhour] = 0 end
	data[localhour] = data[localhour] + body_length
	save_data_on(filename,data)
	
	data = nil
	newdata = nil
	filename = path .. '/total.json'
	data = get_data_on(filename)
	if type(data) == "table" then data = 0 end
	data = data + body_length
	save_data_on(filename,data)
	
	data = nil
	newdata = nil
	filename = cpath .. '/total/network.json'
	data = get_data_on(filename)
	if type(data) == "table" then data = 0 end
	data = data + body_length
	save_data_on(filename,data)
end

function total_request()
	local path = cpath .. '/total/' .. server_name .. '/request'
	local tmp_path = cpath..'/tmp'
	if not check_dir(path) then create_dir(path) end
	if not check_dir(tmp_path) then create_dir(tmp_path) end
	
	local files = {
				path .. '/' .. today .. '.json',
				path .. '/total.json',
				cpath .. '/total/request.json'
			}
	
	state = tostring(httpd.status)
	for i,filename in ipairs(files)
	do
		local data = get_data_on(filename)
		if i == 1 then
			if not data[localhour] then data[localhour] = {} end
			if data[localhour][method] == nil then data[localhour][method] = 0 end
			data[localhour][method] = data[localhour][method] + 1
			
			if data[localhour][state]  == nil then data[localhour][state] = 0 end
			data[localhour][state] = data[localhour][state] + 1
			
			--ip or pv or uv
			if method == 'GET' and httpd.status == 200 then
				if request_header['user-agent'] then
					ua = string.lower(request_header['user-agent'])
				else
					ua = ''
				end
				if not string.find(ua,'spider') and not string.find(ua,'bot') then
					if not httpd:regex(httpd.uri,"\.(js|css|png|jpeg|jpg|gif)$",0x01) then
						local ip_token = server_name..'_'..ip
						if not cache:get(ip_token) then
							if data[localhour]['ip'] == nil then data[localhour]['ip'] = 0 end
							data[localhour]['ip'] = data[localhour]['ip'] + 1
							cache:set(ip_token,1,get_end_time())
						end
						
						if data[localhour]['pv'] == nil then data[localhour]['pv'] = 0 end
						data[localhour]['pv'] = data[localhour]['pv'] + 1
						
						if request_header['user-agent'] then
							if string.find(ua,'mozilla') then
								local uv_token = httpd:md5(ip .. request_header['user-agent'] .. today)
								if not cache:get(uv_token) then
									if data[localhour]['uv'] == nil then data[localhour]['uv'] = 0 end
									data[localhour]['uv'] = data[localhour]['uv'] + 1
									cache:set(uv_token,1,get_end_time())
								end
							end
						end
					end
				end
			end
		else
			if data[method] == nil then data[method] = 0 end
			data[method] = data[method] + 1
			
			if data[state]  == nil then data[state] = 0 end
			data[state] = data[state] + 1
		end
		save_data_on(filename,data)
	end
end

function total_area()
	local isn = false
	if not area_ip then
		area_ip = cache:get('area_ip')
		if not area_ip then
			area_ip = read_file_body_bylog(cpath .. '/total/iplist.json')
			cache:set('area_ip',area_ip)
		end
		area_ip = json.decode(area_ip)
	end
	
	for k,arr in pairs(area_ip)
	do
		for _,v in ipairs(arr)
		do
			if compare_ip_bylog(v) then
				write_area(k)
				return true
			end
		end
	end
	write_area('other')
end

function write_area(k)
	local path = cpath .. '/total/' .. server_name .. '/area'
	if not check_dir(path) then create_dir(path) end
	local files = {
		path .. '/' .. today .. '.json',
		path .. '/total.json',
		cpath .. '/total/area.json'
	}
	for i,filename in ipairs(files)
	do
		local data = get_data_on(filename)
		if data[k] == nil then data[k] = 0 end
		data[k] = data[k] + 1
		save_data_on(filename,data)
	end
end

function total_spider()
    if request_header['user-agent'] == nil then return true end
	local path = cpath .. '/total/' .. server_name .. '/spider'
	if not check_dir(path) then create_dir(path) end
	for _,bot in ipairs(config['spiders'])
	do
		if string.find(request_header['user-agent'],bot) then
			local files = {
				path .. '/' .. today .. '.json',
				path .. '/total.json',
				cpath .. '/total/spider.json'
			}
			for i,filename in ipairs(files)
			do
				local data = get_data_on(filename)
				if i == 1 then
					if not data[localhour] then data[localhour] = {} end
					if data[localhour][bot] == nil then data[localhour][bot] = 0 end
					data[localhour][bot] = data[localhour][bot] + 1
				else
					if data[bot] == nil then data[bot] = 0 end
					data[bot] = data[bot] + 1
				end
				save_data_on(filename,data)
			end
			break
		end
	end
end

function total_client()	
    if request_header['user-agent'] == nil then return true end
	local path = cpath .. '/total/' .. server_name .. '/client'
	if not check_dir(path) then create_dir(path) end
	
	for _,ua in ipairs(config['clients'])
	do
		if string.find(request_header['user-agent'],ua) then
			local files = {
				path .. '/' .. today .. '.json',
				path .. '/total.json',
				cpath .. '/total/client.json'
			}
			for i,filename in ipairs(files)
			do
				local data = get_data_on(filename)
				if i == 1 then
					if not data[localhour] then data[localhour] = {} end
					if data[localhour][ua] == nil then data[localhour][ua] = 0 end
					data[localhour][ua] = data[localhour][ua] + 1
				else
					if data[ua] == nil then data[ua] = 0 end
					data[ua] = data[ua] + 1
				end
				save_data_on(filename,data)
			end
			return true
		end
	end
end

function error_log()
	if httpd.status ~= 500 and httpd.status ~= 502 and httpd.status ~= 401 and httpd.status ~= 503 then return false end
	local logline = {localtime , ip , server_name , method , httpd.status , httpd.unparsed_uri , body_length , httpd.headers_in['referer'] , httpd.headers_in['user-agent'] , httpd.protocol}
	local path = cpath .. '/logs/' .. server_name .. '/error'
	if not check_dir(path) then create_dir(path) end
	write_file_bylog(path .. '/'.. tostring(httpd.status) .. '.log',json.encode(logline) .. "\n",'ab')
end

function exclude_extension()
	if not config['sites'][server_name] then return false end
	if not httpd.uri then return false end
	for _,v in ipairs(config['sites'][server_name]['log_exclude_extension'])
	do
		if httpd:regex(httpd.uri,v.."$",0x01) then
			return true
		end
	end
	return false
end

function exclude_status()
	if not config['sites'][server_name] then return false end
	for _,v in ipairs(config['sites'][server_name]['log_exclude_status'])
	do
		if httpd.status == v then
			return true
		end
	end
	return false
end

function total_ip()
	if not config['sites'][server_name] then return false end
	
	for k,v in pairs(config['sites'][server_name]['total_ip'])
	do
		if ip == k then
			config['sites'][server_name]['total_ip'][k] = config['sites'][server_name]['total_ip'][k] + 1
			is_write = is_write + 1
		end
	end
	return false
end

function total_uri()
	if not config['sites'][server_name] then return false end
	for k,v in pairs(config['sites'][server_name]['total_uri'])
	do
		if httpd.uri == k then
			config['sites'][server_name]['total_uri'][k] = config['sites'][server_name]['total_uri'][k] + 1
			is_write = is_write + 1
		end
	end
	return false
end

function get_server_name()
	local c_name = httpd.server_name
	local my_name = cache:get(c_name)
	if my_name then return my_name end
	local tmp = read_file_body_bylog(cpath .. '/domains.json')
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
	local tmp = split_bylog(tconf[1].file,'/')
	if not tmp then return c_name end
	return string.gsub(tmp[arrlen_bylog(tmp)],'.conf$','')
end

function run_logs(request)
	httpd = request
	if httpd.uri == '/favicon.ico' or httpd.status == 0 or httpd.status == 416 then return apache2.DONE end
                              
    cache = memcached.Connect("127.0.0.1", 11211)
	if not cache then
		cache = memcached.Connect("localhost", 11211)
	end
	if not cache then return apache2.OK end
    
	server_name = get_server_name()
	if server_name == 'httpd-vhosts' or server_name == '127.0.0.1' or server_name == 'phpinfo' then return apache2.OK end
	
	if not config then
		config = json.decode(read_file_body_bylog(cpath..'/config.json'))
	end
	if not config['open'] then return apache2.OK end
	if config['sites'][server_name] then
		if not config['sites'][server_name]['open'] then return apache2.OK end
	end
	method = httpd.method
	if method == "" or not method then return apache2.OK end
	request_header = httpd.headers_in
	out_header = httpd.headers_out
	is_write = 0
	body_length = get_length()
	ip = get_client_ip_bylog()
	ipn = arrip_bylog(ip)
	today = os.date("%Y-%m-%d")
	localtime = os.date("%Y-%m-%d %X")
	localhour = os.date("%H")
	error_log()
	total_net()
	total_request()
	total_ip()
	total_uri()
	total_spider()
	total_client()
	--total_area()
	
	if is_write > 0 then
		save_data_on(cpath..'/config.json',config)
	end
	if exclude_status() then return apache2.DONE end
	if exclude_extension() then return apache2.DONE end
	
	if config['sites'][server_name] then
		write_logs_bylog()
		if config['sites'][server_name]['log_open'] then return apache2.DONE end
	end
	return apache2.OK
end
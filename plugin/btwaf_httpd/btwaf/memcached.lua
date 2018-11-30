--Copyright (c) 2006-2008 Neil Richardson (nrich@neiltopia.com)
--
--Permission is hereby granted, free of charge, to any person obtaining a copy 
--of this software and associated documentation files (the "Software"), to deal
--in the Software without restriction, including without limitation the rights 
--to use, copy, modify, merge, publish, distribute, sublicense, and/or sell 
--copies of the Software, and to permit persons to whom the Software is 
--furnished to do so, subject to the following conditions:
--
--The above copyright notice and this permission notice shall be included in all
--copies or substantial portions of the Software.
--
--THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR 
--IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, 
--FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE 
--AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER 
--LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, 
--OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS 
--IN THE SOFTWARE.

local _M = {}
local table = require('table')
local socket = require('socket')
local CRC32 = require('CRC32')

local SERVER_RETRIES = 10

local STATS_KEYS = {
    malloc = true,
    sizes = true,
    slabs = true,
    items = true,
}

local FLAGS = {
    'STORABLE',
    'COMPRESSED',
    'SERIALISED',
}

local function warn(str)
    io.stderr:write(string.format('Warning: %s\n', tostring(str)))
end

local function _select_server(cache, key)
    local server_count = #cache.servers

    local hashfunc = cache.hash or CRC32.Hash

    if server_count == 1 then
	return cache.servers[1].socket
    else
	local serverhash = hashfunc(key)

	for i = 0, SERVER_RETRIES do
	    local index = (serverhash % server_count) + 1
	    local server = cache.servers[index].socket

	    if not server then
		serverhash = hashfunc(serverhash .. i)
	    else
		return server
	    end
	end
    end

    error('No servers found')
    return nil
end

local function _retrieve(cache, key, str)
    local server = _select_server(cache, key)

    server:send(str .. '\r\n')

    local function toboolean(value)
	if type(value) == 'string' then
	    if value == 'true' then
		return true
	    elseif value == 'false' then
		return false 
	    end
	end

	return nil
    end

    local function extract_flags(str)
	local num = tonumber(str)
	local flags = {}

	for i = #(FLAGS), 1, -1 do
	    local bf = 2 ^ (i - 1)

	    if num >= bf then
		flags[FLAGS[i]] = true
		num = num - bf
	    end
	end

	return flags
    end

    local returndata = {}
    while true do
	local line, err = server:receive()

	if line == 'END' then
	    break
	elseif string.sub(line, 1, 5) == 'VALUE' then
	    local key,flagstr,size,cas = string.match(line, 'VALUE (%S+) (%d+) (%d+)')

	    flags = extract_flags(flagstr)

	    local data = server:receive(size)

	    if flags.COMPRESSED and cache.compress_enabled then
		data = cache.decompress(data)
	    end

            if flags.SERIALISED then
                returndata[key] = cache.decode(data)
            else
                local ldata = tonumber(data) or toboolean(data) 

                if ldata == nil then
                    if data == 'nil' then
                        returndata[key] = nil
                    else
                        returndata[key] = data
                    end
                else
                    returndata[key] = ldata
                end
            end
	end
    end

    return returndata
end

local function _send(cache, key, str)
    local server = _select_server(cache, key)

    server:send(str .. "\r\n")
    local line, err = server:receive()
    
    if not err then return line end
end

local function _store(cache, op, key, value, expiry)
    local str
    local flags = 0

    if type(value) == 'table' then
	str = cache.encode(value)    
	-- TODO lookup rather than hard code 
        flags = flags + 4
    else
	str = tostring(value)
    end

    if cache.compress_enabled and string.len(str) > cache.compress_threshold then
	local cstr = cache.compress(str)

	if string.len(cstr) < (string.len(str) * 0.8) then
	    str = cstr

	    -- TODO lookup rather than hard code 
	    flags = flags + 2
	end
    end

    local len = string.len(str)

    expiry = expiry or 0

    local cmd = op .. ' ' .. key .. ' ' .. flags .. ' ' .. expiry .. ' ' .. len .. '\r\n' .. str

    local res = _send(cache, key, cmd)

    if res ~= 'STORED' then
	return false, res
    end

    return true
end

local function set(cache, key, value, expiry)
    return _store(cache, 'set', key, value, expiry)
end

local function add(cache, key, value, expiry)
    return _store(cache, 'add', key, value, expiry)
end

local function replace(cache, key, value, expiry)
    return _store(cache, 'replace', key, value, expiry)
end

local function get(cache, key)
    local dataset = _retrieve(cache, key, 'get ' .. key)
    return dataset[key]
end

local function delete(cache, key)
    local res = _send(cache, key, 'delete ' .. key)

    if res == 'NOT_FOUND' then
	return false
    end

    if res ~= 'DELETED' then
	return false, res
    end

    return true
end

local function incr(cache, key, val)
    val = val or 1
	
    local res = _send(cache, key, 'incr ' .. key .. ' ' .. val)

    if res == 'ERROR' or res == 'CLIENT_ERROR' then
        return false, res
    end

    return res
end

local function decr(cache, key, val)
    val = val or 1

    local res = _send(cache, key, 'decr ' .. key .. ' ' .. val)

    if res == 'ERROR' or res == 'CLIENT_ERROR' then
        return false, res
    end

    return res
end

local function stats(cache, key)
    local servers = {}

    key = key or ''

    if string.len(key) > 0 and not STATS_KEYS[key] then
	error(string.format("Unknown stats key '%s'", key))
    end

    for i,server in pairs(cache.servers) do
	server.socket:send('stats ' .. key .. '\r\n')

	local stats = {}

	while true do
	    local line, err = server.socket:receive()

	    if line == 'END' or line == 'ERROR' then
		break
	    end

	    local k,v = string.match(line, 'STAT (%S+) (%S+)')

	    if k then
		stats[k] = v
	    end
	end

	servers[server.name] = stats
    end

    return servers
end 

local function get_multi(cache, ...)
    local dataset = nil
    local arg = {...}

    if #(cache.servers) > 1 then
	dataset = {}

	for i,k in ipairs(arg or table.pack(...)) do
	    local data = _retrieve(cache, k, 'get ' .. k)
	    dataset[k] = data[k]
	end
    else
	local keys = table.concat(arg, ' ')
	dataset = _retrieve(cache, keys, 'get ' .. keys)
    end

    return dataset
end

local function flush_all(cache)
    local success = true

    for i,server in ipairs(cache.servers) do
	server.socket:send('flush_all\r\n')
	local res = assert(server.socket:receive())

	if res ~= 'OK' then
	    success = false
	end
    end

    return success
end

local function disconnect_all(cache)
    while true do
	local server = table.remove(cache.servers)

	if not server then
	    break
	end

	server.socket:close()
    end    
end

local function set_hash(cache, hashfunc)
    cache.hash = hashfunc
end

local function set_encode(cache, func)
    cache.encode = func
end

local function set_decode(cache, func)
    cache.decode = func
end

local function set_compress(cache, func)
    cache.compress = func
end

local function set_decompress(cache, func)
    cache.decompress = func
end

function _M.Connect(hostlist, port)
    local servers = {}

    if type(hostlist) == 'table' then
	for i,host in pairs(hostlist) do
	    local h, p

	    if type(host) == 'table' then
		h = host[1]
		p = host[2]
	    elseif type(host) == 'string' then
		h = host
	    elseif type(host) == 'number' then
		p = host
		h = nil
	    end

	    if not h then
		h = '127.0.0.1'
	    end

	    if not p then 
		p = 11211
	    end

	    local server = socket.connect(h, p)

	    if not server then
		warn('Could not connect to ' .. h .. ':' .. p)
	    else
		table.insert(servers, {socket = server, name = string.format('%s:%d', h, p)})
	    end
	end
    else
	local address = hostlist

	if type(address) == 'number' then
	    port = address
	    address = nil
	end

	if address == nil then
	    address = '127.0.0.1'
	end

	if port == nil then
	    port = 11211
	end

	local server = socket.connect(address, port)

	if not server then
	    warn('Could not connect to ' .. address .. ':' .. port)
	else
	    servers = {{socket = server, name = string.format('%s:%d', address, port)}}
	end
    end

    if #(servers) < 1 then
		return false
    end

    local cache = {
	servers = servers,

	set_hash = set_hash,
	set_encode = set_encode,
	set_decode = set_decode,
	set_decompress = set_decompress,
	set_compress = set_compress,

	compress_enabled = false,
	enable_compression = function(self, on)
	    self.compress_enabled = on
	end,

	hash = nil,
	encode = function()
	    error('No encode function set')
	end,

	decode = function()
	    error('No decode function set')
	end,

	compress = function()
	    error('No compress function set')
	end,

	decompress = function()
	    error('No decompress function set')
	end,

	-- 10K default
	compress_threshold = 10240,
	set_compress_threshold = function(self, threshold)
	    if threshold == nil then
		self:enable_compression(false)
	    else
		self.compress_threshold = threshold
	    end
	end,

	set = set,
	add = add,
	replace = replace,
	get = get,
	delete = delete,
	incr = incr,
	decr = decr,

	get_multi = get_multi,
	stats = stats,
	flush_all = flush_all,
	disconnect_all = disconnect_all,
    }

    return cache
end

function _M.New(hostlist, port)
    return _M.Connect(hostlist, port)
end

return _M
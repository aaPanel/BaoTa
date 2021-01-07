var bt = 
{
	os : 'Linux',
	check_ip : function(ip) //验证ip
	{
		var reg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
		return reg.test(ip);
	},
	check_ips : function(ips)//验证ip段
	{
		var reg = /^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}(\/\d{1,2})?$/;
		return reg.test(ip);
	},
	check_url : function(url) //验证url
	{
		var reg = /^((https|http|ftp|rtsp|mms)?:\/\/)[^\s]+/;
		return reg.test(url);
	},
	check_port : function(port)
	{
		var reg = /^([1-9]|[1-9]\d|[1-9]\d{2}|[1-9]\d{3}|[1-5]\d{4}|6[0-4]\d{3}|65[0-4]\d{2}|655[0-2]\d|6553[0-5])$/;
		return reg.test(port);
	},
	check_chinese : function(str)
	{
		var reg = /[\u4e00-\u9fa5]/;
		return reg.test(str);
	},
	check_domain : function(domain) //验证域名
	{	
        var reg = /^([\w\u4e00-\u9fa5\-\*]{1,100}\.){1,4}([\w\u4e00-\u9fa5\-]{1,24}|[\w\u4e00-\u9fa5\-]{1,24}\.[\w\u4e00-\u9fa5\-]{1,24})$/;
		return reg.test(bt.strim(domain));
	},
	check_img : function(fileName) //验证是否图片
	{
		var exts = ['jpg','jpeg','png','bmp','gif','tiff','ico'];
		var check =  bt.check_exts(fileName,exts);
		return check;
	},
	check_email:function(email){
		var reg = /\w[-\w.+]*@([A-Za-z0-9][-A-Za-z0-9]+\.)+[A-Za-z]{2,14}/;
		return reg.test(email);
	},
	check_phone:function(phone){
		var reg = /^1(3|4|5|6|7|8|9)\d{9}$/;
		return reg.test(phone);
	},
	check_zip : function(fileName)
	{
		var ext = fileName.split('.');
		var extName = ext[ext.length-1].toLowerCase();
		if( extName == 'zip') return 0;
		if( extName == 'rar') return 2;
		if( extName == 'gz' || extName == 'tgz') return 1;
		return -1;
	},
	check_text : function(fileName)
	{
		var exts = ['rar','zip','tar.gz','gz','iso','xsl','doc','xdoc','jpeg','jpg','png','gif','bmp','tiff','exe','so','7z','bz'];
		return bt.check_exts(fileName,exts)?false:true;
	},
	check_exts : function(fileName,exts)
	{
		var ext = fileName.split('.');
		if(ext.length < 2) return false;
		var extName = ext[ext.length-1].toLowerCase();		
		for(var i=0;i<exts.length;i++){
			if(extName == exts[i]) return true;
		}
		return false;
	},
	check_version:function(version,cloud_version){
		var arr1 = version.split('.'); //
		var arr2 = cloud_version.split('.');
		var leng = arr1.length>arr2.length?arr1.length:arr2.length;
		while(leng - arr1.length>0){
			arr1.push(0);
		}
		while(leng - arr2.length>0){
			arr2.push(0);
		}
		for (var i=0;i<leng;i++) {
			if(i==leng-1){				
				if(arr1[i]!=arr2[i]) return 2; //子版本匹配不上
			}			
			else{
				if(arr1[i]!=arr2[i]) return -1; //版本匹配不上
			}			
		}
		return 1; //版本正常
	},
	replace_all:function(str,old_data,new_data){
		var reg_str = "/("+old_data+"+)/g"
        var reg = eval(reg_str);      
		return str.replace(reg,new_data);
	},
	get_file_ext : function(fileName)
	{
		var text = fileName.split(".");
		var n = text.length-1;
		text = text[n];
		return text;
	},
	get_file_path : function(filename)
	{
		var arr = filename.split('/');
		path = filename.replace('/'+arr[arr.length-1],"");
		return path;
	},
	get_date:function(a){
		var dd = new Date();
		dd.setTime(dd.getTime() + (a == undefined || isNaN(parseInt(a)) ? 0 : parseInt(a)) * 86400000);
		var y = dd.getFullYear();
		var m = dd.getMonth() + 1;
		var d = dd.getDate();
		return y + "-" + (m < 10 ? ('0' + m) : m) + "-" + (d < 10 ? ('0' + d) : d);
    },
    get_form: function (select) {
        var sarr = $(select).serializeArray();
        var iarr = {}
        for (var i = 0; i < sarr.length; i++) {
            iarr[sarr[i].name] = sarr[i].value;
        }
        return iarr;
    },
	ltrim:function(str,r){
		var reg_str = "/(^\\"+r+"+)/g"
		var reg = eval(reg_str);
		str = str.replace(reg,"");
		return str;
	},
	rtrim:function(str,r){
		var reg_str = "/(\\"+r+"+$)/g"
		var reg = eval(reg_str);
		str = str.replace(reg,"");
		return str;
        },
        strim: function (str) {
            var reg_str = "/ /g"
            var reg = eval(reg_str);
            str = str.replace(reg, "");
            return str;
        },
	contains : function(str,substr){
		if(str){
			return str.indexOf(substr) >= 0;
		}
		return false;
	},
	format_size : function(bytes ,is_unit,fixed, end_unit) //字节转换，到指定单位结束 is_unit：是否显示单位  fixed：小数点位置 end_unit：结束单位
    {
        if (bytes == undefined) return 0;

		if(is_unit==undefined) is_unit = true;
		if(fixed==undefined) fixed = 2;
        if (end_unit == undefined) end_unit = '';
       
		if(typeof bytes == 'string') bytes = parseInt(bytes);
		var unit = [' B',' KB',' MB',' GB','TB'];
		var c = 1024;
		for(var i=0;i<unit.length;i++){
			var cUnit = unit[i];				
			if(end_unit)
			{
				if(cUnit.trim() == end_unit.trim())
				{
					var val = i == 0 ? bytes : fixed==0? bytes:bytes.toFixed(fixed)
					if(is_unit){
						return  val + cUnit;
					}
					else{
						val = parseFloat(val);		
						return val;					
					}
				}
			}
			else{
				if(bytes < c){
					var val = i == 0 ? bytes : fixed==0? bytes:bytes.toFixed(fixed)
					if(is_unit){
						return  val + cUnit;
					}
					else{
						val = parseFloat(val);		
						return val;
					}
				}
			}
	
			bytes /= c;
		}
	},
	format_data : function(tm,format)
	{
		if(format==undefined) format = "yyyy/MM/dd hh:mm:ss";
		tm  = tm.toString();
		if(tm.length > 10){
			tm = tm.substring(0,10);
		}	
		 var data = new Date(parseInt(tm) * 1000);
		 var o = {
		 "M+" : data.getMonth()+1, //month
		 "d+" : data.getDate(),    //day
		 "h+" : data.getHours(),   //hour
		 "m+" : data.getMinutes(), //minute
		 "s+" : data.getSeconds(), //second
		 "q+" : Math.floor((data.getMonth()+3)/3),  //quarter
		 "S" : data.getMilliseconds() //millisecond
		 }
		 if(/(y+)/.test(format)) format=format.replace(RegExp.$1,
		 (data.getFullYear()+"").substr(4 - RegExp.$1.length));
		 for(var k in o)if(new RegExp("("+ k +")").test(format))
		 format = format.replace(RegExp.$1,
		 RegExp.$1.length==1 ? o[k] : ("00"+ o[k]).substr((""+ o[k]).length));
		 
		return format;
	},
	format_path:function(path){
		var reg = /(\\)/g;
		path = path.replace(reg,'/');
		return path;
	},
	get_random : function(len)
	{
		len = len || 32;
		var $chars = 'AaBbCcDdEeFfGHhiJjKkLMmNnPpRSrTsWtXwYxZyz2345678'; // 默认去掉了容易混淆的字符oOLl,9gq,Vv,Uu,I1  
		var maxPos = $chars.length;
		var pwd = '';
		for (i = 0; i < len; i++) {
			pwd += $chars.charAt(Math.floor(Math.random() * maxPos));
		}
		return pwd;
	},
	refresh_pwd : function(length,obj)
	{
		if(obj==undefined) obj = 'MyPassword';
		var _input = $("#"+obj);
		if(_input.length>0){			
			 _input.val(bt.get_random(length))
		}
		else{
			$("."+obj).val(bt.get_random(length))
		}
	},
	get_random_num : function(min,max) //生成随机数
	{
		var range = max - min;
	    var rand = Math.random();
	    var num = min + Math.round(rand * range); //四舍五入
	    return num;
	},
	/**
     * @description 设置本地存储，local和session
     * @param {String} type 存储类型，可以为空，默认为session类型。
     * @param {String} key 存储键名
     * @param {String} val 存储键值
     * @return 无返回值
     */
    set_storage: function (type, key, val) {
        if (type != "local" && type != "session") val = key, key = type, type = 'local';
        window[type + 'Storage'].setItem(key, val);
    },


    /**
     * @description 获取本地存储，local和session
     * @param {String} type 存储类型，可以为空，默认为session类型。
     * @param {String} key 存储键名
     * @return {String} 返回存储键值
     */
    get_storage: function (type, key) {
        if (type != "local" && type != "session") key = type, type = 'local';
        return window[type + 'Storage'].getItem(key);
    },

    /**
     * @description 删除指定本地存储，local和session
     * @param {String} type 类型，可以为空，默认为session类型。
     * @param {String} key 键名
     * @return 无返回值
     */
    remove_storage: function (type, key) {
        if (type != "local" && type != "session") key = type, type = 'local';
        window[type + 'Storage'].removeItem(key);
    },

    /**
     * @description 删除指定类型的所有存储信息储，local和session
     * @param {String} type 类型，可以为空，默认为session类型。
     * @return 无返回值
     */
    clear_storage: function (type) {
        if (type != "local" && type != "session") key = type, type = 'local';
        window[type + 'Storage'].clear();
    },
	set_cookie : function(key,val,time){
		if(time != undefined){
			var exp = new Date();
			exp.setTime(exp.getTime() + time);
			time = exp.toGMTString();
		}else{
			var Days = 30;
			var exp = new Date();
			exp.setTime(exp.getTime() + Days*24*60*60*1000);
			time = exp.toGMTString();
		}
		document.cookie = key + "="+ escape (val) + ";expires=" + time;
	},
	get_cookie : function(key){
		var arr,reg=new RegExp("(^| )"+key+"=([^;]*)(;|$)");
		if(arr=document.cookie.match(reg))
		{
			var val = unescape(arr[2]);
			return val== 'undefined'?'':val;
		}
		else{
			return null;
		}
	},
	clear_cookie:function(key){
	  this.set_cookie(key,'',new Date());
	},
	select_path:function(id){
		_this = this;
		_this.set_cookie("SetName", "");
		var loadT = bt.open({
			type: 1,
			area: "650px",
			title: lan.bt.dir,
			closeBtn: 2,
			shift: 5,
			content: "<div class='changepath'><div class='path-top'><button type='button' id='btn_back' class='btn btn-default btn-sm'><span class='glyphicon glyphicon-share-alt'></span> "+lan.public.return+"</button><div class='place' id='PathPlace'>"+lan.bt.path+"：<span></span></div></div><div class='path-con'><div class='path-con-left'><dl><dt id='changecomlist' >"+lan.bt.comp+"</dt></dl></div><div class='path-con-right'><ul class='default' id='computerDefautl'></ul><div class='file-list divtable'><table class='table table-hover' style='border:0 none'><thead><tr class='file-list-head'><th width='40%'>"+lan.bt.filename+"</th><th width='20%'>"+lan.bt.etime+"</th><th width='10%'>"+lan.bt.access+"</th><th width='10%'>"+lan.bt.own+"</th><th width='10%'></th></tr></thead><tbody id='tbody' class='list-list'></tbody></table></div></div></div></div><div class='getfile-btn' style='margin-top:0'><button type='button' class='btn btn-default btn-sm pull-left' onclick='CreateFolder()'>"+lan.bt.adddir+"</button><button type='button' class='btn btn-danger btn-sm mr5' onclick=\"layer.close(getCookie('ChangePath'))\">"+lan.public.close+"</button> <button type='button' id='bt_select' class='btn btn-success btn-sm' >"+lan.bt.path_ok+"</button></div>"
        });
        _this.set_cookie('ChangePath', loadT.form);
		setTimeout(function(){			
			$('#btn_back').click(function(){
				var path = $("#PathPlace").find("span").text();			
				path = bt.rtrim(bt.format_path(path),'/');						
				var back_path = bt.get_file_path(path);
				get_file_list(back_path);
			})
			//选择
			$('#bt_select').click(function(){						
				var path = bt.format_path($("#PathPlace").find("span").text());
                path = bt.rtrim(path, '/');
				$("#"+id).val(path);
				$("."+id).val(path);
				loadT.close();
			})
		},100);
		var paths = $("#" + id).val();
		if($('#defaultPath').length > 0 && $("#" + id).parents('.tab-body').length > 0){
			paths = $('#defaultPath').text();
		}
		get_file_list(paths);
		function get_file_list(path)
        {
            bt.send('GetDir', 'files/GetDir', { path: path, disk: true }, function (rdata) {
                var d = '',a='';                
				if(rdata.DISK != undefined) {
					for(var f = 0; f < rdata.DISK.length; f++) {
						a += "<dd class=\"bt_open_dir\" path =\""+rdata.DISK[f].path+"\"><span class='glyphicon glyphicon-hdd'></span>&nbsp;" + rdata.DISK[f].path + "</dd>"
					}
					$("#changecomlist").html(a)
				}
				for(var f = 0; f < rdata.DIR.length; f++) {
					var g = rdata.DIR[f].split(";");
					var e = g[0];
					if(e.length > 20) {
						e = e.substring(0, 20) + "..."
					}
					if(isChineseChar(e)) {
						if(e.length > 10) {
							e = e.substring(0, 10) + "..."
						}
					}
					d += "<tr><td class=\"bt_open_dir\" path =\"" + rdata.PATH + "/" + g[0] + "\"  title='" + g[0] + "'><span class='glyphicon glyphicon-folder-open'></span>" + e + "</td><td>" + bt.format_data(g[2]) + "</td><td>" + g[3] + "</td><td>" + g[4] + "</td><td><span class='delfile-btn' onclick=\"NewDelFile('" + rdata.PATH + "/" + g[0] + "')\">X</span></td></tr>"
				}
				
				if(rdata.FILES != null && rdata.FILES != "") {
					for(var f = 0; f < rdata.FILES.length; f++) {
						var g = rdata.FILES[f].split(";");
						var e = g[0];
						if(e.length > 20) {
							e = e.substring(0, 20) + "..."
						}
						if(isChineseChar(e)) {
							if(e.length > 10) {
								e = e.substring(0, 10) + "..."
							}
						}
						d += "<tr><td title='" + g[0] + "'><span class='glyphicon glyphicon-file'></span>" + e + "</td><td>" + bt.format_data(g[2]) + "</td><td>" + g[3] + "</td><td>" + g[4] + "</td><td></td></tr>"
					}
				}
				
				$(".default").hide();
				$(".file-list").show();
				$("#tbody").html(d);
				if(rdata.PATH.substr(rdata.PATH.length - 1, 1) != "/") {
					rdata.PATH += "/"
				}
				$("#PathPlace").find("span").html(rdata.PATH);
				
				$('.bt_open_dir').click(function(){	
					get_file_list($(this).attr('path'));
				})
			})
        }


        function ActiveDisk() {
            var a = $("#PathPlace").find("span").text().substring(0, 1);
            switch (a) {
                case "C":
                    $(".path-con-left dd:nth-of-type(1)").css("background", "#eee").siblings().removeAttr("style");
                    break;
                case "D":
                    $(".path-con-left dd:nth-of-type(2)").css("background", "#eee").siblings().removeAttr("style");
                    break;
                case "E":
                    $(".path-con-left dd:nth-of-type(3)").css("background", "#eee").siblings().removeAttr("style");
                    break;
                case "F":
                    $(".path-con-left dd:nth-of-type(4)").css("background", "#eee").siblings().removeAttr("style");
                    break;
                case "G":
                    $(".path-con-left dd:nth-of-type(5)").css("background", "#eee").siblings().removeAttr("style");
                    break;
                case "H":
                    $(".path-con-left dd:nth-of-type(6)").css("background", "#eee").siblings().removeAttr("style");
                    break;
                default:
                    $(".path-con-left dd").removeAttr("style")
            }
        }
	},
	show_confirm : function(title, msg, fun, error) 
	{
		if(error == undefined) {
			error = ""
		}
		var d = Math.round(Math.random() * 9 + 1);
		var c = Math.round(Math.random() * 9 + 1);
		var e = "";
		e = d + c;
		sumtext = d + " + " + c;
		bt.set_cookie("vcodesum", e);
		var mess = layer.open({
			type: 1,
			title: title,
			area: "365px",
			closeBtn: 2,
			shadeClose: true,
			content: "<div class='bt-form webDelete pd20 pb70'><p style='font-size:13px;word-break: break-all;margin-bottom: 5px;'>" + msg + "</p>" + error + "<div class='vcode'>"+lan.bt.cal_msg+"<span class='text'>" + sumtext + "</span>=<input type='number' id='vcodeResult' value=''></div><div class='bt-form-submit-btn'><button type='button' class='btn btn-danger btn-sm bt-cancel'>"+lan.public.cancel+"</button> <button type='button' id='toSubmit' class='btn btn-success btn-sm' >"+lan.public.ok+"</button></div></div>"
		});
		$("#vcodeResult").focus().keyup(function(a) {
			if(a.keyCode == 13) {
				$("#toSubmit").click()
			}
		});
		$(".bt-cancel").click(function(){
			layer.close(mess);
		});
		$("#toSubmit").click(function() {
			var a = $("#vcodeResult").val().replace(/ /g, "");
			if(a == undefined || a == "") {
				layer.msg(lan.bt.cal_err);
				return
			}
			if(a != bt.get_cookie("vcodesum")) {
				layer.msg(lan.bt.cal_err);
				return
			}
			layer.close(mess);
			fun();
		})
	},
	to_login:function()
	{
		layer.confirm('您的登陆状态已过期，请重新登陆!',{title:'会话已过期',icon:2,closeBtn: 1,shift: 5},function(){
			location.reload();
		});
	},
	do_login:function()
	{
		bt.confirm({msg:lan.bt.loginout},function(){
			window.location.href = "/login?dologin=True"
		})
	},
	send : function(response,module,data,callback,sType)
	{
		if(sType==undefined) sType=1;
		
		module = module.replace('panel_data','data');
		sType=1;
		var str = bt.get_random(16);
		console.time(str);
		if(!response) alert(lan.get('lack_param',['response']));
		modelTmp = module.split('/')
		if(modelTmp.length<2)   alert(lan.get('lack_param',['s_module','action']));	
		if(bt.os == 'Linux' && sType === 0)
		{		
			socket.on(response,function(rdata){
				socket.removeAllListeners(response);
				var rRet = rdata.data;
				if(rRet.status===-1){
					bt.to_login();
					return;
				}
				console.timeEnd(str);
			  	if(callback) callback(rRet);
			});
			if(!data) data = {};
			data = bt.linux_format_param(data);
			data['s_response'] = response;
			data['s_module'] = modelTmp[0];
			data['action'] = modelTmp[1];
			socket.emit('panel',data)
		}
		else{
			data = bt.win_format_param(data);
			var url = '/' + modelTmp[0] + '?action=' + modelTmp[1];
            $.post(url, data, function (rdata) {

                //会话失效时自动跳转到登录页面
                if (typeof (rdata) == 'string') {
                    if ((rdata.indexOf('/static/favicon.ico') != -1 && rdata.indexOf('/static/img/qrCode.png') != -1) || rdata.indexOf('<!DOCTYPE html>') === 0) {
                        window.location.href = "/login"
                        return
                    }
                }
                
				if(callback) callback(rdata);
            }).error(function (e, f) {
                //console.log(e,f)
				if(callback) callback('error');
			});
		}
	},
	linux_format_param : function(param)
	{		
		if(typeof param == 'string')
		{
			var data= {};
			arr = param.split('&');		
			var reg = /(^[^=]*)=(.*)/;
			for (var i=0;i<arr.length;i++) {
				var tmp = arr[i].match(reg);
				if(tmp.length>=3) data[tmp[1]] =  tmp[2]=='undefined'?'': tmp[2];			
			}
			return data;	
		}
		return param;
	},
	win_format_param : function(param)
	{
		if(typeof data == 'object')
		{
			var data = '';
			for(var key in param){
			 	data+=key+'='+param[key]+'&';
			}
			if(data.length>0) data = data.substr(0,data.length-1);
			return data;
		}
		return param;
	},
	msg : function(config)
	{		
		var btns = [];
		var btnObj =  {						
			title:config.title?config.title:false,						
			shadeClose: config.shadeClose?config.shadeClose:true,
			closeBtn: config.closeBtn?config.closeBtn:0,	
			scrollbar:true,
			shade:0.3,
		};
		if(!config.hasOwnProperty('time')) config.time = 2000;		
		if(typeof config.msg=='string' && bt.contains(config.msg,'ERROR')) config.time = 0;
		
        if (config.hasOwnProperty('icon')) {
            if (typeof config.icon == 'boolean') config.icon = config.icon ? 1 : 2;
        }
        else if (config.hasOwnProperty('status')) {
            config.icon = config.status ? 1 : 2;
            if (!config.status) {
                btnObj.time = 0;
            }
        }
		if(config.icon) btnObj.icon = config.icon;
		btnObj.time = config.time;
		var msg = ''
		if(config.msg) msg += config.msg;
		if(config.msg_error) msg+=config.msg_error;
		if(config.msg_solve) msg+=config.msg_solve;
		
		layer.msg(msg,btnObj);	
	},
	confirm : function(config,callback,callback1){
		var btnObj =  {						
			title:config.title?config.title:false,
			time : config.time?config.time:0,					
			shadeClose: config.shadeClose?config.shadeClose:true,
			closeBtn: config.closeBtn?config.closeBtn:2,	
			scrollbar:true,
			shade:0.3,
			icon:3,
			cancel: (config.cancel?config.cancel:function(){})
		};
		layer.confirm(config.msg, btnObj, function(index){
		 	if(callback) callback(index);
		},function(index){
			if(callback1) callback1(index);
		});
	},
	load : function(msg)  
	{
		if(!msg) msg = lan.public.the;
		var loadT = layer.msg(msg,{icon:16,time:0,shade: [0.3, '#000']});
		var load = {
			form : loadT,
			close:function(){
				layer.close(load.form);
			}
		}
		return load;
	},
	open: function(config)
	{
		config.closeBtn = 2;
		var loadT = layer.open(config);
		var load = {
			form : loadT,
			close:function(){
				layer.close(load.form);
			}
		}		
		return load;
	},
	closeAll : function(){
		layer.closeAll();
	},
	check_select:function(){
        setTimeout(function () {
            var num = $('input[type="checkbox"].check:checked').length;
            //console.log(num);
            if (num == 1) {
                $('button[batch="true"]').hide();
                $('button[batch="false"]').show();
            }else if (num>1){
                $('button[batch="true"]').show();
                $('button[batch="false"]').show();
			}else{
                $('button[batch="true"]').hide();
                $('button[batch="false"]').hide();
			}
		},5)
	},
	render_help:function(arr){
		var html = '<ul class="help-info-text c7">';
		for(var i = 0;i<arr.length;i++){	
			html +='<li>'+arr[i]+'</li>';
		}
		html += '</ul>';
		return html;
	},
	render_ps:function(item){		
		var	html='<p class=\'p1\'>'+item.title+'</p>';
		for(var i = 0;i<item.list.length;i++){	
			html +='<p><span>'+item.list[i].title+'：</span><strong>' + item.list[i].val + '</strong></p>';
		}
		html+='<p style="margin-bottom: 19px; margin-top: 11px; color: #666"></p>';
		return html;
	},
    render_table: function (obj, arr, append) { //渲染表单表格
            var html = '';
            for (var key in arr) {
                html += '<tr><th>' + key + '</th>'
                if (typeof arr[key] != 'object') {
                    html += '<td>' + arr[key] + '</td>';
                }
                else {
                    for (var i = 0; i < arr[key].length; i++) {
                        html += '<td>' + arr[key][i] + '</td>';
                    }
                }
                html += '</tr>'
            }
            if (append) {
                $('#' + obj).append(html)
            }
            else {
                $('#' + obj).html(html);
            }
        },

	fixed_table:function(name){
	
		$('#'+name).parent().bind('scroll',function(){	
			var scrollTop = this.scrollTop;
			$(this).find("thead").css({"transform":"translateY("+scrollTop+"px)","position":"relative","z-index":"1"});
		});
	},
	render_tab:function(obj,arr){
		var _obj = $('#'+obj).addClass("tab-nav");
		for(var i = 0;i<arr.length;i++){
			var item = arr[i];
			var _tab = $('<span '+(item.on?'class="on"':'')+'>'+item.title+'</span>')
			if(item.callback){
				_tab.data('callback',item.callback);
				_tab.click(function(){
					$('#'+obj).find('span').removeClass('on');
					$(this).addClass('on');
					var _contents =$('.tab-con');
					_contents.html('');					
					$(this).data('callback')(_contents);					
				})
			}
			_obj.append(_tab);
		}		
	},
    render_form_line: function (item, bs, form) {
        var clicks = [], _html = '', _hide = '', is_title_css = ' ml0';
        if (!bs) bs = '';
        if (item.title) {
            _html += '<span class="tname">' + item.title + '</span>';
            is_title_css = '';
        }
        _html += "<div class='info-r "+ item.class +" "+ is_title_css + "'>";

        var _name = item.name;
        var _placeholder = item.placeholder;
        if (item.items && item.type != 'select') {
            for (var x = 0; x < item.items.length; x++) {
                var _obj = item.items[x];
                if (!_name && !_obj.name) {
                    alert('缺少必要参数name');
                    return;
                }
                if (_obj.hide) continue;
                if (_obj.name) _name = _obj.name;
                if (_obj.placeholder) _placeholder = _obj.placeholder;
                if (_obj.title) _html += '<div class="inlineBlock mr5"><span class="mr5">' + _obj.title + "</span>  ";
                switch (_obj.type) {
                    case 'select':
                        var _width = _obj.width ? _obj.width : '100px';
                        _html += '<select ' + (_obj.disabled ? 'disabled' : '') + ' class="bt-input-text mr5 ' + _name + bs + '" name="' + _name + '" style="width:' + _width + '">';
                        for (var j = 0; j < _obj.items.length; j++) {
                            _html += '<option ' + (_obj.value == _obj.items[j].value ? 'selected' : '') + ' value="' + _obj.items[j].value + '">' + _obj.items[j].title + '</option>';
                        }
                        _html += '</select>';
                        break;
                    case 'textarea':
                        var _width = _obj.width ? _obj.width : '330px';
                        var _height = _obj.height ? _obj.height : '100px';
                        _html += '<textarea class="bt-input-text mr20 ' + _name + bs + '" name="' + _name + '" style="width:' + _width + ';height:' + _height + ';line-height:22px">' + (_obj.value ? _obj.value : '') + '</textarea>';
                        if (_placeholder) _html += '<div class="placeholder c9" style="top: 15px; left: 15px; display: block;">' + _placeholder + '</div>';
                        break;
                    case 'button':
                        var _width = _obj.width ? _obj.width : '330px';
                        _html += '<button name=\'' + _name + '\' class="btn btn-success btn-sm mr5 ml5 ' + _name + bs +' '+ (_obj.class?_obj.class:'') + '">' + _obj.text + '</button>';
                        break;
                    case 'radio':
                        var _v = _obj.value === true ? 'checked' : ''
                        _html += '<input type="radio" class="' + _name + '" id="' + _name + '" name="' + _name + '"  ' + _v + '><label class="mr20" for="' + _name + '" style="font-weight:normal">' + _obj.text + '</label>'
                        break;
                    case 'checkbox':
                        var _v = _obj.value === true ? 'checked' : ''
                        _html += '<input type="checkbox" class="' + _name + '" id="' + _name + '" name="' + _name + '"  ' + _v + '><label class="mr20" for="' + _name + '" style="font-weight:normal">' + _obj.text + '</label>'
                        break;
                    case 'number':
                        var _width = _obj.width ? _obj.width : '330px';
                        _html += "<input name='" + _name + "' " + (_obj.disabled ? 'disabled' : '') + " class='bt-input-text mr5 " + _name + bs + "' " + (_placeholder ? ' placeholder="' + _placeholder + '"' : "") + " type='number' style='width:" + _width + "' value='" + (_obj.value ? _obj.value : '0') + "' />";
                        _html += _obj.unit ? _obj.unit : '';
                        break;
                    case 'password':
                        var _width = _obj.width ? _obj.width : '330px';
                        _html += "<input name='" + _name + "' " + (_obj.disabled ? 'disabled' : '') + " class='bt-input-text mr5 " + _name + bs + "' " + (_placeholder ? ' placeholder="' + _placeholder + '"' : "") + " type='password' style='width:" + _width + "' value='" + (_obj.value ? _obj.value : '') + "' />";
                        break;
                    case 'div':
                    	var _width = _obj.width ? _obj.width : '330px';
                        var _height = _obj.height ? _obj.height : '100px';
                        _html += '<div class="bt-input-text ace_config_editor_scroll mr20 ' + _name + bs + '" name="' + _name + '" style="width:' + _width + ';height:' + _height + ';line-height:22px">' + (_obj.value ? _obj.value : '') + '</div>';
                        if (_placeholder) _html += '<div class="placeholder c9" style="top: 15px; left: 15px; display: block;">' + _placeholder + '</div>';
                        break;
                    case 'switch':
                        _html += '<div style="display: inline-block;vertical-align: middle;">\
                            <input type="checkbox" id="' + _name + '" ' + (_obj.value==true?'checked':'') + ' class="btswitch btswitch-ios">\
                            <label class="btswitch-btn" for="' + _name + '" style="margin-top:5px;"></label>\
                        </div>';
                        break;
                    default:
                        var _width = _obj.width ? _obj.width : '330px';

                        _html += "<input name='" + _name + "' " + (_obj.disabled ? 'disabled' : '') + " class='bt-input-text mr5 " + _name + bs + "' " + (_placeholder ? ' placeholder="' + _placeholder + '"' : "") + " type='text' style='width:" + _width + "' value='" + (_obj.value ? _obj.value : '') + "' />";
                        break;
                }
                if (_obj.title) _html += '</div>';
                if (_obj.callback) clicks.push({ bind: _name + bs, callback: _obj.callback });
                if (_obj.event) {
                    _html += '<span data-id="' + _name + bs + '" class="glyphicon cursor mr5 ' + _obj.event.css + ' icon_' + _name + bs + '" ></span>';
                    if (_obj.event.callback) clicks.push({ bind: 'icon_' + _name + bs, callback: _obj.event.callback });
                }
                if (_obj.ps) _html += " <span class='c9 mt10'>" + _obj.ps + "</span>";
                if (_obj.ps_help) _html += "<span class='bt-ico-ask "+_obj.name+"_help' tip='"+_obj.ps_help+"'>?</span>";
            }
            if (item.ps) _html += " <span class='c9 mt10'>" + item.ps + "</span>";
        }
        else {
            switch (item.type) {
                case 'select':
                    var _width = item.width ? item.width : '100px';
                    _html += '<select ' + (item.disabled ? 'disabled' : '') + ' class="bt-input-text mr5 ' + _name + bs + '" name="' + _name + '" style="width:' + _width + '">';
                    for (var j = 0; j < item.items.length; j++) {
                        _html += '<option ' + (item.value == item.items[j].value ? 'selected' : '') + ' value="' + item.items[j].value + '">' + item.items[j].title + '</option>';
                    }
                    _html += '</select>';
                    break;
                case 'button':
                    var _width = item.width ? item.width : '330px';
                    _html += '<button name=\'' + _name + '\' class="btn btn-success btn-sm mr5 ml5 ' + _name + bs + '">' + item.text + '</button>';
                    break;
                case 'number':
                    var _width = item.width ? item.width : '330px';
                    _html += "<input name='" + item.name + "' " + (item.disabled ? 'disabled' : '') + " class='bt-input-text mr5 " + _name + bs + "' " + (_placeholder ? ' placeholder="' + _placeholder + '"' : "") + " type='number' style='width:" + _width + "' value='" + (item.value ? item.value : '0') + "' />";
                    break;
                case 'checkbox':
                    var _v = item.value === true ? 'checked' : ''
                    _html += '<input type="checkbox" class="' + _name + '" id="' + _name + '" name="' + _name + '"  ' + _v + '><label class="mr20" for="' + _name + '" style="font-weight:normal">' + item.text + '</label>'
                    break;
                case 'password':
                    var _width = item.width ? item.width : '330px';
                    _html += "<input name='" + _name + "' " + (item.disabled ? 'disabled' : '') + " class='bt-input-text mr5 " + _name + bs + "' " + (_placeholder ? ' placeholder="' + _placeholder + '"' : "") + " type='password' style='width:" + _width + "' value='" + (item.value ? item.value : '') + "' />";
                    break;
                 case 'textarea':
                    var _width = item.width ? item.width : '330px';
                    var _height = item.height ? item.height : '100px';
                    _html += '<textarea class="bt-input-text mr20 ' + _name + bs + '"  ' + (item.disabled ? 'disabled' : '')+'  name="' + _name + '" style="width:' + _width + ';height:' + _height + ';line-height:22px">' + (item.value ? item.value : '') + '</textarea>';
                    if (_placeholder) _html += '<div class="placeholder c9" style="top: 15px; left: 15px; display: block;">' + _placeholder + '</div>';
                    break;
                default:
                    var _width = item.width ? item.width : '330px';

                    _html += "<input name='" + item.name + "' " + (item.disabled ? 'disabled' : '') + " class='bt-input-text mr5 " + _name + bs + "' " + (_placeholder ? ' placeholder="' + _placeholder + '"' : "") + " type='text' style='width:" + _width + "' value='" + (item.value ? item.value : '') + "' />";
                    break;
            }
            if (item.callback) clicks.push({ bind: _name + bs, callback: item.callback });
            if (item.ps) _html += " <span class='c9 mt10 mr5'>" + item.ps + "</span>";
        }
        _html += '</div>';
        if (!item.class) item.class = '';
        if (item.hide) _hide = 'style="display:none;"'
        _html = '<div class="line ' + item.class + '" ' + _hide + '>' + _html + '</div>'

        if (form) {
            form.append(_html)
            bt.render_clicks(clicks)
        }
        return { html: _html, clicks: clicks, data: item };
    },
	render_form:function(data,callback){
			if(data){		
			var bs = '_' + bt.get_random(6);
			var _form = $("<div data-id='form"+bs+"' class='bt-form bt-form pd20 pb70 "+ (data.class?data.class:'')  +"'></div>");
			var _lines = data.list; 
			var clicks = [];
			for (var i = 0; i < _lines.length; i++)
            {
                var _obj = _lines[i]
                if (_obj.hasOwnProperty("html")) {
                    _form.append(_obj.html)
                }
                else {
                    var rRet = bt.render_form_line(_obj, bs);
                    for (var s = 0; s < rRet.clicks.length; s++) clicks.push(rRet.clicks[s]);
                    _form.append(rRet.html);	
                }			
			}
			
			var _btn_html = '';
			for (var i = 0;i<data.btns.length;i++) {
				var item = data.btns[i];
				var css = item.css?item.css:'btn-danger';
				_btn_html += "<button type='button' class='btn btn-sm "+css+" " + item.name + bs + "' >"+item.title+"</button>";
				clicks.push({bind:item.name + bs,callback:item.callback});
			}
			_form.append("<div class='bt-form-submit-btn'>" + _btn_html + "</div>");				
			var loadOpen = bt.open({
				type: 1,
				skin: data.skin,
				area: data.area,
				title: data.title,
				closeBtn: 2,
				content:_form.prop("outerHTML"),
                end: data.end ? data.end : false
			})				
			setTimeout(function(){
				bt.render_clicks(clicks,loadOpen,callback);			
			},100)
		}
		return bs;
	},
	render_clicks:function(clicks,loadOpen,callback){
		for(var i =0;i<clicks.length;i++){
			var obj= clicks[i];			
			
			var btn = $('.'+obj.bind);
			btn.data('item',obj);
			btn.data('load',loadOpen);
			btn.data('callback',callback);
			
			switch(btn.prop("tagName")){
				case 'SPAN':
					btn.click(function(){
						var _obj =  $(this).data('item');
						_obj.callback($(this).attr('data-id'));							
					})
					break;
				case 'SELECT':
					btn.change(function(){
						var _obj =  $(this).data('item');
						_obj.callback($(this));	
					})
					break;
				case 'TEXTAREA':
				case 'INPUT':
                case 'BUTTON':      
                    
                    if (btn.prop("tagName") == 'BUTTON' || btn.attr("type") == 'checkbox')
					{
						btn.click(function(){							
							var _obj =  $(this).data('item');
							var load = $(this).data('load');
							var _callback =  $(this).data('callback');
							var parent = $(this).parents('.bt-form');	
							
                            if (_obj.callback) {
                            
								var data = {};
								parent.find('*').each(function(index,_this){
                                    var _name = $(_this).attr('name');
                               
									if(_name){
										if($(_this).attr('type')=='checkbox' || $(_this).attr('type')=='radio'){
											data[_name] = $(_this).prop('checked');
										}else{
											data[_name] = $(_this).val();
										}										
									}
								})	
								_obj.callback(data,load,function(rdata){
									if(_callback) _callback(rdata);
								});
							}
							else{									
								load.close();
							}
						})
					}
                    else {
                        if (btn.attr("type") == 'radio') {
                            btn.click(function () {
                                var _obj = $(this).data('item');
                                _obj.callback($(this))
                            })
                        }
                        else {
                            btn.on('input', function () {
                                var _obj = $(this).data('item');
                                _obj.callback($(this));
                            })		
                        }									
					}					
					break;
			}					
		}	
	},
	render:function(obj) //columns 行
	{
		if(obj.columns)
		{
			var checks = {};
			$(obj.table).html('');
			var thead = '<thead><tr>';			
			for (var h=0;h < obj.columns.length;h++) {
				var item = obj.columns[h];
				if(item){									
					thead += '<th';
					if(item.width) thead += ' width="'+item.width+'" ';
					if(item.align || item.sort){
						thead+=' style="';
						if(item.align) thead += 'text-align:'+item.align+';';
						if(item.sort) thead += item.sort?'cursor: pointer;':'';
						thead+='"';
					}				
					if(item.type=='checkbox'){
						thead += '><input  class="check"  onclick="bt.check_select();" type="checkbox">';			
					}
					else{
						thead += '>'+item.title;
					}
					if(item.sort) {					
						checks[item.field] = item.sort;
						thead += ' <span data-id="'+item.field+'" class="glyphicon glyphicon-triangle-top" style="margin-left:5px;color:#bbb"></span>';					
					}
					if(item.help) thead+='<a href="'+item.help+'" class="bt-ico-ask" target="_blank" title="点击查看说明">?</a>';
					
					thead += '</th>';	
				}
			}	
			thead += '</tr></thead>';
			var _tab = $(obj.table).append(thead);			
			if(obj.data.length>0){
				for (var i=0;i < obj.data.length;i++) {
					var val = obj.data[i];
					var tr = $('<tr></tr>');		
					for (var h=0;h < obj.columns.length;h++) {
						var item = obj.columns[h];	
						if(item){		
							var _val = val[item.field];
							if(typeof _val =='string') _val= _val.replace(/\\/g,'');
							if(item.hasOwnProperty('templet')) _val = item.templet(val);	
							if(item.type=='checkbox') _val = '<input value='+val[item.field]+'  class="check" onclick="bt.check_select();" type="checkbox">';
							var td = '<td ';
							if(item.align){
								td+='style="';
								if(item.align) td+='text-align:'+item.align;
								td+='"';
							}
							if(item.index) td +='data-index="' + i + '" '
							td+='>';
							tr.append(td +_val+'</td>');
							tr.data('item',val);
							_tab.append(tr);
						}
					}
				}
			}
			else{
				_tab.append("<tr><td colspan='"+obj.columns.length+"'>"+lan.bt.no_data+"</td></tr>");
			}
			$(obj.table).find('.check').click(function(){
				var checked = $(this).prop('checked');				
				if($(this).parent().prop('tagName')=='TH'){
					$('.check').prop('checked',checked?'checked':'');					
				}				
			})
            var asc = 'glyphicon-triangle-top';
            var desc = 'glyphicon-triangle-bottom';

            var orderby = bt.get_cookie('order');
            if (orderby != undefined) {
                var arrys = orderby.split(' ')
                if (arrys.length == 2) {
                    if (arrys[1] == 'asc') {
                        $(obj.table).find('th span[data-id="' + arrys[0] + '"]').removeClass(desc).addClass(asc);
                    }
                    else {
                        $(obj.table).find('th span[data-id="' + arrys[0] + '"]').removeClass(asc).addClass(desc);
                    }
                }
            }

            $(obj.table).find('th').data('checks', checks).click(function () {
                var _th = $(this);
                var _checks = _th.data('checks');
                var _span = _th.find('span');
                if (_span.length > 0) {
                    var or = _span.attr('data-id');
                    if (_span.hasClass(asc)) {
                        bt.set_cookie('order', or + ' desc');
                        $(obj.table).find('th span[data-id="' + or + '"]').removeClass(asc).addClass(desc);
                        _checks[or]();

                    } else if (_span.hasClass(desc)) {
                        bt.set_cookie('order', or + ' asc');
                        $(obj.table).find('th span[data-id="' + arrys[0] + '"]').removeClass(desc).addClass(asc);
                        _checks[or]();
                    }
                }
            })
		}
		return _tab;
	},
	// ACE编辑配置文件
	aceEditor:function(obj){
		var aEditor = {
				ACE:ace.edit(obj.el,{
					theme: "ace/theme/chrome", //主题
					mode: "ace/mode/"+ (obj.mode || 'nginx'), // 语言类型
					wrap: true,
					showInvisibles:false,
					showPrintMargin: false,
					showFoldWidgets:false,
					useSoftTabs:true,
					tabSize:2,
					showPrintMargin: false,
					readOnly:false
				}),
				path:obj.path,
				content:'',
				saveCallback:obj.saveCallback
			},_this = this;
			$('#' + obj.el).css('fontSize','12px');
			aEditor.ACE.commands.addCommand({
				name: '保存文件',
				bindKey: {win: 'Ctrl-S',mac: 'Command-S'},
				exec: function (editor) {
					_this.saveEditor(aEditor,aEditor.saveCallback);
				},
				readOnly: false // 如果不需要使用只读模式，这里设置false
			});
			if(obj.path != undefined){
				var loadT = layer.msg(lan.soft.get_config,{icon:16,time:0,shade: [0.3, '#000']})
				bt.send('GetFileBody','files/GetFileBody',{path:obj.path},function(res){
					layer.close(loadT);
					if(!res.status){
						bt.msg(res);
						return false;
					}
					aEditor.ACE.setValue(res.data); //设置配置文件内容
					aEditor.ACE.moveCursorTo(0, 0); //设置文件光标位置
					aEditor.ACE.resize();
				});
			}else if(obj.content != undefined){
				aEditor.ACE.setValue(obj.content);
				aEditor.ACE.moveCursorTo(0, 0); //设置文件光标位置
				aEditor.ACE.resize();
			}
		return aEditor;
	},
	// 保存编辑器文件
	saveEditor:function(ace){
		if(!ace.saveCallback){
			var loadT = bt.load(lan.soft.the_save);
			bt.send('SaveFileBody','files/SaveFileBody',{data:ace.ACE.getValue(),path:ace.path,encoding:'utf-8'},function(rdata){
				loadT.close();
				bt.msg(rdata);
			});
		}else{
			ace.saveCallback(ace.ACE.getValue());
		}
	},
    /**
     * @description 遍历数组和对象
     * @param {Array|Object} obj 遍历数组|对象
     * @param {Function} fn 遍历对象或数组
     * @return 当前对象
     */
    each: function (obj, fn) {
        var key, that = this;
        if (typeof fn !== 'function') return that;
        obj = obj || [];
        if (obj.constructor === Object) {
            for (key in obj) {
                if (fn.call(obj[key], key, obj[key])) break;
            }
        } else {
            for (key = 0; key < obj.length; key++) {
                if (fn.call(obj[key], key, obj[key])) break;
            }
        }
        return that;
    }
};



bt.pub = {
	get_data : function(data,callback,hide){
		if(!hide) var loading = bt.load(lan.public.the);
		bt.send('getData','data/getData',data,function(rdata){
			if(loading) loading.close();
			if(callback) callback(rdata);
		})
    },
    set_data_by_key: function (tab, key, obj) {		
		var _span = $(obj);
		var _input = $("<input class='baktext' type='text' placeholder='"+lan.ftp.ps+"' />").val(_span.text())
		_span.hide().after(_input);
		_input.focus();
		_input.blur(function(){
			var item = $(this).parents('tr').data('item');
			var _txt = $(this);
			var data = {table:tab,id:item.id};
			data[key] = _txt.val()
			bt.pub.set_data_ps(data,function(rdata){
				if(rdata.status){	
					_span.text(_txt.val());								
					_span.show();
					_txt.remove();
				}
			})
		})
		_input.keyup(function(){
			if(event.keyCode == 13){
				_input.trigger("blur");
			}
		})
	},
	set_data_ps:function(data,callback){
		bt.send('setPs','data/setPs',data,function(rdata){			
			if(callback) callback(rdata);
		})
	},
	set_server_status : function(serverName,type)
	{
		if(bt.contains(serverName,'php-')) {
			serverName = "php-fpm-" + serverName.replace('php-','').replace('.','');
		}		
		if(serverName=='pureftpd') serverName = 'pure-ftpd';
		if(serverName=='mysql') serverName = 'mysqld';
		serverName = serverName.replace('_soft','');
		var data = "name=" + serverName + "&type=" + type;
		var msg = lan.bt[type];
		var typeName = '';
		switch(type){
          	case 'stop':
				typeName = '停止';
			break;
			case 'restart':
				typeName = '重启';
			break;
			case 'reload':
				typeName = '重载';
			break;
		}
		bt.confirm({msg:lan.get('service_confirm',[msg,serverName]),title:typeName+serverName+'服务'},function(){
			var load = bt.load(lan.get('service_the',[msg,serverName]))		
			bt.send('system','system/ServiceAdmin',data,function(rdata){				
				load.close();
				var f = rdata.status ? lan.get('service_ok',[serverName,msg]):lan.get('service_err',[serverName,msg]);
				bt.msg({msg:f,icon:rdata.status})
			
				if(type != "reload" && rdata.status) {
					setTimeout(function() {
						window.location.reload()
					}, 1000)
				}
				if(!rdata.status) {
					bt.msg(rdata);
				}
			})
		})
	},	
	set_server_status_by:function(data,callback){
		bt.send('system','system/ServiceAdmin',data,function(rdata){
			if(callback) callback(rdata)
		})
	},
	get_task_count:function(callback){
		bt.send('GetTaskCount','ajax/GetTaskCount',{},function(rdata){
			$(".task").text(rdata);
			if(callback) callback(rdata);
		})
	},
	check_install:function(callback){
		bt.send('CheckInstalled','ajax/CheckInstalled',{},function(rdata){
			if(callback) callback(rdata);
		})
	},
	get_user_info:function(callback){
		var loading = bt.load();
		bt.send('GetUserInfo','ssl/GetUserInfo',{},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	show_hide_pass:function(obj){
		var a = "glyphicon-eye-open";
		var b = "glyphicon-eye-close";
		
		if($(obj).hasClass(a)){
			$(obj).removeClass(a).addClass(b);
			$(obj).prev().text($(obj).prev().attr('data-pw'))
		}
		else{
			$(obj).removeClass(b).addClass(a);
			$(obj).prev().text('**********');
		}
	},
	copy_pass:function(password){
		var clipboard = new ClipboardJS('#bt_copys');
		clipboard.on('success', function (e) {
		    bt.msg({msg:'复制成功',icon:1});
		});
		
		clipboard.on('error', function (e) {
		    bt.msg({msg:'复制失败，浏览器不兼容!',icon:2});
		});
		$("#bt_copys").attr('data-clipboard-text',password);
		$("#bt_copys").click();
    },
    login_btname: function (username,password,callback) {
        var loadT = bt.load(lan.config.token_get);
        bt.send('GetToken', 'ssl/GetToken', "username=" + username + "&password=" + password, function (rdata) {
            loadT.close();
            bt.msg(rdata);
            if (rdata.status) {
                if (callback) callback(rdata)                          
            }
        })	
    },
	bind_btname:function(callback){
		layer.open({
			type: 1,
			title: '绑定宝塔官网账号',
			area: ['420px','360px'],
			closeBtn: 2,
			shadeClose: false,
			content:'<div class="libLogin pd20" ><div class="bt-form text-center"><div class="line mb15"><h3 class="c2 f16 text-center mtb20">绑定宝塔官网账号</h3></div><div class="line"><input class="bt-input-text" name="username2" type="text" placeholder="手机" id="p1"></div><div class="line"><input autocomplete="new-password" class="bt-input-text" type="password" name="password2"  placeholder="密码" id="p2"></div><div class="line"><input class="login-button" value="登录" type="button" ></div><p class="text-right"><a class="btlink" href="https://www.bt.cn/register.html" target="_blank">未有账号，去注册</a></p></div></div>',
			success:function(){
			    $('.login-button').click(function(){
    				var p1 = $("#p1").val(),p2 = $("#p2").val(),loadT = bt.load(lan.config.token_get);
    				bt.send('GetToken','ssl/GetToken',"username=" + p1 + "&password=" + p2,function(rdata){
    					loadT.close();
    					bt.msg(rdata);
    					if(rdata.status) {
    					    var username = p1 = p1.substring(0,3)+'****'+p1.substring(7,11);
    					    bt.set_cookie('bt_user_info',JSON.stringify({data:{username:username}}));
    					    $('.bind-user').text(username);
    						if(callback){
    							layer.closeAll();
    							callback(rdata)
    						}else{
    							window.location.reload();
    						}					
    						$("input[name='btusername']").val(p1);
    					}
    				});
    			});
    			$('.libLogin input[type=password]').keyup(function(e){
    				if(e.keyCode == 13){
    					$('.login-button').click();
    				}
    			});
			}
		});
	},
	unbind_bt : function()
	{
		var name = $("input[name='btusername']").val();
		bt.confirm({msg:lan.config.binding_un_msg,title:lan.config.binding_un_title},function(){
			bt.send('DelToken','ssl/DelToken',{},function(rdata){
				bt.msg(rdata);
				$("input[name='btusername']").val('');
			})
		})
	},
	get_menm:function(callback){
		var loading = bt.load();
		bt.send('GetMemInfo','system/GetMemInfo',{},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	on_edit_file:function(type, fileName) {	
		if(type != 0) {			
			var l = $("#PathPlace input").val();
			var body = encodeURIComponent($("#textBody").val());			
			var encoding = $("select[name=encoding]").val();
			var loadT = bt.load(lan.bt.save_file);
			bt.send('SaveFileBody','files/SaveFileBody',"data=" + body + "&path=" + fileName + "&encoding=" + encoding,function(rdata){
				if(type == 1) loadT.close();
				bt.msg(rdata);				
			})	
			return;
		}
		var loading = bt.load(lan.bt.read_file);
		ext = bt.get_file_ext(fileName);
		
		bt.send('GetFileBody','files/GetFileBody','path='+fileName,function(rdata){
			if(!rdata.status){
				bt.msg({msg:rdata.msg,icon:5});
				return;
			}			
			loading.close();
			var u = ["utf-8", "GBK", "GB2312", "BIG5"];
			var n = "";
			var m = "";
			var o = "";
			for(var p = 0; p < u.length; p++) {
				m = rdata.encoding == u[p] ? "selected" : "";
				n += '<option value="' + u[p] + '" ' + m + ">" + u[p] + "</option>"
			}
			var aceEditor = {},r = bt.open({
				type: 1,
				shift: 5,
				closeBtn: 1,
				area: ["90%", "90%"],
				shade:false,
				title: lan.bt.edit_title+"[" + fileName + "]",
				btn:[lan.public.save,lan.public.close],
				content: '<form class="bt-form pd20 pb70"><div class="line"><p style="color:red;margin-bottom:10px">'+lan.bt.edit_ps
					+'		<select class="bt-input-text" name="encoding" style="width: 74px;position: absolute;top: 31px;right: 19px;height: 22px;z-index: 9999;border-radius: 0;">' 
					+ n + '</select></p><div class="mCustomScrollbar bt-input-text ace_config_editor_scroll" id="textBody" style="width:100%;margin:0 auto;line-height: 1.8;position: relative;top: 10px;"></div></div></form>',
				yes:function(layer,index){
					bt.saveEditor(aceEditor);
				},
				btn2:function(layer,index){
					r.close();
				},
				success:function(){
					var q = $(window).height() * 0.9;
					$("#textBody").height(q - 160);
					aceEditor = bt.aceEditor({el:'textBody',content:rdata.data,mode:'html',saveCallback:function(val){
						bt.send('SaveFileBody','files/SaveFileBody',{path:fileName,encoding:$('[name="encoding"] option:selected').val(),data:val},function(rdata){
							bt.msg(rdata);
						});
					}});
				}
			})

		})
	}	
};

bt.index = {	
	rec_install:function(){		
		bt.send('GetSoftList','ajax/GetSoftList',{},function(l){
			
			var c = "";
			var g = "";
			var e = "";
			for(var h = 0; h < l.length; h++) {
				if(l[h].name == "Tomcat") {
					continue
				}
				var o = "";
				var m = "<input id='data_" + l[h].name + "' data-info='" + l[h].name + " " + l[h].versions[0].version + "' type='checkbox' checked>";
				for(var b = 0; b < l[h].versions.length; b++) {
					var d = "";
					if((l[h].name == "PHP" && (l[h].versions[b].version == "5.6" || l[h].versions[b].version == "5.6")) || (l[h].name == "MySQL" && l[h].versions[b].version == "5.6") || (l[h].name == "phpMyAdmin" && l[h].versions[b].version == "4.4")) {
						d = "selected";
						m = "<input id='data_" + l[h].name + "' data-info='" + l[h].name + " " + l[h].versions[b].version + "' type='checkbox' checked>"
					}
					o += "<option value='" + l[h].versions[b].version + "' " + d + ">" + l[h].name + " " + l[h].versions[b].version + "</option>"
				}
				var f = "<li><span class='ico'><img src='/static/img/" + l[h].name.toLowerCase() + ".png'></span><span class='name'><select id='select_" + l[h].name + "' class='sl-s-info'>" + o + "</select></span><span class='pull-right'>" + m + "</span></li>";
				if(l[h].name == "Nginx") {
					c = f
				} else {
					if(l[h].name == "Apache") {
						g = f
					} else {
						e += f
					}
				}
			}
			c += e;
			g += e;
		
			g = g.replace(new RegExp(/(data_)/g), "apache_").replace(new RegExp(/(select_)/g), "apache_select_");
			var k = layer.open({
				type: 1,
				title: lan.bt.install_title,
				area: ["670px", "510px"],
				closeBtn: 2,
				shadeClose: false,
                content: "<div class='rec-install'><div class='important-title'><p><span class='glyphicon glyphicon-alert' style='color: #f39c12; margin-right: 10px;'></span>" + lan.bt.install_ps + " <a href='javascript:jump()' style='color:#20a53a'>" + lan.bt.install_s + "</a> " + lan.bt.install_s1 + "</p></div><div class='rec-box'><h3>" + lan.bt.install_lnmp + "</h3><div class='rec-box-con'><ul class='rec-list'>" + c + "</ul><p class='fangshi1'>" + lan.bt.install_type + "：<label data-title='" + lan.bt.install_rpm_title + "'><span>" + lan.bt.install_rpm + "</span><input type='checkbox' checked></label><label data-title='" + lan.bt.install_src_title + "'><span>" + lan.bt.install_src + "</span><input type='checkbox'></label></p><div class='onekey'>" + lan.bt.install_key + "</div></div></div><div class='rec-box' style='margin-left:16px'><h3>LAMP</h3><div class='rec-box-con'><ul class='rec-list'>" + g + "</ul><p class='fangshi1'>" + lan.bt.install_type + "：<label data-title='" + lan.bt.install_rpm_title + "'><span>" + lan.bt.install_rpm + "</span><input type='checkbox' checked></label><label data-title='" + lan.bt.install_src_title + "'><span>" + lan.bt.install_src + "</span><input type='checkbox'></label></p><div class='onekey'>"+lan.bt.install_key +"</div></div></div></div>",
                success:function(){
                	form_group.select_all([
                		'#select_Nginx',
                		'#select_MySQL',
                		'#select_Pure-Ftpd',
                		'#select_PHP',
                		'#select_phpMyAdmin',
                		'#apache_select_Apache',
                		'#apache_select_MySQL',
                		'#apache_select_Pure-Ftpd',
                		'#apache_select_PHP',
                		'#apache_select_phpMyAdmin'
                	]);
                	form_group.checkbox();
                	$('.layui-layer-content').css('overflow','inherit');
                	
                	$('.fangshi1 label').click(function(){
                	    var input = $(this).find('input'),siblings_label = input.parents('label').siblings()
                	    input.prop('checked','checked').next().addClass('active');
                	    siblings_label.find('input').removeAttr('checked').next().removeClass('active');

                	})
            //     	$(".fangshi1").on('click','.bt_checkbox_group',function (e) {
		          //      if($(this).prev().prop('checked')){
		          //      	$(this).prev().removeAttr('checked').parent().siblings().find('input').prop('checked','checked');
		          //      	$(this).removeClass('active').parent().siblings().find('.bt_checkbox_group').addClass('active')
		          //      }else{
		          //      	$(this).prev().attr('checked','checked').parent().siblings().find('input').removeAttr('checked')
		          //      	$(this).addClass('active').parent().siblings().find('.bt_checkbox_group').removeClass('active')
		          //      }
		          //  });
		          //  $(".fangshi1").on('click','span',function(){
		          //  	$(this).parent().find('.bt_checkbox_group').click();
		          //  })
		            var loadT = '';
					$('.fangshi1 label').hover(function(){
						var _title = $(this).attr('data-title'),_that = $(this);
						loadT = setTimeout(function(){
							layer.tips(_title,_that[0], {
							  tips: [1, '#20a53a'], //还可配置颜色
							  time:0
							});
						},500);
					},function(){
						clearTimeout(loadT);
						layer.closeAll('tips');
					});
                }
			});
			$(".sl-s-info").change(function() {
				var p = $(this).find("option:selected").text();
				var n = $(this).attr("id");
				p = p.toLowerCase();
				$(this).parents("li").find("input").attr("data-info", p)
			});
			$("#apache_select_PHP").change(function() {
				var n = $(this).val();
				j(n, "apache_select_", "apache_")
			});
			$("#select_PHP").change(function() {
				var n = $(this).val();
				j(n, "select_", "data_")
			});
	
			function j(p, r, q) {
				var n = "4.4";
				switch(p) {
					case "5.2":
						n = "4.0";
						break;
					case "5.3":
						n = "4.0";
						break;
					case "5.4":
						n = "4.4";
						break;
					case "5.5":
						n = "4.4";
						break;
					default:
						n = "4.9"
				}
				$("#" + r + "phpMyAdmin option[value='" + n + "']").attr("selected", "selected").siblings().removeAttr("selected");
				$("#"+q+"phpMyAdmin").attr("data-info", "phpmyadmin " + n)
			}
			$("#select_MySQL,#apache_select_MySQL").change(function() {
				var n = $(this).val();
				a(n)
			});
			
			$("#apache_select_Apache").change(function(){
				var apacheVersion = $(this).val();
				if(apacheVersion == '2.2'){
					layer.msg(lan.bt.install_apache22);
				}else{
					layer.msg(lan.bt.install_apache24);
				}
			});
			
			$("#apache_select_PHP").change(function(){
				var apacheVersion = $("#apache_select_Apache").val();
				var phpVersion = $(this).val();
				if(apacheVersion == '2.2'){
					if(phpVersion != '5.2' && phpVersion != '5.3' && phpVersion != '5.4'){
						layer.msg(lan.bt.insatll_s22+'PHP-' + phpVersion,{icon:5});
						$(this).val("5.4");
						$("#apache_PHP").attr('data-info','php 5.4');
						return false;
					}
				}else{
					if(phpVersion == '5.2'){
						layer.msg(lan.bt.insatll_s24+'PHP-' + phpVersion,{icon:5});
						$(this).val("5.4");
						$("#apache_PHP").attr('data-info','php 5.4');
						return false;
					}
				}
			});
	
			function a(n) {
				memSize = bt.get_cookie("memSize");
				max = 64;
				msg = "64M";
				switch(n) {
					case "5.1":
						max = 256;
						msg = "256M";
						break;
					case "5.7":
						max = 1500;
						msg = "2GB";
                        break;
                    case "8.0":
                        max = 5000;
                        msg = "6GB";
                        break;
					case "5.6":
						max = 800;
						msg = "1GB";
						break;
					case "AliSQL":
						max = 800;
						msg = "1GB";
						break;
					case "mariadb_10.0":
						max = 800;
						msg = "1GB";
						break;
					case "mariadb_10.1":
						max = 1500;
						msg = "2GB";
						break
				}
				if(memSize < max) {
					layer.msg( lan.bt.insatll_mem.replace("{1}",msg).replace("{2}",n), {
						icon: 5
					})
				}
			}
			var de = null;
			$(".onekey").click(function() {
				if(de) return;
				var v = $(this).prev().find("input").eq(0).prop("checked") ? "1" : "0";
				var r = $(this).parents(".rec-box-con").find(".rec-list li").length;
				var n = "";
				var q = "";
				var p = "";
				var x = "";
				var s = "";
				de = true;
				for(var t = 0; t < r; t++) {
					var w = $(this).parents(".rec-box-con").find("ul li").eq(t);
					var u = w.find("input");
					if(u.prop("checked")) {
						n += u.attr("data-info") + ","
					}
				}
				q = n.split(",");
				loadT = layer.msg(lan.bt.install_to, {
					icon: 16,
					time: 0,
					shade: [0.3, "#000"]
				});
				
				install_plugin(q);
				
				function install_plugin(q){
					if(!q[0]) return;
					p = q[0].split(" ")[0].toLowerCase();
					x = q[0].split(" ")[1];
					if(p=='pure-ftpd') p = 'pureftpd';
					if(p=='php') p = 'php-'+x;
					
                    s = "sName=" + p + "&version=" + x + "&type=" + v + "&id=" + (t + 1);
					bt.send('install_plugin','plugin/install_plugin',s,function(){
						q.splice(0,1);
						install_plugin(q);
					});
				}
				
				layer.close(loadT);
				layer.close(k);
				setTimeout(function() {
					GetTaskCount()
				}, 2000);
				layer.msg(lan.bt.install_ok, {
					icon: 1
				});
				setTimeout(function() {
					task()
				}, 1000)
			});
		})
	}
}

bt.weixin = {
		settiming:'',
		relHeight:500,
		relWidth:500,
		userLength:'',
		get_user_info:function(callback){
			bt.send('get_user_info','panel_wxapp/get_user_info',{},function(rdata){
				if(callback) callback(rdata);
			},1)
		},
		init:function(){
			var _this = this;
			$('.layui-layer-page').css('display', 'none');
			$('.layui-layer-page').width(_this.relWidth);
			$('.layui-layer-page').height(_this.relHeight);
			$('.bt-w-menu').height((_this.relWidth - 1) - $('.layui-layer-title').height());
			var width = $(document).width();
			var height = $(document).height();
			var boxwidth =  (width / 2) - (_this.relWidth / 2);
			var boxheight =  (height / 2) - (_this.relHeight / 2);
			$('.layui-layer-page').css({
				'left':boxwidth +'px',
				'top':boxheight+'px'
			});
			$('.boxConter,.layui-layer-page').css('display', 'block');
			$('.layui-layer-close').click(function(event) {
				window.clearInterval(_this.settiming);
			});
			this.get_user_details();
			$('.iconCode').hide();
			$('.personalDetails').show();
		},
		// 获取二维码
		get_qrcode:function(){
			var _this = this;
			var qrLoading = bt.load(lan.config.config_qrcode);
			
			bt.send('blind_qrcode','panel_wxapp/blind_qrcode',{},function(res){
				qrLoading.close();
				if (res.status){
                	$('#QRcode').empty();
					$('#QRcode').qrcode({
					    render: "canvas", //也可以替换为table
					    width: 200,
					    height: 200,
					    text:res.msg
					});
					_this.settiming =  setInterval(function(){
						_this.verify_binding();
					},2000);
				}else{
					bt.msg(res);
				}
			})
		},
		// 获取用户信息
		get_user_details:function(type){
			var _this = this;
			var conter = '';	
			_this.get_user_info(function(res){
				clearInterval(_this.settiming);
				if (!res.status){
					res.time = 3000;
					bt.msg(res);
					
					$('.iconCode').hide();
					return false;
				}
				if (JSON.stringify(res.msg) =='{}'){
					if (type){
						bt.msg({msg:lan.config.qrcode_no_list,icon:2})
					}else{
						_this.get_qrcode();
					}
					$('.iconCode').show();
					$('.personalDetails').hide();
					return false;
				}
				$('.iconCode').hide();
				$('.personalDetails').show();
				var datas = res.msg;
				for(var item in datas){
					conter += '<li class="item">\
								<div class="head_img"><img src="'+datas[item].avatarUrl+'" title="用户头像" /></div>\
								<div class="nick_name"><span>昵称:</span><span class="nick"></span>'+datas[item].nickName+'</div>\
								<div class="cancelBind">\
									<a href="javascript:;" class="btlink" title="取消当前微信小程序的绑定" onclick="bt.weixin.cancel_bind('+ item +')">取消绑定</a>\
								</div>\
							</li>'
				}
				conter += '<li class="item addweChat" style="height:45px;"><a href="javascript:;" class="btlink" onclick="bt.weixin.add_wx_view()"><span class="glyphicon glyphicon-plus"></span>添加绑定账号</a></li>'
				$('.userList').empty().append(conter);
			})
		},
		// 添加绑定视图
		add_wx_view:function(){
			$('.iconCode').show();
			$('.personalDetails').hide();
			this.get_qrcode();
		},
		// 取消当前绑定
		cancel_bind:function(uid){
			var _this = this;
			var bdinding = layer.confirm('您确定要取消当前绑定吗？',{
				btn:['确认','取消'],
				icon:3,
				title:'取消绑定'
			},function(){
				bt.send("blind_del","panel_wxapp/blind_del",{uid:uid},function(res){
					bt.msg(res);
					_this.get_user_details();
				})
			},function(){
				layer.close(bdinding);
			});
		},
		// 监听是否绑定
		verify_binding:function(){
			var _this = this;
			bt.send('blind_result','panel_wxapp/blind_result',{},function(res){
				if(res){
					bt.msg({status:true,msg:'绑定成功!'});
					clearInterval(_this.settiming);
					_this.get_user_details();
					}
				})
			},
		open_wxapp : function(){
				var rhtml = '<div class="boxConter" style="display: none">\
								<div class="iconCode" >\
									<div class="box-conter">\
										<div id="QRcode"></div>\
										<div class="codeTip">\
											<ul>\
												<li>1、打开宝塔面板小程序<span class="btlink weChat">小程序二维码<div class="weChatSamll"><img src="https://app.bt.cn/static/app.png"></div></span></li>\
												<li>2、使用宝塔小程序扫描当前二维码，绑定该面板</li>\
											</ul>\
											<span><a href="javascript:;" title="返回面板绑定列表" class="btlink" style="margin: 0 auto" onclick="bt.weixin.get_user_details(true)">查看绑定列表</a></span>\
										</div>\
									</div>\
								</div>\
								<div class="personalDetails" style="display: none">\
									<ul class="userList"></ul>\
								</div>\
							</div>'
				
				bt.open({
					type: 1,
					title: "绑定微信",
					area: '500px',			
					shadeClose: false,
					content:rhtml
			})		
			bt.weixin.init();
		}
};

bt.ftp = {	
	get_list : function(page,search,callback)
	{
		if(page == undefined) page = 1
		search = search == undefined ? '':search;
		var order = bt.get_cookie('order') ? '&order=' + bt.get_cookie('order'):'';
		
		var data = 'tojs=ftp.get_list&table=ftps&limit=15&p='+page+'&search='+search + order; 
		bt.pub.get_data(data,function(rdata){
			if(callback) callback(rdata);
		})
	},
	add:function(callback)
    {
        bt.data.ftp.add.list[1].items[0].value = bt.get_random(16);
		var bs = bt.render_form(bt.data.ftp.add,function(rdata){		
			if(callback) callback(rdata);
        });	
        $('.path' + bs).val($("#defaultPath").text());
	},
	set_password : function(callback){
		var bs = bt.render_form(bt.data.ftp.set_password,function(rdata){		
			if(callback) callback(rdata);
		});	
		return bs;
	},
	del: function(id,username,callback)
	{
		var loading = bt.load(lan.get('del_all_task_the',[username]));
		bt.send('DeleteUser','ftp/DeleteUser',{id:id,username:username},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	set_status: function(id, username,status,callback){
		var loadT = bt.load(lan.public.the);
		var data='id=' + id + '&username=' + username + '&status='+status;		
		bt.send('SetStatus','ftp/SetStatus',data,function(rdata){
			loadT.close();
			if(callback) callback(rdata);
			bt.msg(rdata);
		})		
	},
	set_port:function(callback)
	{
		var bs = bt.render_form(bt.data.ftp.set_port,function(rdata){		
				if(callback) callback(rdata);
			});	
		return bs;
	}	
}

bt.recycle_bin = {				
	open_recycle_bin:function(type){
		if(type==undefined) type = 1;
		bt.files.get_recycle_bin(type,function(rdata){
		var data = [];							
		switch(type){
			case 2:
				data = rdata.dirs;
				break;
			case 3:
				data = rdata.files;
				break;
			case 4:
			case 5:
			case 6:
				for (var i=0;i< rdata.files.length;i++) {
					if(type==6 && bt.contains(rdata.files[i].name,'BTDB_')){
						data.push(rdata.files[i]);
					}
					else{
						if(type==4 && bt.check_img(rdata.files[i].name)){
							data.push(rdata.files[i]);
						}
						else if(type==5 && !bt.check_img(rdata.files[i].name)){
							data.push(rdata.files[i]);
						}
					}							
				}						
				break;
			default:
				data = rdata.dirs.concat(rdata.files);
				break;
		}				
		if($('#tab_recycle_bin').length <= 0)
		{		
			bt.open({
				type: 1,
				skin: 'demo-class',
				area: ['80%','606px'],
				title: lan.files.recycle_bin_title,
				closeBtn: 2,
				shift: 5,
				shadeClose: false,
				content: '<div class="re-head">\
							<div style="margin-left: 3px;" class="ss-text">\
			                        <em>'+lan.files.recycle_bin_on+'</em>\
			                        <div class="ssh-item">\
			                                <input class="btswitch btswitch-ios" id="Set_Recycle_bin" type="checkbox" '+(rdata.status?'checked':'')+'>\
			                                <label class="btswitch-btn" for="Set_Recycle_bin" onclick="bt.files.set_recycle_bin()"></label>\
			                        </div>\
			                        <em style="margin-left: 20px;">'+lan.files.recycle_bin_on_db+'</em>\
			                        <div class="ssh-item">\
			                                <input class="btswitch btswitch-ios" id="Set_Recycle_bin_db" type="checkbox" '+(rdata.status_db?'checked':'')+'>\
			                                <label class="btswitch-btn" for="Set_Recycle_bin_db" onclick="bt.files.set_recycle_bin(1)"></label>\
			                        </div>\
			                </div>\
							<span style="line-height: 32px; margin-left: 30px;">'+lan.files.recycle_bin_ps+'</span>\
			                <button style="float: right" class="btn btn-default btn-sm" onclick="bt.recycle_bin.clear_recycle_bin();">'+lan.files.recycle_bin_close+'</button>\
							</div>\
							<div class="re-con">\
								<div class="re-con-menu"></div>\
								<div class="re-con-con">\
								<div style="margin: 15px;" class="divtable">\
									<table id="tab_recycle_bin" width="100%" class="table table-hover"></table>\
								</div></div></div>'
			});
		}
		
		setTimeout(function(){
			var menus = [
				{title:lan.files.recycle_bin_type1,click:'bt.recycle_bin.open_recycle_bin(1)'},
				{title:lan.files.recycle_bin_type2,click:'bt.recycle_bin.open_recycle_bin(2)'},
				{title:lan.files.recycle_bin_type3,click:'bt.recycle_bin.open_recycle_bin(3)'},
				{title:lan.files.recycle_bin_type4,click:'bt.recycle_bin.open_recycle_bin(4)'},
				{title:lan.files.recycle_bin_type5,click:'bt.recycle_bin.open_recycle_bin(5)'},
				{title:lan.files.recycle_bin_type6,click:'bt.recycle_bin.open_recycle_bin(6)'}
			];
			var m_html = '';
			for (var i=0;i<menus.length;i++) {
				var c = type==(i+1)?'class="on"':'';
				m_html+='<p '+c+' onclick="'+menus[i].click+'" >'+menus[i].title+'</p>';
			}
			$('.re-con-menu').html(m_html);
			var _tab =  bt.render({
				table:'#tab_recycle_bin',
				columns:[
					{field:'name',title:lan.files.recycle_bin_th1},
					{field:'dname',title:lan.files.recycle_bin_th2},
					{field:'size',title:lan.files.recycle_bin_th3,templet:function(item){
						return bt.format_size(item.size)
					}},
					{field:'time',title:lan.files.recycle_bin_th4,templet:function(item){
						return bt.format_data(item.time);
					}},
					{field:'opt',title:lan.files.recycle_bin_th5,align:'right',templet:function(item){
						var opt = '<a class="btlink" href="javascript:;" onclick="bt.recycle_bin.re_recycle_bin(\''+item.rname+'\','+type+')">恢复</a> | ';
						opt += '<a class="btlink" href="javascript:;" onclick="bt.recycle_bin.del_recycle_bin(\''+item.rname+'\','+type+')">永久删除</a>';
						return opt;
					}},
				],
				data:data
			});	
		},100)
		})
	},
	clear_recycle_bin:function(){
		var _this = this;
		bt.files.clear_recycle_bin(function(rdata){
			_this.open_recycle_bin(1);
			bt.msg(rdata);
		})
	},
	del_recycle_bin:function(path,type){
		var _this = this;
		bt.files.del_recycle_bin(path,function(rdata){
			if(rdata.status) _this.open_recycle_bin(type);
			bt.msg(rdata);
		})
	},
	re_recycle_bin:function(path,type){
		var _this = this;
		bt.files.re_recycle_bin(path,function(rdata){
			if(rdata.status) _this.open_recycle_bin(type);
			bt.msg(rdata);
		})
	}		
}

bt.files = {
	get_path:function()
	{
		path = path = bt.get_cookie('Path');
		if(!path)
		{
			bt.msg({msg:lan.get('lack_param',['response'])});

		}
	},	
	get_files:function(Path,searchV,callback){
		var searchtype = Path;
		if(isNaN(Path)){
			var p = '1';
		}else{
			var p = Path;
			Path = bt.get_cookie('Path');
		}		
		var search = '';
		if(searchV.length > 1 && searchtype == "1"){
			search = "&search="+searchV;
		}
		var showRow = bt.get_cookie('showRow');
		if(!showRow) showRow = '500';
		var totalSize = 0;
		var loadT = bt.load(lan.public.the);
		bt.send('get_files','files/GetDir','tojs=GetFiles&p=' + p + '&showRow=' + showRow + search+'&path='+ Path,function(rdata){
			loadT.close();
			//bt.set_cookie('Path',rdata.PATH);
			if(callback) callback(rdata);
		})
	},
	get_recycle_bin:function(type,callback)
	{
		loading = bt.load(lan.public.the);
		bt.send('Get_Recycle_bin','files/Get_Recycle_bin',{},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	re_recycle_bin:function(path,callback)
	{
		bt.confirm({msg:lan.files.recycle_bin_re_msg,title:lan.files.recycle_bin_re_title},function(){
			var loadT = bt.load(lan.files.recycle_bin_re_the);
			bt.send('Re_Recycle_bin','files/Re_Recycle_bin','path='+path,function(rdata){
				loadT.close();
				bt.msg(rdata);
				if(callback) callback(rdata);
			})
		});
	},
	del_recycle_bin:function(path,callback)
	{
		bt.confirm({msg:lan.files.recycle_bin_del_msg,title:lan.files.recycle_bin_del_title},function(){
			var loadT = bt.load(lan.files.recycle_bin_del_the);
			bt.send('Re_Recycle_bin','files/Del_Recycle_bin','path='+path,function(rdata){
				loadT.close();
				bt.msg(rdata);
				if(callback) callback(rdata);
			})
		});
	},
	clear_recycle_bin:function(callback)
	{
		bt.confirm({msg:lan.files.recycle_bin_close_msg,title:lan.files.recycle_bin_close},function(){
			var loadT = bt.load("<div class='myspeed'>"+lan.files.recycle_bin_close_the+"</div>");
			bt.send('Re_Recycle_bin','files/Close_Recycle_bin',{},function(rdata){
				loadT.close();
				bt.msg(rdata);
				if(callback) callback(rdata);
			})
		});
	},
	set_recycle_bin:function(db)
	{
		var loadT = bt.load(lan.public.the);
		var data = {};
		if(db) data = {db:db}		
		bt.send('Recycle_bin','files/Recycle_bin',data,function(rdata){
			loadT.close();
			bt.msg(rdata);
		})
	},
	rename:function(fileName,type,callback) 
	{
		if(type==undefined) type = 0;
		_this = this;
		path = _this.get_path();
		if(type)
		{
			var newFileName = path + '/' + $("#newFileName").val();
			var oldFileName = path + '/' + fileName;
			var loading = bt.load(lan.public.the);
			bt.send('MvFile','files/MvFile','sfile=' + oldFileName + '&dfile=' + newFileName,function(rdata) {
				loading.close();
				bt.msg(rdata);
				if(callback) callback(rdata);
			});
			return;
		}		
		bt.open({
			type: 1,
			shift: 5,
			closeBtn: 2,
			area: '320px', 
			title: lan.files.file_menu_rename,
			content: '<div class="bt-form pd20 pb70">\
						<div class="line">\
						<input type="text" class="bt-input-text" name="Name" id="newFileName" value="' + fileName + '" placeholder="'+lan.files.file_name+'" style="width:100%" />\
						</div>\
						<div class="bt-form-submit-btn">\
						<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+lan.public.close+'</button>\
						<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title">'+lan.public.save+'</button>\
						</div>\
					</div>'
		});
		setTimeout(function(){
			$("#ReNameBtn").click(function(){
				_this.rename(fileName,1,callback);
			})			
			$("#newFileName").focus().keyup(function(e){
				if(e.keyCode == 13) $("#ReNameBtn").click();
			});
		},100)
		
	},
	get_file_body:function(path,callback){
		bt.send('GetFileBody','files/GetFileBody','path='+path,function(rdata){
			if(callback) callback(rdata);
		})
	},
	set_file_body:function(path,data,encoding,callback){		
		var loading = bt.load(lan.site.saving_txt);
		bt.send('SaveFileBody','files/SaveFileBody',{path:path,data:data,encoding:encoding},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	del_file:function(path,callback)
	{
		bt.confirm({msg:lan.get('recycle_bin_confirm',[fileName]),title:lan.files.del_file},function(){
			loading = bt.load(lan.public.the);
			bt.send('del_file','files/DeleteFile','path='+path,function(rdata){
				loading.close();
				bt.msg(rdata);
				if(callback) callback(rdata);
			})
		})		
	},
	del_dir:function(path,callback)
	{
		bt.confirm({msg:lan.get('recycle_bin_confirm_dir',[fileName]),title:lan.files.del_file},function(){
			loading = bt.load(lan.public.the);
			bt.send('DeleteDir','files/DeleteDir','path='+path,function(rdata){
				loading.close();
				bt.msg(rdata);
				if(callback) callback(rdata);
			})
		})	
	},
	cut_file:function(fileName,callback) //裁剪
	{
		bt.set_cookie('cutFileName', fileName);
		bt.set_cookie('copyFileName', null);	
		bt.msg({msg:lan.files.mv_ok,icon:1,time:1})
		if(callback) callback(rdata);
	},
	copy_file:function(fileName,callback)
	{
		bt.set_cookie('cutFileName', null);
		bt.set_cookie('copyFileName', fileName);	
		bt.msg({msg:lan.files.copy_ok,icon:1,time:1})
		if(callback) callback(rdata);
	},
	paste_file:function(fileName,callback) //粘贴
	{		
		_this = this;
		path = _this.get_path();
		var copyName = bt.get_cookie('copyFileName');
		var cutName = bt.get_cookie('cutFileName');
		var filename = copyName;
		if(cutName != 'null' && cutName != undefined) filename=cutName;
		filename = filename.split('/').pop();
		
		bt.send('CheckExistsFiles','files/CheckExistsFiles',{dfile:path,filename:filename},function(rdata){
			if(rdata.length > 0){
				var tbody = '';
				for(var i=0;i<rdata.length;i++){
					tbody += '<tr><td>'+rdata[i].filename+'</td><td>'+bt.format_size(rdata[i].size)+'</td><td>'+bt.format_data(rdata[i].mtime)+'</td></tr>';
				}
				var mbody = '<div class="divtable"><table class="table table-hover" width="100%" border="0" cellpadding="0" cellspacing="0"><thead><th>'+lan.bt.filename+'</th><th>'+lan.bt.file_size+'</th><th>'+lan.bt.etime+'</th></thead>\
							<tbody>'+tbody+'</tbody>\
							</table></div>';
				bt.show_confirm(bt.files.file_conver_msg,mbody,function(){
					_this.paste_to(path,copyName,cutName,fileName,callback);
				})
			}else{
				_this.paste_to(path,copyName,cutName,fileName,callback);
			}
		})
	},
	paste_to:function(path,copyName,cutName,fileName,callback)
	{
		if (copyName != 'null' && copyName != undefined) {
			var loading =  bt.msg({msg:lan.files.copy_the,icon:16});		
			bt.send('CopyFile','files/CopyFile','sfile=' + copyName + '&dfile=' + path +'/'+ fileName,function(rdata){
				loading.close();
				bt.msg(rdata);
				if(callback) callback(rdata);
			})
			bt.set_cookie('copyFileName',null);
			bt.set_cookie('cutFileName',null);
			return;
		}
		
		if (cutName != 'null' && cutName != undefined) {
			var loading =  bt.msg({msg:lan.files.copy_the,icon:16});	
			bt.send('MvFile','files/MvFile','sfile=' + copyName + '&dfile=' + path +'/'+ fileName,function(rdata){
				loading.close();
				bt.msg(rdata);
				if(callback) callback(rdata);
			});
			bt.set_cookie('copyFileName',null);
			bt.set_cookie('cutFileName',null);

		}
	},
	zip:function(dirName,submits,callback)
	{
		_this = this;
		if(submits != undefined)
		{
			if(dirName.indexOf(',') == -1){
				tmp = $("#sfile").val().split('/');
				sfile = tmp[tmp.length-1];
			}else{
				sfile = dirName;
			}			
			dfile = $("#dfile").val();
			layer.closeAll();
			var loading = bt.load(lan.files.zip_the);
			bt.send('Zip','files/Zip','sfile=' + sfile + '&dfile=' + dfile + '&type=tar&path='+path, function(rdata) {
				loading.close();
				if(rdata == null || rdata == undefined){
					bt.msg({msg:lan.files.zip_ok,icon:1})
					if(callback) callback(rdata);
					return;
				}
				bt.msg(rdata);
				if(rdata.status) if(callback) callback(rdata);
			});
			return;
		}
		var ext = '.zip';
		if(bt.os=='Linux') ext = '.tar.gz'; 
		
		param = dirName;
		if(dirName.indexOf(',') != -1){
			tmp = path.split('/')
			dirName = path + '/' + tmp[tmp.length-1]
		}		
		bt.open({
			type: 1,
			shift: 5,
			closeBtn: 2,
			area: '650px',
			title: lan.files.zip_title,
			content: '<div class="bt-form pd20 pb70">'
						+'<div class="line noborder">'
						+'<input type="text" class="form-control" id="sfile" value="' +param + '" placeholder="" style="display:none" />'
						+'<span>'+lan.files.zip_to+'</span><input type="text" class="bt-input-text" id="dfile" value="'+dirName + ext + '" placeholder="'+lan.files.zip_to+'" style="width: 75%; display: inline-block; margin: 0px 10px 0px 20px;" /><span class="glyphicon glyphicon-folder-open cursor" onclick="ChangePath(\'dfile\')"></span>'
						+'</div>'
						+'<div class="bt-form-submit-btn">'
						+'<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+lan.public.close+'</button>'
						+'<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title"'+lan.files.file_menu_zip+'</button>'
						+'</div>'
					+'</div>'
		});
		
		setTimeout(function(){
			$("#dfile").change(function(){
				var dfile = bt.rtrim($(this).val(),'/');
				if(bt.check_zip(dfile)===-1)
				{
					dfile += ext;
					$(this).val(dfile)
				}
			});
			$("#ReNameBtn").click(function(){
				_this.zip(param,1,callback);
			})
		},100);
	},
	un_zip : function(fileName ,type ,callback) // type: zip|tar
	{	
		_this = this;
		if(type.length == 3){
			var sfile = encodeURIComponent($("#sfile").val());
			var dfile = encodeURIComponent($("#dfile").val());
			var password = encodeURIComponent($("#unpass").val());
			coding = $("select[name='coding']").val();
			layer.closeAll();
			var loading = bt.load(lan.files.unzip_the);
			bt.send('UnZip','files/UnZip','sfile=' + sfile + '&dfile=' + dfile +'&type=' + type + '&coding=' + coding + '&password=' + password, function(rdata) {
				loading.close();
				bt.msg(rdata);
				if(callback) callback(rdata);
			});
			return
		}		
		var path = bt.get_file_path(fileName);
		type = (type == 1) ? 'tar':'zip'
		var umpass = '';
		if(type == 'zip'){
			umpass = '<div class="line"><span class="tname">'+lan.files.zip_pass_title+'</span><input type="text" class="bt-input-text" id="unpass" value="" placeholder="'+lan.files.zip_pass_msg+'" style="width:330px" /></div>'
		}		
		bt.open({
			type: 1,
			shift: 5,
			closeBtn: 2,
			area: '490px',
			title: lan.files.unzip_title,
			content: '<div class="bt-form pd20 pb70">'
						+'<div class="line unzipdiv">'
						+'<span class="tname">'+lan.files.unzip_name+'</span><input type="text" class="bt-input-text" id="sfile" value="' +fileName + '" placeholder="'+lan.files.unzip_name_title+'" style="width:330px" /></div>'
						+'<div class="line"><span class="tname">'+lan.files.unzip_to+'</span><input type="text" class="bt-input-text" id="dfile" value="'+path + '" placeholder="'+lan.files.unzip_to+'" style="width:330px" /></div>' + umpass
						+'<div class="line"><span class="tname">'+lan.files.unzip_coding+'</span><select class="bt-input-text" name="coding">'
							+'<option value="UTF-8">UTF-8</option>'
							+'<option value="gb18030">GBK</option>'
						+'</select>'
						+'</div>'
						+'<div class="bt-form-submit-btn">'
						+'<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+lan.public.close+'</button>'
						+'<button type="button" id="ReNameBtn" class="btn btn-success btn-sm btn-title" >'+lan.files.file_menu_unzip+'</button>'
						+'</div>'
					+'</div>'
		});		
		setTimeout(function(){
	
			$("#ReNameBtn").click(function(){
				_this.un_zip(fileName,type,callback);
			})
		},100);
	},
	show_img:function(fileName)
	{
		var imgUrl = '/download?filename='+fileName;
		bt.open({
			type:1,
			closeBtn: 2,
			title:false,
			area: '500px',
			shadeClose: true,
			content: '<div class="showpicdiv"><img width="100%" src="'+imgUrl+'"></div>'
		});
		$(".layui-layer").css("top", "30%");
	},
	get_files_bytes:function(fileName, fileSize)
	{
		window.open('/download?filename='+encodeURIComponent(fileName));
	},
	upload_files : function()
	{
		path = this.get_path();
		bt.open({
			type:1,
			closeBtn: 2,
			title:lan.files.up_title,
			area: ['500px','500px'], 
			shadeClose:false,
			content:'<div class="fileUploadDiv"><input type="hidden" id="input-val" value="'+path+'" />\
					<input type="file" id="file_input"  multiple="true" autocomplete="off" />\
					<button type="button"  id="opt" autocomplete="off">'+lan.files.up_add+'</button>\
					<button type="button" id="up" autocomplete="off" >'+lan.files.up_start+'</button>\
					<span id="totalProgress" style="position: absolute;top: 7px;right: 147px;"></span>\
					<span style="float:right;margin-top: 9px;">\
					<font>'+lan.files.up_coding+':</font>\
					<select id="fileCodeing" >\
						<option value="byte">'+lan.files.up_bin+'</option>\
						<option value="utf-8">UTF-8</option>\
						<option value="gb18030">GB2312</option>\
					</select>\
					</span>\
					<button type="button" id="filesClose" autocomplete="off" onClick="layer.closeAll()" >'+lan.public.close+'</button>\
					<ul id="up_box"></ul></div>'
		});
		UploadStart();
	},
	set_chmod:function(action,fileName,callback)
	{
		_this = this;
		if(action == 1){
			var chmod = $("#access").val();
			var chown = $("#chown").val();
			var data = 'filename='+ fileName+'&user='+chown+'&access='+chmod;
			var loadT =  bt.load(lan.public.config);
			bt.send('SetFileAccess','files/SetFileAccess',data,function(rdata){
				loadT.close();
				if(rdata.status) layer.closeAll();
				bt.msg(rdata);
				if(callback) callback(rdata);
			});
			return;
		}
		
		var toExec = fileName == lan.files.all?'Batch(3,1)':'_this.set_chmod(1,\''+fileName+'\',callback)';
		
		bt.send('GetFileAccess','files/GetFileAccess', 'filename='+fileName,function(rdata){			
			if(bt.os=='Linux')
			{
				bt.open({
					type:1,
					title: lan.files.set_auth + '['+fileName+']',
					area: '400px', 
					shadeClose:false,
					content:'<div class="setchmod bt-form ptb15 pb70">\
								<fieldset>\
									<legend>'+lan.files.file_own+'</legend>\
									<p><input type="checkbox" id="owner_r" />'+lan.files.file_read+'</p>\
									<p><input type="checkbox" id="owner_w" />'+lan.files.file_write+'</p>\
									<p><input type="checkbox" id="owner_x" />'+lan.files.file_exec+'</p>\
								</fieldset>\
								<fieldset>\
									<legend>'+lan.files.file_group+'</legend>\
									<p><input type="checkbox" id="group_r" />'+lan.files.file_read+'</p>\
									<p><input type="checkbox" id="group_w" />'+lan.files.file_write+'</p>\
									<p><input type="checkbox" id="group_x" />'+lan.files.file_exec+'</p>\
								</fieldset>\
								<fieldset>\
									<legend>'+lan.files.file_public+'</legend>\
									<p><input type="checkbox" id="public_r" />'+lan.files.file_read+'</p>\
									<p><input type="checkbox" id="public_w" />'+lan.files.file_write+'</p>\
									<p><input type="checkbox" id="public_x" />'+lan.files.file_exec+'</p>\
								</fieldset>\
								<div class="setchmodnum"><input class="bt-input-text" type="text" id="access" maxlength="3" value="'+rdata.chmod+'">'+lan.files.file_menu_auth+'，\
								<span>'+lan.files.file_own+'\
								<select id="chown" class="bt-input-text">\
									<option value="www" '+(rdata.chown=='www'?'selected="selected"':'')+'>www</option>\
									<option value="mysql" '+(rdata.chown=='mysql'?'selected="selected"':'')+'>mysql</option>\
									<option value="root" '+(rdata.chown=='root'?'selected="selected"':'')+'>root</option>\
								</select></span></div>\
								<div class="bt-form-submit-btn">\
									<button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+lan.public.close+'</button>\
							        <button type="button" class="btn btn-success btn-sm btn-title" onclick="'+toExec+'" >'+lan.public.ok+'</button>\
						        </div>\
							</div>'
				});
				
				settimeout(function(){
					_this.on_linux_access();
					$("#access").keyup(function(){
						_this.on_linux_access();
					});
					
					$("input[type=checkbox]").change(function(){
						var idName = ['owner','group','public'];
						var onacc = '';
						for(var n=0;n<idName.length;n++){
							var access = 0;
							access += $("#"+idName[n]+"_x").prop('checked')?1:0;
							access += $("#"+idName[n]+"_w").prop('checked')?2:0;
							access += $("#"+idName[n]+"_r").prop('checked')?4:0;
							onacc += access;
						}
						$("#access").val(onacc);					
					});
				},100)
			}
		})
	},
	on_linux_access:function()
	{
		var access = $("#access").val();
		var idName = ['owner','group','public'];				
		for(var n=0;n<idName.length;n++){
			$("#"+idName[n]+"_x").prop('checked',false);
			$("#"+idName[n]+"_w").prop('checked',false);
			$("#"+idName[n]+"_r").prop('checked',false);
		}
		for(var i=0;i<access.length;i++){
			var onacc = access.substr(i,1);
			if(i > idName.length) continue;
			if(onacc > 7) $("#access").val(access.substr(0,access.length-1));
			switch(onacc){
				case '1':
					$("#"+idName[i]+"_x").prop('checked',true);
					break;
				case '2':
					$("#"+idName[i]+"_w").prop('checked',true);
					break;
				case '3':
					$("#"+idName[i]+"_x").prop('checked',true);
					$("#"+idName[i]+"_w").prop('checked',true);
					break;
				case '4':
					$("#"+idName[i]+"_r").prop('checked',true);
					break;
				case '5':
					$("#"+idName[i]+"_r").prop('checked',true);
					$("#"+idName[i]+"_x").prop('checked',true);
					break;
				case '6':
					$("#"+idName[i]+"_r").prop('checked',true);
					$("#"+idName[i]+"_w").prop('checked',true);
					break;
				case '7':
					$("#"+idName[i]+"_r").prop('checked',true);
					$("#"+idName[i]+"_w").prop('checked',true);
					$("#"+idName[i]+"_x").prop('checked',true);
					break;
			}
		}
	},
	on_win_access:function()
	{
	
	},
	get_right_click:function(type,path,name){
		_this = this;
		var displayZip = bt.check_zip(type);
		var options = {items:[
		  {text: lan.files.file_menu_copy, 	onclick: function() {_this.copy_file(path)}},
		  {text: lan.files.file_menu_mv, 	onclick: function() {_this.cut_file(path)}},
		  {text: lan.files.file_menu_rename, 	onclick: function() {_this.rename(path,name)}},
		  {text: lan.files.file_menu_auth, 	onclick: function() {_this.set_chmod(0,path)}},
		  {text: lan.files.file_menu_zip, onclick: function() {_this.zip(path)}}
		  
		]};
		if(type == "dir"){
			options.items.push({text: lan.files.file_menu_del, onclick: function() {_this.del_dir(path)}});
		}
		else if(isText(type)){
			options.items.push({text: lan.files.file_menu_edit, onclick: function() {bt.on_edit_file(0,path)}},{text: lan.files.file_menu_down, onclick: function() {_this.get_files_bytes(path)}},{text: lan.files.file_menu_del, onclick: function() {_this.del_file(path)}});
		}
		else if(displayZip != -1){
			options.items.push({text: lan.files.file_menu_unzip, onclick: function() {_this.un_zip(path,displayZip)}},{text: lan.files.file_menu_down, onclick: function() {_this.get_files_bytes(path)}},{text: lan.files.file_menu_del, onclick: function() {_this.del_file(path)}});
		}
		else if(isImage(type)){
			options.items.push({text: lan.files.file_menu_img, onclick: function() {_this.show_img(path)}},{text: lan.files.file_menu_down, onclick: function() {_this.get_files_bytes(path)}},{text: lan.files.file_menu_del, onclick: function() {_this.del_file(path)}});
		}
		else{
			options.items.push({text: lan.files.file_menu_down, onclick: function() {_this.get_files_bytes(path)}},{text: lan.files.file_menu_del, onclick: function() {_this.del_file(path)}});
		}
		return options;
	},
	get_dir_size:function(path,callback){
		if(!path) path = this.get_path();
		var loading = bt.load(lan.public.the);
		bt.send('GetDirSize','files/GetDirSize',{path:path},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	batch:function(type,access,callback)
	{
		_this = this;
		
		var el = document.getElementsByTagName('input');
		var len = el.length;
		var data='path='+path+'&type='+type;
		var name = 'data';
		
		var oldType = bt.get_cookie('BatchPaste');
		
		for(var i=0;i<len;i++){
			if(el[i].checked == true && el[i].value != 'on'){
				data += '&'+name+'='+el[i].value;
			}
		}
		
		if(type == 3 && access == undefined){
			_this.set_chmod(0,lan.files.all);
			return;
		}
		
		if(type < 3) bt.set_cookie('BatchSelected', '1');
		bt.set_cookie('BatchPaste',type);
		
		if(access == 1){
			var access = $("#access").val();
			var chown = $("#chown").val();
			data += '&access='+access+'&user='+chown;
			layer.closeAll();
		}
		if(type == 4){
			AllDeleteFileSub(data,path);
			bt.set_cookie('BatchPaste',oldType);
			return;
		}
		
		if(type == 5){
			var names = '';
			for(var i=0;i<len;i++){
				if(el[i].checked == true && el[i].value != 'on'){
					names += el[i].value + ',';
				}
			}
			_this.zip(names);
			return;
		}
			
		myloadT = bt.load("<div class='myspeed'>"+lan.public.the+"</div>");
		setTimeout(function(){getSpeed('.myspeed');},1000);
		bt.send('SetBatchData','files/SetBatchData',data,function(rdata){
			myloadT.close();
			bt.msg(rdata);
			if(callback) callback(rdata);
		})
	},
	download_file:function(action,callback)
	{
		path = bt.get_cookie('Path');	
		if(action == 1){
			var fUrl = $("#mUrl").val();
			fUrl = fUrl;
			fpath = $("#dpath").val();
			fname = $("#dfilename").val();
			layer.closeAll();
			loading = bt.load(lan.files.down_task);
			bt.send('DownloadFile','files/DownloadFile','path='+fpath+'&url='+fUrl+'&filename='+fname,function(rdata){
				loading.close();
				bt.msg(rdata);
				if(callback) callback(rdata);
			});
			return;
		}
		layer.open({
			type: 1,
			shift: 5,
			closeBtn: 2,
			area: '500px',
			title: lan.files.down_title,
			content: '<form class="bt-form pd20 pb70">\
						<div class="line">\
						<span class="tname">'+lan.files.down_url+':</span><input type="text" class="bt-input-text" name="url" id="mUrl" value="" placeholder="'+lan.files.down_url+'" style="width:330px" />\
						</div>\
						<div class="line">\
						<span class="tname ">'+lan.files.down_to+':</span><input type="text" class="bt-input-text" name="path" id="dpath" value="'+path+'" placeholder="'+lan.files.down_to+'" style="width:330px" />\
						</div>\
						<div class="line">\
						<span class="tname">'+lan.files.file_name+':</span><input type="text" class="bt-input-text" name="filename" id="dfilename" value="" placeholder="'+lan.files.down_save+'" style="width:330px" />\
						</div>\
						<div class="bt-form-submit-btn">\
						<button type="button" class="btn btn-danger btn-sm" onclick="layer.closeAll()">'+lan.public.close+'</button>\
						<button type="button" id="dlok" class="btn btn-success btn-sm dlok" onclick="DownloadFile(1)">'+lan.public.ok+'</button>\
						</div>\
					</form>'
		});
		fly("dlok");
		$("#mUrl").keyup(function(){
			durl = $(this).val()
			tmp = durl.split('/')
			$("#dfilename").val(tmp[tmp.length-1])
		});
	}
}
// 任务管理器
bt.crontab = {
	// 执行计划任务请求
	start_task_send:function(id,name){
		var that = this,loading = bt.load();
		bt.send('start_task_send','crontab/StartTask',{id:id},function (rdata) {
			loading.close();
			rdata.time = 2000;
			bt.msg(rdata);
		});
	},
	
	// 删除计划任务
	del_task_send:function(id,name){
		bt.show_confirm('删除['+ name +']','您确定要删除该任务吗?',function(){
			bt.send('del_task_send','crontab/DelCrontab',{id:id},function (rdata) {
				loading.close();
				rdata.time = 2000;
				bt.msg(rdata);
				that.get_crontab_list();
			});
		});
	},
	
	// 设置计划任务状态
	set_crontab_status:function(id,status,callback){
		var that = this,loading = bt.load();
		bt.confirm({title:'提示',msg:status?'计划任务暂停后将无法继续运行，您真的要停用这个计划任务吗？':'该计划任务已停用，是否要启用这个计划任务？'},function () {
			bt.send('set_crontab_status','crontab/set_cron_status',{id:id},function (rdata) {
				loading.close();
				if(callback) callback(rdata)
			});
		});
	},
	
	// 编辑计划任务脚本
	edit_crontab_file:function(echo){
		bt.pub.on_edit_file(0,'/www/server/cron/'+ echo);
	},

	// 编辑计划任务
	edit_crontab:function(id,data){
		var that = this,loading = bt.load('提交数据中...');
		bt.send('edit_crontab','crontab/modify_crond',data,function(rdata){
			loading.close();
			if(rdata.status){
				// that.get_crontab_list();
				layer.msg(rdata.msg,{icon:1});
			}else{
				layer.msg(rdata.msg,{icon:2});
			}
		});
	},
	
	// 获取计划任务日志
	get_logs_crontab:function(id,name){
		var that = this;
		bt.send('get_logs_crontab','crontab/GetLogs',{id:id},function (rdata) {
			if(!rdata.status) {
				rdata.time = 1000;
				bt.msg(rdata);
			}else{
				bt.open({
					type:1,
					title:'查看日志-['+name+']',
					area: ['700px','520px'], 
					shadeClose:false,
					closeBtn:1,
					content:'<div class="setchmod bt-form pd20 pb70">'
							+'<pre class="crontab-log" style="overflow: auto; border: 0px none; line-height:28px;padding: 15px; margin: 0px; height: 405px; background-color: rgb(51,51,51);color:#f1f1f1;font-family: \"微软雅黑\"">'+ (rdata.msg == '' ? '当前日志为空':rdata.msg) +'</pre>'
							+'<div class="bt-form-submit-btn" style="margin-top: 0px;">'
							+'<button type="button" class="layui-btn layui-btn-sm" onclick="bt.crontab.del_logs_crontab('+id+')">'+lan.public.empty+'</button>'
							+'<button type="button" class="layui-btn layui-btn-sm layui-btn-primary" onclick="layer.closeAll()">'+lan.public.close+'</button>'
							+'</div>'
							+'</div>'
				})
				setTimeout(function () {
					var div = document.getElementsByClassName('crontab-log')[0]
					div.scrollTop  = div.scrollHeight;
				},200);
			}
		})
	},
	
	// 删除计划任务日志
	del_logs_crontab:function(id,name){
		var that = this,loading = bt.load();
		bt.send('del_logs_crontab','crontab/DelLogs',{id:id},function (rdata) {
			loading.close();
			layer.closeAll();
			rdata.time = 2000;
			bt.msg(rdata);
		});
	},
	
	// 获取计划任务列表
	get_crontab_list:function(status,callback){
		var that = this;
		 var loading = bt.load();
		bt.send('get_crontab_list','crontab/GetCrontab',{},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		});
	},
	
	// 获取站点和备份位置信息
	get_data_list:function(type,name){
		var that = this;
		bt.send('get_data_list','crontab/GetDataList',{type:type},function(rdata){
			that.backupsList.siteList = [{'name': 'ALL','ps':'所有'}]
			that.backupsList.optList =[{'name':'服务器磁盘','value':'localhost'}]
			that.backupsList.siteList = that.backupsList.siteList.concat(rdata.data);
			that.backupsList.optList = that.backupsList.optList.concat(rdata.orderOpt);
			that.initFrom["crontab-name"] = name + "["+ that.backupsList.siteList[that.initFrom['crontab-site']].name +"]";
			that.insert_control_from(that.initFrom['crontab-submit']);
		});
	},
	
	// 添加计划任务请求
	add_control_send:function(data){
		var that = this,loading = bt.load('提交数据中...');
		bt.send('addCrontab','crontab/AddCrontab',data,function(rdata){
			loading.close();
			if(rdata.status){
				that.insert_control_from(true,true);
				that.get_crontab_list();
				layer.msg(rdata.msg,{icon:1});
			}else{
				layer.msg(rdata.msg,{icon:2});
			}
		});
	},
	get_crontab_find:function(id,callback){
		bt.send('get_crontab_find','crontab/get_crontab_find',{id:id},function(rdata){
			if(callback) callback(rdata);
		})
	}

}

bt.config = 
{
	close_panel:function(callback)
	{
		layer.confirm(lan.config.close_panel_msg,{title:lan.config.close_panel_title,closeBtn:2,icon:13,cancel:function(){
			if(callback) callback(false);
		}}, function() {
			loading = bt.load(lan.public.the);
			bt.send('ClosePanel','config/ClosePanel',{},function(rdata){
				loading.close();
				if(callback) callback(rdata);
			})
		},function(){
			if(callback) callback(false);
		});
	},
	set_auto_update:function(callback)
	{
		loading = bt.load(lan.public.the);
		bt.send('AutoUpdatePanel','config/AutoUpdatePanel',{},function(rdata){
			loading.close();
			bt.msg(rdata);
			if(callback) callback(rdata);
		})
	},
	sync_data:function(callback)
	{
		var loadT = bt.load(lan.config.config_sync);
		bt.send('syncDate','config/syncDate',{},function(rdata){
			loadT.close();
			bt.msg(rdata);
			if(callback) callback(rdata);
		});
	},
	save_config:function(data,callback)
	{
		loading = bt.load(lan.config.config_save);
		bt.send('setPanel','config/setPanel',data,function(rdata){
			loading.close();
			bt.msg(rdata);
			if(callback) callback(rdata);
		});
	},
	set_template:function(template,callback)
	{		
		var loadT = bt.load(lan.public.the);
		bt.send('SetTemplates','config/SetTemplates',{templates:template},function(rdata){
			loadT.close();
			bt.msg(rdata);
			if(callback) callback(rdata);
		});
	},
	set_panel_ssl:function(status,callback)
	{
		var msg = status?lan.config.ssl_close_msg:'<a style="font-weight: bolder;font-size: 16px;">'+lan.config.ssl_open_ps+'</a><li style="margin-top: 12px;color:red;">'+lan.config.ssl_open_ps_1+'</li><li>'+lan.config.ssl_open_ps_2+'</li><li>'+lan.config.ssl_open_ps_3+'</li><p style="margin-top: 10px;"><input type="checkbox" id="checkSSL" /><label style="font-weight: 400;margin: 3px 5px 0px;" for="checkSSL">'+lan.config.ssl_open_ps_4+'</label><a target="_blank" class="btlink" href="https://www.bt.cn/bbs/thread-4689-1-1.html" style="float: right;">'+lan.config.ssl_open_ps_5+'</a></p>';
		layer.confirm(msg,{title:lan.config.ssl_title,closeBtn:2,icon:3,area:'550px',cancel:function(){
			if(callback) {
				if(status == 0){
					callback(false);
				}
				else{
					callback(true);
				}
			}
		}},function(){
			if(window.location.protocol.indexOf('https') == -1){
				if(!$("#checkSSL").prop('checked')){					
					bt.msg({msg:lan.config.ssl_ps,icon:2});
					if(callback)  callback(false);
				}
			}
			var loadT = bt.load(lan.config.ssl_msg);
			bt.send('SetPanelSSL','config/SetPanelSSL',{},function(rdata){
				loadT.close();
				bt.msg(rdata);
				if(callback)  callback(rdata);
			})			
		},function(){
			if(callback) {
				if(status == 0){
					callback(false);
				}
				else{
					callback(true);
				}
			}
		});
	},
	get_panel_ssl:function()
	{
		_this = this;
		loading = bt.load('正在获取证书信息...');
		bt.send('GetPanelSSL','config/GetPanelSSL',{},function(cert){
			loading.close();
			var certBody = '<div class="tab-con">\
				<div class="myKeyCon ptb15">\
					<div class="ssl-con-key pull-left mr20">密钥(KEY)<br>\
						<textarea id="key" class="bt-input-text">'+cert.privateKey+'</textarea>\
					</div>\
					<div class="ssl-con-key pull-left">证书(PEM格式)<br>\
						<textarea id="csr" class="bt-input-text">'+cert.certPem+'</textarea>\
					</div>\
					<div class="ssl-btn pull-left mtb15" style="width:100%">\
						<button class="btn btn-success btn-sm" id="btn_submit">保存</button>\
					</div>\
				</div>\
				<ul class="help-info-text c7 pull-left">\
					<li>粘贴您的*.key以及*.pem内容，然后保存即可<a href="http://www.bt.cn/bbs/thread-704-1-1.html" class="btlink" target="_blank">[帮助]</a>。</li>\
					<li>如果浏览器提示证书链不完整,请检查是否正确拼接PEM证书</li><li>PEM格式证书 = 域名证书.crt + 根证书(root_bundle).crt</li>\
				</ul>\
			</div>'
			bt.open({
				type: 1,
				area: "600px",
				title: '自定义面板证书',
				closeBtn: 2,
				shift: 5,
				shadeClose: false,
				content:certBody
			});
			
			$("#btn_submit").click(function(){
				key = $('#key').val();
				csr = $('#csr').val();
				_this.set_panel_ssl({privateKey:key,certPem:csr});
			})
		})
	},
	set_panel_ssl:function(data,callback)
	{		
		var loadT = bt.load(lan.config.ssl_msg);
		bt.send('SavePanelSSL','config/SavePanelSSL',data,function(rdata){
			loadT.close();
			bt.msg(rdata);
			if(callback) callback(rdata);
		})
	},
	set_username:function(type)
	{
		if(type==1)
		{
			if(p1 == "" || p1.length < 3) {
				bt.msg({msg:lan.bt.user_len,icon:2})
				return;
			}
			if(p1 != p2) {
				bt.msg({msg:lan.bt.user_err_re,icon:2})
				return;
			}
			var checks = ['admin','root','admin123','123456'];
			if($.inArray(p1,checks)){
				bt.msg({msg:'禁止使用常用用户名!',icon:2})
				return;
			}
			bt.send('setUsername','config/setUsername',{username1:p1,username2:p2},function(rdata){
				if(rdata.status) {
					layer.closeAll();					
					$("input[name='username_']").val(p1)
				}
				bt.msg(rdata);
			})
			return;
		}
		bt.open({
			type: 1,
			area: "290px",
			title: lan.bt.user_title,
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content: "<div class='bt-form pd20 pb70'><div class='line'><span class='tname'>"+lan.bt.user+"</span><div class='info-r'><input class='bt-input-text' type='text' name='password1' id='p1' value='' placeholder='"+lan.bt.user_new+"' style='width:100%'/></div></div><div class='line'><span class='tname'>"+lan.bt.pass_re+"</span><div class='info-r'><input class='bt-input-text' type='text' name='password2' id='p2' value='' placeholder='"+lan.bt.pass_re_title+"' style='width:100%'/></div></div><div class='bt-form-submit-btn'><button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">"+lan.public.close+"</button> <button type='button' class='btn btn-success btn-sm' onclick=\"bt.config.set_username(1)\">"+lan.public.edit+"</button></div></div>"
		})
	},
	set_password:function(type){
		if(type == 1) {
			p1 = $("#p1").val();
			p2 = $("#p2").val();
			if(p1 == "" || p1.length < 8) {			
				bt.msg({msg:lan.bt.pass_err_len,icon:2})
				return
			}
			
			//准备弱口令匹配元素
			var checks = ['admin888','123123123','12345678','45678910','87654321','asdfghjkl','password','qwerqwer'];
			pchecks = 'abcdefghijklmnopqrstuvwxyz1234567890';
			for(var i=0;i<pchecks.length;i++){
				checks.push(pchecks[i]+pchecks[i]+pchecks[i]+pchecks[i]+pchecks[i]+pchecks[i]+pchecks[i]+pchecks[i]);
			}
			
			//检查弱口令
			cps = p1.toLowerCase();
			var isError = "";
			for(var i=0;i<checks.length;i++){
				if(cps == checks[i]){
					isError += '['+checks[i]+'] ';
				}
			}			
			if(isError != ""){
				bt.msg({msg:lan.bt.pass_err+isError,icon:2})
				return;
			}			
			
			if(p1 != p2) {
				bt.msg({msg:lan.bt.pass_err_re,icon:2})
				return
			}
			bt.send('setPassword','config/setPassword',{password1:p1,password2:p2},function(rdata){
				layer.closeAll();
				bt.msg(rdata);
			})		
			return
		}
		layer.open({
			type: 1,
			area: "290px",
			title: lan.bt.pass_title,
			closeBtn: 2,
			shift: 5,
			shadeClose: false,
			content: "<div class='bt-form pd20 pb70'><div class='line'><span class='tname'>"+lan.public.pass+"</span><div class='info-r'><input class='bt-input-text' type='text' name='password1' id='p1' value='' placeholder='"+lan.bt.pass_new_title+"' style='width:100%'/></div></div><div class='line'><span class='tname'>"+lan.bt.pass_re+"</span><div class='info-r'><input class='bt-input-text' type='text' name='password2' id='p2' value='' placeholder='"+lan.bt.pass_re_title+"' style='width:100%' /></div></div><div class='bt-form-submit-btn'><span style='float: left;' title='"+lan.bt.pass_rep+"' class='btn btn-default btn-sm' onclick='randPwd(10)'>"+lan.bt.pass_rep_btn+"</span><button type='button' class='btn btn-danger btn-sm' onclick=\"layer.closeAll()\">"+lan.public.close+"</button> <button type='button' class='btn btn-success btn-sm' onclick=\"bt.config.set_password(1)\">"+lan.public.edit+"</button></div></div>"
		});
	}	
}

bt.system = {	
	get_total:function(callback){
		bt.send('GetSystemTotal','system/GetSystemTotal',{},function(rdata){
			if(callback) callback(rdata);
		})
	},
	get_net:function(callback){
		bt.send('GetNetWork','system/GetNetWork',{},function(rdata){
			if(callback) callback(rdata);
		})
	},
	get_disk_list:function(callback){
		bt.send('GetDiskInfo','system/GetDiskInfo',{},function(rdata){
			if(callback) callback(rdata);
		})
	},
    re_memory: function (callback) {
		    bt.send('ReMemory','system/ReMemory',{},function(rdata){
			    if(callback) callback(rdata);
            })
	},
    check_update: function (callback, check) {
        var data = {};
        if (check == undefined) data = { check: true };
        if (check === false) data = {}
        if (check) var load = bt.load(lan.index.update_get);
        bt.send('UpdatePanel', 'ajax/UpdatePanel', data ,function(rdata){
            if (check) load.close();
			if(callback) callback(rdata);
		})
	},
    to_update: function (callback){
		var load = bt.load(lan.index.update_the);
        bt.send('UpdatePanel', 'ajax/UpdatePanel', { toUpdate: 'yes' }, function (rdata) {
            load.close();
            if (callback) callback(rdata);
		})
	},
	reload_panel:function(callback){
		bt.send('ReWeb','system/ReWeb',{},function(rdata){
			if(callback) callback(rdata);
		})
	},
	rep_panel:function(callback){
		var loading = bt.load(lan.index.rep_panel_the)
		bt.send('RepPanel','system/RepPanel',{},function(rdata){
			loading.close();			
			if(rdata){
				if(callback) callback({status:rdata,msg:lan.index.rep_panel_ok});
				bt.system.reload_panel();				
			}
			
		})
	},
	get_warning:function(callback){
		bt.send('GetWarning','ajax/GetWarning',{},function(rdata){
			if(callback) callback(rdata);
		})
	},
	root_reload:function(callback){
		bt.send('RestartServer','system/RestartServer',{},function(rdata){
			if(callback) callback(rdata);
		})
	}	
}

bt.control = {
	get_status:function(callback){
		loading = bt.load(lan.public.read);
		bt.send('GetControl','control/SetControl',{type:1},function(rdata){
			if(callback) callback(rdata);
		})
	},
	set_control:function(type,day,callback){			
		loadT = bt.load(lan.public.the);
		bt.send('SetControl','config/SetControl',{type:type,day:day},function(rdata){
			loadT.close();
			bt.msg(rdata);
			if(callback) callback(rdata);
		})
	},
	clear_control:function(callback){
		bt.confirm({msg:lan.control.close_log_msg,title:lan.control.close_log},function(){
			loadT = bt.load(lan.public.the);
			bt.send('SetControl','config/SetControl',{type:'del'},function(rdata){
				loadT.close();
				bt.msg(rdata);
				if(callback) callback(rdata);
			})
		})
	},
	get_data:function(type,start,end,callback){
		action = '';
		switch(type)
		{
			case 'cpu': //cpu和内存一起获取
				action='GetCpuIo';
				break;
			case 'disk':
				action='GetDiskIo';
				break;
			case 'net':
				action='GetNetWorkIo';
				break;
			case 'load':
				action='get_load_average';
				break;
		}
		if(!action) bt.msg(lan.get('lack_param','type'));
		bt.send(action,'ajax/'+action,{start:start,end:end},function(rdata){
			if(callback) callback(rdata,type);
		})
	},
	format_option:function(obj,type){
		option = {
			tooltip: {
				trigger: 'axis',
				axisPointer: {
					type: 'cross'
				},
				formatter: obj.formatter
			},
			xAxis: {
				type: 'category',
				boundaryGap: false,
				data: obj.tData,
				axisLine:{
					lineStyle:{
						color:"#666"
					}
				}
			},
			yAxis: {
				type: 'value',
				name: obj.unit,
				boundaryGap: [0, '100%'],
				min:0,
				splitLine:{
					lineStyle:{
						color:"#ddd"
					}
				},
				axisLine:{
					lineStyle:{
						color:"#666"
					}
				}
			},
			dataZoom: [{
				type: 'inside',
				start: 0,
				zoomLock:true
			}, {
				start: 0,
				handleIcon: 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
				handleSize: '80%',
				handleStyle: {
					color: '#fff',
					shadowBlur: 3,
					shadowColor: 'rgba(0, 0, 0, 0.6)',
					shadowOffsetX: 2,
					shadowOffsetY: 2
				}
			}],
			series: []
		};		
		if(obj.legend) option.legend = obj.legend;		
		if(obj.dataZoom) option.dataZoom = obj.dataZoom;
		
		for (var i=0;i<obj.list.length;i++) 
		{
			var item = obj.list[i];
			series = {
				name : item.name,
				type : item.type?item.type:'line',
				smooth : item.smooth ? item.smooth : true,
				symbol : item.symbol ? item.symbol : 'none',
				showSymbol:item.showSymbol?item.showSymbol:false,
				sampling : item.sampling ? item.sampling : 'average',
				areaStyle : item.areaStyle ? item.areaStyle : {},
				lineStyle : item.lineStyle ? item.lineStyle : {},
				itemStyle : item.itemStyle ? item.itemStyle : { normal:{ color: 'rgb(0, 153, 238)'}},
				symbolSize:6,
				symbol: 'circle',
				data :  item.data						
			}
			option.series.push(series);
		}
		return option;
	}
}

bt.firewall = {
	get_log_list:function(page,search,callback){		
		if(page == undefined) page = 1
		search = search == undefined ? '':search;
		var order = bt.get_cookie('order') ? '&order=' + bt.get_cookie('order'):'';
		
		var data = 'tojs=firewall.get_log_list&table=logs&limit=10&p='+page+'&search='+search + order; 
		bt.pub.get_data(data,function(rdata){
			if(callback) callback(rdata);
		})
	},	
	get_list:function(page,search,callback){
		if(page == undefined) page = 1
		search = search == undefined ? '':search;
		var order = bt.get_cookie('order') ? '&order=' + bt.get_cookie('order'):'';
		
		var data = 'tojs=firewall.get_list&table=firewall&limit=10&p='+page+'&search='+search + order; 
		bt.pub.get_data(data,function(rdata){
			if(callback) callback(rdata);
		})
	},
	get_logs_size:function(callback){
		if(bt.os=='Linux'){
			bt.files.get_dir_size('/www/wwwlogs',function(rdata){
				if(callback) callback(rdata);
			})
		}
	},
	get_ssh_info : function(callback){
		bt.send('GetSshInfo','firewall/GetSshInfo',{},function(rdata){
			if(callback) callback(rdata);
		})
	},
	set_mstsc : function(port,callback){
		bt.confirm({msg:lan.firewall.ssh_port_msg,title:lan.firewall.ssh_port_title},function(){
			loading = bt.load(lan.public.the);
			bt.send('SetSshPort','firewall/SetSshPort',{port:port},function(rdata){
                loading.close();
                bt.msg(rdata);
				if(callback) callback(rdata);
			})
		})
	},
	ping : function(status,callback){
		var msg = status==0?lan.firewall.ping_msg:lan.firewall.ping_un_msg;
		layer.confirm(msg,{closeBtn:2,title:lan.firewall.ping_title,cancel:function(){
			if(callback) callback(-1); //取消
		}},function(){
			loading = bt.load(lan.public.the);
			bt.send('SetPing','firewall/SetPing',{status:status},function(rdata){
				loading.close();
				if(callback) callback(rdata);
			})
		},function(){
			if(callback) callback(-1); //关闭
		})
	},
	set_mstsc_status : function(status,callback){
		var msg = status==1?lan.firewall.ssh_off_msg:lan.firewall.ssh_on_msg;
		layer.confirm(msg,{closeBtn:2,title:lan.public.warning,cancel:function(){			
			if(callback) callback(-1); //取消
		}},function(){
			loading = bt.load(lan.public.the);
			bt.send('SetSshStatus','firewall/SetSshStatus',{status:status},function(rdata){
				loading.close();
				if(callback) callback(rdata);
			})
		},function(){
			if(callback) callback(-1); //关闭
		})
	},
	add_accept_port : function(type,port,ps,callback){
		var action = "AddDropAddress";
		if(type == 'port'){
            ports = port.split(':');
            if (port.indexOf('-') != -1) ports = port.split('-');
			for(var i=0;i<ports.length;i++){
				if(!bt.check_port(ports[i])){
					layer.msg(lan.firewall.port_err,{icon:5});
					return;
				}
			}
			action = "AddAcceptPort";
		}
		
		if(ps.length < 1){
			layer.msg(lan.firewall.ps_err,{icon:2});
			return -1;
		}
		loading = bt.load();
		bt.send(action,'firewall/'+action,{port:port,type:type,ps:ps},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})		
	},
	del_accept_port : function(id,port,callback){
		var action = "DelDropAddress";
		if(port.indexOf('.') == -1){
			action = "DelAcceptPort";
		}		
		bt.confirm({msg:lan.get('confirm_del',[port]),title: lan.firewall.del_title}, function(index) {
			var loadT = bt.load(lan.public.the_del);
			bt.send(action,'firewall/'+action,{id:id,port:port},function(rdata){
				loadT.close();
				if(callback) callback(rdata);
			})
		});
	},
	clear_logs_files:function(callback){
		var loadT = bt.load(lan.firewall.close_the);
        bt.send('CloseLogs', 'files/CloseLogs', {}, function (rdata) {
			if(callback) callback(rdata);
		})
	},
	clear_logs : function(callback){
		bt.confirm({msg:lan.firewall.close_log_msg,title:lan.firewall.close_log},function(){
			var loadT = bt.load(lan.firewall.close_the);
            bt.send('delClose', 'ajax/delClose', {}, function (rdata) {
                loadT.close();
                if (callback) {
                    callback(rdata);
                } else {
                    bt.msg(rdata)
                }
			})
		})
	}	
}

bt.soft = {
	pub :{
		wxpayTimeId : 0
	},
	php : {
		get_config:function(version,callback){ //获取禁用函数,扩展列表
			//var loading = bt.load();
			bt.send('GetPHPConfig','ajax/GetPHPConfig',{version:version},function(rdata){				
				//loading.close();
				if(callback) callback(rdata);
			})
		},
		get_limit_config:function(version,callback){ //获取超时限制,上传限制
			var loading = bt.load();
			bt.send('get_php_config','config/get_php_config',{version:version},function(rdata){
				loading.close();
				if(callback) callback(rdata);
			})
		},
		get_php_config:function(version,callback){
			var loading = bt.load();
			bt.send('GetPHPConf','config/GetPHPConf',{version:version},function(rdata){				
				loading.close();
				if(callback) callback(rdata);
			})			
		},
		install_php_lib:function(version,name,title,callback){
			bt.confirm({msg:lan.soft.php_ext_install_confirm.replace('{1}',name),title:'安装【'+ name +'】'},function(){
				name = name.toLowerCase();
				var loadT = bt.load(lan.soft.add_install);
				bt.send('InstallSoft','files/InstallSoft',{name:name,version:version,type:"1"},function(rdata){
					loadT.close();				
					if(callback) callback(rdata);
					bt.msg(rdata);
				});			
				fly("bi-btn");			
			});
		},
		un_install_php_lib:function(version,name,title,callback){
			bt.confirm({msg:lan.soft.php_ext_uninstall_confirm.replace('{1}',name),title:'卸载【'+ name +'】'},function(){
				name = name.toLowerCase();
				var data = 'name='+name+'&version='+version;
				var loadT = bt.load();
				bt.send('UninstallSoft','files/UninstallSoft',{name:name,version:version},function(rdata){
					loadT.close();
					if(callback) callback(rdata);
					bt.msg(rdata);
				});
			});
		},
		set_upload_max:function(version,max,callback){			
			var loadT =  bt.load(lan.soft.the_save);
			bt.send('setPHPMaxSize','config/setPHPMaxSize',{version:version,max:max},function(rdata){
				loadT.close();
				if(callback) callback(rdata);
			})
		},
		set_php_timeout:function(version,time,callback){
			var loadT = bt.load(lan.soft.the_save);
			bt.send('setPHPMaxTime','config/setPHPMaxTime',{version:version,time:time},function(rdata){
				loadT.close();
				if(callback) callback(rdata);
			});
		},		
		disable_functions:function(version,fs,callback){		
			var loadT = bt.load();
			bt.send('setPHPDisable','config/setPHPDisable',{version:version,disable_functions:fs},function(rdata){
				loadT.close();
				if(callback) callback(rdata);
			});
		},
		get_fpm_config:function(version,callback){
			var loadT = bt.load();
			bt.send('getFpmConfig','config/getFpmConfig',{version:version},function(rdata){
				loadT.close();
				if(callback) callback(rdata);
			})
		},
		set_fpm_config:function(version,data,callback){
			var loadT = bt.load();
			data.version = version;
			bt.send('setFpmConfig','config/setFpmConfig',data,function(rdata){
				loadT.close();
				if(callback) callback(rdata);
			})			
		},
		get_php_status:function(version,callback){
			var loadT = bt.load();
			bt.send('GetPHPStatus','ajax/GetPHPStatus',{version:version},function(rdata){
				loadT.close();
				if(callback) callback(rdata);
			})
		},
      			// 获取PHP_session
		get_php_session:function(version,callback){
			var loadT = bt.load();
			bt.send('GetSessionConf','config/GetSessionConf',{version:version},function(res){
				loadT.close();
				if(callback) callback(res);
			});
		},
		// 设置PHP_session文件
		set_php_session:function (obj,callback){
			var loadT = bt.load();
			bt.send('SetSessionConf','config/SetSessionConf',obj,function(res){
				loadT.close();
				if(callback) callback(res);
			});
		},
		// 获取PHP_session清理信息
		get_session_count:function(callback){
			var loadT = bt.load();
			bt.send('GetSessionCount','config/GetSessionCount',{},function(res){
				loadT.close();
				if(callback) callback(res);
			});
		},
		// 清理php_session
		clear_session_count:function(obj,callback){
			bt.confirm({msg:obj.msg,title:obj.title},function(){
				var loadT = bt.load();
				bt.send('DelOldSession','config/DelOldSession',{},function(res){
					loadT.close();
					if(callback) callback(res);
				})
			});
		},
		get_fpm_logs:function(version,callback){
			var loadT = bt.load();
			bt.send('GetFpmLogs','ajax/GetFpmLogs',{version:version},function(logs){
				loadT.close();
				if(logs.status !== true){
					logs.msg = '';
				}
				if (logs.msg == '') logs.msg = '当前没有fpm日志.';
				if(callback) callback(logs);
			})		
		},
		get_slow_logs:function(version,callback){
			var loadT = bt.load();
			bt.send('GetFpmSlowLogs','ajax/GetFpmSlowLogs',{version:version},function(logs){
				loadT.close();
				if(logs.status !== true){
					logs.msg = '';
				}
				if (logs.msg == '') logs.msg = '当前没有慢日志.';
				if(callback) callback(logs);
			})
		}
	},
	redis : {
		get_redis_status:function(callback){
			var loadT = bt.load();
			bt.send('GetRedisStatus','ajax/GetRedisStatus',{},function(rdata){	
				loadT.close();
				if(callback) callback(rdata);
			});
		}
	},
	pro : {		
		conver_unit:function(name){
			var unit= '';
			switch (name){
				case "year":
					unit = "年";
					break;
				case "month":
					unit = "个月";
					break;
				case "day":
					unit = "天";
					break;
				case "1":
					unit = "1个月";
					break;
				case "3":
					unit = "3个月";
					break;
				case "6":
					unit = "6个月";
					break;
				case "12":
					unit = "1年";
					break;
				case "24":
					unit = "2年";
					break;
				case "36":
					unit = "3年";
					break;
				case "999":
					unit = "永久";
					break;
			}
			return unit;
		},
		get_product_discount_by:function(pluginName,callback){
			if(pluginName){
				bt.send('get_plugin_price','auth/get_plugin_price',{pluginName:pluginName},function(rdata){
					if(callback) callback(rdata)
				})
			}
			else{
				bt.send('get_product_discount_by','auth/get_product_discount_by',{},function(rdata){					
					if(callback) callback(rdata)
				})
			}
			
		},
		get_plugin_coupon:function(pid,callback){
            bt.send('check_pay_status','auth/check_pay_status',{id:pid},function(rdata){
				if(callback) callback(rdata);
			})
		},
		get_re_order_status:function(callback){
			bt.send('get_re_order_status','auth/get_re_order_status',{},function(rdata){
				if(callback) callback(rdata);
			})
		},
		get_voucher:function(pid,callback){
			if(pid){
				bt.send('get_voucher_plugin','auth/get_voucher_plugin',{pid:pid},function(rdata){
					if(callback) callback(rdata);
				})			
			}
			else{
				bt.send('get_voucher','auth/get_voucher',{},function(rdata){
					if(callback) callback(rdata);
				})
			}			
		},
		create_order_voucher:function(pid,code,callback){
			var loading =  bt.load();
			if(pid){
				bt.send('create_order_voucher_plugin','auth/create_order_voucher_plugin',{pid:pid,code:code},function(rdata){
					loading.close();
					if(callback) callback(rdata);
					bt.msg(rdata);
				})
			}else{
				bt.send('create_order_voucher','auth/create_order_voucher',{code:code},function(rdata){
					loading.close();
					if(callback){ 
						callback(rdata);
					}else{
						bt.soft.pro.update();
					}
				})
			}
		},
		create_order:function(config,callback){
			if(typeof config.pid != 'undefined'){				
				bt.send('get_buy_code','auth/get_buy_code',config,function(rdata){
					if(callback) callback(rdata);
				})
			}
			else{
				bt.send('create_order','auth/create_order',config,function(rdata){
					if(callback) callback(rdata);
				})
			}
		}
	},
	updata_commercial_view:function(){
		layer.closeAll();
		var html = '<div class="business-edition">\
			<div class="price-compare-item" style="margin-right:20px">\
				<div class="price-header">专业版</div>\
				<div class="title-wrap">\
					<p class="title-info">推荐个人及5人以下团队公司购买</p>\
				</div>\
				<div class="title-desc">\
					<p>包含所有<b>免费版</b>功能和：</p>\
					<p>宝塔系统加固，网站防篡改程序</p>\
					<p>网站监控报表，Apache防火墙</p>\
					<p>Nginx防火墙，宝塔负载均衡</p>\
					<p>MySQL主从复制，宝塔任务管理器</p>\
					<p>异常监控推送，微信小程序</p>\
					<p>宝塔数据同步工具</p>\
				</div>\
				<div class="price-wrap">\
					<div class="month">\
						<span class="price-unit">￥</span>\
						<span class="price-value">39.8</span>\
						<span class="price-ext">/月</span>\
					</div>\
					<div class="div-line"></div>\
					<div class="year">\
						<span class="price-unit">￥</span>\
						<span class="price-value">382</span>\
						<span class="price-ext">/年</span>\
					</div>\
				</div>\
				<button class="btn-price" data-type="pro">立即购买</button>\
			</div>\
			<div class="price-compare-item">\
				<div class="price-header">企业版<san class="recommend-tips"></span></div>\
				<div class="title-wrap">\
					<p class="title-info">推荐5人以上或企事业单位购买</p>\
				</div>\
				<div class="title-desc">\
					<p>包含所有<b>专业版</b>功能和：</p>\
					<p>1、提供在线客服工单协助</p>\
					<p>2、多用户管理插件（仅可查看日志）</p>\
					<p>3、后期还会有10+企业版专用插件</p>\
					<p>4、官方跟进响应的QQ群（需年付）</p>\
					<p>4、官方跟进响应的QQ群（需年付）</p>\
					<p>5、不定期线上运维培训（需年付）</p>\
				</div>\
				<div class="price-wrap">\
					<div class="month">\
						<span class="price-unit">￥</span>\
						<span class="price-value">148</span>\
						<span class="price-ext">/月</span>\
					</div>\
					<div class="div-line"></div>\
					<div class="year">\
						<span class="price-unit">￥</span>\
						<span class="price-value">999</span>\
						<span class="price-ext">/年</span>\
					</div>\
				</div>\
				<button class="btn-price" data-type="ltd">立即购买</button>\
			</div>\
		</div>';
		layer.open({
			type: 1 
			,closeBtn:2
			,area: ['800px', '640px']
			,title: '升级付费版，对应版本插件，免费使用 '
			,shade: 0.6 
			,anim: 0
			,content:html,
			success:function(layero,index){
				$('.btn-price').click(function(){
					var _type = $(this).attr('data-type');
					if(_type == 'pro'){
						bt.soft.updata_pro();
						layer.close(index);
					}else{
						bt.soft.updata_ltd();
						layer.close(index);
					}
				})
			}
		})
	},
	get_index_renew:function(){
	 	bt.soft.get_product_renew(function(res){
            var html = $('<div><div>');
            if(res.length >0){
                bt.soft.each(res,function(index,item){
                    html.append($('<p><span class="glyphicon glyphicon-alert" style="color: #f39c12; margin-right: 10px;"></span>' + item.msg +'&nbsp;&nbsp;&nbsp;&nbsp;<a href="javascript:;" class="set_messages_status" style="color:#777">[ 忽略提示 ]</a></p>').data(item))
                });
                $('#messageError').show().html(html);
                $('.set_messages_status').click(function(){
                    var data = $(this).parent().data(),that = this;
                    bt.soft.set_product_renew_status({id:data.id,state:0},function(rdata){
                        if(!res.status){
                            console.log(that);
                            $(that).parent().remove();
                        }
                        bt.msg(rdata);
                    });
                })
            }  

	 	});
	},
	// 获取产品续费状态
	get_product_renew:function(callback){
	    $.get('/message/get_messages',function(res){
	        if(res.status === false){
	            layer.msg(res.msg,{icon:2});
	            return false;
	        }
            if(callback) callback(res)
        });
	},
	set_product_renew_status:function(data,callback){
	    $.post('/message/status_message',{id:data.id,state:data.state},function(res){
	        if(res.status === false){
	            layer.msg(res.msg,{icon:2});
	            return false;
	        }
            if(callback) callback(res)
        });
	},
	// 产品支付视图(配置参数)
	product_pay_view:function(config){
	    if(!bt.get_cookie('bt_user_info')){
	        bt.pub.bind_btname(function(){
                window.location.reload();
            });
	        return false;
	    }
		if(typeof config == "string") config = JSON.parse(config);
		config = $.extend({
			plugin:null,
			renew:null,
			active:'',
			type:'',
			pro: parseInt(bt.get_cookie('pro_end')),
			ltd: parseInt(bt.get_cookie('ltd_end'))}
			,config);
		var title = '',that = this,endTime = null;
		if(!config.is_alone){
			if(config.plugin){ // 条件：当前为插件
				title = (config.renew == -1?'购买':'续费') + config.name;
				ndTime = config.renew != -1?config.renew:null
			}else if(config.pro == -1 && config.ltd == -1){  // 条件：专业版和企业版都没有购买过
				title = '升级付费版，对应版本插件，免费使用';
			}else if(config.ltd > 0){  // 条件：企业版续费
				title = '续费' +(config.name == ''?'宝塔专业版':config.name);
				endTime = config.ltd;
			}else if(config.pro > 0 || config.pro == -2){  // 条件：专业版续费
				title = '续费' + (config.name == ''?'宝塔专业版':config.name);
				endTime = config.pro;
			}else if(config.ltd == -2){
				title = '续费' + (config.name == ''?'宝塔专业版':config.name);
				endTime = config.ltd;
			}
		}else{
			title = (config.ltd>0?'续费':'购买')+'宝塔企业版';
		}
		bt.open({
			type:1,
			title:title,
			area:['650px','760px'],
			shadeClose:false,
			content:'<div class="libPay plr15" id="pay_product_view">\
				<div class="libPay-item" style="margin-bottom:20px">\
					<span class="bindUser">绑定用户：<span></span></span>\
					<span class="endTime">过期时间：<span></span></span>\
				</div>\
				<div class="libPay-item" id="libPay-type">\
					<div class="li-tit c3">类型</div>\
					<div class="li-con c5"></div>\
					<div class="pro-tips">温馨提示：了解专业版和企业版的区别，请点击<a href="https://www.bt.cn/download/linux.html#info" target="_blank" class="btlink ml5">查看详情</a>'+ (!(config.ltd == -1 && config.pro == -1)?'、<a href="https://www.bt.cn/bbs/thread-50342-1-1.html" target="_blank" class="btlink ml5">《专业版和企业版切换教程》</a>':'') +'</div>\
				</div>\
				<div class="libPay-item" id="libPay-mode">\
					<div class="li-tit c4">付款方式</div>\
					<div class="li-con c5"></div>\
				</div>\
				<div class="libPay-item" id="libPay-content">\
					<div class="li-tit c4">开通时长</div>\
					<div class="li-con c5"></div>\
				</div>\
				<div class="libPay-item" id="libPay-pay"></div>\
				<div class="libPay-item" id="libPay-tips"><p style="display:inline-block;position:absolute;bottom:17px;left:0;width:100%;text-align:center;color:red">注：如需购买多台永久授权专业版，请登录宝塔官网购买。<a class="btlink" href="https://www.bt.cn/download/linuxpro.html#price" target="_blank">去宝塔官网</a></p></div>\
				<div class="libPay-mask"></div>\
			</div>',
			success:function(indexs,layers){
			    var bt_user_info = bt.get_cookie('bt_user_info');
			    if(!bt_user_info){
			        bt.pub.get_user_info(function(res){
			            $('.bindUser span').html(res.data.username +'<a href="javascript:;" class="btlink ml5">更换</a>');
			        });
			    }else{
			        $('.bindUser span').html(JSON.parse(bt_user_info).data.username +'<a href="javascript:;" class="btlink ml5">更换</a>');
			    }
				endTime != null?$('.endTime span').html(endTime > parseInt(new Date().getTime() /1000)?bt.format_data(endTime):'<i style="color:red;font-style:inherit">已过期</i>'):$('.endTime').hide();
				$('.bindUser').on('click','a',function(){
					bt.pub.bind_btname(function(){
					 	bt.soft.product_pay_view(config);
					 });
				});
			    var arry = [];
				if(config.plugin) arry.push({title:config.name,name:config.name,ps:'单款插件',pid:config.pid,active:((config.pro < 0 && config.ltd < 0) || (config.type == 12 && config.ltd<0)?true:false)});
				if((((config.pro > 0  || config.pro == -2 || config.ltd < 0) && ((config.ltd > 0 && config.ltd != config.pro) || config.ltd < 0) && config.type != 12) || config.limit == 'pro' || (config.ltd < 0 && config.pro == -1)) && config.type != 12 && ((config.ltd < 0 && config.pro > 0) || (config.ltd < 0 && config.pro < 0))){
					arry.push({title:'<span class="pro-font-icon"></span>',name:'',pid:'',ps:'推荐个人购买',active:  (((config.type == 8 && !config.plugin) || config.limit == 'pro' || (config.pro > 0 || config.pro == -2)) && config.ltd < 0 && (config.ltd == -2?(config.pro == -2?false:true):true))});
				}
			
				if((((config.ltd > 0 || config.ltd == -2 || config.pro == -2) || (config.ltd == -1 && config.pro == -1) || config.limit == 'ltd') && (config.pro < 0 || (config.pro >= 0 && config.ltd >0))) || (config.is_alone && config.pid == 100000032)){
					arry.push({title:'<span class="ltd-font-icon"></span>',name:'宝塔面板企业版',ps:'推荐企业购买',pid:100000032,recommend:true,active:((config.type == 12 && !config.plugin && config.ltd > 0) || config.limit == 'ltd' || (config.renew == config.ltd && config.ltd > 0)? true:false)});
				}
				if(config.type == 12 && config.pro >= 0 && config.ltd < 0) $('.pro-tips').html('温馨提示：专业版升级企业版需要手动结算当前专业版授权，<a href="https://www.bt.cn/bbs/thread-50342-1-1.html" target="_blank" class="btlink">《专业版和企业版切换教程》</a>').css('color','red');
				$('#libPay-type .li-con').append(that.product_pay_swicth('type',arry));
				if(config.source) bt.set_cookie('pay_source',config.source);
				that.each(arry,function(index,item){ 
					if(item.active){
						that.product_pay_page_refresh($.extend({condition:1},item));
					}
				});
			},
			end:function(){
				clearInterval(bt.soft.pub.wxpayTimeId);
				bt.clear_cookie('pay_source');
			}
		});
	},
    product_cache:{}, //产品周期缓存
    order_cache:{},
    // 获取产品周期 ，并进行对象缓存
    get_product_discount_cache:function(config,callback){
        var that = this;
        if(typeof this.product_cache[config.pid] != "undefined"){
            if(callback) callback(this.product_cache[config.pid]);
        }else{
            bt.soft.pro.get_product_discount_by(config.name,function(rdata){
                if(typeof rdata.status === "boolean"){
                    if(!rdata.status) return false;
                }
                that.product_cache[config.pid] = rdata;
                setTimeout(function(){ delete that.product_cache[config.pid] },60000);
                if(callback) callback(rdata);
            });
        }
    },
    // 产品页面刷新
    product_pay_page_refresh: function (config){
        var condition = config.condition, that = this;
        switch (condition){
            case 1:
                var loadT = bt.load();
                bt.soft.pro.get_voucher(config.pid, function (rdata) {
                    loadT.close();
                    var _arry = [{ title: '微信支付', condition: 2 },{ title: '支付宝支付', condition: 3 }, { title: '抵扣劵', condition: 4 }];
                    if (rdata == null) rdata = [];
                    _arry[rdata.length > 0 ? '2' : '0'].active = true;
                    $('#libPay-mode .li-con').empty().append(
                        that.product_pay_swicth('payment', {
                            name: config.name,
                            pid: config.pid,
                            data: _arry,
                            voucher_data: rdata
                        })
                    );
                    config.condition = (rdata.length > 0?4:2) 
                    if (rdata.length > 0) config.voucher_data = rdata;
                    that.product_pay_page_refresh(config);
                });
                break;
            case 2:
            case 3:
                console.log(config)
                $('#libPay-content .li-tit').text('开通时长');
                config.pay = condition;
                if (config.pid == '100000030') {
                    $('#libPay-tips').show();
                } else {
                    $('#libPay-tips').hide();
                }
                var loadT = bt.load();
                bt.soft.get_product_discount_cache(config,function (rdata){
                    loadT.close();
					var _arry = [],index = $('#libPay-content .pay-cycle-btn.active').index() || 0;
					if(index < 0) index = 0
                    try {
                        delete rdata.pid
                    } catch (error) {
                        console.log(rdata.pid);
                    }
                    that.each(rdata, function (key, item) {
                        _arry.push($.extend({ cycle: parseInt(key) }, item));
                    });
                    _arry[index].active = true;
                    $('#libPay-content .li-con').empty().append(
                        that.product_pay_swicth('time',{ name: config.name, pid: config.pid, data: _arry})
                    );
                    config.condition = 5;
                    config = $.extend(config, _arry[index]);
                    that.product_pay_page_refresh(config);
                });
                break;
            case 4:
                clearInterval(bt.soft.pub.wxpayTimeId);
                $('#libPay-content .li-tit').text('抵扣劵列表');
                $('#libPay-pay').removeAttr('data-qecode');
                $('#libPay-tips').hide();
                function callback(rdata) {
                    if(rdata == null)  rdata = [];
                    if(rdata.length == 0){
                        $('#libPay-content .li-con').empty()
                        that.product_pay_page_refresh({ condition: 6, pid: '', code: false });
                        return false;
                    }
                    rdata[0].active = true;
                    $('#libPay-content .li-con').empty().append(
                        that.product_pay_swicth('voucher', {
                            name: config.name,
                            pid: config.pid,
                            data: rdata
                        })
                    );
                    config.condition = 6;
                    that.product_pay_page_refresh($.extend(config, rdata[0]));
                }
                if (config.voucher_data) {
                    callback(config.voucher_data);
                } else {
                    bt.soft.pro.get_voucher(config.pid, function (rdata) {
                        callback(rdata);
                    });
                }
                break;
            case 5:
                $('#libPay-content .li-con').css('height', 'auto');
                $('.libPay-mask').show();
                if($('#libPay-pay').attr('data-qecode')) {
                    var qcode = $('#libPay-content li').eq(config.dom_index).data('qrcode-url');
                    $('#libPay-pay').find('.sale-price').html((config.price).toFixed(2));
                    $('#libPay-pay').find('.cost-price').css('display', (config.sprice > config.price ? 'inline-block' : 'none')).html((config.sprice).toFixed(2) + '元');
                    $('#libPay-pay').find('#PayQcode').html('<div class="loading">加载中，请稍后...</div>');
                    if (qcode) {
                        $('#libPay-pay').find('#PayQcode').empty().qrcode(qcode);
                        that.product_pay_monitor({ pid: config.pid, name: config.name });
                        $('.libPay-mask').hide();
                        return false;
                    }
                }else{
                    $('#libPay-pay').html('<div class="cloading">加载中，请稍后...</div>');
				}
				var paream = {pid:config.pid,cycle:config.cycle},pay_source = bt.get_cookie('pay_source');
				if(pay_source) paream.source = bt.get_cookie('pay_source');
				if(!paream.pid) delete paream.pid;
                that.pro.create_order(paream,function (rdata){
                    if (rdata.status === false){
                        bt.set_cookie('force', 1);
                        if (soft) soft.flush_cache();
                        layer.msg(rdata.msg, { icon: 2 });
                        return;
                    }
                    config.pay = parseInt($('#libPay-mode .pay-cycle-btn.active').data('condition'));
                    // 二维码显示界面
                    $('#libPay-pay').empty().append(that.product_pay_swicth((config.pay == 2?'wechat':'alipay'),$.extend({ data: config.pay == 2?rdata.msg:rdata.ali_msg }, config)));
                });
                break;
            case 6:
                var _html = $('<div class="paymethod-submit text-center"></div>'), _button = $('<button class="btn btn-success btn-sm f16 ' + (config.code ? '' : 'disabled') + '" style="width: 200px; height: 40px;">' + (config.code ? '提交' : '暂无抵扣劵') + '</button>');
                _button.click(function (ev) {
                    if (!config.code){
                        layer.msg('无可用优惠券');
                        return false;
                    }
                    bt.soft.pro.create_order_voucher(config.pid, config.code, function (rdata) {
                        layer.closeAll();
                        bt.set_cookie('force', 1);
                        if (soft) soft.flush_cache();
                        bt.msg(rdata);
                    });
                });
                $('#libPay-pay').empty().append(_html.append(_button));
                break;
        }
    },
    // 产品购买，渲染方法
    product_pay_swicth: function (type,config){
        var _html = '', that = this;
        switch (type) {
            case 'type': // 产品类型（配置参数）
                _html = $('<ul class="li-c-item"></ul>');
                this.each(config, function (index, item) {
                    _html.append($('<li class="pay-cycle-btn ' + (item.active ? 'active' : '') + '">' +
                        (item.recommend ? '<span class="recommend-pay-icon"></span>' : '') +
                        '<span class="item-name pull-left">' + item.title + '</span>' +
                        '<span class="item-info f12 pull-right c7">' + item.ps + '</span>' +
                        '</li>').data(item).click(function(ev){
                            var data = $(this).data();
                            if (!$(this).hasClass('active')) that.product_pay_page_refresh($.extend({ condition: 1 }, data));
                            $(this).addClass('active').siblings().removeClass('active');

                        }));
                });
                break;
            case 'payment':// 产品付款方式
                _html = $('<ul class="pay-btn-group"></ul>');
                this.each(config.data, function (index, item) {
                    _html.append($('<li class="pay-cycle-btn ' + (item.active ? 'active' : '') + '" data-condition="' + item.condition + '"><span>' + item.title + '</span></li>').data($.extend({ pid: config.pid, name: config.name }, item)).click(function (ev) {
                        var data = $(this).data();
                        if (!$(this).hasClass('active')) that.product_pay_page_refresh($.extend({ condition: $(this).attr('data-condition') }, data));
                        $(this).addClass('active').siblings().removeClass('active');
                    }));
                });
                break;
            case 'time': // 产品开通时长（配置参数）
                _html = $('<ul class="pay-btn-group"></ul>');
                this.each(config.data, function (index, item) {
                    _html.append($('<li class="pay-cycle-btn ' + (item.active ? 'active' : '') + '"><span>' + that.pro.conver_unit(item.cycle + '') + '</span>' + (item.discount != 1 ? '<em>' + (item.discount * 10).toFixed(1) + '折</em>' : '') + '</li>').data($.extend({ pid: config.pid, dom_index: index }, item)).click(function (ev) {
                        var data = $(this).data();
                        if (!$(this).hasClass('active')) that.product_pay_page_refresh($.extend({ condition: 5 }, data));
                        $(this).addClass('active').siblings().removeClass('active');
                    }));
                });
                break;
            case 'voucher':// 产品抵扣卷（配置参数）
                _html = $('<ul class="pay-btn-group"></ul>');
                this.each(config.data, function (index, item){
                    _html.append($('<li class="pay-cycle-btn ' + (item.active ? 'active' : '') + '"><span>' + (item.unit == 'month' && item.cycle == 999 ? '永久' : (item.cycle + that.pro.conver_unit(item.unit))) + '</span></li>').data($.extend({ pid: config.pid }, item)).click(function (ev) {
                        var data = $(this).data();
                        $(this).addClass('active').siblings().removeClass('active');
                        that.product_pay_page_refresh($.extend({ condition: 6 }, data));
                    }));
                });
                break;
            case 'wechat':
            case 'alipay':
                _html = $('<div class="lib-price-box text-center">' +
                    '<span class="lib-price-name f14"><b>总计</b></span>' +
                    '<span class="price-txt"><b class="sale-price">' + (config.price).toFixed(2) + '</b>元</span>' +
                    '<s class="cost-price" style="display: ' + (config.sprice > config.price ? 'inline-block' : 'none') + ';">' + (config.sprice).toFixed(2) + '元</s></div>' +
                    '<div class="lib-price-box text-center">' +
                    '<div class="paymethod"><div class="pay-wx" id="PayQcode"></div>' +
                    '<div class="pay-wx-info f16 text-center"><span class="wx-pay-ico mr5 '+ type +'"></span><span>'+ (type == 'wechat'?'微信':'支付宝') +'扫码支付</span></div></div></div>');
                $(_html).find('#PayQcode').qrcode(config.data);
                $('.libPay-mask').hide();
                that.product_pay_monitor({ pid: config.pid, name: config.name });
                break;
        }
        return _html;
    },
	// 支付状态监听
	product_pay_monitor:function(config){
		var that = this;
		function callback(rdata){
			if(rdata.status){
				clearInterval(bt.soft.pub.wxpayTimeId);
				layer.closeAll();
				var title = '';
				if(config.pid == 100000032 || config.pid === ''){
					title = config.pid === ''?'专业版支付成功！':'企业版支付成功！';
					setTimeout(function(){
						bt.set_cookie('force',1);
						if(soft) soft.flush_cache();
						location.reload(true);
					},2000);   // 需要重服务端重新获取软件列表，并刷新软件管理浏览器页面
				}else{
					title = config.name + '插件支付成功！';
					setTimeout(function(){
						bt.set_cookie('force',1);
						if(soft) soft.flush_cache();
						location.reload(true);
					},2000);   // 需要重服务端重新获取软件列表，
				}
				bt.msg({ msg:title, icon: 1,shade: [0.3, "#000"] });
			}
		}
		clearInterval(bt.soft.pub.wxpayTimeId);
		function intervalFun(){
			if(config.pid){
				that.pro.get_plugin_coupon(config.pid,callback);
			}else{
				that.pro.get_re_order_status(callback);
			}
		}
		intervalFun();
		bt.soft.pub.wxpayTimeId = setInterval(function () {
			intervalFun();
		},2500);
	},
	updata_ltd:function(is_alone){
		var param = {name:'宝塔面板企业版',pid:100000032,limit:'ltd'};
		if(is_alone || false) $.extend(param,{source:5,is_alone:true});
		bt.soft.product_pay_view(param);
	},	
	updata_pro:function(){
		bt.soft.product_pay_view({name:'',pid:'',limit:'pro'});
	},
	//遍历数组和对象
	each:function(obj, fn){
		var key,that = this;
		if(typeof fn !== 'function') return that;
		obj = obj || [];
		if(obj.constructor === Object){
			for(key in obj){
			if(fn.call(obj[key], key, obj[key])) break;
			}
		} else {
			for(key = 0; key < obj.length; key++){
			if(fn.call(obj[key], key, obj[key])) break;
			}
		}
		return that;
	},
    re_plugin_pay_other: function (pluginName, pid, type,price) {
        bt.pub.get_user_info(function (rdata) {
            if (!rdata.status) {
                bt.pub.bind_btname(0, function (rdata) {
                    
                })
                return;
            }
            var txt = '购买';
            if (type) txt = '续费';
            var payhtml = '<div class="libPay" style="padding:15px 30px 30px 30px">\
					<div class="libpay-con">\
						<div class="payment-con">\
							<div class="pay-weixin">\
								<div class="libPay-item f14 plr15">\
									<div class="li-tit c4">'+txt+'时长</div>\
									<div class="li-con c6" id="PayCycle"><ul class="pay-btn-group">\
                                        <li class="pay-cycle-btn active" onclick="bt.soft.get_rscode_other('+pid+','+price+',1,'+type+')"><span>1个月</span></li>\
                                        <li class="pay-cycle-btn" onclick="bt.soft.get_rscode_other('+ pid + ',' + price + ',3,' + type +')"><span>3个月</span></li>\
                                        <li class="pay-cycle-btn" onclick="bt.soft.get_rscode_other('+ pid + ',' + price + ',6,' + type +')"><span>6个月</span></li>\
                                        <li class="pay-cycle-btn" onclick="bt.soft.get_rscode_other('+ pid + ',' + price + ',12,' + type +')"><span>1年</span></li>\
                                    </ul></div>\
								</div>\
								<div class="lib-price-box text-center"><span class="lib-price-name f14"><b>总计</b></span><span class="price-txt"><b class="sale-price"></b>元</span><s class="cost-price"></s></div>\
								<div class="paymethod">\
									<div class="pay-wx"></div>\
									<div class="pay-wx-info f16 text-center"><span class="wx-pay-ico mr5"></span>微信扫码支付</div>\
								</div>\
							</div>\
						</div>\
					</div>\
				</div>';

            layer.open({
                type: 1,
                title: txt + pluginName,
                area: ['616px', '450px'],
                closeBtn: 2,
                shadeClose: false,
                content: payhtml
            });
            bt.soft.get_rscode_other(pid, price, 1,type)
            setTimeout(function () {
                $(".pay-btn-group > li").unbind('click').click(function () {
                    $(this).addClass("active").siblings().removeClass("active");
                });
            }, 100);
        })
    },
    get_rscode_other: function (pid, price, cycle,type) {
        var loadT = layer.msg('正在获取支付信息...', { icon: 16, time: 0, shade: 0.3 });
        $.post('/auth?action=create_plugin_other_order', { pid: pid, cycle: cycle,type:type }, function (rdata) {
            layer.close(loadT);
            if (!rdata.status) {
                layer.closeAll();
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
                return;
            }

            if (!rdata.msg.code) {
                layer.closeAll();
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
                soft.flush_cache();
                return;
            }
            $(".sale-price").text((price * cycle).toFixed(2))
            $(".pay-wx").html('');
            $(".pay-wx").qrcode(rdata.msg.code);
            bt.set_cookie('other_oid',rdata.msg.oid)
            bt.soft.get_order_stat(rdata.msg.oid,type);
        });
    },
    get_order_stat: function (order_id,type) {
        if (bt.get_cookie('other_oid') != order_id) return;
        setTimeout(function () {
            $.post('/auth?action=get_order_stat', { oid: order_id,type:type }, function (stat) {
                if (stat == 1) {
                    layer.closeAll();
                    soft.flush_cache();
                    return;
                }

                if ($(".pay-btn-group").length > 0) {
                    bt.soft.get_order_stat(order_id,type);
                }
            });

        }, 1000)
    },
	get_index_list:function(callback){
		bt.send('get_index_list','plugin/get_index_list',{},function(rdata){
			if(callback) callback(rdata);
		})
	},
	set_sort_index:function(data,callback){
		var loading = bt.load();
		bt.send('sort_index','plugin/sort_index',{ssort:data},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},	
	get_soft_list:function(p, type,search,callback){
		if(p == undefined) p=1;
		if(type == undefined) type = 0;
		if(search == undefined) search = '';
		var force = bt.get_cookie('force');
        if (force == undefined) force = 0;
        p = p + ''
        if (p.indexOf('not_load') == -1) {
            var loading = bt.load(lan.public.the, 1);
        } else {
            var loading = null;
            p = p.split("not_load")[0];
        }
		
        bt.send('get_soft_list', 'plugin/get_soft_list', { p: p, type: type, tojs: 'soft.get_list', force: force, query: search }, function (rdata) {
            if (loading) loading.close();
			bt.set_cookie('force',0);
			bt.set_cookie('ltd_end',rdata.ltd);
			bt.set_cookie('pro_end',rdata.pro);
			if(callback) callback(rdata);
		})
	},
    to_index: function (name, callback) {       
        var status = $("#index_" + name).prop("checked") ? "0" : "1";
        if (name.indexOf('php-')>=0) {
            var verinfo = name.replace(/\./,"");
            status = $("#index_" + verinfo).prop("checked")?"0":"1";
        }       
		if(status==1){
			bt.send('add_index','plugin/add_index',{sName:name},function(rdata){
				rdata.time = 1000;
				if(!rdata.status) bt.msg(rdata);
				if(callback) callback(rdata);
			})
		}
		else{
			bt.send('remove_index','plugin/remove_index',{sName:name},function(rdata){
			rdata.time = 1000;
				if(!rdata.status) bt.msg(rdata);
				if(callback) callback(rdata);
			})
		}
	},
	add_make_args:function(name,init){
		name = bt.soft.get_name(name);
		pdata = {
			name:name,
			args_name: $("input[name='make_name']").val(),
			init: init,
			ps: $("input[name='make_ps']").val(),
			args: $("input[name='make_args']").val()
		}
		if(pdata.args_name.length < 1 || pdata.args.length < 1){
			layer.msg('自定义模块名称和参数不能为空!');
			return
		}
		loadT = bt.load('正在添加自定义模块...')
		bt.send('add_make_args','plugin/add_make_args',pdata,function(rdata){
			loadT.close();
			bt.msg(rdata);
			if(rdata.status){
			    bt.soft.loadOpen.close();
			    bt.soft.get_make_args(name)
			}
		})
	},
	show_make_args:function(name){
		name = bt.soft.get_name(name);
		var _aceEditor = '';
		bt.soft.loadOpen = bt.open({
			type: 1,
			title: '添加自定义选装模块',
			area: '500px',
			btn:[lan.public.submit,lan.public.close],
			content: '<div class="bt-form c6">\
				<from class="bt-form" id="outer_url_form" style="padding:30px 10px;display:inline-block;">\
					<div class="line">\
						<span class="tname">模块名称</span>\
						<div class="info-r">\
							<input name="make_name" class="bt-input-text mr5" type="text" placeholder="只能是字母、数字、下划线" style="width:350px" value="">\
						</div>\
					</div>\
					<div class="line">\
						<span class="tname">模块描述</span>\
						<div class="info-r">\
							<input name="make_ps" class="bt-input-text mr5" placeholder="30字以内的描述" type="text" style="width:350px" value="">\
						</div>\
					</div>\
					<div class="line">\
						<span class="tname">模块参数</span>\
						<div class="info-r">\
							<input name="make_args" class="bt-input-text mr5" type="text" placeholder="如：--add-module=/tmp/echo/echo-nginx-module-master" style="width:350px" value="">\
						</div>\
					</div>\
					<div class="line">\
						<span class="tname">前置脚本</span>\
						<div class="info-r">\
							<div id="preposition_shell" class="bt-input-text" style="height:300px;width:350px;font-size:11px;line-height:20px;"></div>\
						</div>\
					</div>\
				</from>\
			</div>',
			success:function(layer,index){
				_aceEditor = ace.edit('preposition_shell',{
					theme: "ace/theme/chrome", //主题
					mode: "ace/mode/sh", // 语言类型
					wrap: true,
					showInvisibles:false,
					showPrintMargin: false,
					showFoldWidgets:false,
					useSoftTabs:true,
					tabSize:2,
					showPrintMargin: false,
					readOnly:false
				});
				_aceEditor.setValue('# 在编译前执行的shell脚本内容，通常为第三方模块的依赖安装和源码下载等前置准备');
			},
			yes:function(){
				bt.soft.add_make_args(name,_aceEditor.getValue());
			}
		})
	},
	modify_make_args:function(name,args_name){
		name = bt.soft.get_name(name);
		var _aceEditor = '';
		bt.soft.loadOpen = bt.open({
			type: 1,
			title: '编辑自定义选装模块['+name+':'+args_name+']',
			area: '500px',
			btn:[lan.public.submit,lan.public.close],
			content: '<div class="bt-form c6">\
				<from class="bt-form" id="outer_url_form" style="padding:30px 10px;display:inline-block;">\
					<div class="line">\
						<span class="tname">模块名称</span>\
						<div class="info-r">\
							<input name="make_name" class="bt-input-text mr5" type="text" placeholder="只能是字母、数字、下划线" style="width:350px" value="'+bt.soft.make_data[args_name].name+'">\
						</div>\
					</div>\
					<div class="line">\
						<span class="tname">模块描述</span>\
						<div class="info-r">\
							<input name="make_ps" class="bt-input-text mr5" placeholder="30字以内的描述" type="text" style="width:350px" value="'+bt.soft.make_data[args_name].ps+'">\
						</div>\
					</div>\
					<div class="line">\
						<span class="tname">模块参数</span>\
						<div class="info-r">\
							<input name="make_args" class="bt-input-text mr5" type="text" placeholder="如：--add-module=/tmp/echo/echo-nginx-module-master" style="width:350px" value="'+bt.soft.make_data[args_name].args+'">\
						</div>\
					</div>\
					<div class="line">\
						<span class="tname">前置脚本</span>\
						<div class="info-r">\
							<div id="preposition_shell" class="bt-input-text" style="height:300px;width:350px;font-size:11px;line-height:20px;"></div>\
						</div>\
					</div>\
				</from>\
			</div>',
			success:function(layer,index){
				_aceEditor = ace.edit('preposition_shell',{
					theme: "ace/theme/chrome", //主题
					mode: "ace/mode/sh", // 语言类型
					wrap: true,
					showInvisibles:false,
					showPrintMargin: false,
					showFoldWidgets:false,
					useSoftTabs:true,
					tabSize:2,
					showPrintMargin: false,
					readOnly:false
				});
				_aceEditor.setValue(bt.soft.make_data[args_name].init);
			},
			yes:function(){
				bt.soft.add_make_args(name,_aceEditor.getValue());
			}
		})
	},
	set_make_args:function(_this,name,args_name){
		name = bt.soft.get_name(name);
		if($('.args_'+args_name)[0].checked){
			bt.soft.make_config.push(args_name)
		}else{
			index = bt.soft.make_config.indexOf(args_name)
			if(index === -1) return;
			bt.soft.make_config.splice(index,1);
		}
		index = bt.soft.make_config.indexOf('')
		if(index !== -1) bt.soft.make_config.splice(index,1);
		bt.send('set_make_args','plugin/set_make_args',{name:name,args_names:bt.soft.make_config.join("\n")},function(rdata){
			if(!rdata.status){
				bt.msg(rdata)
			}
		})
	},
	del_make_args:function(name,args_name){
		name = bt.soft.get_name(name);
		bt.confirm({msg:'真的要删除['+name+':'+args_name+']模块吗？',title:'删除['+name+':'+args_name+']模块!'},function(){
			loadT = bt.load('正在删除模块['+args_name+']...')
			bt.send('del_make_args','plugin/del_make_args',{name:name,args_name:args_name},function(rdata){
				bt.msg(rdata);
				bt.soft.get_make_args(name);
			});
		});
	},
	get_make_args:function(name){
		name = bt.soft.get_name(name);
		loadT = bt.load('正在获取可选模块...')
		bt.send('get_make_args','plugin/get_make_args',{name:name},function(rdata){
			loadT.close();
			var module_html = ''; 
			bt.soft.make_config = rdata.config.split("\n")
			bt.soft.make_data = {}
			for(var i=0;i<rdata.args.length;i++){
				bt.soft.make_data[rdata.args[i].name] = rdata.args[i]
				var checked_str = (bt.soft.make_config.indexOf(rdata.args[i].name)== -1?'':'checked="checked"')
				module_html += '<tr>\
									<td>\
										<input class="args_'+rdata.args[i].name+'" onclick="bt.soft.set_make_args(this,\''+name+'\',\''+rdata.args[i].name+'\')" type="checkbox" '+checked_str+' />\
									</td>\
									<td>'+ rdata.args[i].name +'</td><td>'+ rdata.args[i].ps +'</td>\
									<td>\
										<a onclick="bt.soft.modify_make_args(\''+name+'\',\''+rdata.args[i].name+'\')" class="btlink">编辑</a>\
										| <a onclick="bt.soft.del_make_args(\''+name+'\',\''+rdata.args[i].name+'\')" class="btlink">删除</a>\
									</td>\
								</tr>';
			}
			$(".modules_list").html(module_html);
		});
	},
	check_make_is: function(name){
		name = bt.soft.get_name(name);
		var shows = ["nginx",'apache','mysql','php']
		for(var i=0;i<shows.length;i++){
			if(name.indexOf(shows[i]) === 0){
				return true
			}
		}
		return false
	},
	get_name: function(name){
		if(name.indexOf('php-') === 0){
			return 'php';
		}
		return name
	},
	install:function(name,that){
		var _this = this;
		if(bt.soft.is_install){
			layer.msg('正在安装其他软件，请稍后操作！',{icon:0});
			return false;
		}
        _this.get_soft_find(name, function (rdata) {
            var arrs = ['apache', 'nginx', 'mysql'];
            if ($.inArray(name, arrs) >= 0 || name.indexOf('php-')>=0) { 
                var SelectVersion = '', shtml = name;
                if (rdata.versions.length > 1) {
                    for (var i = 0; i < rdata.versions.length; i++) {
                        var item = rdata.versions[i];
                        SelectVersion += '<option>' + name + ' ' + item.m_version + '</option>';
                    }
                    shtml = "<select id='SelectVersion' class='bt-input-text' style='margin-left:10px'>" + SelectVersion + "</select>";
                }else {
                    shtml = "<span id='SelectVersion'>" + name + "</span>";
                }
                var loadOpen = bt.open({
                    type: 1,
                    title: name + lan.soft.install_title,
					area: '400px',
					btn:[lan.public.submit,lan.public.close],
                    content: "<div class='bt-form pd20 c6'>\
						<div class='version line' style='padding-left:15px'>"+ lan.soft.install_version + "：" + shtml+"</div>\
						<div class='fangshi line' style='padding-left:15px;margin-bottom:0px'>"+ lan.bt.install_type + "：<label data-title='" + lan.bt.install_src_title + "'>" + lan.bt.install_src + "<input type='checkbox'></label><label data-title='" + lan.bt.install_rpm_title + "'>" + lan.bt.install_rpm + "<input type='checkbox' checked></label></div>\
						<div class='install_modules' style='display: none;'>\
							<div style='margin-bottom:15px;padding-top:15px;border-top:1px solid #ececec;'><button onclick=\"bt.soft.show_make_args(\'" +name+ "\')\" class='btn btn-success btn-sm'>添加自定义模块</button></div>\
							<div class='select_modules divtable' style='margin-bottom:20px'>\
								<table class='table table-hover'>\
									<thead>\
										<tr>\
											<th width='10px'></th>\
											<th width='80px'>模块名称</th>\
											<th >模块描述</th>\
											<th width='80px'>操作</th>\
										</tr>\
									</thead>\
									<tbody class='modules_list'></tbody>\
								</table>\
							</div>\
						</div>\
					</div>",
					success:function(){
						$('.fangshi input').click(function () {
							$(this).attr('checked', 'checked').parent().siblings().find("input").removeAttr('checked');
							var type = $('.fangshi input:eq(0)').prop("checked") ? '0' : '1';
							if(type === '1') {
								$(".install_modules").hide();
								return;
							}
							if(bt.soft.check_make_is(name)){
								$(".install_modules").show();
								bt.soft.get_make_args(name);
							}
						});
					},
					yes:function(){
						loadOpen.close();
						var info = $("#SelectVersion").val().toLowerCase();
						name = info.split(" ")[0];
						version = info.split(" ")[1];
						var type = $('.fangshi input:eq(0)').prop("checked") ? '0' : '1';
						if (rdata.versions.length > 1) {
							_this.install_soft(rdata, version, type);
						} else {
							_this.install_soft(rdata, rdata.versions[0].m_version, type,that);
						}
					}
                });
            }
			else if (rdata.versions.length > 1){
				var SelectVersion = '';
				for(var i=0; i<rdata.versions.length; i++){
					var item = rdata.versions[i];
					SelectVersion += '<option>'+name+' '+item.m_version+'</option>';
                }
		        var loadOpen = bt.open({
					type: 1,
				    title: name + lan.soft.install_title,
				    area: '350px',
				    content:"<div class='bt-form pd20 pb70 c6'>\
						<div class='version line'>"+ lan.soft.install_version + "：<select id='SelectVersion' class='bt-input-text' style='margin-left:30px'>" + SelectVersion +"</select></div>\
                        <div class='bt-form-submit-btn'>\
							<button type='button' class='btn btn-danger btn-sm btn-title' onclick='layer.closeAll()'>"+lan.public.close+"</button>\
					        <button type='button' id='bi-btn' class='btn btn-success btn-sm btn-title bi-btn'>"+lan.public.submit+"</button>\
				        </div>\
				    </div>"
				})
				$("#bi-btn").click(function(){
					loadOpen.close();
					var info = $("#SelectVersion").val().toLowerCase();
					name = info.split(" ")[0];
					version = info.split(" ")[1];				
					_this.install_soft(rdata,version,0,that);
				});
            }            
			else{
				_this.install_soft(rdata,rdata.versions[0].m_version,0,that);
			}
		})	
	},
	is_loop_speed:true,
	is_install:false,
	//显示进度
	show_speed: function () {
		bt.send('get_lines','ajax/get_lines',{ 
			num: 10, 
			filename: "/tmp/panelShell.pl"
		},function(rdata){
			if ($("#install_show").length < 1) return;
			if (rdata.status === true) {
				$("#install_show").text(rdata.msg);
				$('#install_show').animate({scrollTop:$('#install_show').prop("scrollHeight")}, 400);
			}
			if(bt.soft.is_loop_speed){
				setTimeout(function(){
					bt.soft.show_speed();
				},1000)
			}
		});
	},
	loadT:null,
		//显示进度窗口
	show_speed_window: function(config,callback){
		if(!config.soft) config['soft'] = {type:10}
		if(config.soft.type == 5){ //使用消息盒子安装
			if (callback) callback();
			return false;
		}else if(config.soft.type == 10 && !config.status){ //第三方安装, 非安装，仅下载安装脚本
			if (callback) callback();
			return false;
		}
		layer.closeAll();
		bt.soft.loadT = layer.open({
			title: config.title || '正在执行安装脚本，请稍后...',
			type:1,
			closeBtn:false,
			maxmin:true,
			shade:false,
			skin:'install_soft',
			area:["500px",'300px'],
			content: "<pre style='width:500px;margin-bottom: 0px;height:100%;border-radius:0px; text-align: left;background-color: #000;color: #fff;white-space: pre-wrap;' id='install_show'>"+ config.msg +"</pre>",
			success:function(layers,index){
				$(config.event).removeAttr('onclick').html('正在安装');
				$('.layui-layer-max').hide();
				bt.soft.is_loop_speed = true;
				bt.soft.is_install = true;
				bt.soft.show_speed();
				if (callback) callback();
			},
			end:function(){
				bt.soft.is_install = false;
				bt.soft.is_loop_speed = false;
			},
			min:function(){
				$('.layui-layer-max').show();
			},
			restore:function(){
				$('.layui-layer-max').hide();
			}
		});
	},
	install_soft: function (item, version, type,that) { //安装单版本
        if (type == undefined) type = 0;
        var loadT = '';
		item.title = bt.replace_all(item.title,'-' + version,'');
		layer.confirm(item.type!=5?lan.soft.lib_insatll_confirm.replace('{1}',item.title):lan.get('install_confirm',[item.title,version]),{ title:item.type!=5?lan.soft.lib_install:lan.soft.install_title,icon:0,closeBtn:2},function(){
				layer.closeAll();
				bt.soft.show_speed_window({title:'正在安装'+ item.title +',请稍后...',msg:lan.soft.lib_install_the,soft:item,event:that},function(){
					if(item.type == 10) loadT = layer.msg('正在获取第三方软件安装信息，请稍后<img src="/static/img/ing.gif">', { icon: 16, time: 0, shade: [0.3, '#000'] });
					bt.send('install_plugin', 'plugin/install_plugin', { sName: item.name, version: version, type: type }, function (rdata) {
						if (rdata.size) {
							layer.close(loadT);
							bt.soft.install_other(rdata,status);
							return;
						}
						layer.close(bt.soft.loadT);
						bt.pub.get_task_count(function(rdata){
							if(rdata > 0 && item.type === 5) messagebox();
						});
						if(typeof soft != "undefined") soft.get_list();
						bt.msg(rdata);
					})
				})
		})
    },
    install_other: function (data) {
        layer.closeAll();
        var loadT = layer.open({
            type: 1,
            area: "500px",
            title: (data.update?"更新":"安装") + "第三方插件包",
            closeBtn: 2,
            shift: 5,
            shadeClose: false,
            btn:['确定' + (data.update ? "更新" : "安装"),'取消'],
            content: '<style>\
                        .install_three_plugin{padding:25px;}\
                        .plugin_user_info p { font-size: 14px;}\
                        .plugin_user_info {padding: 15px 30px;line-height: 26px;background: #f5f6fa;border-radius: 5px;border: 1px solid #efefef;}\
                        .btn-content{text-align: center;margin-top: 25px;}\
                    </style>\
                    <div class="bt-form c7  install_three_plugin pb70">\
                        <div class="plugin_user_info">\
                            <p><b>名称：</b>'+ data.title + '</p>\
                            <p><b>版本：</b>' + data.versions + '</p>\
                            <p><b>描述：</b>' + (data.update?data.update:data.ps) + '</p>\
                            <p><b>大小：</b>' + bt.format_size(data.size, true) + '</p>\
                            <p><b>开发商：</b>' + data.author + '</p>\
                            <p><b>来源：</b><a class="btlink" href="'+ data.home + '" target="_blank">' + data.home + '</a></p>\
                        </div>\
                        <ul class="help-info-text c7">\
                            '+ (data.update ? "<li>更新过程可能需要几分钟时间，请耐心等候!</li>" : "<li>安装过程可能需要几分钟时间，请耐心等候!</li><li>如果已存在此插件，将被替换!</li>")+'\
                        </ul>\
                    </div>',
            yes:function(index,event){
            	soft.input_zip(data.name,data.tmp_path,data);
            }
        });
    },
    update_soft: function (name,title, version, min_version,update_msg,type){
        var _this = this;
		var msg = "<li style='color:red;'>建议您在服务器负载闲时进行软件更新.</li>";
		if(name == 'mysql') msg = "<ul style='color:red;'><li>更新数据库有风险,建议在更新前,先备份您的数据库.</li><li>如果您的是云服务器,强烈建议您在更新前做一个快照.</li><li>建议您在服务器负载闲时进行软件更新.</li></ul>";
        if (update_msg) msg += '<div style="    margin-top: 10px;"><span style="font-size: 14px;font-weight: 900;">本次更新说明: </span><hr style="margin-top: 5px; margin-bottom: 5px;" /><pre>' + update_msg.replace(/(_bt_)/g, "\n") +'</pre><hr style="margin-top: -5px; margin-bottom: -5px;" /></div>';
        bt.show_confirm('更新[' + title + ']', '更新过程可能会导致服务中断,您真的现在就将[' + title + ']更新到[' + version + '.' + min_version + ']吗?', function () {
			bt.soft.show_speed_window({title:'正在更新到[' + title+'-'+version+'.'+min_version+'],请稍候...',status:true,soft:{type:parseInt(type)}},function(){
				bt.send('install_plugin', 'plugin/install_plugin', { sName: name, version: version, upgrade: version }, function (rdata) {
					if (rdata.size) {
						_this.install_other(rdata)
						return;
					}
					console.log(type);
					layer.close(bt.soft.loadT);	
					bt.pub.get_task_count(function(rdata){
						if(rdata > 0 && item.type === 5) messagebox();
					});
					if(typeof soft != "undefined") soft.get_list();
					bt.msg(rdata);	
				})
			})
		},msg);	
	},
	un_install:function(name){
		var _this = this;
		_this.get_soft_find(name,function(item){
			var version = '';
			for(var i=0;i<item.versions.length;i++){
				if(item.versions[i].setup && bt.contains(item.version,item.versions[i].m_version)){
					version = item.versions[i].m_version;
					if(version.indexOf('.') < 0) version += '.' + item.versions[i].version;
					break;
				}
			}
			var title = bt.replace_all(item.title,'-'+version,'');
			bt.confirm({msg:lan.soft.uninstall_confirm.replace('{1}',title).replace('{2}',version), title:lan.soft.uninstall,icon:3,closeBtn:2}, function() {
				var loadT = bt.load(lan.soft.lib_uninstall_the);
				bt.send('uninstall_plugin','plugin/uninstall_plugin',{sName:name,version:version},function(rdata){
					loadT.close();				
					bt.pub.get_task_count();				
					if(typeof soft != "undefined") soft.get_list();
					bt.msg(rdata);
				})
			})
		})
		
	},
	get_soft_find:function(name,callback){
		var loadT = bt.load();
		bt.send('get_soft_find','plugin/get_soft_find',{sName:name},function(rdata){
			loadT.close();			
			if(callback) callback(rdata);
		})
	},
	get_config_path:function(name){
		var fileName = '';
		if(bt.os=='Linux'){
            switch (name) {
                case 'mysql':
				case 'mysqld':
					fileName = '/etc/my.cnf';
					break;
				case 'nginx':
					fileName = '/www/server/nginx/conf/nginx.conf';
					break;
				case 'pureftpd':
					fileName = '/www/server/pure-ftpd/etc/pure-ftpd.conf';
					break;
				case 'apache':
					fileName = '/www/server/apache/conf/httpd.conf';
					break;
				case 'tomcat':
					fileName = '/www/server/tomcat/conf/server.xml';
					break;
				case 'memcached':
					fileName = '/etc/init.d/memcached';
					break;
				case 'redis':
					fileName = '/www/server/redis/redis.conf';
					break;
				case 'openlitespeed':
                    fileName = '/usr/local/lsws/conf/httpd_config.conf';
                    break;
				default:
					fileName = '/www/server/php/'+name+'/etc/php.ini';
					break;
			}
		}
		return fileName
	},
	set_lib_config:function(name,title){		
		var loadT = bt.load(lan.soft.menu_temp);
		bt.send('getConfigHtml','plugin/getConfigHtml',{name:name},function(rhtml){
			loadT.close();
			if(rhtml.status === false){
				if(name == "phpguard"){
					layer.msg(lan.soft.menu_phpsafe,{icon:1})
				}
				else{
					layer.msg(rhtml.msg,{icon:2});
				}
				return;
			}
			bt.open({
				type: 1,
				shift: 5,
				offset: '20%',
				closeBtn: 2,
				area: '700px', 
				title: ''+ title,
                content: rhtml.replace('"javascript/text"', '"text/javascript"'),
                success:function(){
                	if(rhtml.indexOf('CodeMirror') != -1){
                		loadLink(['/static/codemirror/lib/codemirror.css']);
                		loadScript(['/static/codemirror/lib/codemirror.js','/static/codemirror/addon/edit/editAll.js','/static/codemirror/mode/modeAll.js','/static/codemirror/addon/dialog/dialog.js','/static/codemirror/addon/search/search.js','/static/codemirror/addon/scroll/annotatescrollbar.js']);
                	}
                }
            });
            /*rtmp = rhtml.split('<script type="javascript/text">')
            if (rtmp.length < 2) {
                rtmp = rhtml.split('<script type="text/javascript">')
            }
            rcode = rtmp[1].replace('</script>','');
			setTimeout(function(){
				if(!!(window.attachEvent && !window.opera)){ 
                    execScript(rcode); 
				}else{
                    window.eval(rcode);
				}
			},200)*/
		});
	},
	save_config:function(fileName,data){
		var encoding = 'utf-8';
		var loadT = bt.load(lan.soft.the_save);
		bt.send('SaveFileBody','files/SaveFileBody',{data:data,path:fileName,encoding:encoding},function(rdata){
			loadT.close();
			bt.msg(rdata);
		})
	}
	
}


bt.database = {
	get_list : function(page,search,callback)
	{
		if(page == undefined) page = 1
		search = search == undefined ? '':search;
		var order = bt.get_cookie('order') ? '&order=' + bt.get_cookie('order'):'';
		
		var data = 'tojs=database.get_list&table=databases&limit=15&p='+page+'&search='+search + order; 
		bt.pub.get_data(data,function(rdata){
			if(callback) callback(rdata);
		})
	},
	get_root_pass:function(callback){
		bt.send('getKey','data/getKey',{table:'config',key:'mysql_root',id:1},function(rdata){
			if(callback) callback(rdata);
		})
	},
	set_root : function(){
		bt.database.get_root_pass(function(rdata){
			var bs = bt.render_form(bt.data.database.root);
			$('.password'+bs).val(rdata);
		})		
	},
	set_data_pass:function(callback){
		var bs = bt.render_form(bt.data.database.data_pass,function(rdata){
			if(callback) callback(rdata);
		});
		return bs;
	},
	set_data_access:function(name){
		var loading = bt.load();
		bt.send('GetDatabaseAccess','database/GetDatabaseAccess',{name:name},function(rdata){
			loading.close();
			var bs = bt.render_form(bt.data.database.data_access);
			$('.name'+bs).val(name);
			setTimeout(function(){
				if(rdata.msg=='127.0.0.1' || rdata.msg =='%'){
					$('.dataAccess'+bs).val(rdata.msg)
				}
				else{
					$('.dataAccess'+bs).val('ip').trigger('change');
					$('#dataAccess_subid').val(rdata.msg);	
				}			
			},100)
		})		
	},
    add_database: function (callback) {
        bt.data.database.data_add.list[2].items[0].value = bt.get_random(16);
		bt.render_form(bt.data.database.data_add,function(rdata){		
			if(callback) callback(rdata);
		});				
	},
	del_database:function(data,callback){
		var loadT = bt.load(lan.get('del_all_task_the',[data.name]));
		bt.send('DeleteDatabase','database/DeleteDatabase',data,function(rdata){
			loadT.close();	
			bt.msg(rdata);
			if(callback) callback(rdata);
		})	
	},
	sync_database:function(callback){
		var loadT = bt.load(lan.database.sync_the);
		bt.send('SyncGetDatabases','database/SyncGetDatabases',{},function(rdata){	
			loadT.close();			
			if(callback) callback(rdata);
			bt.msg(rdata);
		});
	},
	sync_to_database:function(data,callback){
		var loadT = bt.load(lan.database.sync_the);
		bt.send('SyncToDatabases','database/SyncToDatabases',data,function(rdata){
			loadT.close();
			if(callback) callback(rdata);
			bt.msg(rdata);
		})
	},
	open_phpmyadmin:function(name,username,password){
		if($("#toPHPMyAdmin").attr('action').indexOf('phpmyadmin') == -1){
		layer.msg(lan.database.phpmyadmin_err,{icon:2,shade: [0.3, '#000']})
		setTimeout(function(){ window.location.href = '/soft'; },3000);
			return;
		}
		$("#toPHPMyAdmin").attr('action',$("#toPHPMyAdmin").attr('public-data'))
		var murl = $("#toPHPMyAdmin").attr('action');
		$("#pma_username").val(username);
		$("#pma_password").val(password);
		$("#db").val(name);
		layer.msg(lan.database.phpmyadmin,{icon:16,shade: [0.3, '#000'],time:1000});
		setTimeout(function(){
			$("#toPHPMyAdmin").submit();
			layer.closeAll();
		},200);
	},
	submit_phpmyadmin: function(name,username,password,pub){
		if(pub === true){
			$("#toPHPMyAdmin").attr('action',$("#toPHPMyAdmin").attr('public-data'))
		}else{
			$("#toPHPMyAdmin").attr('action','/phpmyadmin/index.php')
		}
		var murl = $("#toPHPMyAdmin").attr('action');
		$("#pma_username").val(username);
		$("#pma_password").val(password);
		$("#db").val(name);
		layer.msg(lan.database.phpmyadmin,{icon:16,shade: [0.3, '#000'],time:1000});
		setTimeout(function(){
			$("#toPHPMyAdmin").submit();
			layer.closeAll();
		},200);
	},

	input_sql:function(fileName,dataName){
		bt.show_confirm(lan.database.input_title,'<span style="color:red;font-size:13px;">【'+dataName +'】'+lan.database.input_confirm+'</span>',function(index){
			var loading = bt.load(lan.database.input_the);
			bt.send('InputSql','database/InputSql',{file:fileName,name:dataName},function(rdata){
				loading.close();
				bt.msg(rdata);
			})
		});
	},
	backup_data:function(id,dataname,callback){
		var loadT = bt.load(lan.database.backup_the);
		bt.send('ToBackup','database/ToBackup',{id:id},function(rdata){
			loadT.close();			
			bt.msg(rdata);
			if(callback) callback(rdata);
		});

	},
	del_backup:function(id,dataid,dataname){
		bt.confirm({msg:lan.database.backup_del_confirm,title:lan.database.backup_del_title},function(index){
			var loadT = bt.load();
			bt.send('DelBackup','database/DelBackup',{id:id},function(frdata){
				loadT.close();
				if(frdata.status){
					if(database) database.database_detail(dataid,dataname);
				}
				bt.msg(frdata);
			});
		});
	}
}

bt.send('get_config','config/get_config',{},function(rdata){
	bt.config = rdata;
});

bt.plugin = {
	get_plugin_byhtml:function(name,callback){
		bt.send('getConfigHtml','plugin/getConfigHtml',{name:name},function(rdata){
			if(callback) callback(rdata);
		});		
	},
	get_firewall_state:function(callback){		
		var typename = getCookie('serverType');
		var name = 'btwaf_httpd';
		if(typename == "nginx") name='btwaf'		
        bt.send('a', 'plugin/a', { name: name, s:'get_total_all'},function(rdata){
			if(callback) callback(rdata);
		})
	}
}

bt.site = {
	get_list : function(page,search,type,callback){
		if(page == undefined) page = 1
		type = type == undefined ? '&type=-1' : ('&type='+ type);
		search = search == undefined ? '':search;
		var order = bt.get_cookie('order') ? '&order=' + bt.get_cookie('order'):'';		
		var data = 'tojs=site.get_list&table=sites&limit=15&p='+page+'&search='+search + order + type;
		bt.pub.get_data(data,function(rdata){
			if(callback) callback(rdata);
		})
	},
	get_domains:function(id,callback){
		var data = 'table=domain&list=True&search='+id;
		bt.pub.get_data(data,function(rdata){
			if(callback) callback(rdata);
		},1)
	},
	get_type:function(callback){
		bt.send('get_site_types','site/get_site_types','',function(rdata){
			if(callback) callback(rdata);
		});
	},
	add_type:function(name,callback){
		bt.send('add_site_type','site/add_site_type',{name:name},function(rdata){
			if(callback) callback(rdata);
		});
	},
	edit_type:function(data,callback){
        bt.send('modify_site_type_name','site/modify_site_type_name',{id:data.id,name:data.name},function(rdata){
			if(callback) callback(rdata);
		});
	},
	del_type:function(id,callback){
        bt.send('remove_site_type','site/remove_site_type',{id:id},function(rdata){
			if(callback) callback(rdata);
		});
	},
	set_site_type:function(data,callback){
        bt.send('set_site_type','site/set_site_type',{id:data.id,site_ids:data.site_array},function(rdata){
			if(callback) callback(rdata);
		});
	},
	get_site_domains:function(id,callback){
		var loading =  bt.load();
		bt.send('GetSiteDomains','site/GetSiteDomains',{id:id},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	add_domains:function(id,webname,domains,callback){
		var loading = bt.load();
		bt.send('AddDomain','site/AddDomain',{domain:domains,webname:webname,id:id},function(rdata){
			loading.close();
			if(callback) callback(rdata);
			bt.msg(rdata);
		})
	},
	del_domain:function(siteId,siteName,domain,port,callback){
		var loading = bt.load();
		bt.send('DelDomain','site/DelDomain',{id:siteId,webname:siteName,domain:domain,port:port},function(rdata){
			loading.close();
			if(callback) callback(rdata);
			bt.msg(rdata);
		})
	},
	get_dirbind:function(id,callback){
		var loading =  bt.load();
		bt.send('GetDirBinding','site/GetDirBinding',{id:id},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	add_dirbind:function(id,domain,dirName,callback){
		var loading =  bt.load();
		bt.send('AddDirBinding','site/AddDirBinding',{id:id,domain:domain,dirName:dirName},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	del_dirbind:function(id,callback){
		var loading = bt.load();
		bt.send('DelDirBinding','site/DelDirBinding',{id:id},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	get_dir_rewrite:function(data,callback){
		var loading = bt.load();
		bt.send('GetDirRewrite','site/GetDirRewrite',data,function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	get_site_path:function(id,callback){
		bt.send('getKey','data/getKey',{table:'sites',key:'path',id:id},function(rdata){
			if(callback) callback(rdata);
		})
	},
	get_dir_userini:function(id,path,callback){
		bt.send('GetDirUserINI','site/GetDirUserINI',{id:id,path:path},function(rdata){
			if(callback) callback(rdata);
		})		
	},
	set_dir_userini:function(path,callback){
		var loading = bt.load();
		bt.send('SetDirUserINI','site/SetDirUserINI',{path:path},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	set_logs_status:function(id,callback){
		var loading = bt.load();
		bt.send('logsOpen','site/logsOpen',{id:id},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	set_site_runpath:function(id,path,callback){
		var loading = bt.load();
		bt.send('SetSiteRunPath','site/SetSiteRunPath',{id:id,runPath:path},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	set_site_path:function(id,path,callback){
		var loading = bt.load();
		bt.send('SetPath','site/SetPath',{id:id,path:path},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
    set_site_pwd: function (id, username, password, callback){
		var loading = bt.load();
		bt.send('SetHasPwd','site/SetHasPwd',{id:id,username:username,password:password},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
    },
    close_site_pwd: function (id, callback) {
        var loading = bt.load();
        bt.send('SetHasPwd', 'site/CloseHasPwd', { id: id}, function (rdata) {
            loading.close();
            if (callback) callback(rdata);
        })
    },
	get_limitnet:function(id,callback){
		bt.send('GetLimitNet','site/GetLimitNet',{id:id},function(rdata){
			if(callback) callback(rdata);
		})	
	},
	set_limitnet:function(id,perserver,perip,limit_rate,callback){
		var loading = bt.load();
		bt.send('SetLimitNet','site/SetLimitNet',{id:id,perserver:perserver,perip:perip,limit_rate:limit_rate},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	close_limitnet:function(id,callback){
		var loading = bt.load();
		bt.send('CloseLimitNet','site/CloseLimitNet',{id:id},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	get_rewrite_list:function(siteName,callback){
		bt.send('GetRewriteList','site/GetRewriteList',{siteName:siteName},function(rdata){
			if(callback) callback(rdata);
		})		
	}, 
	set_rewrite_tel:function(name,data,callback){
		var loading = bt.load(lan.site.saving_txt);
		bt.send('SetRewriteTel','site/SetRewriteTel',{name:name,data:data},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})	
	},
	get_index:function(id,callback){
		bt.send('GetIndex','site/GetIndex',{id:id},function(rdata){
			if(callback) callback(rdata);
		})
	},
	set_index:function(id,index,callback){
		var loading = bt.load();
		bt.send('SetIndex','site/SetIndex',{id:id,Index:index},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	get_site_config:function(siteName,callback){
		if(bt.os=='Linux'){
			var sPath = '/www/server/panel/vhost/'+bt.get_cookie('serverType')+'/'+siteName+'.conf';
			bt.files.get_file_body(sPath,function(rdata){
				if(callback) callback(rdata);
			})
		}
	},
	set_site_config:function(siteName,data,encoding,callback){
		var loading = bt.load(lan.site.saving_txt);
		if(bt.os=='Linux'){
			var sPath = '/www/server/panel/vhost/'+bt.get_cookie('serverType')+'/'+siteName+'.conf';
			bt.files.set_file_body(sPath,data,'utf-8',function(rdata){
				loading.close();
				if(callback) callback(rdata);
			})
		}
	},
	set_phpversion:function(siteName,version,callback){
		var loading = bt.load();
		bt.send('SetPHPVersion','site/SetPHPVersion',{siteName:siteName,version:version},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	// 重定向列表
	get_redirect_list:function(name,callback){
		var loadT = bt.load(lan.site.the_msg);
		bt.send('GetRedirectList','site/GetRedirectList',{sitename:name },function(rdata){
			loadT.close();
			if(callback) callback(rdata);
		});
	},
	// 重定向列表
	get_redirect_list:function(name,callback){
		var loadT = layer.load();
		bt.send('GetRedirectList','site/GetRedirectList',{sitename:name },function(rdata){
			layer.close(loadT);
			if(callback) callback(rdata);
		});
	},
	create_redirect:function(obj,callback){
		var loadT = bt.load(lan.site.the_msg);
		bt.send('CreateRedirect','site/CreateRedirect',obj,function(rdata){
			loadT.close();
			if(callback) callback(rdata);
		});
	},
	modify_redirect:function(obj,callback){
		var loadT = bt.load(lan.site.the_msg);
		bt.send('ModifyRedirect','site/ModifyRedirect',obj,function(rdata){
			loadT.close();
			if(callback) callback(rdata);
		});
	},
	remove_redirect:function(sitename,redirectname,callback){
		bt.show_confirm('删除重定向['+ redirectname +']','您真的要删除该重定向吗?',function(){
			var loadT = bt.load(lan.site.the_msg);
			bt.send('DeleteRedirect','site/DeleteRedirect',{sitename:sitename,redirectname:redirectname},function(rdata){
				loadT.close();
				if(callback) callback(rdata);
			});
		});
	},
	get_redirect_config:function(obj,callback){
		var loadT = bt.load(lan.site.the_msg);
		bt.send('GetRedirectFile','site/GetRedirectFile',obj,function(rdata){
			loadT.close();
			if(callback) callback(rdata);
		});
	},
	save_redirect_config:function(obj,callback){
		var loadT = bt.load(lan.site.the_msg);
		bt.send('SaveProxyFile','site/SaveRedirectFile',obj,function(rdata){
			loadT.close();
			if(callback) callback(rdata);
		});
	},
	get_site_proxy:function(siteName ,callback){
		bt.send('GetProxy','site/GetProxy',{name :siteName },function(rdata){
			if(callback) callback(rdata);
		})
	},
	set_site_proxy:function(siteName,type,proxyUrl,toDomain,sub1,sub2,callback){
		var loading = bt.load();
		bt.send('SetProxy','site/SetProxy',{name:siteName,type:type,proxyUrl:proxyUrl,toDomain:toDomain,sub1:sub1,sub2:sub2},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	set_open_proxy_cache:function(siteName,callback){
		var loading = bt.load();
		bt.send('ProxyCache','site/ProxyCache',{siteName:siteName},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	get_proxy_list:function(name,callback){
		var loadT = bt.load(lan.site.the_msg);
		bt.send('GetProxyList','site/GetProxyList',{sitename:name },function(rdata){
			loadT.close();
			if(callback) callback(rdata);
		})
	},
	create_proxy:function(obj,callback){
		var loadT = bt.load(lan.site.the_msg);
		bt.send('CreateProxy','site/CreateProxy',obj,function(rdata){
			loadT.close();
			if(callback) callback(rdata);
		});
	},
	remove_proxy:function(sitename,proxyname,callback){
		bt.show_confirm('删除反向代理['+ proxyname +']','您真的要从列表中删除吗?',function(){
			var loadT = bt.load(lan.site.the_msg);
			bt.send('RemoveProxy','site/RemoveProxy',{sitename:sitename,proxyname:proxyname},function(rdata){
				loadT.close();			
				if(callback) callback(rdata);	
				bt.msg(rdata);
			})	
		})
	},
	modify_proxy:function(obj,callback){
		var loadT = bt.load(lan.site.the_msg);
		bt.send('ModifyProxy','	site/ModifyProxy',obj,function(rdata){
			loadT.close();
			if(callback) callback(rdata);
		});
	},
	get_proxy_config:function(obj,callback){
		var loadT = bt.load(lan.site.the_msg);
		bt.send('GetProxyFile','site/GetProxyFile',obj,function(rdata){
			loadT.close();
			if(callback) callback(rdata);
		});
	},
	save_proxy_config:function(obj,callback){
		var loadT = bt.load(lan.site.the_msg);
		bt.send('SaveProxyFile','site/SaveProxyFile',obj,function(rdata){
			loadT.close();
			if(callback) callback(rdata);
		});
	},
	get_site_security:function(id,name,callback){
		bt.send('GetSecurity','site/GetSecurity',{id:id,name:name },function(rdata){
			if(callback) callback(rdata);
		})
	},
	set_site_security:function(id,name,fix,domains,status,return_rule,callback){
		var loading = bt.load(lan.site.the_msg);
		bt.send('SetSecurity','site/SetSecurity',{id:id,name:name,fix:fix,domains:domains,status:status,return_rule:return_rule},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	get_site_301:function(siteName,callback){
		bt.send('Get301Status','site/Get301Status',{siteName:siteName},function(rdata){
			if(callback) callback(rdata);
		})
	},
	set_site_301:function(siteName,srcDomain,toUrl,type,callback){
		var loading = bt.load();
		bt.send('Set301Status','site/Set301Status',{siteName:siteName,toDomain:toUrl,srcDomain:srcDomain,type:type},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	set_tomcat:function(siteName,callback){
		var loading = bt.load(lan.public.config);
		bt.send('SetTomcat','site/SetTomcat',{siteName:siteName},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	get_site_logs:function(siteName,callback){
		var loading = bt.load();
		bt.send('GetSiteLogs','site/GetSiteLogs',{siteName:siteName},function(rdata){
			loading.close();
			if(rdata.status !== true) rdata.msg = '';
			if (rdata.msg == '') rdata.msg = '当前没有日志.';
			if(callback) callback(rdata);
		})
	},
	get_site_ssl:function(siteName,callback){
		var loadT = bt.load(lan.site.the_msg);
        bt.send('GetSSL', 'site/GetSSL', { siteName: siteName }, function (rdata) {
            loadT.close();
            if (callback) callback(rdata);
        });
	},
	create_let:function(data,callback){
        var loadT = layer.open({
            title: false,
            type:1,
            closeBtn:0,
            shade: 0.3,
            area: "500px",
            offset: "30%",
            content: "<pre style='margin-bottom: 0px;height:250px;text-align: left;background-color: #000;color: #fff;white-space: pre-wrap;' id='create_lst'>正在准备申请证书...</pre>",
            success:function(layers,index){
            	bt.site.get_let_logs();
            	bt.send('CreateLet', 'site/CreateLet', data, function (rdata) {
		            layer.close(loadT);
		            if (callback) callback(rdata);
		        });
            }
        });
    },
    get_let_logs: function () {
    	bt.send('get_lines','ajax/get_lines',{ 
    		num: 10, 
    		filename: "/www/server/panel/logs/letsencrypt.log" 
    	},function(rdata){
            if ($("#create_lst").text() === "") return;
            if (rdata.status === true) {
                $("#create_lst").text(rdata.msg);
                $("#create_lst").scrollTop($("#create_lst")[0].scrollHeight);
            }
            setTimeout(function () { bt.site.get_let_logs(); }, 1000);
    	});
    },
	get_dns_api:function(callback){		
		var loadT = bt.load();
		bt.send('GetDnsApi','site/GetDnsApi',{},function(rdata){
			loadT.close();			
			if(callback) callback(rdata);		
		})	
	},
	set_dns_api:function(data,callback){
		var loadT = bt.load();
		bt.send('SetDnsApi','site/SetDnsApi',data,function(rdata){
			loadT.close();			
			if(callback) callback(rdata);		
		})	
	},
	verify_domain:function(partnerOrderId,siteName,callback){
		var loadT = bt.load(lan.site.ssl_apply_2);
		bt.send('Completed','ssl/Completed',{partnerOrderId:partnerOrderId,siteName:siteName},function(rdata){
			loadT.close();			
			if(callback) callback(rdata);		
		})
	},
	get_dv_ssl:function(domain,path,callback){
		var loadT = bt.load(lan.site.ssl_apply_1);
		bt.send('GetDVSSL','ssl/GetDVSSL',{domain:domain,path:path},function(rdata){
			loadT.close();			
			if(callback) callback(rdata);		
		})
	},
	get_ssl_info:function(partnerOrderId,siteName,callback){
		var loadT = bt.load(lan.site.ssl_apply_3);
		bt.send('GetSSLInfo','ssl/GetSSLInfo',{partnerOrderId:partnerOrderId,siteName:siteName},function(rdata){
			loadT.close();			
			if(callback) callback(rdata);		
		})	
	},
	set_cert_ssl:function(certName,siteName,callback){
		var loadT = bt.load('正在部署证书...');
		bt.send('SetCertToSite','ssl/SetCertToSite',{certName:certName,siteName:siteName},function(rdata){
            loadT.close();
            site.reload();
			if(callback) callback(rdata);	
			bt.msg(rdata);
		})	
	},
	remove_cert_ssl:function(certName,callback){
		bt.show_confirm('删除证书','您真的要从证书夹删除证书吗?',function(){
			var loadT = bt.load(lan.site.the_msg);
			bt.send('RemoveCert','ssl/RemoveCert',{certName:certName},function(rdata){
				loadT.close();			
				if(callback) callback(rdata);	
				bt.msg(rdata);
			})	
		})
	},
	set_http_to_https:function(siteName,callback){	
		var loading = bt.load();
		bt.send('HttpToHttps','site/HttpToHttps',{siteName:siteName},function(rdata){	
			loading.close();
			if(callback) callback(rdata);	
			bt.msg(rdata);
		})	
	},
	close_http_to_https:function(siteName,callback){
		var loading = bt.load();
		bt.send('CloseToHttps','site/CloseToHttps',{siteName:siteName},function(rdata){	
			loading.close();
			if(callback) callback(rdata);	
			bt.msg(rdata);
		})	
	},
	set_ssl:function(siteName,data,callback){
		if(data.path){
			//iis导入证书
		}
		else{
			var loadT = bt.load(lan.site.saving_txt);
			bt.send('SetSSL','site/SetSSL',{type:1,siteName:siteName,key:data.key,csr:data.csr},function(rdata){
				loadT.close();			
				if(callback) callback(rdata);		
			})
		}			
	},
	set_ssl_status:function(action,siteName,callback){
		var loadT = bt.load(lan.site.get_ssl_list);
		bt.send(action,'site/'+action,{updateOf:1,siteName:siteName},function(rdata){
			loadT.close();			
			if(callback) callback(rdata);		
		})
	},
	get_cer_list:function(callback){
		var loadT = bt.load(lan.site.the_msg);
		bt.send('GetCertList','ssl/GetCertList',{},function(rdata){
			loadT.close();			
			if(callback) callback(rdata);		
		})	
	},
	get_order_list:function(siteName,callback){
		bt.send('GetOrderList','ssl/GetOrderList',{siteName:siteName},function(rdata){
			if(callback) callback(rdata);
		})
	},
	del_site:function(data,callback){	
		var loadT = bt.load(lan.get('del_all_task_the',[data.webname]));
		bt.send('DeleteSite','site/DeleteSite',data,function(rdata){
			loadT.close();			
			if(callback) callback(rdata);		
		})		
	},
	add_site:function(callback)
    {
		var _form = $.extend(true, {}, bt.data.site.add);
        bt.site.get_all_phpversion(function (rdata) {
            bt.site.get_type(function (tdata) {                 
			    for(var i=0;i<_form.list.length;i++){
                    if (_form.list[i].name == 'version') {
                        var items = [];
                        for (var j = rdata.length - 1; j >= 0; j--) {
                            var o = rdata[j];
                            o.value = o.version;
                            o.title = o.name;
                            items.push(o);
                        }
                        _form.list[i].items = items;
                    }
                    else if (_form.list[i].name == 'type_id') {
                        for (var x = 0; x < tdata.length; x++)  _form.list[i].items.push({ value: tdata[x].id, title: tdata[x].name });                                              
                    }
			    }
			    var bs = bt.render_form(_form,function(rdata){	
					console.log(rdata);
				    if(callback) callback(rdata);
			    });			
			    $(".placeholder").click(function(){
				    $(this).hide();
				    $('.webname'+bs).focus();
                })
                $('.path' + bs).val($("#defaultPath").text());
			    $('.webname'+bs).focus(function() {
			        $(".placeholder").hide();
			    });			
			    $('.webname'+bs).blur(function() {
				    if($(this).val().length==0){
					    $(".placeholder").show();
				    }  
                });
            })
		})			
	},	
	get_all_phpversion:function(callback){
		bt.send('GetPHPVersion','site/GetPHPVersion',{},function(rdata){
			if(callback) callback(rdata);
		})
	},
	get_site_phpversion:function(siteName,callback){
		bt.send('GetSitePHPVersion','site/GetSitePHPVersion',{siteName:siteName},function(rdata){
			if(callback) callback(rdata);
		})
	},
	stop:function(id,name,callback){
		bt.confirm({title:'停用站点 【'+ name +'】',msg:lan.site.site_stop_txt},function(index){
			if (index > 0) {
				var loadT = bt.load();
				bt.send('SiteStop','site/SiteStop',{id:id,name:name},function(ret){
					loadT.close();
					if(site && typeof callback == "undefined"){
						site.get_list();
					}else{
						if(callback) callback(ret);
					}
					bt.msg(ret);
				});
			}
		});
	},
	start:function(id,name,callback){
		bt.confirm({title:'启动站点 【'+ name +'】',msg:lan.site.site_start_txt},function(index){
			if (index > 0) {
				var loadT = bt.load();
				bt.send('SiteStart','site/SiteStart',{id:id,name:name},function(ret){
					loadT.close();
					if(site && typeof callback == "undefined"){
						site.get_list();
					}else{
						if(callback) callback(ret);
					}
					bt.msg(ret);
				});
			}
		});
	},
	backup_data:function(id,callback){
		var loadT = bt.load(lan.database.backup_the);
		bt.send('ToBackup','site/ToBackup',{id:id},function(rdata){
			loadT.close();			
			bt.msg(rdata);
			if(callback) callback(rdata);
		});
	},
	del_backup:function(id,siteId,siteName){
		bt.confirm({msg:lan.site.webback_del_confirm,title:lan.site.del_bak_file},function(index){
			var loadT = bt.load();
			bt.send('DelBackup','site/DelBackup',{id:id},function(frdata){
				loadT.close();
				if(frdata.status){
					if(site) site.site_detail(siteId,siteName);
				}
				bt.msg(frdata);
			});
		});
	},
	set_endtime:function(id,dates,callback){
		var loadT = bt.load(lan.site.saving_txt); 
	 	bt.send('SetEdate','site/SetEdate',{id:id,edate:dates},function(rdata){
		  loadT.close();
		  if(callback) callback(rdata);        
        });
	},
	get_default_path:function(type,callback){
		var vhref='';
		if(bt.os=='Linux'){			
			switch(type){
				case 0:
					vhref = '/www/server/panel/data/defaultDoc.html';
					break;
				case 1:
					vhref = '/www/server/panel/data/404.html';
					break;
				case 2:
					var serverType = bt.get_cookie('serverType');
					vhref = '/www/server/apache/htdocs/index.html';					
					if(serverType=='nginx') vhref = '/www/server/nginx/html/index.html';					
					break;
				case 3:
					vhref = '/www/server/stop/index.html';
					break;
			}			
		}
		if(callback) callback(vhref);
	},
	get_default_site:function(callback){
		var loading = bt.load();
		bt.send('GetDefaultSite','site/GetDefaultSite',{},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	set_default_site:function(name,callback){
		var loading = bt.load();
		bt.send('SetDefaultSite','site/SetDefaultSite',{name:name},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	get_dir_auth:function(id,callback){
		var loading = bt.load();
		bt.send('get_dir_auth','site/get_dir_auth',{id:id},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	create_dir_guard:function(data,callback){
		var loading = bt.load();
		bt.send('set_dir_auth','site/set_dir_auth',{id:data.id,name:data.name,site_dir:data.site_dir,username:data.username,password:data.password},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	edit_dir_account:function(data,callback){
		var loading = bt.load();
		bt.send('modify_dir_auth_pass','site/modify_dir_auth_pass',{id:data.id,name:data.name,username:data.username,password:data.password},function(rdata){
			loading.close();
			if(callback) callback(rdata);
		})
	},
	delete_dir_guard:function(id,data,callback){
		bt.show_confirm('删除['+ data +']',"你确定要删除目录保护吗",function(){
			var loading = bt.load();
			bt.send('delete_dir_auth','site/delete_dir_auth',{id:id,name:data},function(rdata){
				loading.close();
				if(callback) callback(rdata);
			})
		})
	},
	delete_php_guard:function(website,data,callback){
		bt.show_confirm('删除PHP防护',"你确定要删除PHP防护["+ data +"]吗？",function(){
			var loading = bt.load();
			bt.send('del_file_deny','config/del_file_deny',{website:website,deny_name:data},function(rdata){
				loading.close();
				if(callback) callback(rdata);
			})
		})
	}
}



bt.form ={
	btn:{
		close:function(title,callback){
			var obj = {title:'关闭',name:'btn-danger'};
			if(title) obj.title = title;
			if(callback) obj['callback'] = callback;
			return obj;
		},
		submit:function(title,callback){
			var obj = {title:'提交',name:'submit',css:'btn-success'};
			if(title) obj.title = title;
			if(callback) obj['callback'] = callback;
			return obj;
		}
	},
	item:{
		data_access:{ title:'访问权限',items:[
					{name:'dataAccess',type:'select',width:'100px',items:[
					{title:'本地服务器',value:'127.0.0.1'},
					{title:'所有人(不安全)',value:'%'},
					{title:'指定IP',value:'ip'}
				],callback:function(obj){
					var subid = obj.attr('name')+'_subid';
					$('#'+subid).remove();
					if(obj.val()=='ip'){
						obj.parent().append('<input id="'+subid+'" class="bt-input-text mr5" type="text" name="address" placeholder="多个IP使用逗号(,)分隔" style="width: 203px; display: inline-block;">');
					}
				}
			}
		]},
		password:{title:'密码',name:'password',items:[
			{type:'text',width:'311px',value:bt.get_random(16),event: {css:'glyphicon-repeat',callback:function(obj){bt.refresh_pwd(16,obj);}}}
		]},
	}
}

bt.data = {
	database:{
		root:{
			title : lan.database.edit_pass_title,
			area:'530px',
			list:[{title:'root密码',name:'password',items:[
					{type:'text',width:'311px',event: {css:'glyphicon-repeat',callback:function(obj){bt.refresh_pwd(16,obj);}}}
				]},
			],
			btns:[
				bt.form.btn.close(),	
				bt.form.btn.submit('提交',function(rdata,load){
					var loading = bt.load();
					bt.send('SetupPassword','database/SetupPassword',rdata,function(rRet){
						loading.close();
						bt.msg(rRet);
						load.close();
					})
				})
			]
		},
		data_add:{
			title:lan.database.add_title,
			area:'530px',
			list:[
				{title:'数据库名',items:[
					{name:'name',placeholder:'新的数据库名称',type:'text',width:'65%',callback:function(obj){				
						$('input[name="db_user"]').val(obj.val());
					}},
					{name:'codeing',type:'select',width:'27%',items:[
						{title:'utf-8',value:'utf8'},
						{title:'utf8mb4',value:'utf8mb4'},
						{title:'gbk',value:'gbk'},
						{title:'big5',value:'big5'},
					]}
				]},
				{title:'用户名',name:'db_user',placeholder:'数据库用户',width:'65%'},
				bt.form.item.password,
				{title:'类型',name:'dtype',type:'select',disabled:(bt.contains(bt.get_cookie('serverType'),'nginx') || bt.contains(bt.get_cookie('serverType'),'apache') ?true:false),items:[
					{title:'MySQL',value:'MySQL'},
					{title:'SQLServer',value:'SQLServer'}
				]},
				bt.form.item.data_access
			],
			btns:[
				bt.form.btn.close(),
				bt.form.btn.submit('提交',function(rdata,load,callback){		
					if(!rdata.address) rdata.address = rdata.dataAccess;
					if(!rdata.ps) rdata.ps = rdata.name;
					var loading = bt.load();
					bt.send('AddDatabase','database/AddDatabase',rdata,function(rRet){
						loading.close();						
						if(rRet.status) load.close();	
						if(callback) callback(rRet);
						bt.msg(rRet);
					})
				})
			]
		},
		data_access:{
			title:'设置数据库权限',
			area:'480px',
			list:[
				{title:'name',name:'name',hide:true},
				bt.form.item.data_access
			],
			btns:[
				bt.form.btn.close(),
				{title:'提交',name:'submit',css:'btn-success',callback:function(rdata,load){
					var loading = bt.load();
					rdata.access = rdata.dataAccess;
					if(rdata.access == 'ip') rdata.access = rdata.address;
					bt.send('SetDatabaseAccess','database/SetDatabaseAccess',rdata,function(rRet){
						loading.close();
						bt.msg(rRet);
						if(rRet.status) load.close();			
					})
				}}
			]
		},
		data_pass : {
			title:'修改数据库密码',
			area:'530px',
			list:[
				{title:'id',name:'id',hide:true},
				{title:'用户名',name:'name',disabled:true},
				{title:'密码',name:'password',items:[
					{type:'text',event: {css:'glyphicon-repeat',callback:function(obj){bt.refresh_pwd(16,obj);}}}
				]},
			],
			btns:[
				{title:'关闭',name:'close'},
				{title:'提交',name:'submit',css:'btn-success',callback:function(rdata,load,callback){
					var loading = bt.load();
					bt.send('ResDatabasePassword','database/ResDatabasePassword',rdata,function(rRet){
						loading.close();
						bt.msg(rRet);
						if(rRet.status) load.close();	
						if(callback) callback(rRet);
					})
				}}
			]
		}
	},
	site:{
		add:{
			title:lan.site.site_add,
			area: '640px',
			list:[
				{title:'域名',name:'webname',items:[
					{type:'textarea',width:'458px',callback:function(obj){
						var array = obj.val().split("\n");
						var ress =array[0].split(":")[0];
						var res = bt.strim(ress.replace(new RegExp(/([-.])/g), '_'));
						var ftp_user = res;
						var data_user = res;
						if(!isNaN(res.substr(0,1))){
							ftp_user='ftp_'+ftp_user;
                            data_user = 'sql_' + data_user;
                        }
                        if (data_user.length > 16) data_user = data_user.substr(0, 16)
						obj.data('ftp',ftp_user);
						obj.data('database',data_user);	
				
						$('.ftp_username').val(ftp_user);
						$('.datauser').val(data_user);
						
						var _form = obj.parents('div.bt-form');
						var _path_obj = _form.find('input[name="path"]');
                        var path = _path_obj.val();
                        var defaultPath = $('#defaultPath').text();
                        var dPath = bt.rtrim(defaultPath,'/');
						if(path.substr(0,dPath.length)==dPath) _path_obj.val(dPath+'/'+ress);	
						_form.find('input[name="ps"]').val(ress);
					},placeholder:'每行填写一个域名，默认为80端口<br>泛解析添加方法 *.domain.com<br>如另加端口格式为 www.domain.com:88'}
				]},
				{title:'备注',name:'ps',placeholder:'网站备注'},
				{title:'根目录',name:'path',items:[
					{type:'text',width:'330px',event: {css:'glyphicon-folder-open',callback:function(obj){bt.select_path(obj);}}}
				]},
				{title:'FTP',items:[
					{name:'ftp',type:'select',items:[
						{value:'false',title:'不创建'},
						{value:'true',title:'创建'}						
					],callback:function(obj){
						var subid = obj.attr('name')+'_subid';
						$('#'+subid).remove();
						if(obj.val()=='true'){
							var _bs = obj.parents('div.bt-form').attr('data-id');
							var ftp_user = $('textarea[name="webname"]').data('ftp');							
							var item = {title:'FTP设置',items:[
								{name:'ftp_username',title:'用户名',width:'173px',value:ftp_user},
								{name:'ftp_password',title:'密码',width:'173px',value:bt.get_random(16)}
							],ps:'创建站点的同时，为站点创建一个对应FTP帐户，并且FTP目录指向站点所在目录。'}
							var _tr = bt.render_form_line(item)
				
							obj.parents('div.line').append('<div class="line" id='+subid+'>'+_tr.html+'</div>');
						}
					}}
				]},
				{title:'数据库',items:[
					{name:'sql',type:'select',items:[
						{value:'false',title:'不创建'},
						{value:'MySQL',title:'MySQL'},
						{value:'SQLServer',title:'SQLServer'}		
					],callback:function(obj){
						var subid = obj.attr('name')+'_subid';
						$('#'+subid).remove();
						if(obj.val()!='false')
						{
							if(bt.os=='Linux' && obj.val()=='SQLServer'){
								obj.val('false');
								bt.msg({msg:'Linux暂不支持SQLServer!',icon:2});
								return;
							}
							var _bs = obj.parents('div.bt-form').attr('data-id');
							var data_user =$('textarea[name="webname"]').data('database');
							var item = {title:'数据库设置',items:[
								{name:'datauser',title:'用户名',width:'173px',value:data_user},
								{name:'datapassword',title:'密码',width:'173px',value:bt.get_random(16)}
							],ps:'创建站点的同时，为站点创建一个对应的数据库帐户，方便不同站点使用不同数据库。'}
							var _tr = bt.render_form_line(item)
							obj.parents('div.line').append('<div class="line" id='+subid+'>'+_tr.html+'</div>');
						}
					}},
					{name:'codeing',type:'select',items:[
						{value:'utf8',title:'utf-8'},
						{value:'utf8mb4',title:'utf8mb4'},
						{value:'gbk',title:'gbk'},
						{value:'big5',title:'big5'}
					]}
				]},
				{title:'程序类型',type:'select',name:'type',disabled:(bt.contains( bt.get_cookie('serverType'),'IIS')?false:true),items:[
					{value:'PHP',title:'PHP'},
					{value:'Asp',title:'Asp'},
					{value:'Aspx',title:'Aspx'},					
				],callback:function(obj){
					if(obj.val()=='Asp' || obj.val()=='Aspx'){
						obj.parents('div.line').next().hide();
					}else{
						obj.parents('div.line').next().show();
					}
				}},
				{title:'PHP版本',name:'version',type:'select',items:[
					{value:'00',title:'纯静态'}
                ]
                }, {
                    title: '网站分类', name: 'type_id', type: 'select', items: [
                        
                    ]
                }
			],
			btns:[
				{title:'关闭',name:'close'},
				{title:'提交',name:'submit',css:'btn-success',callback:function(rdata,load,callback){
					var loading = bt.load();
					if(!rdata.webname){
						bt.msg({msg:'主域名格式不正确',icon:2});
						return;
					}
					var webname =  bt.replace_all(rdata.webname,'http:\\/\\/','');
					webname =  bt.replace_all(webname,'https:\\/\\/','');
					var arrs = webname.split('\n');		
					var list = [];
					var domain_name,port;					
					for (var i=0;i<arrs.length;i++) {
						if(arrs[i]){							
							var temp = arrs[i].split(':');	
							var item = {};
							item['name'] = temp[0]
							item['port'] = temp.length>1?temp[1]:80;					
							if(!bt.check_domain(item.name)){
								bt.msg({msg:lan.site.domain_err_txt,icon:2})
								return;
							}
							if(i>0) {
								list.push(arrs[i]);
							}else{
								domain_name = item.name;
								port = item.port;
							}
						}
					}	
					var domain = {};
					domain['domain'] = domain_name;
					domain['domainlist'] = list;
					domain['count'] = list.length;
					rdata.webname = JSON.stringify(domain);
                    rdata.port = port;
					bt.send('AddSite','site/AddSite',rdata,function(rRet){
						loading.close();																	
						if(rRet.siteStatus) load.close();	
						if(callback) callback(rRet);
					})
				}}
			]
        }       
	},
	ftp:{
		add:{
			title: lan.ftp.add_title,
			area:'530px',
			list:[
                { title: '用户名', name: 'ftp_username', callback: function (obj) {
                    var defaultPath = $('#defaultPath').text();
                    var wootPath = bt.rtrim(defaultPath,'/');
					if(bt.contains($('input[name="path"]').val(),wootPath)){						
						$('input[name="path"]').val(wootPath+'/'+obj.val())
					}
				}},
				{title:'密码',name:'ftp_password',items:[
					{type:'text',width:'330px',value:bt.get_random(16),event: {css:'glyphicon-repeat',callback:function(obj){bt.refresh_pwd(16,obj);}}}
				]},
				{title:'根目录',name:'path',items:[
					{type:'text',event: {css:'glyphicon-folder-open',callback:function(obj){bt.select_path(obj);}}}
				]}
			],
			btns:[
				{title:'关闭',name:'close'},
				{title:'提交',name:'submit',css:'btn-success',callback:function(rdata,load,callback){
					var loading = bt.load();
					if(!rdata.ps) rdata.ps = rdata.ftp_username; 
					bt.send('AddUser','ftp/AddUser',rdata,function(rRet){
						loading.close();						
						if(rRet.status) load.close();	
						if(callback) callback(rRet);
						bt.msg(rRet);
					})
				}}
			]
		},
		set_port:{
			title:lan.ftp.port_title,
			skin:'',
			area:'500px',
			list:[
				{title:'默认端口',name:'port',width:'250px'}
			],
			btns:[
				{title:'关闭',name:'close'},
				{title:'提交',name:'submit',css:'btn-success',callback:function(rdata,load,callback){
					var loading = bt.load();
					bt.send('setPort','ftp/setPort',rdata,function(rRet){
						loading.close();						
						if(rRet.status) load.close();	
						if(callback) callback(rRet);
						bt.msg(rRet);
					})
				}}
			]
		},
		set_password:{
			title:lan.ftp.pass_title,
			area:'530px',
			list:[
				{title:'id',name:'id',hide:true},
				{title:'用户名',name:'ftp_username',disabled:true},
				{title:'密码',name:'new_password',items:[
					{type:'text',event: {css:'glyphicon-repeat',callback:function(obj){bt.refresh_pwd(16,obj);}}}
				]},
			],
			btns:[
				{title:'关闭',name:'close'},
				{title:'提交',name:'submit',css:'btn-success',callback:function(rdata,load,callback){
					bt.confirm({msg:lan.ftp.pass_confirm,title: lan.ftp.stop_title},function(){
							var loading = bt.load();
							bt.send('SetUserPassword','ftp/SetUserPassword',rdata,function(rRet){
								loading.close();						
								if(rRet.status) load.close();	
								if(callback) callback(rRet);
								bt.msg(rRet);
							})				
						})
					}
				}
			]
		}
	}
}
var form_group = {
	select_all:function(_arry){
		for(var j=0;j<_arry.length;j++){
			this.select(_arry[j]);
		}
	},
    select:function(elem){
        $(elem).after('<div class="bt_select_group"><div class="bt_select_active"><span class="select_val default">请选择</span><span class="glyphicon glyphicon-triangle-bottom" aria-hidden="true"></span> </div><ul class="bt_select_ul"></ul></div>');
		var _html = '',select_el = $(elem),select_group= select_el.next(),select_ul = select_group.find('.bt_select_ul'),select_val = select_group.find('.select_val'),select_icon = select_group.find('.glyphicon');
		select_el.find('option').each(function(index,el){
			var active = select_el.val() === $(el).val(),_val = $(el).val(),_name = $(el).text();
			_html += '<li data-val="'+ _val +'" class="'+ (active?'active':'') +'">'+ _name +'</li>';
			if(active){
				select_val.text(_name);
				_val !== ''?select_val.removeClass('default'):select_val.addClass('default');
			}
		});
		select_el.hide();
		select_ul.html(_html);
		$(elem).next('.bt_select_group').find('.select_val').unbind('click').click(function(e){
			if($('.bt_select_group .bt_select_ul.active').length >=1){
				$('.bt_select_group').removeAttr('style');
				$('.bt_select_group').find('.bt_select_ul').removeClass('active fadeInUp animated');
				$('.bt_select_group').find('.glyphicon').css({'transform':'rotate(0deg)'});
			}
			is_show_select_ul(select_ul.hasClass('active'));
			$(document).click(function(){
				is_show_select_ul(true);
				$(this).unbind('click');
			});
			e.stopPropagation();
			e.preventDefault();
		});
		$(elem).next('.bt_select_group').find('.bt_select_ul li').unbind('click').click(function(){
			var _val = $(this).attr('data-val'),_name = $(this).text();
			$(this).addClass('active').siblings().removeClass('active');
			_val !== ''?select_val.removeClass('default'):select_val.addClass('default');
			select_val.text(_name);
			select_el.val(_val);
			$(elem).find('option[value="'+ _val +'"]').change();
			is_show_select_ul(true);
		});
		function is_show_select_ul(active){
			if(active){
				select_group.removeAttr('style');
				select_icon.css({'transform':'rotate(0deg)'});
				select_ul.removeClass('active fadeInUp animated');
			}else{
				select_group.css('borderColor','#20a53a');
				select_icon.css({'transform':'rotate(180deg)'});
				select_ul.addClass('active fadeInUp animated');
			}
		}
	},
	checkbox:function(){
		$('input[type="checkbox"]').each(function(index,el){
			$(el).hide();
			$(el).after('<div class="bt_checkbox_group '+ ($(this).prop("checked")?'active':'default') +'"></div>');
		});
		$('.bt_checkbox_group').click(function(){
			$(this).prev().click();
			if($(this).hasClass('active')){
				$(this).removeClass('active');
				$(this).prev().removeAttr('checked');
			}else{
				$(this).addClass('active');
				$(this).prev().attr('checked','checked');
			}
		});
	}
}
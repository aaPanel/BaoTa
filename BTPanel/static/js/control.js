//默认显示7天周期图表
setTimeout(function(){
	Wday(0,'getload');
},500);
setTimeout(function(){
	Wday(0,'cpu');
},500);
setTimeout(function(){
	Wday(0,'mem');
},1000);
setTimeout(function(){
	Wday(0,'disk');
},1500);
setTimeout(function(){
	Wday(0,'network');
},2000);
$(".st").hover(function(){
	$(this).next().show();
},function(){
	$(this).next().hide();
	$(this).next().hover(function(){
		$(this).show();
	},function(){
		$(this).hide();
	})
})

$(".searcTime .gt").click(function(){
	$(this).addClass("on").siblings().removeClass("on");
});


$('.time_range_submit').click(function(){
    $(this).parents(".searcTime").find("span").removeClass("on");
	$(this).parents(".searcTime").find(".st").addClass("on");
	var b = (new Date($(this).parent().find(".btime").val()).getTime())/1000;
	var e = (new Date($(this).parent().find(".etime").val()).getTime())/1000;
	b = Math.round(b);
	e = Math.round(e);
	eval($(this).attr('data-type')+'('+ b +','+ e +')');
});
//指定天数
function Wday(day,name){
	var now = (new Date().getTime())/1000;
	if(day==0){
		var b = (new Date(GetToday() + " 00:00:01").getTime())/1000;
			b = Math.round(b);
		var e = Math.round(now);
	}
	if(day==1){
		var b = (new Date(getBeforeDate(day) + " 00:00:01").getTime())/1000;
		var e = (new Date(getBeforeDate(day) + " 23:59:59").getTime())/1000;
		b = Math.round(b);
		e = Math.round(e);
	}
	else{
		var b = (new Date(getBeforeDate(day) + " 00:00:01").getTime())/1000;
			b = Math.round(b);
		var e = Math.round(now);
	}
	switch (name){
		case "cpu":
			cpu(b,e);
			break;
		case "mem":
			mem(b,e);
			break;
		case "disk":
			disk(b,e);
			break;
		case "network":
			network(b,e);
			break;
		case "getload":
			getload(b,e);
			break;
	}
}

function GetToday(){
   var mydate = new Date();
   var str = "" + mydate.getFullYear() + "/";
   str += (mydate.getMonth()+1) + "/";
   str += mydate.getDate();
   return str;
}



//取监控状态
function GetStatus(){
	loadT = layer.msg(lan.public.read,{icon:16,time:0})
	$.post('/config?action=SetControl','type=-1',function(rdata){
		layer.close(loadT);
		if(rdata.status){
			$("#openJK").html("<input class='btswitch btswitch-ios' id='ctswitch' type='checkbox' checked><label class='btswitch-btn' for='ctswitch' onclick='SetControl()'></label>")
		}
		else{
			$("#openJK").html("<input class='btswitch btswitch-ios' id='ctswitch' type='checkbox'><label class='btswitch-btn' for='ctswitch' onclick='SetControl()'></label>")
		}
		$("#saveDay").val(rdata.day)
	})
}

GetStatus()

//设置监控状态
function SetControl(act){
	var day = $("#saveDay").val()
	if(day < 1){
		layer.msg(lan.control.save_day_err,{icon:2});
		return;
	}
	if(act){
		var type = $("#ctswitch").prop('checked')?'1':'0';
	}else{
		var type = $("#ctswitch").prop('checked')?'0':'1';
	}
	
	loadT = layer.msg(lan.public.the,{icon:16,time:0})
	$.post('/config?action=SetControl','type='+type+'&day='+day,function(rdata){
		layer.close(loadT);
		layer.msg(rdata.msg,{icon:rdata.status?1:2});
	});
}

//清理记录
function CloseControl(){
	layer.confirm(lan.control.close_log_msg,{title:lan.control.close_log,icon:3,closeBtn:2}, function() {
		loadT = layer.msg(lan.public.the,{icon:16,time:0})
		$.post('/config?action=SetControl','type=del',function(rdata){
			layer.close(loadT);
			$.get('/system?action=ReWeb',function(){});
			layer.msg(rdata.msg,{icon:rdata.status?1:2});
		});
	});
}



//字节单位转换MB
function ToSizeG(bytes){
	var c = 1024 * 1024;
	var b = 0;
	if(bytes > 0){
		var b = (bytes/c).toFixed(2);
	}
	return b;
}

//定义周期时间
function getBeforeDate(n){
    var n = n;
    var d = new Date();
    var year = d.getFullYear();
    var mon=d.getMonth()+1;
    var day=d.getDate();
    if(day <= n){
		if(mon>1) {
		   mon=mon-1;
		}
		else {
		 year = year-1;
		 mon = 12;
		}
	}
	d.setDate(d.getDate()-n);
	year = d.getFullYear();
	mon=d.getMonth()+1;
	day=d.getDate();
    s = year+"/"+(mon<10?('0'+mon):mon)+"/"+(day<10?('0'+day):day);
    return s;
}

//cpu
function cpu(b,e){
$.get('/ajax?action=GetCpuIo&start='+b+'&end='+e,function(rdata){
	var myChartCpu = echarts.init(document.getElementById('cpuview'));
	var xData = [];
	var yData = [];
	//var zData = [];
	
	for(var i = 0; i < rdata.length; i++){
		xData.push(rdata[i].addtime);
		yData.push(rdata[i].pro);
		//zData.push(rdata[i].mem);
	}
	option = {
		tooltip: {
			trigger: 'axis',
			axisPointer: {
				type: 'cross'
			},
			formatter: '{b}<br />{a}: {c}%'
		},
		xAxis: {
			type: 'category',
			boundaryGap: false,
			data: xData,
			axisLine:{
				lineStyle:{
					color:"#666"
				}
			}
		},
		yAxis: {
			type: 'value',
			name: lan.public.pre,
			boundaryGap: [0, '100%'],
			min:0,
			max: 100,
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
			end: 100,
			zoomLock:true
		}, {
			start: 0,
			end: 100,
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
		series: [
			{
				name:'CPU',
				type:'line',
				smooth:true,
				symbol: 'none',
				sampling: 'average',
				itemStyle: {
					normal: {
						color: 'rgb(0, 153, 238)'
					}
				},
				data: yData
			}
		]
	};
	myChartCpu.setOption(option);
    window.addEventListener("resize",function(){
		myChartCpu.resize();
	});
})
}

//内存
function mem(b,e){
$.get('/ajax?action=GetCpuIo&start='+b+'&end='+e,function(rdata){
	var myChartMen = echarts.init(document.getElementById('memview'));
	var xData = [];
	//var yData = [];
	var zData = [];
	
	for(var i = 0; i < rdata.length; i++){
		xData.push(rdata[i].addtime);
		//yData.push(rdata[i].pro);
		zData.push(rdata[i].mem);
	}
	option = {
		tooltip: {
			trigger: 'axis',
			axisPointer: {
				type: 'cross'
			},
			formatter:function(config){
			    return config[0].axisValueLabel +'</br>' + config[0].seriesName+':'+config[0].value.toFixed(2) +'%'
			}
		},
		xAxis: {
			type: 'category',
			boundaryGap: false,
			data: xData,
			axisLine:{
				lineStyle:{
					color:"#666"
				}
			}
		},
		yAxis: {
			type: 'value',
			name: lan.public.pre,
			boundaryGap: [0, '100%'],
			min:0,
			max: 100,
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
			end: 100,
			zoomLock:true
		}, {
			start: 0,
			end: 100,
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
		series: [
			{
				name:lan.index.process_mem,
				type:'line',
				smooth:true,
				symbol: 'none',
				sampling: 'average',
				itemStyle: {
					normal: {
						color: 'rgb(0, 153, 238)'
					}
				},
				data: zData
			}
		]
	};
	myChartMen.setOption(option);
	window.addEventListener("resize",function(){
		myChartMen.resize();
	});
})
}

//磁盘io
function disk(b, e) {
    $.get('/ajax?action=GetDiskIo&start=' + b + '&end=' + e, function (rdata) {
        var diskview = document.getElementById('diskview'),myChartDisk = echarts.init(diskview),rData = [],wData = [],xData = [],unit_size = 1,_unit = getCookie('disk-unitType');
        $(diskview).next().removeClass('hide').addClass('show');
		switch (_unit) {
			case 'MB/s':
				unit_size = 1024;
				break;
			case 'GB/s':
				unit_size = 1024*1024;
				break;
			default:
				unit_size = 1;
				break;
		}

        for (var i = 0; i < rdata.length; i++) {
            rData.push((rdata[i].read_bytes / 1024 / 60).toFixed(3)/unit_size);
            wData.push((rdata[i].write_bytes / 1024 / 60).toFixed(3)/unit_size);
            xData.push(rdata[i].addtime);
            //yData.push(rdata[i].read_count);
            //zData.push(rdata[i].write_count);
        }
        option = {
            tooltip: {
                trigger: 'axis',
                axisPointer: {
                    type: 'cross'
                },
                formatter:function(config){
                	var _config = config,_tips = '';
                	for(var i=0;i<config.length;i++){
                		_tips +=  '<span style="display: inline-block;width: 10px;height: 10px;margin-rigth:10px;border-radius: 50%;background: '+ config[i].color +';"></span>  '+ config[i].seriesName +'：'+ config[i].data.toFixed(2) + _unit + ( config.length-1 !== i?'<br />':'')
                	}
                	return "时间："+ _config[0].axisValue +"<br />" + _tips;
                },
            },
            legend: {
                top:'18px',
                data: [lan.control.disk_read_bytes, lan.control.disk_write_bytes]
            },
            xAxis: {
                type: 'category',
                boundaryGap: false,
                data: xData,
                axisLine: {
                    lineStyle: {
                        color: "#666"
                    }
                }
            },
            yAxis: {
                type: 'value',
                //name: lan.index.unit + ':KB/s',
                boundaryGap: [0, '100%'],
                splitLine: {
                    lineStyle: {
                        color: "#ddd"
                    }
                },
                axisLine: {
                    lineStyle: {
                        color: "#666"
                    }
                }
            },
            dataZoom: [{
                type: 'inside',
                start: 0,
                end: 100,
                zoomLock: true
            }, {
                start: 0,
                end: 100,
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
            series: [
                {
                    name: lan.control.disk_read_bytes,
                    type: 'line',
                    smooth: true,
                    symbol: 'none',
                    sampling: 'average',
                    itemStyle: {
                        normal: {
                            color: 'rgb(255, 70, 131)'
                        }
                    },
                    data: rData
                },
                {
                    name: lan.control.disk_write_bytes,
                    type: 'line',
                    smooth: true,
                    symbol: 'none',
                    sampling: 'average',
                    itemStyle: {
                        normal: {
                            color: 'rgba(46, 165, 186, .7)'
                        }
                    },
                    data: wData
                }
            ]
        };
        myChartDisk.setOption(option);
        window.addEventListener("resize", function () {
            myChartDisk.resize();
        });
    })
}

//网络Io
function network(b,e){
$.get('/ajax?action=GetNetWorkIo&start='+b+'&end='+e,function(rdata){
    var anetwork = document.getElementById('network'),myChartNetwork = echarts.init(anetwork),aData = [],bData = [],cData = [],dData = [],xData = [],yData = [],zData = [],unit_size = 1,_unit = getCookie('network-unitType'),network_io = [{title:'全部',value:'all'}],network_select = $('[name="network-io"]'),network_html = '<option value="">全部</option>',is_network = 0,network_io_key = bt.get_cookie('network_io_key') || '';
	$(anetwork).next().removeClass('hide').addClass('show');
	switch (_unit) {
		case 'MB/s':
			unit_size = 1024;
			break;
		case 'GB/s':
			unit_size = 1024*1024;
			break;
		default:
			unit_size = 1;
			break;
	}
    network_select.unbind('change').change(function(){
	    bt.set_cookie('network_io_key',$(this).val());
	    network(b,e);
	}).removeClass('hide').addClass('show');
	
	for(var i = 0; i < rdata.length; i++){
	    var items = rdata[i];
	    if(is_network < 1 && typeof items.down_packets === 'object'){
           	for(var key in items.down_packets){
	            network_html += '<option value="'+ key +'" '+ (network_io_key === key?'selected':'') +'>'+ key +'</option>';
	        }
	        network_select.html(network_html);
	        is_network ++;
        }
	    if(typeof network_io_key != 'undefined' && network_io_key != ''){
	        if(typeof items.down_packets === 'object'){
	            zData.push(items.down_packets[network_io_key]/unit_size);
	        }else{
	            zData.push(0);
	        }
	    }else{
	        zData.push(items.down/unit_size);
	    }
	    if(typeof network_io_key != 'undefined' && network_io_key != ''){
	        if(typeof items.up_packets === 'object'){
	            yData.push(items.up_packets[network_io_key]/unit_size);
	        }else{
	            yData.push(0);
	        }
	    }else{
	        yData.push(items.up/unit_size);
	    }
		xData.push(items.addtime);
	}
	option = {
		tooltip: {
			trigger: 'axis',
			axisPointer: {
				type: 'cross'
			},
			formatter:function(config){
            	var _config = config,_tips = '';
            	for(var i=0;i<config.length;i++){
            		_tips +=  '<span style="display: inline-block;width: 10px;height: 10px;margin-rigth:10px;border-radius: 50%;background: '+ config[i].color +';"></span>  '+ config[i].seriesName +'：'+ config[i].data.toFixed(2) + _unit + ( config.length-1 !== i?'<br />':'')
            	}
            	return "时间："+ _config[0].axisValue +"<br />" + _tips;
            }
		},
		legend: {
		    top:'18px',
			data:[lan.index.net_up,lan.index.net_down]
		},
		xAxis: {
			type: 'category',
			boundaryGap: false,
			data: xData,
			axisLine:{
				lineStyle:{
					color:"#666"
				}
			}
		},
		yAxis: {
			type: 'value',
			//name: lan.index.unit+':KB/s',
			boundaryGap: [0, '100%'],
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
			end: 100,
			zoomLock:true
		}, {
			start: 0,
			end: 100,
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
		series: [
			{
				name:lan.index.net_up,
				type:'line',
				smooth:true,
				symbol: 'none',
				sampling: 'average',
				itemStyle: {
					normal: {
						color: 'rgb(255, 140, 0)'
					}
				},
				data: yData
			},
			{
				name:lan.index.net_down,
				type:'line',
				smooth:true,
				symbol: 'none',
				sampling: 'average',
				itemStyle: {
					normal: {
						color: 'rgb(30, 144, 255)'
					}
				},
				data: zData
			}
		]
	};
	myChartNetwork.setOption(option);
	window.addEventListener("resize",function(){
		myChartNetwork.resize();
	});
})
}
//负载
function getload_old(b,e){
$.get('/ajax?action=get_load_average&start='+b+'&end='+e,function(rdata){
	var myChartgetload = echarts.init(document.getElementById('getloadview'));
	var aData = [];
	var bData = [];
	var xData = [];
	var yData = [];
	var zData = [];
	
	for(var i = 0; i < rdata.length; i++){
		xData.push(rdata[i].addtime);
		yData.push(rdata[i].pro);
		zData.push(rdata[i].one);
		aData.push(rdata[i].five);
		bData.push(rdata[i].fifteen);
	}
	option = {
		tooltip: {
			trigger: 'axis'
		},
		calculable: true,
		legend: {
			data:['系统资源使用率','1分钟','5分钟','15分钟'],
			selectedMode: 'single',
		},
		xAxis: {
			type: 'category',
			boundaryGap: false,
			data: xData,
			axisLine:{
				lineStyle:{
					color:"#666"
				}
			}
		},
		yAxis: {
			type: 'value',
			name: '',
			boundaryGap: [0, '100%'],
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
			end: 100,
			zoomLock:true
		}, {
			start: 0,
			end: 100,
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
		series: [
			{
				name:'系统资源使用率',
				type:'line',
				smooth:true,
				symbol: 'none',
				sampling: 'average',
				itemStyle: {
					normal: {
						color: 'rgb(255, 140, 0)'
					}
				},
				data: yData
			},
			{
				name:'1分钟',
				type:'line',
				smooth:true,
				symbol: 'none',
				sampling: 'average',
				itemStyle: {
					normal: {
						color: 'rgb(30, 144, 255)'
					}
				},
				data: zData
			},
			{
				name:'5分钟',
				type:'line',
				smooth:true,
				symbol: 'none',
				sampling: 'average',
				itemStyle: {
					normal: {
						color: 'rgb(0, 178, 45)'
					}
				},
				data: aData
			},
			{
				name:'15分钟',
				type:'line',
				smooth:true,
				symbol: 'none',
				sampling: 'average',
				itemStyle: {
					normal: {
						color: 'rgb(147, 38, 255)'
					}
				},
				data: bData
			}
		]
	};
	myChartgetload.setOption(option);
	window.addEventListener("resize",function(){
		myChartgetload.resize();
	});
})
}
//系统负载
function getload(b,e){
	$.get('/ajax?action=get_load_average&start='+b+'&end='+e,function(rdata){
	var myChartgetload = echarts.init(document.getElementById('getloadview'));
	var aData = [];
	var bData = [];
	var xData = [];
	var yData = [];
	var zData = [];
	
	for(var i = 0; i < rdata.length; i++){
		xData.push(rdata[i].addtime);
		yData.push(rdata[i].pro);
		zData.push(rdata[i].one);
		aData.push(rdata[i].five);
		bData.push(rdata[i].fifteen);
	}
	option = {
		animation: false,
		tooltip: {
			trigger: 'axis',
			axisPointer: {
                type: 'cross'
			},
			formatter:function(config){
				var _line = config[0].axisValueLabel,
				line_color = '';
				for (var i = 0; i < config.length; i++) {
					switch (config[i].seriesName) {
						case '1分钟':
							line_color = 'rgb(30, 144, 255)';
							break;
						case '5分钟':
							line_color = 'rgb(0, 178, 45)';
							break;
						case '15分钟':
							line_color = 'rgb(147, 38, 255)';
							break;
						default:
							line_color = 'rgb(255, 140, 0)';
							break;
					}
					var color_line = '</br><span style="width: 8px;display: inline-block;height: 8px;background: '+line_color+';border-radius: 100px;margin-right: 7px;"></span>',
					text_line = config[i].seriesName+': '+config[i].value.toFixed(2) +'%';
					if (config[i].seriesName == '资源使用率') {
						if (i == 0) {
							_line += color_line+text_line+'</br></br>'+config[0].axisValueLabel;
						} else {
							_line += '</br></br>'+config[0].axisValueLabel+color_line+text_line+'</br>';
						}
					} else {
						_line += color_line+text_line;
					}
				}
			    return _line;
			}
		},
		legend: {
			data:['1分钟','5分钟','15分钟'],
			right:'16%',
			top:'10px'
		},
		axisPointer: {
			link: {xAxisIndex: 'all'},
			lineStyle: {
				color: '#aaaa',
				width: 1
			}
		},
		grid: [{ // 直角坐标系内绘图网格
				top: '60px',
				left: '5%',
				right: '55%',
				width: '40%',
				height: 'auto'
			},
			{
				top: '60px',
				left: '55%',
				width: '40%',
				height: 'auto'
			}
		],
		xAxis: [

			{ // 直角坐标系grid的x轴
				type: 'category',
				axisLine: {
					lineStyle: {
						color: '#666'
					}
				},
				data: xData
			},
			{ // 直角坐标系grid的x轴
				type: 'category',
				gridIndex: 1,
				axisLine: {
					lineStyle: {
						color: '#666'
					}
				},
				data: xData
			},
		],
		yAxis: [{
				scale: true,
				name: '资源使用率',
				boundaryGap: [0, '100%'],
				splitLine: { // y轴网格显示
					show: true,
					lineStyle:{
						color:"#ddd"
					}
				},
				nameTextStyle: { // 坐标轴名样式
					color: '#666',
					fontSize: 12,
					align: 'left'
				},
				axisLine:{
					lineStyle:{
						color: '#666',
					}
				}
			},
			{
				scale: true,
				name: '负载详情',
				gridIndex: 1,
				splitLine: { // y轴网格显示
					show: true,
					lineStyle:{
						color:"#ddd"
					}
				},
				nameTextStyle: { // 坐标轴名样式
					color: '#666',
					fontSize: 12,
					align: 'left'
				},
				axisLine:{
					lineStyle:{
						color: '#666',
					}
				}
			},
		],
		dataZoom: [{
			type: 'inside',
			start: 0,
			end: 100,
			xAxisIndex:[0,1],
			zoomLock:true
		}, {
			xAxisIndex: [0, 1],
            type: 'slider',
			start: 0,
			end: 100,
			handleIcon: 'M10.7,11.9v-1.3H9.3v1.3c-4.9,0.3-8.8,4.4-8.8,9.4c0,5,3.9,9.1,8.8,9.4v1.3h1.3v-1.3c4.9-0.3,8.8-4.4,8.8-9.4C19.5,16.3,15.6,12.2,10.7,11.9z M13.3,24.4H6.7V23h6.6V24.4z M13.3,19.6H6.7v-1.4h6.6V19.6z',
			handleSize: '80%',
			handleStyle: {
				color: '#fff',
				shadowBlur: 3,
				shadowColor: 'rgba(0, 0, 0, 0.6)',
				shadowOffsetX: 2,
				shadowOffsetY: 2
			},
			left:'5%',
			right:'5%'
		}],
		series: [
			{
				name: '资源使用率',
				type: 'line',
				lineStyle: {
					normal: {
						width: 2,
						color: 'rgb(255, 140, 0)'
					}
				},
				itemStyle: {
					normal: {
						color: 'rgb(255, 140, 0)'
					}
				},
				data: yData
			},
			{
				xAxisIndex: 1,
				yAxisIndex: 1,
				name: '1分钟',
				type: 'line',
				lineStyle: {
					normal: {
						width: 2,
						color: 'rgb(30, 144, 255)'
					}
				},
				itemStyle: {
					normal: {
						color: 'rgb(30, 144, 255)'
					}
				},
				data: zData
			},
			{
				xAxisIndex: 1,
				yAxisIndex: 1,
				name: '5分钟',
				type: 'line',
				lineStyle: {
					normal: {
						width: 2,
						color: 'rgb(0, 178, 45)'
					}
				},
				itemStyle: {
					normal: {
						color: 'rgb(0, 178, 45)'
					}
				},
				data: aData
			},
			{
				xAxisIndex: 1,
				yAxisIndex: 1,
				name: '15分钟',
				type: 'line',
				lineStyle: {
					normal: {
						width: 2,
						color: 'rgb(147, 38, 255)'
					}
				},
				itemStyle: {
					normal: {
						color: 'rgb(147, 38, 255)'
					}
				},
				data: bData
			}
		],
		textStyle: {
			color: '#666',
			fontSize: 12
		}
	}
	myChartgetload.setOption(option);
	window.addEventListener("resize",function(){
		myChartgetload.resize();
	})
	})
}

$('.btime').val(GetToday() + ' 00:00:00');
$('.etime').val(GetToday() + ' 23:59:59');
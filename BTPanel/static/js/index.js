
if (bind_user == 'True') new BindAccount().installBindUser();

$("select[name='network-io'],select[name='disk-io']").change(function () {
  var key = $(this).val(), type = $(this).attr('name')
  if (type == 'network-io') {
    if (key == 'all') key = '';
    bt.set_cookie('network_io_key', key);
  } else {
    bt.set_cookie('disk_io_key', key);
  }
});
$('.tabs-nav span').click(function () {
  var indexs = $(this).index();
  $(this).addClass('active').siblings().removeClass('active')
  $('.tabs-content .tabs-item:eq(' + indexs + ')').addClass('tabs-active').siblings().removeClass('tabs-active')
  $('.tabs-down select:eq(' + indexs + ')').removeClass('hide').siblings().addClass('hide')
  switch (indexs) {
    case 0:
      index.net.table.resize();
      break;
    case 1:
      index.iostat.table.resize();
      break;
  }
})



var interval_stop = false;
var index = {
  // 顾问服务弹窗
  consultancy_services: function (show) {
    var consultancy_cookies = bt.get_cookie('consultancy_cookies');
    if (consultancy_cookies) return false;
    if (show !== 0) return false;
    layer.open({
      type: 1,
      title: '免费顾问服务',
      closeBtn: false,
      area: ['600px', '470px'],
      btn: ['接受顾问服务', '放弃顾问服务'],
      content: '<div style="padding: 30px 35px;">\
                <div style="text-align: center;margin-bottom: 20px;font-size: 20px;height: 40px;line-height: 40px;">\
                <span style="vertical-align: middle;margin-left: 10px;font-size:21px;">感恩您使用宝塔，我们为您提供专属客服服务</span></div>\
                <div style="font-size: 14px;line-height: 27px;padding: 20px;border: 1px solid #ececec;border-radius: 5px;background: #fcfcfc;color: #555;text-indent:2em;">\
                    <div style="text-indent: 2em;margin-bottom: 10px;">我们提供给您<span style="font-weight: bold;">【免费的顾问服务】</span>，确保您在使用宝塔面板过程中遇到紧急或者棘手的问题能第一时间找到专人协助您处理，我们期待与您沟通。</div>\
                    <div style="text-indent: 2em;margin-bottom: 10px;">如果您点<span style="font-weight: bold;">【接受顾问服务】</span>，您无需再做什么，我们会有专人致电联系您并加您为好友，让您可以在有疑问的时候能第一时间联系到专员。</div>\
                    <div style="text-indent: 2em;margin-bottom: 10px;">同时您也可以<span style="font-weight: bold;">【放弃顾问服务】</span>，在遇到问题的时候可以在我们官网论坛发言，我们也有论坛值守人员协助您处理。</div></div>\
                </div>',
      yes: function (indexs, layero) {
        bt.send('set_user_adviser', 'auth/set_user_adviser ', { status: 1 }, function (res) {
          bt.set_cookie('consultancy_cookies', '1');
          layer.close(indexs);
          bt.msg(res)
        })
      },
      btn2: function (indexs, layero) {
        layer.confirm('是否放弃免费顾问服务，放弃后在遇到问题的时候可以在我们官网论坛发言，我们也有论坛值守人员协助您处理。', {
          title: '提示',
          area: '400px',
          btn: ['确认', '取消'],
          icon: 0,
          closeBtn: 2,
          yes: function () {
            bt.send('set_user_adviser', 'auth/set_user_adviser ', { status: 0 }, function (res) {
              bt.set_cookie('consultancy_cookies', '1');
              layer.close(indexs);
              bt.msg(res)
            })
          }
        })
        return false
      }
    })
  },
  warning_list: [],
  warning_num: 0,
  series_option: {},// 配置项
  chart_json: {}, // 所有图表echarts对象
  chart_view: {}, // 磁盘echarts对象
  disk_view: [], // 释放内存标记
  chart_result: null,
  release: false,
  load_config: [{
    title: '运行堵塞',
    val: 90,
    color: '#dd2f00'
  }, {
    title: '运行缓慢',
    val: 80,
    color: '#ff9900'
  }, {
    title: '运行正常',
    val: 70,
    color: '#20a53a'
  }, {
    title: '运行流畅',
    val: 30,
    color: '#20a53a'
  }],
  release: false,
  interval: {
    limit: 10,
    count: 0,
    task_id: 0,
    start: function () {
      var _this = this;
      _this.count = 0;
      _this.task_id = setInterval(function () {
        if (_this.count >= _this.limit) {
          _this.reload();
          return;
        }
        _this.count++;
        if (!interval_stop) index.reander_system_info();
      }, 3000)
    },
    reload: function () {
      var _this = this;
      if (_this) clearInterval(_this.task_id);
      _this.start();
    }
  },
  net: {
    table: null,
    data: {
      uData: [],
      dData: [],
      aData: []
    },
    init: function () {
      //流量图表
      index.net.table = echarts.init(document.getElementById('NetImg'));
      var obj = {};
      obj.dataZoom = [];
      obj.unit = lan.index.unit + ':KB/s';
      obj.tData = index.net.data.aData;
      obj.formatter = function (config) {
        var _config = config, _tips = '';
        for (var i = 0; i < config.length; i++) {
          if (typeof config[i].data == "undefined") return false
          _tips += '<span style="display: inline-block;width: 10px;height: 10px;margin-rigth:10px;border-radius: 50%;background: ' + config[i].color + ';"></span>  ' + config[i].seriesName + '：' + (parseFloat(config[i].data)).toFixed(2) + ' KB/s' + (config.length - 1 !== i ? '<br />' : '')
        }
        return "时间：" + _config[0].axisValue + "<br />" + _tips;
      }
      obj.list = [];
      obj.list.push({ name: lan.index.net_up, data: index.net.data.uData, circle: 'circle', itemStyle: { normal: { color: '#f7b851' } }, areaStyle: { normal: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(255, 140, 0,1)' }, { offset: 1, color: 'rgba(255, 140, 0,.4' }], false) } }, lineStyle: { normal: { width: 1, color: '#f7b851' } } });
      obj.list.push({ name: lan.index.net_down, data: index.net.data.dData, circle: 'circle', itemStyle: { normal: { color: '#52a9ff' } }, areaStyle: { normal: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(30, 144, 255,1)' }, { offset: 1, color: 'rgba(30, 144, 255,.4)' }], false) } }, lineStyle: { normal: { width: 1, color: '#52a9ff' } } });
      option = bt.control.format_option(obj)

      index.net.table.setOption(option);
      window.addEventListener("resize", function () {
        index.net.table.resize();
      });
    },
    add: function (up, down) {
      var _net = this;
      var limit = 8;
      var d = new Date()
      if (_net.data.uData.length >= limit) _net.data.uData.splice(0, 1);
      if (_net.data.dData.length >= limit) _net.data.dData.splice(0, 1);
      if (_net.data.aData.length >= limit) _net.data.aData.splice(0, 1);
      _net.data.uData.push(up);
      _net.data.dData.push(down);
      _net.data.aData.push(d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds());
    }
  },
  iostat: {
    table: null,
    data: {
      uData: [],
      dData: [],
      aData: [],
      tipsData: []
    },
    init: function () {
      //流量图表
      index.iostat.table = echarts.init(document.getElementById('IoStat'));
      var obj = {};
      obj.dataZoom = [];
      obj.unit = lan.index.unit + ':MB/s';
      obj.tData = index.iostat.data.aData;
      obj.formatter = function (config) {
        var _config = config, _tips = "时间：" + _config[0].axisValue + "<br />", options = {
          read_bytes: '读取字节数',
          read_count: '读取次数 ',
          read_merged_count: '合并读取次数',
          read_time: '读取延迟',
          write_bytes: '写入字节数',
          write_count: '写入次数',
          write_merged_count: '合并写入次数',
          write_time: '写入延迟',
        }, data = index.iostat.data.tipsData[config[0].dataIndex], list = ['read_count', 'write_count', 'read_merged_count', 'write_merged_count', 'read_time', 'write_time',]
        for (var i = 0; i < config.length; i++) {
          if (typeof config[i].data == "undefined") return false
          _tips += '<span style="display: inline-block;width: 10px;height: 10px;border-radius: 50%;background: ' + config[i].color + ';"></span>&nbsp;&nbsp;<span>' + config[i].seriesName + '：' + (parseFloat(config[i].data)).toFixed(2) + ' MB/s' + '</span><br />'
        }
        $.each(list, function (index, item) {
          _tips += '<span style="display: inline-block;width: 10px;height: 10px;"></span>&nbsp;&nbsp;<span style="' + (item.indexOf('time') > -1 ? ('color:' + ((data[item] > 100 && data[item] < 1000) ? '#ff9900' : (data[item] >= 1000 ? 'red' : '#20a53a'))) : '') + '">' + options[item] + '：' + data[item] + (item.indexOf('time') > -1 ? ' ms' : ' 次/秒') + '</span><br />'
        })
        return _tips;
      }
      obj.list = [];
      obj.list.push({ name: '读取字节数', data: index.iostat.data.uData, circle: 'circle', itemStyle: { normal: { color: '#FF4683' } }, areaStyle: { normal: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(255,70,131,1)' }, { offset: 1, color: 'rgba(255,70,131,.4' }], false) } }, lineStyle: { normal: { width: 1, color: '#FF4683' } } });
      obj.list.push({ name: '写入字节数', data: index.iostat.data.dData, circle: 'circle', itemStyle: { normal: { color: '#6CC0CF' } }, areaStyle: { normal: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [{ offset: 0, color: 'rgba(108,192,207,1)' }, { offset: 1, color: 'rgba(108,192,207,.4)' }], false) } }, lineStyle: { normal: { width: 1, color: '#6CC0CF' } } });
      option = bt.control.format_option(obj)
      index.iostat.table.setOption(option);
      window.addEventListener("resize", function () {
        index.iostat.table.resize();
      });
    },
    add: function (read, write, data) {
      var _disk = this;
      var limit = 8;
      var d = new Date()
      if (_disk.data.uData.length >= limit) _disk.data.uData.splice(0, 1);
      if (_disk.data.dData.length >= limit) _disk.data.dData.splice(0, 1);
      if (_disk.data.aData.length >= limit) _disk.data.aData.splice(0, 1);
      if (_disk.data.tipsData.length >= limit) _disk.data.tipsData.splice(0, 1);
      _disk.data.uData.push(read);
      _disk.data.dData.push(write);
      _disk.data.tipsData.push(data);
      _disk.data.aData.push(d.getHours() + ':' + d.getMinutes() + ':' + d.getSeconds());
    }
  },
  get_init: function () {
    var _this = this;
    _this.reander_system_info(function (rdata) {
      // 负载悬浮事件
      $('#loadChart').hover(function () {
        var arry = [
          ['最近1分钟平均负载', rdata.load.one],
          ['最近5分钟平均负载', rdata.load.five],
          ['最近15分钟平均负载', rdata.load.fifteen]
        ], tips = '';
        $.each(arry || [], function (index, item) {
          tips += item[0] + '：' + item[1] + '</br>';
        })
        $.each(rdata.cpu_times || {}, function (key, item) {
          tips += key + '：' + item + '</br>';
        })
        // '最近1分钟平均负载：' + rdata.load.one + '</br>最近5分钟平均负载：' + rdata.load.five + '</br>最近15分钟平均负载：' + rdata.load.fifteen + ''
        layer.tips(tips, this, { time: 0, tips: [1, '#999'] });
      }, function () {
        layer.closeAll('tips');
      })

      // cpu悬浮事件
      $('#cpuChart').hover(function () {
        var cpuText = '';
        for (var i = 1; i < rdata.cpu[2].length + 1; i++) {
          var cpuUse = parseFloat(rdata.cpu[2][i - 1] == 0 ? 0 : rdata.cpu[2][i - 1]).toFixed(1)
          if (i % 2 != 0) {
            cpuText += 'CPU-' + i + '：' + cpuUse + '%&nbsp;|&nbsp;'
          } else {
            cpuText += 'CPU-' + i + '：' + cpuUse + '%'
            cpuText += '\n'
          }
        }

        layer.tips(rdata.cpu[3] + "</br>" + rdata.cpu[5] + "个物理CPU，" + (rdata.cpu[4]) + "个物理核心，" + rdata.cpu[1] + "个逻辑核心</br>" + cpuText, this, { time: 0, tips: [1, '#999'] });
      }, function () {
        layer.closeAll('tips');
      })

      $('#memChart').hover(function () {
        $(this).append('<div class="mem_mask shine_green" title="点击清理内存"><div class="men_inside_mask"></div><div class="mem-re-con" style="display:block"></div></div>');
        $(this).find('.mem_mask .mem-re-con').animate({ top: '5px' }, 400);
        $(this).next().hide();
      }, function () {
        $(this).find('.mem_mask').remove()
        $(this).next().show();
      }).click(function () {
        var that = $(this);
        var data = _this.chart_result.mem;
        bt.show_confirm('真的要释放内存吗？', '<font style="color:red;">若您的站点处于有大量访问的状态，释放内存可能带来无法预测的后果，您确定现在就释放内存吗？</font>', function () {
          _this.release = true
          var option = JSON.parse(JSON.stringify(_this.series_option));
          // 释放中...
          var count = ''
          var setInter = setInterval(function () {
            if (count == '...') {
              count = '.'
            } else {
              count += '.'
            }
            option.series[0].detail.formatter = "释放中" + count
            option.series[0].detail.fontSize = 15
            option.series[0].data[0].value = 0
            _this.chart_view.mem.setOption(option, true)
            that.next().hide()
          }, 400)
          // 释放接口请求 
          bt.system.re_memory(function (res) {
            that.next().show()
            clearInterval(setInter)
            option.series[0].detail = $.extend(option.series[0].detail, {
              formatter: "已释放\n" + bt.format_size(data.memRealUsed - res.memRealUsed),
              lineHeight: 18,
              padding: [5, 0]
            })
            _this.chart_view.mem.setOption(option, true)
            setTimeout(function () {
              _this.release = false;
              _this.chart_result.mem = res;
              _this.chart_active('mem');
            }, 2000);
          })
        })
      })

      // 磁盘悬浮事件
      for (var i = 0; i < rdata.disk.length; i++) {
        var disk = rdata.disk[i], texts = "基础信息</br>"
        texts += "文件系统：" + disk.filesystem + "</br>"
        texts += "类型：" + disk.type + "</br>"
        texts += "挂载点：" + disk.path + "</br>"
        texts += "<strong>Inode信息:</strong></br>"
        texts += "总数：" + disk.inodes[0] + "</br>"
        texts += "已用：" + disk.inodes[1] + "</br>"
        texts += "可用：" + disk.inodes[2] + "</br>"
        texts += "Inode使用率：" + disk.inodes[3] + "</br>"
        texts += "<strong>容量信息</strong></br>"
        texts += "容量：" + disk.size[0] + "</br>"
        texts += "已用：" + disk.size[1] + "</br>"
        texts += "可用：" + disk.size[2] + "</br>"
        texts += "使用率：" + disk.size[3] + "</br>"
        $("#diskChart" + i).data('title', texts).hover(function () {
          layer.tips($(this).data('title'), this, { time: 0, tips: [1, '#999'] });
        }, function () {
          layer.closeAll('tips');
        })
      }
      _this.get_server_info(rdata);
      if (rdata.installed === false) bt.index.rec_install();
      if (rdata.user_info.status) {
        var rdata_data = rdata.user_info.data;
        bt.set_cookie('bt_user_info', JSON.stringify(rdata.user_info));
        $(".bind-user").html(rdata_data.username);
      }
      else {
        $(".bind-weixin a").attr("href", "javascript:;");
        $(".bind-weixin a").click(function () {
          bt.msg({ msg: '请先绑定宝塔账号!', icon: 2 });
        })
      }
    })
    setTimeout(function () { _this.get_index_list() }, 400)
    setTimeout(function () { _this.net.init() }, 500);
    setTimeout(function () { _this.iostat.init() }, 500);
    setTimeout(function () { _this.get_warning_list() }, 600);
    setTimeout(function () { _this.interval.start() }, 700);
    setTimeout(function () {
      bt.system.check_update(function (rdata) {
        index.consultancy_services(rdata.msg.adviser);
        if (rdata.status !== false) {
          $('#toUpdate a').html('更新<i style="display: inline-block; color: red; font-size: 40px;position: absolute;top: -35px; font-style: normal; right: -8px;">.</i>');
          $('#toUpdate a').css("position", "relative");

        }
        if (rdata.msg.is_beta === 1) {
          $('#btversion').prepend('<span style="margin-right:5px;">Beta</span>');
          $('#btversion').append('<a class="btlink" href="https://www.bt.cn/bbs/forum-39-1.html" target="_blank">  [找Bug奖宝塔币]</a>');
        }

      }, false)
    }, 700)
  },
  get_server_info: function (info) {
    // bt.system.get_total(function (info){
    var memFree = info.memTotal - info.memRealUsed;
    if (memFree < 64) {
      $("#messageError").show();
      $("#messageError").append('<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;">' + lan.index.mem_warning + '</span> </p>')
    }

    if (info.isuser > 0) {
      $("#messageError").show();
      $("#messageError").append('<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;"></span>' + lan.index.user_warning + '<span class="c7 mr5" title="此安全问题不可忽略，请尽快处理" style="cursor:no-drop"> [不可忽略]</span><a class="btlink" href="javascript:setUserName();"> [立即修改]</a></p>')
    }

    if (info.isport === true) {
      $("#messageError").show();
      $("#messageError").append('<p><span class="glyphicon glyphicon-alert" style="color: #ff4040; margin-right: 10px;"></span>当前面板使用的是默认端口[8888]，有安全隐患，请到面板设置中修改面板端口!<span class="c7 mr5" title="此安全问题不可忽略，请尽快处理" style="cursor:no-drop"> [不可忽略]</span><a class="btlink" href="/config"> [立即修改]</a></p>')
    }
    var _system = info.system;
    $("#info").html(_system);
    $("#running").html(info.time);
    if (_system.indexOf("Windows") != -1) {
      $(".ico-system").addClass("ico-windows");
    }
    else if (_system.indexOf("CentOS") != -1) {
      $(".ico-system").addClass("ico-centos");
    }
    else if (_system.indexOf("Ubuntu") != -1) {
      $(".ico-system").addClass("ico-ubuntu");
    }
    else if (_system.indexOf("Debian") != -1) {
      $(".ico-system").addClass("ico-debian");
    }
    else if (_system.indexOf("Fedora") != -1) {
      $(".ico-system").addClass("ico-fedora");
    }
    else {
      $(".ico-system").addClass("ico-linux");
    }
    // })
  },

  /**
   * @description 渲染系统信息
   * @param rdata 接口返回值
   * 
  */
  reander_system_info: function (callback) {
    var _this = this;
    bt.system.get_net(function (res) {
      _this.chart_result = res
      // 动态添加磁盘，并赋值disk_view
      if (_this.chart_view.disk == undefined) {
        for (var i = 0; i < res.disk.length; i++) {
          var diskHtml = "<li class='rank col-xs-6 col-sm-3 col-md-3 col-lg-2 mtb20 circle-box text-center'><div id='diskName" + i + "'></div><div class='chart-li' id='diskChart" + i + "'></div><div id='disk" + i + "'></div></li>";
          $("#systemInfoList").append(diskHtml);
          _this.disk_view.push(echarts.init(document.querySelector("#diskChart" + i)));
        }
      }

      // 负载
      var loadCount = Math.round((res.load.one / res.load.max) * 100) > 100 ? 100 : Math.round((res.load.one / res.load.max) * 100);
      loadCount = loadCount < 0 ? 0 : loadCount;
      var loadInfo = _this.chart_color_active(loadCount);

      // cpu
      var cpuCount = res.cpu[0];
      var cpuInfo = _this.chart_color_active(cpuCount);

      // 内存
      var memCount = Math.round((res.mem.memRealUsed / res.mem.memTotal) * 1000) / 10; // 返回 memRealUsed 占 memTotal 的百分比
      var memInfo = _this.chart_color_active(memCount);
      bt.set_cookie('memSize', res.mem.memTotal)

      // 磁盘
      var diskList = res.disk;
      var diskJson = [];
      for (var i = 0; i < diskList.length; i++) {
        var ratio = diskList[i].size[3];
        ratio = parseFloat(ratio.substring(0, ratio.lastIndexOf("%")));
        var diskInfo = _this.chart_color_active(ratio)

        diskJson.push(diskInfo)

      }

      // chart_json存储最新数据
      _this.chart_json['load'] = loadInfo;
      _this.chart_json['cpu'] = cpuInfo;
      _this.chart_json['mem'] = memInfo;
      _this.chart_json['disk'] = diskJson
      // 初始化 || 刷新
      if (_this.chart_view.disk == undefined) {
        _this.init_chart_view()
      } else {
        _this.set_chart_data()
      }
      $('.rank .titles').show()

      var net_key = bt.get_cookie('network_io_key');
      if (net_key) {
        res.up = res.network[net_key].up;
        res.down = res.network[net_key].down;
        res.downTotal = res.network[net_key].downTotal;
        res.upTotal = res.network[net_key].upTotal;
        res.downPackets = res.network[net_key].downPackets;
        res.upPackets = res.network[net_key].upPackets;
        res.downAll = res.network[net_key].downTotal;
        res.upAll = res.network[net_key].upTotal;
      }
      var net_option = '<option value="all">全部</option>';
      $.each(res.network, function (k, v) {
        var act = (k == net_key) ? 'selected' : '';
        net_option += '<option value="' + k + '" ' + act + '>' + k + '</option>';
      });

      $('select[name="network-io"]').html(net_option);


      //刷新流量
      $("#upSpeed").html(res.up.toFixed(2) + ' KB');
      $("#downSpeed").html(res.down.toFixed(2) + ' KB');
      $("#downAll").html(bt.format_size(res.downTotal));
      $("#upAll").html(bt.format_size(res.upTotal));
      index.net.add(res.up, res.down);


      var disk_key = bt.get_cookie('disk_io_key') || 'ALL', disk_io_data = res.iostat[disk_key || 'ALL'], mb = 1048576, ioTime = disk_io_data.write_time > disk_io_data.read_time ? disk_io_data.write_time : disk_io_data.read_time
      $('#readBytes').html(bt.format_size(disk_io_data.read_bytes))
      $('#writeBytes').html(bt.format_size(disk_io_data.write_bytes))
      $('#diskIops').html((disk_io_data.read_count + disk_io_data.write_count) + ' 次')
      $('#diskTime').html(ioTime + ' ms').css({ 'color': ioTime > 100 && ioTime < 1000 ? '#ff9900' : ioTime >= 1000 ? 'red' : '#20a53a' })

      index.iostat.add((disk_io_data.read_bytes / mb).toFixed(2), (disk_io_data.write_bytes / mb).toFixed(2), disk_io_data);


      var disk_option = '';
      $.each(res.iostat, function (k, v) {
        disk_option += '<option value="' + k + '" ' + (k == disk_key ? 'selected' : '') + '>' + (k == 'ALL' ? '全部' : k) + '</option>';
      });
      $('select[name="disk-io"]').html(disk_option);

      if (index.net.table) index.net.table.setOption({ xAxis: { data: index.net.data.aData }, series: [{ name: lan.index.net_up, data: index.net.data.uData }, { name: lan.index.net_down, data: index.net.data.dData }] });
      if (index.iostat.table) index.iostat.table.setOption({ xAxis: { data: index.iostat.data.aData }, series: [{ name: '读取字节数', data: index.iostat.data.uData }, { name: '写入字节数', data: index.iostat.data.dData }] });
      if (callback) callback(res)
    });
  },
  /**
   * @description 渲染画布视图
   * 
  */
  init_chart_view: function () {
    // 所有图表对象装进chart_view
    this.chart_view['load'] = echarts.init(document.querySelector("#loadChart"))
    this.chart_view['cpu'] = echarts.init(document.querySelector("#cpuChart"))
    this.chart_view['mem'] = echarts.init(document.querySelector("#memChart"))
    this.chart_view['disk'] = this.disk_view

    // 图表配置项
    this.series_option = {
      series: [{
        type: 'gauge',
        startAngle: 90,
        endAngle: -270,
        animationDuration: 1500,
        animationDurationUpdate: 1000,
        radius: '99%',
        pointer: {
          show: false
        },
        progress: {
          show: true,
          overlap: false,
          roundCap: true,
          clip: false,
          itemStyle: {
            borderWidth: 1,
            borderColor: '#20a53a'
          }
        },
        axisLine: {
          lineStyle: {
            width: 7,
            color: [[0, "rgba(204,204,204,0.5)"], [1, "rgba(204,204,204,0.5)"]]
          }
        },
        splitLine: {
          show: false,
          distance: 0,
          length: 10
        },
        axisTick: {
          show: false
        },
        axisLabel: {
          show: false,
          distance: 50
        },
        data: [{
          value: 0,
          detail: {
            offsetCenter: ['0%', '0%']
          },
          itemStyle: {
            color: '#20a53a',
            borderColor: '#20a53a'
          },
        }],
        detail: {
          width: 50,
          height: 15,
          lineHeight: 15,
          fontSize: 17,
          color: '#20a53a',
          formatter: '{value}%',
          fontWeight: 'normal'
        }
      }]
    };
    this.set_chart_data()
  },
  /**
   * @description 赋值chart的数据
   * 
  */
  set_chart_data: function () {
    this.chart_active("load")
    this.chart_active("cpu")
    if (!this.release) {
      this.chart_active("mem")
    }
    for (var i = 0; i < this.chart_view.disk.length; i++) {
      this.series_option.series[0].data[0].value = this.chart_json.disk[i].val
      this.series_option.series[0].data[0].itemStyle.color = this.chart_json.disk[i].color
      this.series_option.series[0].data[0].itemStyle.borderColor = this.chart_json.disk[i].color
      this.series_option.series[0].progress.itemStyle.borderColor = this.chart_json.disk[i].color
      this.series_option.series[0].detail.color = this.chart_json.disk[i].color
      this.chart_view.disk[i].setOption(this.series_option, true)
      $("#disk" + i).text(this.chart_result.disk[i].size[1] + " / " + this.chart_result.disk[i].size[0])
      $("#diskName" + i).text(this.chart_result.disk[i].path)
    }
  },
  /**
   * @description 赋值chart的数据
   * 
  */
  chart_active: function (name) {
    // 图表数据
    this.series_option.series[0].data[0].value = this.chart_json[name].val
    this.series_option.series[0].data[0].itemStyle.color = this.chart_json[name].color
    this.series_option.series[0].data[0].itemStyle.borderColor = this.chart_json[name].color
    this.series_option.series[0].progress.itemStyle.borderColor = this.chart_json[name].color
    this.series_option.series[0].detail.color = this.chart_json[name].color

    this.chart_view[name].setOption(this.series_option, true)

    // 文字
    var val = ""
    switch (name) {
      case 'load':
        val = this.chart_json[name].title
        break;
      case 'cpu':
        val = this.chart_result.cpu[1] + ' 核心'
        break;
      case 'mem':
        val = this.chart_result.mem.memRealUsed + " / " + this.chart_result.mem.memTotal + "(MB)"
        break;
    }

    $("#" + name).text(val)
  },
  /**
   * @description 赋值chart的颜色
   * 
  */
  chart_color_active: function (number) {
    var activeInfo = {};
    for (var i = 0; i < this.load_config.length; i++) {
      if (number >= this.load_config[i].val) {
        activeInfo = JSON.parse(JSON.stringify(this.load_config[i]));
        break;
      } else if (number <= 30) {
        activeInfo = JSON.parse(JSON.stringify(this.load_config[3]));
        break;
      }
    }
    activeInfo.val = number;
    return activeInfo;
  },




  get_index_list: function () {
    bt.soft.get_index_list(function (rdata) {
      var con = '';
      var icon = '';
      var rlen = rdata.length;
      var clickName = '';
      var setup_length = 0;
      for (var i = 0; i < rlen; i++) {
        if (rdata[i].setup) {
          setup_length++;
          if (rdata[i].admin) {
            clickName = ' onclick="bt.soft.set_lib_config(\'' + rdata[i].name + '\',\'' + rdata[i].title + '\')"';
          }
          else {
            clickName = 'onclick="soft.set_soft_config(\'' + rdata[i].name + '\')"';
          }
          var icon = rdata[i].name;
          if (bt.contains(rdata[i].name, 'php-')) {
            icon = 'php';
            rdata[i].version = '';
          }
          var status = '';
          if (rdata[i].status) {
            status = '<span style="color:#20a53a" class="glyphicon glyphicon-play"></span>';
          } else {
            status = '<span style="color:red" class="glyphicon glyphicon-pause"></span>'
          }
          con += '<div class="col-sm-3 col-md-3 col-lg-3" data-id="' + rdata[i].name + '">\
							<span class="spanmove"></span>\
							<div '+ clickName + '>\
							<div class="image"><img width="48" src="/static/img/soft_ico/ico-'+ icon + '.png"></div>\
							<div class="sname">'+ rdata[i].title + ' ' + rdata[i].version + status + '</div>\
							</div>\
						</div>'
        }
      }
      $("#indexsoft").html(con);
      //软件位置移动
      var softboxsum = 12;
      var softboxcon = '';
      if (setup_length <= softboxsum) {
        for (var i = 0; i < softboxsum - setup_length; i++) {
          softboxcon += '<div class="col-sm-3 col-md-3 col-lg-3 no-bg"></div>'
        }
        $("#indexsoft").append(softboxcon);
      }
      $("#indexsoft").dragsort({ dragSelector: ".spanmove", dragBetween: true, dragEnd: saveOrder, placeHolderTemplate: "<div class='col-sm-3 col-md-3 col-lg-3 dashed-border'></div>" });

      function saveOrder () {
        var data = $("#indexsoft > div").map(function () { return $(this).attr("data-id"); }).get();
        data = data.join('|');
        bt.soft.set_sort_index(data)
      };
    })
  },
  check_update: function () {
    var _load = bt.load('正在获取更新内容，请稍后...');
    bt.system.check_update(function (rdata) {
      _load.close();
      if (rdata.status === false) {
        if (!rdata.msg.beta) {
          bt.msg(rdata);
          return;
        }
        var loading = bt.open({
          type: 1,
          title: '[Linux' + (rdata.msg.is_beta == 1 ? '测试版' : '正式版') + ']-更新版本',
          area: '580px',
          shadeClose: false,
          skin: 'layui-layer-dialog',
          closeBtn: 2,
          content: '<div class="setchmod bt-form">\
                                <div class="update_title"><i class="layui-layer-ico layui-layer-ico1"></i><span>恭喜您，当前已经是最新版本</span></div>\
                                <div class="update_version">当前版本：<a href="http://www.bt.cn/bbs/forum.php?mod=viewthread&tid=19376" target="_blank" class="btlink" title="查看当前版本日志">宝塔Linux'+ (rdata.msg.is_beta == 1 ? '测试版 ' + rdata.msg.beta.version : '正式版 ' + rdata.msg.version) + '</a>&nbsp;&nbsp;发布时间：' + (rdata.msg.is_beta == 1 ? rdata.msg.beta.uptime : rdata.msg.uptime) + '</div>\
                                <div class="update_conter">\
                                    <div class="update_tips">'+ (rdata.msg.is_beta != 1 ? '测试版' : '正式版') + '最新版本为&nbsp;' + (rdata.msg.is_beta != 1 ? rdata.msg.beta.version : rdata.msg.version) + '&nbsp;&nbsp;&nbsp;更新时间&nbsp;&nbsp;' + (rdata.msg.is_beta != 1 ? rdata.msg.beta.uptime : rdata.msg.uptime) + '&nbsp;&nbsp;&nbsp;\
                                    '+ (rdata.msg.is_beta !== 1 ? '<span>如需更新测试版请点击<a href="javascript:;" onclick="index.beta_msg()" class="btlink btn_update_testPanel">查看详情</a></span>' : '<span>如需切换回正式版请点击<a href="javascript:;" onclick="index.to_not_beta()" class="btlink btn_update_testPanel">切换到正式版</a></span>') + '\
                                    '+ (rdata.msg.is_beta !== 1 ? rdata.msg.btb : '') + '\
                                    </div>\
                                </div>\
                                <div class="bt-form-submit-btn">\
                                    <button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+ lan.public.cancel + '</button>\
                                    <button type="button" class="btn btn-success btn-sm btn-title btn_update_panel" onclick="layer.closeAll()">'+ lan.public.know + '</button>\
                                </div>\
                            </div>\
                            <style>\
                                .setchmod{padding-bottom:50px;}\
                                .update_title{overflow: hidden;position: relative;vertical-align: middle;margin-top: 10px;}\
                                .update_title .layui-layer-ico{display: block;left: 60px !important;top: 1px !important;}\
                                .update_title span{display: inline-block;color: #333;height: 30px;margin-left: 105px;margin-top: 3px;font-size: 20px;}\
                                .update_conter{background: #f9f9f9;border-radius: 4px;padding: 20px;margin: 15px 37px;margin-top: 15px;}\
                                .update_version{font-size: 12px;margin:15px 0 10px 85px}\
                                .update_logs{margin-bottom:10px;border-bottom:1px solid #ececec;padding-bottom:10px;}\
                                .update_tips{font-size: 13px;color: #666;font-weight: 600;}\
                                .update_tips span{padding-top: 5px;display: block;font-weight: 500;}\
                            </style>'
        });
        return;
      }
      if (rdata.status === true) {
        var result = rdata
        var is_beta = rdata.msg.is_beta
        if (is_beta) {
          rdata = result.msg.beta
        } else {
          rdata = result.msg
        }
        var loading = bt.open({
          type: 1,
          title: '[Linux' + (is_beta === 1 ? '测试版' : '正式版') + ']-版本更新',
          area: '58 0px',
          shadeClose: false,
          skin: 'layui-layer-dialog',
          closeBtn: 2,
          content: '<div class="setchmod bt-form" style="padding-bottom:50px;">\
                                    <div class="update_title"><i class="layui-layer-ico layui-layer-ico0"></i><span>有新的面板版本更新，是否更新？</span></div>\
                                    <div class="update_conter">\
                                        <div class="update_version">最新版本：<a href="https://www.bt.cn/bbs/forum.php?mod=forumdisplay&fid=36" target="_blank" class="btlink" title="查看版本更新日志">宝塔Linux'+ (is_beta === 1 ? '测试版' : '正式版') + rdata.version + '</a>&nbsp;&nbsp;更新日期：' + (result.msg.is_beta == 1 ? result.msg.beta.uptime : result.msg.uptime) + '</div>\
                                        <div class="update_logs">'+ rdata.updateMsg + '</div>\
                                    </div>\
                                    <div class="update_conter">\
                                        <div class="update_tips">'+ (is_beta !== 1 ? '测试版' : '正式版') + '最新版本为&nbsp;' + (result.msg.is_beta != 1 ? result.msg.beta.version : result.msg.version) + '&nbsp;&nbsp;&nbsp;更新时间&nbsp;&nbsp;' + (is_beta != 1 ? result.msg.beta.uptime : result.msg.uptime) + '</div>\
                                        '+ (is_beta !== 1 ? '<span>如需更新测试版请点击<a href="javascript:;" onclick="index.beta_msg()" class="btlink btn_update_testPanel">查看详情</a></span>' : '<span>如需切换回正式版请点击<a href="javascript:;" onclick="index.to_not_beta()" class="btlink btn_update_testPanel">切换到正式版</a></span>') + '\
                                    </div>\
                                    <div class="bt-form-submit-btn">\
                                        <button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+ lan.public.cancel + '</button>\
                                        <button type="button" class="btn btn-success btn-sm btn-title btn_update_panel" onclick="index.to_update()" >'+ lan.index.update_go + '</button>\
                                    </div>\
                                </div>\
                                <style>\
                                    .update_title{overflow: hidden;position: relative;vertical-align: middle;margin-top: 10px;}.update_title .layui-layer-ico{display: block;left: 60px !important;top: 1px !important;}.update_title span{display: inline-block;color: #333;height: 30px;margin-left: 105px;margin-top: 3px;font-size: 20px;}.update_conter{background: #f9f9f9;border-radius: 4px;padding: 20px;margin: 15px 37px;margin-top: 15px;}.update_version{font-size: 13.5px; margin-bottom: 10px;font-weight: 600;}.update_logs{margin-bottom:10px;}.update_tips{font-size: 13px;color:#666;}.update_conter span{display: block;font-size:13px;color:#666}\
                                </style>'
        });
      }
    })
  },
  to_update: function () {
    layer.closeAll();
    bt.system.to_update(function (rdata) {
      if (rdata.status) {
        bt.msg({ msg: lan.index.update_ok, icon: 1 })
        $("#btversion").html(rdata.version);
        $("#toUpdate").html('');
        bt.system.reload_panel();
        setTimeout(function () { window.location.reload(); }, 3000);
      }
      else {
        bt.msg({ msg: rdata.msg, icon: 5, time: 5000 });
      }
    });
  },
  to_not_beta: function () {
    bt.show_confirm('切换到正式版', '是否从测试版切换到正式版？', function () {

      bt.send('apple_beta', 'ajax/to_not_beta', {}, function (rdata) {
        if (rdata.status === false) {
          bt.msg(rdata);
          return;
        }
        bt.system.check_update(function (rdata) {
          index.to_update();
        });

      });
    });
  },
  beta_msg: function () {
    bt.send('get_beta_logs', 'ajax/get_beta_logs', {}, function (data) {
      var my_list = '';
      for (var i = 0; i < data.list.length; i++) {
        my_list += '<div class="item_list">\
                                            <span class="index_acive"></span>\
                                            <div class="index_date">'+ bt.format_data(data.list[i].uptime).split(' ')[0] + '</div>\
                                            <div class="index_title">'+ data.list[i].version + '</div>\
                                            <div class="index_conter">'+ data.list[i].upmsg + '</div>\
                                        </div>'
      }
      layer.open({
        type: 1,
        title: '申请Linux测试版',
        area: '650px',
        shadeClose: false,
        skin: 'layui-layer-dialog',
        closeBtn: 2,
        content: '<div class="bt-form pd20" style="padding-bottom:50px;padding-top:0">\
                            <div class="bt-form-conter">\
                                <span style="font-weight: 600;">申请内测须知</span>\
                                <div class="form-body">'+ data.beta_ps + '</div>\
                            </div>\
                            <div class="bt-form-conter">\
                                <span style="font-size:16px;">Linux测试版更新日志</span>\
                                <div class="item_box"  style="height:180px;overflow: auto;">'+ my_list + '</div>\
                            </div>\
                            <div class="bt-form-line"> <label for="notice" style="cursor: pointer;"><input id="notice" disabled="disabled" type="checkbox" style="vertical-align: text-top;margin-right:5px"></input><span style="font-weight:500">我已查看“<b>《申请内测须知》</b>”<i id="update_time"></i></span></label>\</div>\
                            <div class="bt-form-submit-btn">\
                                <button type="button" class="btn btn-danger btn-sm btn-title" onclick="layer.closeAll()">'+ lan.public.cancel + '</button>\
                                <button type="button" class="btn btn-success btn-sm btn-title btn_update_panel_beta" disabled>'+ lan.index.update_go + '</button>\
                            </div>\
                            <style>\
                                .bt-form-conter{padding: 20px 25px;line-height: 29px;background: #f7f7f7;border-radius: 5px;padding-bottom:30px;margin-bottom:20px;}\
                                .bt-form-conter span{margin-bottom: 10px;display: block;font-size: 19px;text-align: center;color: #333;}\
                                .form-body{color: #333;}\
                                #notice span{cursor: pointer;}\
                                #update_time{font-style:normal;color:red;}\
                                .item_list{margin-left:95px;border-left:5px solid #e1e1e1;position:relative;padding:5px 0 0 2px}.index_title{border-bottom:1px solid #ececec;margin-bottom:5px;font-size:15px;color:#20a53a;padding-left:15px;margin-top:7px;margin-left:5px}.index_conter{line-height:25px;font-size:12px;min-height:40px;padding-left:20px;color:#888}.index_date{position:absolute;left:-90px;top:13px;font-size:13px;color:#333}.index_acive{width:15px;height:15px;background-color:#20a53a;display:block;border-radius:50%;position:absolute;left:-10px;top:21px}.index_acive::after{position:relative;display:block;content:"";height:5px;width:5px;display:block;border-radius:50%;background-color:#fff;top:5px;left:5px}\
                            </style>\
                        </div>'
      });
      var countdown = 5;
      function settime (val) {
        if (countdown == 0) {
          val.removeAttr("disabled");
          $('#update_time').text('');
          return false;
        } else {
          $('#update_time').text('还剩' + countdown + '秒，可点击。');
          countdown--;
          setTimeout(function () {
            settime(val)
          }, 1000)
        }
      }
      settime($('#notice'));
      $('#notice').click(function () {
        if ($(this).prop('checked')) {
          $('.btn_update_panel_beta').removeAttr('disabled');
        } else {
          $('.btn_update_panel_beta').attr('disabled', 'disabled');
        }
      });
      $('.btn_update_panel_beta').click(function () {
        bt.show_confirm('升级Linux内测版', '请仔细阅读内测升级须知，是否升级Linux内测版？', function () {

          bt.send('apple_beta', 'ajax/apple_beta', {}, function (rdata) {
            if (rdata.status === false) {
              bt.msg(rdata);
              return;
            }
            bt.system.check_update(function (rdata) {
              index.to_update();
            });
          });
        });
      })
    });
  },
  re_panel: function () {
    layer.confirm(lan.index.rep_panel_msg, { title: lan.index.rep_panel_title, closeBtn: 2, icon: 3 }, function () {
      bt.system.rep_panel(function (rdata) {
        if (rdata.status) {
          bt.msg({ msg: lan.index.rep_panel_ok, icon: 1 });
          return;
        }
        bt.msg(rdata);
      })
    });
  },
  re_server: function () {
    bt.open({
      type: 1,
      title: '重启服务器或者面板',
      area: '330px',
      closeBtn: 2,
      shadeClose: false,
      content: '<div class="rebt-con"><div class="rebt-li"><a data-id="server" href="javascript:;">重启服务器</a></div><div class="rebt-li"><a data-id="panel" href="javascript:;">重启面板</a></div></div>'
    })
    setTimeout(function () {
      $('.rebt-con a').click(function () {
        var type = $(this).attr('data-id');
        switch (type) {
          case 'panel':
            layer.confirm(lan.index.panel_reboot_msg, { title: lan.index.panel_reboot_title, closeBtn: 2, icon: 3 }, function () {
              var loading = bt.load();
              interval_stop = true;
              bt.system.reload_panel(function (rdata) {
                loading.close();
                bt.msg(rdata);
              });
              setTimeout(function () { window.location.reload(); }, 3000);
            });
            break;
          case 'server':
            var rebootbox = bt.open({
              type: 1,
              title: lan.index.reboot_title,
              area: ['500px', '280px'],
              closeBtn: 2,
              shadeClose: false,
              content: "<div class='bt-form bt-window-restart'>\
									<div class='pd15'>\
									<p style='color:red; margin-bottom:10px; font-size:15px;'>"+ lan.index.reboot_warning + "</p>\
									<div class='SafeRestart' style='line-height:26px'>\
										<p>"+ lan.index.reboot_ps + "</p>\
										<p>"+ lan.index.reboot_ps_1 + "</p>\
										<p>"+ lan.index.reboot_ps_2 + "</p>\
										<p>"+ lan.index.reboot_ps_3 + "</p>\
										<p>"+ lan.index.reboot_ps_4 + "</p>\
									</div>\
									</div>\
									<div class='bt-form-submit-btn'>\
										<button type='button' class='btn btn-danger btn-sm btn-reboot'>"+ lan.public.cancel + "</button>\
										<button type='button' class='btn btn-success btn-sm WSafeRestart' >"+ lan.public.ok + "</button>\
									</div>\
								</div>"
            });
            setTimeout(function () {
              $(".btn-reboot").click(function () {
                rebootbox.close();
              })
              $(".WSafeRestart").click(function () {
                var body = '<div class="SafeRestartCode pd15" style="line-height:26px"></div>';
                $(".bt-window-restart").html(body);
                $(".SafeRestartCode").append("<p>" + lan.index.reboot_msg_1 + "</p>");
                bt.pub.set_server_status_by("name=" + bt.get_cookie('serverType') + "&type=stop", function (r1) {
                  $(".SafeRestartCode p").addClass('c9');
                  $(".SafeRestartCode").append("<p>" + lan.index.reboot_msg_2 + "...</p>");
                  bt.pub.set_server_status_by("name=mysqld&type=stop", function (r2) {
                    $(".SafeRestartCode p").addClass('c9');
                    $(".SafeRestartCode").append("<p>" + lan.index.reboot_msg_3 + "...</p>");
                    bt.system.root_reload(function (rdata) {
                      $(".SafeRestartCode p").addClass('c9');
                      $(".SafeRestartCode").append("<p>" + lan.index.reboot_msg_4 + "...</p>");
                      var sEver = setInterval(function () {
                        bt.system.get_total(function () {
                          clearInterval(sEver);
                          $(".SafeRestartCode p").addClass('c9');
                          $(".SafeRestartCode").append("<p>" + lan.index.reboot_msg_5 + "...</p>");
                          setTimeout(function () {
                            layer.closeAll();
                          }, 3000);
                        })
                      }, 3000);
                    })
                  })
                })
              })
            }, 100)
            break;
        }
      })
    }, 100)
  },
  open_log: function () {
    bt.open({
      type: 1,
      area: '640px',
      title: lan.index.update_log,
      closeBtn: 2,
      shift: 5,
      shadeClose: false,
      content: '<div class="DrawRecordCon"></div>'
    });
    $.get('https://www.bt.cn/Api/getUpdateLogs?type=' + bt.os, function (rdata) {
      var body = '';
      for (var i = 0; i < rdata.length; i++) {
        body += '<div class="DrawRecord DrawRecordlist">\
							<div class="DrawRecordL">'+ rdata[i].addtime + '<i></i></div>\
							<div class="DrawRecordR">\
								<h3>'+ rdata[i].title + '</h3>\
								<p>'+ rdata[i].body + '</p>\
							</div>\
						</div>'
      }
      $(".DrawRecordCon").html(body);
    }, 'jsonp');
  },
  get_cloud_list: function () {
    $.post('/plugin?action=get_soft_list', { type: 8, p: 1, force: 1, cache: 1 }, function (rdata) {
      console.log("已成功从云端获取软件列表");
    });
  },
  // 获取安全风险列表
  get_warning_list: function (active, callback) {
    var that = this, obj = {};
    if (active == true) obj = { force: 1 }
    bt.send('get_list', 'warning/get_list', obj, function (res) {
      if (res.status !== false) {
        that.warning_list = res;
        that.warning_num = res.risk.length;
        $('.warning_num').css('color', (that.warning_num > 0 ? 'red' : '#20a53a')).html(that.warning_num);
        $('.warning_scan_ps').html(that.warning_num > 0 ? ('本次扫描共检测到风险项<i>' + that.warning_num + '</i>个,请及时修复！') : '本次扫描检测无风险项，请继续保持！');
        if (callback) callback(res);
      }
    });
  },
  /**
   * @description 获取时间简化缩写
   * @param {Numbre} dateTimeStamp 需要转换的时间戳
   * @return {String} 简化后的时间格式
  */
  get_simplify_time: function (dateTimeStamp) {
    if (dateTimeStamp === 0) return '刚刚';
    if (dateTimeStamp.toString().length == 10) dateTimeStamp = dateTimeStamp * 1000
    var minute = 1000 * 60, hour = minute * 60, day = hour * 24, halfamonth = day * 15, month = day * 30, now = new Date().getTime(), diffValue = now - dateTimeStamp;
    if (diffValue < 0) return '刚刚';
    var monthC = diffValue / month, weekC = diffValue / (7 * day), dayC = diffValue / day, hourC = diffValue / hour, minC = diffValue / minute;
    if (monthC >= 1) {
      result = "" + parseInt(monthC) + "月前";
    } else if (weekC >= 1) {
      result = "" + parseInt(weekC) + "周前";
    } else if (dayC >= 1) {
      result = "" + parseInt(dayC) + "天前";
    } else if (hourC >= 1) {
      result = "" + parseInt(hourC) + "小时前";
    } else if (minC >= 1) {
      result = "" + parseInt(minC) + "分钟前";
    } else {
      result = "刚刚";
    }
    return result;
  },
  /**
   * @description 渲染安全模块视图
   * @return 无返回值
  */
  reader_warning_view: function () {
    var that = this;
    function reader_warning_list (data) {
      var html = '', scan_time = '', arry = [['risk', '风险项'], ['security', '无风险项'], ['ignore', '已忽略项']], level = [['低危', '#e8d544'], ['中危', '#E6A23C'], ['高危', 'red']]
      bt.each(arry, function (index, item) {
        var data_item = data[item[0]], data_title = item[1];
        html += '<li class="module_item ' + item[0] + '">' +
          '<div class="module_head">' +
          '<span class="module_title">' + data_title + '</span>' +
          '<span class="module_num">' + data_item.length + '</span>' +
          '<span class="module_cut_show">' + (item[index] == 'risk' && that.warning_num > 0 ? '<i>点击折叠</i><span class="glyphicon glyphicon-menu-up" aria-hidden="false"></span>' : '<i>查看详情</i><span class="glyphicon glyphicon-menu-down" aria-hidden="false"></span>') + '</span>' +
          '</div>' +
          (function (index, item) {
            var htmls = '<ul class="module_details_list ' + (item[0] == 'risk' && that.warning_num > 0 ? 'active' : '') + '">';
            bt.each(data_item, function (indexs, items) {
              scan_time = items.check_time;
              htmls += '<li class="module_details_item">' +
                '<div class="module_details_head">' +
                '<span class="module_details_title"><span title="' + items.ps + '">' + items.ps + '</span><i>（&nbsp;检测时间：' + (that.get_simplify_time(items.check_time) || '刚刚') + '，耗时：' + (items.taking > 1 ? (items.taking + '秒') : ((items.taking * 1000).toFixed(2) + '毫秒')) + '&nbsp;，等级：' + (function (level) {
                  var level_html = '';
                  switch (level) {
                    case 3:
                      level_html += '<span style="color:red">高危</span>';
                      break;
                    case 2:
                      level_html += '<span style="color:#E6A23C">中危</span>';
                      break;
                    case 1:
                      level_html += '<span style="color:#e8d544">低危</span>';
                      break;
                  }
                  return level_html;
                }(items.level)) + '）</i></span>' +
                '<span class="operate_tools">' + (item[0] != 'security' ? ('<a href="javascript:;" class="btlink cut_details">详情</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" data-model="' + items.m_name + '" data-title="' + items.title + '" ' + (item[0] == 'ignore' ? 'class=\"btlink\"' : '') + ' data-type="' + item[0] + '">' + (item[0] != 'ignore' ? '忽略' : '移除忽略') + '</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" class="btlink" data-model="' + items.m_name + '" data-title="' + items.title + '">检测</a>') : '<a href="javascript:;" class="btlink cut_details">详情</a>') + '</span>' +
                '</div>' +
                '<div class="module_details_body">' +
                '<div class="module_details_line">' +
                '<div class="module_details_block"><span class="line_title">检测类型：</span><span class="line_content">' + items.title + '</span></div>' +
                '<div class="module_details_block"><span class="line_title">风险等级：</span><span class="line_content" style="color:' + level[items.level - 1][1] + '">' + level[items.level - 1][0] + '</span></div>' +
                '</div>' +
                '<div class="module_details_line"><span class="line_title">风险描述：</span><span class="line_content">' + items.msg + '</span></div>' +
                '<div class="module_details_line"><span class="line_title">' + (item[0] != 'security' ? '解决方案：' : '配置建议') + '</span><span class="line_content">' +
                (function () {
                  var htmlss = '';
                  bt.each(items.tips, function (indexss, itemss) {
                    htmlss += '<i>' + (indexss + 1) + '、' + itemss + '</i></br>';
                  });
                  return htmlss;
                }()) + '</span></div>' +
                (items.help != '' ? ('<div class="module_details_line"><span class="line_title">帮助文档：</span><span class="line_content"><a href="' + items.help + '" target="_blank" class="btlink">' + items.help + '</span></div>') : '') +
                '</div>' +
                '</li>';
            });
            htmls += '</ul>';
            return htmls;
          }(index, item))
          + '</li>'
      });
      $('.warning_scan_body').html(html);
      scan_time = Date.now() / 1000;
      $('.warning_scan_time').html('检测时间：&nbsp;' + bt.format_data(scan_time));
    }
    bt.open({
      type: '1',
      title: '安全风险',
      area: ['750px', '700px'],
      skin: 'warning_scan_view',
      content: '<div class="warning_scan_view">' +
        '<div class="warning_scan_head">' +
        '<span class="warning_scan_ps">' + (that.warning_num > 0 ? ('本次扫描共检测到风险项<i>' + that.warning_num + '</i>个,请及时修复！') : '本次扫描检测无风险项，请继续保持！') + '</span>' +
        '<span class="warning_scan_time"></span>' +
        '<button class="warning_again_scan">重新检测</button>' +
        '</div>' +
        '<ol class="warning_scan_body"></ol>' +
        '</div>',
      success: function () {
        $('.warning_again_scan').click(function () {
          var loadT = layer.msg('正在重新检测安全风险，请稍后...', { icon: 16 });
          that.get_warning_list(true, function () {
            layer.msg('扫描成功', { icon: 1 });
            reader_warning_list(that.warning_list);
          });
        });
        $('.warning_scan_body').on('click', '.module_item .module_head', function () {
          var _parent = $(this).parent(), _parent_index = _parent.index(), _list = $(this).next();
          if (parseInt($(this).find('.module_num').text()) > 0) {
            if (_list.hasClass('active')) {
              _list.css('height', 0);
              $(this).find('.module_cut_show i').text('查看详情').next().removeClass('glyphicon-menu-up').addClass('glyphicon-menu-down');
              setTimeout(function () {
                _list.removeClass('active').removeAttr('style');
              }, 500);
            } else {
              $(this).find('.module_cut_show i').text('点击折叠').next().removeClass('glyphicon-menu-down').addClass('glyphicon-menu-up');
              _list.addClass('active');
              var details_list = _list.parent().siblings().find('.module_details_list');
              details_list.removeClass('active');
              details_list.prev().find('.module_cut_show i').text('查看详情').next().removeClass('glyphicon-menu-up').addClass('glyphicon-menu-down')
            }
          }
        });
        $('.warning_scan_body').on('click', '.operate_tools a', function () {
          var index = $(this).index(), data = $(this).data();
          switch (index) {
            case 0:
              if ($(this).hasClass('active')) {
                $(this).parents('.module_details_head').next().hide();
                $(this).removeClass('active').text('详情');
              } else {
                var item = $(this).parents('.module_details_item'), indexs = item.index();
                $(this).addClass('active').text('折叠');
                item.siblings().find('.module_details_body').hide();
                item.siblings().find('.operate_tools a:eq(0)').removeClass('active').text('详情');
                $(this).parents('.module_details_head').next().show();
                $('.module_details_list').scrollTop(indexs * 41);
              }
              break;
            case 1:
              if (data.type != 'ignore') {
                bt.confirm({ title: '忽略风险', msg: '是否忽略【' + data.title + '】风险,是否继续?' }, function () {
                  that.warning_set_ignore(data.model, function (res) {
                    that.get_warning_list(false, function () {
                      bt.msg(res)
                      reader_warning_list(that.warning_list);
                    });
                  });
                });
              } else {
                that.warning_set_ignore(data.model, function (res) {
                  that.get_warning_list(false, function () {
                    bt.msg(res)
                    reader_warning_list(that.warning_list);
                    setTimeout(function () {
                      $('.module_item.ignore').click();
                    }, 100)
                  });
                });
              }
              break;
            case 2:
              that.waring_check_find(data.model, function (res) {
                that.get_warning_list(false, function () {
                  bt.msg(res)
                  reader_warning_list(that.warning_list);
                });
              });
              break;
          }
        });
        reader_warning_list(that.warning_list);
      }
    })
  },
  /**
   * @description 安全风险指定模块检查
   * @param {String} model_name 模块名称
   * @param {Function} callback 成功后的回调
   * @return 无返回值
  */
  waring_check_find: function (model_name, callback) {
    var loadT = layer.msg('正在检测指定模块，请稍后...', { icon: 16, time: 0 });
    bt.send('check_find', 'warning/check_find', { m_name: model_name }, function (res) {
      bt.msg(res);
      if (res.status !== false) {
        if (callback) callback(res);
      }
    });

  },

  /**
   * @description 安全风险指定模块是否忽略
   * @param {String} model_name 模块名称
   * @param {Function} callback 成功后的回调
   * @return 无返回值
  */
  warning_set_ignore: function (model_name, callback) {
    var loadT = layer.msg('正在设置模块状态，请稍后...', { icon: 16, time: 0 });
    bt.send('set_ignore', 'warning/set_ignore', { m_name: model_name }, function (res) {
      bt.msg(res);
      if (res.status !== false) {
        if (callback) callback(res);
      }
    });
  }
}
index.get_init();
index.consultancy_services()
//setTimeout(function () { index.get_cloud_list() }, 800);
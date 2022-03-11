$('.footer').css({
  'position': 'inherit',
  'padding-left': '180px'
});  //日报悬浮调整
var controlObj = {
  // 监控
  conTrolView: {
    init: function () {
      var that = this;
      var networkType = bt.get_cookie('network-unitType')
      if (!networkType) {
        bt.set_cookie('network-unitType', 'KB/s')
        networkType = 'KB/s'
      }
      var diskType = bt.get_cookie('disk-unitType')
      if (!diskType) {
        bt.set_cookie('disk-unitType', 'MB/s')
        diskType = 'MB/s'
      }

      $(".network-unit .picker-text-list").text(networkType);
      $(".disk-unit .picker-text-list").text(diskType);
      $(".network-unit .select-list-item li:contains(" + networkType + ")").addClass("active");
      $(".disk-unit .select-list-item :contains(" + diskType + ")").addClass("active");
      $(".bt-crontab-select-button").on('click', '.select-picker-search', function () {
        $(this).next().toggle();
        if ($(this).parent().hasClass('network-unit')) {
          $(".disk-unit .select-list-item").hide();
        } else {
          $(".network-unit .select-list-item").hide();
        }
      });
      $(".bt-crontab-select-button").on('click', '.select-list-item li', function () {
        var _button = $(this).parents('.bt-crontab-select-button');
        $(this).addClass('active').siblings().removeClass('active');
        _button.find('.picker-text-list').text($(this).text());
        _button.find(".select-list-item").toggle();
        var cookie_type = $(this).parents('.bgw').find('.searcTime .time_range_submit').attr('data-type');
        setCookie(cookie_type + '-unitType', $(this).attr('data-attr'));
        $(this).parents('.bgw').find('.searcTime .gt.on').click();
      });
      // 默认显示7天周期图表
      setTimeout(function () {
        that.Wday(0, 'getload');
      }, 500);

      setTimeout(function () {
        that.Wday(0, 'cpu');
      }, 500);

      setTimeout(function () {
        that.Wday(0, 'mem');
      }, 1000);

      setTimeout(function () {
        that.Wday(0, 'disk');
      }, 1500);

      setTimeout(function () {
        that.Wday(0, 'network');
      }, 2000);

      $('.btime').val(that.get_today() + ' 00:00:00');
      $('.etime').val(that.get_today() + ' 23:59:59');

      that.GetStatus();

      $(".st").hover(function () {
        $(this).next().show();
      }, function () {
        $(this).next().hide();
        $(this).next().hover(function () {
          $(this).show();
        }, function () {
          $(this).hide();
        })
      });

      $(".searcTime .gt").click(function () {
        $(this).addClass("on").siblings().removeClass("on");
        $(this).siblings('.ss').children('.on').removeClass('on');
      });

      $('.time_range_submit').click(function () {
        $(this).parents(".searcTime").find("span").removeClass("on");
        $(this).parents(".searcTime").find(".st").addClass("on");
        var b = (new Date($(this).parent().find(".btime").val()).getTime()) / 1000;
        var e = (new Date($(this).parent().find(".etime").val()).getTime()) / 1000;
        b = Math.round(b);
        e = Math.round(e);
        eval('that.' + $(this).attr('data-type') + '(' + b + ',' + e + ')');
      });
    },

    // 指定天数
    Wday: function (day, name) {
      var data = this.get_date(day);
      var b = data.b;
      var e = data.e;
      switch (name) {
        case "cpu":
          this.cpu(b, e);
          break;
        case "mem":
          this.mem(b, e);
          break;
        case "disk":
          this.disk(b, e);
          break;
        case "network":
          this.network(b, e);
          break;
        case "getload":
          this.getload(b, e);
          break;
      }
      //处理日报页面resize导致监控页图表没有重绘
      var event = document.createEvent("HTMLEvents");
      event.initEvent("resize", true, true);
      window.dispatchEvent(event);
    },

    get_date: function (day) {
      var now = Math.floor((new Date().getTime()) / 1000);
      var b = 0;
      var e = now;
      if (day == 0) {
        b = (new Date(this.get_today() + " 00:00:00").getTime()) / 1000;
      } else if (day == 1) {
        b = (new Date(this.get_before_date(day) + " 00:00:00").getTime()) / 1000;
        e = (new Date(this.get_before_date(day) + " 23:59:59").getTime()) / 1000;
      } else {
        b = (new Date(this.get_before_date(day - 1) + " 00:00:00").getTime()) / 1000;
      }
      b = Math.floor(b);
      e = Math.floor(e);
      return {
        b: b,
        e: e
      }
    },

    get_today: function () {
      var mydate = new Date();
      return bt.format_data(mydate.getTime() / 1000, 'yyyy/MM/dd');
    },

    get_before_date: function (day) {
      var now = new Date(this.get_today());
      var now_time = now.getTime();
      var before_days_time = (now_time - (day * 24 * 3600 * 1000)) / 1000;
      return bt.format_data(before_days_time, 'yyyy/MM/dd');
    },

    //取监控状态
    GetStatus: function () {

      loadT = layer.msg(lan.public.read, { icon: 16, time: 0 })
      $.post('/config?action=SetControl', 'type=-1', function (rdata) {
        layer.close(loadT);
        if (rdata.status) {
          $("#openJK").html("<input class='btswitch btswitch-ios' id='ctswitch' type='checkbox' checked><label class='btswitch-btn' for='ctswitch' onclick='controlObj.conTrolView.SetControl()'></label>")
        }
        else {
          $("#openJK").html("<input class='btswitch btswitch-ios' id='ctswitch' type='checkbox'><label class='btswitch-btn' for='ctswitch' onclick='controlObj.conTrolView.SetControl()'></label>")
        }
        $("#saveDay").val(rdata.day)
      })
    },

    //设置监控状态
    SetControl: function (act) {
      var day = $("#saveDay").val()
      if (day < 1) {
        layer.msg(lan.control.save_day_err, { icon: 2 });
        return;
      }
      if (act) {
        var type = $("#ctswitch").prop('checked') ? '1' : '0';
      } else {
        var type = $("#ctswitch").prop('checked') ? '0' : '1';
      }

      loadT = layer.msg(lan.public.the, { icon: 16, time: 0 })
      $.post('/config?action=SetControl', 'type=' + type + '&day=' + day, function (rdata) {
        layer.close(loadT);
        layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
      });
    },

    // 清理记录
    CloseControl: function () {
      bt.show_confirm(lan.control.close_log, lan.control.close_log_msg, function () {
        loadT = layer.msg(lan.public.the, { icon: 16, time: 0 })
        $.post('/config?action=SetControl', 'type=del', function (rdata) {
          layer.close(loadT);
          $.get('/system?action=ReWeb');
          layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
          setTimeout(function () {
            location.reload();
          }, 2000);
        });
      });
    },

    // 字节单位转换MB
    ToSizeG: function (bytes) {
      var c = 1024 * 1024;
      var b = 0;
      if (bytes > 0) {
        var b = (bytes / c).toFixed(2);
      }
      return b;
    },

    /**
    * 获取默认echart配置
    */
    get_default_option: function (startTime, endTime) {
      var interval = ((endTime - startTime) / 3) * 1000;
      return {
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          }
        },
        grid: {
          bottom: 80
        },
        xAxis: {
          type: 'time',
          boundaryGap: ['1%', '0%'],
          minInterval: interval,
          axisLine: {
            lineStyle: {
              color: "#666"
            }
          },
          axisLabel: {
            formatter: function (value) {
              return bt.format_data(value / 1000, 'MM/dd\nhh:mm');
            }
          }
        },
        yAxis: {
          type: 'value',
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
        dataZoom: [
          {
            type: 'inside',
            start: 0,
            end: 100,
            zoomLock: true
          },
          {
            bottom: 10,
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
          }
        ]
      }
    },

    /**
    * 补全数据
    * @param {*} rdata 
    */
    set_data: function (data, startTime, endTime) {
      if (data.length <= 0) return;
      var time;
      // var min = data[0];
      // min.addtime = min.addtime.replace(/([0-9]{2}\/[0-9]{2}).{1}[0-9:]*/, '$1 00:00');
      // data.unshift(min);
      // for (var key in data[0]) {
      //   if (key == 'addtime') continue;
      //   data[0][key] = 0;
      // }

      for (var i = 0; i < data.length; i++) {
        if (typeof data[i].addtime === "number") continue;
        time = this.get_time(data[i].addtime, data[data.length - 1].addtime);
        data[i].addtime = time;
      }
    },

    get_time: function (date, endDate) {
      var endMonth = endDate.split(' ')[0].split('/');
      endMonth = parseInt(endMonth);

      var today = new Date();
      var str = date.split(' ');
      var dateStr = str[0].split('/');
      var timeStr = str[1].split(':');
      var month = parseInt(dateStr[0]);
      var year = today.getFullYear();
      if (month > endMonth) {
        year -= 1;
      }
      var newDate = new Date(year, month - 1, dateStr[1], timeStr[0], timeStr[1]);
      return newDate.getTime();
    },

    //cpu
    cpu: function (b, e) {
      var that = this;
      $.get('/ajax?action=GetCpuIo&start=' + b + '&end=' + e, function (rdata) {
        that.set_data(rdata, b, e);
        var myChartCpu = echarts.init(document.getElementById('cpuview'));
        var xData = [];
        var yData = [];
        //var zData = [];
        if (rdata.length > 0) {
          for (var i = 0; i < rdata.length; i++) {
            // xData.push(rdata[i].addtime);
            // yData.push(rdata[i].pro);
            // zData.push(rdata[i].mem);
            yData.push([rdata[i].addtime, rdata[i].pro]);
          }
          var startTime = rdata[0].addtime / 1000;
          var endTime = rdata[rdata.length - 1].addtime / 1000;
          var option = that.get_cpu_option(startTime, endTime, yData);
          myChartCpu.setOption(option);
          window.addEventListener("resize", function () {
            myChartCpu.resize();
          });
        }
      });
    },

    /**
    * 获取cpu图表配置
    */
    get_cpu_option: function (startTime, endTime, yData) {
      var option = this.get_default_option(startTime, endTime);
      option.tooltip.formatter = function (config) {
        var data = config[0];
        var time = data.data[0];
        var date = bt.format_data(time / 1000);
        return date + '<br>' + data.seriesName + ': ' + data.data[1].toFixed(2) + '%';
      };
      option.yAxis.name = lan.public.pre;
      option.yAxis.min = 0;
      option.yAxis.max = 100;
      option.series = [
        {
          name: 'CPU',
          type: 'line',
          symbol: 'none',
          itemStyle: {
            normal: {
              color: 'rgb(0, 153, 238)'
            }
          },
          data: yData
        }
      ];
      return option;
    },

    //内存
    mem: function (b, e) {
      var that = this;
      $.get('/ajax?action=GetCpuIo&start=' + b + '&end=' + e, function (rdata) {
        that.set_data(rdata, b, e);
        var myChartMen = echarts.init(document.getElementById('memview'));
        var xData = [];
        //var yData = [];
        var zData = [];
        if (rdata.length > 0) {
          for (var i = 0; i < rdata.length; i++) {
            // xData.push(rdata[i].addtime);
            // yData.push(rdata[i].pro);
            // zData.push(rdata[i].mem);
            zData.push([rdata[i].addtime, rdata[i].mem]);
          }
          var startTime = rdata[0].addtime / 1000;
          var endTime = rdata[rdata.length - 1].addtime / 1000;
          option = that.get_mem_option(startTime, endTime, zData);
          myChartMen.setOption(option);
          window.addEventListener("resize", function () {
            myChartMen.resize();
          });
        }
      })
    },

    /**
    * 获取mem图表配置
    */
    get_mem_option: function (startTime, endTime, zData) {
      var option = this.get_default_option(startTime, endTime);
      option.tooltip.formatter = function (config) {
        var data = config[0];
        var time = data.data[0];
        var date = bt.format_data(time / 1000);
        return date + '<br>' + data.seriesName + ': ' + data.data[1].toFixed(2) + '%';
      };
      option.yAxis.name = lan.public.pre;
      option.yAxis.min = 0;
      option.yAxis.max = 100;
      option.series = [
        {
          name: lan.index.process_mem,
          type: 'line',
          symbol: 'none',
          itemStyle: {
            normal: {
              color: 'rgb(0, 153, 238)'
            }
          },
          data: zData
        }
      ];
      return option;
    },

    //磁盘io
    disk: function (b, e) {
      var that = this;
      $.get('/ajax?action=GetDiskIo&start=' + b + '&end=' + e, function (rdata) {
        that.set_data(rdata, b, e);
        var diskview = document.getElementById('diskview'), myChartDisk = echarts.init(diskview), rData = [], wData = [], xData = [], unit_size = 1, _unit = getCookie('disk-unitType');
        $(diskview).next().removeClass('hide').addClass('show');
        switch (_unit) {
          case 'MB/s':
            unit_size = 1024;
            break;
          case 'GB/s':
            unit_size = 1024 * 1024;
            break;
          default:
            unit_size = 1;
            break;
        }

        var is_gt_MB = false;
        var is_gt_GB = false;
        for (var i = 0; i < rdata.length; i++) {
          var read = (rdata[i].read_bytes / 1024).toFixed(3);
          var write = (rdata[i].write_bytes / 1024).toFixed(3);
          // rData.push(read / unit_size);
          // wData.push(write / unit_size);
          // xData.push(rdata[i].addtime);
          // yData.push(rdata[i].read_count);
          // zData.push(rdata[i].write_count);
          rData.push([rdata[i].addtime, read / unit_size]);
          wData.push([rdata[i].addtime, write / unit_size]);
          var read_MB = read / 1024;
          var write_MB = write / 1024;
          if ((read_MB >= 1 || write_MB >= 1) && !is_gt_MB) {
            is_gt_MB = true;
          }
          if (is_gt_MB) {
            var read_GB = read_MB / 1024;
            var write_GB = write_MB / 1024;
            if ((read_GB >= 1 || write_GB >= 1) && !is_gt_GB) {
              console.log(read_GB);
              console.log(write_GB);
              is_gt_GB = true;
            }
          }
        }
        if (!is_gt_GB) {
          $('#diskview').next().find('.select-list-item li').eq(2).hide();
        } else {
          $('#diskview').next().find('.select-list-item li').eq(2).show();
        }
        if (!is_gt_MB) {
          $('#diskview').next().find('.select-list-item li').eq(1).hide();
        } else {
          $('#diskview').next().find('.select-list-item li').eq(1).show();
        }
        if (rdata.length > 0) {
          var startTime = rdata[0].addtime / 1000;
          var endTime = rdata[rdata.length - 1].addtime / 1000;
          var option = that.get_disk_option(_unit, startTime, endTime, rData, wData);
          myChartDisk.setOption(option);
          window.addEventListener("resize", function () {
            myChartDisk.resize();
          });
        }
      })
    },

    /**
    * 获取磁盘IO图表配置
    */
    get_disk_option: function (unit, startTime, endTime, rData, wData) {
      var option = this.get_default_option(startTime, endTime);
      option.tooltip.formatter = function (config) {
        var data = config[0];
        var time = data.data[0];
        var date = bt.format_data(time / 1000);
        var _tips = '';
        for (var i = 0; i < config.length; i++) {
          _tips += '<span style="display: inline-block; width: 10px; height: 10px; margin-rigth:10px; border-radius: 50%; background: ' + config[i].color + ';"></span>  ' + config[i].seriesName + '：' + config[i].data[1].toFixed(3) + unit + (config.length - 1 !== i ? '<br />' : '');
        }
        return "时间：" + date + "<br />" + _tips;
      };
      option.legend = {
        top: '18px',
        data: [lan.control.disk_read_bytes, lan.control.disk_write_bytes]
      };
      option.series = [
        {
          name: lan.control.disk_read_bytes,
          type: 'line',
          symbol: 'none',
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
          symbol: 'none',
          itemStyle: {
            normal: {
              color: 'rgba(46, 165, 186, .7)'
            }
          },
          data: wData
        }
      ];
      return option;
    },

    //网络Io
    network: function (b, e) {
      var that = this;
      $.get('/ajax?action=GetNetWorkIo&start=' + b + '&end=' + e, function (rdata) {
        that.set_data(rdata, b, e);
        var anetwork = document.getElementById('network'), myChartNetwork = echarts.init(anetwork), aData = [], bData = [], cData = [], dData = [], xData = [], yData = [], zData = [], unit_size = 1, _unit = getCookie('network-unitType'), network_io = [{ title: '全部', value: 'all' }], network_select = $('[name="network-io"]'), network_html = '<option value="">全部</option>', is_network = 0, network_io_key = bt.get_cookie('network_io_key') || '';
        $(anetwork).next().removeClass('hide').addClass('show');
        switch (_unit) {
          case 'MB/s':
            unit_size = 1024;
            break;
          case 'GB/s':
            unit_size = 1024 * 1024;
            break;
          default:
            unit_size = 1;
            break;
        }
        network_select.unbind('change').change(function () {
          bt.set_cookie('network_io_key', $(this).val());
          that.network(b, e);
        }).removeClass('hide').addClass('show');

        var is_gt_MB = false;
        var is_gt_GB = false;
        for (var i = 0; i < rdata.length; i++) {
          var items = rdata[i];
          if (is_network < 1 && typeof items.down_packets === 'object') {
            for (var key in items.down_packets) {
              network_html += '<option value="' + key + '" ' + (network_io_key === key ? 'selected' : '') + '>' + key + '</option>';
            }
            network_select.html(network_html);
            is_network++;
          }
          if (typeof network_io_key != 'undefined' && network_io_key != '') {
            if (typeof items.down_packets === 'object') {
              // zData.push(items.down_packets[network_io_key] / unit_size);
              zData.push([items.addtime, items.down_packets[network_io_key] / unit_size]);
            } else {
              // zData.push(0);
              zData.push([items.addtime, 0]);
            }
          } else {
            // zData.push(items.down / unit_size);
            zData.push([items.addtime, items.down / unit_size]);
          }
          if (typeof network_io_key != 'undefined' && network_io_key != '') {
            if (typeof items.up_packets === 'object') {
              // yData.push(items.up_packets[network_io_key] / unit_size);
              yData.push([items.addtime, items.up_packets[network_io_key] / unit_size]);
            } else {
              // yData.push(0);
              yData.push([items.addtime, 0]);
            }
          } else {
            // yData.push(items.up / unit_size);
            yData.push([items.addtime, items.up / unit_size]);
          }
          var up_MB = items.up / 1024;
          var down_MB = items.down / 1024;
          if ((up_MB >= 1 || down_MB >= 1) && !is_gt_MB) {
            is_gt_MB = true;
          }
          if (is_gt_MB) {
            var up_GB = up_MB / 1024;
            var down_GB = down_MB / 1024;
            if ((up_GB >= 1 || down_GB >= 1) && !is_gt_GB) {
              is_gt_GB = true;
            }
          }
          // xData.push(items.addtime);
        }
        if (!is_gt_GB) {
          $('#network').next().find('.select-list-item li').eq(2).hide();
        } else {
          $('#network').next().find('.select-list-item li').eq(2).show();
        }
        if (!is_gt_MB) {
          $('#network').next().find('.select-list-item li').eq(1).hide();
        } else {
          $('#network').next().find('.select-list-item li').eq(1).show();
        }
        if (rdata.length > 0) {
          var startTime = rdata[0].addtime / 1000;
          var endTime = rdata[rdata.length - 1].addtime / 1000;
          var option = that.get_network_option(_unit, startTime, endTime, yData, zData);
          myChartNetwork.setOption(option);
          window.addEventListener("resize", function () {
            myChartNetwork.resize();
          });
        }
      })
    },

    /**
    * 获取网络IO图表配置
    */
    get_network_option: function (unit, startTime, endTime, yData, zData) {
      var option = this.get_default_option(startTime, endTime);
      option.tooltip.formatter = function (config) {
        var data = config[0];
        var time = data.data[0];
        var date = bt.format_data(time / 1000);
        var _tips = '';
        for (var i = 0; i < config.length; i++) {
          _tips += '<span style="display: inline-block;width: 10px;height: 10px;margin-rigth:10px;border-radius: 50%;background: ' + config[i].color + ';"></span> ' + config[i].seriesName + '：' + config[i].data[1].toFixed(3) + unit + (config.length - 1 !== i ? '<br />' : '');
        }
        return "时间：" + date + "<br />" + _tips;
      };
      option.legend = {
        top: '18px',
        data: [lan.index.net_up, lan.index.net_down]
      };
      option.series = [
        {
          name: lan.index.net_up,
          type: 'line',
          symbol: 'none',
          itemStyle: {
            normal: {
              color: 'rgb(255, 140, 0)'
            }
          },
          data: yData
        },
        {
          name: lan.index.net_down,
          type: 'line',
          symbol: 'none',
          itemStyle: {
            normal: {
              color: 'rgb(30, 144, 255)'
            }
          },
          data: zData
        }
      ];
      return option;
    },

    //负载
    getload_old: function (b, e) {
      $.get('/ajax?action=get_load_average&start=' + b + '&end=' + e, function (rdata) {
        var myChartgetload = echarts.init(document.getElementById('getloadview'));
        var aData = [];
        var bData = [];
        var xData = [];
        var yData = [];
        var zData = [];


        for (var i = 0; i < rdata.length; i++) {
          xData.push(rdata[i].addtime);
          yData.push(rdata[i].pro);
          zData.push(rdata[i].one);
          aData.push(rdata[i].five);
          bData.push(rdata[i].fifteen);
        }
        var interval = ((e - b) / 3) * 1000;
        option = {
          tooltip: {
            trigger: 'axis'
          },
          calculable: true,
          legend: {
            data: ['系统资源使用率', '1分钟', '5分钟', '15分钟'],
            selectedMode: 'single',
          },
          xAxis: {
            type: 'category',
            boundaryGap: false,
            data: xData,
            minInterval: interval,
            axisLine: {
              lineStyle: {
                color: "#666"
              }
            }
          },
          yAxis: {
            type: 'value',
            name: '',
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
              name: '系统资源使用率',
              type: 'line',
              smooth: true,
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
              name: '1分钟',
              type: 'line',
              smooth: true,
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
              name: '5分钟',
              type: 'line',
              smooth: true,
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
              name: '15分钟',
              type: 'line',
              smooth: true,
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
        window.addEventListener("resize", function () {
          myChartgetload.resize();
        });
      })
    },


    // 系统负载
    getload: function (b, e) {
      var that = this;
      $.get('/ajax?action=get_load_average&start=' + b + '&end=' + e, function (rdata) {
        that.set_data(rdata, b, e);
        var myChartgetload = echarts.init(document.getElementById('getloadview'));
        var aData = [];
        var bData = [];
        var xData = [];
        var yData = [];
        var zData = [];

        for (var i = 0; i < rdata.length; i++) {
          // xData.push(rdata[i].addtime);
          // yData.push(rdata[i].pro);
          // zData.push(rdata[i].one);
          // aData.push(rdata[i].five);
          // bData.push(rdata[i].fifteen);
          zData.push([rdata[i].addtime, rdata[i].one]);
          yData.push([rdata[i].addtime, rdata[i].pro]);
          aData.push([rdata[i].addtime, rdata[i].five]);
          bData.push([rdata[i].addtime, rdata[i].fifteen]);
        }
        if (rdata.length > 0) {
          var startTime = rdata[0].addtime / 1000;
          var endTime = rdata[rdata.length - 1].addtime / 1000;
          var option = that.get_load_option(startTime, endTime, yData, zData, aData, bData);
          myChartgetload.setOption(option);
          window.addEventListener("resize", function () {
            myChartgetload.resize();
          });
        }
      })
    },

    /**
    * 获取平均负载图表配置
    */
    get_load_option: function (startTime, endTime, yData, zData, aData, bData) {
      var option = this.get_default_option(startTime, endTime);
      var interval = ((endTime - startTime) / 3) * 1000;
      option.tooltip.formatter = function (config) {
        var line = config[0].axisValueLabel,
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
          var color_line = '</br><span style="width: 8px; display: inline-block; height: 8px; background: ' + line_color + '; border-radius: 100px; margin-right: 7px;"></span>',
            text_line = config[i].seriesName + ': ' + config[i].data[1].toFixed(2);
          if (config[0].componentIndex == 0) {
            if (config[i].seriesName == '资源使用率') {
              line += color_line + text_line + '%';
            }
          } else {
            if (config[i].seriesName != '资源使用率') {
              line += color_line + text_line;
            }
          }
        }
        return line;
      };
      option.legend = {
        data: ['1分钟', '5分钟', '15分钟'],
        right: '16%',
        top: '10px'
      };
      option.axisPointer = {
        link: { xAxisIndex: 'all' },
        lineStyle: {
          color: '#aaaa',
          width: 1
        }
      };
      // 直角坐标系内绘图网格
      option.grid = [
        {
          left: '5%',
          bottom: 80,
          right: '55%',
          width: '40%',
          height: 'auto'
        },
        {
          bottom: 80,
          left: '55%',
          width: '40%',
          height: 'auto'
        }
      ];
      // 直角坐标系grid的x轴
      option.xAxis = [
        {
          type: 'time',
          boundaryGap: ['1%', '0%'],
          minInterval: interval,
          axisLine: {
            lineStyle: {
              color: "#666"
            }
          },
          axisLabel: {
            formatter: function (value) {
              return bt.format_data(value / 1000, 'MM/dd\nhh:mm');
            }
          }
        },
        {
          type: 'time',
          gridIndex: 1,
          boundaryGap: ['1%', '0%'],
          minInterval: interval,
          axisLine: {
            lineStyle: {
              color: "#666"
            }
          },
          axisLabel: {
            formatter: function (value) {
              return bt.format_data(value / 1000, 'MM/dd\nhh:mm');
            }
          }
        }
      ];
      option.yAxis = [
        {
          scale: true,
          name: '资源使用率',
          boundaryGap: [0, '100%'],
          min: 0,
          max: function (value) {
            // 最大值超过80
            if(value.max == 100 || (value.max + 20 > 100)) return 100;
            // 小于80取当前最大值的首位数字
            return parseInt((value.max + 10).toString().slice(0,1) + '0')
          },
          // y轴网格显示
          splitLine: {
            show: true,
            lineStyle: {
              color: "#ddd"
            }
          },
          // 坐标轴名样式
          nameTextStyle: {
            color: '#666',
            fontSize: 12,
            align: 'left'
          },
          axisLine: {
            lineStyle: {
              color: '#666',
            }
          }
        },
        {
          scale: true,
          name: '负载详情',
          gridIndex: 1,
          splitLine: {
            show: true,
            lineStyle: {
              color: "#ddd"
            }
          },
          nameTextStyle: {
            color: '#666',
            fontSize: 12,
            align: 'left'
          },
          axisLine: {
            lineStyle: {
              color: '#666',
            }
          }
        }
      ];
      option.dataZoom[0].xAxisIndex = [0, 1];
      option.dataZoom[1].type = 'slider';
      option.dataZoom[1].left = '5%';
      option.dataZoom[1].right = '5%';
      option.dataZoom[1].xAxisIndex = [0, 1];
      option.series = [
        {
          name: '资源使用率',
          type: 'line',
          symbol: 'none',
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
          symbol: 'none',
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
          symbol: 'none',
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
          symbol: 'none',
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
      ];
      option.textStyle = {
        color: '#666',
        fontSize: 12
      };
      return option;
    }
  },
  // 日报
  dailyView: function (date) {
    var that = this, _liHthml = '', paramDate = date ? date : getBeforeDate(1).replace(/\//g, '')
    $.post('/daily?action=get_daily_data', { date: paramDate }, function (res) {
      if (!res.status) {
        var product_view = '<div class="daily-thumbnail">' +
          '<div class="thumbnail-box">' +
          '<img style="max-width: 400px;box-shadow: 1px 1px 30px rgb(0 0 0 / 10%);" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAA4wAAAM4CAIAAAAI8/uWAAAgAElEQVR4Aey9C3Bc13nn+VFybPmxtmWGBEBRtNthvGu5DIAiLPMhyS5EIsaARrDJpVekKG0IaEWmlCEwira8pAgYAvgY12oUgGXNkhoBTEl8eMQlLTAGEsoOJrFFglJAgYDG8iTFuGUJJAAytBRP7DjeKNjvO+eec899dDcAAt0N4H+rq/vc8z6/+/rf7zx63tjYGGEDARAAARAAARAAARAAgXwicF0+VQZ1AQEQAAEQAAEQAAEQAAEhAJGK8wAEQAAEQAAEQAAEQCDvCECk5t0hQYVAAARAAARAAARAAAQgUnEOgAAIgAAIgAAIgAAI5B0BiNS8OySoEAiAAAiAAAiAAAiAwPtmE4J/VBvWK7j2Yzpv3ryPqO3as0IOIAACIAACIAACIDAJArNNpC5YsOD666+fBAgkcQm89957V65cYZnqesINAiAAAiAAAiAAAlkjMKu6+9mGCoU6JacOY4RBekpIIhMQAAEQAAEQAIHJEZhVInVyCJAKBEAABEAABEAABEAg3whApObbEUF9QAAEQAAEQAAEQAAEsJg/zgEQAAEQAAEQAAEQAIH8IwBLav4dE9QIBEAABEAABEAABOY8AYjUOX8KAAAIgMCMI/BON/2/6+ilp+nHIzOu7qgwCIAACIyTQKolqAZby3rK++qLVTaD+8p67uyrX9RZt4sa91XPd/K+erKumRrb7r3YWlZzyPHXztWNp9ruleicQ81zkWDxWN3Q3Va9UFyD++qS9yn3Za8gOllX0XxawmTb1GHqo/fxDQIgAAJzlMDPeuhfTtDPT9CHKucoATQbBEBgDhBIJVKL65/tKdvWeUok6WDPc5vKtxFdTsOjuL6vgxxdy5qztaw9scIXtJue7asvDecgwlT8rnZuq2g5Q/RcWYuJUrGNOu4iI3NFNJsQ/IIACIDA3CZw5bBqfyV9MpEWxAj92f30T2mjSOBaWvtIxkiIAAIgAAJZJpC6u7+0vmNpy/Pn6erJ9kN0qKasrKyy5fSZlgp2yFbX+UZnXVkZWzpPN7Nf6yAV13cn2tl1nuUsB7UnjIl0HE2aX72vr+NBtqr2ydbdsHpVA+vjm8aR8hqisPD1trqTV00+1rOu04hythabiNxMZ5NmqvY6fmFnJI6f275AZm5CG8epmFij9eZ6uqngBgEQmBsE+uld1cv/gbV0c6YW/3MP/Sbj591MuSAcBEAABHJAIJUlVapSvK2vmA2iDxFrR+mRN73w1jpa3VdtuvuV38LqtmeTZQ+VHXI68SfSptMtlcaSuqpBJxQF3Kydm8onklfGuIP7WEb39clIAxamFa1L2NDLBt2aZOOpPh6icL61rLI1wQMMLnc2v1nb19fG8bixFca6LMMbVm3atCpNOZxtJM751ormREdfW7EyHted9IZDBHI538ojKPr65gvwyubOFTIEgouuudBwqk8M26a2gUTYAQEQmM0E3vs1/eLXXgMvddN7ynnjLfROUF++/+P04dmMAW0DARCYUwTiRao3hFSZM+uVPssERQkyjvRgR19fveq+Lyvj7vuJqVUzPlWpYV1iqLtfKsZaLTguNlPd4sOLt7FS1Ftx+YPU/tZVWvRyz5lNtfuU4C59oGFVRc/5+uLS6jYe6qC2+SvKVzcnLxLNZ7OxtJNF7SE1XMGLEPyJiTP4w0PcIlXu/OqaTS0dL1+9NzDGV3IorW8rVTktvL18VUvyEtHCqy//4PSmmjZVs+IHGldX/HCwvtRUP1hq7N7Pfvazt956KzaIPZcsWfLJT34yVSj8QQAEck/gygn6y/vD1RhZRaF5U/PP0N0rw9Fkfy19+TgVBkNGjsTkGYyCPRAAARDIIYF4kco21L77ZPbSxcDUJalnhbF1ih7dJjpJjJ0/YCOfiFPePNvqvr5qtWu/DomFNbqtbrjPesZYUm3YdDp40C0lnp1Pl5KnHywXk6ls8xNLqYeVa6k1HNPVsz2nV5U36vDJfF9NXlhdfp/JcFFi9RkteVPkdVmLZg69mDyzqXyfF23+kgT9IHmVik1GKZI73lqDxupUKFSHE5wgAAIgAAIgAAL5QiBepNra3XRvW9+9vMeGUjXZnzvBf1iutal0iJfVcJg2drKNs+I5m8700StbrNZSaSdO6YQxllSbo3aIeg55XeuudPEfYsFdyvI6tVWUS5Geeh75EDF8TqACrDUp/TQHnZlnybYLGlxOpq3ZuGoQq1OhUMfFDpFAIH8IfOTb9MnPhqvz6x76u91hT+yDAAiAwAwnkEGkeq1jkbQqEZjGpNVqX72ym0oskY/bxOFZUtXKU7J/bdv0jUmVesmgzxbSg1DZdsoWyjfjq6tUI6+BZUcIxETjhnsLZjnSPBjvpkTcGFYjSdVgCWWcNjD53aCsR1ZFSCTo2mUqhXQqFGrw6GAPBGYCgQ/cSp+PdOiPjNDfxVZ+mLyBrJ+lBbER4AkCIAAC+UtgPCJ1sFUpObdz+epbydWfCqjWa2uiGdIaXIKqYelpY38VU+61FRFJzTr7IeIhtIGhnRdsNzp3zVPiTm60LI/VcxcPZ3ABRHJjjetZnWOCHK/Taoyp8uDRBasSPHhgvtH3TjTttMNPeTeZvEzFakFZhk9LyzPUJpKX9rA6FQo1BSF4g8AMIXD5J/Shz9JH0tb2V+94wdffSNenjYlAEAABEMg/AtelrBJLKA5jWyP36T/bp9fkJx5G+ZysRsUd3+XOGqiq699bIMksSuXtyopUmTeZY9TX17GJbZD8LdOt+vr2JZK8PqueQmRyYKMjr95q14sy3pP4vdrZcWjTs96/FXjpebIUyapbsp1/voUaHuDSlaNxagzDMlnqUIeuv6pATczgAV471qx+Nfh88+lNd7KKZrVKLd/RS1axJzXcF5DWXv3H98M69Y477tBqdXwpEAsEQCCvCCTpT2+hnlvo1f4M1RoyET4YGSGQISWCQQAEQCD3BFJYUpWVcdODLRXfYVOjMwqUF5kKT4hSbShVk92VM1V3f6aJU2wrlaVV2UBY311eV9lKjclDD9bWTxciGR566Iwzl0vNA6ve2VBXWVYmhXLnvihIMVueOeRPF5vYegWR2svqs2U6NxnLG5TgOnbxttoeVvhqx8aZf29jwzZej1Z82bqs/6NLx8c3CIDAHCOQoA/fQL9kI0I7/fzb9IlUrX+X/vZJL+zGOJH6UTvbP0k/p9T5pMof/iAAAiAwvQTmjY2NRUuw/1Dqj7OMRnrw8U3P7Y4uiRorUtkCKn+sGtFkpiDuUm+mnd7/o6qiBlu3JR9Q/3fl/eGqWUwgWhHrMzw8XFRUZHfhuBYCgHkt9JAWBKaYgF0uSi8y9XY7nX5Iirj5p7Q6QaFQXfbZ++nNI8oZt/6UBPTTsVu9JVffX0vzy+kTSrb+8if04XX0eSthdXb4BgEQAIFsE4gXqdmuxRSVB101RSAlG8CcQpjICgSulUBYhr5Lf3qjGFPpcbp3F/3CrHjqrZP6a3q5loa0QiUqfI2+vCy+Aqer6O3umKDPvEO3fjzGH14gAAIgkEUCqcekZrESKAoEQAAEQGAiBD5On3xcxd9NP343kPAf+unFW3yF+qHDdEcKhcrJVhymT5QHkstOOc2HQo1QgQcIgEDWCaQYk5r1eqBAEAABEACBCRD43Dr6m930W7vot28IpPrHn9CvzYp1H3qWyjemm9d//cdpzV/Qz39CF4edTG7EelUODThBAARyRgAiNWfoUTAIgMDMIBDWcNmq9W+voqKgAHVLvn4ZrXmHPqZMnu6fo960kYqTNMgTqg7T75WnU6g2t098lviDDQRAAATyjABEap4dEFQHBEAg3wiMnKAf78xBpT41TEVpZy9phRqt2S2P0421GdJGU8EHBEAABPKMwKwSqfPmzXvvvfeuvx6LVl/rWcYYGea15oL0IAAC106g7zF6q5/+1XTH//yP6MQHw7naUB3wTi/95Az9JBwr0/5nqbwyUxyEgwAIgED2CMwqkfqRj3zkypUrsYtqZY/orCiJFSrDnBVNQSNAYIYT+Jck/cb5v72xXvpNphb9c5IuP5YpUjR8FxFEahQLfEAABHJGYLaJVEirnJ1KKBgEZiuBpX9ERY/koHEfVONN35eg95eLJfVflGl03kr6rThLqg7NQS1RJAiAAAhMF4FZJVKnCxLyBQEQmMsE3n8D8SdXW9mTxH81Z9dJ/cR/pLtXhutiQ3XAR8vpc3/Baei/36/W6q+lz20MJ7H7v+qh5G67BwcIgAAI5A8BiNT8ORaoCQiAAAhMBYEPFXr/FzXyR3SVZ/4niWXrJ1Pk/PJ/9AIWoq8/BSJ4gwAI5IgAFvPPEXgUCwIgAAKTJjDcS6d2088zpS+oVTHYVtofH/Ufe2hI/+NUJf1u6jX/4xPDFwRAAASmlwBE6vTyRe4gAAIgMMUE3ummv1pF7+ykN8yi/akKWGr+TepKj+r3j8Q7b8yoH3mEbo6EwgMEQAAEckoAIjWn+FE4CIAACEyUwI3ldKNaP3WonX6VNvGHymmhso++9xi9Fvz3VE538Ygxo66k/wV9/WlJIhAEQCAXBCBSc0EdZYIACIDA5AncQAm9wtRu+nFEeoay/V2zLsGbTwcU7XtJOvdHXtyP7aKloWTYBQEQAIHcE4BIzf0xQA1AAARAIAOB94Lhn1lLH1A+Q8eDAZG9m+/3zK7v7aReZ2Rq7x/Sr/S/qT5CXzSjAiKp4QECIAACOSQAkZpD+CgaBEAABMZH4B/M8NPr9GJYCVqsJkX989P0t+lzuIFKnvZiXHmE3vi1uM/vNB39hfSZXfSJ9DkgFARAAARyQwAiNTfcUSoIgAAITIDA/3jDi/zhIs+hlz7ldf6vz9TjX7iWPqXXSe2lwVo6u5v+u1kYdf4JulX9ZcAEqoKoIAACIJAlAlgnNUugUQwIgAAITJ7AP6m/m+L0NxhN+aFV9KV3qEjt6n77NLl/YRdd7lH9+0foTRPvQ4epPPK/ACYQvyAAAiCQcwKwpOb8EKACIAACIJCewAi9q4eT8rx+3d3P8W/wFGr6pDr0+gR96TDNc6Je/ziVb6TrHR84QQAEQCDPCECk5tkBQXVAAARAIETgnddIDSUlWkYLQmHj22Uzas/9NOZEfu8IvdpDv3F84AQBEACBPCMAkZpnBwTVAQEQAIEQgZ/1eB433EofCoVl2v3NCPWso57fo38OjQlI0uXfo++uo9dD/pkyRDgIgAAIZIsARGq2SKMcEAABEJgMgXfpbfO/UL+dYghpaIEqXQrL09OP0XeL6PIJU2yCil6jr7xBH054PmMn6MdFdOx+OttrjLUmLn5BAARAINcEMHEq10cA5YMACIBAGgI/O06/1MGV9EkjLn/WS7+4gRar3V/+hAa/7WXwW2rE6nAv/bdv09UjgVzf/0dUspN+R020+rdv0Nmd9KbRvtz1/yZ/EvThtVS0jpYso4V25GsgD+yAAAiAQDYJzBsbc4cpZbNolAUCIAACIJCewLv0vc/SP6oe+Q88S19Ta6Nyitf+kP7WrH7qZ1BIt/TQz6rol2ZRVS+onD71bfrCZ8PTpP7hJ3T2MXqn28/Ac62ksjP4D6oIFniAAAhkmwC6+7NNHOWBAAiAwHgJvPcOXaetp4X0O/f7qT5qTKq+F9FH26n4s/Q7RshK0Gdp4V/QV/+CVkQUKgd+7LNU0UVrXqP5ehVVk1fh01CohgV+QQAEckkAltRc0kfZIAACIJCBwHvv0l+uo/9RS191pOQ7vdR/xkn4cVpSRUsLlc8IvVhE/99GuvkP6daV9H4nVhrnb35NPz1BPz1Mv1pFlY9PeHpWmpwRBAIgAAKTJQCROllySAcCIAACWSLwa/qHG+hj4y6MF5YapzYdd5aICAIgAALZJwCRmn3mKBEEQAAEQAAEQAAEQCADAYxJzQAIwSAAAiAAAiAAAiAAAtknAJGafeYoEQRAAARAAARAAARAIAMBiNQMgBAMAiAAAiAAAiAAAiCQfQIQqdlnjhJBAARAAARAAARAAAQyEIBIzQAIwSAAAiAAAiAAAiAAAtknAJGafeYoEQRAAARAAARAAARAIAMBiNQMgBAMAiAAAiAAAiAAAiCQfQIQqdlnjhJBAARAAARAAARAAAQyEIBIzQAIwSAAAiAAAiAAAiAAAtknAJGafeYoEQRAAARAAARAAARAIAMBiNQMgBAMAiAAAiAAAiAAAiCQfQIQqdlnjhJBAARAAARAAARAAAQyEIBIzQAIwSAAAiAAAiAAAiAAAtknAJGafeYoEQRAAARAAARAAARAIAMBiNQMgBAMAiAAAiAAAiAAAiCQfQIQqdlnjhJBAARAAARAAARAAAQyEIBIzQAIwSAwowkM7itrPa9bMNha1jroNObqyTodxHGcra7zso50tXObdTvJHCfnUHfyqudxvrVsW6fsXO6sc7IzzgxZObnCCQIgAAIgAAJCACIV5wEIzEICAfmo2nf1ZHuy8YFip63z762lh7R2XN3Q3ae2Uw2rOIYrT9ltdGZZmS9JnXw8Z2l9X02ygnXqwuo2nZn/rbONpknl4xbqCmvW2d7m18TVxPtcES6ZOxo9VVns77ZXR4srKJIBQzbVcSvpVD5SH5VHigis8k3jzHuCW2R8lVLUwSaMTZWiAjZROoeT1n3ncY6CeSlycnFCuYn22KWvvBMqiSwT/51KvxQ55cAJAiAw2wiMYQMBEJh1BP6+c9u2zr/nZg20Lf/jfvn94+Wh7Y8H2Hv0xW1tAwNt214c5Zj8/fcv/rvYbwFk85Qdtfk+nM+/e1HKi990tvFhUV/OVtVZQrj+y72cOZPlulFS7eW6XeypGqLichu9CGaX22yzEr/oprLidEzAbLEFmUD7O/riHyvC7CGVbBOcQbcwd+qjw93ITgSphlcHbj7X2svOS5SiSv1cghfTAeWl4SMWRyxFBWyitI6Uh6bNHH2nSn5O0rpQi+R0spUXd+T8EU9D1WblNtPFbiPAAQIgMJsIwJI629460B4QiBIY3FeTbDzlWzbF9UByW+sgWz23udbVaNKQz8vW3MfWrYrm06ebK9jR+mMTLWgzcw1gJkbm3/n3ttWXetGK72tYfSZ5kffOP99yZlPtvfMlYGF17YN06IdsN51fva/eNKD4gcbVp9+UuGrIQXuiO5MFl42Xlcnavo5NksZs8QWZUPu7sLpeV4bopk+tpgtJPdSh/bnVDffpGqn6/OBlMx5CpbzcGRth8Dstpx+srV4ocdjCvYkO9XiDNFSq+Cpd7ew4tNpYxxWonpe9oRqpU6WogEqQ+Sv+0PBR2FatDgzRosRqSibdasTnevXlH5y2lZcmnwlWPj7VYM9ztKnGK0ua/FxP2HgenxC+IAACM5IAROqMPGyoNAhMgMAPW2uoo+3e+ar/1HZMz7/9rmTNhDtMb693pO6pxtWrlfat/5xTnVUNRg7Ha0Tprh1/uZeSp1XeV99K0oPlRo86utAp+eKbOq6o2La+Nq35nPCIk4co9FmN64WOp6BgRqK3POXEtV1VfrvSmhxn/pIEaYVtE8RHuJq8QJvu9BuXWEXJt66SDACQbu4UVbqYPLO6fIUnDmlhIkGnk5dkhIPGG58qvgK2fhNxmEPjprl6tsdT2+p1xev6l0ITN7nxwu6bEquk8npAs07FR3P1p9ImkiaPRxCHC8M+CIDATCEAkTpTjhTqCQKTJXBnfZ8yl7IZrK+vvIctn2qsJO92LG153rXYxZdwuqWS04jdlMNZ6doxhfHRz7SIcVW2ipYz8VHG7TvY+pBnLPQFqEos+i+0nW+t8a2YobAJ7GYuyGRmBk02084+bfoVXehuYlYMbCkisNx0o81PLHV3Kb5Kl5PBwljnZU71TqYaBrJIt+MfGollLOjN1KhPtnBSe1Z47yf8jrT6dPPznh1UTMXhFLyv7fR8JplTrricLegdan6enIrth2ISwQsEQGD2EHjf7GkKWgICIGAIsABtU+7ibX3WQKc9xHhoounQwR/yvhjzUmw8rUqskqzJmqUzurF8W3PnitR2Srak7tMdsjzJhlOENy60L+wXt8+6p5I7wTv6TK96XCTPj+vGGnrTs32ZradpcplgkIj+ezmNmku0tCNenE0wz0B0MfSKx4R6tC1eNe4hkN+U7UQPjZiuqzl/JdwTHWyfNj5SqLJYq9KZVUXFvgSzknekN8tqypTOfLCBZ+yJ5nZSSUO2qURSXEXrEnkTKN52qoFzKGvhgNWNDZuoR8XAFwiAwOwkAEvq7DyuaNWcJ+BP61ZGzeCXmXXOksLYqNiYl0iYfuq09OZX7yzv2eVZs9LGnHygaJ3KlsSzLFM8jS3jPp3NMUmKRqxoZmHkmTOdWEGnsfYJC0MgGEP2UhTk8AyPVWAgPDiynfvlw/bdSId4igghI2j4hSG+StLZ7W4hc2x8Q24MWaAjNeQc/enzzpx6W1L00NggdvA7TMOqQ+12YTI3TNzzq2s2kRlIKjJUb9sSPHQhsSgc29v3hyCrHPZ5idpWsK4d50mbImd4gwAI5DcBiNT8Pj6oHQhMnsAm1m19PCtIDxLtbljNVknenrXThHgwJfGgxuJtbdU8tk8K4nlIqU2ktiZs7vJspdbLcdiO3Ul3959vjYpOkXdG3HBhMmDxrtt5PObgvooWtmJGhpY6FTJOsdKZzWhfE+b/piio2B+MG992pZa4f9+ZABQaFSplxEeQ/n01D0xXIzjYlI9KfNtlHGfPWTMvS3r/N5WbCWecUXyq+Arocr1vXztGx/XGHZpAYrWTWGJGykbDYn3O9xxyxvLGRol6qvGv/jDlaAT4gAAIzHQCEKkz/Qii/iAwaQLWenq1c1dLojHR7q18GZKqgTGpmQvzJ06xIoyRvHZmT4qsApPW/Til5Tzn3TPRqSnqMmcoMFfdj3tNrtiCIjlePdlqVu4Ueqf1pK6Ft5evOt3yHd0/P/g8j0Dwp0OpLFJEKL6T7Ytii+VNhlpqxWYmTlF8lQLDOtX6AKLYfLyxqVJUINK+WI8Uh+ZyZ6sxnV492cyLMIhWVnZrPQXq6mWjpElGsroT4FQx4unNPPNTXb1qlwiQ0cbuxDKV6HJnczOZhRRiawtPEACBGU8AY1Jn/CFEA0BgkgTYfPVgeb0MqazouesUT/+nJTydvFUGFAZyDIxJDYREd8TIGvWdsI/MmHGGs/Jg0/rS4vruBh6bqPy9KpHoGNHQMkTR29h+HKq/CRnvb1xBkbTz732A+G8O9HQfNlF7plnW9x1JHmn5nCRQ1Q6lTBGhtP5UY12Fbog/qNemja9ScFinrUP6VCkqYBNlcsQdmuoHiP/XQC+tEMN//qXnyyq9OU6yHIQeZMwSnAWr2mJBXfxOWYXCyKNP+c8m9GhjHmygJ/Apz5hXoEzVRzgIgMBMIjCPF32dSfVFXUEABDIRcB7kaaKu/vf/nq58rjHRUZGscUZznm+te6u8/Ac1Mts6Ri2pDH15YcViZ90uaoz0g7NVj21gsqXKSgXiCwRAAARAAASiBCBSo0zgAwIgAAIgAAIgAAIgkGMC1+W4fBQPAiAAAiAAAiAAAiAAAhECEKkRJPAAARAAARAAARAAARDINQGI1FwfAZQPAiAAAiAAAiAAAiAQIQCRGkECDxAAARAAARAAARAAgVwTgEjN9RFA+SAAAiAAAiAAAiAAAhECEKkRJPAAARAAARAAARAAARDINQGI1FwfAZQPAiAAAiAAAiAAAiAQIQCRGkECDxAAARAAARAAARAAgVwTgEjN9RFA+SAAAiAAAiAAAiAAAhECEKkRJPAAARAAARAAARAAARDINQGI1FwfAZQPAiAAAiAAAiAAAiAQIQCRGkECDxAAARAAARAAARAAgVwTgEjN9RFA+SAAAiAAAiAAAiAAAhECEKkRJPAAARAAARAAARAAARDINQGI1FwfAZQPAiAAAiAAAiAAAiAQIQCRGkECDxAAARAAARAAARAAgVwTgEjN9RFA+SAAAiAAAiAAAiAAAhECEKkRJPAAARAAARAAARAAARDINQGI1FwfAZQPAiAAAiAAAiAAAiAQIQCRGkECDxAAARAAARAAARAAgVwTgEjN9RFA+SAAAiAAAiAAAiAAAhECEKkRJPAAARAAARAAARAAARDINQGI1FwfAZQPAiAAAiAAAiAAAiAQIQCRGkECDxAAARAAARAAARAAgVwTgEjN9RFA+SAAAiAAAiAAAiAAAhECEKkRJPAAARAAARAAARAAARDINQGI1FwfAZQPAiAAAiAAAiAAAiAQIQCRGkECDxAAARAAARAAARAAgVwTgEjN9RFA+SAAAiAAAiAAAiAAAhECEKkRJPAAARAAARAAARAAARDINQGI1FwfAZQPAiAAAiAAAiAAAiAQIQCRGkGSLY+rJ+vqTl51S4v6uKF0ubOurK7zcsDP7Fzt3OYHcT5l2zoDWZt48sv5pA4d3FfWel7FPt9aFt5aB4k4QnCr6zwZjunl4BYKNwiAAAiAAAiAAAhMhMC8sbGxicRH3KkiwLKyObmUDj13mmh1w7PlPQ+1sMvbVjWc2lc9nwZby2oOGb+439UN3W3VC4lYUHbQJjp06ExcLM6fo11qLXsoVWabOvrqi1VS1qA9d/bVl6o8f1jet017cxhX+PnEPh3taue+l2+/M/k81Udj+jnE1gWeIAACIAACIAACIDAOAu8bRxxEmQYCl1/uofLGbdX193XW7aLbS6ur+6rZAtpMjW0rXmYfs/nyUcnEZtqpVKkJVr9XOzsObaphZVlfH/AP7lwierDDEZ02lKVwj+ywhbVSCeXnyg7Rpo5niZ6rKXvORmPHpg53z3UHY2660w2DGwRAAARAAARAAAQmTAAidcLIpiTB1bM9p5fWzufe8++0JGpOvbytrMUzglaUqQIqttGpfQlxspXUtYBWlrXoGnjWVo7wfMuZ1Q07HZWpI5jvTc8qyyjvBqWkCeffTeX8tSiSbKEAACAASURBVLC6ra/at4Oebw2KWrGkShJbH9Gvhzw568hfyUHiYQMBEAABEAABEACByROASJ08u2tIOfh882l6sJYFXw119JXOp3191WwpdSypjaq7X4oore/r0xZSGSFgLKmDrduSqgKDrSJhV4tbqUzlmeLLkZJODGNJtV5vddZ1UGNNVNQaS+qDDQ1Eqru/nB5SijQof40lVYYrJBtPtd3LahwbCIAACIAACIAACEyAAETqBGBNVdSrJ9uTq0RWDv7wED13qOw5d0yqsqSuYhGot0M13PfubtaSymbMspZN39hEz55q6GiWKLa/3o3PZtJxWlJVDu3P0elVbMTlEbFkxHEwu+ieL6MlDJbUKCH4gAAIgAAIgAAITJQAROpEiU1B/Is8GrUmWfFDKt7W17dN2UcXSVe7Z0kN2B1TjUkVS+oDSkrKWFVdqWu0pMrsq0TDg5S4s3q+7dOPNFdk8XMtyWfZ9Nt66CE2t24qZ3G8ixr3JZ5XVeJGmclWxWwEjmQADxAAARAAARAAARDITAAiNTOjKY9RfG81d/QTJTu39ST2PUCUSPDU+0ptMa0oE6uo0qaXk8lViZtCetFaUlc1cMrgFrsagFkBgKMGO+WdtGpMKhtE97EdtEWGETjG0bB0Pt966MEOmdRPLEHLedJVksfXnjmtx9KycZcDVqOL34ELJwiAAAiAAAiAwCQIQKROAtpUJUkklrb0nEwkKdFYWs1962E5eCl5mhK0KMEjAxLSZc8214qeu9QQT9Wz//z5aiUW3fq4llfxH9xXp8euurrTTZDSfb617q0H9HDS081aOhPxbK3oWNVmLrStmBfM8o27KXNFAAiAAAiAAAiAAAiMhwBE6ngoTVec4vsa2itbqPHUxX1lFc/pUrQcFPPn7W8lV9/1wPyF89v6bu882dnZ0cKz+DctbS4rU0urdvfJCqnj3ETUJmv7ynvKesp5Gta+sprnfHsni+OKN2tDq1PxeNnTVE4kc54CltHArH+ZdJVoTNaU6TUJZJgsxzejYDFxapyHB9FAAARAAARAAATCBCBSw0Syv892SjaU9m0zs/u9MalXO39A5TtllSq1pD/L1lMNu5rpvra+O2VRqiSvexojUiMTrXgl//uudu5q4SLY2KkXh1JjYXVDRWWW97Wd4j+p2ufo1Mud7RcaOu5qLytLNDRGkASGDWzquLet716OA0tqBBQ8QAAEQAAEQAAEJksA/zg1WXLXmI5Hmv6QNj2XTMhfRkk/vlkn1eRbds9tt6z9T/cllQX0gaQXwe/N50n0Nc/pXbs0lVac3n9H6Yyku/8+f/1/lcoUoX/tulTe4gCbOroT7WJ2Vfl4njbJ6ob/O9Hyuv0nKi6RVyo4fTr0T1d2DVebDg4QAAEQAAEQAAEQmAgBiNSJ0EJcEAABEAABEAABEACBrBC4LiuloBAQAAEQAAEQAAEQAAEQmAABiNQJwEJUEAABEAABEAABEACB7BCASM0OZ5QCAiAAAiAAAiAAAiAwAQIQqROAhaggAAIgAAIgAAIgAALZIQCRmh3OKAUEQAAEQAAEQAAEQGACBCBSJwALUUEABEAABEAABEAABLJDACI1O5xRCgiAAAiAAAiAAAiAwAQIQKROABaiggAIgAAIgAAIgAAIZIcARGp2OKMUEAABEAABEAABEACBCRCASJ0ALEQFARAAARAAARAAARDIDgGI1OxwRikgAAIgAAIgAAIgAAITIACROgFYiAoCIAACIAACIAACIJAdAhCp2eGMUkAABEAABEAABEAABCZAACJ1ArAQFQRAAARAAARAAARAIDsEIFKzwxmlgAAIgAAIgAAIgAAITIAAROoEYCEqCIAACIAACIAACIBAdghApGaHM0oBARAAARAAARAAARCYAAGI1AnAQlQQAAEQAAEQAAEQAIHsEIBIzQ5nlAICIAACIAACIAACIDABAhCpE4CFqFkiMHSE5s2joyN+cUfX0bx1NOR7wAUCIAACIAACIDC7CUCkzu7jO/7W9YounLc7nODsbuXPQSq0RTuC32c5ESePE5Fabrb0BrJ1FafVo5xzKBqnscVtPEF0gm425bJ+5SApl0hyM/6uQ4eqKPgCgbwmoK+yaz9jdT7R6yjUeH1ZZYwmFzVfWZF7Qii3wK5K8vUjxk/tSkE6q+B16kcz0e3dwHjE/+r6h3DptN4dYB21xN0W3PdeyXqEvs5VirtxxRcMXxAAgWwTgEjNNvEpKM9KN7kjqztsQEqqJ4G+g3s3bucx4/pod+yzSopQOa94nMbOSJ2bz9DY46ryu2hszPv07vKac/RJJSKdgrwA98c8qFzFeTCpYvTQ62upcVVYpzaYgo6sJVpLb5vdO3qokWil83TpNUFcN1srt3C4QWCmEkirpVxxtnKnNJGvI/dtLSA0VVZ87USjhTQfR2hZpeLtDF+VbomceVRrqmTyxV0f67k+T9LQSv+mIXcPdUux0UKOjUWB+kv+mkDc7UXf+lh9Lt5IY8NS3PrDNHaclnKmzh3j7cOhQjLshtoY5un087gvyS5D/y7tVNt6+nI5ddMyVBHBIDAnCECkzqjDrG+d+hmTvuIrjaExfbRJhloDiUm/4bhIw95yanEtr/Po5vslhn5qHk14DypXcW5OqCzK6YWnRYM2rBTLqE7Fzyqbm6trWT3TRqVE2bbqPABMXfALAnlPwLywafWjxSVfs74Y2k3+m2cRHeMGOT0JfrR5NMTiTL2hyWVFdGQ4KAf1y5t6vZS7h8rKjdOsULGwW6Ec9otL5/sMv5pyBL5+Xfml40gmShRSUtkjdeWVrj12P339P4nnzT30KL/HnqAfjdiMMzvc6nHTXtiYOUnKGEoCppHRkjAC1saXN3MFUCgZyevqXb5Z8a3JorCvzSxG/bv0Tk/HC1L1hs+3yo2PeIOXjj5Cxzhn/f6fshkIAIE5SwAidQYd+hF6VGk+cmyZR271G+DdUvWTg+j7wU52P970uNjmumIlNbDlVT8X1be+oeuK0SPeM9hVnFaP8uNTevOr6Ajf9JXZg2/9NjdX17KZZDERF8eevbi5T8/RRK5ZIGA1kLb9294ALRylE4MvIn05O5e8e32x2xOXvaKW+M6woVAqrt9m3U4S/e7HRXDm/PonolMJZdZSfKGFhCAnF928S14aG5TV08qvGCwJesFe8ioyS94XlGLmyLoVulYxafPBy6hPCzZEI00dLzDztXQHMy+kr3GTlRxneqJQdbYKyLHjIkmTr9F69U6+mL9PiA/HFI37tNzQsIEACMQRgEiNo5KffmfblUGFH1eOMtvweOQGp2+X09mGIdVHv1QbQbkg3WPFElPZNdlgYE0Rbi3Y2sqPAf089o0l6iZun9ZjXfSnY3SHTtbjG5ZcXctmJJ0/Zxgy/7jFwQ0CM4UAyxfWNLFKRSxtrCedSz62UTLehuVmbWygeOqrj68XT3Ty1cpWT6V9QwqSlZO8Otr7zEqSV002Nzqja0LFsAJ2BXEg1N4ctKnVXLx+HMeo7L+yporsJxufKyn0Pm/vVONLZGPZgRMiOo3BVVdSx1lqhCnvWsGqb4/Nj6kDulLeCrQkTdxKx9SdUyLw4VZGB771hfjrnPENAiCgCECk5vREOHiQFi6UDzsybvIk4w648kwRR+i7/H5P5IvItCm8G7EZf6Z7Em1fFT+x5GGmuvxipaeEFYopRe7FvI3QUzuJ+/v8QVfa31h3dM+mHXZ2VN21JYp6VgV6FcsDRllr52CHNnXwo9GW4naV6iJMsfgFgWwQmNC1HKiQvmDj+sS1pY314oqI1NPXqScNg2bUQObujs5EXc5s7JQLdmd4XhS/YfoKVcvH3Wq4J79MKpVmr1C5hPU4hKTccGTgqVtW0O29hZpOnmCg7MlAUmuO1Q71+hqIybVV4lXfnfQl71/sXFtVH775pJ/sZQeGevU36lNnbm8pXLR9eRZWxuDqdvez9OcgfTfjWvWqTh59o7a3XxGybEYdEaNys2oC15lj/ohfP5StWoKxgQAIxBO4Lt4bvtkh8I1v0JUr8mHHtW+e3NRPDtPxlyZbmWpgHwz6keD2KqobrsQxxk7bC6ZNBQnVsRjOnwWriu91KTrBnFWoW5NL31Aucx1eT5KYgvhuHhy7xjJUPzkC33ocqnq089CuO9hAq0rk55xrpoWR1WEP57QTmPS1PNSjekiU1gm8B9rhPVx39R5or1bRTLytpc0r5VebUaUr2VgltbXPGgJZeIkyKyJSWpBlFis570XUKD8e6v3XqpdflFnUcKtmPnG53O8/LGX6AzEpQU8pU+vB1OOLArcmlXxiX3HNt6Mj5DbC9yKuoRLBondN/cN9PrZUozgtUnbou4eNMh6HHrlrY6YbFKEi2ZmgtFs6+tlAbm9xKU3RNnc4QGAuEoBInTlHnXuLeGvsGUeNTVedDH7i7bWwkUMPjZLnVoouPDGgxq0JpcvWpgK+I1szqPb3vlfK7Z4fddyfFdiUkZXNQosjy6DyI5Nv2dxBtiIqfIOPEz07hLPVj3bdp6YfRZPu1AtUEjsgkF0CB7lvXZ3kfG67VkA+w1lTenrUqZKelCNSTL1GetZWHcFMonfHgmsNp+XRUyTXNUtYf7yN6QPhkZFfUG+tPA411SaZHCfWuqGN3z+5nqxErZ01FCGjJVUabrr4PYfu21EZsRZkT9fG6eevzcP6xdX39VxJdYfiF+YfRYLG42FVvgh6Y3D1u/t7vZG7WumKxj1BVqlfMDdHGQZAFHilVwnlDsljUkkmjPLxSm+KHk9tEQcEZiMBiNScHtVvfYsWLJAPOzJuK8pVFDNXVMc/utsXoH6XmTEkUELslO6tU56IkxukxSNEd5M8pcrVFA1V/B1qbkfUZskdW/yoW1xIAUuGGh/GPYz6Lq/7yM4W0udVVixe45+O5tmgH10yOFVtPzouP3erB6ouRbt1KL5BIMsEJnQt27qxIY0FkJ46w33HrFPtuFJWfrbvwu+hNtPGrar78yQ1H1aXuc00zqF1Hl96vbqjo11FUpZXqcDwtY6M3Mx1iCwRYCuSzpJqhLVr1LRuS8BmldnBqw2sUx0sT9N3efqX2hJKf49/9Ke+pVgpL68K5m3ZdvfrOPqFn8O1RYA7he7g5UesNaHXm0TlDjiWtb3U7U5yuFWGrtqpVJISGwiAgE8AItVnkQPX5s10+bJ82JF5UxZKjmafT6zbNr6WNp2ZRBUwCZhewrQp/cCzbNHhey55nWhyh+VHKZsN1MZP2ZiOKtPtKCPG7MAD8zTSd3n9AODBdq+rfFJODTHPBv3c8iypehgfj9XjtMZA62pl/UhOZdfRNcc3CEwhgYldy7rgHtWB4EydYZ0aK6S0HVRfAq5gYp+H+IVQv76mbYy3VgCvBqBvI7qXX6klziS20LT5hQNdSR0OcwZ3clkh3ak7bc4qg6iMdnAso9IVnsJEGi2CfXTvyrHX6CllY9ZzzvRSIRzK94TAaIrYLIyn7iwKmD9NkP1drIYq6Zn77Klfm79WTtpfxvuybZgJc/P1JCqVkqvB91L/dqe6uUStppg5pxLhCwTmLIH3zdmWz8iGy5Om3Lvx6QasXycv4mmmLPBjL7FbdUvpBKz51B3ca7+yU/os+MbKstLZ+JbKxkp+tMjGzw814JVH/fOYKr1xZ1bjrbT0SWUwYCsvr0ezUY0P00m8WPLDTyO/p0yNwOOIduMFs5JPqs4vZSK1/rqXzd9l162kFzrQc8hadJWU8dgb3qBWe8FNPwANO3lIQE0NzGq9zCUshZpBQZOrAPeE6OtX+mrMpo2LgYE3ajipCQ/8SjQ97lZNLeIlnDbeT2fHZC2nYzvpbC1d4Og76WgtdwjJZktUe8QTp9xNbi/Hpeuc74e86UER/CbMf/yhN9adrF95WVnZQvc9HcN+63fgFKpRt1HiqqZxQTebmvAwWf2q/MKwd6vkWGxgtn1EXEl+b+eOfh1NplKZ5FxVXXNbCzhAAASYwBg2EIgSePswa8yx5jOBkGYao7Vjbys/HYHjSLQ/HVtPY73sf0Z2U32ODHu56bSyOywJ2dG7y0ulS7QRjqz1S9SJxWeXONnBJcquLloHqwx1BUKV1+H4BoG8IKCulNAp6l5T9mKRi06d8Ppi0ef2+sPBRqjTnj0lcuxnlx8UThvMKbCnL2dduhNgL09dJcnQue68W4T2iaT1a6juJPrC143V2QoTVa6fbSQTpy6m6GCcwG3BuSnptrv3MTcrvzJ8Rzo85oLSSY6Y25S9DbrJ4QYBEJgGAvM4T4h1EMh7Ao4FiO0Q1jKR9/VGBUEABEAABEAABCZHACJ1ctyQCgRAAARAAARAAARAYBoJYOLUNMJF1iAAAiAAAiAAAiAAApMjAJE6OW5IBQIgAAIgAAIgAAIgMI0EIFKnES6yBgEQAAEQAAEQAAEQmBwBiNTJcUMqEAABEAABEAABEACBaSQAkTqNcJE1CIAACIAACIAACIDA5AhApE6OG1KBAAiAAAiAAAiAAAhMIwGI1GmEi6xBAARAAARAAARAAAQmRwAidXLckAoEQAAEQAAEQAAEQGAaCUCkTiNcZA0CIAACIDB7CfA/4c2jrx/xGzh0hObNo6Mjvg9cIAAC10AAIvUa4OUw6dF1470Vckx7D2V3S29Mrc/uHkdu6nY8bx0NxWRA1Cs5SObKwW73YyvgJU2fVWz+Qc+WYP5uWV41dHxbq2Dy0J77XNFg3QylUarCZ0PJeFflH25dNBp8QGCcBOzlYy40uTaNm/PQZ37MqZgpf32S6xObz1h9ybvnuVuKPuEDPinyH++NSLdrdziXQDV2e60L1GoeSWP1HSPFVe9egNJMXYpK4gVx6Zahcy3H3kZi9GWKyruNsQ25+X7x3ljk3QA1an3XdQ+B28bYe7KbOdwgMIcJQKTOxIM/Qt89IfVOFIZrH7gPmvvysftFPnLQxhPU+KSvMu2NdeVOycfeWPkGGnOnLqTPc6QTfnK3bFau60llvpLGxpzPGTdWZneg/nHPJF2xBrcIx927K1DE2R7ZXZqIf8jFtJFow3F6+7CkOjJMY6byZ9vpGNFKw1OCU2wWaYih628Vht9Y5+GtY8bWLUWZ8J55BPxDHzrJV9H6w+ryOU6LVbO+z9emc9Hdrc7w70deNb13UatxnWxdDdc7Rs2W1lp621w7vieHsowrkhOey73ZyUd0VegSSH0j4tS6jbEKTNShymrF495V1nyGxh5XNdvl3z1ClzM5Qd5NxlyhKqV8DSWJdvqv5eLFTFZJW340Invha9nJU1/4Eml8ldcx9bc0RMH07x5q94VyemonNa7y76jSUoPd3mHcrOAGARBwCECkOjDy3Om/9+tHCMum0CNkHh1MeBqLn0Zjj8kzhoUpb3yX1K/4+sFjdRIHcUz9MBBZNuYl1yj8ElVBjco3VOhZZZm4uYce5ceneRLo5Bm+I49A+zS193F5dppHqfsIyZCzCZYH/C7awFK+kF4IPRi0v668NX6oB6c859bSHYXqgaey4icQl37kMfqRMjn7VhB++BHxOwD78MOY9SXLfV15rjmLfs1Z+5tKGbE7Qo/er6TwMK3faSzcvV4OUmdss5fA4o2eUjmy1mukXLDq82jSnAwc0kt80fEZtcKoT/0+yZezdxLq15teucyP8XnLr4hKt+mTUF8yn+eXtPTbCL3OEW5VspgLMrcXfUOQWhkt2PyYxPFvCyZm6J6gL4f0ZaYLVY2NVbcZU2k+ckmquolDXaScUF7Cd5O+ltffSkNKs7KitZezd4dMV0YgTFS4KaXF3BlCltSjRC8oelz6jwKpsQMCIDAeAhCp46GUH3E886F+YBjp5r+Uqydcw0r60XHRWGKG4ScWCyBtFDTqUz8LVwRbxDduflhubA/66r0UBXG59vmqI2pbwgTUVSTnFzbGVSDOT5sb0z/G+BEiD/hy0Y5W/kpC9dDq1WYbJV594webr0bE8rF+nWfH4sLFEEvEqmLDStpg7CUednUstOmLySdfk5h3r1Tf1uKlMmQv/cgX2a2lfFKMVWILVybq11lh8OOf67aLOCtss5+AekFicanPH31J6vcZ1qD69ebok4Lh7gR9/UmxeuoT1b7CyUmoTmOJxldTedjSKbcCc0KKi28J8+Si8DdVB620jtQao+Mu763V71rRl8yYd2aO80bklzJVLkdQespSVYyOi9DUxAJw1C3R3iHt/Yqv5RcepxX6PTCFJXU8VWa8zYflBstHsMHcGfybiSpd7ocr5cBxxe4YT6aIAwIgECAAkRrAMQN2RMfwFjFD8m1a+ohVB5zVWNK3xaaadnl6HTwuN9MkD2bd7fXEaauDtoKIwVU9A3xLgNMHrQdf6scA21Hi1aF+4DnGXSsNJ4rVGorkgWpaOjE7h7JT8pN7c0JE57HjNKTMM2LpVPKRWx3biqOP0LFdxHKZmyklKoOrZzrSdlY76C3SqsSt4qW7Yn3BqsSoZ9BlxaBKv8CSNCGPt6Q6ZGzHYnMXC5RGlhpaPUcyh8csIyBnmmqStsRr1bXyNa8LXjSrso/yNbu4h46pF5uD6oSUdxh1MusxIfwyxhcv2ziHetT7j3rbaWS37ovfRVr+anr8jiqvSXZzehi0nNLCd0W5jWEcwXzYN8ONyKSbxK90ZZiXQy+5HmvkCEorPdnx1DqJlbyq4vb4llGN1Ps2dzPvWja7Xv6T+uGhQQ0GlJetvmm4Q6fUTYNlMd48J8UYiUCAu5iw5Y5AR8fYggXyYcd4tiNrx4jk0xuM3btLPI8Mj7192IvAu+t3ja2nsebD8r1eJTxyRtwcTbZhcdOusbEzkmT9YS9HnYMXR/lpn+YzY29zQi5CJ1w79rZOYfNRDo4mm3JLnk7mzarmXFbsR5doy9J5SxJTkFsx3d7YfNhT6qDK9SKsHTui+Hh1U1l7Bf1f4cqEwOpq8LeQVzXRrfCyclqnY9oDxEW7LQrh1bu6DhzTgnKx26LhmBEEJnot20Z554w+z/mMCp7w+hzm801H0+fn2+pC1ueYey3wiWRPql7nEuDk2p+T8wnM0dxUugj+/s/qMrG73kmuL3DnsuVM7Hkeul7sjYhbZ2tiMww4VDPdOFwrubh2eQn5WtC5eU127myBfFTF5ArSm2q1V3PjJ7XlG53Z7K6+lkO5uZdtKMjfNcfIv9GZzGN/uZnuofHzUZUP1TY2B3iCwFwlAJGa0yPP8lTfsNiRcYt9rrj3O3tb57uefYroCEfsLd7cXnUEe3/k+zUnt3dt++zRPnbXVlJXRpIHRapbH3lyODJOsjKl23zYEX2wubWySfTzTD9C/NLdjCJuN+dIYMBDaOi6OY92D92wxPQjmGe21MRpHcdxn7g6LXPTnvYhGtr1KhHU9JI2DpQXGT95SWBC1zK3QJ+ccqwd/dSrXinZ015x3olnzjp9XvnfOq0OVeeMPQn1RaR3+VzVDs6WL0M+G6X0tWPNa9ULkj29OZplq/N06mZD/JorjeVXxuzqi9TGF4e+rOJy00G6tnKL2OVrU12QRRHIMNVO5Pr1qucULUjVri6Oc2KH1NnBGMg+TeVVkjQCVFdeSjRvrVIoH6ngrSNQHHZAAAR8AujunznWdJ4GxL11emSVnWahu73sNNjFziQJPdaNe/fYsUFN1GC3nvrgNZp7w83wRx5nxv193mizMdVFqLrvuZ+at+jECOk3P0yv86zVywGC3pgwNRY2EDCRnSno7ufi1GBQro/0Y0aGIkgnoOry43666LCE6Bwyv/qF9BQPRDscGWFmBhjoGdN6aNpTR7x0MqlFbborMzSXRXp+19JTPMZglZl3dYIORmZwe1ngZxYQMCOVpSnOUMuV98uZcGSXXHEyukb1+Ms1q/rl5drnASHq4tJXtx6TqmesH3laBlLrE2z9WpIef/JGqNtZgJytDKEx29Jb1UgYZ4zQo3a4jp4U5dRN95tzrcZzI+ISpAdcdXab0vzfNBP/OZIeKsOLaZiLxk8oedqeejXmIXzx2tVFXEpm8K6fketSs9NkAK5qMs+P5G1ylfenmpkBxJKXGXehb0T+HDUJwwYCIJCeAERqej7THPqtb9GCBfJhR8aNFaQdXhZSjXp0KefAg59YidpNTx7iQW88/lLca0VW6rGYG/hebIZ7BgZvqaeU3PrVc9FOCGA1HNLHDTz/gKXtQluaODx9qZ9wgZBx7ehHrL3XS1vM/Cot+zLnovQoD9fTY/50fc6asXfuOgbygFfzmj3JqGjocbfpS5GJFxtFNwQUpx57qqdI84FQbwusTReXy9hTFiI6Z1lwIDjeTo8pFIWhKqPnaS3lIxV9RKevFkJzSmBC13JguQkjaLzT/jhtqKX1u+R8kHGfLEyf9N6jLvDAcXOC+W01epdlFl+2ovDW0qM8THMnHe2VtersCHV9Kbn3hzu4oBP0qBod+7XywCIYOpr/MqxfO9WMzPHciPzqjdPFY0l3q5fkcm9BEk53h5qNtMJ5wxSFbXWzGp1vR/TyJS/TIoMi24ZahR2tjlzF6sWAg+R9fqU/aTIaOb2PP9XMDE7l+DxWmAcf8wxO2dRdwnMrD3yBAAikJXBd2lAETjOBzZvp8mX5sGNCm//wUHNIrSU1lAnPtODbLotLVjzsZpPM14Lqhw2NOi1nKI8lnppwbUZQz5KqajX+2fq22tqIInPe026uwTgcUT0GeKUCeaKbmRZW3Icjq31eO/YCO5Qa1jH1wyblVC3z1JQI1hq9UgE0YlQv0SpPo0Jhzpt+r5CnrF79SvxEJfNCVPJoNE2+oLQpVz5kbdXR8Z23BCZxLbOoCs3e0yZGead6XKQSW92a19HdT8tLEVtV+eRx9Y1E5kmQSgPps5ej8ZnDqnSFelnduMqz0DM0fWWF6amTk2dlcXK2ttqNV13lsvi0TH/hcPxx3ohszlGHvlK4OG0V1rqcbcl645q0JL314/SdimvlQdjltQAAIABJREFUzZpy1tZgH3sFeVUKWlJj7pB64a2d3tp8LIg5jn6fj1ZynD727ZrrY1+q3TUWvOUaTP+VZDu59bbGWSFEA4EZT+B9M74FaAATCD2B2HwoGy+dyN/cgWjd2l9NQpcIU7spa2Vslr7eUtbK2DjiqfvF9PpZkUjabKm9tUgVW6N7u1dhOho/y9ne06DUJDefHx72GeZm7D3g+T8O2FdJSc6QHzChjcWErH5AdPNu9ShN0VIucek6EaN6s4XyLGBaZ+xDwfn7LWxyZh+WILypgQQ3r1KVYXkdaZrOFt+zgwB3KMtZxws+jDmmu3KRSnwKsRRjxck9FXxReEvrc1T9RjSikumefbabsrlRnz/srYSX2ETZWs/nM5+0alkAPvlFvPJCAV5S74fX/dUnto3GAbpiugJ+9GBHge8fdIVuRJztzeZykIhsBFU9CTYRX1l8mntXnGlpL18vpk+fq914q0yNZ7UqVVWjYmzycTlMtpyWm+9dyyeopVz+neTzZ/x594tZp/Idpcf4ZKp8tHR+ubWHwgtVAzb4vZTlvi6aX+NF+qvFPfhX3690/0k0Q/iAAAj4w1PhmhEE9Bh8bzKBHumv5yuYqTY8MJ9nIXC0wGQdO2+AB+yvHfu2GsjvTSkw0x3Cu5Vj96QKcvyPDJhVAoL4ZH6A/jgVi50PpKdH6IkLMnHETtRVExo4iZ6bL7mZrLiodLM3uLHBORAaWriBeq6YyjNVBF3oY+68CtuuoMNO9gpiwB4IxBDQVwdfxXaeE59p3kXN0dWsmsea1BWkzk877UnnZS8ue7Hoy6GZp0PZKUH69FZnqZ7prxf34IL4WrOXjzu/6ttP+yXqgmw0fSH406rMBP80N6KYZhsv3ZzQJSONMhe4i0Wi8WoGfMsyoV426ecemSlNpkzvl0vx50gFL2Fpo/qEKhbKIVB5U4r2lJzNpn30IeYMA6lUHP+eY2/OJi1+QQAEDIF57IBSBwEQAAEQmJEExBjpmCfZfn+hSC24a/5YVSyjbJjH+rvZOrye0ZeLA/ZsMUc5s5cAROrsPbZoGQiAAAiAAAiAAAjMWAKYODVjDx0qDgIgAAIgAAIgAAKzlwBE6uw9tmgZCIAACIAACIAACMxYAhCpM/bQoeIgAAIgAAIgAAIgMHsJQKTO3mOLloEACIAACIAACIDAjCUAkTpjDx0qDgIgAAIgAAIgAAKzlwBE6uw9tmgZCIAACIAACIAACMxYAhCpM/bQoeIgAAIgAAIgAAIgMHsJQKTO3mOLloEACIAACIAACIDAjCUAkTozDx3/qcm8eXTU/It3oBG9EnTW9VJ/YT/P/B22F6I8v36Eho4Qf7sb+3AOLfw/1mrTZQUyNLHPmjjioUtZR0MmNOZX1S1lzXUCHSdU20he/Ec7Xj6xrSP5s2+OYD+6jWnaEikBHiAAAiAAAiAAAjkkAJGaQ/iTLnqEvntCEicKY7I42yOeK9OLRSfdj47TsfvDOtUP12WtJVLK1Wo+7Vj5pJGkrBSL6BgnO0E3O9JQopmaiKxc5WW8sciXjzorK7h1/Y/USkytRM8aPe0lVj/f57+CXEt3MIGklLs+4QYaN/8t4Zh8jnD9eeuljcxtF60w4fgFARAAARAAARDIVwIQqfl6ZKL14v/g9jSiloOsRK2PcbD5c8Xj1LuL1t9KQ7F21ki+G45LfNmUCdMaUHXEs+1KAq6jFRsDgq9Xib8x/f/gnNBUif86XOvCsTM6A2p+jBYTceXtP4yvP2zijFGzjrWLNhjB7avPEXqKlShrykL62lpR0r41t5caOaEWxEr4cqgHR6GwMdl0au3EWv7STj9mqLFejfEDAiAAAiAAAiCQewIQqbk/BuOtQYPWhVr8raW39W7wu2Gl5MY69YXHRdtl3LS2Y/nIjqPJmOgiGYke3RgT5HmxQmWZuMtTur6JVGlH1rK6Sl7lx+jtw1KWFZSsNUXvPu5lxiMN2Gf9OtG1Rx8RfaxNqhsekwgrzRiAo0+KGdUjoIC4wpdVcoyt9LhSyTrVMK3nUg57dfPKxg8IgAAIgAAIgEAeEYBIzaODMa6qtCjxF9Orroao6v5xloBiI9SDO9myqM2cjgXxWe55j9g+N0R6zLVkzFCtlcosypq4PBIx0rHO9tSb7/eirddd8Cw9nRG0B00oN4S75llHehbWlaJu2QgqZtERumCEbKTIlB7H1AAJ5iZDZtUIgc9H2psyMQJAAARAAARAAASyTQAiNdvEA+UdPEgLF8qHHePZuPNaurm19dGxoXr99cqGavvZSctHjqYMh2zs9Drix+ihx8XdzBmpYZ3RuVNSxlV61EhG2U2xWVmsx5s2n1Gl6BIdWfyw6oXnynsRxuiF4159uBp63ML/+YTXOi6KLbisYl2bq1a3x47TUCE1HKcXjHF3SBmAMyrO9buoWcni5AjpJEshUlMcU3iDAAiAAAiAQB4QgEjN6UH4xjfoyhX5sCPjpo2LOlpoNKod7pkxEzfCUmPLZPsly0E7jtON47n1DHolNGXukZGVbLL9fonpdldq+PVVJMsIFNILjoZmQfzMmDceoJEjqHzst5Xddb8ropk74nnj4QGsYrWMlm59q7NZpKp5/Ta5Fq/hbM3AAJWZ+kpQw9OS+Xd7iOeKeZOu/GC4QAAEQAAEQAAE8ooARGpeHY60lWHjIg/f1BPVvXlLRghaS2raDOICT9DB3WK/5AzD4zjn09cOmzlVjugMVaChjB61ojMyrkBLSVf+6prrCrturtzicupVY0/jKur78YhbaxL2xKsK9OdsMRYzyNVPxq5CenSXyHEZSKCGvQZCsQMCIAACIAACIJBHBCBSc3owvvUtWrBAPuzIuLFx0erI8VhSuRM//ez1xK1SZuNO6YK3ObvV2GC61F3PsNvRr2L4dIciaPPnWpkFZTddc236dd0SoZBWuF3wI/Q6e94aSG7z0Q49uYrFLkvnjY+Y9bBUGK9aMFYra3WxKv3uOm94gB04m24qWKgM7IIACIAACIAACOSAAERqDqD7RW7eTJcvy4cdE9q0DdIaFKOWVO7+vvk4bVaT/VPlvFgpQj3JnccSfD0pFko9GT9VkjT+erws5xard21C13rqum0E69CrX+nZ/doztBgql8g2Ua2wN3BXPq9IZdZk1fElh7V0RFlPZcaVXohAhT3Fu9hAAARAAARAAATyl8D78rdqqNn4CSRf8+PqWUGyQpNexNQPCbhYlWpzJhsaj5YTvUbHXqOhjenMloH0wR2ets9jBlih2vlMEq4m0YdMoWw9tZvrtp6eo1dVz66fqlfst5GM3OQufm/6Pxt0h+UPBfivBFj7slBmQzI3UEdgNb6S171SyVnU3t0ju1+nYG1t5nCAAAiAAAiAAAjkngBEau6PwTXUwP7PE+eh/35JjezkefFPZVSor8mEJ+6IZ33Ji5vyxnpO7+qZTHcHrbBahtq6evpyLb26jm7jRQAcTWzlr0Rm/+DwUK0gbT7sCMQ3AbLSFi9HwGmNHuUQ3UfP6lMmS+lQE19+1cADyW0erX+a6BExsmoJK8NYa0XCPqqHTPCCVgnJhNW5/RMBNye4QQAEQAAEQAAEck1g3hj38GIDARAAARAAARAAARAAgXwigDGp+XQ0UBcQAAEQAAEQAAEQAAFFACIVJwIIgAAIgAAIgAAIgEDeEYBIzbtDggqBAAiAAAiAAAiAAAhApOIcAAEQAAEQAAEQAAEQyDsCEKl5d0hQIRAAARAAARAAARAAAYhUnAMgAAIgAAIgAAIgAAJ5RwAiNe8OCSoEAiAAAiAAAiAAAiAAkYpzAARAAARAAARAAARAIO8IQKTm3SFBhUAABEAABEAABEAABCBScQ6AAAiAAAiAAAiAAAjkHQGI1Lw7JKgQCIAACIAACIAACIAARCrOARAAARAAARAAARAAgbwjAJGad4cEFQIBEAABEAABEAABEIBIxTkAAiAAAiAAAiAAAiCQdwQgUvPukKBCIAACIAACIAACIAACEKk4B0AABEAABEAABEAABPKOAERq3h0SVAgEQAAEQAAEQAAEQAAiFecACIAACIAACIAACIBA3hGASM27Q4IKgQAIgAAIgAAIgAAIQKTiHAABEAABEAABEAABEMg7AhCpeXdIUCEQAAEQAAEQAAEQAAGIVJwDIAACIAACIAACIAACeUcAIjXvDgkqBAIgAAIgAAIgAAIgAJGKcwAEQAAEQAAEQAAEQCDvCECk5t0hQYVAAARAAARAAARAAAQgUnEOgAAIgAAIgAAIgAAI5B0BiNS8OySoEAiAAAiAAAiAAAiAAEQqzgEQAAEQAAEQAAEQAIG8IwCRmneHBBUCARAAARAAARAAARCASMU5AAIgAAIgAAIgAAIgkHcEIFLz7pCgQiAAAiAAAiAAAiAAAhCpOAdAAARAAARAAARAAATyjsD7rrFGP/3pT68xByQHARAAARAAARAAARCYTQQ+/elPX3tzrlWkcg0WLVp07fWY9TlcunQJoGb9UUYDQQAEQAAEQAAEWPNMCQR0908JRmQCAiAAAiAAAiAAAiAwlQQgUqeSJvICARAAARAAARAAARCYEgIQqVOCEZmAAAiAAAiAAAiAAAhMJQGI1KmkibxAAARAAARAAARAAASmhABE6pRgRCYgAAIgAAIgAAIgAAJTSQAidSppIi8QAAEQAAEQAAEQAIEpIQCROiUYkQkIgAAIgAAIgAAIgMBUEoBInUqa05bX6Et76vacGpX8lfOlQfboGJi28pAxCIAACIAACIAACOSWwBQs5h/bgNFTe/acK9uxY00BDXTUdYxU7thRUeDEZKm1p2/5jh1FXXXtMVqrpLatptiJPoudgx1131usQPmNHDhY13G+pKatpkTR8wB176nrpoLSEhWvoLCgq2PPS8GEgnqgtKZts46jIur87xna0041OxZ37Rmqalt+LuaImMhxh0PXzD0oUkPiggr5OA7d4x4sObJdRX4d5EzoLlRt0dn435LJcFWwCSq5UuN+POtSTXNShcvyInKT20dMvpHTT0JjTjlJG0Kn6xLyVGWY5peo1jnV5ciVo4ykSo6dv6loZKrk+8MFAiAAAiAAAiCQisB0iVQqrao617HnYEENKYOfEli2EiW1O6ruqepr39MhkqtAPbxFTNDc0aaGBQucgtGu9lMlQRFvgomlapsynypNz0KfldP5gSEqqardUVPAup+5dXkid/Aci6+S5a46IipeXtLeNTBcyDme6+6iyh0lg10dHK3IfWcgUtKtoHJHW1sNx8wgqgY7Os6zXCatzgbaOwasJhsd6GPf0Y66Oi2ybUPG6ShYs6NtjRc3TnO72aiyCpZL09xtdHiECqhvT12X9TWnHzdwRxH76lNON1MLaCVIOSQqYc9zW2xGJUrod6mGs7/kU3NJS+2SAX7vWsSV4cCBjoMDgVcFm4FyONLWpyTC97wK9mSx1sjs49VWHWv1EiI6WA5linMmWBj2QAAEQAAEQGBmEpgukVpQULKmtqpvT4foIZaeJOYr46DlxSyvlBphTcAPZtYB3cq41a70gH0oz0ymE6p1QXFNVWnHaOmIGCC16PPSs0SrK7j1fx597W88D6O0eHe0vU4bA0vuqhopGGV5RDtq6XviN6AZemlKyksH2HegW7IeYNTDAy8VOdE0apZD+ugErNeFooGjm4rMRscdyl67ZkfNUF2HtekOdHeNeoeP49XVeS0S0co5sUasurTHk2Jezl2+mNTijE+JiGlZpPmePm2ZtzWSsnjHwSIatIIGzo0WsJHes9yL0g0Y8gdtBnGO4qqqggFlG5YixSTMdmc2QrdVjbIturampIBK2tYYSyobkus6Rktqaod0KwRYwZrayqGBosKXDtZ1adFpypGmchuXn9vTPaqrykVodHTKwXK+Y88pPpztXWx7bVszwuK1e2DN5pKBg76ZfMcO2sNpi1wbtikGvyAAAiAAAiAwKwhMl0j1LXMVBWw3qtMiifUTP6Tb2NRn7H8+RM+kJEamc77vXHCVbBbjJfkWRFJGNWNj+99dgx/HE9UVMDnfRnvahwrOd3WMigo04kxrrOXVm6s+6Mvfgqp7qK9dRxuRfO7h8RgsYUVZ1joKdeQSy7+whVIqqXIVGeqPKJB6claik3eUjA5zHKU72ZSuVCmLLdXdr8YYSBbWMmhUoGSl3CpwtGBxCecguRmNrAulgqHR0YFuLeY4Ql+B214Vp5DNw4MdLF2lUdYwydl6QlbJZylFV1GVp6y+2kXKyMovVyz/XqocEQnM6vo8p6o6V7dnoKBEHScvrvrx7b5i7zZbQUWNGIOLrUk4aJkelPNbqupZonlvlIU1v83JoAjd2HMDf7/cZMfAFhXydaGGRjArtRWsqSrt6vjeS6PFcgSxgQAIgAAIgMDsIzBNInX0pe/xoEB+SLOlSZ71RjyJwGKbWsGdD9fWFrIUKKi1SDlIjG2yzaGnrgBhw6bwKWV7aLQP14ug5JLiU1rCOmVkeHR0uH3PpSrpU2altINGBzvYxldVUSDijAd63jPE3EvuYfNbHY/9bZOxv1TFwovNc7xdGqHRUe4ULxPUA+e4776STYRciGvPdY6I1+M8+lK7HM2AxuNdvbHw49Ed99TUnGPzuR6u6ve3m0ju78gQq8lIZ31BwZoaMRN2dQ16mtCxzoryq9ENrC1h/wJuVx0XZgeA8okndmJvE1Fa0KUtqUJgxA1gcae63YPd/V6MgT7aUVPKgrhEQTun6Cwu9JIIA+LOgToqqawa0QZd5VVQ+XDZuWeEkViFOYZv+1Th6qu4pqa0rsMzeLMwlXHbjIJK1UCNgpKygi4G99sVVSXdHcpAW1JTOdC+h82qAT1auKiAzg9xk+bQ5eJDhAsEQAAEQGD2E5gmkSq6ieWRdOWrbTTcJ8sP1s+J8WmQhwMUFogFyzMczjFLqmeGZKkxOlpQVkpd3e0vlVoTomCpqiwYOFdWs7yvw5uIxkJyYORSV/v5UT0qVA1TldlLO8SYN/oS2zJ5K1ZjWcXRpoxzMtZiTTGtqRh46eC5vvPnBpazHU916Ita1YY91jt6RKgoY7+LXIZpanlnDYeBCJ4sNpPklEjsqNsjYpqP+x6pDRskxduVU6OnusSLT4xLomgllt1sNZRPyWbXTGkisZjdXDMw+FIVTyDjAaCVxp8KCtjEqjcxmCoXlyK/bvk6RuRbZDqPK2grOb9nj5y9A13d/D0qNNgkLPbdHW0VgtkbfsCvYd3KQFugvOi35Y1B3jb43KbFfOy6OzoG29io7G+jLznDAPToVT/QcfG5IUeU68CHg0egFnTrC0oXRwVFDG1klNs6jmY52cIJAiAAAiAAAjODwDSJVNN4/TxVKsfOjtJ6R40HGCkp5ZhaoDh2uzn50C0oLlljOoiVztMMVUfwaFeHSCXpRmeba1URjZ4fEOPmZmXgG+wS0x1Pmiou4X5jmbdEfQOja7TZTRSkelXgYawi1MTCt1xGkapOf9aRMZsrW2OCWaKJrjUb23SNU03zkhI9S+oAa7uY7n6OzjZZPS5TDJwddQdlbIBscqo4rWefwLwlOZ/cs6OkeM3ocF8XWxxJN6Wg4J6ysu919bG6r6wqGKZaZUmV0REyKtrWOnV3v9XhFSxGRR06qyUoeepJRq6vZDJUGdCfqg3mSw5oyRpWtBzVR6QGV7ivZN1dL42qTPjNgUpK9BEs9ccDe0NRGVS3vNIUymoJMkTVFINfEAABEAABEJidBKZZpAo0rwe2Sz1ZjXGIH9vS27yYugYKygqL12irqpqhYrtuZyfxtK1SqkjFKKisUjLEE03KwOxNHBo4yDF4DCl3ZO/hef0Fak5/jR7Zyd3xampOXftLJap3WLTa+a5CVmkF0pVfqLqUl5fKJCo1LNKrDo8foGIj/0alH16NBIivrJqxVFBVauLHxDrXUUfL29p28OE/pYM9u6BUntUd21e5njK3qaattmPP9/pEZ7NB3RqAJVFII3rFiIZVOYh1WSndtjZv0QMOKSkueel7ephBQSHxSFlRe/IaZHIePc9SVdQe44129ysfkfn+FlbJIihHLg3JIeDVs8SS6kveCBExr6oREtJe/dqguuk9C6ga+1vCswzZKD5w3n9P85dokIUUuLYlpEay+rWCCwRAAARAAARmO4FpFKnSS8vP6Lo9rHiqKgvZ3CWmPG1b1TNFioaG2MjHRiOxn1GNjE8dYetUh7PK5mznz/N79BJd0su/hqfmhHq2HZGjLalhIFel71gpWiXplHlVRBjP9JG+adZFJbU899yYUXfw7CjT3ewtHaUHQfIoVdNtLO8PeiRAuDDZZxkn609V1gYGSBb5lj+JdF5sqCltfd45IBFlK67ZUazaqXfTfivDsCcxidZIz7veosK6oGR5ESs/6Q8f1WZmiaks0/xe5CUL/xSIAdV6xqlkPlc5nC3ZGpe1vJpEzEdU6aj08tcUR4I5WYVatUqNNlXXg3or27yDp2tpOcvGcm+RYNMFIST1SFbvEhKPAW5UQZWypZuy8QsCIAACIAACs4jANIlUX1vxUEgRRiwo1LOfRcaeur6qLWXcK11StJxKR6oWneMlh2oq+zraWc2WVN1T1tWuH/CzCHPKpnBfuUgu6cP1VEsgqkyoUnPExcKnxqTygkRdi9RCTns6WKNU/ctQF/8UDXBqsaGaXmB+Q9jBSeqGeAmqHunu1wt86slpLBJ5to4cI72c55p7SnhC1UujhTzq0jP7uXPeVY3UUIOqdUVdx2W2u0z2cbvmeYaWqTe3KCRCTUj8r3Oq+JnER2Xf6PhUO54hoNgucX0H+BSzFtM6HoPAkrDy4SrW04sC0o7Z6tUnnFakrICsO1u6vEZNihIm4Yi85pdaOIpH4XpTo4Ix1DGKtoKr5iwQa5IY66/eD6RSbxolwTcFkwy/IAACIAACIDAbCMwbGxu7lnb89Kc/XbRo0bXkMEfSXrp0KZ9BKak3IXE5R45bfjYzzsSbnzVFrUAABEAABOYeAdY8n/70p6+93RCp185wXDnkuUgdVxsQCQRAAARAAARAAAQyEZgqkXpdpoIQDgIgAAIgAAIgAAIgAALZJgCRmm3iKA8EQAAEQAAEQAAEQCAjAYjUjIgQAQRAAARAAARAAARAINsEIFKzTRzlgQAIgAAIgAAIgAAIZCQAkZoRESKAAAiAAAiAAAiAAAhkmwBEaraJozwQAAEQAAEQAAEQAIGMBCBSMyJCBBAAARAAARAAARAAgWwTgEjNNnGUBwIgAAIgAAIgAAIgkJHAFPwtKi/ZmrEYRGACAIXTAARAAARAAARAAATGSWAKROqU/PPVOKs7c6Px/8cC1Mw9fKg5CIAACIAACIDAOAmw5hlnzPTR0N2fng9CQQAEQAAEQAAEQAAEckAAIjUH0FEkCIAACIAACIAACIBAegIQqen5IBQEQAAEQAAEQAAEQCAHBCBScwAdRYIACIAACIAACIAACKQnAJGang9CQQAEQAAEQAAEQAAEckAAIjUH0FEkCIAACIAACIAACIBAegIQqen5IBQEQAAEQAAEQAAEQCAHBCBScwD9Govsf6ape+Qa80idfODo3gEv9Er3PuumgaMPdV/RAQF/otBu6qwRAgIgAAIgAAIgAALjJTAFi/mPtyjEmzSBke6mk0VNDy9TGfS/cvG26sJx5cXy8dmbtm0vSRv58l899Ac/+EuJcsux4xuWldy1dPvR/pINXNiCyg1Lt+87VrRt/fDRpa+UXHh4QSCjgaNLm98wPg3tyvXl2m3PVgajmRj4BQEQAAEQAAEQAIHxE5g3NjY2/tjRmNf0R0r9+7fs71d5FlU/0VRZSP3PbNl/zhSyfOsBkWUc6ZUvHtiqBRrRcPc3m976qr9vYuf7b3pQw11NTScLt9pmWTKF1U1PVBZxs7uaDtCWpqoi4eFBM032QKldX3GaUPf3M3f17l3w7LqjWlB6IeL5pYCuvPxXe/tu+TdD+9afchOLW2tQ1r7bf1TyyN4v6YMyLikczgn7IAACIAACIAACs5NAes0z/jbnzJJqZNkBJXSGu5/pHn64kutddG+TSDElRptYulWNvy0zNKaozpHly7jNZuvfv3+k+okDWrUf6FrGQIqqmqqfYXFaPfyiF+RF7t/fdMkxqy780rPHvyRB3GtPGx66KJbUf/PKUXpYLKN62368ZbvnfGPvM7T94VtMiPld+KXtcihaLjysfLij/+Jd1j7a/8y+P2fvxKWnt++jv73ylyoKkbakLtj7/2xbv9Dzwg8IgAAIgAAIgAAITJpAjkTqSPcB13BIRZUPi0hzRloWLbut6NVJN2smJVy29cAB4g79c295te5/pX959ValPJd9Ydn+F/uHWaQSLXt4K5tRO2/b0sRBok2rm6pG9u+n6gOOvo3pglfy8VSDypw79O+6sH3f9r/1AbWfsm4/tLaxZXuRHQbAEd5YqqyvtY3bliYXLL3jCt20YbuWsGpMauZBBbYQOEAABEAABEAABEBgHASmTaQePEjf+IZU4Fvfos2bwzUZfmt4+RetbS8cKvvD/a8OF36V5ZcjXOPizT6/4UsjRTcZ42jRkqKRtxgBgxju2t+/fGuTtjxf0lhY4AYplmy4cPzKse0/WLrXN50KIh4G8OKCZ5XRdNnelvXideXYM298+eFgRz9L4b0tX+aRrBzuGGUdS+qVY68sWkpXLihturLdm0plLKlEFRsuRE2zUhw2EAABEAABEAABEJgAgWkTqaxQrygFw46ISGUdlqqOwyebtpyUQOn3DwqwVEnmhn9/56tLqr3BD6zgiW7qHyaxsMZtb6xfp02nTmDFBt7pf6YhMNL01A+cGERqfGrAJ7yzYP3DX7rSPcDeC8pKvjzkCV8V64292688BIUaJoZ9EAABEAABEACByRCYNpGatjJFy28rOvlKPy2LqlAzJtVNPzI8QsuMbZGwd4vyAAAgAElEQVTl65IU0sxNM3PdRYsKh/9aG0/ZfPrWcOESbvpwVyd9tclrd39n503VB77wCo9RtRPKgu1V8/RdL7Gkyv6yh2WkKUvVP/9iS2DWvzPwVL1bsDnWHRXgdfeHVeypo0tPOcV85q6HnD04QQAEQAAEQAAEQGDSBKZNpHIvv+3uj9ausLJ6+Zb93+zWU9dZg3U/079MTZyKxF32xeX795/sr9QLMLE+o9tkUOYs3liEn+vsHlkmE6f+ur/otmqZ0v/qbdVP6DbztCpSvfyFS765v39ZrEzNYEn98mcW/OUpb9EoC/LLtXdZtzgSZta/o191BNvHH+zcF0tqIAfsgAAIgAAIgAAIgMBkCUybSOUu/kgvv1vJZQ8f2PrMlqYtncpTlqBiM2HsIIBlDzdVf7NpyxadmkdhypJMs3krrGza+taWbyo0vLxUVdFw1wHPjCorAbBC1cK0qPIPljTxvl24yoOyYL036jQGkrakyqJR90UtqX789uajPE8/sC6VH+i4YEl1YMAJAiAAAiAAAiAwhQSmTaSOo46sUw8Eo7FPdAAA9+9X8npMwZizbY+FqctCzfi3beT1p7ZKj39T08XqAy4hTvVEd0CnBmb32wysw18iqr05pSV1aIjGu5JUYJoULKmWMxwgAAIgAAIgAALXSiCni/lfa+VnUvqpWtg2H9rsrd7Pa1R5Kwa8sVf/QUBAs+ZDTVEHEAABEAABEACBbBOYKs0DkZqlIzdVByxL1UUxIAACIAACIAACIDApAlOlea6bVOlIBAIgAAIgAAIgAAIgAALTSAAidRrhImsQAAEQAAEQAAEQAIHJEYBInRw3pAIBEAABEAABEAABEJhGAhCp0wgXWYMACIAACIAACIAACEyOAETq5LghFQiAAAiAAAiAAAiAwDQSyOU6qdPYLGQdR2BsbCzOG34gAAIgIATmzZsHECAAAiCQPwQgUvPnWExLTSBMpwUrMgWB2UjAvV1AsM7GI4w2gcAMIwCROsMO2Pir6z5vnFTv/N3rb9Oiz3/6E44fnCAAAnOYQKwe1TeQ2KA5jApNBwEQyCqBKVjMP6v1RWHjIxCrUMXz17/8xW/eo+vf/9EP3zC+nBALBEBgrhCIlaSxnnOFCNoJAiAwWQKf/vSnJ5vUTzcFltQpqYdfo1nqmqp/XxgPHlehBt0/T/74Fx/86Ed/84tf0scTiRvJDR1PzogDAiAwawhE1afrk8o9a5qPhoAACEwfAdY8U5L5FIjUKakHMpkqAq7u1G7rM3bxyi/of1ryqU/Rmz9+6/LFf/1Y0VQVinxAAARmHAF9Z3DFqG0Ce3KoDXLdNg4cIAACIDDdBCBSp5twVvP39aiZyK991Pe7yXf/6YMf//xH//VfacmNN/y3d958p/CTH4cxNasHCIWBQJ4QcAUoV8nuardWpfruoYO0T55UHtUAARCYIwQgUmfPgdZPFG4PO958881Qw37zy3/41dgHPv4vbw8NScgNH6B3L/7NT//xw+8PxcMuCIDA3CNw0003sRiNKlHXMxo69zihxSAAAlklAJGaVdzTV5hVqLaIoqJQb354N7RvE8IBAiAwpwgMDw/zDYQ3157KBFyFqoFE48wpUGgsCIBAlglApGYZ+LQXx0+RaS8DBYAACMwuAv/Ko4CUKmVhqjfdPnazA9p0dh1ttAYEZgwBiNQZc6jSVNQKU+2wu2mSIAgEQAAELAEtUq+7Lv6PslmqWp1qHTYtHCAAAiAwTQQgUqcJbM6yhULNGXoUDAIzlsB7772njabajKrVqvbhNkGYztgDi4qDwMwmEP/ePLPbNNtr3/9MU/dITCOtPLWOmEjwAgEQAIEIAbak2o1vIKFNR2fPSDp4gAAIgMA0EsgHkdq//5vdwynaONzVtL8/Rdjc8R7pbnrGUuh/5eJtywrnTuPRUhAAgWknwAqVNaj+jlWo014DFAACIAACEQL52d0/3P3Npk7fWLhlS6jey7ceeHhZyG9G77IWbzpZuPXAVt0qtat0e2F10xOVRYWVW25qauoqbKoqov5X+kf6+7d0+u1dvnX//1Gqd8dGvvdQz3/4r2PUs/qQHwEuEAABEEhLgOUph3Mvv3ZoN6tVPRpVJ0Xvf1qECAQBEJh6ArkSqSEZSr7qUrKs8okDldzY/v1Nl6pFmc3mrX//lv0jy5c5jezvvFh94IDo1f5nthzoWsYEiqqaqp9hm3L18Isj1QzHWlIFUYGPp6DqP99XyY+Wt99+2/eECwRAAATSEtBmVI7COpXdNq7WqXYXDhAAARDIJoFciVRu4zJjOOTu/uFqthdKu8Vt2j/c/SJVf7Vzyxbb061DbEITcWb/cnMOEHfon3vLtGPZ1oc9Z+FNRcMX2aQsbJY9vJXxdN62pYkVqiffR/bvp3v3O/r2x08vHfgOsSX19vyzpI5+f++fFWz//WIidnUV1NzctfftqtYa3scGAiCQWwJsQNXylFWpu2lLqrWh5raSKB0EQGCuEZg2kXrwIH3jG0LzW9+izZvTYR0ZHrkpvO48xx/uOvAqC7JlRSzhvI2V3Dc7C7d6feLGdxb/9neeHF5mmjvctb9/+dYmNSBg+JIeDMECdxk/URiB/qbPPXLhlv/tv5z4TlahDHbsHa7aXuEYdKV49h2t2n43+46e2rv3z0Z1lerriUpralhXF9y9vXWwo76DUupUPwfOrP61stbfL3az8tpYWsP+nhs/00iAXy06qEYdUT66f7J39Cvitg6vZI61t4u+UlXwZ12DTmWKa1IeZifW3HD6b2uB9sac2154QdV2D3sgwZTuuMKUM9a72uEqVPZ3d6e0CsgMBEAABMIEpk2kskK9ckVKY0dakdp/spMuFm15hgLDTNlSeHK46F6nutwr/uKSpgMHHLOhEzr7nJ4iN8NUqb/z1SXVVbqdw/2vEt3UP0wx4l5J1v9C9G+zh6S4puq1jkFKaRMtqNjeWqHsp54llZVNn6oeSxdtWN3bpUVsqscxR6SO+j+h1t9XWdm2yfPe7swFh8h6K/608hNxM1wlSl0JRO9tgN8CvrI98uZwLYgK7q4p2/tng3eneiXwqsaV4oM62PGar6y4hl3XUvKcSasPKDfXlf7inn4CrkiNKlRo0+k/AigBBEAghsC0iVStULlE64gpXcZc7qetB55YxlOFtmx5ZeuBL6pY0tHPBtPOS6xMm5zO/v4mPWFo1k2cCrGRiVOv3uYq8uGuTvpqkyfQ+zs7b6o+8IVXeIyqMbOGMvh6aH+6d4u/cvPeP2Ht1NFxPlDUYH0XlZYXn++xukosqXqzrtK1VaSfzmw67evaWz/oPJM5h+KaGupio6wStCb1HP41Ql4k6d7vb98eNCNbncNCp75+r68Up4AYy9SivaKRO5RQPs9HV23skEqxOuU6QY6Og/T5Dnv6c+ypfp0YRwUiUaxI5RB22+9IRHiAAAiAQPYITJtIXbDAk6fsiN9YgG4purfpgJoXxRODDizav+WZV5bREh6CWfmEGn8p41ZlApVsc2ISlWrpSDcPdJBJ/WpPfbEZ9bbqJ/R+P49D5V5+osIl39zfv2yrN7Hf76HjB8wLRK4V2s9oulzcd//7nHdrq1+A01kvlWH5EtNZrKJz0AWT7mYWozXejs1hsEMpn2B/qNJqJtlc/C0oLivQBun41hf/fmvNn9R3Dd6d0sQdny6dLxvF5ei0tlpTn3Xw0anXgzrq6wu4u3+UXzd8wVpsDmq63OdOWIoxKmyMti9xZN8BqKDqK9OOxrWexhamlSv6+mPhwBMEQGCaCEybSOWhqHZManzdI/OfZIClO3EqPtns9x1+a3jE2Iy5tYXVj9z2qmdGlZUAWKFq+2lR5R8sadqyf2z/FjVO1YKZ/79W/9eLFy/a/el2sMWODahiwStwhahfrI4g+1q2FFTV3Epvi7lUx2dToHk6F1RVsTSNGeHq5WbthNnpA/VKzc+f0cG+0YKq0EjgYFULigoGXxuk4qCxNRhnvHu6N9+YcaOpZFBHKRt3zWS4irujceCTnkDg9FZDfjl+Nk91rUS5UNeYym5o0/QHDqEgAALTRGDaRCqPQ007FDXcHpFfqmN/+datoTATtCwSEoo4g3cLK5sOmOqzWLduz6+SVYaMATBLU3nenOr/Z+99gCTJ7vrOt7vBKgiCCBDLTua01fbNHcchYGdSpak2AebP+bSSqonOxnAYfIGlXd121qyxV4ADsTpiOwvOWiuMQeJAU9myViIIG0FwZrKtKoEAHREOH9c99ObsYgvOBKO4lrqzRmJBCwQg/mzf9/de/quqrOqq7qruqq5valX18uX783ufzJ761u/93qtG268Hqukl/tRPvO8rZHX/0ce/4d+mzU39HR67p03QIfypj//qs29/rmfN/iNvfXoVy/mffv1vpUup1IufasX3Xnwes8TvuaQgV82ns7hOkRwS4ZqKWQzqLNxLU2d3kg4yF6UIRjwYheCIkzQ3ah3cIix0ww0yahXVMlefTuD6659HaPGl1od+9dLrPqXDAgptD1a3hUIXOdk9D6Ayl2k2138vVq/JpkXOnEQmT9FzT5oK9czvBjskARJICExNpB5DWE/oF8v0KzMnWckuc/69oq1Yc1HSEhHRP1arttnUAWTm0muf/L2vuoHdZM7Sk9pllKzZ78qQkxdbrXsvqrdLYKqOUn38PW9+jXru2ecw6Vnm4zMRro+8Var2HF2upp5ri3I6utzD14B7j6yWIT4NK1Gr+cqebLpfAjriRx65dO819qeexVYM75EJ/vzqaXq8KHWzpzcfkMwbZGfZ1w+dk30HOKvvY0XvaWYTEyRAAiRwjgTOS6Se45DZ9ZQJQKyYxfrYasp0pWUNFIvZlErdg7sN/3tk1SxI/+irXl+c7keVJMI1W22VG0xPas7iuBQEYkut9qyrOq7SKNflBv/W655+ujvS4N6dT73+8VX1XOvSGx+XBVRvf3vi4jVia0AU5ij9LUaZe/fi/OtHUdxLejEQcJQkQAIk0EOAIrUHCE9PQODF1kfvvXgtjX0UZ2pXPGIek5p4Uh955M49dU0996EX3/O6Tyn776rY+Jj0bPLQ/nt9Ufz07sWVy3jMI7/nrd1CsrfweOcvfui5F+9des29NxRvMGI5TCvQpm+ANzU5SYoUxdZ4nV3E0vm9KYwOi8zkDLMN6vU9ur9QikkSIAESWEQCFKmLeNcnO+YXP9R6zdPvefweViY/V9KyuNDMqn/tSX0c8/yfev17xMEneyQ9B+/Ra9/wxtfqio88bgRPFvWY+WL15WRpuU5nEX6QrSWdXtgsDLd3+l5WLJnx9n09mCSGe7/6WzZULxa7ZT7SYvO5F1Dv5JBufIsiybR1sUCx4gKle79iYejpdD/Wtz2y+nj3V4psSuKRx9+6QJQ4VBIgARLICNxXjJHPckdP3L1798qVK6OXX9iS0wOVRZIhYQ4Tk2qX7PS/sPg5cBIggYEE4jj+gi/4AvwsKo4HCofJMa9YPpUdaAjpgc3xAgmQwMITmJTmuX/hSRIACZAACZAACZAACZDAzBGgSJ25W0KDSIAESIAESIAESIAEKFL5DJAACZAACZAACZAACcwcAYrUmbslNIgESIAESIAESIAESIAilc8ACZAACZAACZAACZDAzBGgSJ25W0KDSIAESIAESIAESIAEJrBPKjYaIMdRCEwJFLadQu/ZKxLYgurBBx8cxSSWIQESIAEQ2N/fzzacwiZUWTpLmP2nUNJsPsUtqPjYkAAJnAGBCYhU7pM6yn2a1J5h/X0V5SnSOMw+qf0lmUMCJEACpQSWl5eNHi1sk9olVY1I7ZGqpU0xkwRIgAQm5ZXjdD+fJRIgARIgARIgARIggZkjQJE6c7eEBpEACZAACZAACZAACUxgup8QZ5DAF37hF37uc5+bQcNoEgmQwLQJfNEXfdFYXTz00EMvv/zyWFVYmARIgATOgABF6hlAPocu/vzP/3ziscLTC6s9B0Az3+U50j7Hrmf+thxj4Cyggw3jitRjRsXLJEACJHBOBDjdf07g2S0JkAAJkAAJkAAJkMBgAhSpg9nwCgmQAAmQAAmQAAmQwDkRoEg9J/DslgRIgARIgARIgARIYDABitTBbGbiStTcbMczYQmNIAESIAESIAESIIGzIzATIjXa8tsdM+YSTVa4enZczrGnuOU3o7T/aKdTdez0bOj7S7/wSz+d1RtakhdJgARIgARIgARIYNYJnM/q/mjLa+4laOw1399wdzy/3fDUzZ2VRj3VZHF70w+NeN3zwrS42/Br1qxjHdc+CFN/26oHdUcpe9Vb3vTbtgwzuh3Fe5G3nbfnmEI647O/+c+rn/xNScoPo8pPo6oPf1h+JPXo6OPf8G91Fl9IgARIICGwvb29trZGHCRAAiQwLwTOR6Q6G0Gg4DSN3YYder4RYdGmL9Q8T1mu36hpqSqSTImiTbQZvKoXbu47anrNTqXoLrVrDbe5Fam1ODxw/cCgEDYy/FTC4/TLv+7HPvl1UKRHz3/sp9Qbvuu//vuf++/Wv+mXP3b0g3//qw4ODqQCDxIgARLQBKBQ8U6dyseBBEhgjgicj0gVQFG8fEPkVz3w25uh3YATMWpuqfoGnIkKnkVvW8tRaFZdupkklNrzduF8XS2INV1ibl+gvwPVaft7+4UhOPUNSNKwesPHOEWbrvm1uNlUblDwIj//sa//9j/QleA9/bkPZ57UD/w8PakFlkySwMITMArVYKBOXfjHgQBIYG4ITE2kfvCD6h3vEAzvfrd67LE+HnH7Vhh2wtBy69V9dWNlx2vuVNTKxgrciiuY9V71g1VM90O8uvGmv7+uJ8IzuVYQan0tX4yMuL0VORu+CHYVx8YrCjWrz7MRvu7R//TJzkcef+Fvf+DRr4E/NTs+85s/+PmsEBMkQAKLTaCoUA0J6tTFfiI4ehKYGwJTE6lQqJ/9rGBAol+kRlCo0FyiTZuYg9qO7DXX2g6bXqQq9bqmF7eC3arnK9tpwNXajBy4WiHXLPviK1SI8XB3ya2Zp6gT7Spl7cVqkPP4pfqVf6eLSjiquFMlJvVv/VNTm68kMPcEMM+wue8mX1TnfjRnPwDGoZ49c/ZIAiQwEQJTE6nDrIvbt5VjtKaEnzoRPKarNWe1FreaUUV7CzvtYDuOVRKuKo2l0/1OpJxuh+KwrubyGtzMCtG6xvZoO7TWg5XbWPEvy6pKji9r3h3bk6oXpS3VAx1cUdLm2FkSWWv2FkjCh3XMhm9iNippR6I2Qh3GYRcWwJUbg9V14ZKJ6+gtoNeZ6WaylrXBkn/gYlBZAVmWZ8R9ZmAe8ZwNUrevl+hlxss1HS1csDMpnzWOL1Q5wAHtF9cIpo1n3RUhZMYcn8gNyMeSda/SXhAlki5PLNp5fPOTKwGjbi2n8eWTa3aOW9KPVPZMquxJyO9afnPTu5bmZE8LagXqxgVcPzrHN5amkwAJTIfA1EQqZvmz6f5e0+3ahoup/CQ7CvfXV/Y32xbU6sGyOvDbiL+0at7abnjZr9ttf9v2NywTt2q1/LRab6MX5xxu1Krrm/FEiEPVs/z2si8BAGUydVxPqv6gdCqTDOqNWzvLjaCOLx4iQ5sRnF7yNQP7FSBiQT6JdZaKtuEP0zELsOFm28HyuIHGRDt7jrthG6XYZW1Zy5pWDJ+ze8OBDaHygkCieZte0K7gcQLHjtsIZMOELS9oOcWYZvjsQ+j1hlRMjDfqYans21Bp7zIK3KeecIzkkcxUozmPW6G6EUhscQYhKTjiW4TldAnFdCyl/HeW/AAAC/xH7IDFpkFAa03LqeRtlzx4/U+X3caMkqyexMO5HdXkC1iwv+7L3xoPEiABErjoBKYmUjHF3z/LX0JzP7y97G44ndth1Nrfv153D3eDvbg2aGq7pIULlpW7UcUTBuVjhClU+5LvbancdWfGbX3rB757FcksIBWJV155ZdjqfoimQJamRZPbAMBeTTcOk3CM3biD+IRdteZpTW07VTu8LQ5wZ8OEcmCfrWW7sw/fpT3AGCi5jqneVyAua1lgIIZkySwsq9UFCRSzGLIicnAnqrjmc9257jRvRfGqnYr0VNqivOVUrXBHLMUGC0FNVGT2nSjRoXg++8ZltW8hGqWoUEWXQ1r4qyo+sJe79/zJWMWHHbW0kpqhDR7pRRbVmcNasuMDoZi1qVL+jpVCwNUltXsYq+IGEiN11F9IIGh/Obx67v6mPJ7GvY9nVdzel8PkOly86/t6v9/I90LAqTu519C4t/EEBqqKIB9pEF7D64j9kWTm/NaqTvzltpld6TdnrnJsibOX70jpI1Xy4Fn9T1f3w4PvUQF2/DCP91wNn8aSAAmQwAkITE2kHm8LPvD0510nisy/2wi7VDrLar9ne/d3pIVkjr/3LZ0IO76TeSlh1fCJrQ/IIyg5+UTHcrGi8MGHnI9NDwo6tWt1PyoXY1LPaZ9UiMvIqrqW6hzE1vVEgNmXRbgWVRJiGOLKgOgFoRCF26qaBjxoLPnLgJYh7iNnPRHBib6BVApEPUMO2kup6ynTx0mTEMtayMrpED2nxTIsu90/LrXfcZYPfa+pFZWezNUaFw0iJw439fOdT80ncg1qTHs6EzvGfwOlWEK1C0fGP8+DX3nPrq6NL4bzJpKU/uYApZU0Fa/Zvv7uIa5rcXur9mbirjYVgno+3Y8dKtLnGcMX9zbsjrVnva695Z54onXSfIWImnrnYF0MURx76e3rs2puM0oevJJn26q5S9ilD8pWvge1N3fcRhKsPrcDp+EkQAIkMCqB8xKpxlM1xMq3Dbm2AJeET/8wxRlTyJXV/dqHirwxPKmFFiabFNcv3Dx6j1v49wYcWqIND4ctOD4HNNKXLcvLXOO5xTXjtZLpe8+vNswmCX1VJpmB3v3uAAPTevacy6jTMIMkE0ra26yeMGRTIhPC5Ocf0oEU+Sd54vqEcJxM/CK+bMRN3ztIvPv2qut44ndOvea2Woqbm95+6l5N7cK77FAR7aVx5RBc+MoiTlNXS2xrGRL0uk46K05zRx4efK9IPPHwpFbt7eIGbYWGFyCpd5WWceKB2Vn3nWR7vixEdQEQcIgkQAKLSuC8ROqi8r6w405mw4PCTHQnnWLO57VFWu1WGzoicyAK+EQ7Elo64MAcd3/LZnlZr7cQXqhKGCJ6BOrqNpSPvh7vx1oUpc3jRMIC9Eo+0VKZAzgt0PVe2jtEl5v4F52VSnMH/tNex59dW3fCzAbdpIg8THZ3auNuWAGxIsEEWhSnxvXyR75o1oGBsmm9sd6NNxldeU09g++4a2HQalvblisRwMrIKfSbXO9qvFdUxYddl3tO4FNUSz15F+y05MGzVMmznQzbTPRX2v6trhDVIVDu3Lkz5Gp26dq1a1maCRIgARKYKQL3z5Q1NGZOCURbeXiiGYJ43Uy4oULsXYxIUHiC2jehUI/z6iG0VFWTzR/KcJS0rKebV1JZiz0i2okjF6uv7CqWiGGKfy80mfilWbtaDM/EFH8cbieRJ7sduPLKek3zSnpXEKZR2JK5fj3xjc7S0ipqm3yM/VakQw6wA25bF9WRstawkWatdCUgVqBQk59kS67088cUeh7Q3FX/5Cdxqy2YnHq9ouR7AlR/papwlyuGWdxu6esbCEEQ3S/Yk94KkIEiIzDYFjww6fOD9XZmR4jBpefySoEJ5gH0g1f2dJmx4W9nH7H7czlQGk0CJEACJyVAT+pJybFeTqBvMlcmfOs+ojP1BK8shZGPVwThxZEJ0JS6va410x5EJEJLU3Fj8rpf+1qOW9liJikJDyV68bROhcMPK/qVqvn1fc90jYDmNKrStIsfTXA3E0sxMz5ACCSuyrJxwYPo4ycnzK/76h5lcl8vnML+AGhZi9K039oa1hKZLCk7bKTGvp5XeII7shopyZZQV6d3Mr0euFiVtZf/TFvXblk9DY58aldUACcpyqNT2TfALDUDfMPMdtLruON6mZpTVXgG9MKpbsionCj1Qb2LFPbMALBwamxKg5qdpfySB6/v2Tb2moheiUXNQ1Tlz2eWRkNbSIAESGDyBO5DLONpWr179+6VK1dO08KC1J0eKHMH+2NSJ35fpjeE/BmQeIBxt22HfAyXj3XQ5n3MR+osaA8gMUbXYM+dUAsYx0BXqDXZJGx46KGH0OZY0/0vv/zy/fp4oHCYHPN6X+FA4zibrNlsjQRI4CIRmNQ/hvSkXqSnYv7Hku9yMPpY4I8c4P0cvQ2WHJuAXgAnvxs3vjN47L5YgQRIgARIYBEJUKQu4l3nmEng1ASyjQtO3RIbIAESIAESIIEyAlw4VUaFeSRAAiRAAiRAAiRAAudKgCL1XPGzcxIgARIgARIgARIggTICFKllVJhHAiRAAiRAAiRAAiRwrgQmEJOKNVznOoS56XxKoLLV/QBh1vi/8sorDz744NxwoaEkQALnTWB/fz9by4/1/Vk6S5jF/TDTrOvn6v7zvmPsnwQWgsAEROrly5cXAtXpBnl4eDglUJlIzXahgkh96aWXTmcva5MACSwQgUuXLhk9anagQtpIVbxCj+LUiFTzCi4UqQv0cHCoJDA+AWie8SuV1OB0fwkUZpEACZAACZAACZAACZwvAYrU8+XP3kmABEiABEiABEiABEoIUKSWQGEWCZAACZAACZAACZDA+RKYQEzq+Q6AvQ8iMI11WtNoc5D9zD9H2ufY9bzfd6Kb9ztI+0mABGaHAEXq7NyLCVty5cqVybaIT9+JtzlZCy9Sa+dI+xy7nvc7OAvoYMO8Y6T9JEACJGAIcLqfTwIJkAAJkAAJkAAJkMDMEaBInblbQoNIgARIgARIgARIgAQoUvkMkAAJkAAJkAAJkAAJzByBacakvvjcUx/orL7znY/eQ0I9/t7HrV9517vaFhJXwUGuvlDO49rj733M+ti73tW6p69fW12NW0naVEOXDLQAACAASURBVLgkrV5C+p4ulZ2WNzfjuS8899RzZSDyUb3wwaeei2XIHSQA0sCxkRCQhePFD33/B1945C0/9j1fU8hkkgRIgARIgARIgATmj8C0RKroqjuCo/Wup1oay3NPPaXfoVifuvq29z4uJ4kOu5eLV606dTm5XHvn6uG7njOnolyhyXQB+5Io1Ezm3ss6MUWvJjrYnM3DK0b6zjfKmJJD63udziRsNsYukI+/t7L39tbS00+/4WGlfnvvRaUeed0jSr2SNsR3EiABEiABEiABEphLAtMSqQIjkZU9XER19WSNeJoJ36vfelXrWrVau9pqvyCSF8JMJXru6tu0p3bERmej2L32u55q95hy6bc+8C71tlXkpgPsLiBCFkr9XufSvReefZf6ocePWtCo6sUPfv8PHB29853v7C7NMxIgARIgARIgARKYJwLTFKlqr2Qi+9rVwhR10QUqHtaEnJ28Q7qJnr2WnF597L3vTZJwGL7zvW+Uk0evYcY/qzl/PlQzoF5PquSKz/i37rxsIQmQfaERV69pkI88+vTDR+/6wKcvvdB+7p56+E0/9I43fPkrr7zy0ksvmZb5SgIkQAIkQAIkQALzSGBaIlULSrg2MzenwBFXqKpgLl5OxOs3znT/nVzEot63263/U4cTwM/4+HvfK3pNBwIkhcqduNLt7B1XK9fUcyWeVFh69fE3fuPVN36jBDbcKepv7Y0GyMdkNEeXHoXbtPPic5fUI29+9OEXP/R9H4zf9M63ObM3UlpEAiRAAiRAAiRAAqMSmJZIzfp/4QOZm1PnpW7RrMA4CRFqSlYRqa/MvapQbE+1JKbz0Xe+99FxWpuVsiLodRBqshxMq20riWHIjJRhZidIaD+qyUCFZz/9rT/xQz9xdHR072NxsRTTJEACJEACJEACJDCXBKYqUsXHKVR09GTZYqZxpvv1Gv+9F19Qd7Cg6qr6FQRxmsX/mnuXJ7LodJzxu6IFaTqObG0UjL5nxL1xCT+SgNSu6L5F/S+2259RR1g09TVfqz7zwt5n4Fx9Xil6Umf81tO8kQl02v7mvhvU+UyPjIwFSYAESOAiEJiaSO1SX0IqdwTqSX4Vd/RMvSxyKlvd3/n0PVkwVNnLllldevRbrz71AQSpYhIcq/tNTKruRqU7Upkpf/W3JI5zPg5M1Yv7V68JS7W1HlPmSdVwUhkrgyqA1HsCvPD8CwjRffytj6ije7/63Ec/c/Wt/9rZGxqRGjW9ZqT5OPVJffKXtBm3fH9b+3Ur9WBDCwxRG6HOst2GX0vuU9ze9MOltEx646ItL1zy/VVEKPcWKGlZ15L8Axd9ZQXsNdOCUpmBlus3amnYs+lMt4/nEdK+B4jUUj15KKbbtwr5WevFcZnGTded3vGWdpfWGP6ejU7lY8kMyIcAgM093VLGf3i7E78Ko24t99GeeDdz1KDcpk72TJoHu/tJyG9uetfSnOzRwuMaqBvZn88cDZ+mkgAJkMB4BKa7mT9UphxvgxAVryqOd9bMRkv3Xti7py4NVpP37nVwubApk8ScfgRqrHhgBhx7qV5afZveM7V4Za7SkKHYrutSbbUwg98zgITe4wiWgG9Vg1xNQH6sfUc9/ObVR7Cs//ue/ah68w+95RH1NW/pqV88jVs7y41AjobbaSZqtVjgBOmSNjvtYBsyDofvHiTdRNvwh+mjboU326JW8antBftL3aJRLIh29hwXCrW/QFnL2uY42lXumqM67VB5STfbQVtEQNRsQiZKXn0pDFpdIRFxKxCJjKMXCGoZMa+bT160QQdW0eJoS5SHbj0dV1IYesLzbne5tQd3V+xlSDoKIcT1kY2llP/OkjapwH9Io7w0bQLQmp63oyp5PyVPQv+zjZzdqtzIRnV3W55G1Npfp0LNMTJFAiRwgQlMzZNawix1rl6TXU4vYa/Ty1eLKhRazczgY4cpde+5e5esT3/gKezhfxUa9yMtdafVEqWrfxHgqef+x2svfBwLp5IFUmnL0in8tHOlWe997AOIW7j2eNc+qSX0ClnpcK/al9Q9eJwv1ewXnn17697Vx378LV+LuNThu6Taq/VEYFm2pXbh0XZO7Xnub9Pa21Vrnnaf2k7VDm9HynGcjXoyDHvZ7uxDPdpwXQbimIwOCgOUT+KwY6r3FYjLWpbKURguuYGMpVaXnbuU6mBw1gpyop2o4tb1MJ3rTvNWFK/aqcrU0vaGttRyqla4I5ZKbUhPVa87zR050Z5Y7VPVBsElvLev8+WS6OkN3Z6z4jTDqONEN31IC7iBa42gJnXDtPDA7tICx7479Y2kjLVkxwdCsZ+/Y6UQcHVJ7R7GyklHfGwPAwtgIEa2w6vn7m/mTubE7X05TK7Dxbu+70vZyPdC7Z/O3dXGvY2bHqiqtR2K8oLX8PqOqZs5v1HAeOLtir4fA62ajwv2qh+s4qHKHoWSJ8E67PurWeseHTTrgeubx7v7Cs9IgARI4OIRmJpITeaxNbE0pBJT9NnKpquPvfNqivPSG9P9pN6YZuF3lWTr0/R4JK+o0sJuehHCdF7XTGEI/bZ352RwUDbbhKsA8vH3vOcIl97wnjdAnuLIqRyXghCMrKp7aoVa7Cdrs3MQW9cTVWRfFjFcVEnRdhhXhoQYRuG2qjbKRdWAluP2rchZT0Rwom8glQJR5PFhx15Kx5np48RuiGUtZOU013NoQYINnE4zKaa1aZLufoMUtpbT1pGK92O7Ltq09CjvrrTocZmgFDvdFDP+eV34lffs6lo5zLzYCCk0Lg5jCcCQI16zff3dQ1zXItNVe1Pc1WkUhwrq+XR/tOXvrweBqE2ZrW5XfCRj7Vmv6y8AHr4BBDppvkJETV888boY1OpeClh3fSFeSp6EkmfbqrlLHoS+DkVx2ps7bmPAk3UhoHAQJEACJFAkMDWRWuyE6dkjIAGLcMn0RmeeytBim/DvDTi0R60vArWrcMHx2ZU/5KQjU/3Gc4tSxmsF8eR7frUhQme8AwpJYluhxgaPY7wWJ11aR/cWo2LRQZF/0p+4PovhsKcyA1824qbvHSTRw/aq63jid0695rZaipub3n4hVjftL44PVLTneem5g68suE1rrr41WuNf10lxRe8IdHyvSDzxyq5U7e3Mb502sTDvzgYmG+TAF6eddd9B2ICEemchqgsDggMlARJYPAIUqYt3z9OZ6yCdNZ4EAlFD4gtL28RMdCedYoYjUy2tiP9NpNVuFbGhw/xi8Il2XDP/XmZZactwzVrrQeLiy2rBC1UJw724BnV1G8pHX4ejM3d8oihOJCxAxzyIlrKuKzhlVSfKJBVSesI6a7c7gaiJjugq3TrcY3DVdhfoOuvvbljprqrpifiJdZxioWYvf5QVzSq3ZGyJnvbT9268yejKa2ogjruGAN+2tW25mr2RU+g3ud7VQK+oig+7LvecwKeolnryLthpyZNgqbK/GjNuM9Ffafu3EKJas/GntB3VzHrECwaGwyEBEiCBlMB0F06lvfB9hgjoUMtJLepPxtXfpnjdTLihQuxdjEhQmee9CYV63JoPhJaq6pAw2ZKW9XTzSirG4lZTL5aCbYgWtasVW0E37oUmM7od2dVieCam+ONQL0mBMN3twJUngaTpgdl0kWbdk+o9dxNqIwrNYiz4gK1hxkPK9nXX09pxp2YlTbcLvJ8/vomIQp2oiIlbbYkfder1ipJvIBhMpapwlyuGfdxu6esboCW6X7AnoymMGo/Bll4zN3SgeGDS50dJcMjQwvN5scAkefBUybOdjA1/O/vuRO/mfEKj1SRAAotFgJ7UxbrfUIq9E68lk7PjMilts+5jqx3tjZSlMKIg4WWMo00Jr9NHr2vN5EJEIrQ0FTdJ0a43p7fluJUtN5GCmIZGL57MGYvA1CGSNb++75musUYnjaqUEiiz4bubiaXYKCrVuuZi9pq4KsvUKkQtWsckrDSGDm29tZBZOJXVzxKjdZcV70vAE9yR1UjJBdmFyum/py6813tweabV0/2M0vOTvNsVFcBJiqro1CwUk6VmgG+Y2U56HXdcL1NzqgrPgF441Q0Z9/cY3SlS2DMDwMKpYc/DSYYyE3VKnoS+Z9sYaiJ6JRY1D1GVP5+ZGAaNIAESIIGpEbhvrKU2/WbcvXv38uXL/fnM6SFweHg4JVDmDsqaqfR45ZVXXnrppStXrvTYcMpT3OuJt9lrksQDjLttO+RjuHysg7a3p1k/PwvaAxiM0TXYcyfUAsYx0BVqTTYJGx566CG0eedO8svRw9u/dk1+BvAzn/nM/fp4QB9I4t283nfffUjgNTtQHunhzfIqCZDAIhOA5pmIYKAndZGfotkbu1XDvkRjHnBeDvB+jtkQi49DwGwpZTzH49RjWRIgARIgARIYjQBF6micWIoESKCLgNkCtiuLJyRAAiRAAiQwQQJcODVBmGyKBEiABEiABEiABEhgMgQoUifDka2QAAmQAAmQAAmQAAlMkMAEpvsRHjtBgy5wU1MCheVSgJa9IoGFUw8++OAFJsmhkQAJTJbAvXv39LopeTFLprJTkzCrptCpWTLFhVOT5c/WSIAESglMQKROZAFXqXEXKXN6y36L8hRpHBCpBwcHF4kex0ICJDBVAsvLy0aMmtX95rWoU41I7ZGqUzWJjZMACcwvAWieiRjP6f6JYGQjJEACJEACJEACJEACkyRAkTpJmmyLBEiABEiABEiABEhgIgQoUieCkY2QAAmQAAmQAAmQAAlMkgBF6iRpsi0SIAESIAESIAESIIGJEJjAwqmJ2MFGJk5gUmHLRcOm0WaxfaaLBM6R9jl2XSQwj2mim8e7RptJgARmkwBF6mzelwlYNfFdF/DpO/E2JzDOC9rEOdI+x67n/WbOAjrYMO8YaT8JkAAJGAKc7ueTQAIkQAIkQAIkQAIkMHMEKFJn7pbQIBIgARIgARIgARIgAYrU+XsGoi2/3Zk/s2kxCZAACZAACZAACYxOYE5EatT0vGY0+rAuWMlO29/KRh/tHFQd64KNkMMhARIgARIgARIggS4C57VwCqoTotOpB3XH2AMddlN5jZrdZV56goJBmr5w79GW19zTo6rUg42ER5Zpr/n+as1b8v2W5a/aKtqJOlHkhTmGitd8Iqml7rWe+Pi7f+Po6OPf8G/zAkyRAAmQAAmQAAmQwLwROC+RCk62bUVhK3YgvBb56LR3lvxgAxDi9qbfjES2i0JV0OWp9ASsVd/dgqx341sdtxHUMk9q1PQPshOlLq2+/7tqr7zyysHBwSJD5dhJgARIgARIgATmncDUpvs/+EH18MPyHxIDjuqNurUd9IdXxi3f04e/1fTNLD/8rJvtGDquBYdi1N7Ul3WOkkiAJEYT2s7Lp8UH9Dpr2Vatnsh0215SncNYddrhnlNPXaqZvc5G3YnC3aonChXatAUeUbOp1ooq/xPv+4oPf9NX/vw3Z7WYIAESIAESIAESIIF5JDA1kfqOd6jPflb+Q2Lg4dTrVridRVvqcpBf2xa8iDi8pQ6EWM8Rb4fqBi76rgpDVHXq/pqSRiDYDly/T9v1VJ/dU9GmdrViq3g/rizHRoin+htmx61m267LjD/Sh2blVCFewgzstU/+3nf9+3/xqn84u8OkZSRAAiRAAiRAAiQwAoGpiVTIU3NkiVJrIFNVs7gkCvLLXnPNPLddqfaHAthr2pWobKdqi99RpsI99wAxrh33xoCQ1tKuZyoT/uDN3WrDT+bx93a1EA8CiPib4kKG0zTcXU7XS8XRrlIHUb+CT8f082mC7yRAAiRAAiRAAiQwlwSmJlK//MsTHlliAB/MYhdlaudgsPQa0MK8Z0uUwu0V+IbzSNOKm6SdFaezD69p3ArVeirBozBccv3r++JILj/oSS3nwtwzIYDoak+Ho5xJb+yEBEiABEjgghKY2sKpd787mehH4pgD3tQdf3tfqWUUdK47zWYYrcqq/2g7jFW+eGhQM3Er2K36weXQu9l2Bu0PMKjyuedLWGm+qF/MgTBthu2OA50KbRpZVVfcqFW3YWw1FYDFWt5sRk79WskQ4EldK8lOsmSFVijxArab+W4Hlx7titmuQcpmIQgSQLytv3JkuxZIbDHuKY5i19qepW4IuPtbXog9DSS8obdAScvSpg5ZPnCxQ0JWQO+NoN3xmYGW6/c+JBmQ3HjdngT96iVs6R4USa7uSIJS0vyscRTIBqsLyxo4s3VDTibrrgghbXrEd+kRS+gKX2z6KOVdZyZldpZAGLHjUYrZNaztG6XgYpXJ6GePWfYkqPRBTcsUbxm+wc5vFNNi3WKOlgRIYMIEpiZSH3tM4b8RD6fu3oYYEJGKf7/r2FPJ8yS55tp7EK9DjySGFULEdW/5QcsxUZtD68zQRYku3TPD1VbpD6d6I/Y3vVAyIPlqquWrdV+klnyEQdIabWTXbixjYdlR0+sW8l/2Heu/MWR1vzhlEdSrV19NStbHrZ3lBmITFFZ9+ZDOsLDTDkTG+U5x14LtfdfsWYCBmG8UMqKOg0jc3iPa2XNcbHrQX6CsZV1boiDcG46sPFNeEKBNVA7aFSg5KPtkVwRIt56HBF9yQkjkhlRMjE+MQS2Jeu42TRtUcXotzlRFd2mcZardXDk1fyPZnS6zyij17RoxDEKf1cyYMIFoq9lZ8wN86UofMyt78NIH1d5OdvXQP9iBr6lR89ayjyeTBwmQAAksJIGpidRjaOKDu+tfXmcj3wg1S4s/rKLjU62ab/yIq76ftoxdmXQ620J1Lv03GEWwmg4pe8d4i66oVb+euQmL3ARL268Hqukl/lSs7n/hw2roPqn2at0ILNHHSyu9YiuzYZxE1qaybEvtxh1lIax2zahniR4Ob2NXXEdCO8xhL9s6jMHGgxCIYzLq3jILSq5jqvcViMtallZ1FISIb4UNE3Q3HTFkReT4TlRxRUNDMsJVfyuKV+104Km0xTXLqVrhjlgqJaEqVL3uNHfkJP9+oA2Czih8fZJA6iXdui5qXL/w7vurKj6wl7ud2hmrk/I3zzlkaZj0hrc+Skp2jTDXZdeIXYneHgIhb2lYCqO+qdzqblMc5JkbOHMH2k5FYZc0uP3wTWDnerKZ2s71NJ5HdLwlXnzjNRetVojDHtbxgl6LtsLlG/rb6YIC4LBJgAQWncB5idTB3OWjy8wIQzRgZrZLyw6udvGviJztH6VV22weIVv+jwOr+7/qxnH7pCaqAjOMen9WU3Myr0l8gqUQW2xdT3SgfVmEKyI3Ul2oAzkq6Vx5Sc9RuK2qjax4V4kBLcftW5Gznohg+XoDIYXnJxBF3iUiM32ctAqxrIWsnKZ6zrHRggQbOJ1mUkzLwCRd8hZv+962tKCn4LPvSxBzcWic4vkM+xT5l1hmdo1Ys+O9gpLuhVBSrzyrE4bKh5daE45qoke16JS/UxlXtNRbL2ru4ItIXVQ+glj8WqO+LwlL3Qzhac/jsHvrXbRzZ8OPN/OHRP5dw5dPxKPLpJGeMcHXnDUXTwsyZPY/bvpLnl/87nPRkHA8JEACJHAMgdkTqT1OxGPs5+UTEEgkFHSGt1ntC9A8QYNJFQmCxC5gOuJTQl7LDy3R+iJQu8oWHJ9d+UNOOjLVn8U9JP5pfOHxfOyZMPYXHfmJBHgEoW8Hj6NgTOYOF+nWFRidq1UIuDTMYFr8CxalSR0GYEJXoZcncFiupzdBk5035IuHBVexhFjIoV3m3R5x5CJ+R192VirNHRhhSQy6t+lL8O7YN0b3M58vUPP76zrYRb6HN21Ex+gvQvoxw33y2xJhnE2hRM3NZa/RQb4sjxwcTDKfMGg1CZAACYxEYGqr+0fqnYXOk4C96jqd3WgkGXasnfiUlRneIF2TZC0lG4Shpp7X1tProhoDiYgdthAEPtGOuzZQv5S2jDV2Vrb7QWasVXMr8e5eDFdufJCOE9vQWssF/xROJCxAH3F8oKzLCk5ZHSgMLxeCUmVoxV3Ssub7Exqp7MbQd9i1dSe3QV+eKP++DiVcoWvXiKEQSqqPlqWDNkYrutCl9C90rJiHWh5LfA/T0wVJNLbjrik8qBkiPdFf60jAiewYXVfwPWcXmSABEiCBRSFAkboodzodZ9zeMhuv6khNq5ruvZpeP9G7Dt/M1rpLEyKJts0eWQj6jBEJKtPBN0eIQURoqRpmVUnLRQWAbvCrB8knOlZf6d9HwOz2XvIxH92O7GoeeABL7aU4+UUJuGM72FtBPJ3pAS+gTPQPCU3AYKNWglRHOxQVcNSWHwbDIdEIOm51Kvx1F90vZhOI4peBYRC6645xBv9oSg9BwWYzh2OqG8t87G08ovQ/pr25uCyx2hCm2lYdgLFs49uRfIPSWYLOupzGt0TNcMnsBj0XY6ORJEACJDAtArM33T+tkbJdQ8CurUX42Vn92Qj5le69eio84oCM9kxwnTSEduvyS2A+OsKpBNiJDwletzhKdi2Q7O4dlJAjB0QkQkvTj2uT1/3a13LcyhZpSUl4KNGLp3WqjFC8pjUfkZCma8yc6gnrrFEEC7oIFtSWwqQBLlyZOM82VsjqmgQWDHUjlZAGvXAKS7DSK2m/U+DfY46cive6d9eIYRBKmhgtS36tN92Nw12zexbA9bUBMrLI3UFswDrq6Y0g+gpdxAyn3nCxZYc8ZVkEqoTnmijV7G9E749xCxP98heA7U1MiKpM9xec/7oNvpAACZDAxSdw39FRsuTmZGO9e/fulStXTlZ3oWpND5S5g3jNDrNwauL3ZXpDyJ8ECdfDNlXDHZd5cZ2CfAyXu3YM7Skwl6dnQXsAmJN2LdIcYZdj3bwBJsxr9knRTXK8sOGhhx5Ci3fu3Bml3WvXZGuQl19++X59PFA4TI55va9woDzORmmcZUiABBaTwKT+MaQndTGfn1kdtSwcGdc2eEsHeD/HbYnlxyegl/lrv3zuMh+/FdYgARIgARIggT4CFKl9SJhBAiQwMoFsZ4ORa7AgCZAACZAACYxEgAunRsLEQiRAAiRAAiRAAiRAAmdJgCL1LGmzLxIgARIgARIgARIggZEITGC6H+GxI3W18IWmBArrpYA2e0UCC6cefPDBhedNACRAAqMS2N/fz5ZJYelUls4SZt0UmjNLprhwalSyLEcCJHAKAhMQqRNfRX6K4cxu1UmtdOsfYVGeIo3juJ9F7W+DOSRAAgtNYHl52ejRwuL+LqlqRGqPVF1oZBw8CZDAYAKT8spxun8wY14hARIgARIgARIgARI4JwIUqecEnt2SAAmQAAmQAAmQAAkMJkCROpgNr5AACZAACZAACZAACZwTAYrUcwLPbkmABEiABEiABEiABAYTmMDCqcGN88p5EphU2HJxDNNos9g+00UC50j7HLsuEpjHNNHN412jzSRAArNJgCJ1Nu/LBKya+K4L+PSdeJsTGOcFbeIcaZ9j1/N+M2cBHWyYd4y0nwRIgAQMAU7380kgARIgARIgARIgARKYOQIUqTN3S2gQCZAACZAACZAACZDAhRKp0ZbXjOb5nnba/taAAWSXsoQZaKfd8NuxUnfeX79x48aT+nj/C/MMgbaTAAmQAAmQAAmQgFLnFZMaNaEnLddv1Oz8NujMSj3YcPK8hU/FLT+87NdTTNF2GO8pz0u4OPVgs96CtHWVveY/86aHjw5bjW3VWXhsBEACJEACJEACJDDfBM5LpIKabaswjGr1VJHGrbBjpVpsvqmOYz08o5shXKHZkQlQpUV8li+JqBku+cFGF6Wjo5q/oaKtEO7Urcbh9dd31eAJCZAACZAACZAACcwjgXMUqZa7bjVvtWPHOFOjcFtV16zwQKSY11T1wMhXnITLDd/Z8/1treUSV6t2u6bI4UX0V7ukW3pl5t+tmh/UEishWLdtv9uRXNCvO81by17DlqgG4DHFomb9drX5RKr0Z364NJAESIAESIAESIAERiEwLZH6i3dbz0bvgwVPO09+x5XVclOcFacZRp2abSm4UaOKW7+8IyLVcV3L34mU46T5VtTctuqBn2qxuL3Z7Kz5gQhTUatzO72Ngfhht/W5JxXe5jU/ndgHwpV6QwDYG0GAQXs7ouOdunfb81ubbjli5pIACZAACZAACZDAXBKYlkiFQv3Dz38OSJAYKFKhRtdCfzuqbSi4UV0osHhHU7Rr6453GyrVinaVewPKLF6GTvV8t+HXLBTp7HccN3GdOisVFc4lfBht1xqZH1ULVmU7Va/e5RX26zI6mdPPD8SiBsmZ80QTgKItQIo7S/alvBBTJEACJEACJEACJDCvBKYlUkfkYa+6jhe2W1ZkVV2oz2xuG87UWwHywyU3EFVqxBxkHPyMrn/j4q0MggQPl+uufdt2VeC3vEL0griKy9b8Q6jqiIgowIy/OFwP9ztKYPEgARIgARIgARIggXknMK0tqDDL/+pXfQn+Q2IoI/hB43A7ctaLy/xRAw5FuFcj57pMcMNR2G5BwNq1G64NL6rlVK0olBy5tLOn3+f2Bev3MXe/EvgGgb2KKf7AKwpTrKAKgnrFdhtB0HBtROUGvmh6fcSHnWvXnWtPbNoHd9Tzu/dqzzxxdW5Z0HAS6CeAWO3in0N/AeaQAAmQAAlcRALT8qRiin/wLH8XSGfNtQ+Ua7Ro4YpdqdqY60/yHfvAM8Ga8B8iz7nh7m763jYqOE6lUG3OkjLFv1uFBO1a9QWdGqxK2GkoC8KGDymOblsrPhb21wPlvW/zsPHk1tFP/a8PKcT2Dj+Srgsu2+Hlh1/N3b2pgxfxxD1r3RCmkW1lAMFtIjfQrI5zWEqXgqX9YH0YtjLQ5vUWKGlZ15L8AxdLyrIC+Yq6zMDejc9SA3RkcGY8cmWBmv7+kzeie8nyVbZdWvm4dGlpSKKme8fb111a+vj3bHRm/wf96GTDU9kQSuw8vu2JloBRt5a7t5mbaPvz15h+FPJVnvrB7n4S8pubPl1pSGWLnQAAIABJREFUTvYng1qBupH9+cwfBVpMAiRAAiMSmJZIPa57IzV1KSxvb6TFC9nYEFRV/Uy7OVgtlJaS98KieFEz+hLK9GndYp0ZTBdjUnvMA4tA9I0nU/2RGeJeMtJkcZXnOfW6WqraW/VwafPmm62jo6vPPNP+kQ/88mNv+tqe5npO41aABVsZ3p6r457GrZ3lRlCHc1fkWhMBCE6nHSRr3eSTWGepaHvfDfQ9wrhuth3skqs/tZ1KvyFwkDsuNtvqL1DWsjY4TiKYO+1QeVr3o3LQruDjPGqKTAwQ0IynJWg5RWkuKCCRERKdGW8UKrZQ6H+gOu2dZBewoeNKCGoVsoQVgPlR2l1++fhUFEKIG4rpWEr599t5fNssMTUCWmtaxW/UJU9C/7NttwP5Fluz8XBK+D6+gAX76778rfEgARIggYtO4LxE6lCuxi8FR0LX+qGhVS7GRSjv4uooDEor1eGDO7p2pFTz2pEcUtJ68w+/7ZWDg6GeVHwW7lbra7tG3A9vf5Sr9mr6awMWtmrYjREbu7er1jwtzhC5YYeyDM5xNvQaMLRoL0vYhkR1iBTH53fUba9smmuq9xWIy1oWI6MwjWCu1Y37uSOGrODjPNqRvSP05zoCSJq3ongV2/SaI5W2OJMwklC2lbDb4R46LmpLEct6X7S0cWz0u6R2D2OU7htXHGkHOaSwXhiHuhnpsu6K/SRWDXlz6ulDYi3Z8YFQ7OfvWCV2Dml0tEsCQYdHw6vn7m8WNoozbu/LYXId7ur1fXw1AXrfC4Gy7mi9rr2GxjONmx6oqrUdSoP4Y7++Y+pmfmut6iSkx66MB2i0sZx1KT09It+R0keh5EmwDvv+ata67cRf7oF73OxKdxWekQAJkMDcEphJkVrwko4Cdg4dqKMMa3plouYmPJp1q7U78T5kKzG9Bq5zEFvXEx1oXxbhKmou7U9+N6uS/YxDmpu/601zG1nx/AJSA1qO27cQ2ZyI4ETfSCyvqGeE7dpLqesp08dJqxLjLEJWjlR3qv24shxvmr3NzDSrFsumlHmFv3bPrq51GZmOy3byTRuKdZAu6y4H01N4+CkoxU43xYx/XrPMzvzqOCn9zcHs+ybV4jXb19894IGGpnc3VHszcVebVoN6Pt0fbfn768b/C7Uq7m0Iz1h71uvaW+6J31onzVeIqOmnu87J3dxLb984Bs922ZInoeTZtmrukgehr7+wOu3NHbeRbqs828OjdSRAAiRwegIzKVJPPyy2MJAAJIL+cQRIhIFlTnhBgiDh5tE/datdZqXtmBnw3gjUrqIFx2dX/pCTjkz1G88tShmvlUzfe34VvwQxpOKgS/DXYpkapBG8hyYyoVhSXIrFMFNcG2FcxRZOmdazDdg6uKhRi/yT5kvsPHnH+LIRN33vILl3emsO8TunXnNbLcXNTW+/2yrdXxwfqGgv3wLYwVcW3KY1E3NuLYOzWSIpeyfvyMOD7xWJJx6e1Kq9vX9yu+e8ZhbpBLG+s+47WGcpP2uShajO+fBoPgmQAAkMJkCROpjNhbyCOfFOrDbFM6MP39tNZOXphitqSHxhhZnojp4KR7NwZKqlFXE5irTarRrxN7A/+EQ7enPc8hKY4+5vGS5Ma7179RlqwwtVCcO9uAZ1dRvKR3s94/1Yi6K0dZxIWIAjrjrRUokDuOLqHXnhwEpkU+YyFS3YE6460rhMhwO6S60Z5V08i72r7Xr5o50SO0dpfUgZ401GV15Tz+DLPsdBq21tW65mb+QU+k2udzXVK6riw67LPSfwKaqlnrwLdlryJFiq5NlOhm0m+itt/1ZXiOoFg8LhkAAJkECRwLS2oCr2wfQMERCdkRz+mo34v0A7Pk9pYbSVhyeapsTrZsINFWLvYr2VWNy+CYV63KpkyGhV1ZKx3KiSlvV080rqL41bzXbiyMXqK7uKVVmY4t8LTWZ0O7Krxfl1TPHLJmjSGdyxHWhSLUzT8noCXTx9yYElWFCoXT9dO9q4kvpl3aVtj/Su44l7lsz384cDuM/OkZofUihutQUTFutVlHxPgOqvVBXucsWwj9stfX0D7l3R/YI9aa4warict9rHevHxwKTPD9bbhceWH2L2rF4qMEkfvJJnO7Eez9i+2/XUzeqwaBcJkAAJTI4APamTY7m4LfVN5sqEb93HVjt6gleWwoiCRBAeVhRlTtxe15rhBxGJ0NJU3JQx7Ws5RnBtOjWMCpiGRi+e1qnQ5NohWvPr+57pum9BnrPhu9jOzJOq2ChKa12n3oj9xFRpw+wyAHXqwiu8B1diapjsE6T6xuWpm+LrLO4hkFZQZd1lF0dIwBPckdVISVHZUcvpnUwvt1OPbIQeBhWxK3r/XlxGp9h4QRJYagb4pmXbSa/jjutlatjsGM+AXjjVDRmVj9GdIoU9AxoLp4Y9D4PMnfn8kieh79k2gzARvRKLmoeoyrM680OkgSRAAiRwKgL3JUvCT9rI3bt3r1y5ctLaC1RveqDMHZS1/enxyiuyun/i92V6Q8ifA5k3l0Vd4+gpTD9LlG0yO5+3Nd+ps6A9gNAYXYM9d0ItYBwDXaHWZJOw4aGHHkKbd+7cGaXla9euodjLL798vz4eKBwmx7zeVzhQHmejNM4yJEACi0lgUv8Y0pO6mM/PrI5aNnYY1zZ4OsfRtOM2z/LlBPRCsY5xM5eXYO75EjDq83xtYO8kQAIkcBoCFKmnoce6JLCwBIb8DsXCMuHASYAESIAEJkmAC6cmSZNtkQAJkAAJkAAJkAAJTITABDypiDyYiCkXvpEpgUIkKtBlr0ggJvXBBx+88Dw5QBIggUkR2N/fzyJQEZWapbOECUlFdyYalTGpkyLPdkiABIYQmIBInfgCnSHmzu+lSQUR9xMoylOkcZiFU/0lmUMCJEACpQSWl5eNHi2sm+qSqkak9kjV0qaYSQIkQAKT8spxup/PEgmQAAmQAAmQAAmQwMwRoEiduVtCg0iABEiABEiABEiABChS+QyQAAmQAAmQAAmQAAnMHAGK1Jm7JTSIBEiABEiABEiABEiAIpXPAAmQAAmQAAmQAAmQwMwRmMDq/pkbEw3SBCa1tq6IcxptFttnukjgHGmfY9dFAvOYJrp5vGu0mQRIYDYJUKTO5n2ZgFUT3xoMn74Tb3MC47ygTZwj7XPset5v5iyggw3zjpH2kwAJkIAhwOl+PgkkQAIkQAIkQAIkQAIzR+BCiNRO299sxzPHdnyDMJCtqLxadilLmHKddsOXsd95f/3GjRtP6uP9L5S3wVwSIAESIAESIAESmBcC5zvdH7c3/d2q76/a88Lr7O2MW3542a+nhKLtMN5TnpcY4tSDzXoL0tZV9pr/zJsePjpsNbZV5+ztZI8kQAIkQAIkQAIkMEEC5ypSozBccpztMFqtOxMc03w1JW7gsOgGzgSosly/UesaTdQMl/xgI1Ws+trRUc3fUNFWCHfqVuPw+uu7avCEBEiABEiABEiABOaRwHmK1Oh25FwPVpS3EynHqFQotpvKre42t0W2wTcIJytcib4+RYbb8GsWrogLNtTuQrgSjZexkxQrKWPamdHbY9X8IFWiGP627W90KfaCft1p3lr2Gna05TVVPTDFomb9drX5RFeVGR0pzSIBEiABEiABEiCBkQlMS6T+4t3Ws9H7YMbTzpPfcWW1zJ5oZ89Z2VCOcpq32rFTS9yDnTBUfhDYSlyMQbvi11b9wDQQNb3tqLbhRFt+uFQPGqkyg1pNa2lFm5TZXw8CKQJFq9sRdTtrR662M8tyT6qW6enEPq6v1PWQ7Y0gAApvB/rccerebc9vbbpZfSZIgARIgARIgARIYP4JTEukQqH+4ec/Bz5IlIrUuBVGFbeOEs6K0wyjTs02ItJyPROiatXcSrgDRyLyocmaekWRtYwMqNu6lp85/7SWfdlSu3GsrPhARXu53nNMO3mFGUnZtUbmR9WCVdlO1at3Ben6QknJnH5+AECQnDlPNCHFoy2o8bizZF/KCzFFAiRAAiRAAiRAAvNKYFoi1ShUUMkS3YTiaDdWHbgDk+xIu0h7ykBoqutausFvGtRFqt6C0zTW8/zdZUvOsnn/kmuzl4Wxhct1175tuyrwW15hMVmm0HuslkgH8RRHAWb8BeThfkcUPQ8SIAESIAESIAESmHsC09qC6tWv+hLDJkt0ocKSKeViUj85Gq69h8BUfXR2IyNCUaYDL2tnv2O7a1qM3TbOVKdqRWELrlEcUZRU02f5i20vxeG2uRa3t2Z6gyqEKGDufiXwTcSDvep7KvAS17EeElZQQaRXILuDAKwqkOy+m8rR+LBz7bpz7YlN++COen73Xu2ZJ67mIJgiARIgARIgARIggXkkMC2RilBUyFP8h0Q/FyyZsqtOvkbdKuhOy9q/6cnR7LgNeAodd02Fm5Kxg/hVOTBFXre2IewKeX19OBu+ewBPLY5AraUBr33FzjsDfmLY50GCmrEZe6BTg2Blx0OwqdHiQ8yMo9vWiiP7pKKd922+ZvvJrRfoTx0CjJfmjgDC04vf2ebOfhpMAiRAAiRwIgL3HR0dnahiUmnCPwOoV/d7jZnVlCdHNRKo/tX9g6b6U0Ocel3dPqoeBeHSM8+82cLdPIrbP/Ifjh5709cO/AlTWZGWbnqld7nKvy2kzZa+Dx1CbmgahaDybRng+jV7EeRdF4Mx0oiO7m0NsIkB9tvSYQ+9BUpa1hZL/oGLvrIC+cYOmYElQ9bta/+9MV72T9grMCipokeHPX7Ns1o+Lmmh2FRKJjNFpTmFvtLkENrZ6MwmZfr2lbSZd53xTxsf/j6k6+EVe6/CqFvLCaLea+OcC959t/uL3Dj1z67scejkNnX0piXapt4HD5n5zU3vWpqT/cmgVqBumH1OSoYGGx566KGSC0OzXn755fv18UDhMDnm9b7CgZZwNrQ9XiQBElhoAsf9YzgyHJE1pzh+//d//xS1+6rGrc1nWod92RcgY8KgCkRe0cff/M3f/PVf//Vf/dVf/eVf/uVf/MVfDOvupJCHtHn4kZutWNuExjduPo9klsDPCzxjso6eD/QlXH3+5oa50UhsbN4MNjcCqVQ4cEEX7i9Q1rKuiI42xYy4dfMj5iFCZZ0j/ZkEbNjYTK4mvR1+JO09bzk3BOVTo/NMPbqNZAgYTf+40rL91UtYpYWL74NpP38zZZWNpaTNHELOv9j+kPTgrodUKrsE6hP5cy67L2X9nX/eEHTymG3cvFl4/EoevHyk6V1DjmGIhL7vqFXyQBaGDhugOMc99vf3P/3pTx8eHt67d+8P/uAP/uiP/uiP//iP//RP//TP/uzP8O8J/lXBvy34Fwb/zph/cAodMkkCJEACvQSG/GPYW3To+bQWTo0skrsLYtPQRncOzyZOIN6Pl1ZG9J6O2Lm9mv4kloVNGnaxtM3a21Vrno5hwH4Fdoh4YsdxNvRGBWjUXrYRbIx3+BID8R5FWCRXOLD5Q8dU7ysQl7UsVeW3IdxAQnVrdbNnmayxs1Zkd4gd2UpCR/E617HlWRSv2ikBrOFT7g1tqYSdhPmuvWip0w4PXE/2VRAfGHan1WEZcfvmbrXu7mIZnz76xhVHyU+pqfjAXl5Lipm3flZOGl7cVW7giVNP93mwluz4QCiWtZlCwNUltXsYq0J8zcC2j7mQ+Wvh1XP3NzMg4jAWt/flMN2Fw/XX933ZkSPyvVA7jHOvoXFv46YHqmrhtzzQKbyG13dM3cz5nXoQlV0pxsIcY+LMXpYYnlUNKjGx5MGzDvv+arofHjyQwYHrl+7pN7Mjp2EkQAIkcFICMyZSTzoM1huPwF6yr8KQ6ebxGkxLy85iVhWLujoHsXU90YHpvmC5SpIfd610heGmDZj3KNxW1UYqI7uvDWg5bt+KnPVEBCf6RhaciXrG2jJ7KVWCmT5OmoVY1kJWTnv0HMRoaK1jz14cWixLAjrDxxa8dbu9q0+LL+m4bCfZWQwhxTEiqkMU6osZyFgVWxgnDUqx002xpE3o7D27ulYOc5zu8F0C3xygtJKm4jXb1989RMrvOe6Gam8ijjzQP7chDQf1fLrfQCvuWwzhGW9jEt9s29H08A0g2cFDf4WImv62VQ98KYYojr309o1l8UwXLnnwSp5t7MS35EHo6yfQaW/uuD2/QjfTY6RxJEACJHAqAhSpp8I3l5UzuSV+sSY2sIIOmMghQZBw8+gwTfj3Bhzao4Y9xbojULsKFxyfXflDTjriDzWeW5QyXiv5PQjPrzZE6JzkMHtQdFeGYBKXITJ7R1g6rmwfXLkatJxsZ7Eiq5PYpqNgIeKKN6+kTR0Dmf5O20n6KdbBl4246XsHyb2zV11H/1pc6jW31VLc3PT2u63SLcT9+xYDob3marrWMiTodZ2UXZN3BC2+VySeeHhSq/b2ftGShUo7+PEOA7Hl76z7DjYDkV/gy0JUFwoGB0sCJLBYBChSF+t+d43WcV0rwIz4mNPNXW2kJ8lseFCYie6kU8xwZCoTYCDSareKjbSG+cXgE+0k8+9p68V3zHH3twwXZuryLJTVvwcR7sU1qKvbUD7aBYhoBy2K0nI4kbAADUG0VOYAlp/tXU/DGJLS4ryMFVRCcu57uyIB1bHjsmvrTpjY0MsqtWTUd/EsYs2W/CxbdpS0KZpV3JNa/GUFT5MwX2/QldfUPnjsvBEGrba1bbnaFiOn0G9yvauvXlEVH3Zd7jmBT1Et9eRdsNOSB89SJc92Mmwz0V9p+7dw62s2/pRK9pa+YIg4HBIggUUnMK0tqBad6wyPP261zf6xEsTZkRjS0x/RVh6eaFoTr5sJN1Tyww2IBMW0rYRyQtIN71H8l9UhurmkZT3djH24zBG3mu3EzYmf3rWrFVtCYPdCk9m7/ZlM8adb6sIdK1vzmmb0z/ambSZN60n/fHNfCSfAcIaMK2onm4hJNIIJOehnlTY+2jvESrarQFqjpM2oKbdkiLs6rTv6e/LkYEeJipLvCVD9larCXa4YZnG7JU8WInQd85MbwJ60XoCMx2CEfYvxwKTPj5IgitGtnJuSBSbpg1fybCfDwTO27070bs4NJxpKAiSwwAToSV24m2+v2iFcXTJucW71yrCT8OibzJUJ37qPrXb0T4rJUhjpBkF4WFEk4XX66HWtmdwy/2VSIXnrazluZctNpAimodGLp3UqHH5aE9f8+r5nusYanTSq0jQoW+puJpbmQBByYC27SZd4S1yVxen19GL/uDx1U3yd/qrjwO3qaYmV9FvKKm1plHd4gjuyGikpK6GuTu9kej1w4b1OI4+lZLqf0Sg9DCpjV/SPTOAyOt3Q+lOWmgG+eYhsJ72OO66XqTlVhWdAL5zqhozKx+hOkcKeCZ3GwqlU7A4ybS7zSx68vmfbDMxE9NaEfBaiKn8+czlsGk0CJEACIxOYsX1SR7Z77gpObM+wvpFj9wbkFfdwwB4xBwcHA/dJ7WthxIzpDSE3QOIBxt0RE/IxXD7WQZv3MR+ps6A9gMQYXYP9RHZCHWDJ3GWPgW5qY4MN3Cd1anTZMAmQwEgEJvWPIT2pI+FmoTMigD3IgnG7grfUePLGrcjypyFgtpQSV/WFdHOeBg3rkgAJkAAJTIQARepEMLIRElg0AtnGBYs2cI6XBEiABEjgjAhw4dQZgWY3JEACJEACJEACJEACoxOYgCcVkQej97fIJacEKotJBVsTmYqY1AcffHCRUXPsJEACYxHAz6Lenx4PPPBAmszf79MH2sR79jpWFyxMAiRAAuMSmIBInfgCnXHHMBflJxVE3D/YTKRma6fMwqn+kswhARIggVICy8vLRpBCoWZHLlHvv9+I1B6pWtoUM0mABEhgUl45TvfzWSIBEiABEiABEiABEpg5AhSpM3dLaBAJkAAJkAAJkAAJkABFKp8BEiABEiABEiABEiCBmSNAkTpzt4QGkQAJkAAJkAAJkAAJUKTyGSABEiABEiABEiABEpg5AhNY3T9zY6JBmsCk1tYVcU6jzWL7TBcJnCPtc+y6SGAe00Q3j3eNNpMACcwmAYrU2bwvE7Bq4luD4dN34m1OYJwXtIlzpH2OXc/7zZwFdLBh3jHSfhIgARIwBDjdzyeBBEiABEiABEiABEhg5ghQpM7SLem0/a2o3KDsUpYw5Trtht+Olbrz/vqNGzee1Mf7Xyhvg7kkQAIkQAIkQAIkMC8Ezmu6P2p6zUyOOfWg7igF+bW57+qkxhe3N/39dZyXFZ4XwKe2M2754WW/bicNRdthvKc8LzkFus16C9LWVfaa/8ybHj46bDW2VefU3bIBEiABEiABEiABEjhPAuclUjFm2234NctoUx/+wNowDn2FUfFiHCLNQ7hCsyMToMpy/UY3lagZLvnBRqpYdZ2jo5q/oaKtEO7Urcbh9ddnLTFBAiRAAiRAAiRAAvNK4BxFaorMcqrWbnpy3PtYhY9rbCauWzU/SJUoBOu27W/Aq5wfBf2607y17DXsaMtrqnpgikXN+u1q84muKnllpkiABEiABEiABEhgPglMS6T+4t3Ws9H7wORp58nvuLI6DE4n2u1YrrhUUQoz++lMtq7TK76ywsNanKNrEtIQdk/OFwFgCr+AY6XeEB72RhAIpx2JknDq3m3Pb226czRomkoCJEACJEACJEACxxGYlkiFQv3Dz38OvSMxQKTG4aYXin0ylZ+K0SQ8VZutY1J1SqnSwsm1eX6za43Mj6oFq7KdqldfLU7o+3UZoczp5wc4BcmZ80QT9KItQIo7S/alvBBTJEACJEACJEACJDCvBKYlUkfgkYaZjlA0D2AdqfA8FoJrNFyuu/Zt21WB3/L8XKd2rRsrjC0V9FGAGX9xuB7ud9SFidUtDJRJEiABEiABEiCBxSMwrS2oMMv/6ld9Cf5DYvGojjdirN/H3P1K4Ne0/9RexRR/4BV2P5AVVEFQr0DWB0HDtStwo/oSIKGP+LBz7bpz7YlN++COen73Xu2ZJ66OZwBLkwAJkAAJkAAJkMCsEZiWSMUU/963t/DfgLn+WeNwXvZgit8LlAcJmgY8iCXQqUGwsuMh2LSwbqrcxji6ba04sk8q2nnf5mu2n9x6gf7UclbMPRsC8lSP8OiejTHshQRIgARIYF4J3Hd0dHQa22fhZwBPY/+Z1R0JVP/q/kFT/andTr2ubh9Vj4Jw6Zln3mzhbh7F7R/5D0ePvelrh/2Eab7vVRozkDY45H3oEHJDsxbhIfa3tciG69fsRZD3Wwz20MG4S2mZ1AJsYoD9tnTYQ2+BkpZ1Lck/cNFXVgArz5LAicxAvbFXMebXVJUVbEUbsvKZ8alheNftW2Z7X8nOCiPdXV62YtiTIjhSMno4slquCEGXKLwMpW167CSbuCW1einlXWcmZXaWQ0gaOqbrgpFM9hAYii6j3/8kyC7H+kFNyxRv2e2V5M+np7MBp7DhoYceGnBxYPbLL798vz4eKBwmx7zeVzjQCs4GtsULJEACC09g6D+GY9A5x5jUMaxclKLYjqq4OgrDhq5JF0gNgnB0DV8zmtdEn+rvG9abf/htrxwcHAwqr380YbeKBVtpwMDAkiNfiFs7y42gLls0YNvXJqJknU472IaMw5I4EU86S0Xb+LGGQHzG+Cy+2XYaNVs+lDtOpU80qmhnz3GxI2x/gbKWtaVxtKvcGw5sCMU5jTZROWhXsB1v1GxC0smQId2CllMI+U0EX7cNURPKIMCKtdz4FIY2qOL0WpypirRc9p5q0yQjboXqRhCAFVoyELKiIyWMGHWKrvdSSjvJlrrZEIZCGKlrFjo5gWir2VnzA8Sap38jVgvfLeuBbNmRPKj2tmwuh7+QaMtvdxx5bm8t+3pPj5N3zJokQAIkMLcEpjXdP7dALr7h+M0qteZNUKECmb1aTxq0bEt14o6K93bVmquFFPYrsKPb8vtizkYa1WAv2x0s8zIq3HeXerFDyXVMdZHpXQVKW5b6URguuWKGVUu2RxBDxCAo3qiiL6HD6068G3VFUfR1IWYlu9XCStgqrWPTL/0jabr02nLRYoQF20voJjugC818dxwfmOrZpZwVaqklu1fs5gUHpWRHiGBjpety/xAyCMq2l1TnMD4GQldzA05EXbUjCaHGARVlislgTU5zy/f07/qKE1f/oJxOCDo55JIubH77F63ljQzocbGz8QsdyzdMpPpig+DoSYAEFpUAPamLdudFNlWXQs/TImKw/+9kXCAuI6uKRV2dg9i6nggw+7KlduNY5d5H+XHXSipYS3qKwm1VbZTrtwEtx+1bkbMO36ccyXS/LDiTH5TtEpGpPi5v3dTHK5SV6CyoP7M/msjA7GJ/It72vW1kmxn8bGcxiOF097R8hl1cm9gcFzO8PT8e1t/sBHLgV96zq2t2vFdQ0iNC6O++E4YKAdO2JhzVNhz4/FJ3oIwr6vu+ETWxoS+c0gAatjt+rVHfl4SlbobwtE/2y1K/vbOT42z48Wb+kMj3t1W/vgXxLjbi8RIUay425kOGzP7HTX/J84vffWZnMLSEBEiABM6EAEXqmWCerU7iEIGb5XPZpzJU3GYH8lOu0H+Jl62kPS3RitGf/WW041OCB0Y/8CsPyvXSKXBZeYZfkNC+umq+C+/ozWnVIKJUvID6VxOG1U26M+K4awY/V6sQcGmYQZIJnedtVg2uYa2f5ppI7SR0tct5fOI2LdfTm6PZlaotXzwsfOeREAs5xGUe9oWZIGxaX3ZWKs0dGGEhY8fb9CV4N71fJzZnjipCze+v62AXPd1vIzqmBX1vvqjgPumfhs5/fy5qbuLn5TrIl2+Tk/4yOUfcaCoJkMAiE+B0/wLefdtdy1WFTARP4NBi7jp2yEpmJ60lO2s5n9cW1RhIRGb3T7929w+faCe1sPuKPittGa5Za71vYtSquZV4dy+GKzc+SGVzvB9byyMLYMddS2IVSkzpy7JXXceBHR7BAAAgAElEQVSEMfResmvrTm6DvqoL70apXb01Tn2O7wyeRNYiJFfaOgWEIaaUj3ZIhQW9JP5sB7twyCGPJb6H6emCJBobj5nCg5rBMRP9nS0doipfKOF7zi4yQQIkQAKLQoAidVHudDpOuLtUuK3n+hHFuR1bl4+Z904rDnvHohAs+CjO34sk2g51N1jPFCMSFH7G9k0s2Eo008DmEFqqqs5gFVnSclEBiDuzmX6iY/WVXYUOwOz2XvIxj+hYu5oHHpSbgSVGhpDKjC8vaHKjVtvoCx3tUFTAUTvZREyiEXTcatzeSgpLkKg1bKTDujz2GoaAW1L8MjAuhGO7kALwj8bFx2mESsYy3z3III9Qad6LSGg07rcehg7AWLbxVUm+Qems7r/EqBkuTThqfN750X4SIIHFJMDp/oW775ibziLhJPRtAlOuiHNV0Z4JrhOeCLCrO3Ufjeu8tBd43eIo+S1clCrfgAkiEqGlw4RzX8txC4u0sql+rExy0YunPU9JqB9+VBaRkKZrzJzmv+Y14O479RW4IZtyNTVeJs57hHhW2akojFTLDenQ1nsC7FaxqRDW4KdX0n5ra1GaZQpnzUwyId7rPYQqpG3KfPGYENKqw99lMZxnOtJe577p/u7qCPaQRe4OYgPWUc/s+tBd5GKeOfWG6+t4U4wveSwlPNdEqWaPmY5RuYWJfvkLcNIQVZnuH/y17WIC46hIgARIALvdJfsWnZTFpLbCOmn/c1NveqDMHZQNqNLjlVdkC6ph+6SeCNv0hpCbI+F62Kaq6JPNLw5IQT6Gy8c6aAdUntnss6A9YPAn7VqijRF2OdbNG2DCvGafFN0kxwsbuE/qJIGyLRIggfEJTOofQ3pSx2fPGtMjIAtHxm0dbqkJeIPH7ZXlDYFkIwV9knqdyYYESIAESIAEJkCAInUCENkECSwsgWxng4UlwIGTAAmQAAlMicAERCqculMy7oI1OyVQmOQHqOwVCUz3P/jggxeMHodDAiQwPQL7+/vZj6Dih1GzdJYwv4oKA8wPovJnUad3L9gyCZBARmACInXisY+ZcRcpMan4jH4mRXmKNA4Tk9pfkjkkQAIkUEpgeXnZ6FEo1OzIFCoSRqT2SNXSpphJAiRAApPyyk1ApPJmkAAJkAAJzCyBt7zlLf22/czP/Ex/Jv2j/UyYQwIkcI4EuE/qOcJn1yRAAiQwdQL9erQ/Z+pGsAMSIAESGJ8ARer4zFiDBEiABOaKQFGVFtNzNQgaSwIksHAEKFIX7pZzwCRAAgtIwGhTKtQFvPUcMgnMLwGK1Pm9d7ScBEiABMYgMFyhmoBUhqWOAZRFSYAEpkyAInXKgNk8CZAACcw8gaI2HZSe+UHQQBIggYtGgKv7L9odxXjwGYMj2wACaexLZcZ5yvQ02pyUbRevHdA+5f06MZNPfvKTJ657XjbPSL+z8DeCTegMjdFfs38figlUN/+emEy+kgAJkMAZE6BIPWPgE+gu2vLjNb9m9TZlPlGMtsDr5cuXe0uc7vzw8HDibZ7Oootc+xxpo2vbti8y3KmN7RzvWjYm2PA3f/M32emICfzrYf4BMa/9tfR10aw8SIAESODMCMynSO20/c19N6gvyk+2Y7zbtr9hhhvtHFTdPoXa/8T85V/+JT5XJusPm0absHzidl6ANjEE0Da39ez5mK7Pvt/zGu8E+52Fv5G//uu/NvdurFcUxgEUxVdDhq8kQAIkcC4EzkukRk2vGaUjdurQm8gJlxslDsK01IV9j7a85p4eXaUeJEpUZZn2mu+v1rwl329Z/qqtop2oE0VemOOoeM0nUrneaT3x8X/5G0fq17/+Z//qr/4KChWfNxN8nUabk7XwIrV2jrQzpXWReJ7NWM7xrmV/6ZjuH/fbKeD0HPgXBjnm35kskf+zwxQJkAAJTJ/AeYlUjMx2F1KS9t7TTntnyQ82MLsatzf9ZiT+YVGoqh4EqfQErFXf3YKsd+NbHbcR5HP9UdM/FLcqPkXkY8la/TffXcNH1Kc//enPf/7z2UeL+fQyXZ84jdYm3iZMOrE9F76ucWeePR/0mCmtUz4zF/4e9fCZhb8R2ABPqjFs9Ncv+IIvQEVzoFYxUWwE+cVTpkmABEhgqgTOUaQWx5U4VqNNL4Q3cS32byq3utvcjlFIuxIlQi5u+b7JqeTqrdjKXKatWn3VGG7bS2r3MFZ2FO7Budw7RmejrqJmWPV8iFLRpq6/2mk2ldsshA9+4qe/4s6HZZEUBCveXhEJqBPyenT0bc992/rvf+Qf/4u/0Jl6MVVSWExwt9bdT3708Wc/r/7Ra3/pe7/01/75f/rp/9uYlr7+o9c+97d/P1QPf/r/++If/t7/Psl9ae9//7nCaVqW76ciANFwAqlxqi7Tyg8++OB5dZ2aMK/vuGsniAed7Ghhw7ENGq1plKh5vf/++4unWRpNIX1sgyxAAiRAAtMgMDWR+sEPqne8Qyx+97vVY48dZ7pM+OfT/Z1YdcJQ+UFgKwk/DdoVvxY3/W2rHvjQbqJW90aIyjyu19m63mmHe3Z1zVZxGFeW402v2YGBub85bjWjSl3GDwKHck0p0bIiQ7Pjtf/k977qu37hl37uv3VvXIVDNTs6H/0nv/2an/zmr0TGI9/6kXXUOXrp1m/81td/4//0Zbpu1sgjq+E37P3ov8NH1qVHf/wfPCoX/+sHf+BP1v915Ut1wT/avrf839x/sH///X8U/ei3fsqEKeDKP/i539XXv/Tdv/lNX6lTfCEBEphFApnozJSoSeCPHodJZ3ZnhbMcJkiABEjgzAhMTaRCoX72szIMJMpFahzCbyolch0mZ+awXA/xlzismlsJd2KRZfaapxWasitVe3s/KXkx3sSVjHl8HZIL9/HermoEgfaYejfbTqOGWNRwd9lNfK5xtKvUUgSnKxjhUySTmOknys//ww//fOJMFQeq9pu++ifwCfTi/1V7y0v6FNwgbsOfEn7amyqJV/2zj66+QT6n5NNKMuTAuZya8y9b/5ZHX9r7f5Dz5X/n67/+z77rx3NJ+v/+ZPtT/8u3fFVWz9TmKwmQwLkTSP9lyA0xOXjNDvyNI63/1uXF5KNCViCrjJwszQQJkAAJTI/A1ETq8SaXadOSWnF8oNR11TmI1VLJ5QuQ1R+BqipuEnXqrDjNHfGatkK17ifz+lEYLrnB9R3EqA7Y4OC7fuG7b1w7OoLfFApV3Kmd9pO/LZ811/7+L985Onrh42/+dbv19q/U+lUTPPrdD7z9T77tPa8Xd+lLIkr/+CO//D0/+vmM7q2VT+v0q576ldU3PCAFHngAH2Of+8EV/T0jKfeqp/7xAw88kFViggRIYPYIZBLTJOTfhfTItGmaIe+zNwJaRAIksCgEpiZSMcufTfePBNNaLk7gd3ajTs0WV2IYdhxIMfyv2QyjVVFl0XYYI+NiHBHCSvNF/TImEaZhu+NAp8atMLKqrrhRq27DDNhUwPCt5c1mJGySAx8n2qWK9w9/54c/nPhH4SXV/x29+r34BLrz649+z0tHf+9V1f/4idWf/YTxoSbVv2H5O4zChAaFCL3vi7/v19YelWCA3/03/+xP/sFPXn912o+o2PsgUlHuoR+PvuWr0vzf+YmPfAq5FKkpEL6TwIwSyKQnEiZtEqUi1RTASLLEjI6KZpEACVw4AlMTqZjiL5/lH4TQdqrKTxZOQYBZ+zc9Lw3KFB3m1OvYa8nzkLQrTuJTHNTY/ORLdOmeGZY2Wu9CVW/EgkIyEHVaUy0/caNKVAAkrRGmdu3Gso/zoH6tMN777vuy7/y2//g/Q672HfCovu4Nv/afj44+u/O/feiLP/YD/4NUQyl5+933f++fiPBEEh9UP/s7P7n59370YaM3xXHaJT5RQGtUeFJ/4HW/JLWT41Xf/1aK1BQG30lglglkitPIU3PaI1Iz+7PCWQ4TJEACJHAGBKYmUo+xvWT1OnZZCkzMJRZOqWW3Ua93N+JsBEF3zgU4y0ddHIxV86FNs2PVBwpZLnbgFvelQsCu32gnOlVrzfs+8dNXXoAPVetOE3oqSZ2SxMqPfNO7vv3hI/hJf+a/vPFn/kvagS7+jX/nO43CjP/svsY3/4tvv5Rehd9UNGruIX3ggcyT+pP/+e+/Ni33iR/b3u8ql17gOwmQwGwSMOrT6FRYaBL9r+aSGYKpMpvDoVUkQAIXjMB5idQLhvEshiNytr8fkbOSq3WmUl/9vXe/+nuNC1Uy9ZEljNMUr5e+7l/+zt9NaphMaSI9XveGZ1+XpuX9q280i6dwteJjSryp5hULpT7xr37hn34IZb7s//jBfL1Vdx2ekQAJzBKBTGuaRPaKRDFtTDY5s2Q+bSEBElgIAvnC8JMN9+7du1euXDlZ3YWqdQagMrmZiVEQztJZIsvM+GcVsxwmSIAELjCBHtGZqVIMGemeU5NpaJhLF5gMh0YCJDARApPSPPSkTuR2zEQj+PwwctMkej5OskyUKV7qOZ2JkdAIEiCBKRMo/iOArsxp/2t2qZiYsmlsngRIgAQSAhSpF+pRwGdMplMxMCNAe2So+RwyxVDGnF4oChwMCZDAyASK/wJkaZPITtFYMT1y2yxIAiRAAqciQJF6KnwzWBmfJUUB2qNQM4PNR05WMstnggRIYEEI9OvOYs6g9ILA4TBJgARmgQBF6izchQnbgE+XTH2aTxpzWvzUmXCXbI4ESGDeCAz6B6Env+d03kZJe0mABOaYAEXqHN+8IabjcyXTqSjW8zGTXerJH9IgL5EACVxUAkP+HRhy6aLS4LhIgARmhwBF6uzciwlbYj5dMj1abJ0fPEUaTJMACfQT4L8S/UyYQwIkcMYEKFLPGPhZd1f8pCkVrGdtEPsjARKYVQLFfy5m1UbaRQIksEAEKFIX6GbzE2iBbjaHSgIkQAIkQAJzTmACIhVbts45hDMyn6DOCDS7IQESIAESIAESmH8CExCp/MWpUR6DSf36wih9sQwJkAAJkAAJkAAJnBeBSXnl8MPrPEiABEiABEiABEiABEhgtghQpM7W/aA1JEACJEACJEACJEACIECRyseABEiABEiABEiABEhg5ghQpM7cLaFBJEACJEACJEACJEACFKl8BkiABEiABEiABEiABGaOAEXqzN0SGkQCJEACJEACJEACJECRymeABEiABEiABEiABEhg5ghQpM7cLaFBJEACJEACJEACJEACE9jM/6wgRk0vXG74tbjpNVU9qDtn1fHZ9dNp+9u2v1E2suxSljBm4fSm8hq1zpbX3EssdQwdU/L6jteMuoZguX6jZisVt/zwsg+OUaFuoWTSjOSkvdh573F7M1A3/JpVqMEkCZAACZAACZAACUyIwHmJVCjOXDoV1NAIw0LpYIRiF6VIIiUhKvURbYfxnvK85BQw/Bttfytyle1CwVtaeiooyNC+sSyFNC7I0J3rua6PtvxozS9o4aRu0qi8SQv5qVXz15veVhSsmTxc9Xervk+FmjNiigRIgARIgARIYJIEzkukYgypMIJzbrMZ5QpqksObg7Zk+GFcMDQToEq7PAtXlIqa4ZIfbKSKNblW8zfgDYWmjJqb8Uq1qwZOIHMThRo1/UPXX+2pLkXCTa+gSU0LTl2/o7q/bQyMPO2sTSzc9r3t9CaaGnwlARIgARIgARIggQkROEeRmo7Asi21G3eUo72AiR5Kp6ShuxKXa8VJPH/Z1HN+bZ6lEpyUQS1hkU+mp3CgH/PkTvPWstewZXYe8Q4mKgB8bq8k6bxkMRWF23GU+16j5uVgpXhd0gMAalELp+0gVzc8sgXzehvlOQmQAAmQAAmQAAmcmMC0ROov3m09G70PZj3tPPkdV1aH2RftRFbVxcQxJNGBGwSiReG9C1qOX4n8ZsdtBBL4CDW2p/QEdtJY3Ao7a35Q4hcc1tuMXZN587DTZVTuSYV4XPOhEdNjpd4QOPZGEICGtyOhp069ftvzW76bFup77w2PiDv4RtB1WEuqWeJJRRmIV9u2/Hr+faBQsQKhXIwZKFxikgRIgARIgARIgAROR2BaIhUK9Q8//znYhsQAkZpOMUPraO0VH3bUHrRXOqBKR13ejytusjTHWXFU14y0fdmKm753kPoU03pz9W7XIMETi7VgVbZT9epdyhsaEYfM6edHQXk6G6Lroy1I+7izBLd06SExpnZDVpvZlt0jUu1VP6gU12zlhfO2Mt+2yRKnb36RKRIgARIgARIgARKYLIFpiVSjUGFrluiz20wxy3R+FpEKx2ExYhK+0r5ahQwj1MSn2Bw0H10oPeNJDCNcrrv2bdtVgd/yChwEUff6fDOWdNC4fntFhOzhfqz64k2LtfU3AEAuuF27XLn5NwS0Zk7EXaqMAVFf2Kq3NdffEGb8kaB5JEACJEACJLDQBKYlUl/9qi8x8hSJoYCdesNNFk6JZzSMVsXbF7eaUaVeq1Tt7bDdcfSi9RBCrXu6v91Zrcl8d8ULD2Pl9OmzoR3PzkW9MsnCMn2n096Fp3PV91q+5yEn3WZLezE7CABd82vKuDytbPU9PNDOdQeH2vLUnupswPMat2+l40t8rl3OUXG7Jkfqyu1aU9VVGF5as4RL85W1Wa7ewUr2paIzNeXIdxIgARIgARIggckSmNZm/ghFhTzFf0gcY7FV89Y6zc127NR9JDw5AqVn+eWSwsJzHP6BBfFaPOyKCuWK1zxwva758WKpGU9DDmKwXpDpUW2vzL8HKzsYdevYhUlxtGshEiJZTdVYDsXtCumZCtwcAHyq+tiKnI3u/U0hN5vKHYOhmO1hj6qlAcEFeadMkQAJkAAJkAAJkMBJCNx3dHR0knppnbt37165ciU94/tAAiOB6l/dX5ysL2sbfmR1W60o2ZoqiRDQDs7qQYj1WHrdVWA2TCiGUmjfLeSvjrgo+XGEHk9qseOCJ7WYzTQJkAAJkAAJkAAJaAIjaZ4RWFGkjgBpEkUmdcMmYQvbIAESIAESIAESIIFpEZiU5pnWdP+0xs12SYAESIAESIAESIAEFoAAReoC3GQOkQRIgARIgARIgATmjQBF6rzdsf+/vfuLbew87zz+Ogiwvdlg0SYQz8gQbG2LYJHAGkYeCW4XTZuLcUEa4sBbwGhuFqNBdDiFgbkJ0EQ3OryRWyA3Axg1KWPkuwQB2mAomMRmLpp2gcCQZPmMjARF0cXYmHp0KCTpZtFepFezz/Oe/xQ1MxYPPST15cXo/H15zofU8Mfnfc8Rx4sAAggggAACCJwDAULqOXiROUUEEEAAAQQQQGDSBAipk/aKcbwIIIAAAggggMA5ECCknoMXmVNEAAEEEEAAAQQmTYCQOmmvGMeLAAIIIIAAAgicAwFC6jl4kTlFBBBAAAEEEEBg0gQIqZP2inG8CCCAAAIIIIDAORAgpJ6DF5lTRAABBBBAAAEEJk3g88MfsPzxq+EbOQ8tAHUeXmXOEQEEEEAAAQQKESggpM7PzxdyKNPdSFF/x3a6lTg7BBBAAAEEEJh0gaKqcnT3T/o7geNHAAEEEEAAAQSmUICQOoUvKqeEAAIIIIAAAghMugAhddJfQY4fAQQQQAABBBCYQgFC6hS+qJwSAggggAACCCAw6QKE1El/BTl+BBBAAAEEEEBgCgUIqVP4onJKCCCAAAIIIIDApAsQUif9FeT4EUAAAQQQQACBKRQgpE7hi8opIYAAAggggAACky5QwM38J51gjI6/1/V2HG+tPOCQklXJRLiRzL5l3Ealt+U2D6L9yvVWXdoIt7y06zb9XIOlmteoOMYEHa99wZMt/cy+mS2jZnRJ/CxO+uxBd6NlrnuVUmYPJhFAAAEEEEAAgYIEnkpIlXzjtXvZM3BqjRHEHb/p3p4LA1n2ySZrOoqSEirtw99pBwfGdaNZCZLe9a635ddMZKjbGxFuO9fndCPZoqUxdPeSTa5hI1uev+JlsvBJf20heg75Uap4V5rult9aCZfpK7i35Hkk1NSIKQQQQAABBBAoUuCphFSn0mhV5CwkRO4vtwYWDos8x/FuS2qTG+0gc4xJADW25JlZo2LtWa+1FifWaF3FW5MYKpnSb24Ey0u5PWRGYmuUUP2md1Tzqn276ybtDTeTScMWynX7U3b3dsID9F1brI2OcMdzd06m23Bf/kUAAQQQQAABBIYSeCohddARZ7Ja3M0sGXZ3bqXX1oQkYcg1b4X113h9uosuKaVZyianoGm7uX3Pbcc7DHrep75MipQ2seuBpJ3p6WFl8utu8/ac23C0d97Uo3D/+KDvC6Cf1l795oXWctp8OHVK1rSh1rXVWB0/cOLhb3mZwzuxmgUIIIAAAggggMBZBUYVUv/mXucN/6/lqL5b/vM/na8+5vA0bu4tSXlVuo912utGvf/+nvFaLUeLeRutWqPVKmlH865vymWpGrZL0tmdhKeq1wqfR3Lbjl9Zk+A6/t39ejr5kQ9pnBQ0Z8WTjBg/lusNPVtnrdWSc3R3dehpuV7fd72OV4s3OvFTInoruzDoBbmhFtKZP2uaAyqp+lS1huOUvLoWvftGthqzKEE55c8+BdMIIIAAAggggMCQAqMKqZJQ//U/fi0HJxOPD6nB/WCxFl2CU6rUFtu7UqDT8Y7lmu2bdi6UTGmurEuc8pKzdySrd30JSUlCDRmSKFWaC0z5ZK92uNU4/RuPfNBjsoFVT9Ct53rkJSPKQ/v000cmeZbXlMHfkgaC3qxzyjBRabztNLQe6pScvpDqSL5fzF6zlW6cPmN8uVW0RIu+6UqmEEAAAQQQQACBYgVGFVKLPcqTrQVHfUHLJrxZKRraqt/tk3uM+RLJ1+25es3Zd2qm5XXczMjRJHr3nUI8ikHW7y9rkD26H5gTyTy7tx1MKtXZTNnVusWW6XBYaS2c0XKpiUZOnBi26m7Fow76Do1ZBBBAAAEEEEBgOIFRhVTp5U+6+x9/hM6cc9Du9sphd3/7wFmKriI/dVdnccnZiXfxfb9s7vec2nWtrPr7cscle2G7NHtqA2O0wl6ZZEcu9Lp7Uumsem7Hc11ZEg8EtVXMngwAXfEqJix5lpKr7yWvly+V5WG2XHNgemtSeQ26SUyPaq654qiWXaNHXMrNXVOV21hEw0u4LKZem1Wzd7CyI2jjZviJAAIIIIAAAggUKjCqkCpd/I/v5U/ORC4eqt93o2GRp1zEk2wcTmR30X7/cmml7dkWyovxIIBSecl4433hlBYy5V5OMu42e37a/16VEqjbXvG8xwzoDfy90nLD3utUrqZqBJ5cVdWqVxp1CZHtbKM6rtQOcI3HksqYieghffdNU8sfQ7xu4M+o/ipF2YGrWYgAAggggAACCAwp8MzDhw+HaeLevXvz8/PDtHBO9n0iKB3omb+Zf7azfpCUXDdl9s2y0VtTRSME7GjRpQdtuR7LXnfVCm8gJdPJEAJbu5WMar8P6G0QJN7GVVt9lr5KavaJM5XU7GKmEUAAAQQQQAABK/BEmecJrAipT4BUxCZFvWBFHAttIIAAAggggAACoxIoKvN8blQHSLsIIIAAAggggAACCJxVgJB6Vjn2QwABBBBAAAEEEBiZACF1ZLQ0jAACCCCAAAIIIHBWAULqWeXYDwEEEEAAAQQQQGBkAoTUkdHSMAIIIIAAAggggMBZBQipZ5VjPwQQQAABBBBAAIGRCRBSR0ZLwwgggAACCCCAAAJnFSCknlWO/RBAAAEEEEAAAQRGJkBIHRktDSOAAAIIIIAAAgicVeDzZ90x3U/+rkA6w9TpAkCdbsMaBBBAAAEEEEAgJ1BASJ2fn881ycwggaL+RNigtlmGAAIIIIAAAgiMi0BRVTm6+8flFeU4EEAAAQQQQAABBBIBQmpCwQQCCCCAAAIIIIDAuAgQUsflleA4EEAAAQQQQAABBBIBQmpCwQQCCCCAAAIIIIDAuAgQUsflleA4EEAAAQQQQAABBBIBQmpCwQQCCCCAAAIIIIDAuAgQUsflleA4EEAAAQQQQAABBBIBQmpCwQQCCCCAAAIIIIDAuAgUcDP/cTmVT3scva73lnEbFeeJdww6nveg1lorP/Een3JDOaQdxxvYfrIqmQjbjs+it+U2D6KnK9dbdTnGcMtLu27Tzx1HqebZs5bTaV/wZEs/s29my6gZXRI/i5M+e9DdaJnrXqWU2YNJBBBAAAEEEECgIIGnFVL9pkSnOC3F52IXLtZHmALjZ5qgn1GUjKO0v9MODozrRmcgQdK73vW2/Jpxag2NjLq9kQTZdq7P6UayRUtj6O4lm1ztfv6W5694mawd7Rs1qj+0hXS2VPGuNN0tv7USLpO13t6S55FQUyOmEEAAAQQQQKBIgacVUuUcHMe0235Fa372EXTavVKcxaJl5+CH1CY32kHmRJMAamyIz6wxxm+2Z73WWp9SxVuTGCqZ0m9uBMtLuT1kRmJrlFD9pndU86p9u+sm7Q03k0nDFsp1+1N293bCA/RdW6yNjnDHc3dOpttwX/5FAAEEEEAAAQSGEniKIbVUu1Jq3u4G5bDD3W/vmKWVUvtBeD5aq2v3dNpZ8TRX2R7npdl2W3OSlAeXo27spBxr67C6g12S6f5Ouq3TNnWRjWq9KIElYStpRZ/DBuhkL6e8qM0X/JAiZasStZl2pqdPksmvu83bc27D0d55E9eb5Xj3lx9ZexbYwE9rr37zQms5bT6cSk4/v8KGWinaxhT5tRKKt7zM4fWvZR4BBBBAAAEEEDizwKhC6t/c67zh/7Uc1nfLf/6n89XBx1deLjfbfq/iaCd121+s1S/shiFV0s/9K62WFlklI7a6i57muF5bF2rV0G26EtNadakdurYF0/WavVqjlQyRdNakl1sfUghsdYJyVbKd156ttxpx5VYScK/dNl6r5dhioV9ZK0kf91yjVddebJtW5RnSvTSt+rO20cL+SRJw2mJaSbUBXTJi/Fiu24PXU5Ojc6udfgAAACAASURBVHc1RZfr9X3X63i1eKMTPyVhhhLRmqAX2PCfbliaNc0BlVTZQMKr45Q869w3stUYHZiRHTOQNsgUAggggAACCCAwpMCoQqok1H/9j1/LwcnEqSHVlGsrbW9H0qGRMmpNEliwa88nCB4Y/yBNa2Wp10nhs1Sr2YRZmpWZZTtZXl5s7gYmONozK26SUEOUtJ96UQPp7oHEtTihhluUaq7t+3YulMxeIE9yvxf4aVxz5nqBeeDUrod7OeUlJy70hvsP/69TkWAdNWMDq5Fnceu5HnnJiPLQPv30kUme5TU9K39L8njQm5XAP/AhjbedhpaGnZLTF1KdqtdazF6zlW6ctpVUrMNFWvRNVzKFAAIIIIAAAggUKzCqkBomVDnWZGLgcTvVWtltdzslv7RUk3iVdh6f6IDuC1b55noPApOrcWodtLcSV0llCMGJ8mG+gWSur2fbb/aMvf4o2WBEE1oSnqvXnH2nZlpex82MHLU13QFPGx+qrN9f1iB7dD/QLJ9/ZPe2sV+GT2TKrrlSbvq1QNoIZ7RcavQqN8nBbjvftHG34lEHfSuYRQABBBBAAAEEhhMYVUj97f/0X8J4KhOPPEIthTZ3Aum1zsQrx5kNmlphlcJf0N3yy2uPuVFU+VK5KSMHqlopDHzfONKjXa5pPTLw92x+LZWXSu227feXuOX75XLm+eIjLM2V/GSb5papr4WHFx6JDu40IxiWaiu+JblMv9zr7kmls+q5Hc91ZUl8UVk0ytYLVmTYQ1jy1JEJ4WEHRz05fXmYLdccmN6aVF6D7u34nKKaa644qmXX6BGXcnPXVOU2Fq5wmK8F02uzauF9uyimxoj8RAABBBBAAIHCBUYVUmUoajIm9dEHXV6pOQ9M2I+fbFle82obEtRkgZZUB+TJZNNwolz35PqquFLolcu1RRm3KvvL1U7h3pLG6vdduSBddpDgVjYDSrN922h1srxWL4ctpU31Pfcws1rIlHs5ybjYbCva/16VEqjb1ovGsmtOTksKLy037DhdGabbCDy5qqpVl5OVS83ylU9tUPePx5KmZWuJm01Tyx/DyWfKLInqr1KUzSxkEgEEEEAAAQQQKEzgmYcPHw7T2L179+bn54dp4Zzs+0RQJ6/uz3bWD5KSCrTZN8tGb00VjRCwBc6lB225N4KESFcGD9gbSMl0MoQgHq1rx1QE0pkv8Tau2uqz9FVSs0+cqaRmFzONAAIIIIAAAghYgSfKPE9gRUh9AqQiNinqBSviWGgDAQQQQAABBBAYlUBRmedzozpA2kUAAQQQQAABBBBA4KwChNSzyrEfAggggAACCCCAwMgECKkjo6VhBBBAAAEEEEAAgbMKEFLPKsd+CCCAAAIIIIAAAiMTIKSOjJaGEUAAAQQQQAABBM4qQEg9qxz7IYAAAggggAACCIxMgJA6MloaRgABBBBAAAEEEDirACH1rHLshwACCCCAAAIIIDAyAULqyGhpGAEEEEAAAQQQQOCsAp8/647pfvJ3BdIZpk4XAOp0G9YggAACCCCAAAI5gQJC6oULF3JNMjNI4OjoCKhBMCz7TAV4H36m3DwZAgggcC4F5LOmkPOmu78QRhpBAAEEEEAAAQQQKFKAkFqkJm0hgAACCCCAAAIIFCJASC2EkUYQQAABBBBAAAEEihQgpBapSVsIIIAAAggggAAChQgQUgthpBEEEEAAAQQQQACBIgUIqUVq0hYCCCCAAAIIIIBAIQKE1EIYaQQBBBBAAAEEEECgSAFCapGatIUAAggggAACCCBQiAAhtRBGGkEAAQQQQAABBBAoUqCAvzj1iMM5fOfG9l0zU1lff3nm5GbHP97c7Jrq+vrlAStl88PtG9vm2s3VF3SiZxvRXY6qN68u2H2PM23OVCulTtesrj/b2eyUdK/MyrGfHA7K6O6BQC4cbm52+kQ/3L5x6zAGmJGNZrryoiys3lxdiJfyE4GsgP3lKvW9Q8K3aHazdFrfVplf4uM78jY87ltot45+bS+uyq9wunsyZXc0p/x3kWzFBAIIIIDAOREYXUgNP6mU8bi7eaOb8Yw+oo4PD47NTHVBEqoGqV712ovv38rmy4XV9erm5o3ta6vhzvYTzlSvlSSczry8vm42Nw9elNDV0Sy7ftlsdzJPMjmTw0MdHtw15uJMFPWdeCIhCOOCPs/75vhORzbWLwA3dP2gJJHsx8Q5EkjfhuFJH0fvEJmzb5KFqzdvyrsn+y0o/LWN82n/98bjzuaN6Dcy/Jqaxty7adv6ZPGb8Pju+/o/wkV5I4ffS1dfPNjuOKck2vAw+RcBBBBAYHoFRhRSw0+8mYWL5vBuXNkLS3rygRQWUT7sdI7NwjUpwBxuS6nv4urlFxZmLna2371z/MLlmcxH5vGtbfXvbm7al6Fza7NjP9Wm4kUZGkq+A/y4o5XS5IM/my6kKOWok+SD943Wrt5/V9W1SKbP/P6L6s8DAUmKl9dvXg4hBlZSn8zoZIXexk37DpROlYWLC4d3DxfCjo7od1y+i4ZvwsNO91j/H5D/Ed7ZPpR36csLC85C51bnzvECb9Mn82crBBBAYKoERhRS0088LZ/EFZVMv//xnXfDPmj5pLIfSDa5LlzV2unmOzM3r8YfmdEnWYiefgTGVRmp1thVt25sagGxNGkvzvBQJS1Ix8VpLXT1VZ4+zJIcH+sQiZ7+e/zJsSmdKLpmN2YagU8rEFfo8/vJb6YtxOpSTcC3wjK+lP/TKmn0XctuoHH2mh2O8sLqekX+R9ieYXRKnpQ5BBBA4DwIjCikptFSgunNq2G1TheG/f4zX/uyTUvGBIfSw5f2Pofkx1HtJOrfX1/9ZNOOSb14uHnjxnbU+bi6EA1U7cVDV+3O0p09Sa/b8FDrcZyX0+5J8DS2dHqKwcxC5UVz0JHNDg8OpWd14kL9KefF4iEF0vdh3FCmIC9lVvmF/eCf4lVpP74sCWekOFrV1enXyHjj6Gf8rdIG05vRgFRZGMXVi99YuKv/EUhG1S9d8j9CEmTtws6PjxcGjWvXlTwQQAABBKZUYEQhVQqEOmRUupb7B6TKB55eGNHbfvBrLeg5GrHS7sV0lJv91JSioH6eHdr+/qhHUj7Ybv14Yd2RkCUdghJ/e/LSyEfa9rWbiwd6nZZ8UlYn5qqpoaEkS2wm10XZN2nS769zC6vX7ML4n2cvXp456mwfbBu9oE3HA/NAINfZHw7LUZR84vyfsiT+rYxG7Nih5MmY1ECaefZYcqf+DuYe2r9/9eaqvYwyHZeSbGLrqYfv/LwXyP8Itm/BPo+9/DEcnDr4ysukASYQQAABBKZSYEQhNbYKu/P0Y8/Yi4WjAWo2PB3rNRj20TuSz6YXc1U9O2LVZKs52auv7nYOb0p+DfeWHLYQXsCedCnGTz85P88M9ULiEF7jPzNzfJy7ucGHkvA/+SQwpcVne3c10C9UqjObMow1jPiTQ8SRfgYC9lviwsWZw7ulakX7KHLX+B9rv8fMYu43NTko/S0OH5lOfNtJEn3H1JXhNVKaQd+Xax6jsed2r4Wr19L/EXQsysyLfIUKPfkXAQQQOK8CIw6pmapeckHviY+e/MXp4SuRZq+weFOtBp38aEu7PP5YlJ0y/YP5CtBEvLRnhorPTqrR23dtBJBkf2vzTlzfMiI5I5ng8Ljbia9KkQK3POzI1BMvRtweP8+dgO2R17fQwt1Nud4xuoHGjc3k/lKHXX3nLDgD3zTHx1JJPXlniT7FzCX/6aCBEwNUdCyKWWDAdB8eswgggMB5ExhxSD21QJg62wsm5C6nOkztONBSX/oIg6h8bl6Vq3tnPrkhXdvJJ2Z6yZG9g1V8yXC680RNDQWVMNnLpGfCa01ufBLdLPZwWyrWMjJYRvRuxjeeqtib+3A9ykS9R0Z5sPYtJPfhuKmX0Sdf/SSn3ryoI8nfr6xXj+RbkJZCB4+lsUXWhVcWzEHmRhPxEUdDUGX29EpqvK2OKZC7pM1UqvZ/hOP8/wjpVkwhgAACCEy9wIhD6mMLhAfbm3ePZcjaZXNH7gGgn472HjTh4Dfp8os+NvV1kProTc2jcqnFzNe/bv7hH5LPUvsqZSqp8WehXT4Z/wwJlXWSs4+zxQ2z8I2Lh4eSgHXwrg7/lWrZwaL9Swcv66Dh7XcOB99WfTLUOMqiBDJf+fqaDNcc39k+kO+Jtou+b4NwVjroZ6rXXjA9CamP6O5/fCVV/kc4PNZ3bPI/AuNSBoqzEAEEEJh+gWcePnw4zFneu3fvwoULw7RwTvY9OjoC6py81uN8mrwPx/nV4dgQQACB6RCQz5r5+fnhz+VzwzdBCwgggAACCCCAAAIIFCtASC3Wk9YQQAABBBBAAAEEChAgpBaASBMIIIAAAggggAACxQoQUov1pDUEEEAAAQQQQACBAgQIqQUg0gQCCCCAAAIIIIBAsQKE1GI9aQ0BBBBAAAEEEECgAAFCagGINIEAAggggAACCCBQrAAhtVhPWkMAAQQQQAABBBAoQICQWgAiTSCAAAIIIIAAAggUK1DAX5wq9oBoDQEEEEAAAQQQQGCiBQr5i1OfH56gkOMY/jDGvAX5+7FAjflrdB4Oj/fheXiVOUcEEEDg6QrIZ00hB0B3fyGMNIIAAggggAACCCBQpAAhtUhN2kIAAQQQQAABBBAoRICQWggjjSCAAAIIIIAAAggUKUBILVKTthBAAAEEEEAAAQQKESCkFsJIIwgggAACCCCAAAJFChBSi9SkLQQQQAABBBBAAIFCBAiphTDSCAIIIIAAAggggECRAoTUIjVH0Jbf3OgGI2jXNvmrH9559xdR4z/b/FEy/asf/ujNDwYsl0XZzaIt+IEAAggggAACCBQuUMDN/M9yTH6zaep1p+vtON5KoP+umeZGUGtUnLi5oOO1L3i6zUY7n9KcWsOrlOLt9KffdNtz/QuzG0zSdHTiZXvM/m5vqZaYPPI0JFn+4Pdeff1rj9zI/PzN5w9/oJv81nf3Xn3ltdmPV9/71fZLv2PMV9e//PfP3/nZR5edH/7oDfP738u3I42vfOc3UdNvf/8NO/Vnf/vNxz1dtAc/JkqgZ38x18K3YP7Ik1XJRLheZt8ybqPS23KbB9Eu5XqrLm2EW17adZt+rq1SzbO/78kb3s/sm9kyakaXxM/ipM8edDda5nrffwiZvZlEAAEEEJhYgacUUsv15a2mvzJnTNB9675kU/n46c06cRqTDx6v3RNU11ssm8V6K/N56W95NrNKMM196Pkbbjt5GfK7JIvHcyL9bLaH7VTduQ2v6+jnrr/vBwe+u5MeeOYT2/zivW8vffReuk6mvm8DqF30x8/vbD//3urfvfGT7BZfbH30zdfTBV95/fU7b37Qe+7NaLMfPP99u/Lv/uA7Jsmgf//2ey+tv/rT13SNVFI//tarr3wpbYKpcyEQf2mMTtbfaQcHxnWjWXlbete73pZfM9F3SN1efrs32s51+TU3RrZoGXmr716yydXuJ7/L/oqXycInv39qC9FzyI9SxbvSdLf81kq4TP+j2FvyvNxX1nRzphBAAAEEJlrg6YTUKJYdaGVFP4I2uvWlveAgiD7ztMTSKqeV1GbyWWitnVr4ERVXYqSQ6h3VvGoccSfrBel1d2e91pocvH7iNn35CHcqjVpzyzcrQftBzWul1WUN6Jmz/NJL3/voJT3bD+68aS7/2T9rJfWP/tcds375q7HBK9vffCWa7r27+dFL61o0zT2+dlkza7xZvhzbe3f1w49/9zfPmX97Y/VH7/2kr5IqeTd9olybzEyegNQm810W6S+d/UXLnZHfbEdv2uziivSH+FvyCy1jVILlpewqnZbYGiXUU39hg3b2q2bUQLluJ2R3b8d+PzW+a4u10RHueO7OyXQb7cwPBBBAAIHJFXg6IbW81mr1us2d+70Hc9JF6Gh/vak1WpWSLb2EnYAJalQW1U++7HgAWd/Lfm6l5cZstTFpZVwnSpV6NTw2x5k1e0eBKUsOLdft5/3SdU9mNJuueJVAxkjUWpmi0Qd3/uB//DI+r7CGav99O6yGaog0m9933443kZ9vfxTPSHf/lz9ekq5/2+//LyebshuY//yc+Xfzrcuvx6VTKqkx4JT9lCJlqxKdU9qZnp5kGA/t/G7ztvzaOvpV08S9HPIbvL+c7fFI94ym/PZO4Ke1V795obXcv9EpWdOGWinanvaLHfeu9DfHPAIIIIDARAuMLKS+8475i79Qmr/6K3P1ap+RfrxJjfD6XOutvZarQ07Li+X78qPUu2/mku4/7dFfqZmDtJLqu7bvT2OrNlmqep7xWjIqoGq0Y7GhQ+Am9dHrtg+cpRUJpfIIult+eS3sCQ2CB3aZfETnT+9rl3/6kRY7n9vOVzRlGMDbX/je+ld0r/Vv/nRdf/5sM1dh1UXy+OgrfyTd9zKhTemCfCX152/+7heeM8HHunsm7MZjUl/6y29877VMaNYGeEykgFbx7QCb9OjTSqoxzoonGTF+LNcb+kZ05Kum/Iq6uzr0tFyv77tex6vFG534afv7M0uDXqAjejKP0qwMTA9/wzNLdVLCq+OUvLp+m80N8tGV+r9BdsyALuOBAAIIIDAFAiMLqZJQf2EvHJeJEyE1rKTaKy20UqgPLd5I7/+uP7ucfBRp4cQ0vRWvpV35fZVUHSogC6U8Exjp77Nz0efqaQUXu814/qMfvr30gjC/vTdbi+paPX9P4vhBYE4bz/BLNxpImjm1by3ITO5qJ5mPKqzJZrbUmswNmPjK6+sST/9J1nz1T7740n99IY2kYQ4moQ5Am8hFMsIkqaPawGqc8pJbz73lJCPKQ/v000cmecovtURXf0u+YQUyvvyULy9hV4l+mXRKTl9IdapeazF7zVa6cfqMySCfcJH+v5GuZAoBBBBAYJoERhZSH4WUlm08WzexobJSk67AppRMtEgjF1nIELR22MiDtuf6UmaVh62kZvsEkw/JQZ9n4e5j/2/UbZqWSYPubRn8EKV3uUKldKW1vC8FpFPqxCfGhmqC1LP+ndf0aieJqnq1fjZQZkqtP9MNk0v+dSa9+upbCz8Ny7F26Xvf0aup0ofNweksU1MhIN+W2nP1mrPv1EzL60gfRfQ+1G+JJ6uYes7xd0JZvy/fMI05kk6RZK9YJbu3/TIp1dlM2TX9P0F2yBZxoxnbeRIeQNSdEjes22/Fow4yC5lEAAEEEJh0gZGFVOnlT7r7+5GcyvXanr1hjd5K5i1T01xqSrPywVbL31tKLm/vLV1a2jPpcLdo/Jn0Fc4auaLfy1Zjkg+3aBhr/xOP47y9G1duMJ+UUZdqXnis4VqtO83JpdPlzF0O0nN5TCX1pT/+rfd+ks+Xsm9fxIzzaL67P30Omcp17sc5OLcFMxMtIF8LvZ2SXKZf7nWleC91Tbfjua4sib8d2SpmLxwhbcKSZym5+j446pUvleVhtlxzYHprUnnVr1vRI/o6mfsyqWXX6BGXcnPXVOU2lpRs0jJqpl+FYmqMyE8EEEBgygRGFlKli/9EL39qJ1dpyA1rXNfWRx2/V+nt6CjV+lLb3TKZxObvPliSa/n3MsNSdYDaitH64qVWZa0SX+vR93mWPtWYT8lHe3bQrVl8rfYgKqPmLkwpVdxZL49jz6yUuX6//1TDSqpc+//tl09WUpONf/PG0gO9xOpxDyqpjxOa4PVayJR7ObVauQqo9r9XpQTqtlc8Gfb9yEfg75WWG9Ldb6+magSe/GzVK426jOSJukSi/bVBnYzHkoadJLpE4qZeG5g7Bl1+6kMPW4bSSlH21E1YgQACCCAwsQIjC6mPFNFPsgMtrdgSqnzSuG35gNTbMFXk2gt36//WHvyw3ZMwunv/St0x3eytUm0lVcJrrZYdG/fIpxvnlTYH9B3gN/TCqQ3v/pUIKFwtW1qcNMTnru7va0Nm7WX79qr8/nwpK6NKau/j/3NitMDJluwSKqmnwEzD4riQOeBcbAlUg6WOAo+62g/sMJ2kX9515bopM7vsbLl6ayodIVD2GnLb1G7woB2GSFum1TgqgdJuoM8UL5QBPOFoAhnnE1dtdX3foxxesJVZ+ojDzmzFJAIIIIDAZAo88/Dhw2GO/N69e/Pz88O0cE72nVio6J5T/3Ln2/9sL5ySjn77FwRymfWcvIhTcJoT+z6cAntOAQEEEDgvAkV91hBSP6N3TFEv2Gd0uDzNlArwPpzSF5bTQgABBMZIoKjPms+N0TlxKAgggAACCCCAAAIIWAFCKm8EBBBAAAEEEEAAgbETIKSO3UvCASGAAAIIIIAAAggQUnkPIIAAAggggAACCIydACF17F4SDggBBBBAAAEEEECAkMp7AAEEEEAAAQQQQGDsBAipY/eScEAIIIAAAggggAAChFTeAwgggAACCCCAAAJjJ1DAzfzH7pw4IAQQQAABBBBAAIGnJ1DInyP9/PDHX8hxDH8YY95CUX99YcxPk8MbcwHeh2P+AnF4CCCAwBQIyGdNIWdBd38hjDSCAAIIIIAAAgggUKQAIbVITdpCAAEEEEAAAQQQKESAkFoII40ggAACCCCAAAIIFClASC1Sk7YQQAABBBBAAAEEChEgpBbCSCMIIIAAAggggAACRQoQUovUpC0EEEAAAQQQQACBQgQIqYUw0ggCCCCAAAIIIIBAkQKE1CI1R9CW39zoBiNo1zb5qx/eefcXUeM/2/xRMv2rH/7ozQ8GLJdF2c2iLfiBAAIIIIAAAggULlDAzfzPdEx+0236g/cs11v1sjFBx2sZ16s60Va9rrfjeGuyZsofcuLtC54SyMPf7S3VYoJHn7gkyx/83quvf+3RW/38zecPf6Cb/NZ391595bXZj1ff+9X2S79jzFfXv/z3z9/52UeXnR/+6A3z+9/LtyONr3znN1HTb3//DTv1Z3/7zcc9XbQHPyZK4BG/a8mqZCI8M5l9y7iNSm/LbR5EJxv9JodbXtrt/40v1bxGRd7byRvez+yb8Yqa0SXxszjpswfdjZa57lVKmT2YRAABBBCYCoGnFVKNiT+i8ozykdMOlzjVWslt+9UoreU3m5o5OV+v3cuczmK9tebObXhdRz93/X0/OPDdnXSDzCe2+cV731766L10nUx93wZQu+iPn9/Zfv691b974yfZLb7Y+uibr6cLvvL663fe/KD33JvRZj94/vt25d/9wXdMkkH//u33Xlp/9aev6RqppH78rVdf+VLaBFPnQiCKkvEXJn+nHRwY143OXd6W3vWut+XXjFNr6FtXtzf66+xcn9ONZIuWkRi6e8l+B7X7+Vuev+JlvndG+0aN6o/0PwSdK1W8K013y2+t6Jxd6+0teR4JNfTgXwQQQGC6BJ5eSO21vS2ntVbOfG5J1/au8Dr6yRRFN18+BjW32Q+yg2b0oZgsmfgXw6k0WpXoLOSsW2ZFz7TSqDW3fLMStB/UvJZWm8KHfKgHyYwxX3rpex+9pGs+uPOmufxn/6yV1D/6X3fM+uWvRjuYV7a/+Uo03Xt386OX1rVomnt87bJm1nizfDm29+7qhx//7m+eM//2xuqP3vtJXyVV8m76RLk2mZk8AalNbrSDzHEnATT8PplZIwX+ZnvWa61l3ou6uuKtSQyVL5nyixwsL+X2kBmJrVFC9ZveUS3tJEk3DNobruyff5Trdl5293bCA/RdW6yNjnDHc3dOptt8G8whgAACCEygwNMLqVJJvbTrdYLSg9qcsYXDQLq2l5f2JKem0U1jmc1tajs92XTQO8Vvt2drragmVK7bz/ul654EAYvgVYJm0yQbaAsf3PmD//HLuKmwhmr/fTushmqINJvfd9+ON5Gfb38Uz0h3/5c/XpKuf9vv/y8nm7IbmP/8nPl3863Lr8elUyqpMeCU/ZQiZfJ1Ke1MT08yk193m7fn3IajvfMm/gIp43f2l6Mvk+lO2Sm/vRP4ae3Vb15oLWfX6/QpWdOGWinaZrsRsrvqL0h2nmkEEEAAgakQGFlIfecd8xd/oUR/9Vfm6tXBVuV6bd/dvdKqlMtSOvWkYtMoBXt226jWYgKzVD4XfXl+s9mrNWzBWAGC7pZfXgt7QoPggTWRj+hkvV3wtcs//UiLnc9t5yuaMgzg7S98b/0rutH6N3+6rj9/tpmrsOoieXz0lT+S7nuZ0KZ0Qb6S+vM3f/cLz5ngY909E3bjMakv/eU3vvfauXh1lGaqH2nfRXKaaSVVwuOKJxkxfizX7RvVWWu1JJu6uzqIvFyv77tex6vFG534afv7M0uDXpAd5yJrSrOmOaCSKmskvDpOyatLjbZ/ZGv43TU7ZiDzHEwigAACCEyywMhCqiTUX9gLx2XitJAqlwUdGP9BNyhXKldK7f1lyWBRRaS8XLrtB4vm/my5kumItB+cp5RbJvllCDptf7FWTwKf396brUXDAHq+5PbSQWCSa8j6zvSXbjSQNLP8Wwsyk7vaSeajCmuymS21JnMDJr7y+rrE03+SNV/9ky++9F9fSCNpmINJqAPQJnJR2nehX5BksI1xyktuPfeWk4woD+3TTx+Z5Fle0+9Q/pY0EPRmneS9nG6sU9J422noQHOn5PSFVKfqtRaz10emG6eN9I1l16JvupIpBBBAAIFpEhhZSA0TqlAlEyfY/C3tLfSOvLbvmKYpLzabvmcvspBNy8uz7fZOaW5Fopqf7eifxq69QHJo7XpSJg26t42UjkIwuUKldKW1vC83QzjlGrITY0M1QerOv/OaXu0kUVWv1s8Gykyp9We6YXLJv86kV199a+GnYTnWLn3vO3o1VfqwOTidZWoqBKRU2Z6r15x9p2ZaXidze42BVUw957gT3vb4a5A9uh/IwPK+R7YGGn7XXMmWXXOl3GwRNxogoEN9TFhG9U8MW3W34lEHfU/KLAIIIIDAJAuMLKR+6UtRPJWJgY9eu21qUpVxynIxe9vRdlsa7gAAGopJREFUS37lg6q1J53+dvvyWk1uWtM+cPcWtewysI0pWai10iU3KT1JGXWp5oXnJqMAJMgrwJxcOl0eeAeux1RSX/rj33rvJ/l8KW33Rcw4j+a7+3O+uc79OAfntmBmogXslUkl+dpY7nWleC91Tbfjua4sib8d2SpmT4eJexUTljxLye04gqNe+VJZHmbLNQemtyaVV/26FT2immuuOKpl1+gRl3Jz11TlNtYvq2kZVa/Nqtk7WOl9qSimxo78RAABBKZJYGQhVYaiJmNSB4Klnzfy+WQ7EvV6KdfoLaiisop+rkk+0+7++Lp+bcqpRTegGdju5C0MDvaC2eRmqGkZNXdhSqniznrulum/NqWUuX6//9TDSqpcX/Xtl09WUpONf/PG0gO9xOpxDyqpjxOa4PX6Gyf3cmq1ct8Gtf+9KiVQt73iedVHn570BpSWG9Ldb6+magSe/GzV9Ve715Vf6cxDG9RZLY7qWNJohI8skd90vTYwdwyZHU9ORv9RyJDZk+tYggACCCAw6QIjC6kyDvXUoagD0eLuQAmvUl1Nb8xkN85c1z993f0aBVKSMLLrp+/9Kzajx6tkM7kwJZtTc1f3x5ulP+1l+7aO3Z8vZZuoktr7+P+cGC2QtpCbopKa45iumbiQOeCsbAlUg6UvK6Ou9oOoxz3ql3dduW7KzC47W67emkpHspa9htw2tRs8aMttgCVE2jKtxlGZthvoM8ULZZS5NC2d+dJrEFdtdX3foxxesJVZ+ojDzmzFJAIIIIDAZAo88/Dhw2GO/N69e/Pz88O0cE72nVio6J5T/3Ln2/9sL5ySjn77FwRymfWcvIhTcJoT+z6cAntOAQEEEDgvAkV91hBSP6N3TFEv2Gd0uDzNlArwPpzSF5bTQgABBMZIoKjPms+N0TlxKAgggAACCCCAAAIIWAFCKm8EBBBAAAEEEEAAgbETIKSO3UvCASGAAAIIIIAAAggQUnkPIIAAAggggAACCIydACF17F4SDggBBBBAAAEEEECAkMp7AAEEEEAAAQQQQGDsBAipY/eScEAIIIAAAggggAAChFTeAwgggAACCCCAAAJjJ0BIHbuXhANCAAEEEEAAAQQQKOAvToGIAAIIIIAAAggggEAiMD8/n0yfeeLzZ94z2fHChQvJNBOnCRwdHQF1Gg7LEUAAAQQQQGBqBCTzFHIudPcXwkgjCCCAAAIIIIAAAkUKEFKL1KQtBBBAAAEEEEAAgUIECKmFMNIIAggggAACCCCAQJEChNQiNWkLAQQQQAABBBBAoBABQmohjDSCAAIIIIAAAgggUKQAIbVITdpCAAEEEEAAAQQQKESAkFoII40ggAACCCCAAAIIFClASC1Sk7YQQAABBBBAAAEEChEo4Gb+pxzH4faN7cMB62aq6+uXZ3TF4Ts3tgOd68mEWb15tXRnc7PjyMSC3U9bMNdurr6gE73K+vrLM8c/3tw8qsoGOtE9zjQ/U62UOl2zuv5sZ7NT0r0yKydk0p6USXzsUR+LySevrD/77ub7i+vVo83OhfVr5tZmt7R6czVkmpCT4zARQAABBBBAAIFPITC6kKoHMWOTZXo4H27fuNWzs0mE7Wze6Ngl2zdu2J/HMrFgE9jC6np1c/PG9rXVsIUow10rSTideXl93WxuHry4vj7T0Sy7ftlshw2FG0/Kv0nsNub48ODYzFQXbIKPj39mYXGmc3D4rMwfdTp3F6pXzeGmbPZiKd6CnwgggAACCCCAwPQJjDakHnc3b3T70Gbev7VprlVl6cLAeqcGWQlsWlQNK6XHt7a1ie7mpm2pc2uzY6uxdm7S/znuyV8Ou7t9453Vm4sH9oST1K6nNvOHXzf/Wxg6mr+PtTB98ONne+oSbTbYUNbzQAABBBBAAAEEJllgtCG1v5KqUho/37/7/7QQeCB5tH9EwMJF24k9c3n95uV48yitSqxN+rh1qMBdWS9ZTbcyt25szkgFcuLKizMLV9dX37lxcMFsvysU6QkaW3V+8b+/evn3fp0qXVxdPNretpuVZMDDwYvVCRzVYF8w/kEAAQQQQAABBB4lMLqQurB40WwPqKTK0SysvvyHCy//oeawu5lYZuwg1EUZkxodcTxGc/WTTTsm9eLh5o0b27aMunB1dSEaqNqLh67avY7vTFyn/8LVmwuS3Q9Mr1JdsCXk0jUZhHqoXf/mzuYtGa67fizJfrFa6kpClUfvWIqpR8fG0WDOAwEEEEAAAQQQmD6B0YVUI9nrpi0HRlcCRfGr75ImCaZhLTSytXVUmbZby0VUkt8kvIYrbXlVaqi3fryw7hwcatiVkKaDXA9vydBV6TAPy6sLE1ZfFKV3n10PS8cffiL5s2SSSrJZv6lXmHXkeqqXL8+8fPn4x3c6R5337x6+GJiZxYmrHEevMj8QQAABBBBAAIFHCzzz8OHDR2/x6LX37t27cOHCiW1sxNShk6c8LiaX8OsG2nevV/fHAVUWabrtHwmQaStbf402HvPRmUdHR4Og5JxCq+imB9EwhsSnH1I3W7gb3tkgj5DRYRIBBBBAAAEEEHhaApJ55ufnh3/2EVVSo0KgjVxxlrJ5K7k5lO3Kz8bYtKJqR7JKDTU8O7ubU60GnczdqWRVf3yTYmpcko2fcXiez6CF48P35WL9yjW9LdeH29t3JYbqPaa2P7Ql55nL1Yud9EZdwYty7f/MxRdnup3jmWepo34Grw9PgQACCCCAAAJPRWBEIVXPRWKoXNs0I+MsTz2zKE1mKqkaPd9Ptg+DqMS2qxLhZj65sX1jM7mLaNohHpZdx7ySmpxT38ShxE07biFM7XIWmlavhffekpx6XKqsV2/JnbhkqK1A6Eq7i/h2dNiDDnjggQACCCCAAAIITJvAyELq8Z1bcrP9i6ufIkXFtdEFZyauk0oss6FN2SXR3tQ8KgXTma9/3fzDP2TrsHZYalxJtXEu+osBY/6CHR8HxlxcNO/c2NQaanyymsBn5FQ39RZUeqJSXZY7+W+HN5WVwQAyVFdHRNy6c3EyznPMXwYODwEEEEAAAQTGTWBEY1LH7TSf/vGcPib16R8bR4AAAggggAACCBQlUNSY1M8VdUC0gwACCCCAAAIIIIBAUQKE1KIkaQcBBBBAAAEEEECgMAFCamGUNIQAAggggAACCCBQlAAhtShJ2kEAAQQQQAABBBAoTICQWhglDSGAAAIIIIAAAggUJUBILUqSdhBAAAEEEEAAAQQKEyCkFkZJQwgggAACCCCAAAJFCRBSi5KkHQQQQAABBBBAAIHCBAiphVHSEAIIIIAAAggggEBRAgX8WVT5uwJFHc10twPUdL++nB0CCCCAAAIIFChQQEidn58v8ICmtal79+4BNa0vLueFAAIIIIAAAomAZJ5kepgJuvuH0WNfBBBAAAEEEEAAgZEIEFJHwkqjCCCAAAIIIIAAAsMIEFKH0WNfBBBAAAEEEEAAgZEIEFJHwkqjCCCAAAIIIIAAAsMIEFKH0WNfBBBAAAEEEEAAgZEIEFJHwkqjCCCAAAIIIIAAAsMIEFKH0WNfBBBAAAEEEEAAgZEIEFJHwkqjCCCAAAIIIIAAAsMIFHAz/zM8vb/lNg9O32+x3lorG7/pHdW8qnPadqc0Uq636mW7T9DxWsaVFmSifcHTpb2u95ZxGxVHWnebftx0uV43t4Nao2I6nvegps9ujOzl7QTxJslPp9bwKqVkttAJObwdx7PP3t9usiqZCLeIz6iXIY0Iwi0v7WZO1O5TqnkqoCcYsjxWMnVLnz3obrTM9ZFR9J8/8wgggAACCCBwvgSeTkgtr7VasXMSleIF/T9PRihnxbPh9WRelOTUTvZ3ql5NopvfqoWLJGBt7C01PBt7JciFhyBpdXe5XC4dtT23LS23LrXdLSM5VXZvVZPGogl/yzuZW/s3KnQ+8rEHLQ37O+3gwLhu9BxyGt71rrfl10ykodsbdXCuz+lG9kTFcPdSHN6lkS3PX/HCKG8beoykKVW8K013y2+thM8r7Xt7S543orAePgn/IoAAAggggMA5Fng6IVUrcxvtTNpLQpe8FJKqluPqn+/ulMuLJyNU+IoF7Q03zaTRq1iu64SmqHbPLjpwbcU0egrdRUqJ101LA6tr3mrPNWxcq7q1vdb9By1XwlfD5rdcsTVq3UgWjIJasmS4iX6KNIAaW/LMte4327Neay1OrNG6ircmuVMk/OZGsLyU20NmJLZGCfXU4vQjJLMVZd+19e+Icsdzd057afqPgXkEEEAAAQQQQOBTCTylkCrHaPv0ozKhZMIoPxlbCtXqn6wKO+u1kpoLo7I27NA/JSFpU7+/pGE36vfPi2iS09Jgw3gbraVG7f5GHJEXy+UDv1zXrnB96FGEU+m/xVdS5UhalegJ0s709BkzUX63eXvObTgKYuyICNlKkvT+cjg+Id0nN+W3dwI/jb5+80JrObeBzDxCsiZF21MpP/O6cv+BM48AAggggAACUyowqpD6N/c6b/h/LWjfLf/5n86f6DXPaErKCvuunZWoW96u1GgVGM8znnRklxeNuWQHlUqJdMsPO5lLsyYfXpNGJXK9UKm+kB93Gq3VvNUoSwLWimnLdv3no6hEQLf5pf/2xV/84y+TBvMTB7YWa4d15lecYS5T8Y33jiOzzsvwgxDHrlyWI9eFMlhC1XY1hctw2n3X64jSaY/+rB30grDEnOzwSEnHKXn1gZT6NSM7ZiBpjwkEEEAAAQQQQGBYgVGFVEmo//ofv5ajk4lHh9SoSqflz/Rk/K2mWSw7s8tLe+3dWTN3aWlv3zdluZqqvTdbCwuPOmZ0MXulkR2I2chVT+PRq1HLWri1k+F4U8mj3onrtzTTrelGmYKlRsn7V2xhVtLh7bnwwqOo0aF+OJVGUke1gVUS+ZJbz10uJhlRHtqnnz4yyVMG+Golekv69YPerHPKMNEUxyk5fSH1SSTDsQfpOAMt+qaHwxQCCCCAAAIIIFCswKhC6pMf5aBKqtRQa7VL91tHpUqjrj3sTqVmvG6vZG6bWkOSks1zcdTKlh6jbm0p8kVXtcuo1r5jcZvpOID+bu4kxco+enWXHJxeRKXBLzpOaTkcsdrX6rCz0nx7rl5z9p2aaXkdvSlB3KSsSm9EEC+Un1G8D3v8Ncge3Q9Msle8YXZvKyXBPVN2fQLJNRMegO+GCT9u2Rh3Kx51kC5jCgEEEEAAAQQQKEBgVCFVevmT7v5HH+agSqpTkWuD/Kbd0d99sFQrSR93bdf1ZCimLaPGBcjclUBpsVB39HfTMmpms2wMlbB78tKr8MIrbUGKhRoOfXdDSrh6l6rmwKyomw71kEPydkpymX65192T3vyq58poBFeWxFVhewVVT8L6ilcxYfG4lNzHIDjqlS+V5WG2XHNgemtSeQ26t+NDimquORwtu0aPJ5A0fqaMqiN65V5dmoUppsaI/EQAAQQQQACBwgVGFVKli//RvfzmIB6Lmrmmx1Y905QoZxt02r0lN7ytqdGcmKmDaog0tdaJ2uFpSLK93lJAqqfRFuU1rxbeSknLllpTlHGqYTDUvv4DzXc6CFRXtaPrqLSgKkMRiqogRk/ayp+FHY2gz9TWm22ddj7h8sDfKy034sEJjcCTw2vVpQItITJf+dQGdZ94LGmQNPxpJeNKtnwNSNpgAgEEEEAAAQQQKFDgmYcPHw7T3L179+bn5z91C1qEG3jX+kzBT8ufc6U9I+NSm1poDNNjlOq8C217iXtca9QjyOzbd0CZSmq0JtsJ3rexzibDAOLt4hvgD9j2yRY9EdRJlvj5T3sSLfDum2Wjt6aKRghoI2bpQVvuwCUh0pXBA/ZPEqR1ZY3+4d8psKcZSPCXCvWTSUp9O6mknnZMLEcAAQQQQACBcyzwRJnnCXyeUkh9giObsk2KesGmjIXTQQABBBBAAIEpEygq83xuylw4HQQQQAABBBBAAIEpECCkTsGLyCkggAACCCCAAALTJkBInbZXlPNBAAEEEEAAAQSmQICQOgUvIqeAAAIIIIAAAghMmwAhddpeUc4HAQQQQAABBBCYAgFC6hS8iJwCAggggAACCCAwbQKE1Gl7RTkfBBBAAAEEEEBgCgQIqVPwInIKCCCAAAIIIIDAtAkQUqftFeV8EEAAAQQQQACBKRD4/PDnIH9XYPhGzkMLQJ2HV5lzRAABBBBAAIFCBAoIqfPz84UcynQ3UtSfCJtuJc4OAQQQQAABBCZdoKiqHN39k/5O4PgRQAABBBBAAIEpFCCkTuGLyikhgAACCCCAAAKTLkBInfRXkONHAAEEEEAAAQSmUICQOoUvKqeEAAIIIIAAAghMugAhddJfQY4fAQQQQAABBBCYQgFC6hS+qJwSAggggAACCCAw6QKE1El/BTl+BBBAAAEEEEBgCgUIqVP4onJKCCCAAAIIIIDApAsUcDP/p0Lgb7nNg5PPXK636uVwca/rvWXcRsWRiR3HW5PFQXejZa57lZJMeO1etLuzUl/a23Ua9bLfdG/PebKLrJG9NtrBiWdwVjyvqutH8kgP9UTzyapkItxEZu1p9jIgkUK45aVdt+nnmivVwnMMOl77gidew2Hm2mYGAQQQQAABBBAoRODphVRJhHF4ipNfZpENUqbjeQ9qLc2X9iGpa+N+LYqhTq0hcTOLINGznc6XKt6Vprvlt1bCZRpM95Y8T3dxKo1WRRfb2LpYrlzYdV3XLNZb1wNvo6vRVnYPNwn3Dv/1m95Rdv6zmI6iZByM/Z12cGDkYMOH5FHvetfb8msmAtHt9bzazvU53Ua2aGkM3b2U5HeZ9fwVL2aVjYbBDA+EfxFAAAEEEEAAgSIFnlJIlbjZNJKeMjlJctWJRY8606C94WYyabhpuW5/SlDzdsIyqO/agmuU6nY8d0cCWe2+fa7lfe/+lVZdYmupXl90d82uuyFHVbeBMJOYM4fhrNQyc0VMavLOlWyTAGrCpJ59Er/ZnvVaa3FijVZVvDXJnYLhNzeC5aXsDjotGlFC1ZBdG1QJHgaz76tC/7MzjwACCCCAAAIInEHgKYXU4H5QmsuVQU3vfs+Z60tfjzqhk8U/u7XNYVJnzHT851qRImJgVzZdd7fuzd123abdoFSWfm+p6ca52VYgc7tqCCy+kpot2YYd9Enl2D57ZsjBbvP2nNtwtHdesnS4mWTp/eW02Nx3wDrrt3cCP629+s0LreX+zYbB7G+LeQQQQAABBBBAYHiBUYXUv7nXecP/azm+75b//E/nq/0HWq57R54nlVDpYY8yWbnekK52WZSPlwcSJrN7RxmyNGuaAyqpsqXkLccpeXVJlMl4gqQBfTpPx55qxdTWccu5Tn0pOrpu8N8uOf+4nwmHye464dtabFHlQx2EkIyODZ8ne74SmjNnv1xv6Ok7a62WnIJkbOnAL9fr+67X8U4v8Pan7aAXxMNxwyc0Q2FGbfADAQQQQAABBBAoUmBUIVUS6r/+x6/lSGViQEiVpFX1WlUdK+m6cRkvrClq/HIlnEW90mmKDS9muh+eve6+mFwRJcvsKEy5+CmLE18hFC3TOqWdtLFN82g0JCDdR5631bLl3EWJuNr1Lw3KlvHQWDm49lz/WNh0908/lYyOlV1tYDVOecmt567NksAtD+3TTx+Z5Fle07Ttb0kDQW/Wydenkz1SH6fk9IXUoTCTZ2ACAQQQQAABBBAoTmBUITVMqHKcycTAY5aApUXBHb+S9HFr/NIs6Fd1sOigR676mK07Rn3ammtNWEb1pTKbf7hbSe22r2ab782PDqNp7JhVExV0ZWkyHiDf7rBzNv7Wa86+UzMtr+NmRo7KqvgSs9yzyMHYUC7r95c1yB7dD8yJARPZvS2WBPFM2bUwzNyhMYMAAggggAACCAwnMKqQ+tv/6b+E8VQmBhxh5gqe4Cis6+lFP7Xo9k/9/dH5FuLqY6aRE5VUP7zqyEa2bMtxMdW2KPkt05muizLXRUl602jou155UeJs3TQHJsX8oZ1pTiu1OyWNv73unq0xuzrqQJbEhWFbEu7JaNoVr2LC+nEpuZWBAJYvleVhtlxzYHprUnkNurfjQ9G0LdNpJVVmtOwaPQrDjBvkJwIIIIAAAgggUIDAqEKqDEVNxqQOOMxyvbavN33ShyYw7aWvX7H3gdJFOgBA+9l1+pSHvT9ALeyaP2WT/OKoZCh1xHC59HHXH6RXIIVXI0X1S1t91HSnx6Xd/XakrGQ9jbXNExXYsMEz/atHJTfGisYYxE1o/3tVn6utwx7ipYN/Bv5eabmhAyd0eIKM65WfrXqlUZdbvebLyHEmDwfmZnmHxhx8aCxFAAEEEEAAAQTOKvDMw4cPz7qv7nfv3r35+flhWjjLvhoiowGj8e65SmG8MPyZqaSGCyST5e/6lN8+DaGa/PQOVvGo2b7tPs3sE0HpqNnw7w7ETeuZSj331IeWePfNstFbU0UJWxsxSw/acj2WJHJXBg/YobcynQwhsLVb+QpgzysYDvPUQ2MFAggggAACCJxHgSfKPE8AM5kh9QlObNw2KeoFG7fz4ngQQAABBBBAAIGsQFGZ53PZRplGAAEEEEAAAQQQQGAcBAip4/AqcAwIIIAAAggggAACOQFCao6DGQQQQAABBBBAAIFxECCkjsOrwDEggAACCCCAAAII5AQIqTkOZhBAAAEEEEAAAQTGQYCQOg6vAseAAAIIIIAAAgggkBMgpOY4mEEAAQQQQAABBBAYBwFC6ji8ChwDAggggAACCCCAQE6AkJrjYAYBBBBAAAEEEEBgHAQIqePwKnAMCCCAAAIIIIAAAjmBz+fmzjQjf/zqTPudu52AOncvOSeMAAIIIIAAAmcVeObhw4dn3Zf9EEAAAQQQQAABBBAYiQDd/SNhpVEEEEAAAQQQQACBYQQIqcPosS8CCCCAAAIIIIDASAQIqSNhpVEEEEAAAQQQQACBYQQIqcPosS8CCCCAAAIIIIDASAQIqSNhpVEEEEAAAQQQQACBYQQIqcPosS8CCCCAAAIIIIDASAQIqSNhpVEEEEAAAQQQQACBYQQIqcPosS8CCCCAAAIIIIDASAT+PwvZE/fihf2QAAAAAElFTkSuQmCC">' +
          '</div>' +
          '<div class="thumbnail-introduce">' +
          '<span>日报功能介绍：</span>' +
          '<ul>' +
          '<li>服务器运行情况监测</li>' +
          '<li>CPU、内存、磁盘、进程过载等异常信息记录</li>' +
          '<li>协助管理员分析服务器</li>' +
          '</ul>' +
          '<div class="daily-product-buy">' +
          '<a title="立即购买" href="javascript:;" class="btn btn-success va0 ml15">立即购买</a>'
        '</div>' +
          '</div>' +
          '</div>'
        $('.daily-view').html(product_view);
        $('.thumbnail-box').hover(function (e) {
          $(this).addClass('shadow_mask')
        }, function () {
          $(this).removeClass('shadow_mask')
        }).click(function () {
          layer.open({
            title: false,
            btn: false,
            shadeClose: true,
            closeBtn: 2,
            area: '908px',
            content: '<img src="' + $('.thumbnail-box img').attr('src') + '">'
          })
        })
        // 购买
        $('.daily-product-buy a').click(function () {
          bt.soft.updata_ltd()
        })
        return false;
      }
      $.post('/daily?action=get_daily_list', function (dlist) {
        for (var i = dlist.length; i > 0; i--) {
          var tItem = dlist[i - 1],
            _code = tItem.evaluate == '正常' ? '#20a53a' : (tItem.evaluate == '良好' ? '#2034a5' : '#ffa700'),
            _strTime = tItem.time_key.toString(),
            _timeText = _strTime.substr(0, 4) + '-' + _strTime.substr(4, 2) + '-' + _strTime.substr(6, 2)
          _liHthml += '<li class="' + (tItem.time_key == res.date ? 'active' : '') + '" data-time="' + tItem.time_key + '"><i style="background-color:' + _code + '"></i> ' + _timeText + '</li>'
        }
        var _html = '', txtColor = '', serverData = res.data, resTime = res.date.toString(), timeText = resTime.substr(0, 4) + '-' + resTime.substr(4, 2) + '-' + resTime.substr(6, 2);
        txtColor = res.evaluate == '正常' ? '#20a53a' : (res.evaluate == '良好' ? '#2034a5' : '#ffa700')
        _html = '<div class="daily_time_select">' +
          '<span>选择日期:</span>' +
          '<div class="daily_time_box">' +
          '<span class="daily_box_text">' + timeText + '</span>' +
          '<ul class="daily_select_list">' + _liHthml + '</ul>' +
          '</div>' +
          '</div>' +
          '<div class="daily-head">' +
          '<p class="daily-status" style="color:' + txtColor + ';text-align: center;font-size: 46px;">' + res.evaluate + '</p>' +
          '<p style="text-align: center;margin: 10px 0 30px;">监测时间：' + timeText + ' 00:00:00 - 23:59:59</p>' +
          '<p style="margin-bottom: 15px;">健康信息提醒：</p>' +
          '<ul class="report_results ' + (res.evaluate != '正常' ? 'textRed' : '') + '">'

        $.each(res.summary, function (index, item) {
          _html += '<li>' + item + '</li>'
        })
        _html += '</ul></div>'
        _html += '<div class="divtable daily-table" style="width:960px;margin:0 auto">' +
          '<table class="table table-hover">' +
          '<tbody>' +
          '<tr class="daily-title"><td width=110>资源</td><td colspan="2">过载次数(五分钟内平均使用率超过80%)</td></tr>' +
          '<tr><td><i style="background-color:' + (serverData.cpu.ex ? 'red' : '#20a53a') + '"></i> CPU</td><td colspan="2">' + that.resource_info('cpu', serverData.cpu.detail) + '</td></tr>' +
          '<tr><td><i style="background-color:' + (serverData.ram.ex ? 'red' : '#20a53a') + '"></i> 内存</td><td colspan="2">' + that.resource_info('ram', serverData.ram.detail) + '</td></tr>' +
          '<tr><td><i style="background-color:' + (serverData.disk.ex ? 'red' : '#20a53a') + '"></i> 磁盘</td><td colspan="2">' + that.resource_info('disk', serverData.disk.detail) + '</td></tr>' +
          '<tr class="daily-title"><td>常用服务</td><td colspan="2">异常次数(服务出现停止运行的次数)</td></tr>' +
          '<tr><td><i style="background-color:' + (serverData.server.nginx.ex ? 'red' : '#20a53a') + '"></i> Nginx</td><td colspan="2">' + that.resource_info('nginx', serverData.server.nginx.detail) + '</td></tr>' +
          '<tr><td><i style="background-color:' + (serverData.server.mysql.ex ? 'red' : '#20a53a') + '"></i> Mysql</td><td colspan="2">' + that.resource_info('mysql', serverData.server.mysql.detail) + '</td></tr>' +
          '<tr><td><i style="background-color:' + (serverData.server.apache.ex ? 'red' : '#20a53a') + '"></i> Apache</td><td colspan="2">' + that.resource_info('apache', serverData.server.apache.detail) + '</td></tr>' +
          '<tr><td><i style="background-color:' + (serverData.server.php.ex ? 'red' : '#20a53a') + '"></i> PHP</td><td colspan="2">' + that.resource_info('php', serverData.server.php.detail) + '</td></tr>' +
          '<tr><td><i style="background-color:' + (serverData.server.ftpd.ex ? 'red' : '#20a53a') + '"></i> Ftpd</td><td colspan="2">' + that.resource_info('ftpd', serverData.server.ftpd.detail) + '</td></tr>' +
          '<tr><td><i style="background-color:' + (serverData.server.redis.ex ? 'red' : '#20a53a') + '"></i> Redis</td><td colspan="2">' + that.resource_info('redis', serverData.server.redis.detail) + '</td></tr>' +
          '<tr><td><i style="background-color:' + (serverData.server.tomcat.ex ? 'red' : '#20a53a') + '"></i> Tomcat</td><td colspan="2">' + that.resource_info('tomcat', serverData.server.tomcat.detail) + '</td></tr>' +
          '<tr><td><i style="background-color:' + (serverData.server.memcached.ex ? 'red' : '#20a53a') + '"></i> Memcached</td><td colspan="2">' + that.resource_info('memcached', serverData.server.memcached.detail) + '</td></tr>' +
          '<tr class="daily-title"><td>备份类型</td><td width=240>备份失败</td><td>未开启备份</td></tr>' +
          '<tr><td><i style="background-color:' + (serverData.backup.database.backup.length || serverData.backup.database.no_backup.length ? 'red' : '#20a53a') + '"></i> 数据库</td><td>' + that.resource_info('database_backup', serverData.backup.database.backup) + '</td><td>' + that.resource_info('database_no_backup', serverData.backup.database.no_backup) + '</td></tr>' +
          '<tr><td><i style="background-color:' + (serverData.backup.site.backup.length || serverData.backup.site.no_backup.length ? 'red' : '#20a53a') + '"></i> 网站</td><td>' + that.resource_info('site_backup', serverData.backup.site.backup) + '</td><td>' + that.resource_info('site_no_backup', serverData.backup.site.no_backup) + '</td></tr>' +
          '<tr class="daily-title"><td>异常类型</td><td colspan="2">次数</td></tr>' +
          '<tr><td><i style="background-color:' + (serverData.exception.panel.ex ? 'red' : '#20a53a') + '"></i> 面板异常登录</td><td colspan="2">' + that.resource_info('panel', serverData.exception.panel.detail) + '</td></tr>' +
          '<tr><td><i style="background-color:' + (serverData.exception.ssh.ex ? 'red' : '#20a53a') + '"></i> SSH异常登录</td><td colspan="2">' + that.resource_info('ssh', serverData.exception.ssh.detail) + '</td></tr>' +
          '</tbody>' +
          '</table>' +
          '<ul class="help-info-text c7">' +
          '<li style="list-style: none;">在系统监控开启的情况下，日报会记录服务器每天运行的异常信息，协助管理员分析服务器前一天是否运行正常。</li>' +
          '</ul>' +
          '</div>'
        $('.daily-view').html(_html);

        //选择日期
        $('.daily_box_text').on('click', function (e) {
          if ($(this).parent().hasClass('active')) {
            $(this).parent().removeClass('active');
          } else {
            $(this).parent().addClass('active')
          }
          $(document).unbind('click').click(function (e) {
            $('.daily_time_box').removeClass('active');
            $(this).unbind('click');
          });
          e.stopPropagation();
          e.preventDefault();
        })
        //选择日期li
        $('.daily_select_list').on('click', 'li', function (e) {
          var _val = $(this).data('time');
          $(this).addClass('active').siblings().removeClass('active');
          $(this).parent().prev().find('.daily_box_text').html($(this).text());
          that.dailyView(_val);
        });
      })
    })
  },
  resource_info: function (type, data) {
    var tdHTml = ''
    if (type.indexOf('_backup') == -1) {
      tdHTml = data.length > 0 ? (data.length + '次 <span name="daily_' + type + '"><a class="btlink">查看详情</a><div class="daily_details_mask bgw hide"></div></span>') + '' : '未监测到异常'
    } else {
      var backupTotal = data.length, unit = '次';
      if (type == 'database_no_backup' || type == 'site_no_backup') unit = '个'
      tdHTml = backupTotal > 0 ? (backupTotal + unit + ' <span name="daily_' + type + '"><a class="btlink">查看详情</a><div class="daily_details_mask bgw hide"></div></span>') + '' : '未监测到异常'
    }
    $('.daily-view').off('click', '[name=daily_' + type + ']');
    $('.daily-view').on('click', '[name=daily_' + type + ']', function (e) {
      var box = $(this).find('.daily_details_mask')
      if (e.target.localName == 'a') {
        if (box.hasClass('hide')) {
          //隐藏所有
          $('.daily_details_mask').addClass('hide').prev('a').removeAttr('style')
          box.prev('a').css('color', '#23527c');
          box.removeClass('hide').css({ left: e.clientX - 215, top: (e.clientY - 60) + $(document).scrollTop() });
        } else {
          box.addClass('hide')
          box.prev('a').removeAttr('style');
        }
        var _details = '<div class="divtable daliy_details_table"><table class="table table-hover">', thead = '', _tr = '';
        switch (type) {
          case 'cpu':
          case 'ram':
            thead = '<thead><tr><th></th><th>过载时间</th><th>PID</th><th>进程</th><th>占用</th></tr></thead>'
            $.each(data, function (index, item) {
              _tr += '<tr><td>' + (index + 1) + '</td><td>' + bt.format_data(item.time) + '</td><td>' + item.pid + '</td><td><span class="overflow_hide" style="width:100px" title="' + item.name + '">' + item.name + '</span></td><td>' + item.percent + '%</td></tr>'
            })
            break;
          case 'disk':
            thead = '<thead><tr><th></th><th>路径</th><th>占用</th></tr></thead>'
            $.each(data, function (index, item) {
              _tr += '<tr><td>' + (index + 1) + '</td><td><span class="overflow_hide" style="width:230px" title="' + item.name + '">' + item.name + '</span></td><td>' + item.percent + '%</td></tr>'
            })
            break;
          case 'nginx':
          case 'ftpd':
          case 'memcached':
          case 'tomcat':
          case 'apache':
          case 'mysql':
          case 'redis':
          case 'php':
            thead = '<thead><tr><th></th><th>停止时间</th></tr></thead>'
            $.each(data, function (index, item) {
              _tr += '<tr><td>' + (index + 1) + '</td><td>' + bt.format_data(item.time) + '</td></tr>'
            })
            break;
          case 'database_backup':
          case 'site_backup':
          case 'path_backup':
            thead = '<thead><tr><th></th><th>名称</th><th>时间</th></tr></thead>'
            $.each(data, function (index, item) {
              _tr += '<tr><td>' + (index + 1) + '</td><td><span class="overflow_hide" style="width:230px" title="' + item.name + '">' + item.name + '</span></td><td>' + bt.format_data(item.time) + '</td></tr>'
            })
            break;
          case 'database_no_backup':
          case 'site_no_backup':
          case 'path_no_backup':
            thead = '<thead><tr><th></th><th>名称</th></tr></thead>'
            $.each(data, function (index, item) {
              _tr += '<tr><td>' + (index + 1) + '</td><td><span class="overflow_hide" style="width:230px" title="' + item.name + '">' + item.name + '</span></td></tr>'
            })
            break;
          case 'panel':
          case 'ssh':
            thead = '<thead><tr><th></th><th>时间</th><th>用户</th><th>详情</th></tr></thead>'
            $.each(data, function (index, item) {
              _tr += '<tr><td>' + (index + 1) + '</td><td>' + bt.format_data(item.time) + '</td><td>' + item.username + '</td><td>' + item.desc + '</td></tr>'
            })
            break;
        }
        _details += thead + '<tbody>' + _tr + '</tbody></table></div>';

        $(this).find('.daily_details_mask').html(_details)
        if (data.length > 5) {
          // 固定表格头部
          if (jQuery.prototype.fixedThead) {
            $(box).find('.divtable').fixedThead({ resize: false, height: 213 });
            $(box).find('.divtable').css({ 'overflow': 'hidden' });
          } else {
            $(box).find('.divtable').css({ 'overflow': 'auto' });
          }
        }
      }

      $(document).one('click', function () {
        $('.daily_details_mask').addClass('hide').prev('a').removeAttr('style')
      })
      e.stopPropagation();
    })
    return tdHTml;
  }
}
//定义周期时间
function getBeforeDate (n) {
  var n = n;
  var d = new Date();
  var year = d.getFullYear();
  var mon = d.getMonth() + 1;
  var day = d.getDate();
  if (day <= n) {
    if (mon > 1) {
      mon = mon - 1;
    }
    else {
      year = year - 1;
      mon = 12;
    }
  }
  d.setDate(d.getDate() - n);
  year = d.getFullYear();
  mon = d.getMonth() + 1;
  day = d.getDate();
  s = year + "/" + (mon < 10 ? ('0' + mon) : mon) + "/" + (day < 10 ? ('0' + day) : day);
  return s;
}
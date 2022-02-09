var database = {
  database_table: null,
  dbCloudServerTable:null,  //远程服务器视图
  cloudDatabaseList:[],     //远程服务器列表
  init: function () {
    this.event();
    this.database_table_view();
  },
  event: function () {
    $('#SearchValue').keydown(function (e) {
      if (e.keyCode == 13) {
        $(this).next().click();
      }
    });
  },
  database_table_view: function (search) {
    var that = this;
    var loadT = layer.msg('正在获取远程服务器列表,请稍候...', {
      icon: 16,
      time: 0,
      shade: [0.3, '#000']
    });
    var param = {
      table: 'databases',
      search: search || ''
    }
    bt.send('GetCloudServer','database/GetCloudServer',{},function(cloudData){
      layer.close(loadT);
      that.cloudDatabaseList = cloudData
      $('#bt_database_table').empty();
      that.database_table = bt_tools.table({
        el: '#bt_database_table',
        url: '/data?action=getData',
        param: param, //参数
        minWidth: '1000px',
        autoHeight: true,
        default: "数据库列表为空", // 数据为空时的默认提示
        beforeRequest: function(){
          var db_type_val = $('.database_type_select_filter').val()
          switch(db_type_val){
            case 'all':
              delete param['db_type']
              delete param['sid']
              break;
            case 0:
              param['db_type'] = 0;
              break;
            default:
              delete param['db_type'];
              param['sid'] = db_type_val
          }
          return param
        },
        column: [{
          type: 'checkbox',
          width: 20
        },
        {
          fid: 'name',
          title: '数据库名',
          type: 'text'
        },
        {
          fid: 'username',
          title: '用户名',
          type: 'text',
          sort: true
        },
        {
          fid: 'password',
          title: '密码',
          type: 'password',
          copy: true,
          eye_open: true,
          template: function (row) {
            if (row.password === '') return '<span class="c9 cursor" onclick="database.set_data_pass(\'' + row.id + '\',\'' + row.username + '\',\'' + row.password + '\')">无法获取密码，请点击<span style="color:red">改密</span>重置密码!</span>'
            return true
          }
        },
        {
          fid: 'backup',
          title: '备份',
          width: 130,
          template: function (row) {
            var backup = '点击备份',
              _class = "bt_warning";
            if (row.backup_count > 0) backup = lan.database.backup_ok, _class = "bt_success";
            return '<span><a href="javascript:;" class="btlink ' + _class + '" onclick="database.database_detail(' + row.id + ',\'' + row.name + '\')">' + backup + (row.backup_count > 0 ? ('(' + row.backup_count + ')') : '') + '</a> | ' +
              '<a href="javascript:database.input_database(\'' + row.name + '\')" class="btlink">' + lan.database.input + '</a></span>';
          }
        },
        {
          title:'数据库位置',
          type: 'text',
          width: 116,
          template: function (row) {
            var type_column = '-'
            switch(row.db_type){
              case 0:
                type_column = '本地数据库'
                break;
              case 1:
                type_column = ('远程库('+row.conn_config.db_host+':'+row.conn_config.db_port+')').toString()
                break;
              case 2:
                $.each(cloudData,function(index,item){
                  if(row.sid == item.id){
                    if(item.ps !== ''){ // 默认显示备注
                      type_column = item.ps
                    }else{
                      type_column = ('远程服务器('+item.db_host+':'+item.db_port+')').toString()
                    }
                  }
                })
                break;
            }
            return '<span class="size_ellipsis" style="width:100px" title="'+type_column+'">'+type_column+'</span>'
          }
        },
        {
          fid: 'ps',
          title: '备注',
          type: 'input',
          blur: function (row, index, ev) {
            bt.pub.set_data_ps({
              id: row.id,
              table: 'databases',
              ps: ev.target.value
            }, function (res) {
              layer.msg(res.msg, { icon: res.status ? 1 : 2 });
            });
          },
          keyup: function (row, index, ev) {
            if (ev.keyCode === 13) {
              $(this).blur();
            }
          }
        },
        {
          type: 'group',
          title: '操作',
          width: 220,
          align: 'right',
          group: [{
            title: '管理',
            tips: '数据库管理',
            hide:function(rows){return rows.db_type != 0},  // 远程数据库和远程服务器
            event: function (row) {
              bt.database.open_phpmyadmin(row.name, row.username, row.password);
            }
          }, {
            title: '权限',
            tips: '设置数据库权限',
            hide:function(rows){return rows.db_type == 1}, //远程数据库
            event: function (row) {
              bt.database.set_data_access(row.username);
            }
          }, {
            title: '工具',
            tips: 'MySQL优化修复工具',
            event: function (row) {
              database.rep_tools(row.name);
            }
          }, {
            title: '改密',
            tips: '修改数据库密码',
            hide:function(rows){return rows.db_type == 1},
            event: function (row) {
              database.set_data_pass(row.id, row.username, row.password);
            }
          }, {
            title: '删除',
            tips: '删除数据库',
            event: function (row) {
              database.del_database(row.id, row.name,row, function (res) {
                if (res.status) that.database_table.$refresh_table_list(true);
                layer.msg(res.msg, {
                  icon: res.status ? 1 : 2
                })
              });
            }
          }]
        }
        ],
        sortParam: function (data) {
          return {
            'order': data.name + ' ' + data.sort
          };
        },
        tootls: [{ // 按钮组
          type: 'group',
          positon: ['left', 'top'],
          list: [{
            title: '添加数据库',
            active: true,
            event: function () {
              if(that.cloudDatabaseList.length == 0) return layer.msg('至少添加一个远程服务器或安装本地数据库',{time:0,icon:2,closeBtn: 2, shade: .3})
              var cloudList = []
              $.each(that.cloudDatabaseList,function(index,item){
                var _tips = item.ps != ''?(item.ps+' ('+item.db_host+')'):item.db_host
                cloudList.push({title:_tips,value:item.id})
              })
              bt.database.add_database(cloudList,function (res) {
                if (res.status) that.database_table.$refresh_table_list(true);
              })
            }
          }, {
            title: 'root密码',
            event: function () {
              bt.database.set_root('root')
            }
          }, {
            title: 'phpMyAdmin',
            event: function () {
              bt.database.open_phpmyadmin('', 'root', bt.config.mysql_root)
            }
          },
          {
            title:'远程服务器',
            event:function(){
              database.get_cloud_server_list();
            }
          },{
            title: '同步所有',
            style: {
              'margin-left': '30px'
            },
            event: function () {
              database.sync_to_database({
                type: 0,
                data: []
              }, function (res) {
                if (res.status) that.database_table.$refresh_table_list(true);
              })
            }
          }, {
            title: '从服务器获取',
            event: function () {
              if(that.cloudDatabaseList.length == 0) return layer.msg('至少添加一个远程服务器或安装本地数据库',{time:0,icon:2,closeBtn: 2, shade: .3})
              var _list = [];
              $.each(that.cloudDatabaseList,function (index,item){
                var _tips = item.ps != ''?(item.ps+' (服务器地址:'+item.db_host+')'):item.db_host
                _list.push({title:_tips,value:item.id})
              })
              bt_tools.open({
                title:'选择数据库位置',
                area:'450px',
                btn: ['确认','取消'],
                skin: 'databaseCloudServer',
                content: {
                  'class':'pd20',
                  form:[{
                    label:'数据库位置',
                    group:{
                      type:'select',
                      name:'sid',
                      width:'260px',
                      list:_list
                    }
                  }]
                },
                success:function(layers){
                  $(layers).find('.layui-layer-content').css('overflow','inherit')
                },
                yes:function (form,layers,index){
                  bt.database.sync_database(form.sid,function (rdata) {
                    if (rdata.status){
                      that.database_table.$refresh_table_list(true);
                      layer.close(layers)
                    }
                  })
                }
              })
            }
          }, {
            title: '回收站',
            icon: 'trash',
            event: function () {
              bt.recycle_bin.open_recycle_bin(6)
            }
          }]
        }, {
          type: 'batch', //batch_btn
          positon: ['left', 'bottom'],
          placeholder: '请选择批量操作',
          buttonValue: '批量操作',
          disabledSelectValue: '请选择需要批量操作的数据库!',
          selectList: [{
            title: '同步选中',
            url: '/database?action=SyncToDatabases&type=1',
            paramName: 'ids', //列表参数名,可以为空
            paramId: 'id', // 需要传入批量的id
            th: '数据库名称',
            beforeRequest: function (list) {
              var arry = [];
              $.each(list, function (index, item) {
                arry.push(item.id);
              });
              return JSON.stringify(arry)
            },
            success: function (res, list, that) {
              layer.closeAll();
              var html = '';
              $.each(list, function (index, item) {
                html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (res.status ? '#20a53a' : 'red') + '">' + res.msg + '</span></div></td></tr>';
              });
              that.$batch_success_table({
                title: '批量同步选中',
                th: '数据库名称',
                html: html
              });
            }
          }, {
            title: "删除数据库",
            url: '/database?action=DeleteDatabase',
            load: true,
            param: function (row) {
              return {
                id: row.id,
                name: row.name
              }
            },
            callback: function (config) { // 手动执行,data参数包含所有选中的站点
              var ids = [];
              for (var i = 0; i < config.check_list.length; i++) {
                ids.push(config.check_list[i].id);
              }
              database.del_database(ids, function (param) {
                config.start_batch(param, function (list) {
                  layer.closeAll()
                  var html = '';
                  for (var i = 0; i < list.length; i++) {
                    var item = list[i];
                    html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span></div></td></tr>';
                  }
                  that.database_table.$batch_success_table({
                    title: '批量删除',
                    th: '数据库名称',
                    html: html
                  });
                  that.database_table.$refresh_table_list(true);
                });
              })
            }
          }]
        }, {
          type: 'search',
          positon: ['right', 'top'],
          placeholder: '请输入数据库名称/备注',
          searchParam: 'search', //搜索请求字段，默认为 search
          value: '',// 当前内容,默认为空
        }, { //分页显示
          type: 'page',
          positon: ['right', 'bottom'], // 默认在右下角
          pageParam: 'p', //分页请求字段,默认为 : p
          page: 1, //当前分页 默认：1
          numberParam: 'limit', //分页数量请求字段默认为 : limit
          number: 20, //分页数量默认 : 20条
          numberList: [10, 20, 50, 100, 200], // 分页显示数量列表
          numberStatus: true, //　是否支持分页数量选择,默认禁用
          jump: true, //是否支持跳转分页,默认禁用
        }],
        success:function(config){
          //搜索前面新增数据库位置下拉
          if($('.database_type_select_filter').length == 0){
            var _option = '<option value="all">全部</option>'
            $.each(that.cloudDatabaseList,function(index,item){
              var _tips = item.ps != ''?item.ps:item.db_host
              _option +='<option value="'+item.id+'">'+_tips+'</option>'
            })
            $('#bt_database_table .bt_search').before('<select class="bt-input-text mr5 database_type_select_filter" style="width:110px" name="db_type_filter">'+_option+'</select>')

            //事件
            $('.database_type_select_filter').change(function(){
              that.database_table.$refresh_table_list(true);
            })
            $('#bt_database_table ')
          }
        }
      });
    });
  },
  // 同步所有
  sync_to_database: function (obj, callback) {
    bt.database.sync_to_database({
      type: obj.type,
      ids: JSON.stringify(obj.data)
    }, function (rdata) {
      if (callback) callback(rdata);
    });
  },
  // 同步数据库
  database_detail: function (id, dataname) {
    var _that = this
    var cloud_list = { //云存储列表名
      alioss: '阿里云OSS',
      ftp: 'FTP',
      sftp: 'SFTP',
      msonedrive: '微软OneDrive',
      qiniu: '七牛云',
      txcos: '腾讯COS',
      upyun: '又拍云',
      'Google Cloud': '谷歌云',
      'Google Drive': '谷歌网盘',
      bos: '百度云',
      obs: '华为云'
    };
    bt_tools.open({
      area: '850px',
      title: '备份数据库&nbsp;-&nbsp;[&nbsp;' + dataname + '&nbsp;]',
      btn: false,
      skin: 'bt_backup_table',
      content: '<div id="bt_backup_table" class="pd20" style="padding-bottom:40px;"></div>',
      success:function () {
        var backup_table = bt_tools.table({
          el: '#bt_backup_table',
          url: '/data?action=getData',
          param: { table: 'backup', search: id, type: '1', limit:5 },
          default: "[" + dataname + "] 数据库备份列表为空", //数据为空时的默认提示
          column: [
            { type: 'checkbox', class: '', width: 20 },
            { fid: 'name', title: '文件名称', width: 220, fixed: true },
            {
              fid: 'storage_type',
              title: '存储对象',
              type: 'text',
              width: 70,
              template: function (row) {
                var is_cloud = false, cloud_name = '' //当前云存储类型
                if (row.filename.indexOf('|') != -1) {
                  var _path = row.filename;
                  is_cloud = true;
                  cloud_name = _path.match(/\|(.+)\|/, "$1")
                } else {
                  is_cloud = false;
                }
                return is_cloud ? cloud_list[cloud_name[1]] : '本地'
              }
            },
            {
              fid: 'size',
              title: '文件大小',
              width: 80,
              type: 'text',
              template: function (row, index) {
                return bt.format_size(row.size)
              }
            },
            { fid: 'addtime', width: 150, title: '备份时间' },
            { fid: 'ps',
              title: '备注',
              type: 'input',
              blur: function (row, index, ev, key, that) {
                if (row.ps == ev.target.value) return false
                bt.pub.set_data_ps({ id: row.id, table: 'backup', ps: ev.target.value }, function (res) {
                  bt_tools.msg(res, { is_dynamic: true })
                })
              },
              keyup: function (row, index, ev) {
                if (ev.keyCode === 13)  $(this).blur()
              }
            },
            {
              title: '操作',
              type: 'group',
              width: 140,
              align: 'right',
              group: [{
                title: '恢复',
                event: function (row, index, ev, key, that) {
                  var _id = row.id
                  num1 = bt.get_random_num(3, 15),
                  num2 = bt.get_random_num(5, 9),
                  taskID = 0,
                  taskStatus = 0, //0未开始  1正在下载   2下载完成
                  intervalTask = null;
                // 根据id获取对象数据
                  var obj = that.data.filter(function (x) {
                    return x.id === _id
                  })
                  obj = obj[0] //由于filter返回数组所以取第一位
                  var _path = obj.filename,
                    cloud_name = _path.match(/\|(.+)\|/, "$1"),
                    isYun = _path.indexOf('|') != -1;
                  if (!isYun) {
                    bt.database.input_sql(_path, dataname)
                    return
                  }
                  layer.open({
                    type: 1,
                    title: "从云存储恢复",
                    area: ['500px', '350px'],
                    closeBtn: 2,
                    shadeClose: false,
                    skin: 'db_export_restore',
                    content: "<div style='padding: 20px 20px 0 20px;'>" +
                      "<div class='db_export_content'><ul>" +
                      "<li>此备份文件存储在云存储，需要通过以下步骤才能完成恢复：</li>" +
                      "<li class='db_export_txt'>" +
                      "<span>1</span>" +
                      "<div>" +
                      "<p>从[" + cloud_list[cloud_name[1]] + "]下载备份文件到服务器。</p>" +
                      "<p class='btlink'></p>" +
                      "</div>" +
                      "</li>" +
                      "<li class='db_export_txt2'>" +
                      "<span>2</span>" +
                      "<div>" +
                      "<p>恢复备份</p>" +
                      "<p class='btlink'></p>" +
                      "</div>" +
                      "</li>" +
                      "</ul>" +
                      "<p class='db_confirm_txt'style='color:red;margin-bottom: 10px;'>数据库将被覆盖，是否继续？</p>" +
                      "</div>" +
                      "<div class='db_export_vcode db_two_step' style='margin:0'>" + lan.bt.cal_msg + "" +
                      "<span class='text'>" + num1 + " + " + num2 + "</span>=<input type='number' id='vcodeResult' value=''>" +
                      "</div>" +
                      "<div class='bt-form-submit-btn'>" +
                      "<button type='button' class='btn btn-danger btn-sm db_cloud_close'>取消</button>" +
                      "<button type='button' class='btn btn-success btn-sm db_cloud_confirm'>确认</button></div>" +
                      "</div>",
                    success: function (layers, indexs) {
                      // 确认按钮
                      $('.db_export_restore').on('click', '.db_cloud_confirm', function () {
                        var vcodeResult = $('#vcodeResult');
                        if (vcodeResult.val() === '') {
                          layer.tips('计算结果不能为空', vcodeResult, {
                            tips: [1, 'red'],
                            time: 3000
                          })
                          vcodeResult.focus()
                          return false;
                        } else if (parseInt(vcodeResult.val()) !== (num1 + num2)) {
                          layer.tips('计算结果不正确', vcodeResult, {
                            tips: [1, 'red'],
                            time: 3000
                          })
                          vcodeResult.focus()
                          return false;
                        }
                        $('.db_two_step,.db_confirm_txt').remove(); //删除计算
                        $('.db_export_restore .db_export_content li:first').animate({
                          'margin-bottom': '35px'
                        }, 600);
                        $('.db_export_restore .db_cloud_confirm').addClass('hide'); //隐藏确认按钮
                        //请求云储存链接
                        $.post('/cloud', {
                          toserver: true,
                          filename: obj.filename,
                          name: obj.name
                        }, function (res) {
                          taskID = res.task_id
                          if (res.status === false) {
                            layer.msg(res.msg, {
                              icon: 2
                            });
                            return false;
                          } else {
                            // 获取下载进度
                            function downloadDBFile () {
                              $.post('/task?action=get_task_log_by_id', {
                                id: res.task_id,
                                task_type: 1
                              }, function (task) {
                                if (task.status == 1) {
                                  clearInterval(intervalTask)
                                  taskStatus = 2
                                  $('.db_export_txt p:eq(1)').html('下载完成!');
                                  $('.db_export_txt2 p:eq(1)').html('请稍等，正在恢复数据库 <img src="/static/img/ing.gif">');
                                  bt.send('InputSql', 'database/InputSql', {
                                    file: res.local_file,
                                    name: dataname
                                  }, function (rdata) {
                                    layer.close(indexs)
                                    bt.msg(rdata);
                                    console.log('11')
                                  })
                                } else {
                                  taskStatus = 1;
                                  //更新下载进度
                                  $('.db_export_txt p:eq(1)').html('正在下载文件:已下载 ' + task.used + '/' + ToSize(task.total))
                                }
                              })
                            }
                            downloadDBFile();
                            intervalTask = setInterval(function () {
                              downloadDBFile();
                            }, 1500);
                          }
                        })
                      })
                      // 取消按钮
                      $('.db_export_restore').on('click', '.db_cloud_close', function () {
                        switch (taskStatus) {
                          case 1:
                            layer.confirm('正在执行从云存储中下载，是否取消', {
                              title: '下载取消'
                            }, function () {
                              clearInterval(intervalTask) //取消轮询下载进度
                              layer.close(indexs)
                              database.cancel_cloud_restore(taskID)
                            })
                            break;
                          case 2:
                            layer.msg('数据正在恢复中，无法取消', {
                              icon: 2
                            })
                            return false;
                        }
                      })
                    },
                    cancel: function (layers) {
                      switch (taskStatus) {
                        case 0:
                          layer.close(layers);
                          break;
                        case 1:
                          layer.confirm('正在执行从云存储中下载，是否取消', {
                            title: '下载取消'
                          }, function () {
                            clearInterval(intervalTask) //取消轮询下载进度
                            layer.close(layers)
                            database.cancel_cloud_restore(taskID)
                          }, function () {
                            return false;
                          })
                          break;
                        case 2:
                          layer.msg('数据正在恢复中，无法取消', {
                            icon: 2
                          })
                          return false;
                      }
                      return false;
                    }
                  })
                }
              },{
                title: '下载',
                template: function (row, index, ev, key, that) {
                  return '<a target="_blank" class="btlink" href="/download?filename=' + row.filename + '&amp;name=' + row.name + '">下载</a>'
                }
              }, {
                title: '删除',
                event: function (row, index, ev, key, that) {
                  that.del_site_backup({ name: row.name, id: row.id }, function (rdata) {
                    bt_tools.msg(rdata);
                    if (rdata.status) {
                      that.$refresh_table_list();
                      _that.database_table.$refresh_table_list(true)
                    }
                  });
                }
              }]
            }
          ],
          methods: {
            /**
             * @description 删除站点备份
             * @param {object} config 
             * @param {function} callback
             */
            del_site_backup: function (config, callback) {
              bt.confirm({ title: '删除数据库备份', msg: '删除数据库备份[' + config.name + '],是否继续？' }, function () {
                bt_tools.send('database/DelBackup', { id: config.id }, function (rdata) {
                  if (callback) callback(rdata)
                }, true)
              });
            }
          },
          success: function () {
            $('.bt_backup_table').css('top', (($(window).height() - $('.bt_backup_table').height()) / 2) + 'px')
          },
          tootls: [{ // 按钮组
            type: 'group',
            positon: ['left', 'top'],
            list: [{
              title: '备份数据库',
              active: true,
              event: function (ev, that) {
                bt.database.backup_data(id, function (rdata) {
                  bt_tools.msg(rdata);
                  if (rdata.status) {
                    that.$refresh_table_list();
                    _that.database_table.$refresh_table_list(true)
                  }
                });
              }
            }]
          }, {
            type: 'batch',
            positon: ['left', 'bottom'],
            config: {
              title: '删除',
              url: '/site?action=DelBackup',
              paramId: 'id',
              load: true,
              callback: function (that) {
                bt.confirm({ title: '批量删除数据库备份', msg: '是否批量删除选中的数据库备份，是否继续？', icon: 0 }, function (index) {
                  layer.close(index);
                  that.start_batch({}, function (list) {
                    var html = '';
                    for (var i = 0; i < list.length; i++) {
                      var item = list[i];
                      html += '<tr><td><span class="text-overflow" title="' + item.name + '">' + item.name + '</span></td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span></div></td></tr>';
                    }
                    backup_table.$batch_success_table({ title: '批量删除数据库备份', th: '文件名', html: html })
                    backup_table.$refresh_table_list(true)
                    _that.database_table.$refresh_table_list(true)
                  });
                });
              }
            } //分页显示
          }, {
            type: 'page',
            positon: ['right', 'bottom'], // 默认在右下角
            pageParam: 'p', //分页请求字段,默认为 : p
            page: 1, //当前分页 默认：1
            numberParam: 'limit',
            //分页数量请求字段默认为 : limit
            defaultNumber: 10
            //分页数量默认 : 20条
          }]
        })
      }
    });
  },
  // 备份导入》本地导入
  upload_files: function (name) {
    var path = bt.get_cookie('backup_path') + "/database/";
    bt_upload_file.open(path, '.sql,.zip,.bak', lan.database.input_up_type, function () {
      database.input_database(name);
    });
  },
  // 远程服务器列表
  get_cloud_server_list:function(){
    var that = this;
    bt_tools.open({
      title:'远程服务器列表',
      area:'860px',
      btn: false,
      skin: 'databaseCloudServer',
      content: '<div id="db_cloud_server_table" class="pd20" style="padding-bottom:40px;"></div>',
      dataFilter: function(res) { that.cloudDatabaseList = res},
      success:function(){
        that.dbCloudServerTable = bt_tools.table({
          el:'#db_cloud_server_table',
          default:'服务器列表为空',
          url:'/database?action=GetCloudServer',
          column:[
            {fid:'db_host',title:'服务器地址',width:216,template: function (item) {
                return '<span style="width:200px;word-wrap:break-word;" title="'+item.db_host+'">'+item.db_host+'</span>'
              }},
            {fid:'db_port',width:80,title:'数据库端口'},
            {fid:'db_user',title:'管理员名称'},
            {fid:'db_password',type: 'password',title:'管理员密码',copy: true,eye_open: true},
            {fid:'ps',title:'备注',width:170,template: function (item) {
              return '<span class="size_ellipsis" style="width:170px" title="'+item.ps+'">'+item.ps+'</span>'
            }},
            {
              type: 'group',


              title: '操作',
              align: 'right',
              group: [{
                title:'编辑',
                event:function(row){
                  that.render_db_cloud_server_view(row,true);
                }
              },{
                title:'删除',
                event:function(row){
                  that.del_db_cloud_server(row)
                }
              }]
            }
          ],
          tootls:[{
            type:'group',
            positon: ['left','top'],
            list:[{
              title:'添加远程服务器',
              active: true,
              event:function(){that.render_db_cloud_server_view()}
            }]
          }]
        })
      }
    })
  },
  // 添加/编辑远程服务器视图
  render_db_cloud_server_view:function(config,is_edit){
    var that = this;
    if(!config) config = {db_host:'',db_port:'3306',db_user:'',db_password:'',db_user:'root',ps:''}
    bt_tools.open({
      title: (is_edit?'编辑':'添加')+'远程服务器',
      area:'450px',
      btn:['保存','取消'],
      skin:'addCloudServerProject',
      content:{
        'class':'pd20',
        form:[{
          label:'服务器地址',
          group:{
            type:'text',
            name:'db_host',
            width:'260px',
            value:config.db_host,
            placeholder:'请输入服务器地址',
            event:function(){
              $('[name=db_host]').on('input',function(){
                $('[name=db_ps]').val($(this).val())
              })
            }
          }
        },{
          label:'数据库端口',
          group:{
            type:'number',
            name:'db_port',
            width:'260px',
            value:config.db_port,
            placeholder:'请输入数据库端口'
          }
        },{
          label:'管理员名称',
          group:{
            type:'text',
            name:'db_user',
            width:'260px',
            value:config.db_user,
            placeholder:'请输入管理员名称'
          }
        },{
          label:'管理员密码',
          group:{
            type:'text',
            name:'db_password',
            width:'260px',
            value:config.db_password,
            placeholder:'请输入管理员密码'
          }
        },{
          label:'备注',
          group:{
            type:'text',
            name:'db_ps',
            width:'260px',
            value:config.ps,
            placeholder:'服务器备注'
          }
        },{
          group:{
            type:'help',
            style:{'margin-top':'0'},
            list:[
              '支持MySQL5.5、MariaDB10.1及以上版本',
              '支持阿里云、腾讯云等云厂商的云数据库',
              '注意1：请确保本服务器有访问数据库的权限',
              '注意2：请确保填写的管理员帐号具备足够的权限',
            ]
          }
        }]
      },
      yes:function(form,indexs){
        var interface = is_edit?'ModifyCloudServer':'AddCloudServer'
        if(form.db_host == '') return layer.msg('请输入服务器地址',{icon:2})
        if(form.db_port == '') return layer.msg('请输入数据库端口',{icon:2})
        if(form.db_user == '') return layer.msg('请输入管理员名称',{icon:2})
        if(form.db_password == '') return layer.msg('请输入管理员密码',{icon:2})

        if(is_edit) form['id'] = config['id'];
        that.layerT = bt.load('正在'+(is_edit?'修改':'创建')+'远程服务器,请稍候...');
        bt.send(interface,'database/'+interface,form,function(rdata){
          that.layerT.close();
          if(rdata.status){
            that.dbCloudServerTable.$refresh_table_list();
            layer.close(indexs)
            layer.msg(rdata.msg, {icon:1})
          }else{
            layer.msg(rdata.msg,{time:0,icon:2,closeBtn: 2, shade: .3,area: '650px'})
          }
        })
      }
    })
  },
  /**
   * @name 删除导入的文件
   * @author hwliang<2021-09-09>
   * @param {string} filename
   * @param {string} name
   */
  rm_input_file: function (filename, name) {
    bt.files.del_file(filename, function (rdata) {
      bt.msg(rdata);
      database.input_database(name);
    })
  },
  // 备份导入
  input_database: function (name) {
    var path = bt.get_cookie('backup_path') + "/database";

    bt.files.get_files(path, '', function (rdata) {
      var data = [];
      for (var i = 0; i < rdata.FILES.length; i++) {
        if (rdata.FILES[i] == null) continue;
        var fmp = rdata.FILES[i].split(";");
        var ext = bt.get_file_ext(fmp[0]);
        if (ext != 'sql' && ext != 'zip' && ext != 'gz' && ext != 'tgz' && ext != 'bak') continue;
        data.push({
          name: fmp[0],
          size: fmp[1],
          etime: fmp[2],
        })
      }
      if ($('#DataInputList').length <= 0) {
        bt.open({
          type: 1,
          skin: 'demo-class',
          area: ["600px", "478px"],
          title: lan.database.input_title_file,
          closeBtn: 2,
          shift: 5,
          shadeClose: false,
          content: '\
            <div class="pd15">\
              <div class="clearfix">\
                <button class="btn btn-default btn-sm" onclick="database.upload_files(\'' + name + '\')">' + lan.database.input_local_up + '</button>\
                <div class="pull-right">\
                  \
                </div>\
              </div>\
              <div class="divtable mtb15" style="max-height:274px; overflow:auto; border: 1px solid #ddd;">\
                <table id="DataInputList" class="table table-hover" style="border: none;"></table>\
              </div>' +
              bt.render_help([lan.database.input_ps1, lan.database.input_ps2, (bt.os != 'Linux' ? lan.database.input_ps3.replace(/\/www.*\/database/, path) : lan.database.input_ps3)]) +
            '</div>\
          '
        });
      }
      setTimeout(function () {
        bt.fixed_table('DataInputList');
        bt.render({
          table: '#DataInputList',
          columns: [{
            field: 'name',
            title: lan.files.file_name
          },
          {
            field: 'etime',
            title: lan.files.file_etime,
            templet: function (item) {
              return bt.format_data(item.etime);
            }
          },
          {
            field: 'size',
            title: lan.files.file_size,
            templet: function (item) {
              return bt.format_size(item.size)
            }
          },
          {
            field: 'opt',
            title: '操作',
            align: 'right',
            templet: function (item) {
              return '<a class="btlink" herf="javascrpit:;" onclick="bt.database.input_sql(\'' + bt.rtrim(rdata.PATH, '/') + "/" + item.name + '\',\'' + name + '\')">导入</a>  | <a class="btlink" herf="javascrpit:;" onclick="database.rm_input_file(\'' + bt.rtrim(rdata.PATH, '/') + "/" + item.name + '\',\'' + name + '\')">删除</a>';
            }
          },
          ],
          data: data
        });
      }, 100)
    }, 'mtime')
  },
  // 工具
  rep_tools: function (db_name, res) {
    var loadT = layer.msg('正在获取数据,请稍候...', {
      icon: 16,
      time: 0
    });
    bt.send('GetInfo', 'database/GetInfo', {
      db_name: db_name
    }, function (rdata) {
      layer.close(loadT)
      if (rdata.status === false) {
        layer.msg(rdata.msg, {
          icon: 2
        });
        return;
      }
      var types = {
        InnoDB: "MyISAM",
        MyISAM: "InnoDB"
      };
      var tbody = '';
      for (var i = 0; i < rdata.tables.length; i++) {
        if (!types[rdata.tables[i].type]) continue;
        tbody += '<tr>\
                        <td><input value="dbtools_' + rdata.tables[i].table_name + '" class="check" onclick="database.selected_tools(null,\'' + db_name + '\');" type="checkbox"></td>\
                        <td><span style="width:220px;"> ' + rdata.tables[i].table_name + '</span></td>\
                        <td>' + rdata.tables[i].type + '</td>\
                        <td><span style="width:90px;"> ' + rdata.tables[i].collation + '</span></td>\
                        <td>' + rdata.tables[i].rows_count + '</td>\
                        <td>' + rdata.tables[i].data_size + '</td>\
                        <td style="text-align: right;">\
                            <a class="btlink" onclick="database.rep_database(\'' + db_name + '\',\'' + rdata.tables[i].table_name + '\')">修复</a> |\
                            <a class="btlink" onclick="database.op_database(\'' + db_name + '\',\'' + rdata.tables[i].table_name + '\')">优化</a> |\
                            <a class="btlink" onclick="database.to_database_type(\'' + db_name + '\',\'' + rdata.tables[i].table_name + '\',\'' + types[rdata.tables[i].type] + '\')">转为' + types[rdata.tables[i].type] + '</a>\
                        </td>\
                    </tr> '
      }

      if (res) {
        $(".gztr").html(tbody);
        $("#db_tools").html('');
        $("input[type='checkbox']").attr("checked", false);
        $(".tools_size").html('大小：' + rdata.data_size);
        return;
      }

      layer.open({
        type: 1,
        title: "MySQL工具箱【" + db_name + "】",
        area: ['780px', '580px'],
        closeBtn: 2,
        shadeClose: false,
        content: '<div class="pd15">\
                                <div class="db_list">\
                                    <span><a>数据库名称：' + db_name + '</a>\
                                    <a class="tools_size">大小：' + rdata.data_size + '</a></span>\
                                    <span id="db_tools" style="float: right;"></span>\
                                </div >\
                                <div class="divtable">\
                                <div  id="database_fix"  style="height:360px;overflow:auto;border:#ddd 1px solid">\
                                <table class="table table-hover "style="border:none">\
                                    <thead>\
                                        <tr>\
                                            <th><input class="check" onclick="database.selected_tools(this,\'' + db_name + '\');" type="checkbox"></th>\
                                            <th>表名</th>\
                                            <th>引擎</th>\
                                            <th>字符集</th>\
                                            <th>行数</th>\
                                            <th>大小</th>\
                                            <th style="text-align: right;">操作</th>\
                                        </tr>\
                                    </thead>\
                                    <tbody class="gztr">' + tbody + '</tbody>\
                                </table>\
                                </div>\
                            </div>\
                            <ul class="help-info-text c7">\
                                <li>【修复】尝试使用REPAIR命令修复损坏的表，仅能做简单修复，若修复不成功请考虑使用myisamchk工具</li>\
                                <li>【优化】执行OPTIMIZE命令，可回收未释放的磁盘空间，建议每月执行一次</li>\
                                <li>【转为InnoDB/MyISAM】转换数据表引擎，建议将所有表转为InnoDB</li>\
                            </ul></div>'
      });
      tableFixed('database_fix');
      //表格头固定
      function tableFixed (name) {
        var tableName = document.querySelector('#' + name);
        tableName.addEventListener('scroll', scrollHandle);
      }

      function scrollHandle (e) {
        var scrollTop = this.scrollTop;
        //this.querySelector('thead').style.transform = 'translateY(' + scrollTop + 'px)';
        $(this).find("thead").css({
          "transform": "translateY(" + scrollTop + "px)",
          "position": "relative",
          "z-index": "1"
        });
      }
    });
  },
  selected_tools: function (my_obj, db_name) {
    var is_checked = false
    if (my_obj) is_checked = my_obj.checked;
    var db_tools = $("input[value^='dbtools_']");
    var n = 0;
    for (var i = 0; i < db_tools.length; i++) {
      if (my_obj) db_tools[i].checked = is_checked;
      if (db_tools[i].checked) n++;
    }
    if (n > 0) {
      var my_btns = '<button class="btn btn-default btn-sm" onclick="database.rep_database(\'' + db_name + '\',null)">修复</button><button class="btn btn-default btn-sm" onclick="database.op_database(\'' + db_name + '\',null)">优化</button><button class="btn btn-default btn-sm" onclick="database.to_database_type(\'' + db_name + '\',null,\'InnoDB\')">转为InnoDB</button></button><button class="btn btn-default btn-sm" onclick="database.to_database_type(\'' + db_name + '\',null,\'MyISAM\')">转为MyISAM</button>'
      $("#db_tools").html(my_btns);
    } else {
      $("#db_tools").html('');
    }
  },
  rep_database: function (db_name, tables) {
    dbs = database.rep_checkeds(tables)
    var loadT = layer.msg('已送修复指令,请稍候...', {
      icon: 16,
      time: 0
    });
    bt.send('ReTable', 'database/ReTable', {
      db_name: db_name,
      tables: JSON.stringify(dbs)
    }, function (rdata) {
      layer.close(loadT)

      database.rep_tools(db_name, true);
      layer.msg(rdata.msg, {
        icon: rdata.status ? 1 : 2
      });
    });
  },
  op_database: function (db_name, tables) {
    dbs = database.rep_checkeds(tables)
    var loadT = layer.msg('已送优化指令,请稍候...', {
      icon: 16,
      time: 0
    });
    bt.send('OpTable', 'database/OpTable', {
      db_name: db_name,
      tables: JSON.stringify(dbs)
    }, function (rdata) {
      layer.close(loadT)

      database.rep_tools(db_name, true);
      layer.msg(rdata.msg, {
        icon: rdata.status ? 1 : 2
      });
    });
  },
  to_database_type: function (db_name, tables, type) {
    dbs = database.rep_checkeds(tables)
    var loadT = layer.msg('已送引擎转换指令,请稍候...', {
      icon: 16,
      time: 0,
      shade: [0.3, "#000"]
    });
    bt.send('AlTable', 'database/AlTable', {
      db_name: db_name,
      tables: JSON.stringify(dbs),
      table_type: type
    }, function (rdata) {
      layer.close(loadT);

      database.rep_tools(db_name, true);
      layer.msg(rdata.msg, {
        icon: rdata.status ? 1 : 2
      });
    });
  },
  rep_checkeds: function (tables) {
    var dbs = []
    if (tables) {
      dbs.push(tables)
    } else {
      var db_tools = $("input[value^='dbtools_']");
      for (var i = 0; i < db_tools.length; i++) {
        if (db_tools[i].checked) dbs.push(db_tools[i].value.replace('dbtools_', ''));
      }
    }

    if (dbs.length < 1) {
      layer.msg('请至少选择一张表!', {
        icon: 2
      });
      return false;
    }
    return dbs;
  },
  // 改密
  set_data_pass: function (id, username, password) {
    var that = this,
      bs = bt.database.set_data_pass(function (rdata) {
        if (rdata.status) that.database_table.$refresh_table_list(true);
        bt.msg(rdata);
      })
    $('.name' + bs).val(username);
    $('.id' + bs).val(id);
    $('.password' + bs).val(password);
  },
  // 删除
  del_database: function (wid, dbname,obj, callback) {
    var rendom = bt.get_random_code(),
      num1 = rendom['num1'],
      num2 = rendom['num2'],
      title = '',
      tips = '是否确认【删除数据库】，删除后可能会影响业务使用！';
    if(obj && obj.db_type > 0) tips = '远程数据库不支持数据库回收站，删除后将无法恢复，请谨慎操作';
    title = typeof dbname === "function" ? '批量删除数据库' : '删除数据库 [ ' + dbname + ' ]';
    layer.open({
      type: 1,
      title: title,
      icon: 0,
      skin: 'delete_site_layer',
      area: "530px",
      closeBtn: 2,
      shadeClose: true,
      content: "<div class=\'bt-form webDelete pd30\' id=\'site_delete_form\'>" +
        "<i class=\'layui-layer-ico layui-layer-ico0\'></i>" +
        "<div class=\'f13 check_title\' style=\'margin-bottom: 20px;\'>"+tips+"</div>" +
        "<div style=\'color:red;margin:18px 0 18px 18px;font-size:14px;font-weight: bold;\'>注意：数据无价，请谨慎操作！！！" + (!recycle_bin_db_open ? '<br>风险操作：当前数据库回收站未开启，删除数据库将永久消失！' : '') + "</div>" +
        "<div class=\'vcode\'>" + lan.bt.cal_msg + "<span class=\'text\'>" + num1 + " + " + num2 + "</span>=<input type=\'number\' id=\'vcodeResult\' value=\'\'></div>" +
        "</div>",
      btn: [lan.public.ok, lan.public.cancel],
      yes: function (indexs) {
        var vcodeResult = $('#vcodeResult'),
          data = {
            id: wid,
            name: dbname
          };
        if (vcodeResult.val() === '') {
          layer.tips('计算结果不能为空', vcodeResult, {
            tips: [1, 'red'],
            time: 3000
          })
          vcodeResult.focus()
          return false;
        } else if (parseInt(vcodeResult.val()) !== (num1 + num2)) {
          layer.tips('计算结果不正确', vcodeResult, {
            tips: [1, 'red'],
            time: 3000
          })
          vcodeResult.focus()
          return false;
        }
        if (typeof dbname === "function") {
          delete data.id;
          delete data.name;
        }
        layer.close(indexs)
        var arrs = wid instanceof Array ? wid : [wid]
        var ids = JSON.stringify(arrs),
          countDown = 9;
        if (arrs.length == 1) countDown = 4
        title = typeof dbname === "function" ? '二次验证信息，批量删除数据库' : '二次验证信息，删除数据库 [ ' + dbname + ' ]';
        var loadT = bt.load('正在检测数据库数据信息，请稍候...')
        bt.send('check_del_data', 'database/check_del_data', {
          ids: ids
        }, function (res) {
          loadT.close()
          layer.open({
            type: 1,
            title: title,
            closeBtn: 2,
            skin: 'verify_site_layer_info active',
            area: '740px',
            content: '<div class="check_delete_site_main pd30">' +
              '<i class="layui-layer-ico layui-layer-ico0"></i>' +
              '<div class="check_layer_title">堡塔温馨提示您，请冷静几秒钟，确认以下要删除的数据。</div>' +
              '<div class="check_layer_content">' +
              '<div class="check_layer_item">' +
              '<div class="check_layer_site"></div>' +
              '<div class="check_layer_database"></div>' +
              '</div>' +
              '</div>' +
              '<div class="check_layer_error ' + (recycle_bin_db_open ? 'hide' : '') + '"><span class="glyphicon glyphicon-info-sign"></span>风险事项：当前未开启数据库回收站功能，删除数据库后，数据库将永久消失！</div>' +
              '<div class="check_layer_message">请仔细阅读以上要删除信息，防止数据库被误删，确认删除还有 <span style="color:red;font-weight: bold;">' + countDown + '</span> 秒可以操作。</div>' +
              '</div>',
            btn: ['确认删除(' + countDown + '秒后继续操作)', '取消删除'],
            success: function (layers) {
              var html = '',
                rdata = res.data;
              var filterData = rdata.filter(function (el) {
                return ids.indexOf(el.id) != -1
              })
              for (var i = 0; i < filterData.length; i++) {
                var item = filterData[i],
                  newTime = parseInt(new Date().getTime() / 1000),
                  t_icon = '<span class="glyphicon glyphicon-info-sign" style="color: red;width:15px;height: 15px;;vertical-align: middle;"></span>';

                database_html = (function (item) {
                  var is_time_rule = (newTime - item.st_time) > (86400 * 30) && (item.total > 1024 * 10),
                    is_database_rule = res.db_size <= item.total,
                    database_time = bt.format_data(item.st_time, 'yyyy-MM-dd'),
                    database_size = bt.format_size(item.total);

                  var f_size = '<i ' + (is_database_rule ? 'class="warning"' : '') + ' style = "vertical-align: middle;" > ' + database_size + '</i> ' + (is_database_rule ? t_icon : '');
                  var t_size = '注意：此数据库较大，可能为重要数据，请谨慎操作.\n数据库：' + database_size;
                  if (item.total < 2048) t_size = '注意事项：当前数据库不为空，可能为重要数据，请谨慎操作.\n数据库：' + database_size;
                  if (item.total === 0) t_size = '';
                  return '<div class="check_layer_database">' +
                    '<span title="数据库：' + item.name + '">数据库：' + item.name + '</span>' +
                    '<span title="' + t_size + '">大小：' + f_size + '</span>' +
                    '<span title="' + (is_time_rule && item.total != 0 ? '重要：此数据库创建时间较早，可能为重要数据，请谨慎操作.' : '') + '时间：' + database_time + '">创建时间：<i ' + (is_time_rule && item.total != 0 ? 'class="warning"' : '') + '>' + database_time + '</i></span>' +
                    '</div>'
                }(item))
                if (database_html !== '') html += '<div class="check_layer_item">' + database_html + '</div>';
              }
              if (html === '') html = '<div style="text-align: center;width: 100%;height: 100%;line-height: 300px;font-size: 15px;">无数据</div>'
              $('.check_layer_content').html(html)
              var interVal = setInterval(function () {
                countDown--;
                $(layers).find('.layui-layer-btn0').text('确认删除(' + countDown + '秒后继续操作)')
                $(layers).find('.check_layer_message span').text(countDown)
              }, 1000);
              setTimeout(function () {
                $(layers).find('.layui-layer-btn0').text('确认删除');
                $(layers).find('.check_layer_message').html('<span style="color:red">注意：请仔细阅读以上要删除信息，防止数据库被误删</span>')
                $(layers).removeClass('active');
                clearInterval(interVal)
              }, countDown * 1000)
            },
            yes: function (indes, layers) {
              console.log(1);
              if ($(layers).hasClass('active')) {
                layer.tips('请确认信息，稍候在尝试，还剩' + countDown + '秒', $(layers).find('.layui-layer-btn0'), {
                  tips: [1, 'red'],
                  time: 3000
                })
                return;
              }
              if (typeof dbname === "function") {
                dbname(data)
              } else {
                bt.database.del_database(data, function (rdata) {
                  layer.closeAll()
                  if (callback) callback(rdata);
                  bt.msg(rdata);
                })
              }
            }
          })
        })
      }
    })
  },
  // 删除远程服务器管理关系
  del_db_cloud_server: function(row){
    var that = this;
    layer.confirm('仅删除管理关系以及面板中的数据库记录，不会删除远程服务器中的数据', {
      title: '删除【'+row.db_host+'】远程服务器',
      icon: 0,
      closeBtn: 2
    }, function () {
      bt.send('RemoveCloudServer','database/RemoveCloudServer',{id:row.id},function(rdata){
        if(rdata.status) that.dbCloudServerTable.$refresh_table_list(true);
        layer.msg(rdata.msg, {
          icon: rdata.status ? 1 : 2
        })
      })
    })
  }
}
database.init();
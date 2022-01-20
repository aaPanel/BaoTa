var initTab = [];
$('#cutMode .tabs-item').on('click', function () {
  var type = $(this).data('type'),
    index = $(this).index();
  $(this).addClass('active').siblings().removeClass('active');
  $('.tab-con').find('.tab-con-block').eq(index).removeClass('hide').siblings().addClass('hide');
  switch (type) {
    case 'php':
      $('#bt_site_table').empty();
      // if (!isSetup) $('.site_table_view .mask_layer').removeClass('hide').find('.prompt_description.web-model').html('未安装Web服务器，<a href="javascript:;" class="btlink" onclick="bt.soft.install(\'nginx\')">安装Nginx</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="javascript:;" class="btlink" onclick="bt.soft.install(\'apache\')">安装Apache</a>');
      site.php_table_view();
      site.get_types();
      break;
    case 'nodejs':
      $('#bt_node_table').empty();
      $('.site_class_type').remove()
      $.get('/plugin?action=getConfigHtml', {
        name: "nodejs"
      }, function (res) {
        if (typeof res !== 'string') $('#bt_node_table+.mask_layer').removeClass('hide').find('.prompt_description.node-model').html('未安装Node版本管理器，<a href="javascript:;" class="btlink" onclick="bt.soft.install(\'nodejs\')">点击安装</a>');
      })
      site.node_porject_view();
      break;
    case 'java':
      $('.site_class_type').remove()
      if (initTab.indexOf(2) > -1) {
        javaModle.get_project_list()
      } else {
        dynamic.require(['vue.min.js', 'polyfill.min.js', 'vue-components.js', 'java-model.js'], function () {
          initTab.push(index)
        })
      }
      break;
  }
  bt.set_cookie('site_model', type);
});

var site = {
  node: {
    /**
     * @description 选择路径配置
     * @return config {object} 选中文件配置
     *
     */
    get_project_select_path: function (path) {
      var that = this;
      return {
        type: 'text',
        width: '420px',
        name: 'project_script',
        value: path,
        placeholder: '请选择项目启动文件/输入启动命令，不可为空',
        icon: {
          type: 'glyphicon-folder-open',
          select: 'file',
          event: function (ev) { }
        }
      }
    },
    get_project_select: function (path) {
      var that = this;
      return {
        type: 'select',
        name: 'project_script',
        width: '220px',
        disabled: true,
        unit: '* 自动获取package.json文件中的启动模式',
        placeholder: '请选择项目目录继续操作',
        list: path ? function (configs) {
          that.get_project_script_list(path, configs[2], this)
        } : [],
        change: function (formData, elements, formConfig) {
          var project_script = $("[data-name=\'project_script\']");
          if (formData.project_script === '') {
            if ($("#project_script_two").length === 0) {
              project_script.parent().after('<div class="inlineBlock"><input type="text" name="project_script_two" id="project_script_two" placeholder="请选择项目启动文件和启动命令，不可为空" class="mt5 bt-input-text mr10 " style="width:420px;" value="" /><span class="glyphicon glyphicon-folder-open cursor" onclick="bt.select_path(\'project_script_two\',\'file\',null,\'' + path + '\')" style="margin-right: 18px;"></span></div>')
            }
          } else {
            project_script.parent().next().remove();
          }
        }
      }
    },

    /**
     * @description 选择启动脚本配置
     * @param path {string} 项目目录
     * @param form {object} 表单元素
     * @param formObject {object} 表单对象
     * @return config {object} 选中文件配置
     */
    get_project_script_list: function (path, form, formObject) {
      var that = this;
      that.get_start_command({ project_cwd: path }, function (res) {
        var arry = [];
        for (var resKey in res) {
          arry.push({ title: resKey + ' 【' + res[resKey] + '】', value: resKey })
        }
        arry.push({ title: '自定义启动命令', value: '' })
        form.group = that.get_project_select(path);
        form.group.list = arry;
        form.group.disabled = false;
        formObject.$replace_render_content(2)
        if (arry.length === 1) {
          var project_script = $("[data-name=\'project_script\']");
          // form.group.value = '';
          project_script.parent().after('<div class="inlineBlock"><input type="text" name="project_script_two" id="project_script_two" placeholder="请选择项目启动文件和启动命令，不可为空" class="mt5 bt-input-text mr10 " style="width:420px;" value="" /><span class="glyphicon glyphicon-folder-open cursor" onclick="bt.select_path(\'project_script_two\',\'file\',null,\'' + path + '\')" style="margin-right: 18px;"></span></div>')
        }
      }, function () {
        form.label = '启动文件/命令';
        form.group = that.get_project_select_path(path);
        formObject.$replace_render_content(2)
      })
      return [];
    },

    /**
     *
     * @description 获取Node版本列表
     * @return {{dataFilter: (function(*): *[]), url: string}}
     */
    get_node_version_list: function () {
      return {
        url: '/project/nodejs/get_nodejs_version',
        dataFilter: function (res) {
          if (res.length === 0) {
            layer.closeAll();
            bt.soft.set_lib_config('nodejs', 'Node.js版本管理器')
            bt.msg({ status: false, msg: '请至少安装一个Node版本，才可以继续添加Node项目' });
            return;
          }
          var arry = [];
          for (var i = 0; i < res.length; i++) {
            arry.push({ title: res[i], value: res[i] })
          }
          return arry;
        }
      }
    },


    /**
     * @description 获取Node通用Form配置
     * @param config {object} 获取配置参数
     * @return form模板
     */
    get_node_general_config: function (config) {
      config = config || {}
      var that = this,
        formLineConfig = [{
          label: '项目目录',
          group: {
            type: 'text',
            width: '420px',
            name: 'project_cwd',
            readonly: true,
            icon: {
              type: 'glyphicon-folder-open',
              event: function (ev) { },
              callback: function (path) {
                var filename = path.split('/');
                var project_script_config = this.config.form[2],
                  project_name_config = this.config.form[1],
                  project_ps_config = this.config.form[6];
                project_name_config.group.value = filename[filename.length - 1];
                project_ps_config.group.value = filename[filename.length - 1];
                project_script_config.group.disabled = false;
                this.$replace_render_content(1)
                this.$replace_render_content(6)
                that.get_project_script_list(path, project_script_config, this)
              }
            },
            value: bt.get_cookie('sites_path') ? bt.get_cookie('sites_path') : '/www/wwwroot',
            placeholder: '请选择项目目录'
          }
        }, {
          label: '项目名称',
          group: {
            type: 'text',
            name: 'project_name',
            width: '420px',
            placeholder: '请输入Node项目名称',
            input: function (formData, formElement, formConfig) {
              var project_ps_config = formConfig.config.form[6];
              project_ps_config.group.value = formData.project_name;
              formConfig.$replace_render_content(6)
            }
          }
        }, {
          label: '启动选项',
          group: (function () {
            return that.get_project_select(config.path)
          }())
        }, {
          label: '项目端口',
          group: {
            type: 'number',
            name: 'port',
            width: '220px',
            placeholder: '请输入项目的真实端口',
            unit: '* 请输入项目的真实端口',
          }
        }, {
          label: '运行用户',
          group: {
            type: 'select',
            name: 'run_user',
            width: '150px',
            unit: '* 无特殊需求请选择www用户',
            list: [{ title: 'www', value: 'www' }, { title: 'root', value: 'root' }],
            tips: ''
          }
        }, {
          label: 'Node版本',
          group: {
            type: 'select',
            name: 'nodejs_version',
            width: '150px',
            unit: '* 请根据项目选择合适的Node版本，<a href="javascript:;" class="btlink" onclick="bt.soft.set_lib_config(\'nodejs\',\'Node.js版本管理器\')">安装其他版本</a>',
            list: (function () {
              return that.get_node_version_list()
            })()
          }
        }, {
          label: '备注',
          group: {
            type: 'text',
            name: 'project_ps',
            width: '420px',
            placeholder: '请输入项目备注',
            value: config.ps,
          }
        }, {
          label: '绑定域名',
          group: {
            type: 'textarea', //当前表单的类型 支持所有常规表单元素、和复合型的组合表单元素
            name: 'domains', //当前表单的name
            style: { 'width': '420px', 'height': '120px', 'line-height': '22px' },
            tips: { //使用hover的方式显示提示
              text: '<span>如果需要绑定外网，请输入需要绑定的域名，该选项可为空</span><br>如需填写多个域名，请换行填写，每行一个域名，默认为80端口<br>泛解析添加方法 *.domain.com<br>如另加端口格式为 www.domain.com:88',
              style: { top: '10px', left: '15px' },
            }
          }
        }, {
          group: {
            type: 'help',
            list: [
              '【启动选项】：默认读取package.json中的scripts列表，也可以选择[自定义启动命令]选项来手动输入启动命令',
              '【自定义启动命令】：可以选择启动文件，或直接输入启动命令，支持的启动方式：npm/node/pm2/yarn',
              '【项目端口】：错误的端口会导致访问502，若不知道端口，可先随意填写，启动项目后再改为正确端口',
              '【运行用户】：为了安全考虑，默认使用www用户运行，root用户运行可能带来安全风险'
            ]
          }
        }]

      if (config.path) {
        formLineConfig.splice(-1, 1)
        return formLineConfig.concat([{
          label: '开机启动',
          group: {
            type: 'checkbox',
            name: 'is_power_on',
            width: '220px',
            title: '跟随系统启动服务',
          }
        }, {
          label: '',
          group: {
            type: 'button',
            name: 'saveNodeConfig',
            title: '保存配置',
            event: function (data, form, that) {
              if (data.project_cwd === '') {
                bt.msg({ status: false, msg: '项目目录不能为空' })
                return false
              }
              var project_script_two = $('[name="project_script_two"]');
              if (data.project_script === '' && project_script_two.length < 1 || project_script_two.length > 1 && project_script_two.val() === '') {
                bt.msg({ status: false, msg: '启动文件/命令不能为空' })
                return false
              }
              if (data.port === '') {
                bt.msg({ status: false, msg: '项目端口不能为空' })
                return false
              }
              if (data.project_script === '') {
                data.project_script = project_script_two.val()
                delete data.project_script_two
              }
              config.callback(data, form, that)
            }
          }
        }])
      }
      return formLineConfig;
    },

    /**
     * @description 添加node项目表单
     * @returns {{form: 当前实例对象, close: function(): void}}
     */
    add_node_form: function (callback) {
      var that = this;
      var add_node_project = bt_tools.open({
        title: "添加Node项目",
        area: '700px',
        btn: ['提交', '取消'],
        content: {
          class: 'pd30',
          form: (function () {
            return that.get_node_general_config({
              form: add_node_project
            })
          })()
        },
        yes: function (form, indexs, layers) {
          var defaultParam = {
            bind_extranet: 0,
            is_power_on: 1,
            max_memory_limit: 4096,
            project_env: ''
          }
          if (form.domains !== '') {
            var arry = form.domains.replace('\n', '').split('\r'), newArry = []
            for (var i = 0; i < arry.length; i++) {
              var item = arry[i];
              if (bt.check_domain(item)) {
                newArry.push(item.indexOf(':') > -1 ? item : item + ':80')
              } else {
                bt.msg({ status: false, msg: '【' + item + '】 绑定域名格式错误' })
                break;
              }
            }
            defaultParam.bind_extranet = 1
            defaultParam.domains = newArry
          }
          if (form.project_name === '') {
            bt.msg({ status: false, msg: '项目名称不能为空' })
            return false
          }
          var project_script_two = $('[name="project_script_two"]');
          if (project_script_two.length && project_script_two.val() === '') {
            bt.msg({ status: false, msg: '请输入自定义启动命令，不能为空！' });
            return false
          }
          if (form.port === '') {
            bt.msg({ status: false, msg: '项目端口不能为空' })
            return false
          }
          if (form.project_script === null) {
            bt.msg({ status: false, msg: '请选择项目目录，获取启动命令！' })
            return false
          }
          form = $.extend(form, defaultParam)
          if (project_script_two.length) {
            form.project_script = project_script_two.val()
            delete form.project_script_two
          }
          var _command = null;
          setTimeout(function () {
            if (_command < 0) return false;
            _command = that.request_module_log_command({ shell: 'tail -f /www/server/panel/logs/npm-exec.log' })
          }, 500);
          site.node.add_node_project(form, function (res) {
            if (!res.status) _command = -1
            if (_command > 0) layer.close(_command)
            if (callback) callback(res, indexs)
          })
        }
      })
      return add_node_project;
    },

    /**
     * @description 添加node项目请求
     * @param param {object} 请求参数
     * @param callback {function} 回调函数
     */
    add_node_project: function (param, callback) {
      this.http({ create_project: false, verify: false }, param, callback)
    },

    /**
     * @description 获取Node环境
     * @param callback {function} 回调函数
     */
    get_node_environment: function (callback) {
      bt_tools.send({
        url: '/project/nodejs/is_install_nodejs'
      }, function (res) {
        if (callback) callback(res);
      }, { load: '获取Node项目环境' })
    },

    /**
     * @description 编辑Node项目请求
     * @param param {object} 请求参数
     * @param callback {function} 回调函数
     */
    modify_node_project: function (param, callback) {
      this.http({ modify_project: '修改Node项目配置' }, param, callback)
    },

    /**
     * @description 删除Node项目请求
     * @param param {object} 请求参数
     * @param callback {function} 回调函数
     */
    remove_node_project: function (param, callback) {
      this.http({ remove_project: '删除Node项目' }, param, callback)
    },

    /**
     * @description 获取node项目域名
     * @param callback {function} 回调行数
     */
    get_node_project_domain: function (callback) {
      this.http({ project_get_domain: '获取Node项目域名列表' }, callback)
    },

    /**
     * @description 获取启动命令列表
     * @param param {object} 请求参数
     * @param callback {function} 成功回调行数
     * @param callback1 {function} 错误回调行数
     */
    get_start_command: function (params, callback, callback1) {
      this.http({ get_run_list: '获取项目启动命令' }, params, callback, callback1)
    },
    /**
     * @description 添加Node项目域名
     * @param param {object} 请求参数
     * @param callback {function} 回调行数
     */
    add_node_project_domain: function (param, callback) {
      this.http({ project_add_domain: false, verify: false }, param, callback)
    },

    /**
     * @description 删除Node项目域名
     * @param param {object} 请求参数
     * @param callback {function} 回调行数
     */
    remove_node_project_domain: function (param, callback) {
      var that = this;
      bt.confirm({
        title: '删除域名【' + param.domain.split(':')[0] + '】',
        msg: '您真的要从站点中删除这个域名吗？'
      }, function () {
        that.http({ project_remove_domain: '删除Node项目域名' }, param, callback)
      });
    },

    /**
     * @description 启动Node项目
     * @param param {object} 请求参数
     * @param callback {function} 回调行数
     */
    start_node_project: function (param, callback) {
      this.http({ start_project: '启用Node项目' }, param, callback)
    },

    /**
     * @description 停止Node项目
     * @param param {object} 请求参数
     * @param callback {function} 回调行数
     */
    stop_node_project: function (param, callback) {
      this.http({ stop_project: '停止Node项目' }, param, callback)
    },

    /**
     * @description 重启Node项目
     * @param param {object} 请求参数
     * @param callback {function} 回调行数
     */
    restart_node_project: function (param, callback) {
      this.http({ restart_project: '重启Node项目' }, param, callback)
    },

    /**
     * @description 获取值指定Node项目信息
     * @param param {object} 请求参数
     * @param callback {function} 回调行数
     */
    get_node_project_info: function (param, callback) {
      this.http({ get_project_info: '获取Node项目信息' }, param, callback)
    },

    /**
     * @description 绑定外网映射
     * @param param {object} 请求参数
     * @param callback {function} 回调行数
     */
    bind_node_project_map: function (param, callback) {
      this.http({ bind_extranet: '绑定映射', verify: false }, param, callback)
    },
    /**
     * @description 绑定外网映射
     * @param param {object} 请求参数
     * @param callback {function} 回调行数
     */
    unbind_node_project_map: function (param, callback) {
      this.http({ unbind_extranet: '解绑映射', verify: false }, param, callback)
    },
    /**
     * @description 安装node项目依赖
     * @param param {object} 请求参数
     * @param callback {function} 回调行数
     */
    install_node_project_packages: function (param, callback) {
      this.http({ install_packages: false, verify: false }, param, callback)
    },

    /**
     * @description 安装指定模块
     * @param param {object} 请求参数
     * @param callback {function} 回调行数
     */
    npm_install_node_module: function (param, callback) {
      this.http({ install_module: '安装Node模块' }, param, callback)
    },
    /**
     * @description 更新指定模块
     * @param param {object} 请求参数
     * @param callback {function} 回调行数
     */
    upgrade_node_module: function (param, callback) {
      this.http({ upgrade_module: '更新Node模块' }, param, callback)
    },/**
         * @description 删除指定模块
         * @param param {object} 请求参数
         * @param callback {function} 回调行数
         */
    uninstall_node_module: function (param, callback) {
      this.http({ uninstall_module: '卸载Node模块' }, param, callback)
    },
    /**
     * @description 模拟点击
     */
    simulated_click: function (num) {
      $('.bt-w-menu p:eq(' + num + ')').click();
    },
    /**
     * @description 获取Node项目信息
     * @param row {object} 当前行，项目信息
     */
    set_node_project_view: function (row) {
      var that = this;
      bt.open({
        type: 1,
        title: 'Node项目管理-[' + row.name + ']，添加时间[' + row.addtime + ']',
        skin: 'node_project_dialog',
        area: ['780px', '720px'],
        content: '<div class="bt-tabs">' +
          '<div class="bt-w-menu site-menu pull-left"></div>' +
          '<div id="webedit-con" class="bt-w-con pd15" style="height:100%">' +
          '</div>' +
          '<div class="mask_module hide" style="left:110px;"><div class="node_mask_module_text">请开启<a href="javascript:;" class="btlink mapExtranet" onclick="site.node.simulated_click(2)"> 外网映射 </a>后查看配置信息</div></div>' +
          '</div>',
        btn: false,
        success: function (layers) {
          var $layers = $(layers), $content = $layers.find('#webedit-con');
          function reander_tab_list (config) {
            for (var i = 0; i < config.list.length; i++) {
              var item = config.list[i], tab = $('<p class="' + (i === 0 ? 'bgw' : '') + '">' + item.title + '</p>');
              $(config.el).append(tab);
              (function (i, item) {
                tab.on('click', function (ev) {
                  $('.mask_module').addClass('hide');
                  $(this).addClass('bgw').siblings().removeClass('bgw');
                  if ($(this).hasClass('bgw')) {
                    that.get_node_project_info({ project_name: row.name }, function (res) {
                      config.list[i].event.call(that, $content, res, ev)
                    })
                  }
                })
                if (item.active) tab.click()
              }(i, item))
            }
          }
          reander_tab_list({
            el: $layers.find('.bt-w-menu'),
            list: [{
              title: '项目配置',
              active: true,
              event: that.reander_node_project_config
            }, {
              title: '域名管理',
              event: that.reander_node_domain_manage
            }, {
              title: '外网映射',
              event: that.reander_node_project_map,
            }, {
              title: '伪静态',
              event: that.reander_node_project_rewrite
            }, {
              title: '配置文件',
              event: that.reander_node_file_config
            }, {
              title: 'SSL',
              event: that.reander_node_project_ssl
            }, {
              title: '负载状态',
              event: that.reander_node_service_condition
            }, {
              title: '服务状态',
              event: that.reander_node_service_status
            }, {
              title: '模块管理',
              event: that.reander_node_project_module
            }, {
              title: '项目日志',
              event: that.reander_node_project_log
            }, {
              title: '网站日志',
              event: that.reander_node_site_log
            }]

          })
        }
      })
    },

    /**
     * @description 渲染Node项目配置视图
     * @param el {object} 当前element节点
     * @param row {object} 当前项目数据
     * @param that {object} 当前node项目对象
     */
    reander_node_project_config: function (el, rows) {
      var row = $.extend(true, {}, rows);
      var that = this, edit_node_project = bt_tools.form({
        el: '#webedit-con',
        data: row.project_config,
        class: 'ptb15',
        form: (function () {
          var fromConfig = that.get_node_general_config({
            form: edit_node_project,
            path: row.path,
            ps: row.ps,
            callback: function (data, form, formNew) {
              data['is_power_on'] = data['is_power_on'] ? 1 : 0;
              var project_script_two = $('[name="project_script_two"]');
              if (project_script_two.length && project_script_two.val() === '') {
                bt.msg({ status: false, msg: '请输入自定义启动命令，不能为空！' });
                return false
              }
              if (form.port === '') {
                bt.msg({ status: false, msg: '项目端口不能为空' })
                return false
              }
              if (form.project_script === null) {
                bt.msg({ status: false, msg: '请选择项目目录，获取启动命令！' })
                return false
              }
              site.node.modify_node_project(data, function (res) {
                if (res.status) {
                  row['project_config'] = $.extend(row, data);
                  row['path'] = data.project_script;
                  row['ps'] = data.ps;
                }
                bt.msg({ status: res.status, msg: res.data })
                site.node.simulated_click(0)
              })
            }
          })
          setTimeout(function () {
            var is_existence = false, list = fromConfig[2].group.list;
            for (var i = 0; i < list.length; i++) {
              var item = list[i];
              if (item.value === rows.project_config.project_script) {
                is_existence = true;
                break;
              }
            }
            if (!is_existence && list.length > 1) {
              $('[data-name="project_script"] li:eq(' + (list.length - 1) + ')').click()
              $('[name="project_script_two"]').val(rows.project_config.project_script)
            }
            if (list.length === 1) {
              $('[data-name="project_script"] li:eq(0)').click()
              $('[name="project_script_two"]').val(rows.project_config.project_script)
            }
          }, 250)

          fromConfig[1].group.disabled = true;
          fromConfig[fromConfig.length - 3].hide = true;
          fromConfig[fromConfig.length - 3].group.disabled = true;
          return fromConfig
        })()
      })
      setTimeout(function () {
        $(el).append('<ul class="help-info-text c7">' +
          '<li>【启动选项】：默认读取package.json中的scripts列表，也可以选择[自定义启动命令]选项来手动输入启动命令</li>' +
          '<li>【自定义启动命令】：可以选择启动文件，或直接输入启动命令，支持的启动方式：npm/node/pm2/yarn</li>' +
          '<li>【项目端口】：错误的端口会导致访问502，若不知道端口，可先随意填写，启动项目后再改为正确端口</li>' +
          '<li>【运行用户】：为了安全考虑，默认使用www用户运行，root用户运行可能带来安全风险</li>' +
          '</ul>')
        if (!row.listen_ok) $(el).find('input[name="port"]').parent().after('<div class="block mt10" style="margin-left: 100px;color: red;line-height: 20px;">项目端口可能有误，检测到当前项目监听了以下端口[ ' + row.listen.join('、') + ' ]</div>');

      }, 100)
    },

    /**
     * @description 渲染Node项目服务状态
     * @param el {object} 当前element节点
     * @param row {object} 当前项目数据
     */
    reander_node_service_status: function (el, row) {
      var arry = [
        { title: '启动', event: this.start_node_project },
        { title: '停止', event: this.stop_node_project },
        { title: '重启', event: this.restart_node_project }
      ],
        that = this,
        html = $('<div class="soft-man-con bt-form"><p class="status"></p><div class="sfm-opt"></div></div>');
      function reander_service (status) {
        var status_info = status ? ['开启', '#20a53a', 'play'] : ['停止', 'red', 'pause'];
        return '当前状态：<span>' + status_info[0] + '</span><span style="color:' + status_info[1] + '; margin-left: 3px;" class="glyphicon glyphicon glyphicon-' + status_info[2] + '"></span>'
      }
      html.find('.status').html(reander_service(row.run))
      el.html(html)
      for (var i = 0; i < arry.length; i++) {
        var item = arry[i], btn = $('<button class="btn btn-default btn-sm"></button>');
        (function (btn, item, indexs) {
          !(row.run && indexs === 0) || btn.addClass('hide');
          !(!row.run && indexs === 1) || btn.addClass('hide');
          btn.on('click', function () {
            bt.confirm({
              title: item.title + '项目-[' + row.name + ']',
              msg: '您确定要' + item.title + '项目吗，' + (row.run ? '当前项目可能会受到影响，' : '') + '是否继续?'
            }, function (index) {
              layer.close(index)
              item.event.call(that, { project_name: row.name }, function (res) {
                row.run = (indexs === 0 ? true : (indexs === 1 ? false : row.run))
                html.find('.status').html(reander_service(row.run))
                $('.sfm-opt button').eq(0).addClass('hide');
                $('.sfm-opt button').eq(1).addClass('hide');
                $('.sfm-opt button').eq(row.run ? 1 : 0).removeClass('hide');
                bt.msg({ status: res.status, msg: res.data || res.error_msg })
              })
            })
          }).text(item.title)
        })(btn, item, i)
        el.find('.sfm-opt').append(btn)
      }
    },


    /**
     * @description 渲染Node项目域名管理
     * @param el {object} 当前element节点
     * @param row {object} 当前项目数据
     */
    reander_node_domain_manage: function (el, row) {
      var that = this,
        list = [{
          class: 'mb0',
          items: [
            { name: 'nodedomain', width: '340px', type: 'textarea', placeholder: '如果需要绑定外网，请输入需要映射的域名，该选项可为空<br>多个域名，请换行填写，每行一个域名，默认为80端口<br>泛解析添加方法 *.domain.com<br>如另加端口格式为 www.domain.com:88' },
            {
              name: 'btn_node_submit_domain',
              text: '添加',
              type: 'button',
              callback: function (sdata) {
                var arrs = sdata.nodedomain.split("\n");
                var domins = [];
                for (var i = 0; i < arrs.length; i++) domins.push(arrs[i]);
                that.add_node_project_domain({ project_name: row.name, domains: domins }, function (res) {
                  bt.msg({ status: res.status, msg: res.data || res.error_msg });
                  if (res.status) {
                    $('[name=nodedomain]').val('');
                    $('.placeholder').css('display', 'block')
                    project_domian.$refresh_table_list(true);
                  }
                })
              }
            }
          ]
        }]
      var _form_data = bt.render_form_line(list[0]), loadT = null, placeholder = null;
      el.html(_form_data.html + '<div id="project_domian_list"></div>');
      bt.render_clicks(_form_data.clicks);
      // domain样式
      $('.btn_node_submit_domain').addClass('pull-right').css("margin", "30px 35px 0 0");
      $('textarea[name=nodedomain]').css('height', '120px')
      placeholder = $(".placeholder");
      placeholder.click(function () {
        $(this).hide();
        $('.nodedomain').focus();
      }).css({ 'width': '340px', 'heigth': '120px', 'left': '0px', 'top': '0px', 'padding-top': '10px', 'padding-left': '15px' })
      $('.nodedomain').focus(function () {
        placeholder.hide();
        loadT = layer.tips(placeholder.html(), $(this), { tips: [1, '#20a53a'], time: 0, area: $(this).width() });
      }).blur(function () {
        if ($(this).val().length == 0) placeholder.show();
        layer.close(loadT);
      });
      var project_domian = bt_tools.table({
        el: '#project_domian_list',
        url: '/project/nodejs/project_get_domain',
        default: "暂无域名列表",
        param: { project_name: row.name },
        height: 375,
        beforeRequest: function (params) {
          if (params.hasOwnProperty('data') && typeof params.data === 'string') return params
          return { data: JSON.stringify(params) }
        },
        column: [{ type: 'checkbox', class: '', width: 20 }, {
          fid: 'name',
          title: '域名',
          type: 'text',
          template: function (row) {
            return '<a href="http://' + row.name + ':' + row.port + '" target="_blank" class="btlink">' + row.name + '</a>';
          }
        }, {
          fid: 'port',
          title: '端口',
          type: 'text'
        }, {
          title: '操作',
          type: 'group',
          width: '100px',
          align: 'right',
          group: [{
            title: '删除',
            event: function (rowc, index, ev, key, rthat) {
              that.remove_node_project_domain({ project_name: row.name, domain: (rowc.name + ':' + rowc.port) }, function (res) {
                bt.msg({ status: res.status, msg: res.data || res.error_msg })
                rthat.$refresh_table_list(true);
              })
            }
          }]
        }],
        tootls: [{ // 批量操作
          type: 'batch',
          positon: ['left', 'bottom'],
          placeholder: '请选择批量操作',
          buttonValue: '批量操作',
          disabledSelectValue: '请选择需要批量操作的站点!',
          selectList: [{
            title: "删除域名",
            load: true,
            url: '/project/nodejs/project_remove_domain',
            param: function (crow) {
              return { data: JSON.stringify({ project_name: row.name, domain: (crow.name + ':' + crow.port) }) }
            },
            callback: function (that) { // 手动执行,data参数包含所有选中的站点
              bt.show_confirm("批量删除域名", "<span style='color:red'>同时删除选中的域名，是否继续？</span>", function () {
                var param = {};
                that.start_batch(param, function (list) {
                  var html = ''
                  for (var i = 0; i < list.length; i++) {
                    var item = list[i];
                    html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + (item.request.status ? '成功' : '失败') + '</span></div></td></tr>';
                  }
                  project_domian.$batch_success_table({
                    title: '批量删除',
                    th: '删除域名',
                    html: html
                  });
                  project_domian.$refresh_table_list(true);
                });
              });
            }
          }]
        }]
      })
      setTimeout(function () {

        $(el).append('<ul class="help-info-text c7">' +
          '<li>如果您的是HTTP项目，且需要映射到外网，请至少绑定一个域名</li>' +
          '<li>建议所有域名都使用默认的80端口</li>' +
          '</ul>')

      }, 100)
    },

    /**
     * @description 渲染Node项目映射
     * @param el {object} 当前element节点
     * @param row {object} 当前项目数据
     */
    reander_node_project_map: function (el, row) {
      var that = this;
      el.html('<div class="pd15"><div class="ss-text mr50" style="display: block;height: 35px;">' +
        '   <em title="外网映射">外网映射</em>' +
        '       <div class="ssh-item">' +
        '           <input class="btswitch btswitch-ios" id="node_project_map" type="checkbox">' +
        '           <label class="btswitch-btn" for="node_project_map" name="node_project_map"></label>' +
        '       </div>' +
        '</div><ul class="help-info-text c7"><li>如果您的是HTTP项目，且需要外网通过80/443访问，请开启外网映射</li><li>开启外网映射前，请到【域名管理】中至少添加1个域名</li></ul></div>')
      $('#node_project_map').attr('checked', row['project_config']['bind_extranet'] ? true : false)
      $('[name=node_project_map]').click(function () {
        var _check = $('#node_project_map').prop('checked'), param = { project_name: row.name };
        if (!_check) param['domains'] = row['project_config']['domains']
        layer.confirm('是否确认' + (!_check ? '开启' : '关闭') + '外网映射！,是否继续', {
          title: '外网映射',
          icon: 0,
          closeBtn: 2,
          cancel: function () {
            $('#node_project_map').attr('checked', _check)
          }
        }, function () {
          that[_check ? 'unbind_node_project_map' : 'bind_node_project_map'](param, function (res) {
            if (!res.status) $('#node_project_map').attr('checked', _check)
            bt.msg({ status: res.status, msg: typeof res.data != "string" ? res.error_msg : res.data })
            row['project_config']['bind_extranet'] = _check ? 0 : 1
          })
        }, function () {
          $('#node_project_map').attr('checked', _check)
        })
      })
    },

    /**
     * @description 渲染Node项目模块
     * @param el {object} 当前element节点
     * @param row {object} 当前项目数据
     */
    reander_node_project_module: function (el, row) {
      var that = this;
      el.html('<div class="">' +
        '<div class=""><input class="bt-input-text mr5" name="mname" type="text" value="" style="width:240px" placeholder="模块名称" /><button class="btn btn-success btn-sm va0 install_node_module" >安装模块</button><button class="btn btn-success btn-sm va0 pull-right npm_install_node_config">一键安装项目模块</button></div>' +
        '<div id="node_module_list"></div>' +
        '</div>');
      var node_project_module_table = bt_tools.table({
        el: '#node_module_list',
        url: '/project/nodejs/get_project_modules',
        default: "未安装模块，点击一键安装项目模块, 数据为空时的默认提示",
        param: { project_name: row.name, project_cwd: row.path },
        height: '580px',
        load: '正在获取模块列表，请稍候...',
        beforeRequest: function (params) {
          if (params.hasOwnProperty('data') && typeof params.data === 'string') return params
          return { data: JSON.stringify(params) }
        },
        column: [{
          fid: 'name',
          title: '模块名称',
          type: 'text',
        }, {
          fid: 'version',
          title: '版本',
          type: 'text',
          width: '60px'
        }, {
          fid: 'license',
          title: '协议',
          type: 'text',
          template: function (row) {
            if (typeof row.license === "object") return '<span>' + row.license.type + '<span>';
            return '<span>' + row.license + '</span>'
          }
        }, {
          fid: 'description',
          title: '描述',
          width: 290,
          type: 'text',
          template: function (row) {
            return '<span>' + row.description + '<a href="javascript:;"></a></span>'
          }
        }, {
          title: '操作',
          type: 'group',
          width: '100px',
          align: 'right',
          group: [{
            title: '更新',
            event: function (rowc, index, ev, key, rthat) {
              bt.show_confirm("更新模块", "<span style='color:red'>更新[" + rowc.name + "]模块可能会影响项目运行，继续吗？</span>", function () {
                that.upgrade_node_module({ project_name: row.name, mod_name: rowc.name }, function (res) {
                  bt.msg({ status: res.status, msg: res.data || res.error_msg })
                  rthat.$refresh_table_list(true);
                });
              });
            }
          }, {
            title: '卸载',
            event: function (rowc, index, ev, key, rthat) {
              bt.show_confirm("卸载模块", "<span style='color:red'>卸载[" + rowc.name + "]模块可能会影响项目运行，继续吗？</span>", function () {
                that.uninstall_node_module({ project_name: row.name, mod_name: rowc.name }, function (res) {
                  bt.msg({ status: res.status, msg: res.data || res.error_msg })
                  rthat.$refresh_table_list(true);
                });
              });
            }
          }]
        }],
        success: function (config) {
          // 隐藏一键安装
          if (config.data.length > 0) $('.npm_install_node_config').addClass('hide');
        }
      })
      //安装模块
      $('.install_node_module').on('click', function () {
        var _mname = $('input[name=mname]').val();
        if (!_mname) return layer.msg('请输入模块名称及版本', { icon: 2 })
        that.npm_install_node_module({ project_name: row.name, mod_name: _mname }, function (res) {
          bt.msg({ status: res.status, msg: res.data || res.error_msg })
          node_project_module_table.$refresh_table_list(true);
        })
      })
      //一键安装项目模块
      $('.npm_install_node_config').on('click', function () {
        var _command = that.request_module_log_command({ shell: 'tail -f /www/server/panel/logs/npm-exec.log' })
        that.install_node_project_packages({ project_name: row.name }, function (res) {
          if (res.status) {
            node_project_module_table.$refresh_table_list(true);
          }
          layer.close(_command);
          bt.msg({ status: res.status, msg: res.data || res.error_msg })
        })
      })
    },

    /**
     * @description 渲染Node项目伪静态
     * @param el {object} 当前element节点
     * @param row {object} 当前项目数据
     */
    reander_node_project_rewrite: function (el, row) {
      el.empty();
      if (row.project_config.bind_extranet === 0) {
        $('.mask_module').removeClass('hide').find('.node_mask_module_text:eq(1)').hide().prev().show()
        return false;
      }
      site.edit.get_rewrite_list({ name: 'node_' + row.name }, function () {
        $('.webedit-box .line:first').remove();
        $('[name=btn_save_to]').remove();
        $('.webedit-box .help-info-text li:first').remove();
      })
    },
    /**
     * @description 渲染Node配置文件
     * @param el {object} 当前element节点
     * @param row {object} 当前项目数据
     */
    reander_node_file_config: function (el, row) {
      el.empty();
      if (row.project_config.bind_extranet === 0) {
        $('.mask_module').removeClass('hide').find('.node_mask_module_text:eq(1)').hide().prev().show()
        return false;
      }
      site.edit.set_config({ name: 'node_' + row.name })
    },
    /**
     * @description 渲染node项目使用情况
     * @param el {object} 当前element节点
     * @param row {object} 当前项目数据
     */
    reander_node_service_condition: function (el, row) {
      if (!row.run) {
        el.html('').next().removeClass('hide')
        if (el.next().find('.node_mask_module_text').length === 1) {
          el.next().find('.node_mask_module_text').hide().parent().append('<div class="node_mask_module_text">请先启动服务后重新尝试，<a href="javascript:;" class="btlink" onclick="site.node.simulated_click(7)">设置服务状态</a></div')
        } else {
          el.next().find('.node_mask_module_text:eq(1)').show().prev().hide()
        }
        return false
      }
      el.html('<div class="line" style="padding-top: 0;"><span class="tname" style="width: 30px;text-align:left;padding-right: 5px;">PID</span><div class="info-r"><select class="bt-input-text mr5" name="node_project_pid"></select></div></div><div class="node_project_pid_datail"></div>')
      var _option = '', tabelCon = ''
      for (var load in row.load_info) {
        if (row.load_info.hasOwnProperty(load)) {
          _option += '<option value="' + load + '">' + load + '</option>';
        }
      }
      var node_pid = $('[name=node_project_pid]');
      node_pid.html(_option);
      node_pid.change(function () {
        var _pid = $(this).val(), rdata = row['load_info'][_pid], fileBody = '', connectionsBody = '';
        for (var i = 0; i < rdata.open_files.length; i++) {
          var itemi = rdata.open_files[i];
          fileBody += '<tr>' +
            '<td>' + itemi['path'] + '</td>' +
            '<td>' + itemi['mode'] + '</td>' +
            '<td>' + itemi['position'] + '</td>' +
            '<td>' + itemi['flags'] + '</td>' +
            '<td>' + itemi['fd'] + '</td>' +
            '</tr>';
        }
        for (var k = 0; k < rdata.connections.length; k++) {
          var itemk = rdata.connections[k];
          connectionsBody += '<tr>' +
            '<td>' + itemk['client_addr'] + '</td>' +
            '<td>' + itemk['client_rport'] + '</td>' +
            '<td>' + itemk['family'] + '</td>' +
            '<td>' + itemk['fd'] + '</td>' +
            '<td>' + itemk['local_addr'] + '</td>' +
            '<td>' + itemk['local_port'] + '</td>' +
            '<td>' + itemk['status'] + '</td>' +
            '</tr>'
        }

        //     tabelCon = reand_table_config([
        //         [{"名称":rdata.name},{"PID":rdata.pid},{"状态":rdata.status},{"父进程":rdata.ppid}],
        //         [{"用户":rdata.user},{"Socket":rdata.connects},{"CPU":rdata.cpu_percent},{"线程":rdata.threads}],
        //         [{"内存":rdata.user},{"io读":rdata.connects},{"io写":rdata.cpu_percent},{"启动时间":rdata.threads}],
        //         [{"启动命令":rdata.user}],
        //     ])
        //
        // console.log(tabelCon)
        //
        //
        //     function reand_table_config(conifg){
        //         var html = '';
        //         for (var i = 0; i < conifg.length; i++) {
        //             var item = conifg[i];
        //             html += '<tr>';
        //             for (var j = 0; j < item; j++) {
        //                 var items = config[j],name = Object.keys(items)[0];
        //                 console.log(items,name)
        //                 html += '<td>'+  name +'</td><td>'+ items[name] +'</td>'
        //             }
        //             console.log(html)
        //             html += '</tr>'
        //         }
        //         return '<div class="divtable"><table class="table"><tbody>'+ html  +'</tbody></tbody></table></div>';
        //     }


        tabelCon = '<div class="divtable">' +
          '<table class="table">' +
          '<tbody>' +
          '<tr>' +
          '<th width="50">名称</th><td  width="100">' + rdata.name + '</td>' +
          '<th width="50">状态</th><td  width="90">' + rdata.status + '</td>' +
          '<th width="60">用户</th><td width="100">' + rdata.user + '</td>' +
          '<th width="80">启动时间</th><td width="150">' + getLocalTime(rdata.create_time) + '</td>' +
          '</tr>' +
          '<tr>' +
          '<th>PID</th><td  >' + rdata.pid + '</td>' +
          '<th>PPID</th><td >' + rdata.ppid + '</td>' +
          '<th>线程</th><td>' + rdata.threads + '</td>' +
          '<th>Socket</th><td>' + rdata.connects + '</td>' +
          '</tr>' +
          '<tr>' +
          '<th>CPU</th><td>' + rdata.cpu_percent + '%</td>' +
          '<th>内存</th><td>' + ToSize(rdata.memory_used) + '</td>' +
          '<th>io读</th><td>' + ToSize(rdata.io_read_bytes) + '</td>' +
          '<th>io写</th><td>' + ToSize(rdata.io_write_bytes) + '</td>' +

          '</tr>' +
          '<tr>' +

          '</tr>' +
          '<tr>' +
          '<th width="50">命令</th><td colspan="7" style="word-break: break-word;width: 570px">' + rdata.exe + '</td>' +
          '</tr>' +
          '</tbody>' +
          '</table>' +
          '</div>' +
          '<h3 class="tname">网络</h3>' +
          '<div class="divtable" >' +
          '<div style="height:160px;overflow:auto;border:#ddd 1px solid" id="nodeNetworkList">' +
          '<table class="table table-hover" style="border:none">' +
          '<thead>' +
          '<tr>' +
          '<th>客户端地址</th>' +
          '<th>客户端端口</th>' +
          '<th>协议</th>' +
          '<th>FD</th>' +
          '<th>本地地址</th>' +
          '<th>本地端口</th>' +
          '<th>状态</th>' +
          '</tr>' +
          '</thead>' +
          '<tbody>' + connectionsBody + '</tbody>' +
          '</table>' +
          '</div>' +
          '</div>' +
          '<h3 class="tname">打开的文件列表</h3>' +
          '<div class="divtable" >' +
          '<div style="height:160px;overflow:auto;border:#ddd 1px solid" id="nodeFileList">' +
          '<table class="table table-hover" style="border:none">' +
          '<thead>' +
          '<tr>' +
          '<th>文件</th>' +
          '<th>mode</th>' +
          '<th>position</th>' +
          '<th>flags</th>' +
          '<th>fd</th>' +
          '</tr>' +
          '</thead>' +
          '<tbody>' + fileBody + '</tbody>' +
          '</table>' +
          '</div>' +
          '</div>'
        $('.node_project_pid_datail').html(tabelCon);
        bt_tools.$fixed_table_thead('#nodeNetworkList')
        bt_tools.$fixed_table_thead('#nodeFileList')
      }).change().html(_option);
    },

    /**
     * @description 渲染Node项目日志
     * @param el {object} 当前element节点
     * @param row {object} 当前项目数据
     */
    reander_node_project_log: function (el, row) {
      el.html('<div class="node_project_log"></div>')
      bt_tools.send({
        url: '/project/nodejs/get_project_log',
        type: 'GET',
        data: { data: JSON.stringify({ project_name: row.name }) }
      }, function (res) {
        $('#webedit-con .node_project_log').html('<pre class="command_output_pre" style="height:640px;">' + (typeof res == "object" ? res.error_msg : res) + '</pre>')
        $('.command_output_pre').scrollTop($('.command_output_pre').prop('scrollHeight'))
      }, { load: '获取Node项目日志', verify: false })
    },

    reander_node_site_log: function (el, row) {
      el.empty()
      if (row.project_config.bind_extranet === 0) {
        $('.mask_module').removeClass('hide').find('.node_mask_module_text:eq(1)').hide().prev().show()
        return false;
      }
      site.edit.get_site_logs({ name: row.name })
    },

    /**
     * @description node项目SSL
     * @param el {object} 当前element节点
     * @param row {object} 当前项目数据
     */
    reander_node_project_ssl: function (el, row) {
      el.empty();
      if (row.project_config.bind_extranet === 0) {
        $('.mask_module').removeClass('hide').find('.node_mask_module_text:eq(1)').hide().prev().show()
        return false;
      }
      site.set_ssl({ name: row.name, ele: el, id: row.id });
      site.ssl.reload();
    },
    /**
     * @description 请求模块日志终端
     * @param config {object} 当前配置数据
     */
    request_module_log_command: function (config) {
      var r_command = layer.open({
        title: config.name || '正在安装模块，请稍候...',
        type: 1,
        closeBtn: 0,
        area: ['500px', '342px'],
        skin: config.class || 'module_commmand',
        shadeClose: false,
        content: '<div class="site_module_command"></div>',
        success: function () {
          bt_tools.command_line_output({ el: '.site_module_command', shell: config.shell, area: config.area || ['100%', '300px'] })
        }
      })
      return r_command;
    },

    /**
     * @description 请求封装
     * @param keyMethod 接口名和loading，键值对
     * @param param {object || function} 参数，可为空，为空则为callback参数
     * @param callback {function} 成功回调函数
     * @param callback1 {function} 错误调函数
     */
    http: function (keyMethod, param, callback, callback1) {
      var method = Object.keys(keyMethod),
        config = {
          url: '/project/nodejs/' + method[0],
          data: param && { data: JSON.stringify(param) } || {}
        },
        success = function (res) {
          callback && callback(res)
        }
      if (callback1) {
        bt_tools.send(config, success, callback1, { load: keyMethod[method[0]], verify: method[1] ? keyMethod[method[1]] : true })
      } else {
        bt_tools.send(config, success, { load: keyMethod[method[0]], verify: method[1] ? keyMethod[method[1]] : true })
      }
    }
  },
  node_porject_view: function () {
    $('#bt_node_table').empty();
    var node_table = bt_tools.table({
      el: '#bt_node_table',
      url: '/project/nodejs/get_project_list',
      minWidth: '1000px',
      autoHeight: true,
      default: "项目列表为空", //数据为空时的默认提示\
      load: '正在获取Node项目列表，请稍候...',
      beforeRequest: function (params) {
        if (params.hasOwnProperty('data') && typeof params.data === 'string') {
          var oldParams = JSON.parse(params['data'])
          delete params['data']
          return { data: JSON.stringify($.extend(oldParams, params)) }
        }
        return { data: JSON.stringify(params) }
      },
      column: [
        { type: 'checkbox', class: '', width: 20 },
        {
          fid: 'name',
          title: '项目名称',
          type: 'link',
          event: function (row, index, ev) {
            site.node.set_node_project_view(row);
          }
        },
        {
          fid: 'run',
          title: '服务状态',
          width: 80,
          config: {
            icon: true,
            list: [
              [true, '运行中', 'bt_success', 'glyphicon-play'],
              [false, '未启动', 'bt_danger', 'glyphicon-pause']
            ]
          },
          type: 'status',
          event: function (row, index, ev, key, that) {
            var status = row.run;
            bt.confirm({
              title: status ? '停止项目' : '启动项目',
              msg: status ? '停止项目后，当前项目服务将停止运行，继续吗？' : '启用Node项目[' + row.name + '],继续操作?'
            }, function (index) {
              layer.close(index)
              site.node[status ? 'stop_node_project' : 'start_node_project']({ project_name: row.name }, function (res) {
                bt.msg({ status: res.status, msg: res.data || res.error_msg })
                that.$refresh_table_list(true);
              })
            })
          }
        },
        {
          fid: 'pid',
          title: 'PID',
          width: 170,
          type: 'text',
          template: function (row) {
            if ($.isEmptyObject(row['load_info'])) return '<span>-</span>'
            var _id = []
            for (var i in row.load_info) {
              if (row.load_info.hasOwnProperty(i)) {
                _id.push(i)
              }
            }
            return '<span class="size_ellipsis" style="width:180px" title="' + _id.join(',') + '">' + _id.join(',') + '</span>'
          }
        },
        {
          title: 'CPU',
          width: 60,
          type: 'text',
          template: function (row) {
            if ($.isEmptyObject(row['load_info'])) return '<span>-</span>'
            var _cpu_total = 0;
            for (var i in row.load_info) {
              _cpu_total += row.load_info[i]['cpu_percent']
            }
            return '<span>' + _cpu_total.toFixed(2) + '%</span>'
          }
        },
        {
          title: '内存',
          width: 80,
          type: 'text',
          template: function (row) {
            if ($.isEmptyObject(row['load_info'])) return '<span>-</span>'
            var _cpu_total = 0;
            for (var i in row.load_info) {
              _cpu_total += row.load_info[i]['memory_used']
            }
            return '<span>' + bt.format_size(_cpu_total) + '</span>'
          }
        },
        {
          fid: 'path',
          title: '根目录',
          tips: '打开目录',
          type: 'link',
          event: function (row, index, ev) {
            openPath(row.path);
          }
        }, {
          fid: 'ps',
          title: '备注',
          type: 'input',
          blur: function (row, index, ev, key, that) {
            if (row.ps == ev.target.value) return false;
            bt.pub.set_data_ps({ id: row.id, table: 'sites', ps: ev.target.value }, function (res) {
              bt_tools.msg(res, { is_dynamic: true });
            });
          },
          keyup: function (row, index, ev) {
            if (ev.keyCode === 13) {
              $(this).blur();
            }
          }
        },
        {
          fid: 'node_version',
          width: 90,
          title: 'Node版本',
          type: 'text',
          template: function (row) {
            return '<span>' + row['project_config']['nodejs_version'] + '</span>'
          }
        }, {
          fid: 'ssl',
          title: 'SSL证书',
          tips: '部署证书',
          width: 100,
          type: 'text',
          template: function (row, index) {
            var _ssl = row.ssl,
              _info = '',
              _arry = [
                ['issuer', '证书品牌'],
                ['notAfter', '到期日期'],
                ['notBefore', '申请日期'],
                ['dns', '可用域名']
              ];
            try {
              if (typeof row.ssl.endtime != 'undefined') {
                if (row.ssl.endtime < 1) {
                  return '<a class="btlink bt_danger" href="javascript:;">已过期</a>';
                }
              }
            } catch (error) { }
            for (var i = 0; i < _arry.length; i++) {
              var item = _ssl[_arry[i][0]];
              _info += _arry[i][1] + ':' + item + (_arry.length - 1 != i ? '\n' : '');
            }
            return row.ssl === -1 ? '<a class="btlink bt_warning" href="javascript:;">未部署</a>' : '<a class="btlink ' + (row.ssl.endtime < 7 ? 'bt_danger' : '') + '" href="javascript:;" title="' + _info + '">剩余' + row.ssl.endtime + '天</a>';
          },
          event: function (row) {
            site.node.set_node_project_view(row);
            setTimeout(function () {
              $('.site-menu p:eq(5)').click();
            }, 500);
          }
        }, {
          title: '操作',
          type: 'group',
          width: 100,
          align: 'right',
          group: [{
            title: '设置',
            event: function (row, index, ev, key, that) {
              site.node.set_node_project_view(row);
            }
          }, {
            title: '删除',
            event: function (row, index, ev, key, that) {
              bt.prompt_confirm('删除项目', '您正在删除Node项目-[' + row.name + ']，继续吗？', function () {
                site.node.remove_node_project({ project_name: row.name }, function (res) {
                  bt.msg({ status: res.status, msg: res.data || res.error_msg })
                  node_table.$refresh_table_list(true);
                })
              })
            }
          }]
        }
      ],
      sortParam: function (data) {
        return { 'order': data.name + ' ' + data.sort };
      },
      // 渲染完成
      tootls: [{ // 按钮组
        type: 'group',
        positon: ['left', 'top'],
        list: [{
          title: '添加Node项目',
          active: true,
          event: function (ev) {
            site.node.add_node_form(function (res, index) {
              if (res.status) {
                layer.close(index)
                node_table.$refresh_table_list(true);
              }
              bt.msg({ status: res.status, msg: (!Array.isArray(res.data) ? res.data : false) || res.error_msg })
            })
          }
        }, {
          title: 'Node版本管理器',
          event: function (ev) {
            bt.soft.set_lib_config('nodejs', 'Node.js版本管理器')
          }
        }]
      }, { // 搜索内容
        type: 'search',
        positon: ['right', 'top'],
        placeholder: '请输入项目名称',
        searchParam: 'search', //搜索请求字段，默认为 search
        value: '', // 当前内容,默认为空
      }, { // 批量操作
        type: 'batch', //batch_btn
        positon: ['left', 'bottom'],
        placeholder: '请选择批量操作',
        buttonValue: '批量操作',
        disabledSelectValue: '请选择需要批量操作的站点!',
        selectList: [{
          title: "删除项目",
          url: '/project/nodejs/remove_project',
          param: function (row) {
            return {
              data: JSON.stringify({ project_name: row.name })
            }
          },
          refresh: true,
          callback: function (that) {
            bt.prompt_confirm('批量删除项目', '您正在删除选中的Node项目，继续吗？', function () {
              that.start_batch({}, function (list) {
                var html = '';
                for (var i = 0; i < list.length; i++) {
                  var item = list[i];
                  html += '<tr><td><span>' + item.name + '</span></td><td><div style="float:right;"><span style="color:' + (item.requests.status ? '#20a53a' : 'red') + '">' + (item.requests.status ? item.requests.data : item.requests.error_msg) + '</span></div></td></tr>';
                }
                node_table.$batch_success_table({ title: '批量删除项目', th: '项目名称', html: html });
                node_table.$refresh_table_list(true);
              });
            })
          }
        }],
      }, { //分页显示
        type: 'page',
        positon: ['right', 'bottom'], // 默认在右下角
        pageParam: 'p', //分页请求字段,默认为 : p
        page: 1, //当前分页 默认：1
        numberParam: 'limit',
        //分页数量请求字段默认为 : limit
        number: 20,
        //分页数量默认 : 20条
        numberList: [10, 20, 50, 100, 200], // 分页显示数量列表
        numberStatus: true, //　是否支持分页数量选择,默认禁用
        jump: true, //是否支持跳转分页,默认禁用
      }]
    });
  },
  php_table_view: function () {
    $('#bt_site_table').empty();
    var site_table = bt_tools.table({
      el: '#bt_site_table',
      url: '/data?action=getData',
      param: { table: 'sites' }, //参数
      minWidth: '1000px',
      autoHeight: true,
      default: "站点列表为空", //数据为空时的默认提示
      beforeRequest: function (param) {
        param.type = bt.get_cookie('site_type') || -1;
        return param;
      },
      column: [
        { type: 'checkbox', class: '', width: 20 },
        {
          fid: 'name',
          title: '网站名',
          sort: true,
          sortValue: 'asc',
          type: 'link',
          event: function (row, index, ev) {
            site.web_edit(row, true);
          }
        },
        {
          fid: 'status',
          title: '状态',
          sort: true,
          width: 80,
          config: {
            icon: true,
            list: [
              ['1', '运行中', 'bt_success', 'glyphicon-play'],
              ['0', '已停止', 'bt_danger', 'glyphicon-pause']
            ]
          },
          type: 'status',
          event: function (row, index, ev, key, that) {
            var time = row.edate || row.endtime;
            if (time != "0000-00-00") {
              if (new Date(time).getTime() < new Date().getTime()) {
                layer.msg('当前站点已过期，请重新设置站点到期时间', { icon: 2 });
                return false;
              }
            }
            bt.site[parseInt(row.status) ? 'stop' : 'start'](row.id, row.name, function (res) {
              if (res.status) that.$modify_row_data({ status: parseInt(row.status) ? '0' : '1' });
            });
          }
        },
        {
          fid: 'backup_count',
          title: '备份',
          width: 80,
          type: 'link',
          template: function (row, index) {
            var backup = lan.site.backup_no,
              _class = "bt_warning";
            if (row.backup_count > 0) backup = lan.site.backup_yes, _class = "bt_success";
            return '<a href="javascript:;" class="btlink  ' + _class + '">' + backup + (row.backup_count > 0 ? ('(' + row.backup_count + ')') : '') + '</a>';
          },
          event: function (row, index) {
            site.backup_site_view({ id: row.id, name: row.name }, site_table);
          }
        },
        {
          fid: 'path',
          title: '根目录',
          tips: '打开目录',
          type: 'link',
          event: function (row, index, ev) {
            openPath(row.path);
          }
        },
        {
          fid: 'edate',
          title: '到期时间',
          width: 85,
          class: 'set_site_edate',
          sort: true,
          type: 'link',
          template: function (row, index) {
            var _endtime = row.edate || row.endtime;
            if (_endtime === "0000-00-00") {
              return lan.site.web_end_time;
            } else {
              if (new Date(_endtime).getTime() < new Date().getTime()) {
                return '<a href="javscript:;" class="bt_danger">' + _endtime + '</a>';
              } else {
                return _endtime;
              }
            }
          },
          event: function (row) { }
        }, //模拟点击误删
        {
          fid: 'ps',
          title: '备注',
          type: 'input',
          blur: function (row, index, ev, key, that) {
            if (row.ps == ev.target.value) return false;
            bt.pub.set_data_ps({ id: row.id, table: 'sites', ps: ev.target.value }, function (res) {
              bt_tools.msg(res, { is_dynamic: true });
            });
          },
          keyup: function (row, index, ev) {
            if (ev.keyCode === 13) {
              $(this).blur();
            }
          }
        },
        {
          fid: 'php_version',
          title: 'PHP',
          tips: '选择php版本',
          width: 50,
          type: 'link',
          template: function (row, index) {
            if (row.php_version.indexOf('静态') > -1) return row.php_version;
            return row.php_version;
          },
          event: function (row, index) {
            site.web_edit(row);
            setTimeout(function () {
              $('.site-menu p:eq(9)').click();
            }, 500);
          }
        },
        {
          fid: 'ssl',
          title: 'SSL证书',
          tips: '部署证书',
          width: 100,
          type: 'text',
          template: function (row, index) {
            var _ssl = row.ssl,
              _info = '',
              _arry = [
                ['issuer', '证书品牌'],
                ['notAfter', '到期日期'],
                ['notBefore', '申请日期'],
                ['dns', '可用域名']
              ];
            try {
              if (typeof row.ssl.endtime != 'undefined') {
                if (row.ssl.endtime < 0) {
                  return '<a class="btlink bt_danger" href="javascript:;">已过期</a>';
                }
              }
            } catch (error) { }
            for (var i = 0; i < _arry.length; i++) {
              var item = _ssl[_arry[i][0]];
              _info += _arry[i][1] + ':' + item + (_arry.length - 1 != i ? '\n' : '');
            }
            return row.ssl === -1 ? '<a class="btlink bt_warning" href="javascript:;">未部署</a>' : '<a class="btlink ' + (row.ssl.endtime < 7 ? 'bt_danger' : '') + '" href="javascript:;" title="' + _info + '">剩余' + row.ssl.endtime + '天</a>';
          },
          event: function (row, index, ev, key, that) {
            site.web_edit(row);
            setTimeout(function () {
              $('.site-menu p:eq(8)').click();
            }, 500);
          }
        },
        {
          title: '操作',
          type: 'group',
          width: 150,
          align: 'right',
          group: [{
            title: '防火墙',
            event: function (row, index, ev, key, that) {
              site.site_waf(row.name);
            }
          }, {
            title: '设置',
            event: function (row, index, ev, key, that) {
              site.web_edit(row, true);
            }
          }, {
            title: '删除',
            event: function (row, index, ev, key, that) {
              site.del_site(row.id, row.name, function () {
                that.$refresh_table_list(true);
              });
            }
          }]
        }
      ],
      sortParam: function (data) {
        return { 'order': data.name + ' ' + data.sort };
      },
      // 表格渲染完成后
      success: function (that) {
        $('.event_edate_' + that.random).each(function () {
          var $this = $(this);
          laydate.render({
            elem: $this[0] //指定元素
            ,
            min: bt.get_date(1),
            max: '2099-12-31',
            vlue: bt.get_date(365),
            type: 'date',
            format: 'yyyy-MM-dd',
            trigger: 'click',
            btns: ['perpetual', 'confirm'],
            theme: '#20a53a',
            ready: function () {
              $this.click();
            },
            done: function (date) {
              var item = that.event_rows_model.rows;
              bt.site.set_endtime(item.id, date, function (res) {
                if (res.status) {
                  layer.msg(res.msg);
                  return false;
                }
                bt.msg(res);
              });
            }
          });
        });
      },
      // 渲染完成
      tootls: [{ // 按钮组
        type: 'group',
        positon: ['left', 'top'],
        list: [{
          title: '添加站点',
          active: true,
          event: function (ev) {
            site.add_site(function () {
              site_table.$refresh_table_list(true)
            });
            bt.set_cookie('site_type', '-1');
          }
        },
        { title: '修改默认页', event: function (ev) { site.set_default_page() } },
        { title: '默认站点', event: function (ev) { site.set_default_site() } },
        { title: 'PHP命令行版本', event: function (ev) { site.get_cli_version() } },
        { title: '网站设置', event: function (ev) { site.open_site_config() } }
        ]
      }, { // 搜索内容
        type: 'search',
        positon: ['right', 'top'],
        placeholder: '请输入域名或备注',
        searchParam: 'search', //搜索请求字段，默认为 search
        value: '', // 当前内容,默认为空
      }, { // 批量操作
        type: 'batch', //batch_btn
        positon: ['left', 'bottom'],
        placeholder: '请选择批量操作',
        buttonValue: '批量操作',
        disabledSelectValue: '请选择需要批量操作的站点!',
        selectList: [{
          group: [{ title: '开启站点', param: { status: 1 } }, { title: '停止站点', param: { status: 0 } }],
          url: '/site?action=set_site_status_multiple',
          confirmVerify: false, //是否提示验证方式
          paramName: 'sites_id', //列表参数名,可以为空
          paramId: 'id', // 需要传入批量的id
          theadName: '站点名称',
          refresh: true
        }, {
          title: "备份站点",
          url: '/site?action=ToBackup',
          paramId: 'id',
          load: true,
          theadName: '站点名称',
          refresh: true,
          callback: function (that) { // 手动执行,data参数包含所有选中的站点
            that.start_batch({}, function (list) {
              var html = '';
              for (var i = 0; i < list.length; i++) {
                var item = list[i];
                html += '<tr><td><span>' + item.name + '</span></td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span></div></td></tr>';
              }
              site_table.$batch_success_table({ title: '批量备份', th: '站点名称', html: html });
              site_table.$refresh_table_list(true);
            });
          }
        }, {
          title: "设置到期时间",
          url: '/site?action=set_site_etime_multiple',
          paramName: 'sites_id', //列表参数名,可以为空
          paramId: 'id', // 需要传入批量的id
          theadName: '站点名称',
          refresh: true,
          confirm: {
            title: '批量设置到期时间',
            content: '<div class="line"><span class="tname">到期时间</span><div class="info-r "><input name="edate" id="site_edate" class="bt-input-text mr5" placeholder="yyyy-MM-dd" type="text"></div></div>',
            success: function () {
              laydate.render({
                elem: '#site_edate',
                min: bt.format_data(new Date().getTime(), 'yyyy-MM-dd'),
                max: '2099-12-31',
                vlue: bt.get_date(365),
                type: 'date',
                format: 'yyyy-MM-dd',
                trigger: 'click',
                btns: ['perpetual', 'confirm'],
                theme: '#20a53a'
              });
            },
            yes: function (index, layers, request) {
              var site_edate = $('#site_edate'),
                site_edate_val = site_edate.val();
              if (site_edate_val != '') {
                if (new Date(site_edate_val).getTime() < new Date().getTime()) {
                  layer.tips('设置的到期时间不得小于当前时间', '#site_edate', { tips: ['1', 'red'] });
                  return false;
                }
                request({ 'edate': site_edate_val === '永久' ? '0000-00-00' : site_edate_val });
              } else {
                layer.tips('请输入到期时间', '#site_edate', { tips: ['1', 'red'] });
                $('#site_edate').css('border-color', 'red');
                $('#site_edate').click();
                setTimeout(function () {
                  $('#site_edate').removeAttr('style');
                }, 3000);
                return false;
              }
            }
          }
        }, {
          title: "设置PHP版本",
          url: '/site?action=set_site_php_version_multiple',
          paramName: 'sites_id', //列表参数名,可以为空
          paramId: 'id', // 需要传入批量的id
          theadName: '站点名称',
          refresh: true,
          confirm: {
            title: '批量设置PHP版本',
            area: '420px',
            content: '<div class="line"><span class="tname">PHP版本</span><div class="info-r"><select class="bt-input-text mr5 versions" name="versions" style="width:150px"></select></span></div><ul class="help-info-text c7" style="font-size:11px"><li>请根据您的程序需求选择版本</li><li>若非必要,请尽量不要使用PHP5.2,这会降低您的服务器安全性；</li><li>PHP7不支持mysql扩展，默认安装mysqli以及mysql-pdo。</li></ul></div>',
            success: function (res, list, that) {
              bt.site.get_all_phpversion(function (res) {
                var html = '';
                $.each(res, function (index, item) {
                  html += '<option value="' + item.version + '">' + item.name + '</option>';
                });
                $('[name="versions"]').html(html);
              });
            },
            yes: function (index, layers, request) {
              request({ version: $('[name="versions"]').val() });
            }
          }
        }, {
          title: "设置分类",
          url: '/site?action=set_site_type',
          paramName: 'site_ids', //列表参数名,可以为空
          paramId: 'id', // 需要传入批量的id
          refresh: true,
          beforeRequest: function (list) {
            var arry = [];
            $.each(list, function (index, item) {
              arry.push(item.id);
            });
            return JSON.stringify(arry);
          },
          confirm: {
            title: '批量设置分类',
            content: '<div class="line"><span class="tname">站点分类</span><div class="info-r"><select class="bt-input-text mr5 site_types" name="site_types" style="width:150px"></select></span></div></div>',
            success: function () {
              bt.site.get_type(function (res) {
                var html = '';
                $.each(res, function (index, item) {
                  html += '<option value="' + item.id + '">' + item.name + '</option>';
                });
                $('[name="site_types"]').html(html);
              });
            },
            yes: function (index, layers, request) {
              request({ id: $('[name="site_types"]').val() });
            }
          },
          tips: false,
          success: function (res, list, that) {
            var html = '';
            $.each(list, function (index, item) {
              html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (res.status ? '#20a53a' : 'red') + '">' + res.msg + '</span></div></td></tr>';
            });
            that.$batch_success_table({ title: '批量设置分类', th: '站点名称', html: html });
            that.$refresh_table_list(true);
          }
        }, {
          title: "删除站点",
          load: true,
          url: '/site?action=DeleteSite',
          param: function (row) {
            return {
              id: row.id,
              webname: row.name
            }
          },
          // paramName: 'sites_id', //列表参数名,可以为空
          // paramId: 'id', //需要传入批量的id
          // theadName: '站点名称',
          // refresh: true,
          callback: function (that) {
            // bt.show_confirm("批量删除站点", "是否同时删除选中站点同名的FTP、数据库、根目录", function() {
            //     var param = {};
            //     $('.bacth_options input[type=checkbox]').each(function() {
            //         var checked = $(this).is(":checked");
            //         if (checked) param[$(this).attr('name')] = checked ? 1 : 0;
            //     })
            //     if (callback) callback(param);
            // }, "<div class='options bacth_options'><span class='item'><label><input type='checkbox' name='ftp'><span>FTP</span></label></span><span class='item'><label><input type='checkbox' name='database'><span>" + lan.site.database + "</span></label></span><span class='item'><label><input type='checkbox' name='path'><span>" + lan.site.root_dir + "</span></label></span></div>");
            var ids = [];
            for (var i = 0; i < that.check_list.length; i++) {
              ids.push(that.check_list[i].id);
            }
            site.del_site(ids, function (param) {
              that.start_batch(param, function (list) {
                layer.closeAll()
                var html = '';
                for (var i = 0; i < list.length; i++) {
                  var item = list[i];
                  html += '<tr><td>' + item.name + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span></div></td></tr>';
                }
                site_table.$batch_success_table({
                  title: '批量删除',
                  th: '站点名称',
                  html: html
                });
                site_table.$refresh_table_list(true);
              });
            })
          }
        }],
      }, { //分页显示
        type: 'page',
        positon: ['right', 'bottom'], // 默认在右下角
        pageParam: 'p', //分页请求字段,默认为 : p
        page: 1, //当前分页 默认：1
        numberParam: 'limit',
        //分页数量请求字段默认为 : limit
        number: 20,
        //分页数量默认 : 20条
        numberList: [10, 20, 50, 100, 200], // 分页显示数量列表
        numberStatus: true, //　是否支持分页数量选择,默认禁用
        jump: true, //是否支持跳转分页,默认禁用
      }]
    });
    this.site_table = site_table;
    this.init_site_type();
    // return site_table;
  },
  init_site_type: function () {
    $('#php_cate_select').remove();
    $('.tootls_group.tootls_top .pull-left').append('<div id="php_cate_select" class="bt_select_updown site_class_type" style="vertical-align: bottom;"><div class="bt_select_value"><span class="bt_select_content">分类:</span><span class="glyphicon glyphicon-triangle-bottom ml5"></span></span></div><ul class="bt_select_list"></ul></div>');
    bt.site.get_type(function (res) {
      site.reader_site_type(res);
    });
  },
  reader_site_type: function (res) {
    var html = '',
      active = bt.get_cookie('site_type') || -1,
      select = $('#php_cate_select');
      config = this.site_table;
    if (select.find('.bt_select_list li').length > 1) return false
    res.unshift({ id: -1, name: "全部分类" });
    $.each(res, function (index, item) {
      html += '<li class="item ' + (parseInt(active) == item.id ? 'active' : '') + '" data-id="' + item.id + '" title="' + item.name + '">' + item.name + '</li>';
    });
    html += '<li role="separator" class="divider"></li><li class="item" data-id="type_sets">分类设置</li>';
    select.find('.bt_select_value').on('click', function (ev) {
      var $this = this;
      $(this).next().show();
      $(document).one('click', function () {
        $($this).next().hide();
      });
      ev.stopPropagation()
    });

    select.find('.bt_select_list').unbind('click').on('click', 'li', function () {
      var id = $(this).data('id');
      if (id === 'type_sets') {
        site.set_class_type();
      } else {
        bt.set_cookie('site_type', id);
        config.$refresh_table_list(true);
        $(this).addClass('active').siblings().removeClass('active');
        select.find('.bt_select_value .bt_select_content').text('分类: ' + $(this).text());
      }

    }).empty().html(html);
    select = $(select[0])
    if (!select.find('.bt_select_list li.active').length) {
      select.find('.bt_select_list li:eq(0)').addClass('active');
      select.find('.bt_select_value .bt_select_content').text('分类: 默认分类');
    } else {
      select.find('.bt_select_value .bt_select_content').text('分类: ' + select.find('.bt_select_list li.active').text());
    }
  },
  get_list: function (page, search, type) {
    if (page == undefined) page = 1;
    if (type == '-1' || type == undefined) {
      type = bt.get_cookie('site_type');
    }
    if (!search) search = $("#SearchValue").val();
    bt.site.get_list(page, search, type, function (rdata) {
      $('.dataTables_paginate').html(rdata.page);
      var data = rdata.data;
      var _tab = bt.render({
        table: '#webBody',
        columns: [
          { field: 'id', type: 'checkbox', width: 30 },
          {
            field: 'name',
            title: '网站名',
            templet: function (item) {
              return '<a class="btlink webtips" onclick="site.web_edit(this)" href="javascript:;">' + item.name + '</a>';
            },
            sort: function () { site.get_list(); }
          },
          {
            field: 'status',
            title: '状态',
            width: 80,
            templet: function (item) {
              var _status = '<a href="javascript:;" ';
              if (item.status == '1' || item.status == '正常' || item.status == '正在运行') {
                _status += ' onclick="bt.site.stop(' + item.id + ',\'' + item.name + '\') " >';
                _status += '<span style="color:#5CB85C">运行中 </span><span style="color:#5CB85C" class="glyphicon glyphicon-play"></span>';
              } else {
                _status += ' onclick="bt.site.start(' + item.id + ',\'' + item.name + '\')"';
                _status += '<span style="color:red">已停止  </span><span style="color:red" class="glyphicon glyphicon-pause"></span>';
              }
              return _status;
            },
            sort: function () { site.get_list(); }
          },
          {
            field: 'backup',
            title: '备份',
            width: 58,
            templet: function (item) {
              var backup = lan.site.backup_no;
              if (item.backup_count > 0) backup = lan.site.backup_yes;
              return '<a href="javascript:;" class="btlink" onclick="site.site_detail(' + item.id + ',\'' + item.name + '\')">' + backup + '</a>';
            }
          },
          {
            field: 'path',
            title: '根目录',
            templet: function (item) {
              var _path = bt.format_path(item.path);
              return '<a class="btlink" title="打开目录" href="javascript:openPath(\'' + _path + '\');">' + _path + '</a>';
            }
          },
          {
            field: 'edate',
            title: '到期时间',
            width: 86,
            templet: function (item) {
              var _endtime = '';
              if (item.edate) _endtime = item.edate;
              if (item.endtime) _endtime = item.endtime;
              _endtime = (_endtime == "0000-00-00") ? lan.site.web_end_time : _endtime
              return '<a class="btlink setTimes" id="site_endtime_' + item.id + '" >' + _endtime + '</a>';
            },
            sort: function () { site.get_list(); }
          },
          {
            field: 'ps',
            title: '备注',
            templet: function (item) {
              return "<span class='c9 input-edit'  onclick=\"bt.pub.set_data_by_key('sites','ps',this)\">" + item.ps + "</span>";
            }
          },
          {
            field: 'php_version',
            width: 60,
            title: 'PHP',
            templet: function (item) {
              return '<a class="phpversion_tips btlink">' + item.php_version + '</a>';
            }
          },
          {
            field: 'ssl',
            title: 'SSL证书',
            width: 80,
            templet: function (item) {
              var _ssl = '';
              if (item.ssl == -1) {
                _ssl = '<a class="ssl_tips btlink" style="color:orange;">未部署</a>';
              } else {
                var ssl_info = "证书品牌: " + item.ssl.issuer + "<br>到期日期: " + item.ssl.notAfter + "<br>申请日期: " + item.ssl.notBefore + "<br>可用域名: " + item.ssl.dns.join("/");
                if (item.ssl.endtime < 0) {
                  _ssl = '<a class="ssl_tips btlink" style="color:red;" data-tips="' + ssl_info + '">已过期</a>';

                } else if (item.ssl.endtime < 20) {
                  _ssl = '<a class="ssl_tips btlink" style="color:red;" data-tips="' + ssl_info + '">剩余' + (item.ssl.endtime + '天') + '</a>';
                } else {
                  _ssl = '<a class="ssl_tips btlink" style="color:green;" data-tips="' + ssl_info + '">剩余' + item.ssl.endtime + '天</a>';
                }
              }
              return _ssl;
            }
          },
          {
            field: 'opt',
            width: 150,
            title: '操作',
            align: 'right',
            templet: function (item) {
              var opt = '';
              var _check = ' onclick="site.site_waf(\'' + item.name + '\')"';

              if (bt.os == 'Linux') opt += '<a href="javascript:;" ' + _check + ' class="btlink ">防火墙</a> | ';
              opt += '<a href="javascript:;" class="btlink" onclick="site.web_edit(this)">设置 </a> | ';
              opt += '<a href="javascript:;" class="btlink" onclick="site.del_site(' + item.id + ',\'' + item.name + '\')" title="删除站点">删除</a>';
              return opt;
            }
          },
        ],
        data: data
      })
      var outTime = '';
      $('.ssl_tips').hover(function () {
        var that = this,
          tips = $(that).attr('data-tips');
        if (!tips) return false;
        outTime = setTimeout(function () {
          layer.tips(tips, $(that), {
            tips: [2, '#20a53a'], //还可配置颜色
            time: 0
          });
        }, 500);
      }, function () {
        outTime != '' ? clearTimeout(outTime) : '';
        layer.closeAll('tips');
      })
      $('.ssl_tips').click(function () {
        site.web_edit(this);
        var timeVal = setInterval(function () {
          var content = $('#webedit-con').html();
          if (content != '') {
            $('.site-menu p:eq(8)').click();
            clearInterval(timeVal);
          }
        }, 100);
      });
      $('.phpversion_tips').click(function () {
        site.web_edit(this);
        var timeVal = setInterval(function () {
          var content = $('#webedit-con').html();
          if (content != '') {
            $('.site-menu p:eq(9)').click();
            clearInterval(timeVal);
          }
        }, 100);
      });
      //设置到期时间
      $('a.setTimes').each(function () {
        var _this = $(this);
        var _tr = _this.parents('tr');
        var id = _this.attr('id');
        laydate.render({
          elem: '#' + id //指定元素
          ,
          min: bt.get_date(1),
          max: '2099-12-31',
          vlue: bt.get_date(365),
          type: 'date',
          format: 'yyyy-MM-dd',
          trigger: 'click',
          btns: ['perpetual', 'confirm'],
          theme: '#20a53a',
          done: function (dates) {
            var item = _tr.data('item');
            bt.site.set_endtime(item.id, dates, function () { })
          }
        });
      })
      //})
    });

  },
  site_waf: function (siteName) {
    try {
      site_waf_config(siteName);
    } catch (err) {
      site.no_firewall();
    }
  },
  html_encode: function (html) {
    var temp = document.createElement("div");
    //2.然后将要转换的字符串设置为这个元素的innerText(ie支持)或者textContent(火狐，google支持)
    (temp.textContent != undefined) ? (temp.textContent = html) : (temp.innerText = html);
    //3.最后返回这个元素的innerHTML，即得到经过HTML编码转换的字符串了
    var output = temp.innerHTML;
    temp = null;
    return output;
  },
  get_types: function (callback) {
    bt.site.get_type(function (rdata) {
      var optionList = '';
      var t_val = bt.get_cookie('site_type');
      for (var i = 0; i < rdata.length; i++) {
        optionList += '<button class="btn btn-' + (t_val == rdata[i].id ? 'success' : 'default') + ' btn-sm" value="' + rdata[i].id + '">' + rdata[i].name + '</button>'
      }
      if ($('.dataTables_paginate').next().hasClass('site_type')) $('.site_type').remove();
      $('.dataTables_paginate').after('<div class="site_type"><button class="btn btn-' + (t_val == '-1' ? 'success' : 'default') + ' btn-sm" value="-1">全部分类</button>' + optionList + '</div>');

      $('.site_type button').click(function () {
        var val = $(this).attr('value');
        bt.set_cookie('site_type', val);
        site.get_list(0, '', val);
        $(".site_type button").removeClass('btn-success').addClass('btn-default');
        $(this).addClass('btn-success');

      })
      if (callback) callback(rdata);
    });
  },
  no_firewall: function (obj) {
    var typename = bt.get_cookie('serverType');
    layer.confirm(typename + '防火墙暂未开通，<br>请到&quot;<a href="/soft" class="btlink">软件管理>付费插件>' + typename + '防火墙</a>&quot;<br>开通安装使用。', {
      title: typename + '防火墙未开通',
      icon: 7,
      closeBtn: 2,
      cancel: function () {
        if (obj) $(obj).prop('checked', false)
      }
    }, function () {
      window.location.href = '/soft';
    }, function () {
      if (obj) $(obj).prop('checked', false)
    })
  },
  /**
   * @description 备份站点视图
   * @param {object} config  配置参数
   * @param {function} callback  回调函数
   */
  backup_site_view: function (config, thatC, callback) {
    bt_tools.open({
      title: '备份站点&nbsp;-&nbsp;[&nbsp;' + config.name + '&nbsp;]',
      area: '790px',
      btn: false,
      skin: 'bt_backup_table',
      content: '<div id="bt_backup_table" class="pd20" style="padding-bottom:40px;"></div>',
      success: function () {
        var backup_table = bt_tools.table({
          el: '#bt_backup_table',
          url: '/data?action=getData',
          param: { table: 'backup', search: config.id, type: '0' },
          default: "[" + config.name + "] 站点备份列表为空", //数据为空时的默认提示
          column: [
            { type: 'checkbox', class: '', width: 20 },
            { fid: 'name', title: '文件名', width: 280, fixed: true },
            {
              fid: 'size',
              title: '文件大小',
              width: 80,
              type: 'text',
              template: function (row, index) {
                return bt.format_size(row.size);
              }
            },
            { fid: 'addtime', width: 150, title: '备份时间' },
            { fid: 'ps',
              title: '备注',
              type: 'input',
              blur: function (row, index, ev, key, that) {
                if (row.ps == ev.target.value) return false;
                bt.pub.set_data_ps({ id: row.id, table: 'backup', ps: ev.target.value }, function (res) {
                  bt_tools.msg(res, { is_dynamic: true });
                });
              },
              keyup: function (row, index, ev) {
                if (ev.keyCode === 13) {
                  $(this).blur();
                }
              }
            },
            {
              title: '操作',
              type: 'group',
              width: 120,
              align: 'right',
              group: [{
                title: '下载',
                template: function (row, index, ev, key, that) {
                  return '<a target="_blank" class="btlink" href="/download?filename=' + row.filename + '&amp;name=' + row.name + '">下载</a>';
                }
              }, {
                title: '删除',
                event: function (row, index, ev, key, that) {
                  that.del_site_backup({ name: row.name, id: row.id }, function (rdata) {
                    bt_tools.msg(rdata);
                    if (rdata.status) {
                      thatC.$modify_row_data({ backup_count: thatC.event_rows_model.rows.backup_count - 1 });
                      that.$refresh_table_list();
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
              bt.confirm({ title: '删除站点备份', msg: '删除站点备份[' + config.name + '],是否继续？' }, function () {
                bt_tools.send('site/DelBackup', { id: config.id }, function (rdata) {
                  if (callback) callback(rdata);
                }, true);
              });
            }
          },
          success: function () {
            if (callback) callback();
            $('.bt_backup_table').css('top', (($(window).height() - $('.bt_backup_table').height()) / 2) + 'px');
          },
          tootls: [{ // 按钮组
            type: 'group',
            positon: ['left', 'top'],
            list: [{
              title: '备份站点',
              active: true,
              event: function (ev, that) {
                bt.site.backup_data(config.id, function (rdata) {
                  bt_tools.msg(rdata);
                  if (rdata.status) {
                    thatC.$modify_row_data({ backup_count: thatC.event_rows_model.rows.backup_count + 1 });
                    that.$refresh_table_list();
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
                bt.confirm({ title: '批量删除站点备份', msg: '是否批量删除选中的站点备份，是否继续？', icon: 0 }, function (index) {
                  layer.close(index);
                  that.start_batch({}, function (list) {
                    var html = '';
                    for (var i = 0; i < list.length; i++) {
                      var item = list[i];
                      html += '<tr><td><span class="text-overflow" title="' + item.name + '">' + item.name + '</span></td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span></div></td></tr>';
                    }
                    backup_table.$batch_success_table({ title: '批量删除站点备份', th: '文件名', html: html });
                    backup_table.$refresh_table_list(true);
                    thatC.$modify_row_data({ backup_count: thatC.event_rows_model.rows.backup_count - list.length });
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
            number: 10,
            //分页数量默认 : 20条
          }]
        });
      }
    });
  },
  /**
   * @description 添加站点
   * @param {object} config  配置参数
   * @param {function} callback  回调函数
   */
  add_site: function (callback) {
    var add_web = bt_tools.form({
      data: {}, //用于存储初始值和编辑时的赋值内容
      class: '',
      form: [{
        label: '域名',
        group: {
          type: 'textarea', //当前表单的类型 支持所有常规表单元素、和复合型的组合表单元素
          name: 'webname', //当前表单的name
          style: { 'width': '440px', 'height': '100px', 'line-height': '22px' },
          tips: { //使用hover的方式显示提示
            text: '如需填写多个域名，请换行填写，每行一个域名，默认为80端口<br>泛解析添加方法 *.domain.com<br>如另加端口格式为 www.domain.com:88',
            style: { top: '15px', left: '15px' },
          },
          input: function (value, form, that, config, ev) { //键盘事件
            var array = value.webname.split("\n"),
              ress = array[0].split(":")[0],
              oneVal = bt.strim(ress.replace(new RegExp(/([-.])/g), '_')),
              defaultPath = $('#defaultPath').text(),
              is_oneVal = ress.length > 0;
            that.$set_find_value(is_oneVal ? {
              'ftp_username': oneVal,
              'ftp_password': bt.get_random(16),
              'datauser': is_oneVal ? (oneVal.substr(0, 16)) : '',
              'datapassword': bt.get_random(16),
              'ps': ress,
              'path': bt.rtrim(defaultPath, '/') + '/' + ress
            } : { 'ftp_username': '', 'ftp_password': '', 'datauser': '', 'datapassword': '', 'ps': '', 'path': bt.rtrim(defaultPath, '/') });
          }
        }
      }, {
        label: '备注',
        group: {
          type: 'text',
          name: 'ps',
          width: '400px',
          placeholder: '网站备注，可为空' //默认标准备注提示
        }
      }, {
        label: '根目录',
        group: {
          type: 'text',
          width: '400px',
          name: 'path',
          icon: {
            type: 'glyphicon-folder-open',
            event: function (ev) { }
          },
          value: bt.get_cookie('sites_path') ? bt.get_cookie('sites_path') : '/www/wwwroot',
          placeholder: '请选择文件目录'
        }
      }, {
        label: 'FTP',
        group: [{
          type: 'select',
          name: 'ftp',
          width: '120px',
          disabled: (function () {
            if (bt.config['pure-ftpd']) return !bt.config['pure-ftpd'].setup;
            return true;
          }()),
          list: [
            { title: '不创建', value: false },
            { title: '创建', value: true }
          ],
          change: function (value, form, that, config, ev) {
            if (value['ftp'] === 'true') {
              form['ftp_username'].parents('.line').removeClass('hide');
            } else {
              form['ftp_username'].parents('.line').addClass('hide');
            }
          }
        }, (function () {
          if (bt.config['pure-ftpd']['setup']) return {};
          return {
            type: 'link',
            title: '未安装FTP，点击安装',
            name: 'installed_ftp',
            event: function (ev) {
              bt.soft.install('pureftpd');
            }
          }
        }())]
      }, {
        label: 'FTP账号',
        hide: true,
        group: [
          { type: 'text', name: 'ftp_username', placeholder: '创建FTP账号', width: '175px', style: { 'margin-right': '15px' } },
          { label: '密码', type: 'text', placeholder: 'FTP密码', name: 'ftp_password', width: '175px' }
        ],
        help: {
          list: ['创建站点的同时，为站点创建一个对应FTP帐户，并且FTP目录指向站点所在目录。']
        }
      }, {
        label: '数据库',
        group: [{
          type: 'select',
          name: 'sql',
          width: '120px',
          disabled: (function () {
            if (bt.config['mysql']) return !bt.config['mysql'].setup;
            return true;
          }()),
          list: [
            { title: '不创建', value: false },
            { title: 'MySQL', value: 'MySQL' },
            { title: 'SQLServer', value: 'SQLServer', disabled: true, tips: 'Linux暂不支持SQLServer!' }
          ],
          change: function (value, form, that, config, ev) {
            if (value['sql'] === 'MySQL') {
              form['datauser'].parents('.line').removeClass('hide');
              form['codeing'].parents('.bt_select_updown').parent().removeClass('hide');
            } else {
              form['datauser'].parents('.line').addClass('hide');
              form['codeing'].parents('.bt_select_updown').parent().addClass('hide');
            }
          }
        }, (function () {
          if (bt.config.mysql.setup) return {};
          return {
            type: 'link',
            title: '未安装数据库，点击安装',
            name: 'installed_database',
            event: function () {
              bt.soft.install('mysql');
            }
          }
        }()), {
          type: 'select',
          name: 'codeing',
          hide: true,
          width: '120px',
          list: [
            { title: 'utf8', value: 'utf8' },
            { title: 'utf8mb4', value: 'utf8mb4' },
            { title: 'gbk', value: 'gbk' },
            { title: 'big5', value: 'big5' }
          ]
        }]
      }, {
        label: '数据库账号',
        hide: true,
        group: [
          { type: 'text', name: 'datauser', placeholder: '创建数据库账号', width: '175px', style: { 'margin-right': '15px' } },
          { label: '密码', type: 'text', placeholder: '数据库密码', name: 'datapassword', width: '175px' }
        ],
        help: {
          class: '',
          style: '',
          list: ['创建站点的同时，为站点创建一个对应的数据库帐户，方便不同站点使用不同数据库。']
        }
      }, {
        label: 'PHP版本',
        group: [{
          type: 'select',
          name: 'version',
          width: '120px',
          list: {
            url: '/site?action=GetPHPVersion',
            dataFilter: function (res) {
              var arry = [];
              for (var i = res.length - 1; i >= 0; i--) {
                var item = res[i];
                arry.push({ title: item.name, value: item.version });
              }
              return arry;
            }
          }
        }]
      }, {
        label: '网站分类',
        group: [{
          type: 'select',
          name: 'type_id',
          width: '120px',
          list: {
            url: '/site?action=get_site_types',
            dataFilter: function (res) {
              var arry = [];
              $.each(res, function (index, item) {
                arry.push({ title: item.name, value: item.id });
              });
              return arry;
            }
          }
        }]
      }]
    });
    var bath_web = bt_tools.form({
      class: 'plr10',
      form: [{
        line_style: { 'position': 'relative' },
        group: {
          type: 'textarea', //当前表单的类型 支持所有常规表单元素、和复合型的组合表单元素
          name: 'bath_code', //当前表单的name
          style: { 'width': '560px', 'height': '180px', 'line-height': '22px', 'font-size': '13px' },
          value: '域名|1|0|0|0\n域名|1|0|0|0\n域名|1|0|0|0',
        }
      }, {
        group: {
          type: 'help',
          style: { 'margin-top': '0' },
          class: 'none-list-style',
          list: [
            '批量格式：域名|根目录|FTP|数据库|PHP版本',
            '<span style="padding-top:5px;display:inline-block;">域名参数：多个域名用&nbsp;,&nbsp;分割</span>',
            '根目录参数：填写&nbsp;1&nbsp;为自动创建，或输入具体目录',
            'FTP参数：填写&nbsp;1&nbsp;为自动创建，填写&nbsp;0&nbsp;为不创建',
            '数据库参数：填写&nbsp;1&nbsp;为自动创建，填写&nbsp;0&nbsp;为不创建',
            'PHP版本参数：填写&nbsp;0&nbsp;为静态，或输入PHP具体版本号列如：56、71、74',
            '<span style="padding-bottom:5px;display:inline-block;">如需添加多个站点，请换行填写</span>',
            '案例：bt.cn,test.cn:8081|/www/wwwroot/bt.cn|1|1|56'
          ]
        }
      }]
    });
    var web_tab = bt_tools.tab({
      class: 'pd20',
      type: 0,
      theme: { nav: 'mlr20' },
      active: 1, //激活TAB下标
      list: [{
        title: '创建站点',
        name: 'createSite',
        content: add_web.$reader_content(),
        success: function () {
          add_web.$event_bind();
        }
      }, {
        title: '批量创建',
        name: 'batchCreation',
        content: bath_web.$reader_content(),
        success: function () {
          bath_web.$event_bind();
        }
      }]
    });
    bt_tools.open({
      title: '添加站点-支持批量建站',
      skin: 'custom_layer',
      btn: ['提交', '取消'],
      content: web_tab.$reader_content(),
      success: function (layers) {
        web_tab.$init();
        $(layers).find('.layui-layer-content').css('overflow', window.innerHeight > $(layers).height() ? 'inherit' : 'auto');
      },
      yes: function (indexs) {
        var formValue = !web_tab.active ? add_web.$get_form_value() : bath_web.$get_form_value();
        if (!web_tab.active) { // 创建站点
          var loading = bt.load();
          add_web.$get_form_element(true);
          if (formValue.webname === '') {
            add_web.form_element.webname.focus();
            bt_tools.msg('域名不能为空！', 2);
            return;
          }
          var webname = bt.replace_all(formValue.webname, 'http[s]?:\\/\\/', ''),
            web_list = webname.split('\n'),
            param = { webname: { domain: '', domainlist: [], count: 0 }, type: 'PHP', port: 80 },
            arry = ['ps', ['path', '网站目录'], 'type_id', 'version', 'ftp', 'sql', 'ftp_username', 'ftp_password', 'datauser', 'datapassword', 'codeing']
          for (var i = 0; i < web_list.length; i++) {
            var temps = web_list[i].replace(/\r\n/, '').split(':');
            if (i === 0) {
              param['webname']['domain'] = web_list[i];
              if (typeof temps[1] != 'undefined') param['port'] = temps[1]
            } else {
              param['webname']['domainlist'].push(web_list[i]);
            }
          }
          param['webname']['count'] = param['webname']['domainlist'].length;
          param['webname'] = JSON.stringify(param['webname']);
          $.each(arry, function (index, item) {
            if (formValue[item] == '' && Array.isArray(item)) {
              bt_tools.msg(item[1] + '不能为空?', 2);
              return false;
            }
            Array.isArray(item) ? item = item[0] : '';
            if (formValue['ftp'] === 'false' && (item === 'ftp_username' || item === 'ftp_password')) return true;
            if (formValue['sql'] === 'false' && (item === 'datauser' || item === 'datapassword')) return true;
            param[item] = formValue[item];
          });
          if (typeof param.ftp === 'undefined') {
            param.ftp = false;
            delete param.ftp_password;
            delete param.ftp_username;
          }
          if (typeof param.sql === 'undefined') {
            param.sql = false;
            delete param.datapassword;
            delete param.datauser;
          }
          bt.send('AddSite', 'site/AddSite', param, function (rdata) {
            loading.close();
            if (rdata.siteStatus) {
              layer.close(indexs);
              if (callback) callback(rdata);
              var html = '',
                ftpData = '',
                sqlData = ''
              if (rdata.ftpStatus) {
                var list = [];
                list.push({ title: lan.site.user, val: rdata.ftpUser });
                list.push({ title: lan.site.password, val: rdata.ftpPass });
                var item = {};
                item.title = lan.site.ftp;
                item.list = list;
                ftpData = bt.render_ps(item);
              }
              if (rdata.databaseStatus) {
                var list = [];
                list.push({ title: lan.site.database_name, val: rdata.databaseUser });
                list.push({ title: lan.site.user, val: rdata.databaseUser });
                list.push({ title: lan.site.password, val: rdata.databasePass });
                var item = {};
                item.title = lan.site.database_txt;
                item.list = list;
                sqlData = bt.render_ps(item);
              }
              if (ftpData == '' && sqlData == '') {
                bt.msg({ msg: lan.site.success_txt, icon: 1 })
              } else {
                bt.open({
                  type: 1,
                  area: '600px',
                  title: lan.site.success_txt,
                  closeBtn: 2,
                  shadeClose: false,
                  content: "<div class='success-msg'><div class='pic'><img src='/static/img/success-pic.png'></div><div class='suc-con'>" + ftpData + sqlData + "</div></div>"
                });

                if ($(".success-msg").height() < 150) {
                  $(".success-msg").find("img").css({ "width": "150px", "margin-top": "30px" });
                }
              }
            } else {
              bt.msg(rdata);
            }
          });
        } else { //批量创建
          var loading = bt.load();
          if (formValue.bath_code === '') {
            bt_tools.msg('请输入需要批量创建的站点信息!', 2);
            return false;
          } else {
            var arry = formValue.bath_code.split("\n"),
              config = '',
              _list = [];
            for (var i = 0; i < arry.length; i++) {
              var item = arry[i],
                params = item.split("|"),
                _arry = [];
              if (item === '') continue;
              for (var j = 0; j < params.length; j++) {
                var line = i + 1,
                  items = bt.strim(params[j]);
                _arry.push(items);
                switch (j) {
                  case 0: //参数一:域名
                    var domainList = items.split(",");
                    for (var z = 0; z < domainList.length; z++) {
                      var domain_info = domainList[z].trim(),
                        _domain = domain_info.split(":");
                      if (!bt.check_domain(_domain[0])) {
                        bt_tools.msg('第' + line + '行,域名格式错误【' + domain_info + '】', 2);
                        return false;
                      }
                      if (typeof _domain[1] !== "undefined") {
                        if (!bt.check_port(_domain[1])) {
                          bt_tools.msg('第' + line + '行,域名端口格式错误【' + _domain[1] + '】', 2);
                          return false;
                        }
                      }
                    }
                    break;
                  case 1: //参数二:站点目录
                    if (items !== '1') {
                      if (items.indexOf('/') < -1) {
                        bt_tools.msg('第' + line + '行,站点目录格式错误【' + items + '】', 2);
                        return false;
                      }
                    }
                    break;
                }
              }
              _list.push(_arry.join('|').replace(/\r|\n/, ''));
            }
          }
          bt.send('create_type', 'site/create_website_multiple', { create_type: 'txt', websites_content: JSON.stringify(_list) }, function (rdata) {
            loading.close();
            if (rdata.status) {
              var _html = '';
              layer.close(indexs);
              if (callback) callback(rdata);
              $.each(rdata.error, function (key, item) {
                _html += '<tr><td>' + key + '</td><td>--</td><td>--</td><td style="text-align: right;"><span style="color:red">' + item + '</td></td></tr>';
              });
              $.each(rdata.success, function (key, item) {
                _html += '<tr><td>' + key + '</td><td>' + (item.ftp_status ? '<span style="color:#20a53a">成功</span>' : '<span>未创建</span>') + '</td><td>' + (item.db_status ? '<span style="color:#20a53a">成功</span>' : '<span>未创建</span>') + '</td><td  style="text-align: right;"><span style="color:#20a53a">创建成功</span></td></tr>';
              });
              bt.open({
                type: 1,
                title: '站点批量添加',
                area: ['500px', '450px'],
                shadeClose: false,
                closeBtn: 2,
                content: '<div class="fiexd_thead divtable" style="margin: 15px 30px 15px 30px;overflow: auto;height: 360px;"><table class="table table-hover"><thead><tr><th>站点名称</th><th>FTP</th><th >数据库</th><th style="text-align:right;width:150px;">操作结果</th></tr></thead><tbody>' + _html + '</tbody></table></div>',
                success: function () {
                  $('.fiexd_thead').scroll(function () {
                    var scrollTop = this.scrollTop;
                    this.querySelector('thead').style.transform = 'translateY(' + scrollTop + 'px)';
                  });
                }
              });
            } else {
              bt.msg(rdata);
            }
          });
        }
      }
    });
  },
  set_default_page: function () {
    bt.open({
      type: 1,
      area: '460px',
      title: lan.site.change_defalut_page,
      closeBtn: 2,
      shift: 0,
      content: '<div class="change-default pd20"><button  class="btn btn-default btn-sm ">' + lan.site.default_doc + '</button><button  class="btn btn-default btn-sm">' + lan.site.err_404 + '</button>	<button  class="btn btn-default btn-sm ">' + lan.site.empty_page + '</button><button  class="btn btn-default btn-sm ">' + lan.site.default_page_stop + '</button></div>',
      success: function () {
        $('.change-default button').click(function () {
          bt.site.get_default_path($(this).index(), function (path) {
            bt.pub.on_edit_file(0, path);
          })
        })
      }
    });
  },
  set_default_site: function () {
    bt.site.get_default_site(function (rdata) {
      var arrs = [];
      arrs.push({ title: "未设置默认站点", value: '0' })
      for (var i = 0; i < rdata.sites.length; i++) arrs.push({ title: rdata.sites[i].name, value: rdata.sites[i].name })
      var form = {
        title: lan.site.default_site_yes,
        area: '530px',
        list: [{ title: lan.site.default_site, name: 'defaultSite', width: '300px', value: rdata.defaultSite, type: 'select', items: arrs }],
        btns: [
          bt.form.btn.close(),
          bt.form.btn.submit('提交', function (rdata, load) {
            bt.site.set_default_site(rdata.defaultSite, function (rdata) {
              load.close();
              bt.msg(rdata);
            })
          })
        ]
      }
      bt.render_form(form);
      $('.line').after($(bt.render_help([lan.site.default_site_help_1, lan.site.default_site_help_2])).addClass('plr20'));
    })
  },
  //PHP-CLI
  get_cli_version: function () {
    $.post('/config?action=get_cli_php_version', {}, function (rdata) {
      if (rdata.status === false) {
        layer.msg(rdata.msg, { icon: 2 });
        return;
      }
      var _options = '';
      for (var i = rdata.versions.length - 1; i >= 0; i--) {
        var ed = '';
        if (rdata.select.version == rdata.versions[i].version) ed = 'selected'
        _options += '<option value="' + rdata.versions[i].version + '" ' + ed + '>' + rdata.versions[i].name + '</option>';
      }
      var body = '<div class="bt-form pd20 pb70">\
                <div class="line">\
                    <span class="tname">PHP-CLI版本</span>\
                    <div class="info-r ">\
                        <select class="bt-input-text mr5" name="php_version" style="width:300px">' + _options + '</select>\
                    </div>\
                </div >\
                <ul class="help-info-text c7 plr20">\
                    <li>此处可设置命令行运行php时使用的PHP版本</li>\
                    <li>安装新的PHP版本后此处需要重新设置</li>\
                </ul>\
                <div class="bt-form-submit-btn"><button type="button" class="btn btn-sm btn-danger" onclick="layer.closeAll()">关闭</button><button type="button" class="btn btn-sm btn-success" onclick="site.set_cli_version()">提交</button></div></div>';

      layer.open({
        type: 1,
        title: "设置PHP-CLI(命令行)版本",
        area: '560px',
        closeBtn: 2,
        shadeClose: false,
        content: body
      });
    });
  },
  // 网站设置
  open_site_config: function () {
    bt.open({
      type: 1,
      title: '网站设置',
      area: '340px',
      closeBtn: 2,
      shift: 0,
      content: '\
        <div class="bt-form pd20">\
          <div class="line">\
            <span class="tname" style="width: 120px;">HTTPS防窜站</span>\
            <div class="info-r" style="height: 32px; margin-left: 120px; padding-top: 6px;">\
              <input class="btswitch btswitch-ios" id="https_mode" type="checkbox" name="https_mode">\
              <label class="btswitch-btn" for="https_mode" style="margin-bottom: 0;"></label>\
            </div>\
          </div>\
          <ul class="help-info-text c7 plr20">\
            <li>开启后可以解决HTTPS防窜站的问题</li>\
          </ul>\
        </div>\
      ',
      success: function ($layer) {
        this.init();
        $('#https_mode').change(function () {
          var loadT = bt.load('正在设置HTTPS防窜站，请稍候...');
          bt.send('set_https_mode', 'site/set_https_mode', {}, function (res) {
            loadT.close();
            bt.msg(res);
            if (!res.status) {
              var checked = $('#https_mode').is(':checked');
              $('#https_mode').prop('checked', !checked);
            }
          });
        });
      },
      init: function () {
        var loadT = bt.load('正在获取网站设置，请稍候...');
        bt.send('get_https_mode', 'site/get_https_mode', {}, function (res) {
          loadT.close();
          if (typeof res == 'boolean') {
            $('#https_mode').prop('checked', res);
          } else {
            bt.msg(res);
          }
        });
      }
    });
  },
  set_cli_version: function () {
    var php_version = $("select[name='php_version']").val();
    var loading = bt.load();
    $.post('/config?action=set_cli_php_version', { php_version: php_version }, function (rdata) {
      loading.close();
      if (rdata.status) {
        layer.closeAll();
      }
      layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
    });
  },
  del_site: function (wid, wname, callback) {
    var num1 = bt.get_random_num(1, 9), num2 = bt.get_random_num(1, 9), title = '';
    title = typeof wname === "function" ? '批量删除站点' : '删除站点 [ ' + wname + ' ]';
    layer.open({
      type: 1,
      title: title,
      icon: 0,
      skin: 'delete_site_layer',
      area: "440px",
      closeBtn: 2,
      shadeClose: true,
      content: "<div class=\'bt-form webDelete pd30\' id=\'site_delete_form\'>" +
        '<i class="layui-layer-ico layui-layer-ico0"></i>' +
        "<div class=\'f13 check_title\'>是否要删除关联的FTP、数据库、站点目录！</div>" +
        "<div class=\"check_type_group\">" +
        "<label><input type=\"checkbox\" name=\"ftp\"><span>FTP</span></label>" +
        "<label><input type=\"checkbox\" name=\"database\"><span>数据库</span>" + (!recycle_bin_db_open ? '<span class="glyphicon glyphicon-info-sign" style="color: red"></span>' : '') + "</label>" +
        "<label><input type=\"checkbox\"  name=\"path\"><span>站点目录</span>" + (!recycle_bin_open ? '<span class="glyphicon glyphicon-info-sign" style="color: red"></span>' : '') + "</label>" +
        "</div>" +
        "<div class=\'vcode\'>" + lan.bt.cal_msg + "<span class=\'text\'>" + num1 + " + " + num2 + "</span>=<input type=\'number\' id=\'vcodeResult\' value=\'\'></div>" +
        "</div>",
      btn: [lan.public.ok, lan.public.cancel],
      success: function (layers, indexs) {
        $(layers).find('.check_type_group label').hover(function () {
          var name = $(this).find('input').attr('name');
          if (name === 'data' && !recycle_bin_db_open) {
            layer.tips('风险操作：当前数据库回收站未开启，删除数据库将永久消失！', this, { tips: [1, 'red'], time: 0 })
          } else if (name === 'path' && !recycle_bin_open) {
            layer.tips('风险操作：当前文件回收站未开启，删除站点目录将永久消失！', this, { tips: [1, 'red'], time: 0 })
          }
        }, function () {
          layer.closeAll('tips');
        })
      },
      yes: function (indexs) {
        var vcodeResult = $('#vcodeResult'), data = { id: wid, webname: wname };
        $('#site_delete_form input[type=checkbox]').each(function (index, item) {
          if ($(item).is(':checked')) data[$(item).attr('name')] = 1
        })
        if (vcodeResult.val() === '') {
          layer.tips('计算结果不能为空', vcodeResult, { tips: [1, 'red'], time: 3000 })
          vcodeResult.focus()
          return false;
        } else if (parseInt(vcodeResult.val()) !== (num1 + num2)) {
          layer.tips('计算结果不正确', vcodeResult, { tips: [1, 'red'], time: 3000 })
          vcodeResult.focus()
          return false;
        }
        var is_database = data.hasOwnProperty('database'), is_path = data.hasOwnProperty('path'), is_ftp = data.hasOwnProperty('ftp');
        if ((!is_database && !is_path) && (!is_ftp || is_ftp)) {
          if (typeof wname === "function") {
            wname(data)
            return false;
          }
          bt.site.del_site(data, function (rdata) {
            layer.close(indexs);
            if (callback) callback(rdata);
            bt.msg(rdata);
          })
          return false
        }
        if (typeof wname === "function") {
          delete data.id;
          delete data.webname;
        }
        layer.close(indexs)
        var ids = JSON.stringify(wid instanceof Array ? wid : [wid]), countDown = typeof wname === 'string' ? 4 : 9;
        title = typeof wname === "function" ? '二次验证信息，批量删除站点' : '二次验证信息，删除站点 [ ' + wname + ' ]';
        var loadT = bt.load('正在检测站点数据信息，请稍候...')
        bt.send('check_del_data', 'site/check_del_data', { ids: ids }, function (res) {
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
              '<div class="check_layer_error ' + (data.database && recycle_bin_db_open ? 'hide' : '') + '"><span class="glyphicon glyphicon-info-sign"></span>风险事项：当前未开启数据库回收站功能，删除数据库后，数据库将永久消失！</div>' +
              '<div class="check_layer_error ' + (data.path && recycle_bin_open ? 'hide' : '') + '"><span class="glyphicon glyphicon-info-sign"></span>风险事项：当前未开启文件回收站功能，删除站点目录后，站点目录将永久消失！</div>' +
              '<div class="check_layer_message">请仔细阅读以上要删除信息，防止网站数据被误删，确认删除还有 <span style="color:red;font-weight: bold;">' + countDown + '</span> 秒可以操作。</div>' +
              '</div>',
            // recycle_bin_db_open &&
            // recycle_bin_open &&
            btn: ['确认删除(' + countDown + '秒后继续操作)', '取消删除'],
            success: function (layers) {
              var html = '', rdata = res.data;
              for (var i = 0; i < rdata.length; i++) {
                var item = rdata[i], newTime = parseInt(new Date().getTime() / 1000),
                  t_icon = '<span class="glyphicon glyphicon-info-sign" style="color: red;width:15px;height: 15px;;vertical-align: middle;"></span>';

                site_html = (function (item) {
                  if (!is_path) return ''
                  var is_time_rule = (newTime - item.st_time) > (86400 * 30) && (item.total > 1024 * 10),
                    is_path_rule = res.file_size <= item.total,
                    dir_time = bt.format_data(item.st_time, 'yyyy-MM-dd'),
                    dir_size = bt.format_size(item.total);

                  var f_html = '<i ' + (is_path_rule ? 'class="warning"' : '') + ' style = "vertical-align: middle;" > ' + (item.limit ? '大于50MB' : dir_size) + '</i> ' + (is_path_rule ? t_icon : '');
                  var f_title = (is_path_rule ? '注意：此目录较大，可能为重要数据，请谨慎操作.\n' : '') + '目录：' + item.path + '(' + (item.limit ? '大于' : '') + dir_size + ')';

                  return '<div class="check_layer_site">' +
                    '<span title="站点：' + item.name + '">站点名：' + item.name + '</span>' +
                    '<span title="' + f_title + '" >目录：<span style="vertical-align: middle;max-width: 160px;width: auto;">' + item.path + '</span> (' + f_html + ')</span>' +
                    '<span title="' + (is_time_rule ? '注意：此站点创建时间较早，可能为重要数据，请谨慎操作.\n' : '') + '时间：' + dir_time + '">创建时间：<i ' + (is_time_rule ? 'class="warning"' : '') + '>' + dir_time + '</i></span>' +
                    '</div>'
                }(item)),
                  database_html = (function (item) {
                    if (!is_database || !item.database) return '';
                    var is_time_rule = (newTime - item.st_time) > (86400 * 30) && (item.total > 1024 * 10),
                      is_database_rule = res.db_size <= item.database.total,
                      database_time = bt.format_data(item.database.st_time, 'yyyy-MM-dd'),
                      database_size = bt.format_size(item.database.total);

                    var f_size = '<i ' + (is_database_rule ? 'class="warning"' : '') + ' style = "vertical-align: middle;" > ' + database_size + '</i> ' + (is_database_rule ? t_icon : '');
                    var t_size = '注意：此数据库较大，可能为重要数据，请谨慎操作.\n数据库：' + database_size;

                    return '<div class="check_layer_database">' +
                      '<span title="数据库：' + item.database.name + '">数据库：' + item.database.name + '</span>' +
                      '<span title="' + t_size + '">大小：' + f_size + '</span>' +
                      '<span title="' + (is_time_rule && item.database.total != 0 ? '重要：此数据库创建时间较早，可能为重要数据，请谨慎操作.' : '') + '时间：' + database_time + '">创建时间：<i ' + (is_time_rule && item.database.total != 0 ? 'class="warning"' : '') + '>' + database_time + '</i></span>' +
                      '</div>'
                  }(item))
                if ((site_html + database_html) !== '') html += '<div class="check_layer_item">' + site_html + database_html + '</div>';
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
                $(layers).find('.check_layer_message').html('<span style="color:red">注意：请仔细阅读以上要删除信息，防止网站数据被误删</span>')
                $(layers).removeClass('active');
                clearInterval(interVal)
              }, countDown * 1000)
            },
            yes: function (indes, layers) {
              if ($(layers).hasClass('active')) {
                layer.tips('请确认信息，稍候在尝试，还剩' + countDown + '秒', $(layers).find('.layui-layer-btn0'), { tips: [1, 'red'], time: 3000 })
                return;
              }
              if (typeof wname === "function") {
                wname(data)
              } else {
                bt.site.del_site(data, function (rdata) {
                  layer.closeAll()
                  if (rdata.status) site.get_list();
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
  batch_site: function (type, obj, result) {
    if (obj == undefined) {
      obj = {};
      var arr = [];
      result = { count: 0, error_list: [] };
      $('input[type="checkbox"].check:checked').each(function () {
        var _val = $(this).val();
        if (!isNaN(_val)) arr.push($(this).parents('tr').data('item'));
      })
      if (type == 'site_type') {
        bt.site.get_type(function (tdata) {
          var types = [];
          for (var i = 0; i < tdata.length; i++) types.push({ title: tdata[i].name, value: tdata[i].id })
          var form = {
            title: '设置站点分类',
            area: '530px',
            list: [{ title: lan.site.default_site, name: 'type_id', width: '300px', type: 'select', items: types }],
            btns: [
              bt.form.btn.close(),
              bt.form.btn.submit('提交', function (rdata, load) {
                var ids = []
                for (var x = 0; x < arr.length; x++) ids.push(arr[x].id);
                bt.site.set_site_type({ id: rdata.type_id, site_array: JSON.stringify(ids) }, function (rrdata) {
                  if (rrdata.status) {
                    load.close();
                    site.get_list();
                  }
                  bt.msg(rrdata);
                })
              })
            ]
          }
          bt.render_form(form);
        })
        return;
      }
      var thtml = "<div class='options'><label style=\"width:100%;\"><input type='checkbox' id='delpath' name='path'><span>" + lan.site.all_del_info + "</span></label></div>";
      bt.show_confirm(lan.site.all_del_site, "<a style='color:red;'>" + lan.get('del_all_site', [arr.length]) + "</a>", function () {
        if ($("#delpath").is(":checked")) obj.path = '1';
        obj.data = arr;
        bt.closeAll();
        site.batch_site(type, obj, result);
      }, thtml);

      return;
    }
    var item = obj.data[0];
    switch (type) {
      case 'del':
        if (obj.data.length < 1) {
          site.get_list();
          bt.msg({ msg: lan.get('del_all_site_ok', [result.count]), icon: 1, time: 5000 });
          return;
        }
        var data = { id: item.id, webname: item.name, path: obj.path }
        bt.site.del_site(data, function (rdata) {
          if (rdata.status) {
            result.count += 1;
          } else {
            result.error_list.push({ name: item.item, err_msg: rdata.msg });
          }
          obj.data.splice(0, 1)
          site.batch_site(type, obj, result);
        })
        break;

    }
  },
  set_class_type: function () {
    var _form_data = bt.render_form_line({
      title: '',
      items: [
        { placeholder: '请填写分类名称', name: 'type_name', width: '50%', type: 'text' },
        {
          name: 'btn_submit',
          text: '添加',
          type: 'button',
          callback: function (sdata) {
            bt.site.add_type(sdata.type_name, function (ldata) {
              if (ldata.status) {
                $('[name="type_name"]').val('');
                site.get_class_type();
                site.init_site_type();
              }
              bt.msg(ldata);
            })
          }
        }
      ]
    });
    bt.open({
      type: 1,
      area: '350px',
      title: '网站分类管理',
      closeBtn: 2,
      shift: 5,
      shadeClose: true,
      content: "<div class='bt-form edit_site_type'><div class='divtable mtb15' style='overflow:auto'>" + _form_data.html + "<table id='type_table' class='table table-hover' width='100%'></table></div></div>",
      success: function () {
        bt.render_clicks(_form_data.clicks);
        site.get_class_type(function (res) {
          $('#type_table').on('click', '.del_type', function () {
            var _this = $(this);
            var item = _this.parents('tr').data('item');
            if (item.id == 0) {
              bt.msg({ icon: 2, msg: '默认分类不可删除/不可编辑!' });
              return;
            }
            bt.confirm({ msg: "是否确定删除分类？", title: '删除分类【' + item.name + '】' }, function () {
              bt.site.del_type(item.id, function (ret) {
                if (ret.status) {
                  site.get_class_type();
                  site.init_site_type();
                  var active = bt.get_cookie('site_type') || -1;
                  if (active == item.id) {
                    bt.set_cookie('site_type', -1);
                  }
                }
                bt.msg(ret);
              })
            })
          });
          $('#type_table').on('click', '.edit_type', function () {
            var item = $(this).parents('tr').data('item');
            if (item.id == 0) {
              bt.msg({ icon: 2, msg: '默认分类不可删除/不可编辑!' });
              return;
            }
            bt.render_form({
              title: '修改分类管理【' + item.name + '】',
              area: '350px',
              list: [{ title: '分类名称', width: '150px', name: 'name', value: item.name }],
              btns: [
                { title: '关闭', name: 'close' },
                {
                  title: '提交',
                  name: 'submit',
                  css: 'btn-success',
                  callback: function (rdata, load, callback) {
                    bt.site.edit_type({ id: item.id, name: rdata.name }, function (edata) {
                      if (edata.status) {
                        load.close();
                        site.get_class_type();
                        site.init_site_type();
                      }
                      bt.msg(edata);
                    })
                  }
                }
              ]
            });
          });
        });
      }
    });
  },
  get_class_type: function (callback) {
    site.get_types(function (rdata) {
      bt.render({
        table: '#type_table',
        columns: [
          { field: 'name', title: '名称' },
          { field: 'opt', width: '80px', title: '操作', templet: function (item) { return '<a class="btlink edit_type" href="javascript:;">编辑</a> | <a class="btlink del_type" href="javascript:;">删除</a>'; } }
        ],
        data: rdata
      });
      $('.layui-layer-page').css({ 'margin-top': '-' + ($('.layui-layer-page').height() / 2) + 'px', 'top': '50%' });
      site.reader_site_type(rdata);
      if (callback) callback(rdata);
    });
  },
  ssl: {
    my_ssl_msg: null,

    //续签订单内
    renew_ssl: function (siteName, auth_type, index) {
      acme.siteName = siteName;
      if (index.length === 32 && index.indexOf('/') === -1) {
        acme.renew(index, function (rdata) {
          site.ssl.ssl_result(rdata, auth_type, siteName)
        });
      } else {
        acme.get_cert_init(index, siteName, function (cert_init) {
          acme.domains = cert_init.dns;
          var options = '<option value="http">文件验证 - HTTP</option>';
          for (var i = 0; i < cert_init.dnsapi.length; i++) {
            options += '<option value="' + cert_init.dnsapi[i].name + '">DNS验证 - ' + cert_init.dnsapi[i].title + '</option>';
          }
          acme.select_loadT = layer.open({
            title: '续签Let\'s Encrypt证书',
            type: 1,
            closeBtn: 2,
            shade: 0.3,
            area: "500px",
            offset: "30%",
            content: '<div style="margin: 10px;">\
                                    <div class="line ">\
                                        <span class="tname" style="padding-right: 15px;margin-top: 8px;">请选择验证方式</span>\
                                        <div class="info-r label-input-group ptb10">\
                                            <select class="bt-input-text" name="auth_to">' + options + '</select>\
                                            <span class="dnsapi-btn"></span>\
                                            <span class="renew-onkey"><button class="btn btn-success btn-sm mr5" style="margin-left: 10px;" onclick="site.ssl.renew_ssl_other()">一键续签</button></span>\
                                        </div>\
                                    </div>\
                                    <ul class="help-info-text c7">\
                                        <li>通配符证书不能使用【文件验证】，请选择DNS验证</li>\
                                        <li>使用【文件验证】，请确保没有开[启强制HTTPS/301重定向/反向代理]等功能</li>\
                                        <li>使用【阿里云DNS】【DnsPod】等验证方式需要设置正确的密钥</li>\
                                        <li>续签成功后，证书将在下次到期前30天尝试自动续签</li>\
                                        <li>使用【DNS验证 - 手动解析】续签的证书无法实现下次到期前30天自动续签</li>\
                                    </ul>\
                                  </div>',
            success: function (layers) {
              $("select[name='auth_to']").change(function () {
                var dnsapi = $(this).val();
                $(".dnsapi-btn").html('');
                for (var i = 0; i < cert_init.dnsapi.length; i++) {
                  if (cert_init.dnsapi[i].name !== dnsapi) continue;
                  acme.dnsapi = cert_init.dnsapi[i]
                  if (!cert_init.dnsapi[i].data) continue;
                  $(".dnsapi-btn").html('<button class="btn btn-default btn-sm mr5 set_dns_config" onclick="site.ssl.show_dnsapi_setup()">设置</button>');
                  if (cert_init.dnsapi[i].data[0].value || cert_init.dnsapi[i].data[1].value) break;
                  site.ssl.show_dnsapi_setup();
                }
              });
            }
          });
        });
      }
    },
    //续签其它
    renew_ssl_other: function () {
      var auth_to = $("select[name='auth_to']").val()
      var auth_type = 'http'
      if (auth_to === 'http') {
        if (JSON.stringify(acme.domains).indexOf('*.') !== -1) {
          layer.msg("包含通配符的域名不能使用文件验证(HTTP)!", { icon: 2 });
          return;
        }
        auth_to = acme.id
      } else {
        if (auth_to !== 'dns') {
          if (auth_to === "Dns_com") {
            acme.dnsapi.data = [{ value: "None" }, { value: "None" }];
          }
          if (!acme.dnsapi.data[0].value || !acme.dnsapi.data[1].value) {
            layer.msg("请先设置【" + acme.dnsapi.title + "】接口信息!", { icon: 2 });
            return;
          }
          auth_to = auth_to + '|' + acme.dnsapi.data[0].value + '|' + acme.dnsapi.data[1].value;
        }
        auth_type = 'dns'
      }
      layer.close(acme.select_loadT);
      acme.apply_cert(acme.domains, auth_type, auth_to, '0', function (rdata) {
        site.ssl.ssl_result(rdata, auth_type, acme.siteName);
      });
    },
    show_dnsapi_setup: function () {
      var dnsapi = acme.dnsapi;
      acme.dnsapi_loadT = layer.open({
        title: '设置【' + dnsapi.title + '】接口',
        type: 1,
        closeBtn: 0,
        shade: 0.3,
        area: "550px",
        offset: "30%",
        content: '<div class="bt-form pd20 pb70 ">\
                            <div class="line ">\
                                <span class="tname" style="width: 125px;">' + dnsapi.data[0].key + '</span>\
                                <div class="info-r" style="margin-left:120px">\
                                    <input name="' + dnsapi.data[0].name + '" class="bt-input-text mr5 dnsapi-key" type="text" style="width:330px" value="' + dnsapi.data[0].value + '">\
                                </div>\
                            </div>\
                            <div class="line ">\
                                <span class="tname" style="width: 125px;">' + dnsapi.data[1].key + '</span>\
                                <div class="info-r" style="margin-left:120px">\
                                    <input name="' + dnsapi.data[1].name + '" class="bt-input-text mr5 dnsapi-token" type="text" style="width:330px" value="' + dnsapi.data[1].value + '">\
                                </div>\
                            </div>\
                            <div class="bt-form-submit-btn">\
                                <button type="button" class="btn btn-sm btn-danger" onclick="layer.close(acme.dnsapi_loadT);">关闭</button>\
                                <button type="button" class="btn btn-sm btn-success dnsapi-save">保存</button>\
                            </div>\
                            <ul class="help-info-text c7">\
                                <li>' + dnsapi.help + '</li>\
                            </ul>\
                          </div>',
        success: function (layers) {
          $(".dnsapi-save").click(function () {
            var dnsapi_key = $(".dnsapi-key");
            var dnsapi_token = $(".dnsapi-token");
            pdata = {}
            pdata[dnsapi_key.attr("name")] = dnsapi_key.val();
            pdata[dnsapi_token.attr("name")] = dnsapi_token.val();
            acme.dnsapi.data[0].value = dnsapi_key.val();
            acme.dnsapi.data[1].value = dnsapi_token.val();
            bt.site.set_dns_api({ pdata: JSON.stringify(pdata) }, function (ret) {
              if (ret.status) layer.close(acme.dnsapi_loadT);
              bt.msg(ret);
            });
          });
        }
      });
    },
    set_cert: function (siteName, res) {
      var loadT = bt.load(lan.site.saving_txt);
      var pdata = {
        type: 1,
        siteName: siteName,
        key: res.private_key,
        csr: res.cert + res.root
      }
      bt.send('SetSSL', 'site/SetSSL', pdata, function (rdata) {
        loadT.close();
        site.reload();
        layer.msg(res.msg, { icon: 1 });
      })
    },
    show_error: function (res, auth_type) {
      var area_size = '500px';
      var err_info = "";
      if (res.msg[1].challenges === undefined) {
        err_info += "<p><span>响应状态:</span>" + res.msg[1].status + "</p>"
        err_info += "<p><span>错误类型:</span>" + res.msg[1].type + "</p>"
        err_info += "<p><span>错误来源:</span><a href='https://letsencrypt.org/' class='btlink'>Let's Encrypt官网</a></p>"
        err_info += "<p><span>错误代码:</span>" + res.msg[1].detail + "</p>"
      } else {
        if (!res.msg[1].challenges[1]) {
          if (res.msg[1].challenges[0]) {
            res.msg[1].challenges[1] = res.msg[1].challenges[0]
          }
        }
        if (res.msg[1].status === 'invalid') {
          area_size = '600px';
          var trs = $("#dns_txt_jx tbody tr");
          var dns_value = "";

          for (var imd = 0; imd < trs.length; imd++) {
            if (trs[imd].outerText.indexOf(res.msg[1].identifier.value) == -1) continue;
            var s_tmp = trs[imd].outerText.split("\t")
            if (s_tmp.length > 1) {
              dns_value = s_tmp[1]
              break;
            }
          }

          err_info += "<p><span>验证域名:</span>" + res.msg[1].identifier.value + "</p>"
          if (auth_type === 'dns') {
            var check_url = "_acme-challenge." + res.msg[1].identifier.value
            err_info += "<p><span>验证解析:</span>" + check_url + "</p>"
            err_info += "<p><span>验证内容:</span>" + dns_value + "</p>"
            err_info += "<p><span>错误代码:</span>" + site.html_encode(res.msg[1].challenges[1].error.detail) + "</p>"
          } else {
            var check_url = "http://" + res.msg[1].identifier.value + '/.well-known/acme-challenge/' + res.msg[1].challenges[0].token
            err_info += "<p><span>验证URL:</span><a class='btlink' href='" + check_url + "' target='_blank'>点击查看</a></p>"
            err_info += "<p><span>验证内容:</span>" + res.msg[1].challenges[0].token + "</p>"
            err_info += "<p><span>错误代码:</span>" + site.html_encode(res.msg[1].challenges[0].error.detail) + "</p>"
          }
          err_info += "<p><span>验证结果:</span> <a style='color:red;'>验证失败</a></p>"
        }
      }

      layer.msg('<div class="ssl-file-error"><a style="color: red;font-weight: 900;">' + res.msg[0] + '</a>' + err_info + '</div>', {
        icon: 2,
        time: 0,
        shade: 0.3,
        shadeClose: true,
        area: area_size
      });
    },
    ssl_result: function (res, auth_type, siteName) {
      layer.close(acme.loadT);
      if (res.status === false && typeof (res.msg) === 'string') {
        bt.msg(res);
        return;
      }
      if (res.status === true || res.status === 'pending' || res.save_path !== undefined) {
        if (auth_type == 'dns' && res.status === 'pending') {
          var b_load = bt.open({
            type: 1,
            area: '700px',
            title: '手动解析TXT记录',
            closeBtn: 2,
            shift: 5,
            shadeClose: false,
            content: "<div class='divtable pd15 div_txt_jx'>\
                                    <p class='mb15' >请按以下列表做TXT解析:</p>\
                                    <table id='dns_txt_jx' class='table table-hover'></table>\
                                    <div class='text-right mt10'>\
                                        <button class='btn btn-success btn-sm btn_check_txt' >验证</button>\
                                    </div>\
                                    </div>"
          });

          //手动验证事件
          $('.btn_check_txt').click(function () {
            acme.auth_domain(res.index, function (res1) {
              layer.close(acme.loadT);
              if (res1.status === true) {
                b_load.close()
                site.ssl.set_cert(siteName, res1)
              } else {
                site.ssl.show_error(res1, auth_type);
              }
            })

          });

          //显示手动验证信息
          setTimeout(function () {
            var data = [];
            acme_txt = '_acme-challenge.'
            for (var j = 0; j < res.auths.length; j++) {
              data.push({
                name: acme_txt + res.auths[j].domain.replace('*.', ''),
                type: "TXT",
                txt: res.auths[j].auth_value,
                force: "是"
              });
              data.push({
                name: res.auths[j].domain.replace('*.', ''),
                type: "CAA",
                txt: '0 issue "letsencrypt.org"',
                force: "否"
              });
            }
            bt.render({
              table: '#dns_txt_jx',
              columns: [
                { field: 'name', width: '220px', title: '解析域名' },
                { field: 'txt', title: '记录值' },
                { field: 'type', title: '类型' },
                { field: 'force', title: '必需' }
              ],
              data: data
            })
            $('.div_txt_jx').append(bt.render_help([
              '解析域名需要一定时间来生效,完成所以上所有解析操作后,请等待1分钟后再点击验证按钮',
              '可通过CMD命令来手动验证域名解析是否生效: nslookup -q=txt ' + acme_txt + res.auths[0].domain.replace('*.', ''),
              '若您使用的是宝塔云解析插件,阿里云DNS,DnsPod作为DNS,可使用DNS接口自动解析'
            ]));
          });
          return;
        }
        site.ssl.set_cert(siteName, res)
        return;
      }

      site.ssl.show_error(res, auth_type);
    },
    get_renew_stat: function () {
      $.post('/ssl?action=Get_Renew_SSL', {}, function (task_list) {
        if (!task_list.status) return;
        var s_body = '';
        var b_stat = false;
        for (var i = 0; i < task_list.data.length; i++) {
          s_body += '<p>' + task_list.data[i].subject + ' >> ' + task_list.data[i].msg + '</p>';
          if (task_list.data[i].status !== true && task_list.data[i].status !== false) {
            b_stat = true;
          }
        }
        if (site.ssl.my_ssl_msg) {
          $(".my-renew-ssl").html(s_body);
        } else {
          site.ssl.my_ssl_msg = layer.msg('<div class="my-renew-ssl">' + s_body + '</div>', { time: 0, icon: 16, shade: 0.3 });
        }

        if (!b_stat) {
          setTimeout(function () {
            layer.close(site.ssl.my_ssl_msg);
            site.ssl.my_ssl_msg = null;
          }, 3000);
          return;
        }
        setTimeout(function () { site.ssl.get_renew_stat(); }, 1000);
      });
    },
    onekey_ssl: function (partnerOrderId, siteName) {
      bt.site.get_ssl_info(partnerOrderId, siteName, function (rdata) {
        bt.msg(rdata);
        if (rdata.status) site.reload(7);
      })
    },
    set_ssl_status: function (action, siteName, ssl_id) {
      bt.site.set_ssl_status(action, siteName, function (rdata) {
        bt.msg(rdata);
        if (rdata.status) {
          site.reload(7);
          if (ssl_id != undefined) {
            setTimeout(function () {
              $('#ssl_tabs span:eq(' + ssl_id + ')').click();
            }, 1000)
          }
          if (action == 'CloseSSLConf') {
            layer.msg(lan.site.ssl_close_info, { icon: 1, time: 5000 });
          }
        }
      })
    },
    verify_domain: function (partnerOrderId, siteName) {
      bt.site.verify_domain(partnerOrderId, siteName, function (vdata) {
        bt.msg(vdata);
        if (vdata.status) {
          if (vdata.data.stateCode == 'COMPLETED') {
            site.ssl.onekey_ssl(partnerOrderId, siteName)
          } else {
            layer.msg('等待CA验证中，若长时间未能成功验证，请登录官网使用DNS方式重新申请...');
          }

        }
      })
    },
    reload: function (index) {
      if (index == undefined) index = 0
      var _sel = $('#ssl_tabs .on');
      if (_sel.length == 0) _sel = $('#ssl_tabs span:eq(0)');
      _sel.trigger('click');
    }
  },
  edit: {
    update_composer: function () {
      loadT = bt.load()
      $.post('/files?action=update_composer', { repo: $("select[name='repo']").val() }, function (v_data) {
        loadT.close();
        bt.msg(v_data);
        site.edit.set_composer(site.edit.compr_web);
      });
    },
    show_composer_log: function () {
      $.post('/ajax?action=get_lines', { filename: '/tmp/composer.log', num: 30 }, function (v_body) {
        var log_obj = $("#composer-log")
        if (log_obj.length < 1) return;
        log_obj.html(v_body.msg);
        var div = document.getElementById('composer-log')
        div.scrollTop = div.scrollHeight;
        if (v_body.msg.indexOf('BT-Exec-Completed') != -1) {
          //layer.close(site.edit.comp_showlog);
          layer.msg('执行完成', { icon: 1 });
          site.edit.set_composer(site.edit.compr_web);
          return;
        }

        setTimeout(function () { site.edit.show_composer_log() }, 1000)
      });
    },
    comp_confirm: 0,
    comp_showlog: 0,
    exec_composer: function () {
      var title_msg = '执行Composer的影响范围取决于该目录下的composer.json配置文件，继续吗？';
      if ($("select[name='composer_args']").val()) {
        title_msg = '即将执行设定的composer命令，继续吗？';
      }
      site.edit.comp_confirm = layer.confirm(title_msg, { title: '确认执行Composer', closeBtn: 2, icon: 3 }, function (index) {
        layer.close(site.edit.comp_confirm);
        var pdata = {
          php_version: $("select[name='php_version']").val(),
          composer_args: $("select[name='composer_args']").val(),
          composer_cmd: $("input[name='composer_cmd']").val(),
          repo: $("select[name='repo']").val(),
          path: $("input[name='composer_path']").val(),
          user: $("select[name='composer_user']").val()
        }
        $.post('/files?action=exec_composer', pdata, function (rdatas) {
          if (!rdatas.status) {
            layer.msg(rdatas.msg, { icon: 2 });
            return false;
          }
          if (rdatas.status === true) {
            site.edit.comp_showlog = layer.open({
              area: "800px",
              type: 1,
              shift: 5,
              closeBtn: 2,
              title: '在[' + pdata['path'] + ']目录执行Composer，执行完后，确认无问题后请关闭此窗口',
              content: "<pre id='composer-log' style='height: 300px;background-color: #333;color: #fff;margin: 0 0 0;'></pre>"
            });
            setTimeout(function () { site.edit.show_composer_log(); }, 200);
          }
        });
      });
    },
    remove_composer_lock: function (path) {
      $.post('/files?action=DeleteFile', { path: path + '/composer.lock' }, function (rdata) {
        bt.msg(rdata);
        $(".composer-msg").remove();
        $(".composer-rm").remove();
      })
    },
    compr_web: null,
    set_composer: function (web) {
      site.edit.compr_web = web;
      $.post('/files?action=get_composer_version', { path: web.path }, function (v_data) {
        if (v_data.status === false) {
          bt.msg(v_data);
          return;
        }

        var php_versions = '';
        for (var i = 0; i < v_data.php_versions.length; i++) {
          if (v_data.php_versions[i].version == '00') continue;
          php_versions += '<option value="' + v_data.php_versions[i].version + '">' + v_data.php_versions[i].name + '</option>';
        }
        if (!php_versions) layer.msg('没有找到可用的PHP版本!', { time: 10000 });

        var msg = '';
        if (v_data.comp_lock) {
          msg += '<span>' + v_data.comp_lock + ' <a class="btlink composer-rm" onclick="site.edit.remove_composer_lock(\'' + web.path + '\')">[点击删除]</a></span>'
        }
        if (v_data.comp_json !== true) {
          msg += '<span>' + v_data.comp_json + '</span>'
        }

        var com_body = '<from class="bt-form" style="padding:30px 0;display:inline-block;width: 630px;">' +
          '<div class="line"><span style="width: 105px;" class="tname">Composer版本</span><div class="info-r"><input readonly="readonly" style="background-color: #eee;width:275px;" name="composer_version" class="bt-input-text" value="' + (v_data.msg ? v_data.msg : '未安装Composer') + '" /><button onclick="site.edit.update_composer();" style="margin-left: 5px;" class="btn btn-default btn-sm">' + (v_data.msg ? '升级Composer' : '安装Composer') + '</button></div></div>' +
          '<div class="line"><span style="width: 105px;" class="tname">PHP版本</span><div class="info-r">' +
          '<select class="bt-input-text" name="php_version" style="width:275px;">' +
          '<option value="auto">自动选择</option>' +
          php_versions +
          '</select>' +
          '</div></div>' +
          '<div class="line"><span style="width: 105px;" class="tname">执行参数</span><div class="info-r">' +
          '<select class="bt-input-text" name="composer_args" style="width:275px;">' +
          '<option value="install">install</option>' +
          '<option value="update">update</option>' +
          '<option value="create-project">create-project</option>' +
          '<option value="require">require</option>' +
          '<option value="other">自定义命令</option>' +
          '</select>' +
          '</div></div>' +
          '<div class="line"><span style="width: 105px;" class="tname">补充命令</span><div class="info-r">' +
          '<input style="width:275px;" class="bt-input-text" id="composer_cmd" name="composer_cmd"  placeholder="输入要操作的应用名称或完整Composer命令" type="text" value="" />' +
          '</div></div>' +
          '<div class="line"><span style="width: 105px;" class="tname">镜像源</span><div class="info-r">' +
          '<select class="bt-input-text" name="repo" style="width:275px;">' +
          '<option value="https://mirrors.aliyun.com/composer/">阿里源(mirrors.aliyun.com)</option>' +
          '<option value="https://mirrors.cloud.tencent.com/composer/">腾讯源(mirrors.cloud.tencent.com)</option>' +
          '<option value="repos.packagist">官方源(packagist.org)</option>' +
          '</select>' +
          '</div></div>' +
          '<div class="line"><span style="width: 105px;" class="tname">执行用户</span><div class="info-r">' +
          '<select class="bt-input-text" name="composer_user" style="width:275px;">' +
          '<option value="www">www(推荐)</option>' +
          '<option value="root">root(不建议)</option>' +
          '</select>' +
          '</div></div>' +
          '<div class="line"><span style="width: 105px;" class="tname">执行目录</span><div class="info-r">' +
          '<input style="width:275px;" class="bt-input-text" id="composer_path" name="composer_path" type="text" value="' + web.path + '" /><span class="glyphicon glyphicon-folder-open cursor ml5" onclick="bt.select_path(\'composer_path\')"></span>' +
          '</div></div>' +
          '<div class="line"><span style="width: 105px;height: 25px;" class="tname"> </span><span class="composer-msg" style="color:red;">' + msg + '</span></div>' +
          '<div class="line" style="clear:both"><span style="width: 105px;" class="tname"> </span><div class="info-r"><button class="btn btn-success btn-sm" onclick="site.edit.exec_composer()">执行</button></div></div>' +
          '</from>' +
          '<ul class="help-info-text c7" style="margin-top: 0;">' +
          '<li>Composer是PHP主流依赖包管理器，若您的项目使用Composer管理依赖包，可在此处对依赖进行升级或安装</li>' +
          '<li>执行目录：默认为当前网站根目录</li>' +
          '<li>执行用户：默认为www用户，除非您的网站以root权限运行，否则不建议使用root用户执行composer</li>' +
          '<li>镜像源：提供【阿里源】和【官方源】，建议国内服务器使用【阿里源】，海外服务器使用【官方源】</li>' +
          '<li>执行参数：按需选择执行参数,可配合补充命令使用</li>' +
          '<li>补充命令：若此处为空，则按composer.json中的配置执行，此处支持填写完整composer命令</li>' +
          '<li>PHP版本：用于执行composer的PHP版本，无特殊要求，默认即可，如安装出错，可尝试选择其它PHP版本</li>' +
          '<li>Composer版本：当前安装的Composer版本，可点击右侧的【升级Composer】将Composer升级到最新稳定版</li>' +
          '</ul>'
        $("#webedit-con").html(com_body);
      });
    },
    set_domains: function (web) {
      var _this = this;
      var list = [{
        class: 'mb0',
        items: [
          { name: 'newdomain', width: '340px', type: 'textarea', placeholder: '每行填写一个域名，默认为80端口<br>泛解析添加方法 *.domain.com<br>如另加端口格式为 www.domain.com:88' },
          {
            name: 'btn_submit_domain',
            text: '添加',
            type: 'button',
            callback: function (sdata) {
              var arrs = sdata.newdomain.split("\n");
              var domins = "";
              for (var i = 0; i < arrs.length; i++) domins += arrs[i] + ",";
              bt.site.add_domains(web.id, web.name, bt.rtrim(domins, ','), function (ret) {
                if (ret.status) site.reload(0)
              })
            }
          }
        ]
      }]
      var _form_data = bt.render_form_line(list[0]),
        loadT = null,
        placeholder = null;
      $('#webedit-con').html(_form_data.html + "<div class='bt_table' id='domain_table'></div>");
      bt.render_clicks(_form_data.clicks);
      $('.btn_submit_domain').addClass('pull-right').css("margin", "30px 35px 0 0");
      placeholder = $(".placeholder");
      placeholder.click(function () {
        $(this).hide();
        $('.newdomain').focus();
      }).css({ 'width': '340px', 'heigth': '100px', 'left': '0px', 'top': '0px', 'padding-top': '10px', 'padding-left': '15px' })
      $('.newdomain').focus(function () {
        placeholder.hide();
        loadT = layer.tips(placeholder.html(), $(this), { tips: [1, '#20a53a'], time: 0, area: $(this).width() });
      }).blur(function () {
        if ($(this).val().length == 0) placeholder.show();
        layer.close(loadT);
      });
      bt_tools.table({
        el: '#domain_table',
        url: '/data?action=getData',
        param: { table: 'domain', list: 'True', search: web.id },
        dataFilter: function (res) {
          return { data: res };
        },
        column: [
          { type: 'checkbox', width: 20, keepNumber: 1 },
          {
            fid: 'name',
            title: '域名',
            template: function (row) {
              return '<a href="http://' + row.name + ':' + row.port + '" target="_blank" class="btlink">' + row.name + '</a>';
            }
          },
          { fid: 'port', title: '端口', width: 50, type: 'text' },
          {
            title: '操作',
            width: 80,
            type: 'group',
            align: 'right',
            group: [{
              title: '删除',
              template: function (row, that) {
                return that.data.length === 1 ? '<span>不可操作</span>' : '删除';
              },
              event: function (row, index, ev, key, that) {
                if (that.data.length === 1) {
                  bt.msg({ status: false, msg: '最后一个域名不能删除!' });
                  return false;
                }
                bt.confirm({ title: '删除域名【' + row.name + '】', msg: lan.site.domain_del_confirm }, function () {
                  bt.site.del_domain(web.id, web.name, row.name, row.port, function (res) {
                    if (res.status) that.$delete_table_row(index);
                    bt.msg(res);
                  });
                });
              }
            }]
          }
        ],
        tootls: [{ // 批量操作
          type: 'batch',
          positon: ['left', 'bottom'],
          config: {
            title: '删除',
            url: '/site?action=delete_domain_multiple',
            param: { id: web.id },
            paramId: 'id',
            paramName: 'domains_id',
            theadName: '域名',
            confirmVerify: false, //是否提示验证方式
            refresh: true
          }
        }]
      });
      $('#domain_table>.divtable').css('max-height', '350px');
    },
    set_dirbind: function (web) {
      var _this = this;
      $('#webedit-con').html('<div id="sub_dir_table"></div>');
      bt_tools.table({
        el: '#sub_dir_table',
        url: '/site?action=GetDirBinding',
        param: { id: web.id },
        dataFilter: function (res) {
          if ($('#webedit-con').children().length === 2) return { data: res.binding }
          var dirs = [];
          for (var n = 0; n < res.dirs.length; n++) dirs.push({ title: res.dirs[n], value: res.dirs[n] });
          var data = {
            title: '',
            class: 'mb0',
            items: [
              { title: '域名', width: '140px', name: 'domain' },
              { title: '子目录', name: 'dirName', type: 'select', items: dirs },
              {
                text: '添加',
                type: 'button',
                name: 'btn_add_subdir',
                callback: function (sdata) {
                  if (!sdata.domain || !sdata.dirName) {
                    layer.msg(lan.site.d_s_empty, { icon: 2 });
                    return;
                  }
                  bt.site.add_dirbind(web.id, sdata.domain, sdata.dirName, function (ret) {
                    layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
                    if (ret.status) site.reload(1)
                  })
                }
              }
            ]
          }
          var _form_data = bt.render_form_line(data);
          $('#webedit-con').prepend(_form_data.html);
          bt.render_clicks(_form_data.clicks);
          return { data: res.binding };
        },
        column: [
          { type: 'checkbox', width: 20, keepNumber: 1 },
          {
            fid: 'domain',
            title: '域名',
            width: 150,
            template: function (row) {
              return '<a class="btlink" href="http://' + row.domain + ':' + row.port + '" target="_blank" title="' + row.domain + '">' + row.domain + '</a>';
            }
          },
          { fid: 'port', title: '端口', width: 70, type: 'text' },
          { fid: 'path', title: '子目录', type: 'text' },
          {
            title: '操作',
            width: 110,
            type: 'group',
            align: 'right',
            group: [{
              title: '伪静态',
              event: function (row, index, ev, key, that) {
                bt.site.get_dir_rewrite({ id: row.id }, function (ret) {
                  if (!ret.status) {
                    var confirmObj = layer.confirm(lan.site.url_rewrite_alter, { icon: 3, closeBtn: 2 }, function () {
                      bt.site.get_dir_rewrite({ id: row.id, add: 1 }, function (ret) {
                        layer.close(confirmObj);
                        show_dir_rewrite(ret);
                      });
                    });
                    return;
                  }
                  show_dir_rewrite(ret);

                  function get_rewrite_file (name) {
                    var spath = '/www/server/panel/rewrite/' + (bt.get_cookie('serverType') == 'openlitespeed' ? 'apache' : bt.get_cookie('serverType')) + '/' + name + '.conf';
                    if (name == lan.site.rewritename) {
                      if (bt.get_cookie('serverType') == 'nginx') {
                        spath = '/www/server/panel/vhost/rewrite/' + web.name + '_' + row['path'] + '.conf';
                      } else {
                        spath = '/www/wwwroot/' + web.name + '/' + row['path'] + '.htaccess';
                      }
                    }
                    bt.files.get_file_body(spath, function (sdata) {
                      $('.dir_config').text(sdata.data);
                    });
                  }

                  function show_dir_rewrite (ret) {
                    var load_form = bt.open({
                      type: 1,
                      area: ['510px', '515px'],
                      title: lan.site.config_url,
                      closeBtn: 2,
                      shift: 5,
                      skin: 'bt-w-con',
                      shadeClose: true,
                      content: "<div class='bt-form webedit-dir-box dir-rewrite-man-con'></div>",
                      success: function () {
                        var _html = $(".webedit-dir-box"),
                          arrs = [];
                        for (var i = 0; i < ret.rlist.length; i++) {
                          arrs.push({ title: ret.rlist[i], value: ret.rlist[i] });
                        }
                        var datas = [{
                          name: 'dir_rewrite',
                          type: 'select',
                          width: '130px',
                          items: arrs,
                          callback: function (obj) {
                            get_rewrite_file(obj.val(), 'sub_dir');
                          }
                        },
                        { items: [{ name: 'dir_config', type: 'textarea', value: ret.data, width: '470px', height: '260px' }] },
                        {
                          items: [{
                            name: 'btn_save',
                            text: '保存',
                            type: 'button',
                            callback: function (ldata) {
                              bt.files.set_file_body(ret.filename, ldata.dir_config, 'utf-8', function (sdata) {
                                if (sdata.status) load_form.close();
                                bt.msg(sdata);
                              })
                            }
                          }]
                        }
                        ]
                        var clicks = [];
                        for (var i = 0; i < datas.length; i++) {
                          var _form_data = bt.render_form_line(datas[i]);
                          _html.append(_form_data.html);
                          var _other = (bt.os == 'Linux' && i == 0) ? '<span>规则转换工具：<a href="https://www.bt.cn/Tools" target="_blank" style="color:#20a53a">Apache转Nginx</a></span>' : '';
                          _html.find('.info-r').append(_other)
                          clicks = clicks.concat(_form_data.clicks);
                        }
                        _html.append(bt.render_help(['请选择您的应用，若设置伪静态后，网站无法正常访问，请尝试设置回default', '您可以对伪静态规则进行修改，修改完后保存即可。']));
                        bt.render_clicks(clicks);
                        get_rewrite_file($('.dir_rewrite option:eq(0)').val());
                      }
                    });
                  }
                })
              }
            }, {
              title: '删除',
              event: function (row, index, ev, key, that) {
                bt.confirm({ title: '删除子目录绑定【' + row.path + '】', msg: lan.site.s_bin_del }, function () {
                  bt.site.del_dirbind(row.id, function (res) {
                    if (res.status) that.$delete_table_row(index);
                    bt.msg(res);
                  })
                });
              }
            }]
          }
        ],
        tootls: [{ // 批量操作
          type: 'batch',
          positon: ['left', 'bottom'],
          config: {
            title: '删除',
            url: '/site?action=delete_dir_bind_multiple',
            param: { id: web.id },
            paramId: 'id',
            paramName: 'bind_ids',
            theadName: '域名',
            confirmVerify: false, //是否提示验证方式
            refresh: true
          }
        }]
      });
    },
    set_dirpath: function (web) {
      var loading = bt.load();
      bt.site.get_site_path(web.id, function (path) {
        bt.site.get_dir_userini(web.id, path, function (rdata) {
          loading.close();
          var dirs = [];
          var is_n = false;
          for (var n = 0; n < rdata.runPath.dirs.length; n++) {
            dirs.push({ title: rdata.runPath.dirs[n], value: rdata.runPath.dirs[n] });
            if (rdata.runPath.runPath === rdata.runPath.dirs[n]) is_n = true;
          }
          if (!is_n) dirs.push({ title: rdata.runPath.runPath, value: rdata.runPath.runPath });
          var datas = [{
            title: '',
            items: [{
              name: 'userini',
              type: 'checkbox',
              text: '防跨站攻击(open_basedir)',
              value: rdata.userini,
              callback: function (sdata) {
                bt.site.set_dir_userini(path, function (ret) {
                  if (ret.status) site.reload(2)
                  layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
                })
              }
            },
            {
              name: 'logs',
              type: 'checkbox',
              text: '写访问日志',
              value: rdata.logs,
              callback: function (sdata) {
                bt.site.set_logs_status(web.id, function (ret) {
                  if (ret.status) site.reload(2)
                  layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
                })
              }
            }
            ]
          },
          {
            title: '',
            items: [
              { name: 'path', title: '网站目录', width: '240px', value: path, event: { css: 'glyphicon-folder-open', callback: function (obj) { bt.select_path(obj); } } },
              {
                name: 'btn_site_path',
                class: "ml10",
                type: 'button',
                text: '保存',
                callback: function (pdata) {
                  bt.site.set_site_path(web.id, pdata.path, function (ret) {
                    if (ret.status) site.reload(2)
                    layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
                  })
                }
              }
            ]
          },
          {
            title: '',
            items: [
              { title: '运行目录', width: '240px', value: rdata.runPath.runPath, name: 'dirName', type: 'select', items: dirs },
              {
                name: 'btn_run_path',
                type: 'button',
                text: '保存',
                callback: function (pdata) {
                  bt.site.set_site_runpath(web.id, pdata.dirName, function (ret) {
                    if (ret.status) site.reload(2)
                    layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
                  })
                }
              }
            ]
          }
          ]
          var _html = $("<div class='webedit-box soft-man-con'></div>")
          var clicks = [];
          for (var i = 0; i < datas.length; i++) {
            var _form_data = bt.render_form_line(datas[i]);
            _html.append($(_form_data.html).addClass('line mtb10'));
            clicks = clicks.concat(_form_data.clicks);
          }
          _html.find('input[type="checkbox"]').parent().addClass('label-input-group ptb10');
          _html.find('button[name="btn_run_path"]').addClass('ml45');
          _html.find('button[name="btn_site_path"]').addClass('ml33');
          _html.append(bt.render_help(['部分程序需要指定二级目录作为运行目录，如ThinkPHP5，Laravel', '选择您的运行目录，点保存即可']));
          if (bt.os == 'Linux') _html.append('<div class="user_pw_tit" style="margin-top: 2px;padding-top: 11px;"><span class="tit">密码访问</span><span class="btswitch-p"><input class="btswitch btswitch-ios" id="pathSafe" type="checkbox"><label class="btswitch-btn phpmyadmin-btn" for="pathSafe" ></label></span></div><div class="user_pw" style="margin-top: 10px; display: block;"></div>')

          $('#webedit-con').append(_html);
          bt.render_clicks(clicks);
          $('#pathSafe').click(function () {
            var val = $(this).prop('checked');
            var _div = $('.user_pw')
            if (val) {
              var dpwds = [
                { title: '授权账号', width: '200px', name: 'username_get', placeholder: '不修改请留空' },
                { title: '访问密码', width: '200px', type: 'password', name: 'password_get_1', placeholder: '不修改请留空' },
                { title: '重复密码', width: '200px', type: 'password', name: 'password_get_2', placeholder: '不修改请留空' },
                {
                  name: 'btn_password_get',
                  text: '保存',
                  type: 'button',
                  callback: function (rpwd) {
                    if (rpwd.password_get_1 != rpwd.password_get_2) {
                      layer.msg(lan.bt.pass_err_re, { icon: 2 });
                      return;
                    }
                    bt.site.set_site_pwd(web.id, rpwd.username_get, rpwd.password_get_1, function (ret) {
                      layer.msg(ret.msg, { icon: ret.status ? 1 : 2 })
                      if (ret.status) site.reload(2)
                    })
                  }
                }
              ]
              for (var i = 0; i < dpwds.length; i++) {
                var _from_pwd = bt.render_form_line(dpwds[i]);
                _div.append("<div class='line'>" + _from_pwd.html + "</div>");
                bt.render_clicks(_from_pwd.clicks);
              }
            } else {
              bt.site.close_site_pwd(web.id, function (rdata) {
                layer.msg(rdata.msg, { icon: rdata.status ? 1 : 2 });
                _div.html('');
              })
            }
          })
          if (rdata.pass) $('#pathSafe').trigger('click');
        })
      })
    },
    set_dirguard: function (web) {
      $('#webedit-con').html('<div id="set_dirguard"></div>');
      var tab = '<div class="tab-nav mb15">\
                    <span class="on">加密访问</span><span class="">禁止访问</span>\
                    </div>\
                    <div id="dir_dirguard"></div>\
                    <div id="php_dirguard" style="display:none;"></div>';
      $("#set_dirguard").html(tab)
      bt_tools.table({
        el: '#dir_dirguard',
        url: '/site?action=get_dir_auth',
        param: { id: web.id },
        dataFilter: function (res) {
          return { data: res[web.name] };
        },
        column: [
          { type: 'checkbox', width: 20 },
          { fid: 'name', title: '名称', type: 'text' },
          { fid: 'site_dir', title: '加密访问', type: 'text' },
          {
            title: '操作',
            width: 110,
            type: 'group',
            align: 'right',
            group: [{
              title: '编辑',
              event: function (row, index, ev, key, that) {
                site.edit.template_Dir(web.id, false, row);
              }
            }, {
              title: '删除',
              event: function (row, index, ev, key, that) {
                bt.site.delete_dir_guard(web.id, row.name, function (res) {
                  if (res.status) that.$delete_table_row(index);
                  bt.msg(res);
                });
              }
            }],
          }
        ],
        tootls: [{ // 按钮组
          type: 'group',
          positon: ['left', 'top'],
          list: [{
            title: '添加加密访问',
            active: true,
            event: function (ev) {
              site.edit.template_Dir(web.id, true);
            }
          }]
        }, { // 批量操作
          type: 'batch',
          positon: ['left', 'bottom'],
          config: {
            title: '删除',
            url: '/site?action=delete_dir_auth_multiple',
            param: { site_id: web.id },
            paramId: 'name',
            paramName: 'names',
            theadName: '加密访问名称',
            confirmVerify: false, //是否提示验证方式
            refresh: true
          }
        }]
      });
      bt_tools.table({
        el: '#php_dirguard',
        url: '/config?action=get_file_deny',
        param: { website: web.name },
        dataFilter: function (res) {
          return { data: res };
        },
        column: [
          { fid: 'name', title: '名称', type: 'text' },
          {
            fid: 'dir',
            title: '保护的目录',
            type: 'text',
            template: function (row) {
              return '<span title="' + row.dir + '" style="max-width: 250px;text-overflow: ellipsis;overflow: hidden;display: inline-block;">' + row.dir + '</span>';
            }
          },
          {
            fid: 'suffix',
            title: '规则',
            template: function (row) {
              return '<span title="' + row.suffix + '" style="max-width: 85px;text-overflow: ellipsis;overflow: hidden;display: inline-block;">' + row.suffix + '</span>';
            }
          },
          {
            title: '操作',
            width: 110,
            type: 'group',
            align: 'right',
            group: [{
              title: '编辑',
              event: function (row, index, ev, key, that) {
                site.edit.template_php(web.name, row);
              }
            }, {
              title: '删除',
              event: function (row, index, ev, key, that) {
                bt.site.delete_php_guard(web.name, row.name, function (res) {
                  if (res.status) that.$delete_table_row(index);
                  bt.msg(res);
                });
              }
            }],
          }
        ],
        tootls: [{ // 按钮组
          type: 'group',
          positon: ['left', 'top'],
          list: [{
            title: '添加禁止访问',
            active: true,
            event: function (ev) {
              site.edit.template_php(web.name);
            }
          }]
        }]
      });
      $('#dir_dirguard>.divtable,#php_dirguard>.divtable').css('max-height', '405px');
      $('#dir_dirguard').append("<ul class='help-info-text c7'>\
                <li>目录设置加密访问后，访问时需要输入账号密码才能访问</li>\
                <li>例如我设置了加密访问 /test/ ,那我访问 http://aaa.com/test/ 是就要输入账号密码才能访问</li>\
            </ul>");
      $('#php_dirguard').append("<ul class='help-info-text c7'>\
                <li>后缀：禁止访问的文件后缀</li>\
                <li>目录：规则会在这个目录内生效</li>\
            </ul>");
      $("#set_dirguard").on('click', '.tab-nav span', function () {
        var index = $(this).index();
        $(this).addClass('on').siblings().removeClass('on');
        if (index == 0) {
          $("#dir_dirguard").show();
          $("#php_dirguard").hide();
        } else {
          $("#php_dirguard").show();
          $("#dir_dirguard").hide();
        }
      });
    },
    ols_cache: function (web) {
      bt.send('get_ols_static_cache', 'config/get_ols_static_cache', { id: web.id }, function (rdata) {
        var clicks = [],
          newkey = [],
          newval = [],
          checked = false;
        Object.keys(rdata).forEach(function (key) {
          //for (let key in rdata) {
          newkey.push(key);
          newval.push(rdata[key]);
        });
        var datas = [{ title: newkey[0], name: newkey[0], width: '30%', value: newval[0] },
        { title: newkey[1], name: newkey[1], width: '30%', value: newval[1] },
        { title: newkey[2], name: newkey[2], width: '30%', value: newval[2] },
        { title: newkey[3], name: newkey[3], width: '30%', value: newval[3] },
        {
          name: 'static_save',
          text: '保存',
          type: 'button',
          callback: function (ldata) {
            var cdata = {},
              loadT = bt.load();
            Object.assign(cdata, ldata);
            delete cdata.static_save;
            delete cdata.maxage;
            delete cdata.exclude_file;
            delete cdata.private_save;
            bt.send('set_ols_static_cache', 'config/set_ols_static_cache', { values: JSON.stringify(cdata), id: web.id }, function (res) {
              loadT.close();
              bt.msg(res)
            });
          }
        },
        { title: 'test', name: 'test', width: '30%', value: '11' },
        { title: '缓存时间', name: 'maxage', width: '30%', value: '43200' },
        { title: '排除文件', name: 'exclude_file', width: '35%', value: 'fdas.php', },
        {
          name: 'private_save',
          text: '保存',
          type: 'button',
          callback: function (ldata) {
            var edata = {},
              loadT = bt.load();
            if (checked) {
              edata.id = web.id;
              edata.max_age = parseInt($("input[name='maxage']").val());
              edata.exclude_file = $("textarea[name='exclude_file']").val();
              bt.send('set_ols_private_cache', 'config/set_ols_private_cache', edata, function (res) {
                loadT.close();
                bt.msg(res)
              });
            }
          }
        }
        ],
          _html = $('<div class="ols"></div>');
        for (var i = 0; i < datas.length; i++) {
          var _form_data = bt.render_form_line(datas[i]);
          _html.append(_form_data.html);
          clicks = clicks.concat(_form_data.clicks);
        }
        $('#webedit-con').append(_html);
        $("input[name='exclude_file']").parent().removeAttr('class').html('<textarea name="exclude_file" class="bt-input-text mr5 exclude_file" style="width:35%;height: 130px;"></textarea>');
        $("input[name='test']").parent().parent().html('<div style="padding-left: 29px;border-top: #ccc 1px dashed;margin-top: -7px;"><em style="float: left;color: #555;font-style: normal;line-height: 32px;padding-right: 2px;">私有缓存</em><div style="margin-left: 70px;padding-top: 5px;"><input class="btswitch btswitch-ios" id="ols" type="checkbox"><label class="btswitch-btn" for="ols"></label></div></div>');
        var private = $("input[name='maxage'],textarea[name='exclude_file'],button[name='private_save']").parent().parent();
        $("input.bt-input-text").parent().append('<span>秒</span>');
        $("button[name='static_save']").parent().append(bt.render_help(['默认的静态文件缓存时间是604800秒', '如果要关闭，请将其更改为0秒']));
        $(".ols").append(bt.render_help(['私有缓存只支持PHP页面缓存，默认缓存时间为120秒', '排除文件仅支持以PHP为后缀的文件']));
        private.hide();
        var loadT = bt.load();
        bt.send('get_ols_private_cache_status', 'config/get_ols_private_cache_status', { id: web.id }, function (kdata) {
          loadT.close();
          checked = kdata;
          if (kdata) {
            bt.send('get_ols_private_cache', 'config/get_ols_private_cache', { id: web.id }, function (fdata) {
              $("input[name='maxage']").val(fdata.maxage);
              var ss = fdata.exclude_file.join("&#13;");
              $("textarea[name='exclude_file']").html(ss);
              $("#ols").attr('checked', true);
              private.show();
            });
          }
        });
        $('#ols').on('click', function () {
          var loadS = bt.load();
          bt.send('switch_ols_private_cache', 'config/switch_ols_private_cache', { id: web.id }, function (res) {
            loadS.close();
            private.toggle();
            checked = private.is(':hidden') ? false : true;
            bt.msg(res);
            if (checked) {
              bt.send('get_ols_private_cache', 'config/get_ols_private_cache', { id: web.id }, function (fdata) {
                private.show();
                $("input[name='maxage']").val(fdata.maxage);
                $("textarea[name='exclude_file']").html(fdata.exclude_file.join("&#13;"));
              });
            }
          });
        });
        bt.render_clicks(clicks);
        $("button[name='private_save']").parent().css("margin-bottom", "-13px");
        $('.ss-text').css("margin-left", "66px");
        $('.ols .btn-success').css("margin-left", "100px");
      })
    },
    limit_network: function (web) {
      bt.site.get_limitnet(web.id, function (rdata) {
        var limits = [
          { title: '论坛/博客', value: 1, items: { perserver: 300, perip: 25, limit_rate: 512 } },
          { title: '图片站', value: 2, items: { perserver: 200, perip: 10, limit_rate: 1024 } },
          { title: '下载站', value: 3, items: { perserver: 50, perip: 3, limit_rate: 2048 } },
          { title: '商城', value: 4, items: { perserver: 500, perip: 10, limit_rate: 2048 } },
          { title: '门户', value: 5, items: { perserver: 400, perip: 15, limit_rate: 1024 } },
          { title: '企业', value: 6, items: { perserver: 60, perip: 10, limit_rate: 512 } },
          { title: '视频', value: 7, items: { perserver: 150, perip: 4, limit_rate: 1024 } }
        ]
        var datas = [{
          items: [{
            name: 'status',
            type: 'checkbox',
            value: rdata.perserver != 0 ? true : false,
            text: '启用流量控制',
            callback: function (ldata) {
              if (ldata.status) {
                bt.site.set_limitnet(web.id, ldata.perserver, ldata.perip, ldata.limit_rate, function (ret) {
                  layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
                  if (ret.status) site.reload(3)
                })
              } else {
                bt.site.close_limitnet(web.id, function (ret) {
                  layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
                  if (ret.status) site.reload(3)
                })
              }
            }
          }]
        },
        {
          items: [{
            title: '限制方案  ',
            width: '160px',
            name: 'limit',
            type: 'select',
            items: limits,
            callback: function (obj) {
              var data = limits.filter(function (p) { return p.value === parseInt(obj.val()); })[0]
              for (var key in data.items) {
                $('input[name="' + key + '"]').val(data.items[key]);
              }
            }
          }]
        },
        { items: [{ title: '并发限制   ', type: 'number', width: '200px', value: rdata.perserver, name: 'perserver' }] },
        { items: [{ title: '单IP限制   ', type: 'number', width: '200px', value: rdata.perip, name: 'perip' }] },
        { items: [{ title: '流量限制   ', type: 'number', width: '200px', value: rdata.limit_rate, name: 'limit_rate' }] },
        {
          name: 'btn_limit_get',
          text: '保存',
          type: 'button',
          callback: function (ldata) {
            bt.site.set_limitnet(web.id, ldata.perserver, ldata.perip, ldata.limit_rate, function (ret) {
              layer.msg(ret.msg, { icon: ret.status ? 1 : 2 });
              if (ret.status) site.reload(3)
            })
          }
        }
        ]
        var _html = $("<div class='webedit-box soft-man-con'></div>")
        var clicks = [];
        for (var i = 0; i < datas.length; i++) {
          var _form_data = bt.render_form_line(datas[i]);
          _html.append(_form_data.html);
          clicks = clicks.concat(_form_data.clicks);
        }
        _html.find('input[type="checkbox"]').parent().addClass('label-input-group ptb10');
        _html.append(bt.render_help(['限制当前站点最大并发数', '限制单个IP访问最大并发数', '限制每个请求的流量上限（单位：KB）']));
        $('#webedit-con').append(_html);
        bt.render_clicks(clicks);
        if (rdata.perserver == 0) $("select[name='limit']").trigger("change")
      })
    },
    get_rewrite_list: function (web, callback) {
      var filename = '/www/server/panel/vhost/rewrite/' + web.name + '.conf';

      bt.site.get_rewrite_list(web.name, function (rdata) {
        if (typeof rdata != 'object') return;
        var arrs = [],
          webserver = bt.get_cookie('serverType');
        if (bt.get_cookie('serverType') == 'apache') filename = rdata.sitePath + '/.htaccess';
        if (webserver == 'apache' || webserver == 'openlitespeed') filename = rdata.sitePath + '/.htaccess';
        if (webserver == 'openlitespeed') webserver = 'apache';
        for (var i = 0; i < rdata.rewrite.length; i++) arrs.push({ title: rdata.rewrite[i], value: rdata.rewrite[i] });
        var datas = [{
          name: 'rewrite',
          type: 'select',
          width: '130px',
          items: arrs,
          callback: function (obj) {
            if (bt.os == 'Linux') {
              var spath = filename;
              if (obj.val() != lan.site.rewritename) spath = '/www/server/panel/rewrite/' + (webserver == 'openlitespeed' ? 'apache' : webserver) + '/' + obj.val() + '.conf';
              bt.files.get_file_body(spath, function (ret) {
                aceEditor.ACE.setValue(ret.data);
                aceEditor.ACE.moveCursorTo(0, 0);
                aceEditor.path = spath;
              })
            }
          }
        },
        { items: [{ name: 'config', type: 'div', value: rdata.data, widht: '340px', height: '200px' }] },
        {
          items: [{
            name: 'btn_save',
            text: '保存',
            type: 'button',
            callback: function (ldata) {
              // bt.files.set_file_body(filename, editor.getValue(), 'utf-8', function (ret) {
              //     if (ret.status) site.reload(4)
              //     bt.msg(ret);
              // })
              aceEditor.path = filename;
              bt.saveEditor(aceEditor);
            }
          },
          {
            name: 'btn_save_to',
            text: '另存为模板',
            type: 'button',
            callback: function (ldata) {
              var temps = {
                title: lan.site.save_rewrite_temp,
                area: '330px',
                list: [
                  { title: '模板名称', placeholder: '模板名称', width: '160px', name: 'tempname' }
                ],
                btns: [
                  { title: '关闭', name: 'close' },
                  {
                    title: '提交',
                    name: 'submit',
                    css: 'btn-success',
                    callback: function (rdata, load, callback) {
                      var name = rdata.tempname;
                      var isSameName = false;
                      for (var i = 0; i < arrs.length; i++) {
                        if (arrs[i].value == name) {
                          isSameName = true;
                          break;
                        }
                      }
                      var save_to = function () {
                        bt.site.set_rewrite_tel(name, aceEditor.ACE.getValue(), function (rRet) {
                          if (rRet.status) {
                            load.close();
                            site.reload(4)
                          }
                          bt.msg(rRet);
                        });
                      };
                      if (isSameName) {
                        bt.confirm({
                          icon: 0,
                          title: '提示',
                          msg: '【' + name + '】已存在，是否要替换？'
                        }, function () {
                          save_to();
                        });
                      } else {
                        save_to();
                      }
                    }
                  }
                ]
              }
              bt.render_form(temps);
            }
          }
          ]
        }
        ]

        var _html = $("<div class='webedit-box soft-man-con'></div>")
        var clicks = [];
        for (var i = 0; i < datas.length; i++) {
          var _form_data = bt.render_form_line(datas[i]);
          _html.append(_form_data.html);
          var _other = (bt.os == 'Linux' && i == 0) ? '<span>规则转换工具：<a href="https://www.bt.cn/Tools" target="_blank" style="color:#20a53a">Apache转Nginx</a></span>' : '';
          _html.find('.info-r').append(_other)
          clicks = clicks.concat(_form_data.clicks);
        }
        _html.append(bt.render_help(['请选择您的应用，若设置伪静态后，网站无法正常访问，请尝试设置回default', '您可以对伪静态规则进行修改，修改完后保存即可。']));
        $('#webedit-con').append(_html);
        bt.render_clicks(clicks);
        $('div.config').attr('id', 'config_rewrite').css({ 'height': '360px', 'width': '540px' })
        var aceEditor = bt.aceEditor({ el: 'config_rewrite', content: rdata.data });
        $('select.rewrite').trigger('change');
        if (callback) callback(rdata)
      })
    },
    set_default_index: function (web) {
      bt.site.get_index(web.id, function (rdata) {
        if (typeof rdata == 'object' && rdata.status === false) {
          bt.msg(rdata);
          return;
        }
        rdata = rdata.replace(new RegExp(/(,)/g), "\n");
        var data = {
          items: [
            { name: 'Dindex', height: '230px', width: '50%', type: 'textarea', value: rdata },
            {
              name: 'btn_submit',
              text: '添加',
              type: 'button',
              callback: function (ddata) {
                var Dindex = ddata.Dindex.replace(new RegExp(/(\n)/g), ",");
                bt.site.set_index(web.id, Dindex, function (ret) {
                  if (ret.status) site.reload(5)
                })
              }
            }
          ]
        }
        var _form_data = bt.render_form_line(data);
        var _html = $(_form_data.html)
        _html.append(bt.render_help([lan.site.default_doc_help]))
        $('#webedit-con').append(_html);
        $('.btn_submit').addClass('pull-right').css("margin", "90px 100px 0 0")
        bt.render_clicks(_form_data.clicks);
      })
    },
    set_config: function (web) {
      var con = '<p style="color: #666; margin-bottom: 7px">提示：Ctrl+F 搜索关键字，Ctrl+S 保存，Ctrl+H 查找替换</p><div class="bt-input-text ace_config_editor_scroll" style="height: 400px; line-height:18px;" id="siteConfigBody"></div>\
				<button id="OnlineEditFileBtn" class="btn btn-success btn-sm" style="margin-top:10px;">保存</button>\
				<ul class="c7 ptb15">\
					<li>此处为站点主配置文件,若您不了解配置规则,请勿随意修改.</li>\
				</ul>';
      $("#webedit-con").html(con);
      var webserve = bt.get_cookie('serverType'),
        config = bt.aceEditor({ el: 'siteConfigBody', path: '/www/server/panel/vhost/' + (webserve == 'openlitespeed' ? (webserve + '/detail') : webserve) + '/' + web.name + '.conf' });
      $("#OnlineEditFileBtn").click(function (e) {
        bt.saveEditor(config);
      });
    },
    set_php_version: function (web) {
      bt.site.get_site_phpversion(web.name, function (sdata) {
        if (sdata.status === false) {
          bt.msg(sdata);
          return;
        }
        bt.site.get_all_phpversion(function (vdata) {
          var versions = [];
          for (var j = vdata.length - 1; j >= 0; j--) {
            var o = vdata[j];
            o.value = o.version;
            o.title = o.name;
            versions.push(o);
          }
          var data = {
            items: [
              {
                title: 'PHP版本',
                name: 'versions',
                value: sdata.phpversion,
                type: 'select',
                items: versions,
                ps: '<input class="bt-input-text other-version" style="margin-right: 10px;width:300px;color: #000;" type="text" value="' + sdata.php_other + '" placeholder="连接配置，如：1.1.1.1:9001或unix:/tmp/php.sock" />'
              },
              {
                text: '切换',
                name: 'btn_change_phpversion',
                type: 'button',
                callback: function (pdata) {
                  var other = $('.other-version').val();
                  if (pdata.versions == 'other' && other == '') {
                    layer.msg('自定义PHP版本时，PHP连接配置不能为空', { icon: 2 });
                    $('.other-version').focus();
                    return;
                  }
                  bt.site.set_phpversion(web.name, pdata.versions, other, function (ret) {
                    if (ret.status) {
                      var versions = $('[name="versions"]').val();
                      versions = versions.slice(0, versions.length - 1) + '.' + versions.slice(-1);
                      if (versions == '0.0') versions = '静态';
                      site.php_table_view();
                      site.reload();
                      setTimeout(function () {
                        bt.msg(ret);
                      }, 1000);
                    } else {
                      bt.msg(ret);
                    }
                  })
                }
              }
            ]
          }
          var _form_data = bt.render_form_line(data);
          var _html = $(_form_data.html);
          _html.append(bt.render_help(['请根据您的程序需求选择版本', '若非必要,请尽量不要使用PHP5.2,这会降低您的服务器安全性；', 'PHP7不支持mysql扩展，默认安装mysqli以及mysql-pdo。', "【自定义】可自定义PHP连接信息，选择此项需填写可用的PHP连接配置", "【自定义】当前仅支持nginx，可配合[宝塔负载均衡 - 重构版]插件的TCP负载功能实现PHP负载集群", "【PHP连接配置】支持TCP或Unix配置，示例：192.168.1.25:9001 或 unix:/tmp/php8.sock"]));
          $('#webedit-con').append(_html);
          bt.render_clicks(_form_data.clicks);
          if (sdata.phpversion != 'other') {
            $('#webedit-con').append('<div class="user_pw_tit" style="margin-top: 2px;padding-top: 11px;border-top: #ccc 1px dashed;"><span class="tit">session隔离</span><span class="btswitch-p" style="display: inline-flex;"><input class="btswitch btswitch-ios" id="session_switch" type="checkbox"><label class="btswitch-btn session-btn" for="session_switch" ></label></span></div><div class="user_pw" style="margin-top: 10px; display: block;"></div>' +
              bt.render_help(['开启后将会把session文件存放到独立文件夹，不与其他站点公用存储位置', '若您在PHP配置中将session保存到memcache/redis等缓存器时，请不要开启此选项']));
          }
          if (sdata.phpversion != 'other') {
            $('.other-version').hide();
          }
          setTimeout(function () {
            $('select[name="versions"]').change(function () {
              var phpversion = $(this).val();
              if (phpversion == 'other') {
                $('.other-version').show();
              } else {
                $('.other-version').hide();
              }
            });
          }, 500);


          function get_session_status () {
            var loading = bt.load('正在获取session状态请稍候');
            bt.send('get_php_session_path', 'config/get_php_session_path', { id: web.id }, function (tdata) {
              loading.close();
              $('#session_switch').prop("checked", tdata);
            })
          };
          get_session_status()
          $('#session_switch').click(function () {
            var val = $(this).prop('checked');
            bt.send('set_php_session_path', 'config/set_php_session_path', { id: web.id, act: val ? 1 : 0 }, function (rdata) {
              bt.msg(rdata)
            })
            setTimeout(function () {
              get_session_status();
            }, 500);
          })
        })
      })
    },
    templet_301: function (sitename, id, types, obj) {
      if (types) {
        obj = {
          redirectname: (new Date()).valueOf(),
          tourl: 'http://',
          redirectdomain: [],
          redirectpath: '',
          redirecttype: '',
          type: 1,
          domainorpath: 'domain',
          holdpath: 1
        }
      }
      var helps = [
        '重定向类型：表示访问选择的“域名”或输入的“路径”时将会重定向到指定URL',
        '目标URL：可以填写你需要重定向到的站点，目标URL必须为可正常访问的URL，否则将返回错误',
        '重定向方式：使用301表示永久重定向，使用302表示临时重定向',
        '保留URI参数：表示重定向后访问的URL是否带有子路径或参数如设置访问http://b.com 重定向到http://a.com',
        '保留URI参数：  http://b.com/1.html ---> http://a.com/1.html',
        '不保留URI参数：http://b.com/1.html ---> http://a.com'
      ];
      bt.site.get_domains(id, function (rdata) {
        var table_data = site.edit.redirect_table.data;
        var flag = true;
        var domain_html = '';
        var select_list = [];
        for (var i = 0; i < rdata.length; i++) {
          flag = true;
          for (var j = 0; j < table_data.length; j++) {
            var con1 = site.edit.get_list_equal(table_data[j].redirectdomain, rdata[i].name);
            var con2 = !site.edit.get_list_equal(obj.redirectdomain, rdata[i].name);
            if (con1 && con2) {
              flag = false;
              break;
            }
          }
          if (flag) {
            select_list.push(rdata[i]);
            var selected = site.edit.get_list_equal(obj.redirectdomain, rdata[i].name);
            domain_html += '<li ' + (selected ? 'class="selected"' : '') + '><a><span class="text">' + rdata[i].name + '</span><span class="glyphicon glyphicon-ok check-mark"></span></a></li>';
          }
        }
        var content = '\
                    <form id="form_redirect" class="divtable pd20" style="padding-bottom:80px;">\
                        <div class="line" style="overflow: hidden; height: 40px;">\
                            <span class="tname">开启重定向</span>\
                            <div class="info-r ml0 mt5">\
                                <input class="btswitch btswitch-ios" id="type" type="checkbox" name="type"' + (obj.type == 1 ? ' checked' : '') + '/>\
                                <label class="btswitch-btn phpmyadmin-btn" for="type" style="float: left;"></label>\
                                <div style="display: inline-block; ">\
                                    <span class="tname" style="margin-left: 10px; position: relative; top: -5px;">保留URI参数</span>\
                                    <input class="btswitch btswitch-ios" id="holdpath" type="checkbox" name="holdpath"' + (obj.holdpath == 1 ? ' checked' : '') + '/>\
                                    <label class="btswitch-btn phpmyadmin-btn" for="holdpath" style="float: left;"></label>\
                                </div>\
                            </div>\
                        </div>\
                        <div class="line" style="clear: both; display: none;">\
                            <span class="tname">重定向名称</span>\
                            <div class="info-r ml0">\
                                <input type="text" name="redirectname" class="bt-input-text mr5" ' + (types ? '' : 'disabled="disabled"') + 'style="width: 300px;" value="' + obj.redirectname + '">\
                            </div>\
                        </div>\
                        <div class="line" style="clear: both;">\
                            <span class="tname">重定向类型</span>\
                            <div class="info-r ml0">\
                                <select class="bt-input-text mr5" name="domainorpath" style="width: 100px;">\
                                    <option value="domain"' + (obj.domainorpath == 'domain' ? ' selected' : '') + '>域名</option>\
                                    <option value="path"' + (obj.domainorpath == 'path' ? ' selected' : '') + '>路径</option>\
                                </select>\
                                <span class="mlr15">重定向方式</span>\
                                <select class="bt-input-text ml10" name="redirecttype" style="width: 100px;">\
                                    <option value="301"' + (obj.redirecttype == '301' ? ' selected' : '') + '>301</option>\
                                    <option value="302"' + (obj.redirecttype == '302' ? ' selected' : '') + '>302</option>\
                                </select>\
                            </div>\
                        </div>\
                        <div class="line redirectdomain" style="display: ' + (obj.domainorpath == 'domain' ? 'block' : 'none') + '">\
                            <span class="tname">重定向域名</span>\
                            <div class="info-r ml0">\
                                <div class="btn-group bootstrap-select show-tick mr5 redirect_domain" style="float: left">\
                                    <button type="button" class="btn dropdown-toggle btn-default" style="height: 32px; line-height: 18px; font-size: 12px">\
                                        <span class="filter-option pull-left"></span>\
                                        <span class="bs-caret"><span class="caret"></span></span>\
                                    </button>\
                                    <div class="dropdown-menu open">\
                                        <div class="bs-actionsbox">\
                                            <div class="btn-group btn-group-sm btn-block">\
                                                <button type="button" class="actions-btn bs-select-all btn btn-default">全选</button>\
                                                <button type="button" class="actions-btn bs-deselect-all btn btn-default">取消全选</button>\
                                            </div>\
                                        </div>\
                                        <div class="dropdown-menu inner">' + domain_html + '</div>\
                                    </div>\
                                </div>\
                                <span class="tname" style="width: 90px;">目标URL</span>\
                                <input class="bt-input-text mr5" name="tourl" type="text" style="width: 200px;" value="' + obj.tourl + '">\
                            </div>\
                        </div>\
                        <div class="line redirectpath" style="display: ' + (obj.domainorpath == 'path' ? 'block' : 'none') + '">\
                            <span class="tname">重定向路径</span>\
                            <div class="info-r ml0">\
                                <input class="bt-input-text mr5" name="redirectpath" type="text" style="width: 200px; float: left; margin-right: 0;" value="' + obj.redirectpath + '">\
                                <span class="tname" style="width: 90px;">目标URL</span>\
                                <input class="bt-input-text mr5" name="tourl1" type="text" style="width: 200px;" value="' + obj.tourl + '">\
                            </div>\
                        </div>\
                        <ul class="help-info-text c7">' + bt.render_help(helps) + '</ul>\
                        <div class="bt-form-submit-btn">\
                            <button type="button" class="btn btn-sm btn-danger btn-colse-prosy">关闭</button>\
                            <button type="button" class="btn btn-sm btn-success btn-submit-redirect">' + (types ? " 提交" : "保存") + '</button>\
                        </div>\
                    </form>\
                ';
        var form_redirect = bt.open({
          type: 1,
          skin: 'demo-class',
          area: '650px',
          title: types ? '创建重定向' : '修改重定向[' + obj.redirectname + ']',
          closeBtn: 2,
          shift: 5,
          shadeClose: false,
          content: content
        });
        setTimeout(function () {
          var redirectdomain = obj.redirectdomain;
          var show_domain_name = function () {
            var text = '';
            if (redirectdomain.length > 0) {
              text = [];
              for (var i = 0; i < redirectdomain.length; i++) {
                text.push(redirectdomain[i]);
              }
              text = text.join(', ');
            } else {
              text = '请选择站点...';
            }
            $('.redirect_domain .btn .filter-option').text(text);
          };
          show_domain_name();
          $('.redirect_domain .btn').click(function (e) {
            var $parent = $(this).parent();
            $parent.toggleClass('open');
            $(document).one('click', function () {
              $parent.removeClass('open');
            });
            e.stopPropagation();
          });
          // 单选
          $('.redirect_domain .dropdown-menu li').click(function (e) {
            var $this = $(this);
            var index = $this.index();
            var name = select_list[index].name;
            $this.toggleClass('selected');
            if ($this.hasClass('selected')) {
              redirectdomain.push(name);
            } else {
              var remove_index = -1;
              for (var i = 0; i < redirectdomain.length; i++) {
                if (redirectdomain[i] == name) {
                  remove_index = i;
                  break;
                }
              }
              if (remove_index != -1) {
                redirectdomain.splice(remove_index, 1);
              }
            }
            show_domain_name();
            e.stopPropagation();
          });
          // 全选
          $('.redirect_domain .bs-select-all').click(function () {
            redirectdomain = [];
            for (var i = 0; i < select_list.length; i++) {
              redirectdomain.push(select_list[i].name);
            }
            $('.redirect_domain .dropdown-menu li').addClass('selected');
            show_domain_name();
          });
          // 取消全选
          $('.redirect_domain .bs-deselect-all').click(function () {
            redirectdomain = [];
            $('.redirect_domain .dropdown-menu li').removeClass('selected');
            show_domain_name();
          });
          $('#form_redirect').parent().css('overflow', 'inherit');
          $('[name="domainorpath"]').change(function () {
            if ($(this).val() == 'path') {
              $('.redirectpath').show();
              $('.redirectdomain').hide();
              $('.redirect_domain .bs-deselect-all').click();
            } else {
              $('.redirectpath').hide();
              $('.redirectdomain').show();
              $('[name="redirectpath"]').val('')
            }
          });
          $('.btn-colse-prosy').click(function () {
            form_redirect.close();
          });
          $('.btn-submit-redirect').click(function () {
            var type = $('[name="type"]').prop('checked') ? 1 : 0;
            var holdpath = $('[name="holdpath"]').prop('checked') ? 1 : 0;
            var redirectname = $('[name="redirectname"]').val();
            var redirecttype = $('[name="redirecttype"]').val();
            var domainorpath = $('[name="domainorpath"]').val();
            var redirectpath = $('[name="redirectpath"]').val();
            var tourl = $(domainorpath == 'path' ? '[name="tourl1"]' : '[name="tourl"]').val();
            var redirectdomain_val = JSON.stringify(redirectdomain);
            if (!types) {
              bt.site.modify_redirect({
                type: type,
                sitename: sitename,
                holdpath: holdpath,
                redirectname: redirectname,
                redirecttype: redirecttype,
                domainorpath: domainorpath,
                redirectpath: redirectpath,
                redirectdomain: redirectdomain_val,
                tourl: tourl
              }, function (rdata) {
                if (rdata.status) {
                  form_redirect.close();
                  site.reload(11);
                }
                bt.msg(rdata);
              });
            } else {
              bt.site.create_redirect({
                type: type,
                sitename: sitename,
                holdpath: holdpath,
                redirectname: redirectname,
                redirecttype: redirecttype,
                domainorpath: domainorpath,
                redirectpath: redirectpath,
                redirectdomain: redirectdomain_val,
                tourl: tourl
              }, function (rdata) {
                if (rdata.status) {
                  form_redirect.close();
                  site.reload(11);
                }
                bt.msg(rdata);
              });
            }
          });
        }, 100);
      });
    },
    get_list_equal: function (list, name) {
      var result = false;
      for (var i = 0; i < list.length; i++) {
        if (list[i] == name) {
          result = true;
          break;
        }
      }
      return result;
    },
    template_Dir: function (id, type, obj) {
      if (type) {
        obj = { "name": "", "sitedir": "", "username": "", "password": "" };
      } else {
        obj = { "name": obj.name, "sitedir": obj.site_dir, "username": "", "password": "" };
      }
      var form_directory = bt.open({
        type: 1,
        skin: 'demo-class',
        area: '440px',
        title: type ? '添加加密访问' : '修改加密访问',
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: "<form id='form_dir' class='divtable pd15' style='padding-bottom: 60px;'>" +
          "<div class='line'>" +
          "<span class='tname'>名称</span>" +
          "<div class='info-r ml0'><input name='dir_name' class='bt-input-text mr10' type='text' style='width:270px' value='" + obj.name + "'>" +
          "</div></div>" +
          "<div class='line'>" +
          "<span class='tname'>加密访问</span>" +
          "<div class='info-r ml0'><input name='dir_sitedir' placeholder='输入需要加密访问的目录，如：/text/' class='bt-input-text mr10' type='text' style='width:270px' value='" + obj.sitedir + "'>" +
          "</div></div>" +
          "<div class='line'>" +
          "<span class='tname'>用户名</span>" +
          "<div class='info-r ml0'><input name='dir_username' AUTOCOMPLETE='off' class='bt-input-text mr10' type='text' style='width:270px' value='" + obj.username + "'>" +
          "</div></div>" +
          "<div class='line'>" +
          "<span class='tname'>密码</span>" +
          "<div class='info-r ml0'><input name='dir_password' AUTOCOMPLETE='off' class='bt-input-text mr10' type='password' style='width:270px' value='" + obj.password + "'>" +
          "</div></div>" +
          "<ul class='help-info-text c7 plr20'>" +
          "<li>目录设置加密访问后，访问时需要输入账号密码才能访问</li>" +
          "<li>例如我设置了加密访问 /test/ ,那我访问 http://aaa.com/test/ 是就要输入账号密码才能访问</li>" +
          "</ul>" +
          "<div class='bt-form-submit-btn'><button type='button' class='btn btn-sm btn-danger btn-colse-guard'>关闭</button><button type='button' class='btn btn-sm btn-success btn-submit-guard'>" + (type ? '提交' : '保存') + "</button></div></form>"
      });
      $('.btn-colse-guard').click(function () {
        form_directory.close();
      });
      $('.btn-submit-guard').click(function () {
        var guardData = {};
        guardData['id'] = id;
        guardData['name'] = $('input[name="dir_name"]').val();
        guardData['site_dir'] = $('input[name="dir_sitedir"]').val();
        guardData['username'] = $('input[name="dir_username"]').val();
        guardData['password'] = $('input[name="dir_password"]').val();
        if (guardData['name'] == "") {
          return layer.msg('名称不能为空', { icon: 2 });
        }
        if (guardData['site_dir'] == "") {
          return layer.msg('加密访问不能为空', { icon: 2 });
        }
        if (guardData['username'] == "") {
          return layer.msg('用户名不能为空', { icon: 2 });
        }
        if (guardData['password'] == "") {
          return layer.msg('密码不能为空', { icon: 2 });
        }
        if (type) {
          bt.site.create_dir_guard(guardData, function (rdata) {
            if (rdata.status) {
              form_directory.close();
              site.reload()
            }
            bt.msg(rdata);
          });
        } else {
          bt.site.edit_dir_account(guardData, function (rdata) {
            if (rdata.status) {
              form_directory.close();
              site.reload()
            }
            bt.msg(rdata);
          });
        }
      });
      setTimeout(function () {
        if (!type) {
          $('input[name="dir_name"]').attr('disabled', 'disabled');
          $('input[name="dir_sitedir"]').attr('disabled', 'disabled');
        }
      }, 500)

    },
    template_php: function (website, obj) {
      var _type = 'add',
        _name = '',
        _bggrey = '';
      if (obj == undefined) {
        obj = { "name": "", "suffix": "php|jsp", "dir": "" };
      } else {
        obj = { "name": obj.name, "suffix": obj.suffix, "dir": obj.dir };
        _type = 'edit';
        _name = ' readonly';
        _bggrey = 'background: #eee;'
      }
      var form_directory = bt.open({
        type: 1,
        area: '440px',
        title: '添加禁止访问',
        closeBtn: 2,
        btn: ['保存', '取消'],
        content: "<form class='mt10 php_deny'>" +
          "<div class='line'>" +
          "<span class='tname' style='width: 100px;'>名称</span>" +
          "<div class='info-r ml0' style='margin-left: 100px;'><input name='deny_name' placeholder='规则名称' " + _name + " class='bt-input-text mr10' type='text' style='width:270px;" + _bggrey + "' value='" + obj.name + "'>" +
          "</div></div>" +
          "<div class='line'>" +
          "<span class='tname' style='width: 100px;'>后缀</span>" +
          "<div class='info-r ml0' style='margin-left: 100px;'><input name='suffix' placeholder='禁止访问的后缀' class='bt-input-text mr10' type='text' style='width:270px' value='" + obj.suffix + "'>" +
          "</div></div>" +
          "<div class='line'>" +
          "<span class='tname' style='width: 100px;'>目录</span>" +
          "<div class='info-r ml0' style='margin-left: 100px;'><input name='dir' placeholder='禁止访问的目录' class='bt-input-text mr10' type='text' style='width:270px' value='" + obj.dir + "'>" +
          "</div></div></form>" +
          "<ul class='help-info-text c7' style='padding-left:40px;margin-bottom: 20px;'>" +
          "<li>后缀：禁止访问的文件后缀</li>" +
          "<li>目录：规则会在这个目录内生效</li>" +
          "</ul>",
        yes: function () {
          var dent_data = $('.php_deny').serializeObject();
          dent_data.act = _type;
          dent_data.website = website;
          var loading = bt.load();
          bt.send('set_php_deny', 'config/set_file_deny', dent_data, function (rdata) {
            loading.close();
            if (rdata.status) {
              form_directory.close();
              site.reload();
              $("#set_dirguard .tab-nav span:eq(1)").click();
            }
            bt.msg(rdata);
          });
        }
      });
    },
    set_301_old: function (web) {
      bt.site.get_domains(web.id, function (rdata) {
        var domains = [{ title: '整站', value: 'all' }];
        for (var i = 0; i < rdata.length; i++) domains.push({ title: rdata[i].name, value: rdata[i].name });
        bt.site.get_site_301(web.name, function (pdata) {
          var _val = pdata.src == '' ? 'all' : pdata.src
          var datas = [
            { title: '访问域名', width: '360px', name: 'domains', value: _val, disabled: pdata.status, type: 'select', items: domains },
            { title: '目标URL', width: '360px', name: 'toUrl', value: pdata.url },
            {
              title: ' ',
              text: '启用301',
              value: pdata.status,
              name: 'status',
              class: 'label-input-group',
              type: 'checkbox',
              callback: function (sdata) {
                bt.site.set_site_301(web.name, sdata.domains, sdata.toUrl, sdata.status ? '1' : '0', function (ret) {
                  if (ret.status) site.reload(10)
                  bt.msg(ret);
                })
              }
            },
          ]
          var robj = $('#webedit-con');
          for (var i = 0; i < datas.length; i++) {
            var _form_data = bt.render_form_line(datas[i]);
            robj.append(_form_data.html);
            bt.render_clicks(_form_data.clicks);
          }
          robj.append(bt.render_help(['选择[整站]时请不要将目标URL设为同一站点下的域名.', '取消301重定向后，需清空浏览器缓存才能看到生效结果.']));
        })
      })
    },
    set_301: function (web) {
      $('#webedit-con').html('<div id="redirect_list"></div>');
      site.edit.redirect_table = bt_tools.table({
        el: '#redirect_list',
        url: '/site?action=GetRedirectList',
        param: { sitename: web.name },
        dataFilter: function (res) {
          return { data: res };
        },
        column: [
          { type: 'checkbox', width: 20 },
          {
            fid: 'sitename',
            title: '重定向类型',
            type: 'text',
            template: function (row) {
              if (row.domainorpath == 'path') {
                conter = row.redirectpath;
              } else {
                conter = row.redirectdomain ? row.redirectdomain.join('、') : '空'
              }
              return '<span style="width:100px;" title="' + conter + '">' + conter + '</span>';
            }
          },
          { fid: 'redirecttype', title: '重定向方式', type: 'text' },
          {
            fid: 'holdpath',
            title: '保留URL参数',
            config: {
              icon: false,
              list: [
                [1, '开启', 'bt_success'],
                [0, '关闭', 'bt_danger']
              ]
            },
            type: 'status',
            event: function (row, index, ev, key, that) {
              row.holdpath = !row.holdpath ? 1 : 0;
              row.redirectdomain = JSON.stringify(row['redirectdomain']);
              bt.site.modify_redirect(row, function (res) {
                row.redirectdomain = JSON.parse(row['redirectdomain']);
                that.$modify_row_data({ holdpath: row.holdpath });
                bt.msg(res);
              });
            }
          },
          {
            fid: 'type',
            title: '状态',
            config: {
              icon: true,
              list: [
                [1, '运行中', 'bt_success', 'glyphicon-play'],
                [0, '已停止', 'bt_danger', 'glyphicon-pause']
              ]
            },
            type: 'status',
            event: function (row, index, ev, key, that) {
              row.type = !row.type ? 1 : 0;
              row.redirectdomain = JSON.stringify(row['redirectdomain']);
              bt.site.modify_redirect(row, function (res) {
                row.redirectdomain = JSON.parse(row['redirectdomain']);
                that.$modify_row_data({ holdpath: row.type });
                bt.msg(res);
              });
            }
          }, {
            title: '操作',
            width: 150,
            type: 'group',
            align: 'right',
            group: [{
              title: '配置文件',
              event: function (row, index, ev, key, that) {
                bt.site.get_redirect_config({
                  sitename: web.name,
                  redirectname: row.redirectname,
                  webserver: bt.get_cookie('serverType')
                }, function (rdata) {
                  if (typeof rdata == 'object' && rdata.constructor == Array) {
                    if (!rdata[0].status) bt.msg(rdata)
                  } else {
                    if (!rdata.status) bt.msg(rdata)
                  }
                  var datas = [
                    { items: [{ name: 'redirect_configs', type: 'textarea', value: rdata[0].data, widht: '340px', height: '200px' }] },
                    {
                      name: 'btn_config_submit',
                      text: '保存',
                      type: 'button',
                      callback: function (ddata) {
                        bt.site.save_redirect_config({ path: rdata[1], data: editor.getValue(), encoding: rdata[0].encoding }, function (ret) {
                          if (ret.status) {
                            site.reload(11);
                            redirect_config.close();
                          }
                          bt.msg(ret);
                        })
                      }
                    }
                  ]
                  redirect_config = bt.open({
                    type: 1,
                    area: ['550px', '550px'],
                    title: '编辑配置文件[' + row.redirectname + ']',
                    closeBtn: 2,
                    shift: 0,
                    content: "<div class='bt-form'><div id='redirect_config_con' class='pd15'></div></div>"
                  })
                  var robj = $('#redirect_config_con');
                  for (var i = 0; i < datas.length; i++) {
                    var _form_data = bt.render_form_line(datas[i]);
                    robj.append(_form_data.html);
                    bt.render_clicks(_form_data.clicks);
                  }
                  robj.append(bt.render_help(['此处为该负载均衡的配置文件，若您不了解配置规则,请勿随意修改。']));
                  $('textarea.redirect_configs').attr('id', 'configBody');
                  var editor = CodeMirror.fromTextArea(document.getElementById("configBody"), {
                    extraKeys: { "Ctrl-Space": "autocomplete" },
                    lineNumbers: true,
                    matchBrackets: true
                  });
                  $(".CodeMirror-scroll").css({ "height": "350px", "margin": 0, "padding": 0 });
                  setTimeout(function () {
                    editor.refresh();
                  }, 250);
                });
              }
            }, {
              title: '编辑',
              event: function (row, index, ev, key, that) {
                site.edit.templet_301(web.name, web.id, false, row);
              }
            }, {
              title: '删除',
              event: function (row, index, ev, key, that) {
                bt.site.remove_redirect(web.name, row.redirectname, function (rdata) {
                  bt.msg(rdata);
                  if (rdata.status) that.$delete_table_row(index);
                });
              }
            }]
          }
        ],
        tootls: [{ //按钮组
          type: 'group',
          positon: ['left', 'top'],
          list: [{
            title: '添加重定向',
            active: true,
            event: function (ev) {
              site.edit.templet_301(web.name, web.id, true);
            }
          }]
        }, { //批量操作
          type: 'batch',
          positon: ['left', 'bottom'],
          config: {
            title: '删除',
            url: '/site?action=del_redirect_multiple',
            param: { site_id: web.id },
            paramId: 'redirectname',
            paramName: 'redirectnames',
            theadName: '重定向名称',
            confirmVerify: false, // 是否提示验证方式
            refresh: true
          }
        }]
      });
    },
    templet_proxy: function (sitename, type, obj) {
      if (type) {
        obj = { "type": 1, "cache": 0, "proxyname": "", "proxydir": "/", "proxysite": "http://", "cachetime": 1, "todomain": "$host", "subfilter": [{ "sub1": "", "sub2": "" }] };
      }
      var sub_conter = '';
      for (var i = 0; i < obj.subfilter.length; i++) {
        if (i == 0 || obj.subfilter[i]['sub1'] != '') {
          sub_conter += "<div class='sub-groud'>" +
            "<input name='rep" + ((i + 1) * 2 - 1) + "' class='bt-input-text mr10' placeholder='被替换的文本,可留空' type='text' style='width:200px' value='" + obj.subfilter[i]['sub1'] + "'>" +
            "<input name='rep" + ((i + 1) * 2) + "' class='bt-input-text ml10' placeholder='替换为,可留空' type='text' style='width:200px' value='" + obj.subfilter[i]['sub2'] + "'>" +
            "<a href='javascript:;' class='proxy_del_sub' style='color:red;'>删除</a>" +
            "</div>";
        }
        if (i == 2) $('.add-replace-prosy').attr('disabled', 'disabled')
      }
      var helps = [
        '代理目录：访问这个目录时将会把目标URL的内容返回并显示(需要开启高级功能)',
        '目标URL：可以填写你需要代理的站点，目标URL必须为可正常访问的URL，否则将返回错误',
        '发送域名：将域名添加到请求头传递到代理服务器，默认为目标URL域名，若设置不当可能导致代理无法正常运行',
        '内容替换：只能在使用nginx时提供，最多可以添加3条替换内容,如果不需要替换请留空'
      ];
      var form_proxy = bt.open({
        type: 1,
        skin: 'demo-class',
        area: '650px',
        title: type ? '创建反向代理' : '修改反向代理[' + obj.proxyname + ']',
        closeBtn: 2,
        shift: 5,
        shadeClose: false,
        content: "<form id='form_proxy' class='divtable pd15' style='padding-bottom: 60px'>" +
          "<div class='line' style='overflow:hidden'>" +
          "<span class='tname' style='position: relative;top: -5px;'>开启代理</span>" +
          "<div class='info-r  ml0 mt5' >" +
          "<input class='btswitch btswitch-ios' id='openVpn' type='checkbox' name='type' " + (obj.type == 1 ? 'checked="checked"' : '') + "><label class='btswitch-btn phpmyadmin-btn' for='openVpn' style='float:left'></label>" +
          "<div style='display:" + (bt.get_cookie('serverType') == 'nginx' ? ' inline-block' : 'none') + "'>" +
          "<span class='tname' style='margin-left:15px;position: relative;top: -5px;'>开启缓存</span>" +
          "<input class='btswitch btswitch-ios' id='openNginx' type='checkbox' name='cache' " + (obj.cache == 1 ? 'checked="checked"' : '') + "'><label class='btswitch-btn phpmyadmin-btn' for='openNginx'></label>" +
          "</div>" +
          "<div style='display: inline-block;'>" +
          "<span class='tname' style='margin-left:10px;position: relative;top: -5px;'>高级功能</span>" +
          "<input class='btswitch btswitch-ios' id='openAdvanced' type='checkbox' name='advanced' " + (obj.advanced == 1 ? 'checked="checked"' : '') + "'><label class='btswitch-btn phpmyadmin-btn' for='openAdvanced'></label>" +
          "</div>" +
          "</div>" +
          "</div>" +
          "<div class='line' style='clear:both;'>" +
          "<span class='tname'>代理名称</span>" +
          "<div class='info-r  ml0'><input name='proxyname'" + (type ? "" : "readonly='readonly'") + " class='bt-input-text mr5 " + (type ? "" : " disabled") + "' type='text' style='width:200px' value='" + obj.proxyname + "'></div>" +
          "</div>" +
          "<div class='line cachetime' style='display:" + (obj.cache == 1 ? 'block' : 'none') + "'>" +
          "<span class='tname'>缓存时间</span>" +
          "<div class='info-r  ml0'><input name='cachetime'class='bt-input-text mr5' type='text' style='width:200px' value='" + obj.cachetime + "'>分钟</div>" +
          "</div>" +
          "<div class='line advanced'  style='display:" + (obj.advanced == 1 ? 'block' : 'none') + "'>" +
          "<span class='tname'>代理目录</span>" +
          "<div class='info-r  ml0'><input id='proxydir' name='proxydir' class='bt-input-text mr5' type='text' style='width:200px' value='" + obj.proxydir + "'>" +
          "</div>" +
          "</div>" +
          "<div class='line'>" +
          "<span class='tname'>目标URL</span>" +
          "<div class='info-r  ml0'>" +
          "<input name='proxysite' class='bt-input-text mr10' type='text' style='width:200px' value='" + obj.proxysite + "'>" +
          "<span class='mlr15'>发送域名</span><input name='todomain' class='bt-input-text ml10' type='text' style='width:200px' value='" + obj.todomain + "'>" +
          "</div>" +
          "</div>" +
          "<div class='line replace_conter' style='display:" + (bt.get_cookie('serverType') == 'nginx' ? 'block' : 'none') + "'>" +
          "<span class='tname'>内容替换</span>" +
          "<div class='info-r  ml0 '>" + sub_conter + "</div>" +
          "</div>" +
          "<div class='line' style='display:" + (bt.get_cookie('serverType') == 'nginx' ? 'block' : 'none') + "'>" +
          "<div class='info-r  ml0'>" +
          "<button class='btn btn-success btn-sm btn-title add-replace-prosy' type='button'><span class='glyphicon cursor glyphicon-plus  mr5' ></span>添加内容替换</button>" +
          "</div>" +
          "</div>" +
          "<ul class='help-info-text c7'>" + bt.render_help(helps) +
          "<div class='bt-form-submit-btn'><button type='button' class='btn btn-sm btn-danger btn-colse-prosy'>关闭</button><button type='button' class='btn btn-sm btn-success btn-submit-prosy'>" + (type ? " 提交" : "保存") + "</button></div>" +
          "</form>"
      });
      bt.set_cookie('form_proxy', form_proxy);
      $('.add-replace-prosy').click(function () {
        var length = $(".replace_conter .sub-groud").length;
        if (length == 2) $(this).attr('disabled', 'disabled')
        var conter = "<div class='sub-groud'>" +
          "<input name='rep" + (length * 2 + 1) + "' class='bt-input-text mr10' placeholder='被替换的文本,可留空' type='text' style='width:200px' value=''>" +
          "<input name='rep" + (length * 2 + 2) + "' class='bt-input-text ml10' placeholder='替换为,可留空' type='text' style='width:200px' value=''>" +
          "<a href='javascript:;' class='proxy_del_sub' style='color:red;'>删除</a>" +
          "</div>"
        $(".replace_conter .info-r").append(conter);
      });
      $('[name="proxysite"]').keyup(function () {
        var val = $(this).val(),
          ip_reg = /^(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])\.(\d{1,2}|1\d\d|2[0-4]\d|25[0-5])$/;
        val = val.replace(/^http[s]?:\/\//, '');
        // val = val.replace(/:([0-9]*)$/, '');
        val = val.replace(/(:|\?|\/|\\)(.*)$/, '');
        if (ip_reg.test(val)) {
          $("[name='todomain']").val('$host');
        } else {
          $("[name='todomain']").val(val);
        }
      });
      $('#openAdvanced').click(function () {
        if ($(this).prop('checked')) {
          $('.advanced').show();
        } else {
          $('.advanced').hide();
        }
      });
      $('#openNginx').click(function () {
        if ($(this).prop('checked')) {
          $('.cachetime').show();
        } else {
          $('.cachetime').hide();
        }
      });
      $('.btn-colse-prosy').click(function () {
        form_proxy.close();
      });
      $('.replace_conter').on('click', '.proxy_del_sub', function () {
        $(this).parent().remove();
        $('.add-replace-prosy').removeAttr('disabled')
      });
      $(".btn-submit-prosy").click(function () {
        var form_proxy_data = {};
        $.each($('#form_proxy').serializeArray(), function () {
          if (form_proxy_data[this.name]) {
            if (!form_proxy_data[this.name].push) {
              form_proxy_data[this.name] = [form_proxy_data[this.name]];
            }
            form_proxy_data[this.name].push(this.value || '');
          } else {
            form_proxy_data[this.name] = this.value || '';
          }
        });
        form_proxy_data['type'] = (form_proxy_data['type'] == undefined ? 0 : 1);
        form_proxy_data['cache'] = (form_proxy_data['cache'] == undefined ? 0 : 1);
        form_proxy_data['advanced'] = (form_proxy_data['advanced'] == undefined ? 0 : 1);
        form_proxy_data['sitename'] = sitename;
        form_proxy_data['subfilter'] = JSON.stringify([
          { 'sub1': form_proxy_data['rep1'] || '', 'sub2': form_proxy_data['rep2'] || '' },
          { 'sub1': form_proxy_data['rep3'] || '', 'sub2': form_proxy_data['rep4'] || '' },
          { 'sub1': form_proxy_data['rep5'] || '', 'sub2': form_proxy_data['rep6'] || '' },
        ]);
        for (var i in form_proxy_data) {
          if (i.indexOf('rep') != -1) {
            delete form_proxy_data[i];
          }
        }
        if (type) {
          bt.site.create_proxy(form_proxy_data, function (rdata) {
            if (rdata.status) {
              form_proxy.close();
              site.reload(12);
            }
            bt.msg(rdata);
          });
        } else {
          bt.site.modify_proxy(form_proxy_data, function (rdata) {
            if (rdata.status) {
              form_proxy.close();
              site.reload(12);
            }
            bt.msg(rdata);
          });
        }
      });
    },
    set_proxy: function (web) {
      $('#webedit-con').html('<div id="proxy_list"></div>');
      String.prototype.myReplace = function (f, e) { //吧f替换成e
        var reg = new RegExp(f, "g"); //创建正则RegExp对象   
        return this.replace(reg, e);
      }
      bt_tools.table({
        el: '#proxy_list',
        url: '/site?action=GetProxyList',
        param: { sitename: web.name },
        dataFilter: function (res) {
          return { data: res };
        },
        column: [
          { type: 'checkbox', width: 20 },
          { fid: 'proxyname', title: '名称', type: 'text' },
          { fid: 'proxydir', title: '代理目录', type: 'text' },
          { fid: 'proxysite', title: '目标url', type: 'link', href: true },
          bt.get_cookie('serverType') == 'nginx' ? {
            fid: 'cache',
            title: '缓存',
            config: {
              icon: false,
              list: [
                [1, '已开启', 'bt_success'],
                [0, '已关闭', 'bt_danger']
              ]
            },
            type: 'status',
            event: function (row, index, ev, key, that) {
              row['cache'] = !row['cache'] ? 1 : 0;
              row['subfilter'] = JSON.stringify(row['subfilter']);
              bt.site.modify_proxy(row, function (rdata) {
                row['subfilter'] = JSON.parse(row['subfilter']);
                if (rdata.status) site.reload()
                bt.msg(rdata);
              });
            }
          } : {},
          {
            fid: 'type',
            title: '状态',
            config: {
              icon: true,
              list: [
                [1, '运行中', 'bt_success', 'glyphicon-play'],
                [0, '已暂停', 'bt_danger', 'glyphicon-pause']
              ]
            },
            type: 'status',
            event: function (row, index, ev, key, that) {
              row['type'] = !row['type'] ? 1 : 0;
              row['subfilter'] = JSON.stringify(row['subfilter']);
              bt.site.modify_proxy(row, function (rdata) {
                row['subfilter'] = JSON.parse(row['subfilter']);
                if (rdata.status) site.reload()
                bt.msg(rdata);
              });
            }
          },
          {
            title: '操作',
            width: 150,
            type: 'group',
            align: 'right',
            group: [{
              title: '配置文件',
              event: function (row, index, ev, key, that) {
                bt.site.get_proxy_config({
                  sitename: web.name,
                  proxyname: row.proxyname,
                  webserver: bt.get_cookie('serverType')
                }, function (rdata) {
                  if (typeof rdata == 'object' && rdata.constructor == Array) {
                    if (!rdata[0].status) bt.msg(rdata)
                  } else {
                    if (!rdata.status) bt.msg(rdata)
                  }
                  var datas = [
                    { items: [{ name: 'proxy_configs', type: 'textarea', value: rdata[0].data, widht: '340px', height: '200px' }] },
                    {
                      name: 'btn_config_submit',
                      text: '保存',
                      type: 'button',
                      callback: function (ddata) {
                        bt.site.save_proxy_config({ path: rdata[1], data: editor.getValue(), encoding: rdata[0].encoding }, function (ret) {
                          if (ret.status) {
                            site.reload(12);
                            proxy_config.close();
                          }
                          bt.msg(ret);
                        })
                      }
                    }
                  ]
                  proxy_config = bt.open({
                    type: 1,
                    area: ['550px', '550px'],
                    title: '编辑配置文件[' + row.proxyname + ']',
                    closeBtn: 2,
                    shift: 0,
                    content: "<div class='bt-form'><div id='proxy_config_con' class='pd15'></div></div>"
                  })
                  var robj = $('#proxy_config_con');
                  for (var i = 0; i < datas.length; i++) {
                    var _form_data = bt.render_form_line(datas[i]);
                    robj.append(_form_data.html);
                    bt.render_clicks(_form_data.clicks);
                  }
                  robj.append(bt.render_help(['此处为该负载均衡的配置文件，若您不了解配置规则,请勿随意修改。']));
                  $('textarea.proxy_configs').attr('id', 'configBody');
                  var editor = CodeMirror.fromTextArea(document.getElementById("configBody"), {
                    extraKeys: { "Ctrl-Space": "autocomplete" },
                    lineNumbers: true,
                    matchBrackets: true
                  });
                  $(".CodeMirror-scroll").css({ "height": "350px", "margin": 0, "padding": 0 });
                  setTimeout(function () {
                    editor.refresh();
                  }, 250);
                });
              }
            }, {
              title: '编辑',
              event: function (row, index, ev, key, that) {
                site.edit.templet_proxy(web.name, false, row);
              }
            }, {
              title: '删除',
              event: function (row, index, ev, key, that) {
                bt.site.remove_proxy(web.name, row.proxyname, function (rdata) {
                  if (rdata.status) that.$delete_table_row(index);
                })
              }
            }]
          }
        ],
        tootls: [{ //按钮组
          type: 'group',
          positon: ['left', 'top'],
          list: [{
            title: '添加反向代理',
            active: true,
            event: function (ev) {
              site.edit.templet_proxy(web.name, true)
            }
          }]
        }, { //批量操作
          type: 'batch',
          positon: ['left', 'bottom'],
          config: {
            title: '删除',
            url: '/site?action=del_proxy_multiple',
            param: { site_id: web.id },
            paramId: 'proxyname',
            paramName: 'proxynames',
            theadName: '反向代理名称',
            confirmVerify: false, // 是否提示验证方式
            refresh: true
          }
        }]
      });
    },
    set_security: function (web) {
      bt.site.get_site_security(web.id, web.name, function (rdata) {
        if (typeof rdata == 'object' && rdata.status === false && rdata.msg) {
          bt.msg(rdata);
          return;
        }
        var robj = $('#webedit-con');
        var datas = [
          { title: 'URL后缀', name: 'sec_fix', value: rdata.fix, disabled: rdata.status, width: '300px' },
          { title: '许可域名', type: "textarea", name: 'sec_domains', value: rdata.domains.replace(/,/g, "\n"), disabled: rdata.status, width: '300px', height: '210px' },
          { title: '响应资源', name: 'return_rule', value: rdata.return_rule, disabled: rdata.status, width: '300px' },
          {
            title: ' ',
            class: 'label-input-group',
            items: [{
              text: '启用防盗链',
              name: 'door_status',
              value: rdata.status,
              type: 'checkbox',
              callback: function (sdata) {
                if (sdata.sec_domains === '') {
                  $('#door_status').prop('checked', false)
                  bt.msg({
                    status: false,
                    msg: '许可域名不能为空！'
                  });
                  return false;
                }
                bt.site.set_site_security(web.id, web.name, sdata.sec_fix, sdata.sec_domains.split("\n").join(','), sdata.door_status, sdata.return_rule, function (ret) {
                  if (ret.status) site.reload(13)
                  bt.msg(ret);
                })
              }
            },
            {
              text: '允许空HTTP_REFERER请求',
              name: 'none',
              value: rdata.none,
              type: 'checkbox',
              callback: function (sdata) {
                bt.site.set_site_security(web.id, web.name, sdata.sec_fix, sdata.sec_domains.split("\n").join(','), '1', sdata.return_rule, function (ret) {
                  if (ret.status) site.reload(13)
                  bt.msg(ret);
                })
              }
            }
            ]
          }
        ]
        for (var i = 0; i < datas.length; i++) {
          var _form_data = bt.render_form_line(datas[i]);
          robj.append(_form_data.html);
          bt.render_clicks(_form_data.clicks);
        }
        var helps = [
          '【URL后缀】一般填写文件后缀，每行一个后缀,如: png',
          '【许可域名】允许作为来路的域名，每行一个域名,如: www.bt.cn',
          '【响应资源】可设置404/403等状态码，也可以设置一个有效资源，如：/security.png',
          '【允许空HTTP_REFERER请求】是否允许浏览器直接访问，若您的网站访问异常，可尝试开启此功能'
        ]
        robj.append(bt.render_help(helps));
      })
    },
    set_tomact: function (web) {
      bt.site.get_site_phpversion(web.name, function (rdata) {
        var robj = $('#webedit-con');
        if (!rdata.tomcatversion) {
          robj.html('<span>' + lan.site.tomcat_err_msg1 + '</span>');
          layer.msg(lan.site.tomcat_err_msg, { icon: 2 });
          return;
        }
        var data = {
          class: 'label-input-group',
          items: [{
            text: lan.site.enable_tomcat,
            name: 'tomcat',
            value: rdata.tomcat == -1 ? false : true,
            type: 'checkbox',
            callback: function (sdata) {
              bt.site.set_tomcat(web.name, function (ret) {
                if (ret.status) site.reload(9)
                bt.msg(ret);
              })
            }
          }]
        }
        var _form_data = bt.render_form_line(data);
        robj.append(_form_data.html);
        bt.render_clicks(_form_data.clicks);
        var helps = [lan.site.tomcat_help1 + ' ' + rdata.tomcatversion + ',' + lan.site.tomcat_help2, lan.site.tomcat_help3, lan.site.tomcat_help4, lan.site.tomcat_help5]
        robj.append(bt.render_help(helps));
      })
    },
    get_site_logs: function (web) {
      $('#webedit-con').append('<div id="tabLogs" class="tab-nav"></div><div class="tab-con" style="padding:10px 0px;"></div>')
      var _tab = [{
        title: "响应日志",
        on: true,
        callback: function (robj) {
          //   console.log(robj)
          bt.site.get_site_logs(web.name, function (rdata) {
            var logs = { class: 'bt-logs', items: [{ name: 'site_logs', height: '590px', value: rdata.msg, width: '100%', type: 'textarea' }] },
              _form_data = bt.render_form_line(logs);
            robj.append(_form_data.html);
            bt.render_clicks(_form_data.clicks);
            $('textarea[name="site_logs"]').attr('readonly', true)
            $('textarea[name="site_logs"]').scrollTop(100000000000)
          })
        }
      }, {
        title: "错误日志",
        callback: function (robj) {
          //   console.log(robj)
          bt.site.get_site_error_logs(web.name, function (rdata) {
            var logs = { class: 'bt-logs', items: [{ name: 'site_logs', height: '590px', value: rdata.msg, width: '100%', type: 'textarea' }] },
              _form_data = bt.render_form_line(logs);
            robj.append(_form_data.html);
            bt.render_clicks(_form_data.clicks);
            $('textarea[name="site_logs"]').attr('readonly', true)
            $('textarea[name="site_logs"]').scrollTop(100000000000)
          })
        }
      }]
      bt.render_tab('tabLogs', _tab);
      $('#tabLogs span:eq(0)').click();
    }
  },
  create_let: function (ddata, callback) {
    bt.site.create_let(ddata, function (ret) {
      if (ret.status) {
        if (callback) {
          callback(ret);
        } else {
          site.ssl.reload(1);
          bt.msg(ret);
          return;
        }
      } else {
        if (ret.msg) {
          if (typeof (ret.msg) == 'string') {
            ret.msg = [ret.msg, ""];
          }
        }
        if (!ret.out) {
          if (callback) {
            callback(ret);
            return;
          }
          bt.msg(ret);
          return;
        }
        var data = "<p>" + ret.msg + "</p><hr />"
        if (ret.err[0].length > 10) data += '<p style="color:red;">' + ret.err[0].replace(/\n/g, '<br>') + '</p>';
        if (ret.err[1].length > 10) data += '<p style="color:red;">' + ret.err[1].replace(/\n/g, '<br>') + '</p>';

        layer.msg(data, { icon: 2, area: '500px', time: 0, shade: 0.3, shadeClose: true });
      }
    })
  },
  reload: function (index) {
    if (index == undefined) index = 0

    var _sel = $('.site-menu p.bgw');
    if (_sel.length == 0) _sel = $('.site-menu p:eq(0)');
    _sel.trigger('click');
  },
  plugin_firewall: function () {
    var typename = bt.get_cookie('serverType');
    var name = 'btwaf_httpd';
    if (typename == "nginx") name = 'btwaf'

    bt.plugin.get_plugin_byhtml(name, function (rhtml) {
      if (rhtml.status === false) return;

      var list = rhtml.split('<script type="javascript/text">');
      if (list.length > 1) {
        rcode = rhtml.split('<script type="javascript/text">')[1].replace("<\/script>", "");
      } else {
        list = rhtml.split('<script type="text/javascript">');
        rcode = rhtml.split('<script type="text/javascript">')[1].replace("<\/script>", "");
      }
      rcss = rhtml.split('<style>')[1].split('</style>')[0];
      rcode = rcode.replace('    wafview()', '')
      $("body").append('<div style="display:none"><style>' + rcss + '</style><script type="javascript/text">' + rcode + '<\/script></div>');

      setTimeout(function () {
        if (!!(window.attachEvent && !window.opera)) {
          execScript(rcode);
        } else {
          window.eval(rcode);
        }
      }, 200)
    })

  },
  select_site_txt: function (box) {
    layer.open({
      type: 1,
      closeBtn: 2,
      title: '自定义域名',
      area: '600px',
      btn: ['确认', '取消'],
      content: '<div class="pd20"><div class="line "><span class="tname">自定义域名</span><div class="info-r "><input  name="site_name" placeholder="请输入需要申请证书的域名（单域名证书），必填项，例如：www.bt.cn" class="bt-input-text mr5 ssl_site_name_rc" type="text" style="width:400px" value=""></div></div>\
            <ul class="help-info-text c7">\
                    <li> 申请之前，请确保域名已解析，如未解析会导致审核失败(包括根域名)</li>\
                    <li>申请www.bt.cn这种以www为二级域名的证书，需绑定并解析顶级域名(bt.cn)，否则将验证失败</li>\
                    <li>SSL证书可选名称赠送规则：</li>\
                    <li>    1、申请根域名(如：bt.cn),赠送下一级为www的域名(如：www.bt.cn)</li>\
                    <li>    2、申请当前host为www的域名（如：www.bt.cn）,赠送上一级域名，(如: bt.cn)</li>\
                    <li>    3、申请其它二级域名，(如：app.bt.cn)，赠送下一级为www的域名 (如：www.app.bt.cn)</li>\
                </ul >\
            </div>',
      success: function () {

      },
      yes: function (layers, index) {
        layer.close(layers);
        $('#' + box).val($('.ssl_site_name_rc').val())
      }
    })
  },
  /**
   * @descripttion: 选择站点
   * @author: Lifu
   * @Date: 2020-08-14
   * @param {String} box 输出时所用ID
   * @return: 无返回值
   */
  select_site_list: function (box, code) {
    var _optArray = [],
      all_site_list = [];

    $.post('/data?action=getData', { tojs: 'site.get_list', table: 'domain', limit: 10000, search: '', p: 1, order: 'id desc', type: -1 }, function (res) {

      var _tbody = '';
      if (res.data.length > 0) {
        $.each(res.data, function (index, item) {
          _body = '<tr>' +
            '<td>' +
            '<div class="box-group" style="height:16px">' +
            '<div class="bt_checkbox_groups"></div>' +
            '</div>' +
            '</td>' +
            '<td><span class="overflow_style" style="width:210px">' + item['name'] + '</span></td>'

            +
            '</tr>'

          if (code.indexOf('wildcard') > -1) {
            if (item['name'].indexOf('*.') > -1) {
              all_site_list.push(item['name'])
              _tbody += _body;
            }
          } else {
            all_site_list.push(item['name'])
            _tbody += _body;
          }
        })
        if (all_site_list.length == 0) {
          _tbody = '<tr><td colspan="2">暂无数据</td></tr>'
        }
      } else {
        _tbody = '<tr><td colspan="2">暂无数据</td></tr>'
      }

      layer.open({
        type: 1,
        closeBtn: 2,
        title: '选择站点',
        area: '600px',
        btn: ['确认', '取消'],
        content: '<div class="pd20 dynamic_head_box"><div class="line"><input type="text" name="serach_site" class="bt-input-text" style="width: 560px;" placeholder="支持字段模糊搜索"></div>\
                <div class="bt-table dynamic_list_table">\
                    <div class="divtable" style="height:281px">\
                        <table class="table table-hover">\
                            <thead>\
                                <th width="30">\
                                    <div class="box-group" style="height:16px">\
                                        <div class="bt_checkbox_groups" data-key="0"></div>\
                                    </div>\
                                </th>\
                                <th>域名</th>\
                            </thead>\
                            <tbody class="dynamic_list">' + _tbody + '</tbody>\
                        </table>\
                    </div>\
                </div>\
                <ul class="help-info-text c7">\
                    <li> 申请之前，请确保域名已解析，如未解析会导致审核失败(包括根域名)</li>\
                    <li>申请www.bt.cn这种以www为二级域名的证书，需绑定并解析顶级域名(bt.cn)，否则将验证失败</li>\
                    <li>SSL证书可选名称赠送规则：</li>\
                    <li>    1、申请根域名(如：bt.cn),赠送下一级为www的域名(如：www.bt.cn)</li>\
                    <li>    2、申请当前host为www的域名（如：www.bt.cn）,赠送上一级域名，(如: bt.cn)</li>\
                    <li>    3、申请其它二级域名，(如：app.bt.cn)，赠送下一级为www的域名 (如：www.app.bt.cn)</li>\
                </ul >\
                </div> ',
        success: function () {

          // 固定表格头部
          if (jQuery.prototype.fixedThead) {
            $('.dynamic_list_table .divtable').fixedThead({ resize: false });
          } else {
            $('.dynamic_list_table .divtable').css({ 'overflow': 'auto' });
          }
          //检索输入
          $('input[name=serach_site]').on('input', function () {
            var _serach = $(this).val();
            if (_serach.trim() != '') {
              $('.dynamic_list tr').each(function () {
                var _td = $(this).find('td').eq(1).html()
                if (_td.indexOf(_serach) == -1) {
                  $(this).hide()
                } else {
                  $(this).show()
                }
              })
            } else {
              $('.dynamic_list tr').show()
            }
          })

          // 单选设置
          $('.dynamic_list').on('click', '.bt_checkbox_groups', function (e) {
            var _tr = $(this).parents('tr');
            if ($(this).hasClass('active')) {
              $(this).removeClass('active');

            } else {
              $('.dynamic_list .bt_checkbox_groups').removeClass('active');
              $(this).addClass('active');
              _optArray = [_tr.find('td').eq(1).text()]
            }
            e.preventDefault();
            e.stopPropagation();
          })
          // tr点击时
          $('.dynamic_list').on('click', 'tr', function (e) {
            $(this).find('.bt_checkbox_groups').click()
            e.preventDefault();
            e.stopPropagation();
          })
        },
        yes: function (layers, index) {
          var _olist = []
          if (_optArray.length > 0) {
            $.each(_optArray, function (index, item) {
              if ($.inArray(item, _olist) == -1) {
                _olist.push(item)
              }
            })
          }
          layer.close(layers);
          $('#' + box).val(_olist.join('\n'))
          $('textarea[name=lb_site]').focus();
        }
      });
    });
  },
  web_edit: function (obj) {
    var _this = this,
      item = obj;
    bt.open({
      type: 1,
      area: ['780px', '722px'],
      title: lan.site.website_change + '[' + item.name + ']  --  ' + lan.site.addtime + '[' + item.addtime + ']',
      closeBtn: 2,
      shift: 0,
      content: "<div class='bt-tabs'><div class='bt-w-menu site-menu pull-left' style='height: 100%;'></div><div id='webedit-con' class='bt-w-con webedit-con pd15'></div></div>"
    })
    setTimeout(function () {
      var webcache = bt.get_cookie('serverType') == 'openlitespeed' ? { title: 'LS-Cache', callback: site.edit.ols_cache } : '';
      var menus = [
        { title: '域名管理', callback: site.edit.set_domains },
        { title: '子目录绑定', callback: site.edit.set_dirbind },
        { title: '网站目录', callback: site.edit.set_dirpath },
        { title: '访问限制', callback: site.edit.set_dirguard },
        { title: '流量限制', callback: site.edit.limit_network },
        { title: '伪静态', callback: site.edit.get_rewrite_list },
        { title: '默认文档', callback: site.edit.set_default_index },
        { title: '配置文件', callback: site.edit.set_config },
        { title: 'SSL', callback: site.set_ssl },
        { title: 'PHP版本', callback: site.edit.set_php_version },
        { title: 'Composer', callback: site.edit.set_composer },
        { title: 'Tomcat', callback: site.edit.set_tomact },
        // { title: '重定向', callback: site.edit.set_301_old },
        { title: '重定向', callback: site.edit.set_301 },
        { title: '反向代理', callback: site.edit.set_proxy },
        { title: '防盗链', callback: site.edit.set_security },
        { title: '网站日志', callback: site.edit.get_site_logs },
        // { title: '错误日志', callback: site.edit.get_site_error_logs }
      ]
      if (webcache !== '') menus.splice(3, 0, webcache);
      for (var i = 0; i < menus.length; i++) {
        var men = menus[i];
        var _p = $('<p>' + men.title + '</p>');
        _p.data('callback', men.callback);
        $('.site-menu').append(_p);
      }
      $('.site-menu p').click(function () {
        $('#webedit-con').html('');
        $(this).addClass('bgw').siblings().removeClass('bgw');
        var callback = $(this).data('callback')
        if (callback) callback(item);
      })
      site.reload(0);
    }, 100)
  },
  set_ssl: function (web) {  //站点/项目名、放置位置

    $('#webedit-con').html("<div id='ssl_tabs'></div><div class=\"tab-con\" style=\"padding:10px 0;\"></div>");
    bt.site.get_site_ssl(web.name, function (rdata) {
      var _tabs = [{
        title: "商用证书<i class='ssl_recom_icon'></i>",
        on: true,
        callback: function (robj) {
          robj = $('#webedit-con .tab-con')
          bt.pub.get_user_info(function (udata) {
            if (udata.status) {
              var deploy_ssl_info = rdata,
                html = '',
                product_list, userInfo, order_list, is_check = true,
                itemData, activeData, loadY, pay_ssl_layer;
              bt.send('get_order_list', 'ssl/get_order_list', {}, function (rdata) {
                order_list = rdata;
                if (rdata.length == 0) {
                  $('#ssl_order_list tbody').html('<tr><td colspan="5" style="text-align:center;">暂无证书 <a class="btlink" href="javascript:$(\'.ssl_business_application\').click();"> ->申请证书</a></td></tr>');
                  return;
                }
                $.each(rdata, function (index, item) {
                  if (deploy_ssl_info.type == 3 && deploy_ssl_info.oid === item.oid) {
                    html += '<tr data-index="' + index + '">' +
                      '<td><span>' + item.domainName.join('、') + '</span></td><td>' + item.title + '</td><td>' + (function () {
                        var dayTime = new Date().getTime() / 1000,
                          color = '',
                          endTiems = '';
                        if (item.endDate != '') {
                          item.endDate = parseInt(item.endDate);
                          endTiems = parseInt((item.endDate - dayTime) / 86400);
                          if (endTiems <= 15) color = 'orange';
                          if (endTiems <= 7) color = 'red';
                          if (endTiems < 0) return '<span style="color:red">已过期</span>';
                          return '<span style="' + color + '">剩余' + endTiems + '天</span>';
                        } else {
                          return '--';
                        }
                      }()) +
                      '</td><td>订单完成</td><td style="text-align:right">已部署 | <a class="btlink" href="javascript:site.ssl.set_ssl_status(\'CloseSSLConf\',\'' + web.name + '\',2)">关闭</a></td></td>';
                  } else if (deploy_ssl_info.type != 3) {
                    html += '<tr data-index="' + index + '">' +
                      '<td><span>' + (item.domainName == null ? '--' : item.domainName.join('、')) + '</span></td><td>' + item.title + '</td><td>' + (function () {
                        var dayTime = new Date().getTime() / 1000,
                          color = '',
                          endTiems = '';
                        if (item.endDate != '') {
                          item.endDate = parseInt(item.endDate);
                          endTiems = parseInt((item.endDate - dayTime) / 86400);
                          if (endTiems <= 15) color = 'orange';
                          if (endTiems <= 7) color = 'red';
                          if (endTiems < 0) return '<span style="color:red">已过期</span>';
                          return '<span style="' + color + '">剩余' + endTiems + '天</span>'
                        } else {
                          return '--';
                        }
                      }()) +
                      '</td><td>' + (function () {
                        if (item.certId == '') {
                          return '<span style="color:orange;">待完善资料</span>';
                        } else if (item.status === 1) {
                          switch (item.orderStatus) {
                            case 'COMPLETE':
                              return '<span style="color:#20a53a;">订单完成</span>';
                              break;
                            case 'PENDING':
                              return '<span style="color: orange;">申请中</span>';
                              break;
                            case 'CANCELLED':
                              return '<span style="color: #888;">已取消</span>';
                              break;
                            case 'FAILED':
                              return '<span style="color:red;">申请失败</span>';
                              break;
                            default:
                              return '<span style="color: orange;">待验证</span>';
                              break;
                          }
                        } else {
                          switch (item.status) {
                            case 0:
                              return '<span style="color: orange;">未支付</span>';
                              break;
                            case -1:
                              return '<span style="color: #888;">已取消</span>'
                              break;
                          }
                        }
                      }()) +
                      '</td><td style="text-align:right;">' + (function () {
                        var html = '';
                        if (item.renew) html += '<a href="javascript:;" class="btlink options_ssl" data-type="renewal_ssl">续签证书</a>&nbsp;&nbsp;|&nbsp;&nbsp;';
                        if (item.certId == '') {
                          if (item.install) html += '<a href="' + item.qq + '" class="btlink options_ssl" target="_blank">人工服务</a>&nbsp;&nbsp;|&nbsp;&nbsp;';
                          html += '<a href="javascript:;" class="btlink options_ssl"  data-type="perfect_user_info">完善资料</a>';
                          return html;
                        } else if (item.status === 1) {
                          var html = '';
                          switch (item.orderStatus) {
                            case "COMPLETE": //申请成功
                              return '<a href="javascript:;" data-type="deploy_ssl" class="btlink options_ssl">部署</a>&nbsp;&nbsp;|&nbsp;&nbsp;<a href="/ssl?action=download_cert&oid=' + item.oid + '" data-type="download_ssl" class="btlink options_ssl">下载</a>'
                              break;
                            case "PENDING": //申请中
                              if (item.install) html += '<a href="' + item.qq + '" class="btlink options_ssl" target="_blank">人工服务</a>&nbsp;&nbsp;|&nbsp;&nbsp;';
                              html += '<a href="javascript:;" data-type="verify_order" class="btlink options_ssl">验证</a>';
                              return html;
                              break;
                            case "CANCELLED": //已取消
                              return '无操作';
                              break;
                            case "FAILED":
                              return '<a href="javascript:;" data-type="info_order" class="btlink options_ssl">详情</a>';
                              break;
                            default:
                              if (item.install) html += '<a href="' + item.qq + '" class="btlink options_ssl" target="_blank">人工服务</a>&nbsp;&nbsp;|&nbsp;&nbsp;';
                              html += '<a href="javascript:;" data-type="verify_order" class="btlink options_ssl">验证</a>';
                              return html;
                              break;
                          }
                        }
                      }()) + '</td>' +
                      '</tr>';
                  }
                });
                $('#ssl_order_list tbody').html(html);
              });
              robj.append('<div style="margin-bottom: 10px;" class="alert alert-success">此品牌证书适合生产项目使用，宝塔官网BT.CN也是用这款证书，性价比高，推荐使用</div>\
                                        <div class= "mtb10" >\
                                        <button class="btn btn-success btn-sm btn-title ssl_business_application" type="button">申请证书</button>\
                                        <span class="ml5"><a href="http://wpa.qq.com/msgrd?v=3&uin=2927440070&site=qq&menu=yes&from=message&isappinstalled=0" target="_blank" class="btlink"><img src="https://pub.idqqimg.com/qconn/wpa/button/button_old_41.gif" style="margin-right:5px;margin-left:3px;vertical-align: -1px;">售前客服: 2927440070</a></span>\
                                        <div class="divtable mtb10 ssl_order_list"  style="height: 290px;overflow-y: auto;">\
                                            <table class="table table-hover" id="ssl_order_list">\
                                                <thead><tr><th width="120px">域名</th><th  width="220px">证书类型</th><th>到期时间</th><th>状态</th><th style="text-align:right;">操作</th></tr></thead>\
                                                <tbody><tr><td colspan="5" style="text-align:center"><img src="/static/images/loading-2.gif" style="width:15px;vertical-align: middle;"><span class="ml5" style="vertical-align: middle;">正在获取证书列表，请稍候...</span></td></tr></tbody>\
                                            </table>\
                                        </div>\
                                    </div><ul class="help-info-text c7">\
                                        <li style="color:red;">证书支持购买多年，只能一年签发一次（有效期一年），需在到期前30天内续签(续签暂不需要验证域名)</li>\
                                        <li style="color:red;">注意：请勿将SSL证书用于非法网站，一经发现，吊销证书且不退款</li>\
                                        <li>申请之前，请确保域名已解析，如未解析会导致审核失败(包括根域名)</li>\
                                        <li>有效期1年，不支持续签，到期后需要重新申请</li>\
                                        <li>在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点</li>\
                                        <li><a style="color:red;">如果您的站点有使用CDN、高防IP、反向代理、301重定向等功能，可能导致验证失败</a></li>\
                                        <li><a style="color:red;">申请www.bt.cn这种以www为二级域名的证书，需绑定并解析顶级域名(bt.cn)，否则将验证失败</a></li>\
                                        <li><a style="color:red;">商用证书相对于普通证书，具有更高的安全性、赔付保障和支持通配符和多域名等方式。<a class="btlink" target="_blank" href="https://www.racent.com/sectigo-ssl">点击查看</a></a></li>\
                                    </ul>');
              bt.fixed_table('ssl_order_list');
              /**
               * @description 对指定表单元素的内容进行效验
               * @param {Object} el jqdom对象
               * @param {String} name 表单元素name名称
               * @param {*} value 表单元素的值
               * @returns 返回当前元素的值
               */
              function check_ssl_user_info (el, name, value, config) {
                el.css('borderColor', '#ccc');
                var status;
                switch (name) {
                  case 'domains':
                    value = bt.strim(value).replace(/\n*$/, '')
                    var list = value.split('\n');
                    if (value == '') {
                      set_info_tips(el, { msg: '域名不能为空！', color: 'red' });
                      status = false;
                    }
                    if (!Array.isArray(list)) list = [list];
                    $.each(list, function (index, item) {
                      if (bt.check_domain(item)) {
                        var type = item.indexOf(),
                          index = null;
                        if (config.code.indexOf('multi') > -1) index = 0;
                        if (config.code.indexOf('wildcard') > -1) index = 1;
                        if (config.code.indexOf('wildcard') > -1 && config.code.indexOf('multi') > -1) index = 2;
                        switch (index) {
                          case 0:
                            if (list.length > config.limit) {
                              set_info_tips(el, { msg: '多域名证书当前支持' + config.limit + '个域名，如需添加，请联系客服咨询！', color: 'red' });
                              status = false;
                            } else if (list.length == 1) {
                              set_info_tips(el, { msg: '当前为多域名证书(当前支持' + config.limit + '个域名)，至少需要2个域名或多个域名！', color: 'red' });
                              status = false;
                            }
                            break;
                          case 1:
                            if (item.indexOf('*') != 0) {
                              set_info_tips(el, { msg: '通配符域名格式错误,正确写法‘*.bt.cn’', color: 'red' });
                              status = false;
                            }
                            break;
                          case 2:
                            if (list.length > config.limit) {
                              set_info_tips(el, { msg: '多域名通配符证书支持' + config.limit + '个域名，如需添加，请联系客服咨询！！', color: 'red' });
                              status = false;
                            } else if (list.length == 1) {
                              set_info_tips(el, { msg: '当前为多域名通配符(当前支持' + config.limit + '个域名)，需要2个域名或多个域名！', color: 'red' });
                              status = false;
                            }
                            if (item.indexOf('*') != 0) {
                              set_info_tips(el, { msg: '通配符域名格式错误,正确写法‘*.bt.cn’', color: 'red' });
                              status = false;
                            }
                            break;
                        }
                      } else {
                        if (value != '') {
                          set_info_tips(el, { msg: '【 ' + item + ' 】' + ',域名格式错误！', color: 'red' });
                        } else {
                          set_info_tips(el, { msg: '域名不能为空！', color: 'red' });
                        }
                        status = false;
                      }
                    });
                    value = list;
                    break;
                  case 'state':
                    if (value == '') {
                      set_info_tips(el, { msg: '所在省份不能为空！', color: 'red' });
                      status = false;
                    }
                    break;
                  case 'city':
                    if (value == '') {
                      set_info_tips(el, { msg: '所在市/县不能为空！', color: 'red' });
                      status = false;
                    }
                    break;
                  case 'city':
                    if (value == '') {
                      set_info_tips(el, { msg: '所在市/县不能为空！', color: 'red' });
                      status = false;
                    }
                    break;
                  case 'organation':
                    if (value == '') {
                      set_info_tips(el, { msg: '公司名称不能为空，如为个人申请请输入个人姓名！', color: 'red' });
                      status = false;
                    }
                    break;
                  case 'address':
                    if (value == '') {
                      set_info_tips(el, { msg: '请输入公司详细地址，不可为空，具体要求见说明，', color: 'red' });
                      status = false;
                    }
                    break;
                  case 'name':
                    if (value == '') {
                      set_info_tips(el, { msg: '用户姓名不能为空！', color: 'red' });
                      status = false;
                    }
                    break;
                  case 'email':
                    if (value == '') {
                      set_info_tips(el, { msg: '用户邮箱地址不能为空！', color: 'red' });
                      status = false;
                    }
                    if (!bt.check_email(value)) {
                      set_info_tips(el, { msg: '用户邮箱地址格式错误！', color: 'red' });
                      status = false;
                    }
                    break;
                  case 'mobile':
                    if (value != '') {
                      if (!bt.check_phone(value)) {
                        set_info_tips(el, { msg: '用户手机号码格式错误！', color: 'red' });
                        status = false;
                      }
                    }
                    break;
                  default:
                    status = value;
                    break;
                }
                if (typeof status == "boolean" && status === false) return false;
                status = value;
                return status;
              }

              /**
               * @description 设置元素的提示和边框颜色
               * @param {Object} el jqdom对象
               * @param {Object} config  = {
               *  @param {String} config.msg 提示内容
               *  @param {String} config.color 提示颜色
               * }
               */
              function set_info_tips (el, config) {
                $('html').append($('<span id="width_test">' + config.msg + '</span>'));
                layer.tips(config.msg, el, { tips: [1, config.color], time: 3000 });
                el.css('borderColor', config.color);
                $('#width_test').remove();
              }
              /**
               * @description 更换域名验证方式
               * @param {Number} oid 域名订单ID
               * @returns void
               */
              function again_verify_veiw (oid, is_success) {
                var loads = bt.load('正在获取验证方式,请稍候...');
                bt.send('get_verify_result', 'ssl/get_verify_result', { oid: oid }, function (res) {
                  loads.close();
                  var type = res.data.dcvList[0].dcvMethod;
                  loadT = bt.open({
                    type: 1,
                    title: '验证域名-' + (type ? '文件验证' : 'DNS验证'),
                    area: '520px',
                    btn: ['更改', '取消'],
                    content: '<div class="bt-form pd15"><div class="line"><span class="tname">验证方式</span><div class="info-r"><select class="bt-input-text mr5" name="file_rule" style="width:250px"></select></div></div>\
                                                    <ul class="help-info-text c7"><li>文件验证（HTTP）：确保网站能够通过http正常访问</li><li>文件验证（HTTPS）：确保网站已开启https，并且网站能够通过https正常访问</li><li>DNS验证：需要手动解析DNS记录值</li></ul>\
                                                </div>',
                    success: function (layero, index) {
                      var _option_list = { '文件验证(HTTP)': 'HTTP_CSR_HASH', '文件验证(HTTPS)': 'HTTPS_CSR_HASH', 'DNS验证(CNAME解析)': 'CNAME_CSR_HASH' },
                        _option = '';
                      $.each(_option_list, function (index, item) {
                        _option += '<option value="' + item + '" ' + (type == item ? 'selected' : '') + '>' + index + '</option>';
                      })
                      $('select[name=file_rule]').html(_option);
                    },
                    yes: function (index, layero) {
                      var new_type = $('select[name=file_rule]').val();
                      if (type == new_type) return layer.msg('重复的验证方式', { icon: 2 })
                      var loads = bt.load('正在修改验证方式,请稍候...');
                      bt.send('again_verify', 'ssl/again_verify', { oid: oid, dcvMethod: new_type }, function (res) {
                        loads.close();
                        if (res.status) layer.close(index);
                        layer.msg(res.msg, { icon: res.status ? 1 : 2 })
                      })
                    }
                  });
                })
              }
              /**
               * @description 验证域名
               * @param {Number} oid 域名订单ID
               * @returns void
               */
              function verify_order_veiw (oid, is_success) {
                var loads = bt.load('正在获取验证结果,请稍候...');
                bt.send('get_verify_result', 'ssl/get_verify_result', { oid: oid }, function (res) {
                  loads.close();
                  if (!res.status) {
                    bt.msg(res);
                    return false;
                  }
                  if (res.status == 'COMPLETE') {
                    site.ssl.reload();
                    return false;
                  }
                  var rdata = res.data;
                  var domains = [],
                    type = rdata.dcvList[0].dcvMethod != 'CNAME_CSR_HASH',
                    info = {};
                  $.each(rdata.dcvList, function (key, item) {
                    domains.push(item['domainName']);
                  });
                  if (type) {
                    info = { fileName: rdata.DCVfileName, fileContent: rdata.DCVfileContent, filePath: '/.well-known/pki-validation/', paths: res.paths, kfqq: res.kfqq };
                  } else {
                    info = { dnsHost: rdata.DCVdnsHost, dnsType: rdata.DCVdnsType, dnsValue: rdata.DCVdnsValue, paths: res.paths, kfqq: res.kfqq };
                  }
                  if (is_success) {
                    is_success({ type: type, domains: domains, info: info });
                    return false;
                  }
                  loadT = bt.open({
                    type: 1,
                    title: '验证域名-' + (type ? '文件验证' : 'DNS验证'),
                    area: '620px',
                    content: reader_domains_cname_check({ type: type, domains: domains, info: info }),
                    success: function (layero, index) {
                      var clipboard = new ClipboardJS('.parsing_info .parsing_icon');
                      clipboard.on('success', function (e) {
                        bt.msg({ status: true, msg: '复制成功' });
                        e.clearSelection();
                      });
                      clipboard.on('error', function (e) {
                        bt.msg({ status: true, msg: '复制失败，请手动ctrl+c复制！' });
                        console.error('Action:', e.action);
                        console.error('Trigger:', e.trigger);
                      });
                      $('.verify_ssl_domain').click(function () {
                        verify_order_veiw(oid);
                        layer.close(index);
                      });

                      $('.set_verify_type').click(function () {
                        again_verify_veiw(oid);
                        layer.close(index);
                      });

                      $('.return_ssl_list').click(function () {
                        layer.close(index);
                        $('#ssl_tabs span.on').click();
                      });

                      // 重新验证按钮
                      $('.domains_table').on('click', '.check_url_results', function () {
                        var _url = $(this).data('url'),
                          _con = $(this).data('content');
                        check_url_txt(_url, _con, this)

                      })
                    }
                  });
                });
              }

              // 续签视图
              function renewal_ssl_view (item) {
                bt.confirm({
                  title: '续签证书',
                  msg: '当前证书订单需要重新生成新订单，需要手动续签，和重新部署证书，是否继续操作?'
                }, function () {
                  var loadT = bt.load('正在续签证书，可能等待时间较长，请稍候...');
                  bt.send('renew_cert_order', 'ssl/renew_cert_order', { oid: item.oid }, function (res) {
                    loadT.close();
                    site.reload();
                    setTimeout(function () {
                      bt.msg(res)
                    }, 1000)
                  });
                })
              }

              /**
               * @description 重新验证
               * @param {String} url 验证地址
               * @param {String} content 验证内容
               * @returns 返回验证状态
               */
              function check_url_txt (url, content, _this) {
                var loads = bt.load('正在获取验证结果,请稍候...');
                bt.send('check_url_txt', 'ssl/check_url_txt', { url: url, content: content }, function (res) {
                  loads.close();
                  var html = '<span style="color:red">失败[' + res + ']</span><a href="https://www.bt.cn/bbs/thread-56802-1-1.html" target="_blank" class="bt-ico-ask" style="cursor: pointer;">?</a>'
                  if (res === 1) {
                    html = '<a class="btlink">通过</a>';
                  }
                  $(_this).parents('tr').find('td:nth-child(2)').html(html)
                })
              }
              /**
               * @description 渲染验证模板接口
               * @param {Object} data 验证数据
               * @returns void
              */
              function reader_domains_cname_check (data) {
                var html = '';
                if (data.type) {
                  var check_html = '<div class="bt-table domains_table" style="margin-bottom:20px"><div class="divtable"><table class="table table-hover"><thead><tr><th width="250">URL</th><th width="85">验证结果</th><th style="text-align:right;">操作</th></thead>'
                  var paths = data.info.paths
                  for (var i = 0; i < paths.length; i++) {
                    check_html += '<tr><td><span title="' + paths[i].url + '" class="lib-ssl-overflow-span-style">' + paths[i].url + '</span></td><td>' + (paths[i].status == 1 ? '<a class="btlink">通过</a>' : '<span style="color:red">失败[' + paths[i].status + ']</span><a href="https://www.bt.cn/bbs/thread-56802-1-1.html" target="_blank" class="bt-ico-ask" style="cursor: pointer;">?</a>') + '</td><td style="text-align:right;"><a href="javascript:bt.pub.copy_pass(\'' + paths[i].url + '\');" class="btlink">复制</a> | <a href="' + paths[i].url + '" target="_blank" class="btlink">打开</a> | <a data-url="' + paths[i].url + '" data-content="' + data.info.fileContent + '" class="btlink check_url_results">重新验证</a></td>'
                  }
                  check_html += '</table></div></div>'
                  html = '<div class="lib-ssl-parsing">\
                    <div class="parsing_tips">请给以下域名【 <span class="highlight">' + data.domains.join('、') + '</span> 】添加验证文件，验证信息如下：</div>\
                    <div class="parsing_parem"><div class="parsing_title">文件所在位置：</div><div class="parsing_info"><input type="text" name="filePath"  class="parsing_input border" value="' + data.info.filePath + '" readonly="readonly" style="width:350px;"/></div></div>\
                    <div class="parsing_parem"><div class="parsing_title">文件名：</div><div class="parsing_info"><input type="text" name="fileName" class="parsing_input" value="' + data.info.fileName + '" readonly="readonly" style="width:350px;"/><span class="parsing_icon" data-clipboard-text="' + data.info.fileName + '">复制</span></div></div>\
                    <div class="parsing_parem"><div class="parsing_title" style="vertical-align: top;">文件内容：</div><div class="parsing_info"><textarea name="fileValue"  class="parsing_textarea" readonly="readonly" style="width:350px;">' + data.info.fileContent + '</textarea><span class="parsing_icon" style="display: block;width: 60px;border-radius: 3px;" data-clipboard-text="' + data.info.fileContent + '">复制</span></div></div>' + check_html +
                    '<div class="parsing_tips" style="font-size:13px;line-height: 24px;">· 本次验证结果是由【本服务器验证】，实际验证将由【CA服务器】进行验证，请耐心等候</br>· 请确保以上列表所有项都验证成功后点击【验证域名】重新提交验证</br>· 如长时间验证不通过，请通过【修改验证方式】更改为【DNS验证】</br>· SSL添加文件验证方式 ->> <a href="https://www.bt.cn/bbs/thread-56802-1-1.html" target="_blank" class="btlink" >查看教程</a> <span style="padding-left:60px">专属客服QQ：' + data.info.kfqq + '</span></div>\
                        <div class="parsing_parem" style="padding: 0 55px;"><button type="submit" class="btn btn-success verify_ssl_domain">验证域名</button><button type="submit" class="btn btn-success set_verify_type">修改验证方式</button><button type="submit" class="btn btn-default return_ssl_list">返回列表</button></div>\
                    </div>';
                } else {
                  html = '<div class="lib-ssl-parsing">\
                        <div class="parsing_tips">请给以下域名【 <span class="highlight">' + data.domains.join('、') + '</span> 】添加“' + data.info.dnsType + '”解析，解析参数如下：</div>\
                        <div class="parsing_parem"><div class="parsing_title">主机记录：</div><div class="parsing_info"><input type="text" name="host" class="parsing_input" value="' + data.info.dnsHost + '" readonly="readonly" /><span class="parsing_icon" data-clipboard-text="' + data.info.dnsHost + '">复制</span></div></div>\
                        <div class="parsing_parem"><div class="parsing_title">记录值：</div><div class="parsing_info"><input type="text" name="domains"  class="parsing_input" value="' + data.info.dnsValue + '" readonly="readonly" /><span class="parsing_icon" data-clipboard-text="' + data.info.dnsValue + '">复制</span></div></div>\
                        <div class="parsing_tips" style="font-size:13px;line-height: 24px;">· 本次验证结果是由【本服务器验证】，实际验证将由【CA服务器】进行验证，请耐心等候</br>· 请确保以上列表所有项都验证成功后点击【验证域名】重新提交验证</br>· 如长时间验证不通过，请通过【修改验证方式】更改为【DNS验证】</br>· 如何添加域名解析，《<a href="https://cloud.tencent.com/document/product/302/3446" class="btlink" target="__blink">点击查看教程</a>》，和咨询服务器运营商。</div>\
                        <div class="parsing_parem" style="padding: 0 55px;"><button type="submit" class="btn btn-success verify_ssl_domain">验证域名</button><button type="submit" class="btn btn-default set_verify_type">修改验证方式</button><button type="submit" class="btn btn-default return_ssl_list">返回列表</button></div>\
                    </div>';
                }
                return html;
              }
              // 购买证书信息
              function pay_ssl_business () {
                var order_info = {},
                  user_info = {},
                  is_check = false;
                pay_ssl_layer = bt.open({
                  type: 1,
                  title: '购买商业证书',
                  area: ['790px', '860px'],
                  content: '<div class="bt_business_ssl"><div class="bt_business_tab bt_business_form active">\
                                                    <div class="business_line">\
                                                        <div class="business_title">证书优势</div>\
                                                        <div class="business_info business_advantage">\
                                                            <div class="business_advantage_item">\
                                                                <span class="advantage_icon glyphicon glyphicon glyphicon-ok"></span>\
                                                                <span class="advantage_title">企业级证书</span>\
                                                            </div>\
                                                            <div class="business_advantage_item">\
                                                                <span class="advantage_icon glyphicon glyphicon glyphicon-ok"></span>\
                                                                <span class="advantage_title">极速申请</span>\
                                                            </div>\
                                                            <div class="business_advantage_item">\
                                                                <span class="advantage_icon glyphicon glyphicon glyphicon-ok"></span>\
                                                                <span class="advantage_title">安全性高</span>\
                                                            </div>\
                                                            <div class="business_advantage_item">\
                                                                <span class="advantage_icon glyphicon glyphicon glyphicon-ok"></span>\
                                                                <span class="advantage_title">通过率高</span>\
                                                            </div>\
                                                            <div class="business_advantage_item">\
                                                                <span class="advantage_icon glyphicon glyphicon glyphicon-ok"></span>\
                                                                <span class="advantage_title">赔付保证</span>\
                                                            </div>\
                                                            <div class="business_advantage_item" style="width:75%">\
                                                                <span class="advantage_icon glyphicon glyphicon glyphicon-ok"></span>\
                                                                <span class="advantage_title">官方推荐(宝塔官方bt.cn也是使用的该证书)</span>\
                                                            </div>\
                                                        </div>\
                                                    </div>\
                                                    <div class="business_line">\
                                                        <div class="business_title">证书分类</div>\
                                                        <div class="business_info business_type">\
                                                            <div class="ssl_type_item active" data-type="dv">\
                                                                <div class="ssl_type_title">域名型证书(DV)</div>\
                                                                <div class="ssl_type_ps">推荐个人博客、个人网站等个人项目使用</div>\
                                                            </div>\
                                                            <div class="ssl_type_item" data-type="ov">\
                                                                <div class="ssl_type_title">企业型证书(OV)</div>\
                                                                <div class="ssl_type_ps">推荐企业官网、支付、电商、教育、医疗等部门使用</div>\
                                                            </div>\
                                                            <div class="ssl_type_item" data-type="ev">\
                                                                <div class="ssl_type_title">增强型证书(EV)</div>\
                                                                <div class="ssl_type_ps">推荐银行、金融、保险、电子商务、中大型企业、政府机关等使用</div>\
                                                            </div>\
                                                        </div>\
                                                    </div>\
                                                    <div class="business_line">\
                                                        <div class="business_title">证书类型</div>\
                                                        <div class="business_info business_class">\
                                                            <div class="business_class_list"></div>\
                                                        </div>\
                                                    </div>\
                                                    <div class="business_line">\
                                                        <div class="business_title">域名数量</div>\
                                                        <div class="business_info">\
                                                            <div class="domain_number_group">\
                                                                <div class="domain_number_reduce is_disable" data-type="reduce"></div>\
                                                                <input type="number" class="domain_number_input" value=""/>\
                                                                <div class="domain_number_add"  data-type="add"></div>\
                                                            </div>\
                                                            <div class="domain_number_tips"></div>\
                                                        </div>\
                                                    </div>\
                                                    <div class="business_line">\
                                                        <div class="business_title">购买年限</div>\
                                                        <div class="business_info"><div class="business_period_list"></div></div>\
                                                    </div>\
                                                    <div class="business_line">\
                                                        <div class="business_title">人工服务</div>\
                                                        <div class="business_info business_artificial">\
                                                            <div class="business_artificial_content"><div class="business_artificial_checkbox active"></div><div class="business_artificial_label"><span>--元/次</span>，付费安装服务，保证100%成功，不成功可全额退款。</div></div>\
                                                        </div>\
                                                    </div>\
                                                    <div class="business_line">\
                                                        <div class="business_title">总计费用</div>\
                                                        <div class="business_info business_cost">\
                                                            <span class="business_price_large">--</span>\
                                                            <span class="business_price_small">元/1年</span>\
                                                            <span class="business_original_price">原价<span>--</span>元/1年</span>\
                                                        </div>\
                                                    </div>\
                                                    <div class="business_line" style="margin-bottom:0;">\
                                                        <div class="business_info">\
                                                            <button type="button" class="business_pay">立即购买</button>\
                                                        </div>\
                                                    </div>\
                                                    <span style="position: absolute;bottom: 0;left: 0;right: 0;text-align: center;display: inline-block;height: 45px;line-height: 45px;background: #fafafafa;color: #ff0c00;font-size: 13px;">禁止含有诈骗、赌博、色情、木马、病毒等违法违规业务信息的站点申请SSL证书，如有违反，撤销申请，停用账号</span>\
                                                </div>\
                                                <div class="bt_business_tab ssl_applay_info">\
                                                    <div class="guide_nav"><span class="active">微信支付</span><span >支付宝支付</span></div>\
                                                    <div class="paymethod">\
                                                        <div class="pay-wx" id="PayQcode"></div>\
                                                    </div>\
                                                    <div class="lib-price-box text-center">\
                                                        <span class="lib-price-name f14"><b>总计</b></span>\
                                                        <span class="price-txt"><b class="sale-price"></b>元</span>\
                                                    </div>\
                                                    <div class="lib-price-detailed">\
                                                        <div class="info">\
                                                            <span class="text-left">商品名称</span>\
                                                            <span class="text-right"></span>\
                                                        </div>\
                                                        <div class="info">\
                                                            <span class="text-left">下单时间</span>\
                                                            <span class="text-right"></span>\
                                                        </div>\
                                                    </div>\
                                                    <div class="lib-prompt"><span>微信扫一扫支付</span></div>\
                                                    <span style="position: absolute;bottom: 0;left: 0;right: 0;text-align: center;display: inline-block;height: 45px;line-height: 45px;background: #fafafafa;color: #ff0c00;font-size: 13px;">禁止含有诈骗、赌博、色情、木马、病毒等违法违规业务信息的站点申请SSL证书，如有违反，撤销申请，停用账号</span>\
                                                </div>\
                                                <div class="bt_business_tab ssl_order_check">\
                                                    <div class="order_pay_title">支付成功</div>\
                                                    <div class="lib-price-detailed">\
                                                        <div class="info">\
                                                            <span class="text-left">商品名称</span>\
                                                            <span class="text-right"></span>\
                                                        </div>\
                                                        <div class="info">\
                                                            <span class="text-left">商品价格</span>\
                                                            <span class="text-right"></span>\
                                                        </div>\
                                                        <div class="info">\
                                                            <span class="text-left">下单时间</span>\
                                                            <span class="text-right"></span>\
                                                        </div>\
                                                    </div>\
                                                    <div class="order_pay_btn"><a href="javascript:;">人工服务</a><a href="javascript:;" data-type="info">完善证书资料</a><a href="javascript:;" data-type="clear">返回列表</a></div>\
                                                    <ul class="help-info-text c7" style="padding:15px 0 0 70px;font-size:13px;">\
                                                        <li>支付成功后请点击“完善证书资料”继续申请证书。</li>\
                                                        <li>如果已购买人工服务，请点击“人工服务”咨询帮助。</li>\
                                                    </ul>\
                                                </div>\
                                            </div>',
                  success: function (layero, indexs) {
                    var product_list = [],
                      product_current = {},
                      buyPeriod = 1,
                      install_service = null,
                      add_domain_number = 0,
                      order_id = null,
                      qq_info = null;
                    $('.business_type .ssl_type_item').click(function () {
                      $(this).addClass('active').siblings().removeClass('active');
                      reader_product_list({
                        p_type: $(this).data('type')
                      }, function (res) {
                        if (parseInt(res.checked)) install_service = $('.business_artificial_checkbox').hasClass('active');
                        buyPeriod = 1;
                        reader_product_info(product_list[0]);
                      });
                    });
                    $('.business_class .business_class_list').on('click', '.business_class_item', function () {
                      var index = $(this).data('index'), data = product_list[index];
                      $(this).addClass('active').siblings().removeClass('active');
                      $('.domain_number_reduce').addClass('is_disable');
                      delete product_current.current_num;
                      buyPeriod = 1;
                      reader_product_info(data);
                      reader_period_list(data.max_years)
                      product_current = data;
                    });
                    $('.business_period_list').on('click', '.business_period_item', function () {
                      buyPeriod = $(this).index() + 1;
                      $(this).addClass('active').siblings().removeClass('active');
                      is_additional_price($('.business_artificial_checkbox').hasClass('active'), product_current);
                    });


                    $('.business_artificial_checkbox').click(function () {
                      if ($(this).hasClass('active')) {
                        $(this).removeClass('active');
                        is_additional_price(false, product_current);
                        install_service = false;
                      } else {
                        layer.tips('购买人工服务的用户，请及时去官网完善个人信息（QQ/邮箱），方便客服联系', this, {
                          tips: [1, '#20a53a']
                        });
                        $(this).addClass('active');
                        is_additional_price(true, product_current);
                        install_service = true;
                      }
                    });
                    $('.business_artificial_label').click(function () {
                      $(this).prev().click();
                    });
                    $('.business_pay').click(function () {
                      var loadT = bt.load('正在生成支付订单，请稍候...'),
                        data = product_current,
                        num = 0;
                      if (typeof data.current_num == "undefined") data.current_num = data.num
                      if (data.add_price !== 0) num = parseInt(data.current_num - data.num);
                      bt.send('apply_cert_order_pay', 'ssl/apply_cert_order_pay', {
                        pdata: JSON.stringify({
                          pid: data.pid,
                          install: install_service ? 1 : 0,
                          years: buyPeriod,
                          num: num
                        })
                      }, function (res) {
                        loadT.close();
                        if (res.status) {
                          is_check = true;
                          $('.bt_progress_content .bt_progress_item:eq(1)').addClass('active');
                          $('.ssl_applay_info').addClass('active').siblings().removeClass('active');
                          reader_applay_qcode($.extend({
                            name: data.title + buyPeriod + '年' + (install_service ? '(包含人工服务)' : ''),
                            price: parseFloat((install_service ? data.install_price : 0) + ((data.price + (data.add_price * num)) * buyPeriod)).toFixed(2),
                            time: bt.format_data(new Date().getTime())
                          }, res.msg), function (info) {
                            check_applay_status(function (rdata) {
                              $('.bt_progress_content .bt_progress_item:eq(2)').addClass('active');
                              $('.ssl_order_check').addClass('active').siblings().removeClass('active');
                              $('.ssl_order_check .lib-price-detailed .text-right:eq(0)').html(info.name);
                              $('.ssl_order_check .lib-price-detailed .text-right:eq(1)').html('￥' + info.price);
                              $('.ssl_order_check .lib-price-detailed .text-right:eq(2)').html(info.time);
                              $('#ssl_tabs .on').click();
                            }); //检测支付状态
                          }); //渲染二维码
                        }
                      });
                    });

                    $('.guide_nav span').click(function () {
                      var price = $('.business_price_large').text(),
                        is_wx_quota = parseFloat(price) >= 6000;
                      if ($(this).index() === 0 && is_wx_quota) {
                        layer.msg('微信单笔交易限额6000元,请使用支付宝支付', {
                          icon: 0
                        });
                      } else {
                        $(this).addClass('active').siblings().removeClass('active');
                        $('.lib-prompt span').html($(this).index() == 0 ? '微信扫一扫支付' : '支付宝扫一扫支付');
                        $('#PayQcode').empty();
                        $('#PayQcode').qrcode({
                          render: "canvas",
                          width: 200,
                          height: 200,
                          text: $(this).index() != 0 ? order_info.alicode : order_info.wxcode
                        });
                      }
                    });
                    $('.order_pay_btn a').click(function () {
                      switch ($(this).data('type')) {
                        case 'info':
                          confirm_certificate_info($.extend(product_current, {
                            oid: order_id,
                            qq: qq_info,
                            install: install_service,
                            limit: add_domain_number
                          }));
                          break;
                        case 'clear':
                          layer.close(indexs);
                          break;
                      }
                    });
                    $('.domain_number_reduce,.domain_number_add').click(function () {
                      if ($(this).hasClass('is_disable')) return false;
                      var type = $(this).data('type'),
                        data = product_current,
                        input = $('.domain_number_input'),
                        reduce = input.prev(),
                        add = input.next(),
                        min = parseInt(input.attr('min')),
                        max = parseInt(input.attr('max')),
                        input_val = parseInt(input.val());
                      switch (type) {
                        case 'reduce':
                          input_val--;
                          if (min > input_val < max) {
                            input.val(input_val);
                          }
                          break;
                        case 'add':
                          input_val++;
                          if (min > input_val < max) {
                            input.val(input_val);
                            add.removeClass('is_disable');
                          }
                          if (input_val == max) $(this).addClass('is_disable');
                          break;
                      }
                      if (input_val == min) {
                        reduce.addClass('is_disable');
                      } else if (input.val() == max) {
                        add.addClass('is_disable');
                      } else {
                        reduce.removeClass('is_disable');
                        add.removeClass('is_disable');
                      }
                      reader_product_info($.extend(product_current, {
                        current_num: input_val
                      }));
                    });
                    $('.domain_number_input').on('input', function () {
                      var input = $(this),
                        input_val = parseInt(input.val()),
                        input_min = parseInt(input.attr('min')),
                        input_max = parseInt(input.attr('max')),
                        reduce = input.prev(),
                        add = input.next();
                      if (input_val < input_min) {
                        input.val(input_min);
                      } else if (input_val > input_max) {
                        input.val(input_max);
                      }
                      if (input.val() == '') {
                        input.val(input_min);
                        input_val = input_min;
                      }
                      if (input_val == input_min) {
                        reduce.addClass('is_disable');
                      } else if (input_val == input_max) {
                        add.addClass('is_disable');
                      } else {
                        reduce.removeClass('is_disable');
                        add.removeClass('is_disable');
                      }
                      reader_product_info($.extend(product_current, {
                        current_num: parseInt(input.val())
                      }));
                    });
                    $('.business_type .ssl_type_item:eq(0)').click();

                    function reader_product_info (data) {
                      add_domain_number = data.current_num;
                      $('.business_original_price span').html(data.src_price);
                      $('.domain_number_input').val(data.current_num || data.num).attr('min', data.num);
                      $('.business_artificial .business_artificial_label span').html(data.install_price + '元/次');
                      is_additional_price(install_service, data);
                      if (data.add_price != 0) {
                        $('.domain_number_tips').html('每个域名<span>' + data.add_price + '元/个</span>，默认包含' + data.num + '个域名');
                        $('.domain_number_input').next().removeClass('is_disable');
                        $('.domain_number_input').attr('max', 999);
                      } else {
                        $('.domain_number_tips').empty();
                        $('.domain_number_input').next().addClass('is_disable');
                        $('.domain_number_input').attr('max', data.num);
                      }
                    }

                    function is_additional_price (status, data) {
                      var input = $('.domain_number_input').val(),
                        price = parseFloat((status ? data.install_price : 0) + ((data.price + (data.add_price * (parseInt(input) - data.num))) * buyPeriod)).toFixed(2)
                      $('.business_price_large').html(price)
                      $('.business_price_small').html('元/' + buyPeriod + '年' + (status ? '(包含人工服务)' : ''))
                    }

                    function reader_product_list (data, callback) {
                      var html = '', period = [];
                      $('.business_class_list').html('<div class="business_class_loading">正在获取证书列表，请稍候...</div>')
                      bt.send('get_product_list', 'ssl/get_product_list', data, function (res) {
                        user_info = res.administrator;
                        product_list = res.data;
                        for (var i = 0; i < res.data.length; i++) {
                          var item = res.data[i];
                          html += '<div class="business_class_item ' + (i === 0 ? 'active' : '') + '" data-index="' + i + '"><div class="business_class_title">' + item.title + '</div><div class="business_class_original">原价' + item.other_price + '元/1年</div><div class="business_class_price">' + item.price.toFixed(2) + '元/1年</div></div>';
                        }
                        reader_period_list(res.data[0].max_years)
                        $('.business_class_list').html(html);
                        product_current = product_list[0];
                        if (callback) callback(res)
                      });
                    }

                    function reader_period_list (period) {
                      var html = [];
                      for (var i = 1; i <= period; i++) {
                        html += '<div class="business_period_item ' + (i === 1 ? 'active' : '') + '"><span>' + i + '年</span></div>'
                      }
                      $('.business_period_list').html(html);
                    }

                    function reader_applay_qcode (data, callback) {
                      var price = $('.business_price_large').text(),
                        is_wx_quota = parseFloat(price) >= 6000;
                      order_id = data.oid;
                      qq_info = data.qq;
                      order_info = data
                      if (is_wx_quota) {
                        $('.guide_nav span:eq(1)').click();
                      } else {
                        $('#PayQcode').empty().qrcode({
                          render: "canvas",
                          width: 240,
                          height: 240,
                          text: data.wxcode
                        });
                      }
                      $('.price-txt .sale-price').html($('.business_price_large').text());
                      $('.lib-price-detailed .info:eq(0) span:eq(1)').html(data.name);
                      $('.lib-price-detailed .info:eq(1) span:eq(1)').html(data.time);
                      if (typeof data.qq != "undefined") {
                        $('.order_pay_btn a:eq(0)').attr({
                          'href': data.qq,
                          'target': '_blank'
                        });
                      } else {
                        $('.order_pay_btn a:eq(0)').remove();
                      }
                      if (callback) callback(data);
                    }

                    function check_applay_status (callback) {
                      bt.send('get_pay_status', 'ssl/get_pay_status', {
                        oid: order_id
                      }, function (res) {
                        if (res) {
                          is_check = false;
                          if (callback) callback(res);
                        } else {
                          if (!is_check) return false;
                          setTimeout(function () {
                            check_applay_status(callback);
                          }, 2000);
                        }
                      });
                    }
                  },
                  cancel: function (index) {
                    if (is_check) {
                      if (confirm('当前正在支付订单，是否取消？')) {
                        layer.close(index)
                        is_check = false;
                      }
                      return false;
                    }
                  }
                });
              }
              // 确认证书信息
              function confirm_certificate_info (config) {
                var userLoad = bt.load('正在获取用户信息，请稍候...');
                bt.send('get_cert_admin', 'ssl/get_cert_admin', {}, function (res) {
                  userLoad.close();
                  var html = '';
                  var isWildcard = config.code.indexOf('wildcard') > -1;
                  if (typeof pay_ssl_layer != 'undefined') pay_ssl_layer.close();
                  if (config.code.indexOf('multi') > -1) {
                    if (isWildcard) {
                      placeholder = '多域名通配符证书，每行一个域名，支持' + config.limit + '个域名，必填项,例如：\r*.bt.cn\r*.bttest.cn';
                    } else {
                      placeholder = '多域名证书，每行一个域名，支持' + config.limit + '个域名，必填项,例如：\rwww.bt.cn\rwww.bttest.cn';
                    }
                    html = '<textarea class="bt-input-text mr20 key" name="domains" placeholder="' + placeholder + '" style="line-height:20px;width:400px;height:150px;padding:8px;"></textarea>';
                  } else {
                    if (isWildcard) {
                      placeholder = '请输入需要申请证书的域名（单域名通配符证书），必填项，例如：*.bt.cn';
                    } else {
                      placeholder = '请输入需要申请证书的域名（单域名证书），必填项，例如：www.bt.cn';
                    }
                    html = '<input type="text" disabled="true" readonly="readonly" id="apply_site_name" class="bt-input-text mr5" name="domains" placeholder="' + placeholder + '"/><button class="btn btn-success btn-xs" onclick="site.select_site_list(\'apply_site_name\',\'' + config.code + '\')" style="">选择已有域名</button><button class="btn btn-success btn-xs" onclick="site.select_site_txt(\'apply_site_name\')" style="margin: 5px;">自定义域名</button>';
                  }
                  bt.open({
                    type: 1,
                    title: '完善商业证书资料',
                    area: '610px',
                    content: '<form class="bt_form perfect_ssl_info" onsubmit="return false;">\
                        <div class="line">\
                            <span class="tname">证书信息</span>\
                            <div class="info-r">\
                                <span class="ssl_title">' + config.title + (config.limit > 1 ? ('<span style="margin-left:5px;">，包含' + config.limit + '个域名</span>') : '') + '</span>\
                            </div>\
                        </div>\
                        <div class="line">\
                            <span class="tname">域名</span>\
                            <div class="info-r domain_list_info" style="margin-bottom:-5px;">' + html + '</div>\
                        </div>\
                        <div class="line check_model_line">\
                            <span class="tname">验证方式</span>\
                            <div class="info-r">\
                              <label title="如网站还未备案完成，可选【DNS验证】." class="mr20">\
                                <input type="radio" name="dcvMethod" checked="checked" value="CNAME_CSR_HASH">\
                                <span>DNS验证(CNAME解析)</span>\
                              </label>\
                              <label title="如网站未开启301、302、强制HTTPS、反向代理功能." class="mr20"  style="display: ' + (isWildcard ? 'none' : 'inline-block') + ';">\
                                  <input type="radio" name="dcvMethod" value="HTTP_CSR_HASH">\
                                  <span>文件验证(HTTP)</span>\
                              </label>\
                              <label title="如网站开启【强制HTTPS】，请选【HTTPS验证】" class="mr20" style="display: ' + (isWildcard ? 'none' : 'inline-block') + ';">\
                                  <input type="radio" name="dcvMethod" value="HTTPS_CSR_HASH">\
                                  <span>文件验证(HTTPS)</span>\
                              </label>\
                            </div>\
                        </div>\
                        <div class="line">\
                            <span class="tname">所在地区</span>\
                            <div class="info-r">\
                                <input type="text" class="bt-input-text mr5" name="state" value="' + res.state + '" placeholder="请输入所在省份，必填项" style="width: 190px; margin-right:0;" data-placeholder="请输入所在省份，必填项">\
                                <input type="text" class="bt-input-text mr5" name="city" value="' + res.city + '" placeholder="请输入所在市/县，必填项" style="width: 190px; margin-left: 15px;" data-placeholder="请输入所在市/县，必填项" />\
                            </div>\
                        </div>\
                        <div class="line" style="display:' + ((config.code.indexOf('ov') > -1 || config.code.indexOf('ev') > -1) ? 'block' : 'none') + '">\
                            <span class="tname">公司详细地址</span>\
                            <div class="info-r">\
                                <input type="text" class="bt-input-text mr5" name="address" value="' + res.address + '" placeholder="请输入公司详细地址，具体要求见说明，必填项" />\
                            </div>\
                        </div>\
                        <div class="line">\
                            <span class="tname">公司名称</span>\
                            <div class="info-r">\
                                <input type="text" class="bt-input-text mr5" name="organation" value="' + res.organation + '" placeholder="请输入公司名称，如为个人申请请输入个人姓名，必填项" />\
                            </div>\
                        </div>\
                        <div class="line">\
                            <span class="tname">姓名</span>\
                            <div class="info-r ">\
                                <input type="text" class="bt-input-text mr5" name="name" value="' + res.lastName + res.firstName + '" placeholder="请输入姓名，必填项" />\
                            </div>\
                        </div>\
                        <div class="line">\
                            <span class="tname">邮箱</span>\
                            <div class="info-r ">\
                                <input type="text" class="bt-input-text mr5" name="email" value="' + res.email + '" placeholder="请输入邮箱地址，必填项" />\
                            </div>\
                        </div>\
                        <div class="line">\
                            <span class="tname">手机</span>\
                            <div class="info-r">\
                                <input type="text" class="bt-input-text mr5" name="mobile" value="' + res.mobile + '" placeholder="请输入手机号码，若为空，则使用当前绑定手机号" />\
                            </div>\
                        </div>\
                        <div class="line">\
                            <div class="info-r"><button class="btn btn-success submit_ssl_info">提交资料</button></div>\
                        </div>\
                        <ul class="help-info-text c7 ssl_help_info" style="display: ' + (isWildcard ? 'block' : 'none') + ';">\
                            <li>通配符证书只支持DNS验证</li>\
                        </ul>\
                        <ul class="help-info-text c7 ssl_help_info" style="display:' + ((config.code.indexOf('ov') > -1 || config.code.indexOf('ev') > -1) ? 'block' : 'none') + '; margin-top: 0;">\
                            <li>OV/EV证书申请流程条件：</li>\
                            <li>1、填写网站验证信息(文件验证或DNS验证)</li>\
                            <li>2、完成邮箱认证，根据CA发送的邮件完善邮件内容(中文填写即可)</li>\
                            <li>3、企查查或者爱企查、百度地图、114best能查询到相关企业信息，且公司名和公司地址完全匹配</li>\
                            <li>4、企查查或其他平台留下的电话能保证周一到周五(7:00 - 15:00)能接听到CA的认证电话，电话号码归属地来自美国，请留意接听。</li>\
                        </ul>\
                    </form>',
                    // 添加dns接口
                    add_dns_interface: function () {
                      bt.site.get_dns_api(function (api) {
                        var arrs_list = [],
                          arr_obj = {};
                        for (var x = 0; x < api.length; x++) {
                          arrs_list.push({
                            title: api[x].title,
                            value: api[x].name
                          });
                          arr_obj[api[x].name] = api[x];
                        }
                        var data = {
                          title: '选择DNS接口',
                          class: 'dns_interface_line',
                          items: [{
                            name: 'dns_interface_select',
                            width: '120px',
                            type: 'select',
                            items: arrs_list,
                            callback: function (obj) {
                              var _val = obj.val();
                              $('.set_dns_config').remove();
                              var _val_obj = arr_obj[_val];
                              var _form = {
                                title: '',
                                area: '550px',
                                list: [],
                                btns: [{
                                  title: '关闭',
                                  name: 'close'
                                }]
                              };
                              var helps = [];
                              if (_val_obj.data !== false) {
                                _form.title = '设置【' + _val_obj.title + '】接口';
                                helps.push(_val_obj.help);
                                var is_hide = true;
                                for (var i = 0; i < _val_obj.data.length; i++) {
                                  _form.list.push({
                                    title: _val_obj.data[i].name,
                                    name: _val_obj.data[i].key,
                                    value: _val_obj.data[i].value
                                  })
                                  if (!_val_obj.data[i].value) is_hide = false;
                                }
                                _form.btns.push({
                                  title: '保存',
                                  css: 'btn-success',
                                  name: 'btn_submit_save',
                                  callback: function (ldata, load) {
                                    bt.site.set_dns_api({
                                      pdata: JSON.stringify(ldata)
                                    }, function (ret) {
                                      if (ret.status) {
                                        load.close();
                                        robj.find('input[type="radio"]:eq(0)').trigger('click')
                                        robj.find('input[type="radio"]:eq(1)').trigger('click')
                                      }
                                      bt.msg(ret);
                                    })
                                  }
                                })
                                if (is_hide) {
                                  obj.after('<button class="btn btn-default btn-sm mr5 set_dns_config">设置</button>');
                                  $('.set_dns_config').click(function () {
                                    var _bs = bt.render_form(_form);
                                    $('div[data-id="form' + _bs + '"]').append(bt.render_help(helps));
                                  });
                                } else {
                                  var _bs = bt.render_form(_form);
                                  $('div[data-id="form' + _bs + '"]').append(bt.render_help(helps));
                                }
                              }
                            }
                          }]
                        };
                        var form_line_html = bt.render_form_line(data);
                        $('.check_model_line.line').after(form_line_html.html);
                        $('[name="dns_interface_select"] option[value="dns"]').prop('selected', 'selected');
                        bt.render_clicks(form_line_html.clicks);
                      });
                    },
                    // 移除dns接口
                    remove_dns_interface: function () {
                      $('.dns_interface_line.line').remove();
                    },
                    check_dns_interface: function (callback) {
                      var val = $('input[name="dcvMethod"]:radio:checked').val();
                      if (val !== 'CNAME_CSR_HASH') {
                        if (callback) callback();
                        return
                      }
                      var dns_val = $('.dns_interface_select').val();
                      if (dns_val == 'dns') {
                        if (callback) callback();
                      } else {
                        bt.site.get_dns_api(function (res) {
                          var config;
                          for (var i = 0; i < res.length; i++) {
                            if (res[i].name == dns_val) {
                              config = res[i];
                              break;
                            }
                          }
                          var check = true;
                          var title = '';
                          if (config && config.data) {
                            for (var j = 0; j < config.data.length; j++) {
                              if (config.data[j].value === '') {
                                check = false;
                                title = config.title;
                                break;
                              }
                            }
                          }
                          if (check) {
                            if (callback) callback();
                          } else {
                            layer.msg('已选择DNS接口【' + title + '】未配置密钥', { icon: 2 });
                          }
                        });
                      }
                    },
                    success: function (layero, index) {
                      var _this_layer = this;
                      this.add_dns_interface();
                      // 验证方式
                      $('input[name="dcvMethod"]').change(function () {
                        var val = $(this).val();
                        if (val == 'CNAME_CSR_HASH') {
                          _this_layer.add_dns_interface();
                        } else {
                          _this_layer.remove_dns_interface();
                        }
                      });
                      $('.perfect_ssl_info').on('focus', 'input[type=text],textarea', function () {
                        var placeholder = $(this).attr('placeholder');
                        $('html').append($('<span id="width_test">' + placeholder + '</span>'));
                        $(this).attr('data-placeholder', placeholder);
                        layer.tips(placeholder, $(this), { tips: [1, '#20a53a'], time: 0 });
                        $(this).attr('placeholder', '');
                        $('#width_test').remove();
                      }).on('blur', 'input[type=text],textarea', function () {
                        var name = $(this).attr('name'),
                          val = $(this).val();
                        layer.closeAll('tips');
                        $(this).attr('placeholder', $(this).attr('data-placeholder'));
                        check_ssl_user_info($(this), name, val, config);
                      })
                      $('.submit_ssl_info').click(function () {
                        var data = {},
                          form = $('.perfect_ssl_info').serializeObject(),
                          is_ovev = config.code.indexOf('ov') > -1 || config.code.indexOf('ev') > -1,
                          loadT = null;
                        $('.perfect_ssl_info').find('input,textarea').each(function () {
                          var name = $(this).attr('name'),
                            value = $(this).val(),
                            value = check_ssl_user_info($(this), name, value, config);
                          if (typeof value === "boolean") {
                            form = false;
                            return false;
                          }
                          form[name] = value;
                        });
                        if (typeof form == "boolean") return false;
                        if (!(is_ovev)) form['address'] = form['state'] + form['city'];
                        if (typeof config.limit == "undefined") config.limit = config.num
                        if (form.domains.length < config.limit) {
                          bt.confirm({ title: '提示', msg: '检测到当前证书支持' + config.limit + '个域名可以继续添加域名，是否忽略继续提交？' }, function () {
                            req(true);
                          });
                          return false;
                        }
                        req(true);
                        function req (verify) {
                          if (is_ovev && verify) {
                            bt.open({
                              title: 'OV或EV证书企业信息二次确认',
                              area: ['600px'],
                              btn: ['继续提交', '取消'],
                              content: '<div class="bt_form certificate_confirm" style="font-size: 12px;padding-left: 25px">' +
                                '<div class="line">' +
                                '<span class="tname">公司名称</span>' +
                                '<div class="info-r"><input type="text" class="bt-input-text mr5" name="organation" value="' + form.organation + '" style="width:380px;"/></div>' +
                                '<div style="padding:0 0 5px 100px;color:#777">*确保与企查查获取的名称一致，否则认证失败需要重走流程。<a href="javascript:;" class="checkInfo btlink">点击查询</a></div>' +
                                '</div>' +
                                '<div class="line">' +
                                '<span class="tname">公司详细地址</span>' +
                                '<div class="info-r"><input type="text" class="bt-input-text mr5" name="address"  value="' + form.address + '" style="width:380px;"/></div>' +
                                '<div style="padding:0 0 0 100px;color:#777">*确保与企查查获取的地址一致，否则认证失败需要重走流程。</div>' +
                                '</div>' +
                                '<ul class="help-info-text c7 ssl_help_info">' +
                                '<li>商用OV/EV证书申请流程：</li>' +
                                '<li>1、完成邮箱认证，根据CA发送的邮件完善邮件内容(中文回复“确认”即可)</li>' +
                                '<li style="color:red">2、填写完整的【公司名】和【公司详细地址】，并且企查查等平台能查询到企业信息</li>' +
                                '<li>3、EV证书需要在认证平台留下的电话能接听CA的认证电话（周一到周五 7:00 - 15:00），电话号码归属地来自美国，请留意接听。</li>' +
                                '<li>支持认证平台包括企查查、爱企查、百度地图、114best，其中任意一个</li>' +
                                '</ul>' +
                                '</div>',
                              yes: function () {
                                req(false)
                              },
                              success: function () {
                                $('.certificate_confirm [name="organation"]').change(function () {
                                  $('.perfect_ssl_info [name="organation"]').val($(this).val())
                                  form.organation = $(this).val();
                                })
                                $('.certificate_confirm [name="address"]').change(function () {
                                  $('.perfect_ssl_info [name="address"]').val($(this).val())
                                  form.address = $(this).val();
                                })
                                $('.checkInfo').on('click', function (e) {
                                  window.open('https://www.qcc.com/web/search?key=' + $('.certificate_confirm [name="organation"]').val());
                                })
                              }
                            })
                            return false;
                          }
                          _this_layer.check_dns_interface(function () {
                            var loadT = bt.load('正在提交证书资料，请稍候...');
                            var auth_to = $("[name='dns_interface_select']") ? $("[name='dns_interface_select']").val() : '';
                            bt.send('apply_order_ca', 'ssl/apply_order_ca', {
                              pdata: JSON.stringify({
                                pid: config.pid,
                                oid: config.oid,
                                domains: form.domains,
                                dcvMethod: $("[name='dcvMethod']:checked").val(),
                                auth_to: auth_to,
                                Administrator: {
                                  job: '总务',
                                  postCode: '523000',
                                  country: 'CN',
                                  lastName: form.name,
                                  state: form.state,
                                  city: form.city,
                                  address: form.address,
                                  organation: form.organation,
                                  email: form.email,
                                  mobile: form.mobile,
                                  lastName: form.name
                                }
                              })
                            }, function (res) {
                              loadT.close();
                              if (typeof res.msg == "object") {
                                for (var key in res.msg.errors) {
                                  if (Object.hasOwnProperty.call(res.msg.errors, key)) {
                                    var element = res.msg.errors[key];
                                    bt.msg({
                                      status: false,
                                      msg: element
                                    });
                                  }
                                }
                              } else {
                                bt.msg(res);
                              }
                              if (res.status) {
                                layer.close(index);
                                verify_order_veiw(config.oid);
                                $('#ssl_tabs span.on').click();
                              }
                            });
                          });
                        }
                      });
                    }
                  });
                });
              }
              $('.ssl_business_application').click(function () {
                pay_ssl_business();
              });
              //订单证书操作
              $('.ssl_order_list').unbind('click').on('click', '.options_ssl', function () {
                var type = $(this).data('type'),
                  tr = $(this).parents('tr');
                itemData = order_list[tr.data('index')];
                switch (type) {
                  case 'deploy_ssl': // 部署证书
                    bt.confirm({
                      title: '部署证书',
                      msg: '是否部署该证书,是否继续？<br>证书类型：' + itemData.title + ' <br>证书支持域名：' + itemData.domainName.join('、') + '<br>部署站点名:' + web.name + ''
                    }, function (index) {
                      var loads = bt.load('正在部署证书，请稍候...');
                      bt.send('set_cert', 'ssl/set_cert', { oid: itemData.oid, siteName: web.name }, function (rdata) {
                        layer.close(index);
                        $('#webedit-con').empty();
                        site.set_ssl(web);
                        site.ssl.reload();
                        bt.msg(rdata);
                      });
                    });
                    break;
                  case 'verify_order': // 验证订单
                    verify_order_veiw(itemData.oid);
                    break;
                  case 'clear_order': // 取消订单
                    bt.confirm({
                      title: '取消订单',
                      msg: '是否取消该订单，订单域名【' + itemData.domainName.join('、') + '】，是否继续？'
                    }, function (index) {
                      var loads = bt.load('正在取消订单，请稍候...');
                      bt.send('cancel_cert_order', 'ssl/cancel_cert_order', { oid: itemData.oid }, function (rdata) {
                        layer.close(index);
                        if (rdata.status) {
                          $('#ssl_tabs span:eq(2)').click();
                          setTimeout(function () {
                            bt.msg(rdata);
                          }, 2000);
                        }
                        bt.msg(rdata);
                      });
                    })
                    break;
                  case 'perfect_user_info': //完善用户信息
                    confirm_certificate_info(itemData);
                    break;
                  case 'renewal_ssl':
                    renewal_ssl_view(itemData);
                    break;
                }
              });
            } else {
              robj.append('<div class="alert alert-warning" style="padding:10px">未绑定宝塔账号，请注册绑定，绑定宝塔账号(非论坛账号)可实现一键部署SSL</div>');
              var datas = [
                { title: '宝塔账号', name: 'bt_username', value: rdata.email, width: '260px', placeholder: '请输入手机号码' },
                { title: '密码', type: 'password', name: 'bt_password', value: rdata.email, width: '260px' },
                {
                  title: ' ',
                  items: [{
                    text: '登录',
                    name: 'btn_ssl_login',
                    type: 'button',
                    callback: function (sdata) {
                      bt.pub.login_btname(sdata.bt_username, sdata.bt_password, function (ret) {
                        if (ret.status) site.reload(7);
                      })
                    }
                  },
                  {
                    text: '注册宝塔账号',
                    name: 'bt_register',
                    type: 'button',
                    callback: function (sdata) {
                      window.open('https://www.bt.cn/register.html')
                    }
                  }
                  ]
                }
              ]
              for (var i = 0; i < datas.length; i++) {
                var _form_data = bt.render_form_line(datas[i]);
                robj.append(_form_data.html);
                bt.render_clicks(_form_data.clicks);
              }
              robj.append(bt.render_help(['商用证书相对于普通证书，具有更高的安全性、赔付保障和支持通配符和多域名等方式。<a class="btlink" target="_blank" href="https://www.racent.com/sectigo-ssl">点击查看</a>', '已有宝塔账号请登录绑定']));
            }
          });
        }
      },
      {
        title: '宝塔SSL',
        callback: function (robj) {
          robj = $('#webedit-con .tab-con')
          bt.pub.get_user_info(function (udata) {
            if (udata.status) {
              bt.site.get_domains(web.id, function (ddata) {
                var domains = [];
                for (var i = 0; i < ddata.length; i++) {
                  if (ddata[i].name.indexOf('*') == -1) domains.push({ title: ddata[i].name, value: ddata[i].name });
                }
                robj.append("<button name=\"btsslApply\" class=\"btn btn-success btn-sm mr5 btsslApply\">申请证书</button><div id='ssl_order_list' class=\"divtable mtb15 table-fixed-box\" style=\"max-height:340px;overflow-y: auto;\"><table id='bt_order_list' class='table table-hover'><thead><tr><th>域名</th><th>到期时间</th><th>状态</th><th>操作</th></tr></thead><tbody><tr><td colspan='4' style='text-align:center'><img style='height: 18px;margin-right:10px' src='/static/images/loading-2.gif'>正在获取订单,请稍候...</td></tr></tbody></table></div>");
                $('.btsslApply').click(function () {
                  var html = '';
                  for (var i = 0; i < domains.length; i++) {
                    var item = domains[i];
                    html += '<option value="' + item.value + '">' + item.title + '</option>';
                  }
                  bt.open({
                    type: 1,
                    title: '申请免费宝塔SSL证书',
                    area: '610px',
                    content: '<form class="bt_form perfect_ssl_info free_ssl_info" onsubmit="return false;">\
                                                    <div class="line">\
                                                        <span class="tname">证书信息</span>\
                                                        <div class="info-r">\
                                                            <span class="ssl_title">TrustAsia TLS RSA CA(免费版)</span>\
                                                        </div>\
                                                    </div>\
                                                    <div class="line">\
                                                        <span class="tname">域名</span>\
                                                        <div class="info-r"><select class="bt-input-text mr5 " name="domain" style="width:200px">' + html + '</select></div>\
                                                    </div>\
                                                    <div class="line">\
                                                        <span class="tname">个人/公司名称</span>\
                                                        <div class="info-r">\
                                                            <input type="text" class="bt-input-text mr5" name="orgName" value="" placeholder="请输入个人/公司名称，必填项" />\
                                                        </div>\
                                                    </div>\
                                                    <div class="line">\
                                                        <span class="tname">所在地区</span>\
                                                        <div class="info-r">\
                                                            <input type="text" class="bt-input-text mr5" name="orgRegion" value="" placeholder="请输入所在省份，必填项" style="width: 190px; margin-right:0;" >\
                                                            <input type="text" class="bt-input-text mr5" name="orgCity" value="" placeholder="请输入所在市/县，必填项" style="width: 190px; margin-left: 15px;"  />\
                                                        </div>\
                                                    </div>\
                                                    <div class="line">\
                                                        <span class="tname">地址</span>\
                                                        <div class="info-r">\
                                                            <input type="text" class="bt-input-text mr5" name="orgAddress" value="" placeholder="请输入个人/公司地址，必填项" />\
                                                        </div>\
                                                    </div>\
                                                    <div class="line">\
                                                        <span class="tname">手机</span>\
                                                        <div class="info-r">\
                                                            <input type="text" class="bt-input-text mr5" name="orgPhone" value="" placeholder="请输入手机号码，必填项" />\
                                                        </div>\
                                                    </div>\
                                                    <div class="line">\
                                                        <span class="tname">邮政编码</span>\
                                                        <div class="info-r">\
                                                            <input type="text" class="bt-input-text mr5" name="orgPostalCode" value="" placeholder="请输入邮政编码，必填项" />\
                                                        </div>\
                                                    </div>\
                                                    <div class="line" style="display:none;">\
                                                        <span class="tname">部门</span>\
                                                        <div class="info-r">\
                                                            <input type="text" class="bt-input-text mr5" name="orgDivision" value="总务"/>\
                                                        </div>\
                                                    </div>\
                                                    <div class="line">\
                                                        <span class="tname"></span>\
                                                        <div class="info-r">\
                                                            <span style="line-height: 20px;color:red;display: inline-block;">禁止含有诈骗、赌博、色情、木马、病毒等违法违规业务信息的站点申请SSL证书，如有违反，撤销申请，停用账号</span>\
                                                        </div>\
                                                    </div>\
                                                    <div class="line">\
                                                        <div class="info-r"><button class="btn btn-success submit_ssl_info">提交资料</button></div>\
                                                    </div>\
                                                </form>',
                    success: function (layero, index) {
                      $('.submit_ssl_info').click(function () {
                        var form = $('.free_ssl_info').serializeObject();
                        for (var key in form) {
                          if (Object.hasOwnProperty.call(form, key)) {
                            var value = form[key],
                              el = $('[name="' + key + '"]');
                            if (value == '') {
                              layer.tips(el.attr('placeholder'), el, { tips: ['1', 'red'] });
                              el.focus();
                              el.css('borderColor', 'red');
                              return false;
                            } else {
                              el.css('borderColor', '');
                            }
                            switch (key) {
                              case 'orgPhone':
                                if (!bt.check_phone(value)) {
                                  layer.tips('手机号码格式错误', el, { tips: ['1', 'red'] });
                                  el.focus();
                                  el.css('borderColor', 'red');
                                  return false;
                                }
                                break;
                              case 'orgPostalCode':
                                if (!/^[0-9]\d{5}(?!\d)$/.test(value)) {
                                  layer.tips('邮政编号格式错误', el, { tips: ['1', 'red'] });
                                  el.focus();
                                  el.css('borderColor', 'red');
                                  return false;
                                }
                                break;
                            }
                          }
                        }
                        if (form.domain.indexOf('www.') != -1) {
                          var rootDomain = form.domain.split(/www\./)[1];
                          if (!$.inArray(domains, rootDomain)) {
                            layer.msg('您为域名[' + form.domain + ']申请证书，但程序检测到您没有将其根域名[' + rootDomain + ']绑定并解析到站点，这会导致证书签发失败!', { icon: 2, time: 5000 });
                            return;
                          }
                        }
                        var loadT = bt.load('正在提交证书资料，请稍候...');
                        bt.send('ApplyDVSSL', 'ssl/ApplyDVSSL', $.extend(form, { path: web.path }), function (tdata) {
                          loadT.close();
                          if (tdata.msg.indexOf('<br>') != -1) {
                            layer.msg(tdata.msg, { time: 0, shadeClose: true, area: '600px', icon: 2, shade: .3 });
                          } else {
                            bt.msg(tdata);
                          }
                          if (tdata.status) {
                            layer.close(index);
                            site.ssl.verify_domain(tdata.data.partnerOrderId, web.name);
                          }
                        });
                      });
                      $('.free_ssl_info input').keyup(function (res) {
                        var value = $(this).val();
                        if (value == '') {
                          layer.tips($(this).attr('placeholder'), $(this), { tips: ['1', 'red'] });
                          $(this).focus();
                          $(this).css('borderColor', 'red');
                        } else {
                          $(this).css('borderColor', '');
                        }
                      });
                    }
                  });
                });
                var helps = [
                  '<span style="color:red">注意：请勿将SSL证书用于非法网站，一经发现，吊销证书</span>',
                  '申请之前，请确保域名已解析，如未解析会导致审核失败(包括根域名)',
                  '宝塔SSL申请的是免费版TrustAsia DV SSL CA - G5证书，仅支持单个域名申请',
                  '有效期1年，不支持续签，到期后需要重新申请',
                  '建议使用二级域名为www的域名申请证书,此时系统会默认赠送顶级域名为可选名称',
                  '在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点',
                  '宝塔SSL申请注意事项及教程 <a href="https://www.bt.cn/bbs/thread-33113-1-1.html" target="_blank" class="btlink"> 使用帮助</a>'
                ]
                robj.append(bt.render_help(helps));
                var loading = bt.load();
                bt.site.get_order_list(web.name, function (odata) {
                  loading.close();
                  if (odata.status === false) {
                    layer.msg(odata.msg, { icon: 2 });
                    return;
                  }
                  robj.append("<div class=\"divtable mtb15 table-fixed-box\" style=\"max-height:200px;overflow-y: auto;\"><table id='bt_order_list' class='table table-hover'></table></div>");
                  bt.render({
                    table: '#bt_order_list',
                    columns: [
                      { field: 'commonName', title: '域名' },
                      {
                        field: 'endtime',
                        width: '70px',
                        title: '到期时间',
                        templet: function (item) {
                          return bt.format_data(item.endtime, 'yyyy/MM/dd');
                        }
                      },
                      { field: 'stateName', width: '100px', title: '状态' },
                      {
                        field: 'opt',
                        align: 'right',
                        width: '100px',
                        title: '操作',
                        templet: function (item) {
                          var opt = '<a class="btlink" onclick="site.ssl.onekey_ssl(\'' + item.partnerOrderId + '\',\'' + web.name + '\')" href="javascript:;">部署</a>'
                          if (item.stateCode == 'WF_DOMAIN_APPROVAL') {
                            opt = '<a class="btlink" onclick="site.ssl.verify_domain(\'' + item.partnerOrderId + '\',\'' + web.name + '\')" href="javascript:;">验证域名</a>';
                          } else {
                            if (item.setup) opt = '已部署 | <a class="btlink" href="javascript:site.ssl.set_ssl_status(\'CloseSSLConf\',\'' + web.name + '\')">关闭</a>'
                          }
                          return opt;
                        }
                      }
                    ],
                    data: odata.data
                  })
                  bt.fixed_table('bt_order_list');
                })
              })
            } else {
              robj.append('<div class="alert alert-warning" style="padding:10px">未绑定宝塔账号，请注册绑定，绑定宝塔账号(非论坛账号)可实现一键部署SSL</div>');

              var datas = [
                { title: '宝塔账号', name: 'bt_username', value: rdata.email, width: '260px', placeholder: '请输入手机号码' },
                { title: '密码', type: 'password', name: 'bt_password', value: rdata.email, width: '260px' },
                {
                  title: ' ',
                  items: [{
                    text: '登录',
                    name: 'btn_ssl_login',
                    type: 'button',
                    callback: function (sdata) {
                      bt.pub.login_btname(sdata.bt_username, sdata.bt_password, function (ret) {
                        if (ret.status) site.reload(7);
                      })
                    }
                  },
                  {
                    text: '注册宝塔账号',
                    name: 'bt_register',
                    type: 'button',
                    callback: function (sdata) {
                      window.open('https://www.bt.cn/register.html')
                    }
                  }
                  ]
                }
              ]
              for (var i = 0; i < datas.length; i++) {
                var _form_data = bt.render_form_line(datas[i]);
                robj.append(_form_data.html);
                bt.render_clicks(_form_data.clicks);
              }
              robj.append(bt.render_help(['宝塔SSL证书为亚洲诚信证书，需要实名认证才能申请使用', '已有宝塔账号请登录绑定', '宝塔SSL申请的是TrustAsia DV SSL CA - G5 原价：1900元/1年，宝塔用户免费！', '一年满期后免费颁发']));
            }
          });
        }
      },
      {
        title: "Let's Encrypt",
        callback: function (robj) {
          acme.get_account_info(function (let_user) {
            if (let_user.status === false) {
              layer.msg(let_user.msg, { icon: 2, time: 10000 });
            }
          });
          acme.id = web.id;
          if (rdata.status && rdata.type == 1) {
            var cert_info = '';
            if (rdata.cert_data['notBefore']) {
              cert_info = '<div style="margin-bottom: 10px;" class="alert alert-success">\
                                        <p style="margin-bottom: 9px;"><span style="width: 357px;display: inline-block;"><b>已部署成功：</b>将在距离到期时间1个月内尝试自动续签</span>\
                                        <span style="margin-left: 15px;display: inline-block;overflow: hidden;text-overflow: ellipsis;white-space: nowrap;max-width: 140px;width: 140px;">\
                                        <b>证书品牌：</b>' + rdata.cert_data.issuer + '</span></p>\
                                        <span style="display:inline-block;max-width: 357px;overflow:hidden;text-overflow:ellipsis;vertical-align:-3px;white-space: nowrap;width: 357px;"><b>认证域名：</b> ' + rdata.cert_data.dns.join('、') + '</span>\
                                        <span style="margin-left: 15px;"><b>到期时间：</b> ' + rdata.cert_data.notAfter + '</span></div>'
            }
            robj.append('<div>' + cert_info + '<div><span>密钥(KEY)</span><span style="padding-left:194px">证书(PEM格式)</span></div></div>');
            var datas = [{
              items: [
                { name: 'key', width: '45%', height: '220px', type: 'textarea', value: rdata.key },
                { name: 'csr', width: '45%', height: '220px', type: 'textarea', value: rdata.csr }
              ]
            },
            {
              items: [{
                text: '关闭SSL',
                name: 'btn_ssl_close',
                hide: !rdata.status,
                type: 'button',
                callback: function (sdata) {
                  site.ssl.set_ssl_status('CloseSSLConf', web.name);
                }
              },
              {
                text: '续签',
                name: 'btn_ssl_renew',
                hide: !rdata.status,
                type: 'button',
                callback: function (sdata) {
                  site.ssl.renew_ssl(web.name, rdata.auth_type, rdata.index);
                }
              }
              ]
            }
            ]
            for (var i = 0; i < datas.length; i++) {
              var _form_data = bt.render_form_line(datas[i]);
              robj.append(_form_data.html);
              bt.render_clicks(_form_data.clicks);
            }
            robj.find('textarea').css('background-color', '#f6f6f6').attr('readonly', true);
            var helps = [
              '<span style="color:red">注意：请勿将SSL证书用于非法网站</span>',
              '申请之前，请确保域名已解析，如未解析会导致审核失败(包括根域名)',
              '宝塔SSL申请的是免费版TrustAsia DV SSL CA - G5证书，仅支持单个域名申请',
              '有效期1年，不支持续签，到期后需要重新申请',
              '建议使用二级域名为www的域名申请证书,此时系统会默认赠送顶级域名为可选名称',
              '在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点',
              '如果重新申请证书时提示【订单已存在】请登录宝塔官网删除对应SSL订单',
            ]
            robj.append(bt.render_help(['已为您自动生成Let\'s Encrypt免费证书；', '如需使用其他SSL,请切换其他证书后粘贴您的KEY以及PEM内容，然后保存即可。', '如开启后无法使用HTTPS访问，请检查安全组是否正确放行443端口']));
            return;
          }
          bt.site.get_site_domains(web.id, function (ddata) {
            var helps = [
              [
                '<span style="color:red">注意：请勿将SSL证书用于非法网站</span>',
                '<span style="color:red;">Let\'s Encrypt因更换根证书，部分老旧设备访问时可能提示不可信，考虑购买<a class="btlink" onclick="$(\'#ssl_tabs span\').eq(0).click();">[商用SSL证书]</a></span>',
                '申请之前，请确保域名已解析，如未解析会导致审核失败',
                'Let\'s Encrypt免费证书，有效期3个月，支持多域名。默认会自动续签',
                '若您的站点使用了CDN或301重定向会导致续签失败',
                '在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点',
                '如开启后无法使用HTTPS访问，请检查安全组是否正确放行443端口'
              ],
              [
                '<span style="color:red">注意：请勿将SSL证书用于非法网站</span>',
                '在DNS验证中，我们提供了多种自动化DNS-API，并提供了手动模式',
                '使用DNS接口申请证书可自动续期，手动模式下证书到期后需重新申请',
                '使用【DnsPod/阿里云DNS】等接口前您需要先在弹出的窗口中设置对应接口的API',
                '如开启后无法使用HTTPS访问，请检查安全组是否正确放行443端口'
              ]
            ]
            var datas = [{
              title: '验证方式',
              items: [{
                name: 'check_file',
                text: '文件验证',
                type: 'radio',
                callback: function (obj) {
                  $('.checks_line').remove()
                  $(obj).siblings().removeAttr('checked');

                  $('.help-info-text').html($(bt.render_help(helps[0])));
                  //var _form_data = bt.render_form_line({ title: ' ', class: 'checks_line label-input-group', items: [{ name: 'force', type: 'checkbox', value: true, text: '提前校验域名(提前发现问题,减少失败率)' }] });
                  //$(obj).parents('.line').append(_form_data.html);

                  $('#ymlist li input[type="checkbox"]').each(function () {
                    if ($(this).val().indexOf('*') >= 0) {
                      $(this).parents('li').hide();
                    }
                  })
                }
              },
              {
                name: 'check_dns',
                text: 'DNS验证(支持通配符)',
                type: 'radio',
                callback: function (obj) {
                  $('.checks_line').remove();
                  $(obj).siblings().removeAttr('checked');
                  $('.help-info-text').html($(bt.render_help(helps[1])));
                  $('#ymlist li').show();

                  var arrs_list = [],
                    arr_obj = {};
                  bt.site.get_dns_api(function (api) {
                    site.dnsapi = {}

                    for (var x = 0; x < api.length; x++) {
                      site.dnsapi[api[x].name] = {}
                      site.dnsapi[api[x].name].s_key = "None"
                      site.dnsapi[api[x].name].s_token = "None"
                      if (api[x].data) {
                        site.dnsapi[api[x].name].s_key = api[x].data[0].value
                        site.dnsapi[api[x].name].s_token = api[x].data[1].value
                      }
                      arrs_list.push({ title: api[x].title, value: api[x].name });
                      arr_obj[api[x].name] = api[x];
                    }

                    var data = [{
                      title: '选择DNS接口',
                      class: 'checks_line',
                      items: [{
                        name: 'dns_select',
                        width: '120px',
                        type: 'select',
                        items: arrs_list,
                        callback: function (obj) {
                          var _val = obj.val();
                          $('.set_dns_config').remove();
                          var _val_obj = arr_obj[_val];
                          var _form = {
                            title: '',
                            area: '530px',
                            list: [],
                            btns: [{ title: '关闭', name: 'close' }]
                          };

                          var helps = [];
                          if (_val_obj.data !== false) {
                            _form.title = '设置【' + _val_obj.title + '】接口';
                            helps.push(_val_obj.help);
                            var is_hide = true;
                            for (var i = 0; i < _val_obj.data.length; i++) {
                              _form.list.push({ title: _val_obj.data[i].name, name: _val_obj.data[i].key, value: _val_obj.data[i].value })
                              if (!_val_obj.data[i].value) is_hide = false;
                            }
                            _form.btns.push({
                              title: '保存',
                              css: 'btn-success',
                              name: 'btn_submit_save',
                              callback: function (ldata, load) {
                                bt.site.set_dns_api({ pdata: JSON.stringify(ldata) }, function (ret) {
                                  if (ret.status) {
                                    load.close();
                                    robj.find('input[type="radio"]:eq(0)').trigger('click')
                                    robj.find('input[type="radio"]:eq(1)').trigger('click')
                                  }
                                  bt.msg(ret);
                                })
                              }
                            })
                            if (is_hide) {
                              obj.after('<button class="btn btn-default btn-sm mr5 set_dns_config">设置</button>');
                              $('.set_dns_config').click(function () {
                                var _bs = bt.render_form(_form);
                                $('div[data-id="form' + _bs + '"]').append(bt.render_help(helps));
                              })
                            } else {
                              var _bs = bt.render_form(_form);
                              $('div[data-id="form' + _bs + '"]').append(bt.render_help(helps));
                            }
                          }
                        }
                      },]
                    }, {
                      title: ' ',
                      class: 'checks_line label-input-group',
                      items: [
                        { css: 'label-input-group ptb10', text: '自动组合泛域名', name: 'app_root', type: 'checkbox' }
                      ]
                    }]
                    for (var i = 0; i < data.length; i++) {
                      var _form_data = bt.render_form_line(data[i]);
                      $(obj).parents('.line').append(_form_data.html)
                      bt.render_clicks(_form_data.clicks);
                    }
                  })
                }
              },
              ]
            }]

            for (var i = 0; i < datas.length; i++) {
              var _form_data = bt.render_form_line(datas[i]);
              robj.append(_form_data.html);
              bt.render_clicks(_form_data.clicks);
            }
            var _ul = $('<ul id="ymlist" class="domain-ul-list"></ul>');
            var _ul_html = '';
            for (var i = 0; i < ddata.domains.length; i++) {
              if (ddata.domains[i].binding === true) continue;
              _ul_html += '<li class="checked_default" style="cursor: pointer;"><input class="checkbox-text" type="checkbox" value="' + ddata.domains[i].name + '">' + ddata.domains[i].name + '</li>';
            }
            if (_ul_html) {
              _ul.append('<li class="checked_all" style="cursor: pointer;"><input class="checkbox-text" type="checkbox">全选</li>');
              _ul.append(_ul_html);
            }
            var _line = $("<div class='line mtb10'></div>");
            _line.append('<span class="tname text-center">域名</span>');
            _line.append(_ul);
            robj.append(_line);
            robj.find('input[type="radio"]').parent().addClass('label-input-group ptb10');
            // 判断是否全选
            var getSelectAll = function () {
              var count = 0;
              var total = 0;
              $('#ymlist .checked_default').each(function () {
                var checked = $(this).find('input').prop('checked');
                checked && count++;
                total++;
              });
              $('#ymlist .checked_all').find('input').prop('checked', count == total);
            };
            // 设置选中框
            var setCheckedDefault = function (checked) {
              $('#ymlist .checked_default').each(function () {
                $(this).find('input').prop('checked', checked);
              });
            }
            // 点击选择框
            $('#ymlist li').click(function () {
              var o = $(this).find('input');
              var checked = o.prop('checked');
              checked = !checked;
              o.prop('checked', checked);
            });
            // 阻止冒泡事件
            $('#ymlist li input').click(function (e) {
              e.stopPropagation();
            });
            // 点击默认选中框
            $('#ymlist .checked_default').click(function (e) {
              getSelectAll();
            });
            $('#ymlist .checked_default input').click(function (e) {
              getSelectAll();
            });
            // 点击全选
            $('#ymlist .checked_all').click(function (e) {
              var checked = $(this).find('input').prop('checked');
              setCheckedDefault(checked);
            });
            $('#ymlist .checked_all input').click(function (e) {
              var checked = $(this).prop('checked');
              setCheckedDefault(checked);
            });
            var _btn_data = bt.render_form_line({
              title: ' ',
              text: '申请',
              name: 'letsApply',
              type: 'button',
              callback: function (ldata) {
                ldata['domains'] = [];
                $('#ymlist .checked_default input[type="checkbox"]:checked').each(function () {
                  ldata['domains'].push($(this).val())
                })

                var auth_type = 'http'
                var auth_to = web.id
                var auto_wildcard = '0'
                if (ldata.check_dns) {
                  auth_type = 'dns'
                  auth_to = 'dns'
                  auto_wildcard = ldata.app_root ? '1' : '0'
                  if (ldata.dns_select !== auth_to) {
                    if (!site.dnsapi[ldata.dns_select].s_key) {
                      layer.msg("指定dns接口没有设置密钥信息");
                      return;
                    }
                    auth_to = ldata.dns_select + "|" + site.dnsapi[ldata.dns_select].s_key + "|" + site.dnsapi[ldata.dns_select].s_token;
                  }
                }
                if (ldata.domains.length <= 0) {
                  layer.msg('至少需要有一个域名', { icon: 2 });
                  return;
                }
                acme.apply_cert(ldata['domains'], auth_type, auth_to, auto_wildcard, function (res) {
                  site.ssl.ssl_result(res, auth_type, web.name);
                })

              }
            });
            robj.append(_btn_data.html);
            bt.render_clicks(_btn_data.clicks);

            robj.append(bt.render_help(helps[0]));
            robj.find('input[type="radio"]:eq(0)').trigger('click');
          })
        }
      },
      {
        title: "其他证书",
        callback: function (robj) {
          robj = $('#webedit-con .tab-con')
          var cert_info = '';
          if (rdata.cert_data['notBefore']) {
            cert_info = '<div style="margin-bottom: 10px;" class="alert alert-success">\
                                        <p style="margin-bottom: 9px;"><span style="width: 357px;display: inline-block;">' + (rdata.status ? '<b>已部署成功：</b>请在证书到期之前更换新的证书' : '<b style="color:red;">当前未部署：</b>请点击【保存】按钮完成此证书的部署') + '</span>\
                                        <span style="margin-left: 20px;display: inline-block;overflow: hidden;text-overflow: ellipsis;white-space: nowrap;width: 220px;">\
                                        <b>证书品牌：</b>' + rdata.cert_data.issuer + '</span></p>\
                                        <span style="display:inline-block;max-width: 357px;overflow:hidden;text-overflow:ellipsis;vertical-align:-3px;white-space: nowrap;width: 357px;"><b>认证域名：</b> ' + rdata.cert_data.dns.join('、') + '</span>\
                                        <span style="margin-left: 20px;"><b>到期时间：</b> ' + rdata.cert_data.notAfter + '</span></div>'
          }
          robj.append('<div>' + cert_info + '<div><span style="width: 45%;display: inline-block;margin-right: 20px;">密钥(KEY)</span><span  style="width: 45%;display: inline-block;margin-right: 20px;">证书(PEM格式)</span></div></div>');
          var datas = [{
            items: [
              { name: 'key', width: '45%', height: '260px', type: 'textarea', value: rdata.key },
              { name: 'csr', width: '45%', height: '260px', type: 'textarea', value: rdata.csr }
            ]
          },
          {
            items: [{
              text: '保存',
              name: 'btn_ssl_save',
              type: 'button',
              callback: function (sdata) {
                var form = { type: rdata.type, siteName: rdata.siteName, key: $('[name="key"]').val(), csr: $('[name="csr"]').val() }
                bt.site.set_ssl(web.name, form, function (ret) {
                  if (ret.status) site.reload(7);
                  bt.msg(ret);
                })
              }
            },
            {
              text: '关闭SSL',
              name: 'btn_ssl_close',
              hide: !rdata.status,
              type: 'button',
              callback: function (sdata) {
                site.ssl.set_ssl_status('CloseSSLConf', web.name);
              }
            }
            ]
          }
          ]
          for (var i = 0; i < datas.length; i++) {
            var _form_data = bt.render_form_line(datas[i]);
            robj.append(_form_data.html);
            bt.render_clicks(_form_data.clicks);
          }
          var helps = [
            '粘贴您的*.key以及*.pem内容，然后保存即可<a href="http://www.bt.cn/bbs/thread-704-1-1.html" class="btlink" target="_blank">[帮助]</a>。',
            '如果浏览器提示证书链不完整,请检查是否正确拼接PEM证书',
            'PEM格式证书 = 域名证书.crt + 根证书(root_bundle).crt',
            '在未指定SSL默认站点时,未开启SSL的站点使用HTTPS会直接访问到已开启SSL的站点',
            '如开启后无法使用HTTPS访问，请检查安全组是否正确放行443端口'
          ]
          robj.append(bt.render_help(helps));

        }
      },
      {
        title: "关闭",
        callback: function (robj) {
          robj = $('#webedit-con .tab-con')
          if (rdata.type == -1) {
            robj.html("<div class='mtb15' style='line-height:30px'>" + lan.site.ssl_help_1 + "</div>");
            return;
          };
          var txt = '';
          switch (rdata.type) {
            case 1:
              txt = "Let's Encrypt";
              break;
            case 0:
              txt = '其他证书';
              break;
            case 2:
              txt = lan.site.bt_ssl;
              break;
            case 3:
              txt = 'Comodo Positive';
              break;
          }
          $("#webedit-con .tab-con").html("<div class='line mtb15'>" + lan.get('ssl_enable', [txt]) + "</div><div class='line mtb15'><button class='btn btn-success btn-sm' onclick=\"site.ssl.set_ssl_status('CloseSSLConf','" + web.name + "')\">" + lan.site.ssl_close + "</button></div>");

        }
      },
      {
        title: "证书夹",
        callback: function (robj) {
          robj = $('#webedit-con .tab-con')
          robj.html("<div class='divtable' style='height:510px;'><table id='cer_list_table' class='table table-hover'></table></div>");
          bt.site.get_cer_list(function (rdata) {
            bt.render({
              table: '#cer_list_table',
              columns: [{
                field: 'subject',
                title: '域名',
                templet: function (item) {
                  return item.dns.join('<br>')
                }
              },
              { field: 'notAfter', width: '83px', title: '到期时间' },
              { field: 'issuer', width: '150px', title: '品牌' },
              {
                field: 'opt',
                width: '75px',
                align: 'right',
                title: '操作',
                templet: function (item) {
                  var opt = '<a class="btlink" onclick="bt.site.set_cert_ssl(\'' + item.subject + '\',\'' + web.name + '\',function(rdata){if(rdata.status){site.ssl.reload(2);}})" href="javascript:;">部署</a> | ';
                  opt += '<a class="btlink" onclick="bt.site.remove_cert_ssl(\'' + item.subject + '\',function(rdata){if(rdata.status){site.ssl.reload(4);}})" href="javascript:;">删除</a>'
                  return opt;
                }
              }
              ],
              data: rdata
            })
          })
        }
      }
      ]
      bt.render_tab('ssl_tabs', _tabs);
      $('#ssl_tabs').append('<div class="ss-text pull-right mr30" style="position: relative;top:-4px"><em>强制HTTPS</em><div class="ssh-item"><input class="btswitch btswitch-ios" id="toHttps" type="checkbox"><label class="btswitch-btn" for="toHttps"></label></div></div>');
      var ssl_open = $("#toHttps")
      ssl_open.attr('checked', rdata.httpTohttps);
      ssl_open.click(function (sdata) {
        var isHttps = $("#toHttps").is(':checked');
        if (!isHttps) {
          layer.confirm('关闭强制HTTPS后需要清空浏览器缓存才能看到效果,继续吗?', { 
            icon: 3, 
            title: "关闭强制HTTPS",
            cancel:function () { 
              ssl_open.prop('checked', !isHttps);
            }
        }, function () {
            bt.site.close_http_to_https(web.name, function (rdata) {
              if (rdata.status) {
                setTimeout(function () {
                  site.reload(7);
                }, 3000);
              }
            })
          },function () {
            ssl_open.attr('checked', !isHttps);
          });
        } else {
          bt.site.set_http_to_https(web.name, function (rdata) {
            if (!rdata.status) {
              ssl_open.prop('checked', !isHttps);
              setTimeout(function () {
                site.reload(7);
              }, 3000);
            }
          })
        }
      })
      switch (rdata.type) {
        case 0: // 其他证书
          $('#ssl_tabs span:eq(3)').trigger('click');
          break;
        case 1: // Let's Encrypt
          $('#ssl_tabs span:eq(2)').trigger('click');
          break;
        case 2: // 宝塔证书
          $('#ssl_tabs span:eq(1)').trigger('click');
          break;
        default: // 商用证书或其他证书
          $('#ssl_tabs span:eq(0)').trigger('click');
          break;
      }
    });
  },
}

$('#cutMode .tabs-item[data-type="' + (bt.get_cookie('site_model') || 'php') + '"]').trigger('click');

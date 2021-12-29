var bt_tools = {

  commandConnectionPool: {}, //ws连接池
  /**
   * @description 表格渲染
   * @param {object} config  配置对象 参考说明
   * @return 当前实例对象
   */
  table: function (config) {
    var that = this;
    function ReaderTable (config) {
      this.config = config;
      this.$load();
    }
    ReaderTable.prototype = {
      style_list: [], // 样式列表
      event_list: {}, // 事件列表,已绑定事件
      checkbox_list: [], // 元素选中列表
      batch_active: {},
      event_rows_model: {}, // 事件行内元素模型，行内元素点击都会将数据临时存放
      data: [],
      page: '',
      column: [],
      batch_thread: [],
      random: bt.get_random(5),
      init: false, // 是否初始化渲染
      checked: false, // 是否激活，用来判断是否失去焦点
      /**
       * @description 加载数据
       * @return void
       */
      $load: function () {
        var _that = this;
        if (this.config.init) this.config.init(this);
        $(this.config.el).addClass('bt_table');
        if (this.config.minWidth) this.style_list.push({
          className: this.config.el + ' table',
          css: ('min-width:' + this.config.minWidth)
        });
        if (this.config.tootls) {
          this.$reader_tootls(this.config.tootls);
        } else {
          if ($(_that.config.el + '.divtable').length === 0) $(_that.config.el).append('<div class="divtable mtb10" style="max-height:' + (this.config.height || 'auto') + '"></div>');
        }
        this.$reader_content();
        if (_that.config.url !== undefined) {
          this.$refresh_table_list(_that.config.load || false);
        } else if (this.config.data !== undefined) {
          this.$reader_content(this.config.data);
        } else {
          alert('缺少data或url参数');
        }
        if (this.config.methods) { //挂载实例方法
          $.extend(this, this.config.methods);
        }
        if (this.config.height) bt_tools.$fixed_table_thead(this.config.el + ' .divtable')
      },

      /**
       * @description 刷新表格数据
       * @param {boolean} load
       * @param {function} callback 回调函数
       * @return void
      */
      $refresh_table_list: function (load, callback) {
        var _that = this, loadT;
        if (load) loadT = bt_tools.load('获取列表数据');
        this.$http(function (data) {
          if (loadT) loadT.close();
          if (callback) callback(data);
          _that.$reader_content(data.data, typeof data.total != "undefined" ? parseInt(data.total) : data.page);
        });
      },

      /**
       * @description 渲染内容
       * @param {object} data 渲染的数据
       * @param {number} page 数据分页/总数
       * @return void
       */
      $reader_content: function (data, page) {
        var _that = this, thead = '', tbody = '', i = 0, column = this.config.column, event_list = {}, checkbox = $(_that.config.el + ' .checkbox_' + _that.random);
        data = data || [];
        this.data = data;
        if (checkbox.length) {
          checkbox.removeClass('active selected');
          _that.checkbox_list = [];
          _that.$set_batch_view();
        }
        do {
          var rows = data[i],
            completion = 0;
          if (data.length > 0) tbody += '<tr>';
          for (var j = 0; j < column.length; j++) {
            var item = column[j];
            if ($.isEmptyObject(item)) {
              completion++;
              continue;
            }
            if (i === 0 && !this.init) {
              if (!this.init) this.style_list.push(this.$dynamic_merge_style(item, j - completion));
              var sortName = 'sort_' + this.random + '',
                checkboxName = 'checkbox_' + this.random,
                sortValue = item.sortValue || 'desc';
              thead += '<th><span ' + (item.sort ? 'class="not-select ' + sortName + (item.sortValue ? ' sort-active' : '') + ' cursor-pointer"' : '') + ' data-index="' + j + '" ' + (item.sort ? 'data-sort="' + sortValue + '"' : '') + '>' + (item.type == "checkbox" ? '<label><i class="cust—checkbox cursor-pointer ' + checkboxName + '" data-checkbox="all"></i><input type="checkbox" class="cust—checkbox-input"></label>' : '<span>' + item.title + '</span>') + (item.sort ? '<span class="glyphicon glyphicon-triangle-' + (sortValue == 'desc' ? 'bottom' : 'top') + ' ml5"></span>' : '') + '</span></th>';
              if (i === 0) {
                if (!event_list[sortName] && item.sort) event_list[sortName] = {
                  event: this.config.sortEvent,
                  eventType: 'click',
                  type: 'sort'
                };
                if (!event_list[checkboxName]) event_list[checkboxName] = {
                  event: item.checked,
                  eventType: 'click',
                  type: 'checkbox'
                };
              }
            }
            if (rows !== undefined) {
              var template = '', className = 'event_' + item.fid + '_' + this.random;
              if (item.template) {
                template = _that.$custom_template_render(item, rows, j);
              }
              if (typeof template === "undefined" || typeof item.template === "undefined") {
                template = this.$reader_column_type(item, rows);
                event_list = $.extend(event_list, template[1]);
                template = template[0];
              }
              var fixed = false;
              if (typeof item.fixed != "undefined" && item.fixed) {
                if (typeof item.class != "undefined") {
                  if (item.class.indexOf('fixed') === -1) item.class += ' fixed';
                } else {
                  item.class = 'fixed';
                }
                fixed = true;
              }
              tbody += '<td><span ' + (fixed ? 'style="width:' + (item.width - 16) + 'px" title="' + template + '"' : ' ') + (item['class'] ? 'class="' + item['class'] + '"' : '') + ' ' + (item.tips ? 'title="' + item.tips + '"' : '') + '>' + template + '</span></td>'; if (i === 0) {
                if (!event_list[className] && item.event) event_list[className] = {
                  event: item.event,
                  eventType: 'click',
                  type: 'rows'
                };
              }
            }
          }
          if (data.length > 0) tbody += '</tr>'
          if (data.length == 0) tbody += '<tr><td colspan="' + column.length + '" style="text-align:center;">' + (this.config['default'] || '数据为空') + '</td></tr>';
          i++;
        } while (i < data.length);
        if (!this.init) this.$style_bind(this.style_list);
        this.$event_bind(event_list);
        if (!this.init) {
          $(this.config.el + ' .divtable').append('<table class="table table-hover"><thead style="position: relative;z-index: 1;">' + thead + '</thead><tbody>' + tbody + '</tbody></table></div></div>');
        } else {
          $(this.config.el + ' .divtable tbody').html(tbody);
          if (this.config.page) {
            $(this.config.el + ' .page').replaceWith(this.$reader_page(this.config.page, page));
          }
        }
        this.init = true;
        if (this.config.success) this.config.success(this);
      },
      /**
       * @description 自定模板渲染
       * @param {object} item 当前元素模型
       * @param {object} rows 当前元素数据
       * @param {number} j 当前模板index
       * @return void
       */
      $custom_template_render: function (item, rows, j) {
        var className = 'event_' + item.fid + '_' + this.random,
          _template = item.template(rows, j),
          $template = $(_template);
        if ($template.length > 0) {
          template = $template.addClass(className)[0].outerHTML;
        } else {
          if (item.type === 'text') {
            template = '<span class="' + className + ' ' + item['class'] + '">' + _template + '</span>';
          } else {
            template = '<a href="javascript:;" class="btlink ' + className + '">' + _template + '</a>';
          }
        }
        return template;
      },

      /**
       * @description 替换table数据
       * @param {string} newValue 内容数据
       * @return void
       */
      $modify_row_data: function (newValue) {
        this.event_rows_model.rows = $.extend(this.event_rows_model.rows, newValue);
        var row_model = this.event_rows_model, template = null;
        if (typeof row_model.model.template != 'undefined') {
          template = $(this.$custom_template_render(row_model.model, row_model.rows, row_model.index));
          if (!template.length) template = $(this.$reader_column_type(row_model.model, row_model.rows)[0]);
        } else {
          template = $(this.$reader_column_type(row_model.model, row_model.rows)[0]);
        }
        if (row_model.model.type == 'group') {
          $(row_model.el).parent().empty().append(template);
        } else {
          row_model.el.replaceWith(template);
        }
        row_model.el = template;
      },

      /**
       * @description 批量执行程序
       * @param {object} config 配置文件
       * @return void
       */
      $batch_success_table: function (config) {
        var _that = this, length = $(config.html).length;
        bt.open({
          type: 1,
          title: config.title,
          area: config.area || ['350px', '350px'],
          shadeClose: false,
          closeBtn: 2,
          content: config.content || '<div class="batch_title"><span class><span class="batch_icon"></span><span class="batch_text">' + config.title + '操作完成！</span></span></div><div class="' + (length > 4 ? 'fiexd_thead' : '') + ' batch_tabel divtable" style="margin: 15px 30px 15px 30px;overflow: auto;height: 200px;"><table class="table table-hover"><thead><tr><th>' + config.th + '</th><th style="text-align:right;width:120px;">操作结果</th></tr></thead><tbody>' + config.html + '</tbody></table></div>',
          success: function () {
            if (length > 4) _that.$fixed_table_thead('.fiexd_thead');
          }
        });
      },

      /**
       * @description 删除行内数据
       */
      $delete_table_row: function (index) {
        this.data.splice(index, 1)
        this.$reader_content(this.data);
      },


      /**
       * @description 设置批量操作显示
       * @return void 无
       */
      $set_batch_view: function () {
        if (typeof this.config.batch != "undefined") { //判断是否存在批量操作
          var bt_select_btn = $(this.config.el + ' .set_batch_option');
          if (typeof this.config.batch.config != "undefined") { // 判断批量操作是多个还是单个
            if (this.checkbox_list.length > 0) {
              bt_select_btn.removeClass('bt-disabled btn-default').addClass('btn-success').text('批量' + this.batch_active.title + '(已选中' + this.checkbox_list.length + ')')
            } else {
              bt_select_btn.addClass('bt-disabled btn-default').removeClass('btn-success').text('批量' + this.batch_active.title);
            }
          } else {
            var bt_select_val = $(this.config.el + ' .bt_table_select_group .bt_select_value');
            if (this.checkbox_list.length > 0) {
              bt_select_btn.removeClass('bt-disabled btn-default').addClass('btn-success').prev().removeClass('bt-disabled');
              bt_select_val.find('em').html('(已选中' + this.checkbox_list.length + ')');
            } else {
              bt_select_btn.addClass('bt-disabled btn-default').removeClass('btn-success').prev().addClass('bt-disabled');
              bt_select_val.children().eq(0).html('请选择批量操作<em></em>');
              bt_select_val.next().find('li').removeClass('active');
              this.batch_active = {};
            }
          }
        }
      },

      /**
       * @description 渲染指定类型列内容
       * @param {object} data 渲染的数据
       * @param {object} rows 渲染的模板
       * @return void
       */
      $reader_column_type: function (item, rows) {
        var value = rows[item.fid], event_list = {}, className = 'click_' + item.fid + '_' + this.random, config = [], _that = this;
        switch (item.type) {
          case 'text': //普通文本
            config = [value, event_list];
            break;
          case 'checkbox': //单选内容
            config = ['<label><i class="cust—checkbox cursor-pointer checkbox_' + this.random + '"></i><input type="checkbox" class="cust—checkbox-input"></label>', event_list];
            break;
          case 'password':
            var _copy = '',
              _eye_open = '',
              className = 'ico_' + _that.random + '_',
              html = '<span class="bt-table-password mr10"><i>**********</i></span>'
            if (item.eye_open) {
              html += '<span class="glyphicon cursor pw-ico glyphicon-eye-open mr10 ' + className + 'eye_open" title="显示密码"></span>';
              if (!event_list[className + 'eye_open']) event_list[className + 'eye_open'] = {
                type: 'eye_open_password'
              };
            }
            if (item.copy) {
              html += '<span class="ico-copy cursor btcopy mr10 ' + className + 'copy" title="复制密码"></span>'
              if (!event_list[className + 'copy']) event_list[className + 'copy'] = {
                type: 'copy_password'
              };
            }
            config = [html, event_list];
            break;
          case 'link': //超链接类型
            className += '_' + item.fid
            if (!event_list[className] && item.event) event_list[className] = {
              event: item.event,
              type: 'rows'
            };
            config = ['<a class="btlink ' + className + '" href="' + (item.href ? value : 'javascript:;') + '" ' + (item.href ? ('target="' + (item.target || '_blank') + '"') : '') + ' title="' + value + '">' + value + '</a>', event_list];
            break;
          case 'input': //可编辑类型
            blurName = 'blur_' + item.fid + '_' + this.random;
            keyupName = 'keyup_' + item.fid + '_' + this.random;
            if (!event_list[blurName] && item.blur) event_list[blurName] = {
              event: item.blur,
              eventType: 'blur',
              type: 'rows'
            };
            if (!event_list[keyupName] && item.keyup) event_list[keyupName] = {
              event: item.keyup,
              eventType: 'keyup',
              type: 'rows'
            };
            config = ['<input type="text" title="点击编辑内容，按回车或失去焦点自动保存"  class="table-input ' + blurName + ' ' + keyupName + '" data-value="' + value + '" value="' + value + '" />', event_list];
            break;
          case 'status': // 状态类型
            var active = '';
            $.each(item.config.list, function (index, items) {
              if (items[0] === value) active = items;
            });
            if (!event_list[className] && item.event) event_list[className] = {
              event: item.event,
              type: 'rows'
            };
            config = ['<a class="btlink ' + className + ' ' + (active[2].indexOf('#') > -1 ? '' : active[2]) + '" style="' + (active[2].indexOf('#') > -1 ? ('color:' + active[2] + ';') : '') + '" href="javascript:;"><span>' + active[1] + '</span>' + (item.config.icon ? '<span class="glyphicon ' + active[3] + '"></span>' : '') + '</a>', event_list];
            break;
          case 'switch': //开关类型
            var active = '', _random = bt.get_random(5);
            active = new Number(value) == true ? 'checked' : ''
            if (!event_list[className] && item.event) event_list[className] = {
              event: item.event,
              type: 'rows'
            };
            config = ['<div class="switch_group"><input class="btswitch btswitch-ios ' + className + '" id="' + _random + '" type="checkbox" ' + active + '><label class="btswitch-btn" for="' + _random + '" data-index="0" bt-event-click="set_site_server_status"></label></div>', event_list];
            break;
          case 'group':
            var _html = '';
            $.each(item.group, function (index, items) {
              className = (item.fid ? item.fid : 'group') + '_' + index + '_' + _that.random;
              var _hide = false;
              if (items.template) {
                var _template = items.template(rows, _that),
                  $template = $(_template);
                if ($template.length > 0) {
                  _html += $template.addClass(className)[0].outerHTML
                } else {
                  _html += '<a href="javascript:;" class="btlink ' + className + '" title="' + (items.title || '') + '">' + _template + '</a>';
                }
              } else {
                if (typeof items.hide != "undefined") {
                  _hide = typeof items.hide === "boolean" ? items.hide : items.hide(rows);
                  if (typeof _hide != "boolean") return false;
                }
                _html += '<a href="javascript:;" class="btlink ' + className + '" ' + (_hide ? 'style="display:none;"' : '') + ' title="' + (items.tips || items.title) + '">' + items.title + '</a>';
              }
              //当前操作按钮长度等于当前所以值时不向后添加分割
              if (!_hide) _html += ((item.group.length == (index + 1)) ? '' : '&nbsp;&nbsp;|&nbsp;&nbsp;')
              if (!event_list[className] && items.event) event_list[className] = {
                event: items.event,
                type: 'rows'
              };
            });
            config = [_html, event_list];
            break;
          default:
            config = [value, event_list];
            break;
        }
        return config;
      },
      /**
       * @description 批量执行程序
       * @param {object} config 配置文件
       * @return void
      */
      $batch_success_table: function (config) {
        that.$batch_success_table(config);
      },
      /**
       * @description 渲染工具条
       * @param {object} data 配置参数
       * @return void
       */
      $reader_tootls: function (config) {
        var _that = this, event_list = {};
        /**
         * @description 请求方法
         * @param {Function} callback 回调函数
         * @returns void
         */
        function request (active, check_list) {
          var loadT = bt.load('正在执行批量' + active.title + '，请稍候...'),
            batch_config = {},
            list = _that.$get_data_batch_list(active.paramId, check_list);
          if (!active.beforeRequest) {
            batch_config[active.paramName] = list.join(',');
          } else {
            batch_config[active.paramName] = active.beforeRequest(check_list);
          }
          bt_tools.send({
            url: active.url || _that.config.batch.url,
            data: $.extend(active.param || {}, batch_config)
          }, function (res) {
            loadT.close();
            if (res.status === false && typeof res.success === "undefined") {
              bt_tools.msg(res);
              return false;
            }
            if (typeof active.tips === 'undefined' || active.tips) {
              var html = '';
              $.each(res.error, function (key, item) {
                html += '<tr><td><span class="text-overflow" title="' + key + '">' + key + '</span/></td><td><div style="float:right;" class="size_ellipsis"><span style="color:red">' + item + '</span></div></td></tr>';
              });
              $.each(res.success, function (index, item) {
                html += '<tr><td><span class="text-overflow" title="' + item + '">' + item + '</span></td><td><div style="float:right;" class="size_ellipsis"><span style="color:#20a53a">操作成功</span></div></td></tr>';
              });
              _that.$batch_success_table({
                title: '批量' + active.title,
                th: active.theadName,
                html: html
              });
              if (active.refresh) _that.$refresh_table_list(true);
            } else {
              if (!active.success) {
                var html = '';
                $.each(check_list, function (index, item) {
                  html += '<tr><td><span class="text-overflow" title="' + item.name + '">' + item.name + '</span></td><td><div style="float:right;"><span style="color:' + (res.status ? '#20a53a' : 'red') + '">' + ((typeof active.theadValue != 'undefined' ? active.theadValue[res.status ? 0 : 1] : null) || res.msg) + '</span></div></td></tr>';
                });
                _that.$batch_success_table({ title: '批量' + active.title + '完成', th: active.theadName, html: html });
                if (active.refresh) _that.$refresh_table_list(true);
              }
            }
            if (active.success) {
              active.success(res, check_list, _that);
            }
          });
        }
        /**
         * @description 执行批量，包含递归批量和自动化批量
         * @returns void
         */
        function execute_batch (active, check_list, success) {
          // if(active.recursion) 递归方式
          var bacth = {
            loadT: 0,
            config: {},
            check_list: check_list,
            bacth_status: true,
            start_batch: function (param, callback) {
              var _this = this;
              if (typeof param == "undefined") param = {};
              if (typeof param == 'function') callback = param, param = {};
              if (active.load) this.loadT = layer.msg('正在执行批量' + active.title + '，<span class="batch_progress">进度:0/' + this.check_list.length + '</span>,请稍候...', {
                icon: 16,
                skin: 'batch_tips',
                shade: .3,
                time: 0,
                area: '400px'
              })
              this.config = {
                param: param,
                url: active.url
              };
              this.bacth(callback);
            },
            /**
             *
             * @param {Number} index 递归批量程序
             * @param {Function} callback 回调函数
             * @return void(0)
             */
            bacth: function (index, callback) {
              var _this = this, param = {};
              if (typeof index === "function" || typeof index === "undefined") callback = index, index = 0;
              if (index < this.check_list.length) {
                "function" == typeof active.url ? this.config.url = active.url(check_list[index]) : this.config.url = active.url;
                if (typeof active.param == "function") {
                  param = active.param(check_list[index]);
                } else {
                  param = active.param;
                }
                this.config.param = $.extend(this.config.param, param);
                if (typeof active.paramId != 'undefined') _this.config.param[active.paramName || active.paramId] = _this.check_list[index][active.paramId];
                if (typeof active.beforeBacth != 'undefined') this.config.param = $.extend(this.config.param, active.beforeBacth(_this.check_list[index]));
                if (this.config.param['bacth'] && index == this.check_list.length - 1) {
                  delete this.config.param['bacth'];
                }
                if (!_this.bacth_status) return false;
                if (active.load) $('#layui-layer' + _this.loadT).find('.layui-layer-content').html('<i class="layui-layer-ico layui-layer-ico16"></i>正在执行批量' + active.title + '，<span class="batch_progress">进度:' + index + '/' + _this.check_list.length + '</span>，请稍候...' + (active.clear ? '<a href="javascript:;" class="btlink clear_batch" style="margin-left:20px;">取消</a>' : ''));
                bt_tools.send({
                  url: this.config.url,
                  data: this.config.param,
                  bacth: true,
                }, function (res) {
                  $.extend(_this.check_list[index], {
                    request: {
                      status: typeof res.status === "boolean" ? res.status : false,
                      msg: res.msg || '请求网络错误'
                    }
                  }, { requests: res });
                  index++;
                  _this.bacth(index, callback);
                });
              } else {
                if (success) success();
                if (callback) {
                  callback(this.check_list);
                }
                if (active.automatic) {
                  var html = '';
                  for (var i = 0; i < this.check_list.length; i++) {
                    var item = this.check_list[i];
                    html += '<tr><td>' + (typeof item[active.paramThead] != "undefined" ? item[active.paramThead] : item.name) + '</td><td><div style="float:right;"><span style="color:' + (item.request.status ? '#20a53a' : 'red') + '">' + item.request.msg + '</span></div></td></tr>';
                  }
                  _that.$batch_success_table({ title: '批量' + active.title, th: active.theadName, html: html });
                  if (active.refresh) _that.$refresh_table_list(true);
                  _that.$clear_table_checkbox();
                }
                layer.close(this.loadT);
              }
            },
            clear_bacth: function () {
              this.bacth_status = false;
              layer.close(this.loadT);
            }
          }
          if (active.callback) {
            active.callback(bacth);
          } else {
            if (!active.confirm || active.recursion) {
              if (active.confirmVerify) {
                bt.show_confirm('批量操作' + active.title + '已选中', '批量' + active.title + '，该操作可能会存在风险，是否继续？', function (index) {
                  layer.close(index)
                  if (!active.recursion) {
                    request(active, check_list);
                  } else {
                    bacth.start_batch();
                  }
                });
              } else {
                bt.confirm({
                  title: '批量' + active.title,
                  msg: '批量' + active.title + '，该操作可能会存在风险，是否继续？',
                }, function (index) {
                  layer.close(index)
                  if (!active.recursion) {
                    request(active, check_list);
                  } else {
                    bacth.start_batch();
                  }
                });
              }
            } else {
              request(active, check_list);
            }
          }
        }
        for (var i = 0; i < config.length; i++) {
          var template = '',
            item = config[i];
          switch (item.type) {
            case 'group':
              $.each(item.list, function (index, items) {
                var _btn = item.type + '_' + _that.random + '_' + index,
                  html = '';
                if (items.type == 'division') {
                  template += '<span class="mlr5"></span>';
                } else {
                  if (!items.group) {
                    template += '<button type="button" title="' + (items.tips || items.title) + '" class="btn ' + (items.active ? 'btn-success' : 'btn-default') + ' ' + _btn + ' btn-sm mr5" ' + that.$verify(_that.$reader_style(items.style), 'style') + '>' + (items.icon ? '<span class="glyphicon glyphicon-' + items.icon + ' mr5"></span>' : '') + '<span>' + items.title + '</span></button>';
                  } else {
                    template += '<div class="btn-group" style="vertical-align: top;">\
                                        <button type="button" class="btn btn-default ' + _btn + ' btn-sm dropdown-toggle" data-toggle="dropdown" aria-haspopup="true" aria-expanded="false"><span style="margin-right:2px;">分类管理</span><span class="caret" style="position: relative;top: -1px;"></span></button>\
                                        <ul class="dropdown-menu"></ul>\
                                    </div>'
                    if (item.list) {
                      $.each(item.list, function (index, items) {
                        html += '<li><a href="javascript:;" ' + +'>' + items[item.key] + '</a></li>';
                      });
                    }
                    if (items.init) setTimeout(function () {
                      items.init(_btn)
                    }, 400);
                  }
                }
                if (!event_list[_btn]) event_list[_btn] = {
                  event: items.event,
                  type: 'button'
                };
              });
              break;
            case 'search':
              this.config.search = item;
              var _input = 'search_input_' + this.random,
                _focus = 'search_focus_' + this.random,
                _btn = 'search_btn_' + this.random;
              template = '<div class="bt_search"><input type="text" class="search_input ' + _input + '" style="' + (item.width ? ('width:' + item.width) : '') + '" placeholder="' + (item.placeholder || '') + '"/><span class="glyphicon glyphicon-search ' + _btn + '" aria-hidden="true"></span></div>';
              if (!event_list[_input]) event_list[_input] = {
                eventType: 'keyup',
                type: 'search_input'
              };
              if (!event_list[_focus]) event_list[_focus] = {
                type: 'search_focus',
                eventType: 'focus'
              };
              if (!event_list[_btn]) event_list[_btn] = {
                type: 'search_btn'
              };
              break;
            case 'batch':
              this.config.batch = item;
              var batch_list = [],
                _html = '',
                active = item.config;
              if (typeof item.config != 'undefined') {
                _that.batch_active = active;
                $(_that.config.el).on('click', '.set_batch_option', function (e) {
                  var check_list = [];
                  for (var i = 0; i < _that.checkbox_list.length; i++) {
                    check_list.push(_that.data[_that.checkbox_list[i]]);
                  }
                  if ($(this).hasClass('bt-disabled')) {
                    layer.tips(_that.config.batch.disabledTips || '请选择需要批量操作的数据', $(this), {
                      tips: [1, 'red'],
                      time: 2000
                    });
                    return false;
                  }
                  switch (typeof active.confirm) {
                    case 'function':
                      active.confirm(active, function (param, callback) {
                        active.param = $.extend(active.param, param);
                        execute_batch(active, check_list, callback);
                      });
                      break;
                    case 'undefined':
                      execute_batch(active, check_list);
                      break;
                    case 'object':
                      var config = active.confirm;
                      bt.open({
                        title: config.title || '批量操作',
                        area: config.area || '350px',
                        btn: config.btn || ['确认', '取消'],
                        content: config.content,
                        success: function (layero, index) {
                          config.success(layero, index, active);
                        },
                        yes: function (index, layero) {
                          config.yes(index, layero, function (param, callback) {
                            active.param = $.extend(active.param, param);
                            request(active, check_list);
                          });
                        }
                      });
                      break;
                  }
                });
              } else {
                $.each(item.selectList, function (index, items) {
                  if (items.group) {
                    $.each(items.group, function (indexs, itemss) {
                      batch_list.push($.extend({}, items, itemss));
                      _html += '<li class="item">' + itemss.title + '</li>';
                    });
                    delete items.group;
                  } else {
                    batch_list.push(items);
                    _html += '<li class="item">' + items.title + '</li>';
                  }
                });
                // 打开批量类型列表
                $(_that.config.el).unbind().on('click', '.bt_table_select_group .bt_select_value', function (e) {
                  var _this = this, $parent = $(this).parent(), bt_selects = $parent.find('.bt_selects'), area = $parent.offset(), _win_area = _that.$get_win_area();
                  if ($parent.hasClass('bt-disabled')) {
                    layer.tips(_that.config.batch.disabledSelectValue, $parent, { tips: [1, 'red'], time: 2000 })
                    return false;
                  }
                  if ($parent.hasClass('active')) {
                    $parent.removeClass('active');
                  } else {
                    $parent.addClass('active');
                  }
                  if (bt_selects.height() > (_win_area[1] - area.top)) {
                    bt_selects.addClass('top');
                  } else {
                    bt_selects.removeClass('top');
                  }
                  $(document).one('click', function () {
                    $(_that.config.el).find('.bt_table_select_group').removeClass('active');
                    return false;
                  });
                  return false;
                });
                // 选择批量的类型
                $(_that.config.el).on('click', '.bt_table_select_group .item', function (e) {
                  var _text = $(this).text(),
                    _index = $(this).index();
                  $(this).addClass('active').siblings().removeClass('active');
                  $(_that.config.el + ' .bt_select_tips').html('批量' + _text + '<em>(已选中' + _that.checkbox_list.length + ')</em>');
                  _that.batch_active = batch_list[_index];
                  if (!_that.checked) $('.bt_table_select_group').removeClass('active');
                });
                // 执行批量操作
                $(_that.config.el).on('click', '.set_batch_option', function (e) {
                  var check_list = [],
                    active = _that.batch_active;
                  if ($(this).hasClass('bt-disabled')) {
                    layer.tips(_that.config.batch.disabledSelectValue, $(this), {
                      tips: [1, 'red'],
                      time: 2000
                    });
                    return false;
                  }
                  for (var i = 0; i < _that.checkbox_list.length; i++) {
                    check_list.push(_that.data[_that.checkbox_list[i]]);
                  }
                  if (JSON.stringify(active) === '{}') {
                    var bt_table_select_group = $(_that.config.el + ' .bt_table_select_group');
                    layer.tips('请选择需要批量操作的类型', bt_table_select_group, {
                      tips: [1, 'red'],
                      time: 2000
                    });
                    bt_table_select_group.css('border', '1px solid red');
                    setTimeout(function () {
                      bt_table_select_group.removeAttr('style');
                    }, 2000);
                    return false;
                  }
                  switch (typeof active.confirm) {
                    case 'function':
                      active.confirm(active, function (param, callback) {
                        active.param = $.extend(active.param, param);
                        execute_batch(active, check_list, callback);
                      });
                      break;
                    case 'undefined':
                      execute_batch(active, check_list);
                      break;
                    case 'object':
                      var config = active.confirm;
                      bt.open({
                        title: config.title || '批量操作',
                        area: config.area || '350px',
                        btn: config.btn || ['确认', '取消'],
                        content: config.content,
                        success: function (layero, index) {
                          config.success(layero, index, active);
                        },
                        yes: function (index, layero) {
                          config.yes(index, layero, function (param, callback) {
                            active.param = $.extend(active.param, param);
                            request(active, check_list);
                          });
                        }
                      });
                      break;
                  }
                });
              }
              template = '<div class="bt_batch"><label><i class="cust—checkbox cursor-pointer checkbox_' + this.random + '" data-checkbox="all"></i><input type="checkbox" lass="cust—checkbox-input" /></label>' + (typeof item.config != 'undefined' ? '<button class="btn btn-default btn-sm set_batch_option bt-disabled">批量' + item.config.title + '</button>' : '<div class="bt_table_select_group bt-disabled not-select"><span class="bt_select_value"><span class="bt_select_tips">请选择批量操作<em></em></span><span class="glyphicon glyphicon-triangle-bottom ml5"></span></span><ul class="bt_selects ">' + _html + '</ul></div><button class="btn btn-default btn-sm set_batch_option bt-disabled" >' + item.buttonValue + '</button>') + '</div>';
              break;
            case 'page':
              this.config.page = item;
              var pageNumber = bt.get_cookie('page_number');
              if (this.config.cookiePrefix && pageNumber) this.config.page.number = pageNumber;
              template = this.$reader_page(this.config.page, '<div><span class="Pcurrent">1</span><span class="Pcount">共0条数据</span></div>');
              break;
          }
          if (template) {
            var tools_group = $(_that.config.el + ' .tootls_' + item.positon[1]);
            if (tools_group.length) {
              var tools_item = tools_group.find('.pull-' + item.positon[0]);
              tools_item.append(template);
            } else {
              var tools_group_elment = '<div class="tootls_group tootls_' + item.positon[1] + '"><div class="pull-left">' + (item.positon[0] == 'left' ? template : '') + '</div><div class="pull-right">' + (item.positon[0] == 'right' ? template : '') + '</div></div>';
              if (item.positon[1] === 'top') {
                $(_that.config.el).append(tools_group_elment);
                if ($(_that.config.el + ' .divtable').length === 0) $(_that.config.el).append('<div class="divtable mtb10" style="max-height:' + _that.config.height + 'px"></div>');
              } else {
                if ($(_that.config.el + ' .divtable').length === 0) $(_that.config.el).append('<div class="divtable mtb10" style="max-height:' + _that.config.height + 'px"></div>');
                $(_that.config.el).append(tools_group_elment);
              }
            }
          }
        }
        if (!this.init) this.$event_bind(event_list);
      },

      $clear_table_checkbox: function () {
        $(this.config.el).find('.bt_table .cust—checkbox').removeClass('selected active');
      },
      /**
       * @description 获取数据批量列表
       * @param {string} 需要获取的字段
       * @return {array} 当前需要批量列表
       */
      $get_data_batch_list: function (fid, data) {
        var arry = [];
        $.each(data || this.data, function (index, item) {
          arry.push(item[fid])
        });
        return arry;
      },

      /**
       * @description 渲染分页
       * @param {object} config 配置文件
       * @param {object} page 分页
       * @return void
      */
      $reader_page: function (config, page) {
        if (typeof page === 'number') {
          page = this.$custom_page(page);
        }
        var _that = this, $page = $(page), template = '', eventList = {};
        $page.find('a').addClass('page_link_' + this.random);
        template += $page.html();
        if (config.numberStatus) {
          var className = 'page_select_' + this.random, number = bt.get_cookie('page_number');
          template += '<select class="page_select_number ' + className + '">';
          $.each(config.numberList, function (index, item) {
            template += '<option value="' + item + '" ' + ((number || config.number) == item ? 'selected' : '') + '>' + item + '条/页</option>';
          });
          template += '</select>';
          eventList[className] = { eventType: "change", type: 'page_select' };
        }
        if (config.jump) {
          var inputName = 'page_jump_input_' + this.random;
          var btnName = 'page_jump_btn_' + this.random;
          template += '<div class="page_jump_group"><span class="page_jump_title">跳转到</span><input type="number" class="page_jump_input ' + inputName + '" value="' + config.page + '" /><span class="page_jump_title">页</span><button type="button" class="page_jump_btn ' + btnName + '">确认</button></div>'
          eventList[inputName] = {
            eventType: 'keyup',
            type: 'page_jump_input'
          };
          eventList[btnName] = {
            type: 'page_jump_btn'
          };
        }
        eventList['page_link_' + this.random] = {
          type: 'cut_page_number'
        };
        _that.config.page.total = $page.length == 0 ? 0 : (typeof page == "number" ? page : parseInt($page.find('.Pcount').html().match(/([0-9]*)/g)[1]));
        _that.$event_bind(eventList);
        return '<div class="page">' + template + '</div>';
      },
      /**
       * @description 渲染样式
       * @param {object|string} data 样式配置
       * @return {string} 样式
       */
      $reader_style: function (data) {
        var style = '';
        if (typeof data === 'string') return data;
        if (typeof data === 'undefined') return '';
        $.each(data, function (key, item) {
          style += key + ':' + item + ';';
        });
        return style;
      },
      /**
       * @description 自定义分页
       * @param {}
      */
      $custom_page: function (total) {
        var html = '<div class="page">',
          config = this.config.page,
          page = Math.ceil(total / config.number),
          tmpPageIndex = 0;
        if (config.page > 1 && page > 1) {
          html += '<a class="Pstart" href="p=1">首页</a><a class="Pstart" href="p=' + (config.page - 1) + '">上一页</a>';
        }
        if (page <= 10) {
          for (var i = 1; i <= page; i++) {
            i == config.page ? html += '<span class="Pcurrent">' + i + "</span>" : html += '<a class="Pnum" href="p=' + i + '">' + i + "</a>";
          }
        } else if (config.page < 10) {
          for (var i = 1; i <= 10; i++) i == config.page ? html += '<span class="Pcurrent">' + i + "</span>" : html += '<a class="Pnum" href="p=' + i + '">' + i + "</a>";
          html += "<span>...</span>"
        } else if (page - config.page < 7) {
          page - 7 > 1 && (html += '<a class="Pnum" href="p=1">1</a>', html += "<span>...</span>");
          for (var i = page - 7; i <= page; i++) i == config.page ? html += '<span class="Pcurrent">' + i + "</span>" : (html += 1 == i ? "<span>...</span>" : '<a class="Pnum" href="p=' + i + '">' + i + "</a>")
        } else {
          0 == tmpPageIndex && (tmpPageIndex = config.page),
            (tmpPageIndex <= config.page - 5 || tmpPageIndex >= config.page + 5) && (tmpPageIndex = config.page),
            html += '<a class="Pnum" href="p=1">1</a>',
            html += "<span>...</span>";
          for (var i = tmpPageIndex - 3; i <= tmpPageIndex + 3; i++) i == config.page ? html += '<span class="Pcurrent">' + i + "</span>" : html += '<a class="Pnum" href="p=' + i + '">' + i + "</a>";
          html += "<span>...</span>",
            html += '<a class="Pnum" href="p=' + page + '">' + page + "</a>"
        }
        return page > 1 && config.page < page && (html += '<a class="Pstart" href="p=' + (config.page + 1) + '">下一页</a><a class="Pstart" href="p=' + page + '">尾页</a>'),
          html += '<span class="Pcount">共' + total + "条</span></div>"
      },


      /**
       * @deprecated 动态处理合并行内，css样式
       * @param {object} rows 当前行数据
       * @return {stinrg} className class类名
       * @return void
       */
      $dynamic_merge_style: function (column, index) {
        var str = '';
        $.each(column, function (key, item) {
          switch (key) {
            case 'align':
              str += 'text-align:' + item + ';';
              break;
            case 'width':
              str += 'width:' + (typeof item == 'string' ? item : item + 'px') + ';';
              break;
            case 'style':
              str += item;
              break;
            case 'minWidth':
              str += 'min-width:' + (typeof item == 'string' ? item : item + 'px') + ';';
              break;
            case 'maxWidth':
              str += 'max-width:' + (typeof item == 'string' ? item : item + 'px') + ';';
              break;
          }
        });
        return {
          index: index,
          css: str
        };
      },

      /**
       * @description 事件绑定
       * @param {array} eventList 事件列表
       * @return void
       */
      $event_bind: function (eventList) {
        var _that = this;
        $.each(eventList, function (key, item) {
          if (_that.event_list[key] && _that.event_list[key].eventType === item.eventType) return true;
          _that.event_list[key] = item;
          $(_that.config.el).on(item.eventType || 'click', '.' + key, function (ev) {
            var index = $(this).parents('tr').index(),
              data1 = $(this).data(),
              arry = [];
            switch (item.type) {
              case 'rows':
                _that.event_rows_model = {
                  el: $(this),
                  model: _that.config.column[$(this).parents('td').index()],
                  rows: _that.data[index],
                  index: index
                }
                arry = [_that.event_rows_model.rows, _that.event_rows_model.index, ev, key, _that];
                break;
              case 'sort':
                var model = _that.config.column[data1.index];
                if ($(this).hasClass('sort-active')) $('.sort_' + _that.random + ' .sort-active').data({
                  'sort': 'desc'
                });
                $('.sort_' + _that.random).removeClass('sort-active').find('.glyphicon').removeClass('glyphicon-triangle-top').addClass('glyphicon-triangle-bottom');
                $(this).addClass('sort-active');
                if (data1.sort == 'asc') {
                  $(this).data({
                    'sort': 'desc'
                  });
                  $(this).find('.glyphicon').removeClass('glyphicon-triangle-top').addClass('glyphicon-triangle-bottom');
                } else {
                  $(this).data({
                    'sort': 'asc'
                  });
                  $(this).find('.glyphicon').removeClass('glyphicon-triangle-bottom').addClass('glyphicon-triangle-top');
                }
                _that.config.sort = _that.config.sortParam({
                  name: model.fid,
                  sort: data1.sort
                });
                _that.$refresh_table_list(true);
                break;
              case 'checkbox':
                var all = $(_that.config.el + ' [data-checkbox="all"]'),
                  checkbox_list = $(_that.config.el + ' tbody .checkbox_' + _that.random);
                if (data1.checkbox == undefined) {
                  if (!$(this).hasClass('active')) {
                    $(this).addClass('active');
                    _that.checkbox_list.push(index);
                    if (_that.data.length === _that.checkbox_list.length) {
                      all.addClass('active').removeClass('selected')
                    } else if (_that.checkbox_list.length > 0) {
                      all.addClass('selected');
                    }
                  } else {
                    $(this).removeClass('active');
                    _that.checkbox_list.splice(_that.checkbox_list.indexOf(index), 1);
                    if (_that.checkbox_list.length > 0) {
                      all.addClass('selected').removeClass('active');
                    } else {
                      all.removeClass('selected active');
                    }
                  }
                } else {
                  if (_that.checkbox_list.length === _that.data.length) {
                    _that.checkbox_list = [];
                    checkbox_list.removeClass('active selected').next().prop('checked', 'checked')
                    all.removeClass('active');
                  } else {
                    checkbox_list.each(function (index, item) {
                      if (!$(this).hasClass('active')) {
                        $(this).addClass('active').next().prop('checked', 'checked');
                        _that.checkbox_list.push(index);
                      }
                    });
                    all.removeClass('selected').addClass('active');
                  }
                }
                _that.$set_batch_view();
                break;
              case 'button':
                arry.push(ev, _that);
                break;
              case 'search_focus':
                var search_tips = $(_that.config.el + ' .bt_search_tips');
                if ($(_that.config.el + ' .bt_search_tips').length > 0) {
                  search_tips.remove();
                }
                break;
              case 'search_input':
                if (ev.keyCode == 13) {
                  $(_that.config.el + ' .search_btn_' + _that.random).click();
                  return false;
                }
                break;
              case 'search_btn':
                var _search = $(_that.config.el + ' .search_input'), val = $(_that.config.el + ' .search_input').val();
                val = val.replace(/\s+/g, "");
                _search.val(val);
                _that.config.search.value = val;
                _search.append('<div class="bt_search_tips"><span>' + val + '</span><i class="bt_search_close"></i></div>');
                _that.$refresh_table_list(true);
                break;
              case 'page_select':
                var limit = parseInt($(this).val());
                bt.set_cookie('page_number', limit);
                _that.config.page.number = limit;
                _that.config.page.page = 1;
                _that.$refresh_table_list(true);
                return false;
                break;
              case 'page_jump_input':
                if (ev.keyCode === 13) {
                  $(_that.config.el + ' .page_jump_btn_' + _that.random).click();
                  $(this).focus();
                }
                return false;
                break;
              case 'page_jump_btn':
                var jump_page = parseInt($(_that.config.el + ' .page_jump_input_' + _that.random).val()),
                  max_number = Math.ceil(_that.config.page.total / _that.config.page.number);
                if (isNaN(jump_page)) jump_page = 1
                if (jump_page > max_number) jump_page = _that.config.page.page;
                _that.config.page.page = jump_page;
                _that.$refresh_table_list(true);
                break;
              case 'cut_page_number':
                var page = parseInt($(this).attr('href').match(/([0-9]*)$/)[0])
                _that.config.page.page = page;
                _that.$refresh_table_list(true);
                return false;
                break;
              case 'eye_open_password':
                if ($(this).hasClass('glyphicon-eye-open')) {
                  $(this).addClass('glyphicon-eye-close').removeClass('glyphicon-eye-open');
                  $(this).prev().text(_that.data[index].password);
                } else {
                  $(this).addClass('glyphicon-eye-open').removeClass('glyphicon-eye-close');
                  $(this).prev().html('<i>**********</i>');
                }
                return false;
                break;
              case 'copy_password':
                bt.pub.copy_pass(_that.data[index].password);
                return false;
                break;
            }
            if (item.event) item.event.apply(this, arry);
          });
        });
      },

      /**
       * @description 样式绑定
       * @param {array} style_list 样式列表
       * @return void
      */
      $style_bind: function (style_list, status) {
        var str = '',
          _that = this;
        $.each(style_list, function (index, item) {
          if (item.css != '') {
            if (!item.className) {
              str += _that.config.el + ' thead th:nth-child(' + (item.index + 1) + '),' + _that.config.el + ' tbody tr td:nth-child' + (item.span ? ' span' : '') + '(' + (item.index + 1) + '){' + item.css + '}'
            } else {
              str += item.className + '{' + item.css + '}';
            }
          }
        });
        if ($('#bt_table_' + _that.random).length == 0) $(_that.config.el).append('<style type="text/css" id="bt_table_' + _that.random + '">' + str + '</style>');
      },

      /**
       * @deprecated 获取WIN高度或宽度
       * @return 返回当期的宽度和高度
       */
      $get_win_area: function () {
        return [window.innerWidth, window.innerHeight];
      },

      /**
       * @description 请求数据，
       * @param {object} param 参数和请求路径
       * @return void
       */
      $http: function (success) {
        var page_number = bt.get_cookie('page_number'),
          that = this,
          param = {},
          config = this.config,
          _page = config.page,
          _search = config.search,
          _sort = config.sort || {};
        if (_page) {
          if (page_number) _page.number = page_number
          param[_page.numberParam] = _page.number, param[_page.pageParam] = _page.page;
          bt.set_cookie('page_number', _page.number);
        }
        if (_search) param[_search.searchParam] = _search.value;
        if (this.config.beforeRequest) {
          config.param = this.config.beforeRequest($.extend(config.param, param, _sort));
        } else {
          config.param = $.extend(config.param, param, _sort)
        }
        bt_tools.send({
          url: config.url,
          data: config.param
        }, function (res) {
          if (typeof config.dataFilter != "undefined") {
            var data = config.dataFilter(res, that);
            if (typeof data.tootls != "undefined") data.tootls = parseInt(data.tootls);
            if (success) success(data);
          } else {
            if (void 0 == res.data) {
              success && success({
                data: res
              })
            } else success && success({
              data: res.data,
              page: res.page
            })
          }
        });
      }
    }
    return new ReaderTable(config);
  },
  /**
   * @description 渲染Form表单
   * @param {*} config
   * @return 当前实例对象
   */
  form: function (config) {
    var _that = this;
    function ReaderForm (config) {
      this.config = config;
      this.el = config.el
      this.submit = config.submit
      this.data = config.data || {};
      this.$load();
    }
    ReaderForm.prototype = {
      element: null,
      style_list: [], // 样式列表
      event_list: {}, // 事件列表,已绑定事件
      event_type: ['click', 'event', 'focus', 'keyup', 'blur', 'change', 'input'],
      hide_list: [],
      form_element: {},
      form_config: {},
      random: bt.get_random(5),
      $load: function () {
        var that = this;
        if (this.el) {
          $(this.el).html(this.$reader_content())
          this.$event_bind();
        }
      },

      /**
       * @description 渲染Form内容
       * @param {Function} callback 回调函数
       */
      $reader_content: function (callback) {
        var that = this,
          html = '',
          _content = '';
        $.each(that.config.form, function (index, item) {
          if (item.separate) {
            html += '<div class="bt_form_separate"><span class="btn btn-sm btn-default">' + item.separate + '</span></div>'
          } else {
            html += that.$reader_content_row(index, item);
          }
        });
        that.element = $('<form class="bt-form" data-form="' + that.random + '" onsubmit="return false">' + html + '</form>');
        _content = $('<div class="' + _that.$verify(that.config['class']) + '"></div>');
        _content.append(that.element);
        if (callback) callback();
        return _content[0].outerHTML;
      },

      /**
       * @description 渲染行内容
       * @param {object} data Form数据
       * @param {number} index 下标
       * @return {string} HTML结构
       */
      $reader_content_row: function (index, data) {
        try {
          var that = this, help = data.help || false, labelWidth = data.formLabelWidth || this.config.formLabelWidth;
          if (data.display === false) return '';
          return '<div class="line' + _that.$verify(data['class']) + _that.$verify(data.hide, 'hide', true) + '"' + _that.$verify(data.id, 'id') + '>' +
            (typeof data.label !== "undefined" ? '<span class="tname" ' + (labelWidth ? 'style="width:' + labelWidth + '"' : '') + '>' + data.label + '</span>' : '') +
            '<div class="' + (data.label ? 'info-r' : '') + _that.$verify(data.line_class) + '"' + _that.$verify(that.$reader_style($.extend(data.style, labelWidth ? { 'margin-left': labelWidth } : {})), 'style') + '>' +
            that.$reader_form_element(data.group, index) +
            (help ? ('<div class="c9 mt5 ' + _that.$verify(help['class'], 'class') + '" ' + _that.$verify(that.$reader_style(help.style), 'style') + '>' + help.list.join('</br>') + '</div>') : '') +
            '</div>' +
            '</div>';
        } catch (error) {
          console.log(error)
        }
      },

      /**
       * @description 渲染form类型
       * @param {object} data 表单数据
       * @param {number} index 下标
       * @return {string} HTML结构
       */
      $reader_form_element: function (data, index) {
        var that = this, html = '';
        if (!Array.isArray(data)) data = [data];
        $.each(data, function (key, item) {
          item.find_index = index;
          html += that.$reader_form_find(item);
          that.form_config[item.name] = item;
        });
        return html;
      },
      /**
       * @descripttion 渲染单个表单元素
       * @param {Object} item 配置
       * @return: viod
       */
      $reader_form_find: function (item) {
        var that = this, html = '', style = that.$reader_style(item.style) + _that.$verify(item.width, 'width', 'style'),
          attribute = that.$verify_group(item, ['name', 'placeholder', 'disabled', 'readonly', 'autofocus', 'autocomplete', 'min', 'max']),
          event_group = that.$create_event_config(item),
          eventName = '', index = item.find_index;
        if (item.display === false) return html
        html += item.label ? '<span class="mr5 inlineBlock">' + item.label + '</span>' : '';
        if (typeof item['name'] !== "undefined") {
          that.$check_event_bind(item.name, event_group)
        }
        html += '<div class="' + (item.dispaly || 'inlineBlock') + ' ' + _that.$verify(item.hide, 'hide', true) + ' ' + (item['class'] || '') + '">';
        var _value = typeof that.data[item.name] !== "undefined" && that.data[item.name] !== '' ? that.data[item.name] : (item.value || '')
        switch (item.type) {
          case 'text': // 文本选择
          case 'checkbox': // 复选框
          case 'password': // 密码
          case 'radio': // 单选框
          case 'number': // 数字
            var _event = 'event_' + item.name + '_' + that.random;
            switch (item.type) {
              case 'checkbox': // 复选框
                html += '<label class="cursor-pointer form-checkbox-label" ' + _that.$verify(that.$reader_style(item.style), 'style') + '><i class="form-checkbox cust—checkbox cursor-pointer mr5 ' + _event + '_label ' + (_value ? 'active' : '') + '"></i><input type="checkbox" class="form—checkbox-input hide mr10 ' + _event + '" name="' + item.name + '" ' + (_value ? 'checked' : '') + '/><span class="vertical_middle">' + item.title + '</span></label>';
                that.$check_event_bind(_event + '_label', { 'click': { type: 'checkbox_icon', config: item } })
                that.$check_event_bind(_event, { 'input': { type: 'checkbox', config: item, event: item.event } })
                break;
              default:
                html += '<input type="' + item.type + '"' + attribute + ' ' + (item.icon ? 'id="' + _event + '"' : '') + ' class="bt-input-' + (item.type !== 'select_path' && item.type !== 'number' && item.type !== 'password' ? item.type : 'text') + ' mr10 ' + (item.label ? 'vertical_middle' : '') + _that.$verify(item['class']) + '"' + _that.$verify(style, 'style') + ' value="' + _value + '"/>';
                break;
            }
            if (item.btn && !item.disabled) {
              html += '<span class="btn ' + item.btn.type + ' ' + item.name + '_btn cursor" ' + _that.$verify(that.$reader_style(item.btn.style), 'style') + '>' + item.btn.title + '</span>';
              if (typeof item.btn.event !== 'undefined') {
                that.$check_event_bind(item.name + '_btn', {
                  'click': {
                    config: item,
                    event: item.btn.event
                  }
                })
              }
            }
            if (item.icon) {
              html += '<span class="glyphicon ' + item.icon.type + ' ' + item.name + '_icon cursor ' + (item.disabled ? 'hide' : '') + ' mr10" ' + _that.$verify(that.$reader_style(item.icon.style), 'style') + '></span>';
              if (typeof item.icon.event !== 'undefined') {
                that.$check_event_bind(item.name + '_icon', {
                  'click': {
                    type: 'select_path',
                    select: item.icon.select || '',
                    config: item,
                    children: '.' + item.name + '_icon',
                    event: item.icon.event,
                    callback: item.icon.callback
                  }
                })
              }
            }
            break;
          case 'textarea':
            html += '<textarea class="bt-input-text"' + _that.$verify(style, 'style') + attribute + ' >' + _value + '</textarea>';
            $.each(['blur', 'focus', 'input'], function (index, items) {
              if (item.tips) {
                var added = null, event = {}
                switch (items) {
                  case 'blur':
                    added = function (ev, item, element) {
                      if ($(this).val() === '') $(this).next().show();
                      layer.close(item.tips.loadT);
                      $(ev.target).data('layer', '');
                    }
                    break;
                  case 'focus':
                    added = function (ev, item) {
                      $(this).next().hide();
                      item.tips.loadT = layer.tips(tips, $(this), {
                        tips: [1, '#20a53a'],
                        time: 0,
                        area: $(this).width()
                      });
                    }
                    break;
                }
              }
              that.event_list[item.name][items] ? (that.event_list[item.name][items]['added'] = added) : (that.event_list[item.name][items] = {
                type: item.type,
                cust: false,
                event: item[items],
                added: added
              });
            });
            if (item.tips) {
              var tips = '';
              if (typeof item.tips.list === "undefined") {
                tips = item.tips.text;
              } else {
                tips = item.tips.list.join('</br>');
              }
              html += '<div class="placeholder c9 ' + item.name + '_tips" ' + _that.$verify(that.$reader_style(item.tips.style), 'style') + '>' + tips + '</div>';
              that.$check_event_bind(item.name + '_tips', {
                'click': {
                  type: 'textarea_tips',
                  config: item
                }
              })
            }
            break;
          case 'select':
            html += that.$reader_select(item, style, attribute, index);
            that.$check_event_bind('custom_select', {
              'click': {
                type: 'custom_select',
                children: '.bt_select_value'
              }
            })
            that.$check_event_bind('custom_select_item', {
              'click': {
                type: 'custom_select_item',
                children: 'li.item'
              }
            })
            break;
          case 'link':
            eventName = 'event_link_' + that.random + '_' + item.name;
            html += '<a href="' + (item.href || 'javascript:;') + '" class="btlink ' + eventName + '" ' + _that.$verify(that.$reader_style(item.style), 'style') + '>' + item.title + '</a>';
            that.$check_event_bind(eventName, {
              'click': {
                type: 'link_event',
                event: item.event
              }
            })
            break;
          case 'button':
            html += '<button class="btn btn-success btn-' + (item.size || 'sm ') + ' ' + eventName + ' ' + _that.$verify(item['class']) + '"  ' + _that.$verify(that.$reader_style(item.style), 'style') + ' ' + attribute + '>' + item.title + '</button>'
            break;
          case 'help':
            var _html = '';
            $.each(item.list, function (index, items) {
              _html += '<li>' + items + '</li>';
            })
            html += '<ul class="help-info-text c7' + _that.$verify(item['class']) + '"' + _that.$verify(that.$reader_style(item.style), 'style') + ' ' + attribute + '>' + _html + '</ul>';
            break;
        }
        html += item.unit ? '<span class="' + (item.type === 'text-tips' ? 'text-tips' : 'unit') + '">' + item.unit + '</span>' : '';
        html += '</div>'
        return html;
      },

      /**
       * @descripttion 检测检测名称
       * @param {string} eventName 配置
       * @param {object} config 事件配置
       */
      $check_event_bind: function (eventName, config) {
        if (!this.event_list[eventName]) {
          // console.log(eventName)
          if (!this.event_list.hasOwnProperty(eventName)) {
            // console.log('1')
            this.event_list[eventName] = config
          }
        }
      },
      /**
       * @description 创建事件配置
       * @param {object} item 行内配置
       * @return {object} 配置信息
       */
      $create_event_config: function (item) {
        var config = {};
        if (typeof item['name'] === "undefined") return {};
        $.each(this.event_type, function (key, items) {
          if (item[items]) {
            config[(items === 'event' ? 'click' : items)] = {
              type: item.type,
              event: item[items],
              cust: (['select', 'checkbox', 'radio'].indexOf(item.type) > -1),
              config: item
            };
          }
        });
        return config;
      },
      /**
       * @description 渲染样式
       * @param {object|string} data 样式配置
       * @return {string} 样式
       */
      $reader_style: function (data) {
        var style = '';
        if (typeof data === 'string') return data;
        if (typeof data === 'undefined') return '';
        $.each(data, function (key, item) {
          style += key + ':' + item + ';';
        });
        return style;
      },
      /**
       * @descripttion 局部刷新form表单元素
       * @param {String} name 需要刷新的元素
       * @param {String} name 元素新数据
       * @return: viod
       */
      $local_refresh: function (name, config) {
        var formFind = this.element.find('[data-name=' + name + ']')
        if (this.element.find('[data-name=' + name + ']').length === 0) formFind = this.element.find('[name=' + name + ']')
        formFind.parent().replaceWith(this.$reader_form_find(config))
      },
      /**
       * @description 渲染下拉，内容方法
       */
      $reader_select: function (item, style, attribute, index) {
        var that = this, list = '', option = '', active = {};
        if (typeof item.list === 'function') {
          var event = item.list;
          event.call(this, this.config.form);
          item.list = [];
        }
        if (!Array.isArray(item.list)) {
          var config = item.list;
          bt_tools.send({
            url: config.url,
            data: config.param || config.data || {}
          }, function (res) {
            if (res.status !== false) {
              var list = item.list.dataFilter ? item.list.dataFilter(res, that) : res;
              if (item.list.success) item.list.success(res, that, that.config.form[index], list)
              item.list = list
              if (!item.list.length) {
                item.disabled = true
                layer.msg(item.placeholder || '数据获取为空', { icon: 2 })
              }
              that.$replace_render_content(index);
            } else {
              bt.msg(res);
            }
          });
          return false
        }
        if (typeof that.data[item.name] === "undefined") active = item.list[0]
        $.each(item.list, function (key, items) {
          if (items.value === item.value || items.value === that.data[item.name]) {
            active = items
            return false
          }
        })
        $.each(item.list, function (key, items) {
          list += '<li class="item' + _that.$verify(items.value === active.value ? 'active' : '') + ' ' + (items.disabled ? 'disabled' : '') + '" title="' + items.title + '">' + items.title + '</li>';
          option += '<option value="' + items.value + '"' + (items.disabled ? 'disabled' : '') + ' ' + _that.$verify(items.value === active.value ? 'selected' : '') + '>' + items.title + '</option>';
        });
        var title = !Array.isArray(item.list) ? '获取数据中' : (active ? active.title : item.placeholder)
        return '<div class="bt_select_updown mr10 ' + (item.disabled ? 'bt-disabled' : '') + ' ' + + _that.$verify(item['class']) + '" ' + _that.$verify(style, 'style') + ' data-name="' + item.name + '">' +
          '<span class="bt_select_value"><span class="bt_select_content" title="' + (title || item.placeholder) + '">' + (title || item.placeholder) + '</span><span class="glyphicon glyphicon-triangle-bottom ml5"></span></span>' +
          '<ul class="bt_select_list">' + (list || '') + '</ul>' +
          '<select' + attribute + ' class="hide" ' + (item.disabled ? 'disabled' : '') + ' autocomplete="off">' + (option || '') + '</select>' +
          '</div>';
      },

      /**
       * @description 替换渲染内容
       */
      $replace_render_content: function (index) {
        var that = this, config = this.config.form[index], html = that.$reader_content_row(index, config);
        $('[data-form=' + that.random + ']').find('.line:eq(' + index + ')').replaceWith(html);
        this.$event_bind()
      },

      /**
       * @description 重新渲染内容
       * @param {object} formConfig 配置
       */
      $again_render_form: function (formConfig) {
        var formElement = $('[data-form=' + this.random + ']'), that = this;
        formConfig = formConfig || this.config.form
        formElement.empty()
        for (var i = 0; i < formConfig.length; i++) {
          var config = formConfig[i]
          if (config.display === false) continue
          formElement.append(that.$reader_content_row(i, config))
        }
        this.config.form = formConfig
        this.$event_bind()
      },

      /**
       * @description 事件绑定功能
       * @param {Object} eventList 事件列表
       * @param {Function} callback 回调函数
       * @return void
       */
      $event_bind: function (eventList, callback) {
        var that = this, _event = {};
        that.element = $(typeof eventList === 'object' ? that.element : ('[data-form=' + that.random + ']'));
        _event = eventList
        if (typeof eventList === 'undefined') _event = that.event_list;
        $.each(_event, function (key, item) {
          if ($.isEmptyObject(item)) return true;
          $.each(item, function (keys, items) {
            if (!!item.type) return false;
            if (!items.hasOwnProperty('bind')) {
              items.bind = true
            } else {
              return false
            }
            var childNode = '';
            if (typeof items.cust === "boolean") {
              childNode = '[' + (items.cust ? 'data-' : '') + 'name=' + key + ']';
            } else {
              childNode = '.' + key;
            }
            (function (items, key) {
              if (items.onEvent === false) {
                switch (items.type) {
                  case 'input_checked':
                    $(childNode).on(keys != 'event' ? keys : 'click', function (ev) {
                      items.event.apply(this, [ev, that]);
                    });
                    break;
                }
                return true;
              } else {
                if (items.type === 'select') return true
                that.element.on(keys !== 'event' ? keys : 'click', items.children ? items.children : childNode, function (ev) {
                  var form = that.$get_form_element(true), config = that.form_config[key];
                  switch (items.type) {
                    case 'textarea_tips':
                      $(this).hide().prev().focus();
                      break;
                    case 'custom_select':
                      if ($(this).parent().hasClass('bt-disabled')) return false;
                      var select_value = $(this).next();
                      if (!select_value.hasClass('show')) {
                        $('.bt_select_list').removeClass('show');
                        select_value.addClass('show');
                      } else {
                        select_value.removeClass('show');
                      }
                      $(document).click(function () {
                        that.element.find('.bt_select_list').removeClass('show');
                        $(this).unbind('click');
                        return false;
                      });
                      return false;
                      break;
                    case 'custom_select_item':
                      config = that.form_config[$(this).parents('.bt_select_updown').attr('data-name')]
                      var item_config = config.list[$(this).index()]
                      if ($(this).hasClass('disabled')) {
                        $(this).parent().removeClass('show');
                        if (item_config.tips) layer.msg(item_config.tips, { icon: 2 });
                        return true;
                      }
                      if (!$(this).hasClass('active') && !$(this).hasClass('disabled')) {
                        var value = item_config.value.toString();
                        $(this).parent().prev().find('.bt_select_content').text($(this).text());
                        $(this).addClass('active').siblings().removeClass('active');
                        $(this).parent().next().val(value)
                        $(this).parent().removeClass('show');
                      }
                      that.data[config.name] = value
                      if (items.event) items.event = null
                      if (config.change) items.event = config.change
                      break;
                    case 'select_path':
                      bt.select_path('event_' + $(this).prev().attr('name') + '_' + that.random, items.select || "", !items.callback || items.callback.bind(that));
                      break;
                    case 'checkbox':
                      var checked = $(this).is(':checked');
                      if (checked) {
                        $(this).prev().addClass('active');
                      } else {
                        $(this).prev().removeClass('active');
                      }
                      break;
                  }
                  if (items.event) items.event.apply(this, [that.$get_form_value(), form, that, config, ev]); // 事件
                  if (items.added) items.added.apply(this, [ev, config, form]);
                });
              }
            }(items, key));
          });
        });
        if (callback) callback();
      },

      /**
       * @description 获取表单数据
       * @return {object} 表单数据
       */
      $get_form_value: function () {
        var form = {}
        this.element.find('input,textarea[disabled="disabled"]').each(function (index, item) {
          var val = $(this).val();
          if ($(this).attr('type') === 'checkbox') { val = $(this).prop('checked') }
          form[$(this).attr('name')] = val
        })
        return $.extend({}, this.element.serializeObject(), form)
      },

      /**
       * @description 设置指定数据
       *
       */
      $set_find_value: function (name, value) {
        var config = {}, that = this;
        typeof name != 'string' ? config = name : config[name] = value;
        $.each(config, function (key, item) {
          that.form_element[key].val(item);
        });
      },

      /**
       * @description 获取Form，jquery节点
       * @param {Boolean} afresh 是否强制刷新
       * @return {object}
       */
      $get_form_element: function (afresh) {
        var form = {},
          that = this;
        if (afresh || $.isEmptyObject(that.form_element)) {
          this.element.find(':input').each(function (index) {
            form[$(this).attr('name')] = $(this);
          });
          that.form_element = form;
          return form;
        } else {
          return that.form_element;
        }
      },

      /**
       * @description 验证值整个列表是否存在，存在则转换成属性字符串格式
       */
      $verify_group: function (config, group) {
        var that = this,
          str = '';
        $.each(group, function (index, item) {
          if (typeof config[item] === "undefined") return true;
          if (['disabled', 'readonly'].indexOf(item) > -1) {
            str += ' ' + (config[item] ? (item + '="' + item + '"') : '');
          } else {
            str += ' ' + item + '="' + config[item] + '"';
          }
        });
        return str;
      },

      /**
       * @description 验证绑定事件
       * @param {String} value
       */
      $verify_bind_event: function (eventName, row, group) {
        var event_list = {};
        $.each(group, function (index, items) {
          var event_fun = row[items];
          if (event_fun) {
            if (typeof event_list[eventName] === "object") {
              if (!Array.isArray(event_list[eventName])) event_list[eventName] = [event_list[eventName]];
              event_list[eventName].push({
                event: event_fun,
                eventType: items
              });
            } else {
              event_list[eventName] = {
                event: event_fun,
                eventType: items
              };
            }
          }
        });
        return event_list;
      },

      /**
       * @description 验证值是否存在
       * @param {String} value 内容/值
       * @param {String|Boolean} attr 属性
       * @param {String} type 属性
       */
      $verify: function (value, attr, type) {
        if (!value) return '';
        if (type === true) return value ? ' ' + attr : '';
        if (type === 'style') return attr ? attr + ':' + value + ';' : value;
        return attr ? ' ' + attr + '="' + value + '"' : ' ' + value;
      },
      /**
       * @description 验证form表单
      */
      $verify_form: function () {
        var form_list = {}, form = this.config.form, form_value = this.$get_form_value(), form_element = this.$get_form_element(true);
        for (var key = 0; key < form.length; key++) {
          var item = form[key];
          if (!Array.isArray(item.group)) item.group = [item.group];
          if (item.separate) continue
          for (var i = 0; i < item.group.length; i++) {
            var items = item.group[i], name = items.name;
            if (items.type === 'help') continue;
            if (typeof items.verify != "undefined") {
              var value = items.verify(form_value[name], form_element[name], items, true);
              if (value === false && form_value[name] !== false) return false;
              form_list[name] = value;
            } else {
              form_list[name] = (typeof form_value[name] === "undefined" && items.disabled) ? $('[name="' + name + '"]').val() : form_value[name];
            }
          }
        }
        return form_list;
      },
      /**
       * @description 提交内容，需要传入url
       * @param {Object|Function} param 附加参数或回调函数
       * @param {Function} callback 回调
      */
      $submit: function (param, callback, tips) {
        var form = this.$verify_form();
        if (typeof param === "function") tips = callback, callback = param, param = {};
        if (!form) return false;
        form = $.extend(form, param);
        if (typeof this.config.url == "undefined") {
          bt_tools.msg('请求提交地址不能为空！', false);
          return false;
        }
        bt_tools.send({
          url: this.config.url,
          data: form
        }, function (res) {
          if (callback) {
            callback(res, form);
          } else {
            bt_tools.msg(res);
          }
        }, (tips || '提交中'));
      }
    }
    return new ReaderForm(config);
  },
  /**
   * @description tab切换，支持三种模式
   * @param {object} config
   * @return 当前实例对象
   */
  tab: function (config) {
    var _that = this;
    function ReaderTab (config) {
      this.config = config;
      this.theme = this.config.theme || {};
      this.$load();
    }
    ReaderTab.prototype = {
      type: 1,
      theme_list: [{
        content: 'tab-body',
        nav: 'tab-nav',
        body: 'tab-con',
        active: 'on'
      },
      {
        content: 'bt-w-body',
        nav: 'bt-w-menu',
        body: 'bt-w-con'
      }
      ],
      random: bt.get_random(5),
      $init: function () {
        var that = this,
          active = this.config.active,
          config = that.config.list,
          _theme = {};
        this.$event_bind();
        if (config[that.active].success) config[that.active].success();
        config[that.active]['init'] = true;
      },
      $load: function () {
        var that = this;
      },
      $reader_content: function () {
        var that = this, _list = that.config.list, _tab = '', _tab_con = '', _theme = that.theme, config = that.config;
        if (typeof that.active === "undefined") that.active = 0;
        if (!$.isEmptyObject(config.theme)) {
          _theme = this.theme_list[that.active];
          $.each(config.theme, function (key, item) {
            if (_theme[key]) _theme[key] += ' ' + item;
          });
          that.theme = _theme;
        }
        if (config.type && $.isEmptyObject(config.theme)) this.theme = this.theme_list[that.active];
        $.each(_list, function (index, item) {
          var active = (that.active === index),
            _active = _theme['active'] || 'active';
          _tab += '<span class="' + (active ? _active : '') + '">' + item.title + '</span>';
          _tab_con += '<div class="tab-block ' + (active ? _active : '') + '">' + (active ? item.content : '') + '</div>';
        });
        that.element = $('<div id="tab_' + that.random + '" class="' + _theme['content'] + _that.$verify(that.config['class']) + '"><div class="' + _theme['nav'] + '" >' + _tab + '</div><div class="' + _theme['body'] + '">' + _tab_con + '</div></div>');
        return that.element[0].outerHTML;
      },
      /**
       * @description 事件绑定
       *
       */
      $event_bind: function () {
        var that = this, _theme = that.theme,
          active = _theme['active'] || 'active';
        if (!that.el) that.element = $('#tab_' + that.random);
        that.element.on('click', ('.' + _theme['nav'].replace(/\s+/g, '.') + ' span'), function () {
          var index = $(this).index(),
            config = that.config.list[index];
          $(this).addClass(active).siblings().removeClass(active);
          $('#tab_' + that.random + ' .' + _theme['body'] + '>div:eq(' + index + ')').addClass(active).siblings().removeClass(active);
          that.active = index;
          if (!config.init) {
            // console.log(_theme)
            $('#tab_' + that.random + ' .' + _theme['body'] + '>div:eq(' + index + ')').html(config.content);
            if (config.success) config.success();
            config.init = true;
          }
        });
      }
    }
    return new ReaderTab(config);
  },
  /**
   * @description loading过渡
   * @param {*} title
   * @param {*} is_icon
   * @return void
   */
  load: function (title) {
    var random = bt.get_random(5), layel = $('<div class="layui-layer layui-layer-dialog layui-layer-msg layer-anim" id="' + random + '" type="dialog" style="z-index: 99891031;"><div class="layui-layer-content layui-layer-padding"><i class="layui-layer-ico layui-layer-ico16"></i>正在' + title + '，请稍候...</div><span class="layui-layer-setwin"></span></div><div class="layui-layer-shade" id="layer-mask-' + random + '" times="17" style="z-index:99891000; background-color:#000; opacity:0.3; filter:alpha(opacity=30);"></div>'), mask = '', loadT = '';
    $('body').append(layel);
    var win = $(window), msak = $('.layer-loading-mask'), layel = $('#' + random);
    layel.css({ 'top': ((win.height() - 64) / 2), 'left': ((win.width() - 320) / 2) });
    if (title === true) loadT = layer.load();
    return {
      close: function () {
        if (typeof loadT == "number") {
          layer.close(loadT);
        } else {
          $('body').find('#' + random + ',#layer-mask-' + random).remove();
        }
      }
    }
  },
  /**
   * @description 弹窗方法，有默认的参数和重构的参数
   * @param {object} config  和layer参数一致
   * @require 当前关闭弹窗方法
   */
  open: function (config) {
    var _config = {}, layerT = null, form = null;
    _config = $.extend({ type: 1, area: '640px', closeBtn: 2, btn: ['确认', '取消'] }, config);
    if (typeof _config.content == "object") {
      var param = _config.content;
      form = bt_tools.form(param);
      _config.success = function (layero, indexs) {
        form.$event_bind();
        if (typeof config.success != "undefined") config.success(layero, indexs);
      }
      _config.yes = function (indexs, layero) {
        var form_val = form.$verify_form();
        if (!form_val) return false;
        if (typeof config.yes != "undefined") {
          var yes = config.yes.apply(form, [form_val, indexs, layero]);
          if (!yes) return false;
        }
      }
      _config.content = form.$reader_content();
    }
    layerT = layer.open(_config);
    return {
      close: function () {
        layer.close(layerT);
      },
      form: form
    }
  },
  /**
   * @description 封装msg方法
   * @param {object|string} param1 配置参数,请求方法参数
   * @param {number} param2 图标ID
   * @require 当前关闭弹窗方法
   */
  msg: function (param1, param2) {
    var layerT = null,
      msg = '',
      config = {};
    if (typeof param1 === "object") {
      if (typeof param1.status === "boolean") {
        msg = param1.msg, config = { icon: param1.status ? 1 : 2 };
        if (!param1.status) config = $.extend(config, { time: (!param2 ? 0 : 3000), closeBtn: 2, shade: .3 });
      }
    }
    if (typeof param1 === "string") {
      msg = param1, config = {
        icon: typeof param2 !== 'undefined' ? param2 : 1
      }
    }
    layerT = layer.msg(msg, config);
    return {
      close: function () {
        layer.close(layerT);
      }
    }
  },
  /**
   * @description 请求封装
   * @param {string|object} conifg ajax配置参数/请求地址
   * @param {function|object} callback 回调函数/请求参数
   * @param {function} callback1 回调函数/可为空
   * @returns void 无
   */
  send: function (param1, param2, param3, param4, param5, param6) {
    var params = {},
      success = null,
      error = null,
      config = [],
      param_one = '';
    $.each(arguments, function (index, items) {
      config.push([items, typeof items]);
    });
    function diff_data (i) {
      try {
        success = config[i][1] == "function" ? config[i][0] : null;
        error = config[(i + 1)][1] == "function" ? config[(i + 1)][0] : null;
      } catch (error) { }
    }
    param_one = config[0];
    switch (param_one[1]) {
      case "string":
        $.each(config, function (index, items) {
          var value = items[0], type = items[1];
          if (index > 1 && (type == "boolean" || type == "string" || type == "object")) {
            var arry = param_one[0].split('/');
            params['url'] = '/' + arry[0] + '?action=' + arry[1];
            if (type == "object") {
              params['load'] = value.load;
              params['verify'] = value.verify;
              if (value.plugin) params['url'] = '/plugin?action=a&name=' + arry[0] + '&s=' + arry[1];
            } else if (type == 'string') {
              params['load'] = value;
            }
            return false;
          } else {
            params['url'] = param_one[0];
          }
        });
        if (config[1][1] === "object") {
          params['data'] = config[1][0];
          diff_data(2);
        } else {
          diff_data(1);
        }
        break;
      case 'object':
        params['url'] = param_one[0].url;
        params['data'] = param_one[0].data || {};
        $.each(config, function (index, items) {
          var value = items[0], type = items[1];
          if (index > 1 && (type == "boolean" || type == "string" || type == "object")) {
            switch (type) {
              case "object":
                params['load'] = value.load;
                params['verify'] = value.verify;
                break;
              case "string":
                params['load'] = value;
                break;
            }
            return true;
          }
        });
        if (config[1][1] === "object") {
          params['data'] = config[1][0];
          diff_data(2);
        } else {
          diff_data(1);
        }
        break;
    }
    if (params.load) params.load = this.load(params.load);
    $.ajax({
      type: params.type || "POST",
      url: params.url,
      data: params.data || {},
      dataType: params.dataType || "JSON",
      complete: function (res) {
        if (params.load) params.load.close();
      },
      success: function (res) {
        if (typeof params.verify == "boolean" && !params.verify) {
          if (success) success(res);
          return false;
        }
        if (typeof res === "string") {
          layer.msg(res, {
            icon: 2,
            time: 0,
            closeBtn: 2
          });
          return false;
        }
        if (params.batch) {
          if (success) success(res);
          return false;
        }
        if (res.status === false && (res.hasOwnProperty('msg') || res.hasOwnProperty('error_msg'))) {
          if (error) {
            error(res)
          } else {
            bt_tools.msg({ status: res.status, msg: !res.hasOwnProperty('msg') ? res.error_msg : res.msg });
          }
          return false;
        }

        if (params.tips) {
          bt_tools.msg(res);
        }
        if (success) success(res);
      }
    });
  },


  /**
   * @description 命令行输入
   */
  command_line_output: function (config) {
    var _that = this, uuid = bt.get_random(15);

    /**
     * @description 渲染
     * @param config
     * @return {object}
     * @constructor
     */
    function ReaderCommand (config) {
      var that = this;
      for (var key in _that.commandConnectionPool) {
        var item = _that.commandConnectionPool[key], element = $(item.config.el)
        if (config.shell === item.config.shell && element.length) {
          item.el = element
          return item
        }
      }
      if (typeof config === "undefined") config = {}
      this.config = $.extend({ route: '/sock_shell' }, config)
      this.xterm_config = $.extend(this.xterm_config, this.config.xterm)
      this.el = $(this.config.el);
      this.open = config.open;
      this.close = config.close;
      this.message = config.message;
      if (!this.config.hasOwnProperty('el')) {
        _that.msg({ msg: '请输入选择器element，不可为空', status: false })
        return false;
      }
      if (!this.config.hasOwnProperty('shell')) {
        _that.msg({ msg: '请输入命令，不可为空', status: false })
        return false;
      }
      if (this.config.hasOwnProperty('time')) {
        setTimeout(function () {
          that.close_connect()
        }, this.config.time)
      }
      this.init()
    }
    ReaderCommand.prototype = {
      socket: null, //websocket 连接保持的对象
      socketToken: null,
      timeout: 0, // 连接到期时间，为0代表永久有效
      monitor_interval: 2000,
      element_detection: null,
      uuid: uuid,
      fragment: [],
      error: 0, // 错误次数，用于监听元素内容是否还存在
      retry: 0, // 重试次数
      forceExit: false, // 强制断开连接
      /**
       * @description 程序初始化
       */
      init: function () {
        var oldUUID = bt.get_cookie('commandInputViewUUID'), that = this;
        if (!this.el[0]) {
          if (this.error > 10) return false;
          setTimeout(function () {
            that.init()
            this.error++;
          }, 2000)
          return false;
        }
        this.error = 0
        if (this.el[0].localName !== 'pre') {
          this.el.append('<pre class="command_output_pre"></pre>');
          this.el = this.el.find('pre');
          this.config.el = this.config.el + ' pre'
        } else {
          this.el.addClass('command_output_pre');
        }
        if (Array.isArray(this.config.area)) {
          this.el.css({ width: this.config.area[0], height: this.config.area[1] })
        } else {
          this.el.css({ width: '100%', height: '100%' })
        }
        if (oldUUID && typeof _that.commandConnectionPool[oldUUID] != "undefined") {
          _that.commandConnectionPool[oldUUID].close_connect();
          delete _that.commandConnectionPool[oldUUID];
        }
        bt.set_cookie('commandInputViewUUID', this.uuid);
        this.element_detection = setInterval(function () {
          if (!$(that.config.el).length) {
            clearInterval(that.element_detection)
            that.forceExit = true;
            that.close_connect();
          }
        }, 1 * 60 * 1000)
        this.set_full_screen()
        this.create_websocket_connect(this.config.route, this.config.shell)
        this.monitor_element()
      },
      /**
       * @description 创建websocket连接
       * @param {string} url websocket连接地址
       * @param {string} shell 需要传递的命令
       */
      create_websocket_connect: function (url, shell) {
        var that = this;
        this.socket = new WebSocket((location.protocol === 'http:' ? 'ws://' : 'wss://') + location.host + url)
        this.socket.addEventListener('open', function (ev) {
          if (!this.socketToken) {
            var _token = document.getElementById('request_token_head').getAttribute('token');
            this.socketToken = { 'x-http-token': _token }
          }
          this.send(JSON.stringify(this.socketToken))
          this.send(shell)
          if (that.open) that.open()
          that.retry = 0
        });
        this.socket.addEventListener('close', function (ev) {
          if (!that.forceExit) {
            if (ev.code !== 1000 && that.retry <= 10) {
              that.socket = that.create_websocket_connect(that.config.route, that.config.shell)
              that.retry++;
            }
            if (that.close) that.close(ev)
          }
        });
        this.socket.addEventListener('message', function (ws_event) {
          var result = ws_event.data
          if (!result) return;
          that.refresh_data(result)
          if (that.message) that.message(result)

        })
        return this.socket
      },

      /**
       * @description 设置全屏视图
       */
      set_full_screen: function () {
        // 1
      },

      htmlEncodeByRegExp: function (str) {
        if (str.length == 0) return "";
        return str.replace(/&/g, "&amp;")
          .replace(/</g, "&lt;")
          .replace(/>/g, "&gt;")
          .replace(/ /g, "&nbsp;")
          .replace(/\'/g, "&#39;")
          .replace(/\"/g, "&quot;");
      },

      /**
       * @description 刷新Pre数据
       * @param {object} data 需要插入的数据
      */
      refresh_data: function (data) {
        var rdata = this.htmlEncodeByRegExp(data);
        this.fragment.push(rdata)
        if (this.fragment.length >= 300) {
          this.fragment.splice(0, 150)
          this.el.html(this.fragment.join(''))
        } else {
          console.log(data)
          this.el.append(rdata)
        }
        this.el.scrollTop(this.el[0].scrollHeight)
      },

      /**
       * @description 监听元素状态，判断是否移除当前的ws连接
       *
       */
      monitor_element: function () {
        var that = this;
        this.monitor_interval = setInterval(function () {
          if (!that.el.length) {
            that.close_connect()
            clearInterval(that.monitor_interval)
          }
        }, that.config.monitorTime || 2000)
      },

      /**
       * @description 断开命令响应和websocket连接
       */
      close_connect: function () {
        this.socket.send('')
        this.socket.close()
        delete _that.commandConnectionPool[this.uuid];
      }
    }
    this.commandConnectionPool[uuid] = new ReaderCommand(config)
    return this.commandConnectionPool[uuid]
  },



  /**
   * @description 清理验证提示样式
   * @param {object} element  元素节点
  */
  $clear_verify_tips: function (element) {
    element.removeClass('bt-border-error bt-border-sucess');
    layer.close('tips');
  },

  /**
   * @description 验证提示
   * @param {object} element  元素节点
   * @param {string} tips 警告提示
   * @return void
  */
  $verify_tips: function (element, tips, is_error) {
    if (typeof is_error === "undefined") is_error = true;
    element.removeClass('bt-border-error bt-border-sucess').addClass(is_error ? 'bt-border-error' : 'bt-border-sucess');
    element.focus();
    layer.tips('<span class="inlineBlock">' + tips + "</span>", element, { tips: [1, is_error ? 'red' : '#20a53a'], time: 3000, area: element.width() });
  },
  /**
   * @description 验证值是否存在
   * @param {String} value 内容/值
   * @param {String|Boolean} attr 属性
   * @param {String} type 属性
  */
  $verify: function (value, attr, type) {
    if (!value) return '';
    if (type === true) return value ? ' ' + attr : '';
    if (type === 'style') return attr ? attr + ':' + value + ';' : value;
    return attr ? ' ' + attr + '="' + value + '"' : ' ' + value;
  },

  /**
   * @description 批量操作的结果
   * @param {*} config
  */
  $batch_success_table: function (config) {
    var _that = this, length = $(config.html).length;
    bt.open({
      type: 1,
      title: config.title,
      area: config.area || ['350px', '350px'],
      shadeClose: false,
      closeBtn: 2,
      content: config.content || '<div class="batch_title"><span class><span class="batch_icon"></span><span class="batch_text">' + config.title + '操作完成！</span></span></div><div class="' + (length > 4 ? 'fiexd_thead' : '') + ' batch_tabel divtable" style="margin: 15px 30px 15px 30px;overflow: auto;height: 200px;"><table class="table table-hover"><thead><tr><th>' + config.th + '</th><th style="text-align:right;width:120px;">操作结果</th></tr></thead><tbody>' + config.html + '</tbody></table></div>',
      success: function () {
        if (length > 4) _that.$fixed_table_thead('.fiexd_thead');
      }
    });
  },
  /**
   * @description 固定表头
   * @param {string} el DOM选择器
   * @return void
  */
  $fixed_table_thead: function (el) {
    $(el).scroll(function () {
      var scrollTop = this.scrollTop;
      this.querySelector('thead').style.transform = 'translateY(' + scrollTop + 'px)';
    });
  },
  /**
   * @description 插件视图设置
   * @param {object|string} layid dom元素或layer_id
   * @param {object} config 插件宽度高度或其他配置
  */
  $piugin_view_set: function (layid, config) {
    var element = $(typeof layid === "string" ? ('#layui-layer' + layid) : layid).hide(), win = $(window);
    setTimeout(function () {
      var width = config.width || element.width(), height = config.height || element.height();
      element.css($.extend(config, { left: ((win.width() - width) / 2), top: ((win.height() - height) / 2) })).addClass('custom_layer');
    }, 50);
    setTimeout(function () { element.show(); }, 500)
  }
};
$.fn.serializeObject = function () {
  var hasOwnProperty = Object.prototype.hasOwnProperty;
  return this.serializeArray().reduce(function (data, pair) {
    if (!hasOwnProperty.call(data, pair.name)) {
      data[pair.name] = pair.value;
    }
    return data;
  }, {});
};

function arryCopy (arrys) {
  var list = arrys.concat(), arry = []
  for (var i = 0; i < list.length; i++) {
    arry.push($.extend(true, {}, list[i]))
  }
  return arry
}

















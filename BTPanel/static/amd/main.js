/*
 * @Description: Require.js主配置文件
 * @Version: 1.0
 * @Autor: chudong
 * @Date: 2021-11-30 09:59:13
 * @LastEditors: chudong
 * @LastEditTime: 2021-12-05 22:59:36
 */

require.config({
  paths: {
    "jquery": "../js/jquery-2.2.4.min", // Jquery
    "layer": "../layer/layer", // 弹窗
    "utils": "./utils.min", // 工具库
    "home": "home", // 首页代码
    "site": "site", // 站点代码
    "ftp": "ftp", // ftp代码
    "database": "database", // 数据库代码
    "control": "control", // 监控
    "firewall": "firewall", // 系统安全
    "files": "files", // 文件管理
    "xterm": "xterm", // 终端管理
    "crontab": "crontab", // 计划任务
    "soft": "soft", // 软件管理
    "config": "config.min", // 面板设置
    "jquery.qrcode": "../js/jquery.qrcode.min", // 二维码
    "language": "../language/Simplified_Chinese/lan", // 语言包
    "clipboard": "../js/clipboard.min", // 复制
    "public": "../js/public", // 公共方法
    "public_backup": "../js/public_backup", // 公共方法
  },
  shim: {
    "public":{
      exports:'aceEditor'
    },
    "public_backup":{
      exports:'bt'
    },
    "language": {
      exports: "lan"
    },
    "jquery.qrcode": {  // 二维码插件
      deps: ["jquery"],
      exports: "jQuery.fn.qrcode"
    }
  }
})

require(['jquery', 'layer', 'language', 'utils', 'public', 'public_backup'], function () {
  switch (location.pathname) {
    case "/config":
      require(['config'], function (param1) {
        var Config = param1['Config']
        new Config()
      })
      break
  }
})
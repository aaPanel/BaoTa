# 第三方 Nginx 接入方案

## 方案概述
本方案核心目标是**读取第三方 Nginx 实例及全量配置文件**，通过解析、分类、重构，生成符合面板规范的配置（支持 PHP 项目、反向代理、静态 HTML 项目），实现第三方 Nginx 无缝对接面板管理。

---

## 一、模块架构

### 目录结构
```
mod/base/pynginx/
├── nginx_base.py        # 基础类定义（Token、Directive、Block等）
├── nginx_parser.py      # 词法/语法解析器
├── nginx_components.py  # Nginx组件实现（Http、Server、Location、Upstream等）
├── nginx_config.py      # Config和Include类
├── extension/           # 配置操作扩展工具
│   ├── config.py        # 配置查找工具（ConfigFinder、ConfigTools）
│   ├── server.py        # Server块操作工具（ServerTools）
│   ├── location.py      # Location块操作工具
│   ├── nginx_info.py    # Nginx信息获取
│   └── utils.py         # 工具函数
└── btnginx/             # 第三方Nginx接入实现
    ├── nginx_detector.py # Nginx实例探测器
    ├── site_detector.py  # 站点配置分离与分类
    ├── bt_formater.py    # 面板兼容配置格式化
    ├── create_site.py    # 面板站点创建工具
    ├── rel2real_path.py  # 相对路径转绝对路径
    └── panel_utils.py    # 面板工具函数
```

### 核心类关系
```
┌─────────────┐     解析      ┌─────────────┐
│ nginx.conf  │ ───────────▶  │   Config    │
└─────────────┘               └──────┬──────┘
                                     │
                    ┌────────────────┼────────────────┐
                    ▼                ▼                ▼
              ┌──────────┐    ┌──────────┐    ┌──────────┐
              │   Http   │    │ Upstream │    │ Include  │
              └────┬─────┘    └──────────┘    └──────────┘
                   │
                   ▼
              ┌──────────┐
              │  Server  │ ───▶ SiteInfo (站点信息)
              └────┬─────┘
                   │
        ┌──────────┼──────────┐
        ▼          ▼          ▼
   ┌──────────┐ ┌──────────┐ ┌──────────┐
   │ Location │ │ Location │ │  指令...  │
   └──────────┘ └──────────┘ └──────────┘
```

---

## 二、Nginx 实例定位策略

### 1. 进程名称匹配
直接扫描系统运行进程，匹配 `nginx` 进程标识。
通过进程信息反推核心路径：可执行文件路径 + 主配置文件（nginx.conf）路径。

### 2. 常见路径兜底扫描
若进程匹配未命中，遍历行业通用安装路径：
- `/usr/sbin/nginx`
- `/usr/local/nginx/sbin/nginx`
- `/www/server/nginx/sbin/nginx`
- `/opt/nginx/sbin/nginx`

### 使用示例
```python
from mod.base.pynginx.btnginx.nginx_detector import ng_detect, ng_detect_by_bin

# 获取所有Nginx实例
instances = ng_detect()
for ins in instances:
    print(f"可执行文件: {ins.nginx_bin}")
    print(f"配置文件: {ins.nginx_conf}")
    print(f"版本: {ins.version}")
    print(f"运行状态: {ins.running}")

# 仅获取运行中的实例
running_instances = ng_detect(only_running=True)

# 通过可执行文件路径获取实例
ins = ng_detect_by_bin("/usr/local/nginx/sbin/nginx")
```

---

## 三、配置文件全量解析

### 解析能力
- 解析范围：主配置文件（nginx.conf）+ 所有通过 `include` 指令引入的子配置文件（含多级嵌套引入）。
- 解析目标：提取配置结构树（全局块、http 块、server 块、location 块等）、指令参数、注释信息。
- 特殊支持：Lua代码块（`*_by_lua_block`）解析。

### 使用示例
```python
from mod.base.pynginx import parse_file, parse_string, dump_config

# 从文件解析（不解析include）
config = parse_file("/etc/nginx/nginx.conf")

# 从文件解析（递归解析include）
config = parse_file(
    "/etc/nginx/nginx.conf",
    parse_include=True,
    main_config_path="/etc/nginx"  # 用于定位include相对路径
)

# 从字符串解析
config = parse_string("""
server {
    listen 80;
    server_name example.com;
    root /var/www/html;
}
""")

# 查找所有server块
servers = config.find_servers()

# 查找http块
http = config.find_http()

# 查找所有upstream块
upstreams = config.find_upstreams()

# 导出配置为字符串
content = dump_config(config)
```

### 指令查找
```python
from mod.base.pynginx import Config

# 查找指定指令
listen_dirs = server_block.find_directives("listen")

# 查找指令（包含include子块）
server_dirs = http_block.find_directives("server", include=True)

# 查找指令（包含所有子块）
all_proxy_pass = server_block.find_directives("proxy_pass", include=True, sub_block=True)
```

---

## 四、站点配置分离与分类

从解析后的全量配置中，提取所有 `http -> server` 虚拟主机块，按"服务类型"分类、"域名规则"聚合：

### 1. 服务类型判定标准
- **PHP 项目**：配置中存在 `fastcgi_pass` 指令（关联 PHP-FPM 服务）。
- **反向代理项目**：配置中存在 `proxy_pass` 指令（指向后端服务地址）。
- **静态项目**：不满足上述两类条件，默认判定为静态资源服务。

### 2. 虚拟主机聚合规则
- 相同 `server_name` 则合并为一个站点配置（统一管理 HTTP/HTTPS 规则）。

### 使用示例
```python
from mod.base.pynginx import parse_file
from mod.base.pynginx.btnginx.site_detector import site_detector, SiteInfo

# 解析配置
config = parse_file("/etc/nginx/nginx.conf", parse_include=True)

# 检测站点
sites = site_detector(config)

for site in sites:
    print(f"域名: {site.server_names}")
    print(f"端口: {site.listen_ports}")
    print(f"类型: {site.site_type}")  # PHP/反向代理/静态
```

---

## 五、面板兼容配置生成

基于解析后的原始配置，进行"结构调整 + 功能增强"，生成符合面板使用规范的配置文件。

### 配置文件调整
1. **主配置文件调整**
   - 直接保留：非 `http` 块的所有全局配置
   - 条件保留：`http` 块中不含 `server` 块的 `include` 文件
   - 强制注入：面板必需的基础指令和标记

2. **站点配置功能增强**
   - 解析展开：将所有 `include` 引用的子配置直接展开
   - 插入关键标识位：SSL证书配置、PHP关联配置等
   - 结构重组：按规范顺序组织配置

### 使用示例
```python
from mod.base.pynginx.btnginx.bt_formater import bt_nginx_format
from mod.base.pynginx.btnginx.nginx_detector import ng_detect

# 获取Nginx实例
nginx_ins = ng_detect(only_running=True)[0]

# 创建格式化器， 解析并生成面板兼容配置
result = bt_nginx_format(nginx_ins)

# result包含:
# - site_conf: 站点配置信息列表
# - tmp_path: 临时配置文件目录
# - main_conf_path: 主配置文件路径
```

---

## 六、核心API参考

### nginx_base.py - 基础类

| 类/函数         | 说明                                    |
|--------------|---------------------------------------|
| `Token`      | 词法标记，包含类型、内容、行号、列号                    |
| `TokenType`  | 标记类型枚举（EOF, KEYWORD, QUOTED_STRING等）  |
| `Directive`  | 指令实现，包含name、parameters、block、comment等 |
| `Block`      | 块实现，包含directives列表                    |
| `IDirective` | 指令接口定义                                |
| `IBlock`     | 块接口定义                                 |

### nginx_parser.py - 解析器

| 函数                                                                      | 说明       |
|-------------------------------------------------------------------------|----------|
| `parse_file(path, parse_include, main_config_path, comment_line_count)` | 从文件解析配置  |
| `parse_string(content, parse_include, comment_line_count)`              | 从字符串解析配置 |
| `dump_config(config, style)`                                            | 导出配置为字符串 |
| `dump_block(block, style)`                                              | 导出块为字符串  |

### nginx_components.py - 组件类

| 类                | 说明                 |
|------------------|--------------------|
| `Http`           | HTTP块组件            |
| `Server`         | Server块组件          |
| `Location`       | Location块组件        |
| `Upstream`       | Upstream块组件        |
| `UpstreamServer` | Upstream中的server指令 |
| `LuaBlock`       | Lua代码块组件           |

### nginx_detector.py - Nginx探测器

| 函数                           | 说明            |
|------------------------------|---------------|
| `ng_detect(only_running)`    | 获取所有Nginx实例   |
| `ng_detect_by_bin(bin_path)` | 通过可执行文件路径获取实例 |

### site_detector.py - 站点检测器

| 类/函数                    | 说明                                                            |
|-------------------------|---------------------------------------------------------------|
| `SiteInfo`              | 站点信息数据类（server_names, listen_ports, site_type, server_blocks） |
| `SiteDetector`          | 站点检测器类                                                        |
| `site_detector(config)` | 检测并分类所有站点配置                                                   |

### extension/config.py - 配置工具

| 类              | 说明                      |
|----------------|-------------------------|
| `ConfigTools`  | 配置基础工具（获取主server、导出字符串） |
| `ConfigFinder` | 配置查找工具（查找域名、端口、IP限制等）   |

### extension/server.py - Server块工具

| 类             | 说明                         |
|---------------|----------------------------|
| `ServerTools` | Server块操作工具（设置SSL端口、移除域名等） |

---

## 七、完整工作流程

```python
# 1. 探测Nginx实例
from mod.base.pynginx.btnginx.nginx_detector import ng_detect
nginx_instances = ng_detect(only_running=True)

if not nginx_instances:
    print("未找到运行中的Nginx实例")
    exit()

nginx_ins = nginx_instances[0]

# 2. 解析配置文件
from mod.base.pynginx.btnginx.bt_formater import bt_nginx_format

# 3. 格式化为面板兼容配置
result = bt_nginx_format(nginx_ins)

# 4. 查看识别到的站点
for site in result['site_conf']:
    print(f"站点: {site['name']}")
    print(f"  类型: {site['site_type']}")
    print(f"  域名: {site['domains']}")
    print(f"  端口: {site['ports']}")

# 5. 在面板中创建站点
from mod.base.pynginx.btnginx.create_site import CreateSiteUtil
util = CreateSiteUtil(result['tmp_path'])

for site in result['site_conf']:
    if site['site_type'] == 'PHP':
        util.create_php_site(site)
    elif site['site_type'] == 'proxy':
        util.create_proxy_site(site)
    else:
        util.create_static_site(site)
```

---

## 八、注意事项

1. **路径解析**：解析include文件时需指定`main_config_path`参数，否则相对路径无法正确解析。
2. **Lua块支持**：支持`*_by_lua_block`指令的解析和格式化。
3. **注释保留**：默认保留指令前1行注释，可通过`comment_line_count`参数调整。
4. **配置验证**：探测器会执行`nginx -t`验证配置有效性。

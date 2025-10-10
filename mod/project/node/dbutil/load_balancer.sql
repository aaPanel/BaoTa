-- load_sites 负载均衡网站
CREATE TABLE IF NOT EXISTS `load_sites`
(
    `load_id`     INTEGER PRIMARY KEY AUTOINCREMENT, -- 负载均衡ID
    `name`        TEXT    NOT NULL UNIQUE,           -- 负载均衡名称
    `site_id`     INTEGER NOT NULL DEFAULT 0,        -- 站点ID
    `site_name`   TEXT    NOT NULL ,           -- 站点名称，网站主域名
    `site_type`   TEXT    NOT NULL DEFAULT 'http',   -- http, tcp (http:代表http负载均衡，tcp:代表tcp/udp负载均衡)
    `ps`          TEXT    NOT NULL DEFAULT '',
    `http_config` TEXT    NOT NULL DEFAULT '{"proxy_next_upstream":"error timeout http_500 http_502 http_503 http_504","http_alg":"sticky_cookie"}',
    `tcp_config`  TEXT    NOT NULL DEFAULT '{"proxy_connect_timeout":8,"proxy_timeout":86400,"host":"127.0.0.1","port":80,"type":"tcp"}',
    `created_at`  TIMESTAMP        DEFAULT CURRENT_TIMESTAMP
);

-- http_nodes
CREATE TABLE IF NOT EXISTS `http_nodes`
(
    `id`             INTEGER PRIMARY KEY AUTOINCREMENT,
    `load_id`        INTEGER NOT NULL DEFAULT 0,        -- 负载均衡ID
    `node_id`        INTEGER NOT NULL DEFAULT 0,        -- 节点ID
    `node_site_id`   INTEGER NOT NULL DEFAULT 0,        -- 节点上的网站ID
    `node_site_name` TEXT    NOT NULL DEFAULT '',       -- 节点上的网站名称
    `port`           INTEGER NOT NULL DEFAULT 0,        -- 端口
    `location`       TEXT    NOT NULL DEFAULT '/',      -- 实施代理的路由， 默认是根路由 '/' 当前版本也只支持根路由
    `path`           TEXT    NOT NULL DEFAULT '/',      -- 访问验证路径
    `node_status`    TEXT    NOT NULL DEFAULT 'online', -- 节点状态 online, backup, down
    `weight`         INTEGER NOT NULL DEFAULT 1,        -- 权重
    `max_fail`       INTEGER NOT NULL DEFAULT 0,        -- 最大失败次数
    `fail_timeout`   INTEGER NOT NULL DEFAULT 0,        -- 失败恢复时间
    `max_conns`      INTEGER NOT NULL DEFAULT 0,        -- 最大连接数
    `ps`             TEXT    NOT NULL DEFAULT '',
    `created_at`     TIMESTAMP        DEFAULT CURRENT_TIMESTAMP
);

-- tcp_nodes
CREATE TABLE IF NOT EXISTS `tcp_nodes`
(
    `id`           INTEGER PRIMARY KEY AUTOINCREMENT,
    `load_id`      INTEGER NOT NULL DEFAULT 0,        -- 负载均衡ID
    `node_id`      INTEGER NOT NULL DEFAULT 0,        -- 节点ID
    `host`         TEXT    NOT NULL,
    `port`         INTEGER NOT NULL DEFAULT 0,
    `node_status`  TEXT    NOT NULL DEFAULT 'online', -- 节点状态 online, backup, down
    `weight`       INTEGER NOT NULL DEFAULT 1,
    `max_fail`     INTEGER NOT NULL DEFAULT 0,
    `fail_timeout` INTEGER NOT NULL DEFAULT 0,
    `ps`           TEXT    NOT NULL DEFAULT '',
    `created_at`   TIMESTAMP        DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS `load_sites_name` ON `load_sites` (`name`);
CREATE INDEX IF NOT EXISTS `load_sites_site_type` ON `load_sites` (`site_type`);
CREATE INDEX IF NOT EXISTS `http_nodes_load_id` ON `http_nodes` (`load_id`);
CREATE INDEX IF NOT EXISTS `tcp_nodes_load_id` ON `tcp_nodes` (`load_id`);
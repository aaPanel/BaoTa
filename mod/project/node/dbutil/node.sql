CREATE TABLE IF NOT EXISTS `node`
(
    `id`          INTEGER PRIMARY KEY AUTOINCREMENT,
    `address`     VARCHAR,                   -- 节点地址 https://xxx:xx/
    `category_id` INTEGER,                   -- 分类
    `remarks`     VARCHAR,                   -- 节点名称
    `api_key`     VARCHAR,                   -- api key
    `create_time` INTEGER       DEFAULT (0), -- 创建时间
    `server_ip`   TEXT,                      -- 服务器ip
    `status`      INTEGER,                   -- 0: 不在线 1: 在线
    `error`       TEXT          DEFAULT '{}',
    `error_num`   INTEGER       DEFAULT 0,
    `app_key`     TEXT,                      -- app key
    `ssh_conf`    TEXT NOT NULL DEFAULT '{}',
    `ssh_test`    INTEGER       DEFAULT 0,   -- 是否执行了ssh秘钥测试， 0: 未测试 1: 已测试
    `lpver`       TEXT          DEFAULT ''   -- 1panel  版本,当目标面板时1panel时，记录版本是v1还是v2
);

CREATE TABLE IF NOT EXISTS `category`
(
    `id`          INTEGER PRIMARY KEY AUTOINCREMENT,
    `name`        VARCHAR,
    `create_time` INTEGER DEFAULT (0)
);

INSERT INTO `node` (app_key, api_key, remarks, server_ip)
SELECT 'local', 'local', '本机节点', '127.0.0.1'
WHERE NOT EXISTS (SELECT 1 FROM `node` WHERE app_key = 'local' AND api_key = 'local');

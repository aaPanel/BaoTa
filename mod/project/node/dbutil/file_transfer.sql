-- 传输任务表
CREATE TABLE IF NOT EXISTS transfer_tasks
(
    task_id          INTEGER PRIMARY KEY AUTOINCREMENT,
    source_node      TEXT    NOT NULL DEFAULT '{}', -- {"address":"https:/xxxx", "api_key":"xxxxx", "name":"xxxx"}
    target_node      TEXT    NOT NULL DEFAULT '{}', -- {"address":"https:/xxxx", "api_key":"xxxxx", "name":"xxxx"}
    source_path_list TEXT    NOT NULL DEFAULT '[]', -- 源节点上的路径 [{"path":"/www/wwwroot/aaaa", "is_dir":true}]
    target_path      TEXT    NOT NULL,              -- 目标节点上的路径
    task_action      TEXT    NOT NULL,              -- upload/download
    status           TEXT    NOT NULL,              -- pending/running/completed/failed
    default_mode     TEXT    NOT NULL,              -- 默认处理模式  cover: 覆盖，ignore: 跳过，rename:重命名
    created_at       TIMESTAMP        DEFAULT CURRENT_TIMESTAMP,
    started_at       TIMESTAMP,
    completed_at     TIMESTAMP,
    created_by       TEXT    NOT NULL,              -- 创建的节点名称
    target_task_id   INTEGER NOT NULL,
    is_source_node   BOOLEAN NOT NULL,              -- 是否为本节点发送
    is_target_node   BOOLEAN NOT NULL               -- 是否为本节点接收
);

-- 文件传输详情表
CREATE TABLE IF NOT EXISTS file_transfers
(
    transfer_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    task_id      INTEGER NOT NULL,
    src_file     TEXT    NOT NULL,           -- 源文件
    dst_file     TEXT    NOT NULL,           -- 目标文件
    file_size    INTEGER NOT NULL,           -- 文件大小
    is_dir       INTEGER NOT NULL DEFAULT 0,
    status       TEXT    NOT NULL,           -- pending/running/completed/failed
    progress     INTEGER          DEFAULT 0, -- 0-100
    message      TEXT    NOT NULL DEFAULT '',
    created_at   TIMESTAMP        DEFAULT CURRENT_TIMESTAMP,
    started_at   TIMESTAMP,
    completed_at TIMESTAMP
);

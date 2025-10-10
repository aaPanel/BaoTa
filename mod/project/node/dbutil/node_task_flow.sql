-- 创建脚本表
CREATE TABLE IF NOT EXISTS scripts
(
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL CHECK (length(name) <= 255),
    script_type TEXT    NOT NULL CHECK (length(script_type) <= 255),
    content     TEXT    NOT NULL,
    description TEXT,
    created_at  INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at  INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- 创建任务流
CREATE TABLE IF NOT EXISTS flows
(
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    server_ids TEXT    NOT NULL, -- 存储服务器ID列表
    step_count INTEGER NOT NULL,
    strategy   TEXT    NOT NULL, -- 对于不同任务的处理策略， json字段
    status     TEXT    NOT NULL, -- 总体状态  waiting, running, complete, error
    created_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- 创建命令行任务表
CREATE TABLE IF NOT EXISTS command_tasks
(
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id        INTEGER NOT NULL,
    name           TEXT    NOT NULL CHECK (length(name) <= 255),
    step_index     INTEGER NOT NULL,
    script_id      INTEGER NOT NULL,
    script_content TEXT    NOT NULL,
    script_type    TEXT    NOT NULL CHECK (length(script_type) <= 255),
    status         INTEGER NOT NULL DEFAULT 0 CHECK (status IN (0, 1, 2, 3)), -- 0: 等待中, 1: 进行中, 2: 成功, 3: 失败
    created_at     INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at     INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- 创建命令行任务日志表
CREATE TABLE IF NOT EXISTS command_logs
(
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    command_task_id INTEGER NOT NULL,
    server_id       INTEGER NOT NULL,
    ssh_host        TEXT    NOT NULL,
    status          INTEGER NOT NULL DEFAULT 0 CHECK (status IN (0, 1, 2, 3, 4)), -- 0: 等待中, 1: 进行中, 2: 成功, 3: 失败, 4: 异常
    log_name        TEXT    NOT NULL CHECK (length(log_name) <= 255)
);

-- 传输任务表
CREATE TABLE IF NOT EXISTS transfer_tasks
(
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    name             TEXT    NOT NULL CHECK (length(name) <= 255),
    flow_id          INTEGER NOT NULL,                                          -- 当本机不是数据源节点时， 本字段的值为 0
    step_index       INTEGER NOT NULL,
    src_node         TEXT    NOT NULL,                                          -- 数据源节点， json字段
    src_node_task_id INTEGER NOT NULL,                                          -- 当本机是数据源节点时， 本字段的值为 0， 否则为目标机器上的transfer_tasks.id
    dst_nodes        TEXT    NOT NULL,                                          -- 目标节点，多个，json字段
    message          TEXT    NOT NULL DEFAULT '',                               -- 与目标节点的链接错误信息
    path_list        TEXT    NOT NULL DEFAULT '[]',                             -- 源节点上的路径 [{"path":"/www/wwwroots", "is_dir":true}]
    status           INTEGER NOT NULL DEFAULT 0 CHECK (status IN (0, 1, 2, 3)), -- 0: 等待中, 1: 进行中, 2: 成功, 3: 失败
    created_at       INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    updated_at       INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- 传输文件列表
CREATE TABLE IF NOT EXISTS transfer_files
(
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id          INTEGER NOT NULL,
    transfer_task_id INTEGER NOT NULL,
    src_file         TEXT    NOT NULL, -- 源文件
    dst_file         TEXT    NOT NULL, -- 目标文件
    file_size        INTEGER NOT NULL, -- 文件大小
    is_dir           INTEGER NOT NULL DEFAULT 0
);


-- 传输文件列表
CREATE TABLE IF NOT EXISTS transfer_logs
(
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id          INTEGER NOT NULL,
    transfer_task_id INTEGER NOT NULL,
    transfer_file_id INTEGER NOT NULL,
    dst_node_idx     INTEGER NOT NULL,                                             -- 目标节点索引，基于 transfer_tasks.dst_nodes
    status           INTEGER NOT NULL DEFAULT 0 CHECK (status IN (0, 1, 2, 3, 4)), -- 0: 等待中, 1: 进行中, 2: 成功, 3: 失败, 4: 跳过
    progress         INTEGER          DEFAULT 0,                                   -- 0-100
    message          TEXT    NOT NULL DEFAULT '',
    created_at       INTEGER NOT NULL DEFAULT (strftime('%s', 'now')),
    started_at       INTEGER,
    completed_at     INTEGER
);

CREATE INDEX IF NOT EXISTS idx_scripts_name ON scripts (name);
CREATE INDEX IF NOT EXISTS idx_scripts_description ON scripts (description);

CREATE INDEX IF NOT EXISTS idx_flow_server_ids ON flows (server_ids);

-- command_tasks 表
CREATE INDEX IF NOT EXISTS idx_command_tasks_flow_id ON command_tasks (flow_id);
CREATE INDEX IF NOT EXISTS idx_command_tasks_script_id ON command_tasks (script_id);

-- command_logs 表
CREATE INDEX IF NOT EXISTS idx_command_logs_task_id ON command_logs (command_task_id);
CREATE INDEX IF NOT EXISTS idx_command_logs_server_id ON command_logs (server_id);
-- command_logs 状态查询
CREATE INDEX IF NOT EXISTS idx_command_logs_status ON command_logs (command_task_id, status);

-- transfer_tasks 表
CREATE INDEX IF NOT EXISTS idx_transfer_tasks_flow_id ON transfer_tasks (flow_id);
CREATE INDEX IF NOT EXISTS idx_transfer_tasks_src_node_task_id ON transfer_tasks (src_node_task_id);

-- transfer_files 表
CREATE INDEX IF NOT EXISTS idx_transfer_files_task_id ON transfer_files (transfer_task_id);

-- transfer_logs 表
CREATE INDEX IF NOT EXISTS idx_transfer_logs_flow_id ON transfer_logs (flow_id);
CREATE INDEX IF NOT EXISTS idx_transfer_logs_task_id ON transfer_logs (transfer_task_id);
CREATE INDEX IF NOT EXISTS idx_transfer_logs_file_id ON transfer_logs (transfer_file_id);
-- transfer_logs 状态查询
CREATE INDEX IF NOT EXISTS idx_transfer_logs_status ON transfer_logs (transfer_file_id, status);





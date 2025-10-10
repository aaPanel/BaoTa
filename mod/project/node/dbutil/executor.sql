
-- 创建脚本表
CREATE TABLE IF NOT EXISTS scripts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK(length(name) <= 255),
    script_type TEXT NOT NULL CHECK(length(script_type) <= 255),
    content TEXT NOT NULL,
    description TEXT CHECK(length(description) <= 255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    group_id INTEGER NOT NULL DEFAULT 0
);

-- 创建脚本组表
CREATE TABLE IF NOT EXISTS script_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL CHECK(length(name) <= 255),
    description TEXT CHECK(length(description) <= 255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建执行任务表
CREATE TABLE IF NOT EXISTS executor_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    server_ids TEXT NOT NULL,
    script_id INTEGER NOT NULL,
    script_content TEXT NOT NULL,
    script_type TEXT NOT NULL CHECK(length(script_type) <= 255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 创建执行日志表
CREATE TABLE IF NOT EXISTS executor_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    executor_task_id INTEGER NOT NULL,
    server_id INTEGER NOT NULL,
    ssh_host TEXT NOT NULL,
    status INTEGER NOT NULL DEFAULT 0 CHECK(status IN (0,1,2,3)),
    log_name TEXT CHECK(length(log_name) <= 255),
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);


-- 创建索引（分开创建以避免SQLite语法错误）
-- 脚本表索引
CREATE INDEX IF NOT EXISTS idx_scripts_name ON scripts(name);
CREATE INDEX IF NOT EXISTS idx_scripts_script_type ON scripts(script_type);
CREATE INDEX IF NOT EXISTS idx_scripts_group_id ON scripts(group_id);

-- 脚本组索引
CREATE INDEX IF NOT EXISTS idx_script_groups_name ON script_groups(name);

-- 执行任务索引
CREATE INDEX IF NOT EXISTS idx_executor_tasks_script_id ON executor_tasks(script_id);

-- 执行日志索引
CREATE INDEX IF NOT EXISTS idx_executor_logs_task_server ON executor_logs(executor_task_id, server_id);
CREATE INDEX IF NOT EXISTS idx_executor_logs_status ON executor_logs(status);
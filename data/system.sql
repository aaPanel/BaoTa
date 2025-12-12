CREATE TABLE IF NOT EXISTS `network` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `up` INTEGER,
    `down` INTEGER,
    `total_up` INTEGER,
    `total_down` INTEGER,
    `down_packets` INTEGER,
    `up_packets` INTEGER,
    `addtime` INTEGER
);

CREATE TABLE IF NOT EXISTS `cpuio` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `pro` INTEGER,
    `mem` INTEGER,
    `addtime` INTEGER
);

CREATE TABLE IF NOT EXISTS `diskio` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `read_count` INTEGER,
    `write_count` INTEGER,
    `read_bytes` INTEGER,
    `write_bytes` INTEGER,
    `read_time` INTEGER,
    `write_time` INTEGER,
    `addtime` INTEGER
);

CREATE TABLE IF NOT EXISTS `process_top_list` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `cpu_top` REAL,
    `memory_top` REAL,
    `disk_top` REAL,
    `net_top` REAL,
    `all_top` REAL,
    `addtime` INTEGER
);

CREATE TABLE IF NOT EXISTS `load_average` (
    `id` INTEGER PRIMARY KEY AUTOINCREMENT,
    `pro` REAL,
    `one` REAL,
    `five` REAL,
    `fifteen` REAL,
    `addtime` INTEGER
);

CREATE TABLE IF NOT EXISTS `backup_status` (
    `id` INTEGER,
    `target` TEXT,
    `status` INTEGER,
    `msg` TEXT DEFAULT "",
    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `app_usage` (
    `time_key` INTEGER PRIMARY KEY,
    `app` TEXT,
    `disks` TEXT,
    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `server_status` (
    `status` TEXT,
    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS `daily` (
    `time_key` INTEGER,
    `evaluate` INTEGER,
    `addtime` DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS 'cpu' ON 'cpuio'('addtime');
CREATE INDEX IF NOT EXISTS 'ntwk' ON 'network'('addtime');
CREATE INDEX IF NOT EXISTS 'disk' ON 'diskio'('addtime');
CREATE INDEX IF NOT EXISTS 'load' ON 'load_average'('addtime');
CREATE INDEX IF NOT EXISTS 'proc' ON 'process_top_list'('addtime');
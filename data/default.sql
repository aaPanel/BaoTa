
CREATE TABLE IF NOT EXISTS `backup` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `type` INTEGER,
  `name` TEXT,
  `pid` INTEGER,
  `filename` TEXT,
  `size` INTEGER,
  `addtime` TEXT
);

CREATE TABLE IF NOT EXISTS `binding` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pid` INTEGER,
  `domain` TEXT,
  `path` TEXT,
  `port` INTEGER,
  `addtime` TEXT
);


CREATE TABLE IF NOT EXISTS `config` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `webserver` TEXT,
  `backup_path` TEXT,
  `sites_path` TEXT,
  `status` INTEGER,
  `mysql_root` TEXT
);

INSERT INTO `config` (`id`, `webserver`, `backup_path`, `sites_path`, `status`, `mysql_root`) VALUES
(1, 'nginx', '/www/backup', '/www/wwwroot', 0, 'admin');


CREATE TABLE IF NOT EXISTS `crontab` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` TEXT,
  `type` TEXT,
  `where1` TEXT,
  `where_hour` INTEGER,
  `where_minute` INTEGER,
  `echo` TEXT,
  `addtime` TEXT
);

CREATE TABLE IF NOT EXISTS `databases` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pid` INTEGER,
  `name` TEXT,
  `username` TEXT,
  `password` TEXT,
  `accept` TEXT,
  `ps` TEXT,
  `addtime` TEXT
);

CREATE TABLE IF NOT EXISTS `firewall` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `port` TEXT,
  `ps` TEXT,
  `addtime` TEXT
);

INSERT INTO `firewall` (`id`, `port`, `ps`, `addtime`) VALUES
(2, '80', '网站默认端口', '0000-00-00 00:00:00'),
(3, '8888', 'WEB面板', '0000-00-00 00:00:00'),
(4, '21', 'FTP服务', '0000-00-00 00:00:00'),
(5, '22', 'SSH远程管理服务', '0000-00-00 00:00:00');


CREATE TABLE IF NOT EXISTS `ftps` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pid` INTEGER,
  `name` TEXT,
  `password` TEXT,
  `path` TEXT,
  `status` TEXT,
  `ps` TEXT,
  `addtime` TEXT
);


CREATE TABLE IF NOT EXISTS `logs` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `type` TEXT,
  `log` TEXT,
  `addtime` TEXT
);

CREATE TABLE IF NOT EXISTS `sites` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` TEXT,
  `path` TEXT,
  `status` TEXT,
  `index` TEXT,
  `ps` TEXT,
  `addtime` TEXT
);

CREATE TABLE IF NOT EXISTS `domain` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `pid` INTEGER,
  `name` TEXT,
  `port` INTEGER,
  `addtime` TEXT
);

CREATE TABLE IF NOT EXISTS `users` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `username` TEXT,
  `password` TEXT,
  `login_ip` TEXT,
  `login_time` TEXT,
  `phone` TEXT,
  `email` TEXT
);

INSERT INTO `users` (`id`, `username`, `password`, `login_ip`, `login_time`, `phone`, `email`) VALUES
(1, 'admin', '21232f297a57a5a743894a0e4a801fc3', '192.168.0.10', '2016-12-10 15:12:56', 0, '287962566@qq.com');


CREATE TABLE IF NOT EXISTS `tasks` (
  `id` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` 			TEXT,
  `type`			TEXT,
  `status` 		TEXT,
  `addtime` 	TEXT,
  `start` 	  INTEGER,
  `end` 	    INTEGER,
  `execstr` 	TEXT
);

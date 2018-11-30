CREATE TABLE IF NOT EXISTS `plugin_list` (
  `pid` INTEGER PRIMARY KEY AUTOINCREMENT,
  `title`			TEXT,
  `tip`				TEXT,
  `name` 			TEXT,
  `type`			TEXT,
  `status` 			INTEGER,
  `versions` 		TEXT,
  `ps` 	  			TEXT,
  `checks` 	  		TEXT,
  `author` 			TEXT,
  `home`			TEXT,
  `shell`			TEXT,
  `ssort`			INTEGER,
  `addtime`		TEXT
);

CREATE TABLE IF NOT EXISTS `hook_list` (
  `hid` INTEGER PRIMARY KEY AUTOINCREMENT,
  `name` 			TEXT,
  `type`			TEXT,
  `model` 			TEXT,
  `action` 			TEXT,
  `ps` 	  			TEXT,
  `addtime`			TEXT
);
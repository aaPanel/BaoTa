<?php

function get_info(){
	$data = array();
	$data['php_version'] = PHP_VERSION;
	$data['modules'] = get_loaded_extensions();  // 所有已加载的模块

	//加密解密库
	$data['2crypt'] = array();
	$data['2crypt']['Zend Optimizer'] = get_extension_funcs('Zend Optimizer')?OPTIMIZER_VERSION:false;
	$data['2crypt']['Zend Guard Loader'] = get_extension_funcs('Zend Guard Loader')?true:false;
	$data['2crypt']['ionCube Loader'] = get_extension_funcs('ionCube Loader')?true:false;
	$data['2crypt']['SourceGuardian'] = get_extension_funcs('SourceGuardian')?true:false;
	$data['2crypt']['Mcrypt'] = get_extension_funcs('mcrypt')?true:false;
	$data['2crypt']['OpenSSL'] = get_extension_funcs('openssl')?true:false;
	$data['2crypt']['Iconv'] = get_extension_funcs('iconv')?true:false;

	//缓存库
	$data['1cache'] = array();
	$data['1cache']['Zend OPcache'] = get_extension_funcs('Zend OPcache')?true:false;
	$data['1cache']['Redis'] = in_array('redis',$data['modules']);
	$data['1cache']['Memcache'] = get_extension_funcs('memcache')?true:false;
	$data['1cache']['Memcached'] = in_array('memcached',$data['modules']);
	$data['1cache']['apcu'] = get_extension_funcs('apcu')?true:false;
	$data['1cache']['xcache'] = get_extension_funcs('xcache')?true:false;

	//数据库驱动
	$data['0db'] = array();
	$data['0db']['MySQL'] = in_array('mysql',$data['modules']);
	$data['0db']['MySQLi'] = in_array('mysqli',$data['modules']);
	$data['0db']['PDO-MySQL'] = in_array('pdo_mysql',$data['modules']);
	$data['0db']['SqlServer'] =in_array('mssql',$data['modules']);
	$data['0db']['PDO-SqlServer'] = in_array('pdo_mssql',$data['modules']);
	if(!$data['0db']['PDO-SqlServer']) $data['0db']['PDO-SqlServer'] = in_array('pdo_sqlsrv',$data['modules']);
	$data['0db']['Sqlite3'] = in_array('sqlite3',$data['modules']);
	$data['0db']['PDO-Sqlite'] = in_array('pdo_sqlite',$data['modules']);
	$data['0db']['PgSQL'] = get_extension_funcs('pg_query')?true:false;
	$data['0db']['PDO-PgSQL'] = in_array('pdo_pgsql',$data['modules']);
	$data['0db']['MongoDB'] = in_array('mongo',$data['modules']);

	//文件与字符串处理库
	$data['5io_string'] = array();
	$data['5io_string']['Xmlrpc'] = get_extension_funcs('xmlrpc')?true:false;
	$data['5io_string']['FileInfo'] = in_array('fileinfo',$data['modules'])?true:false;
	$data['5io_string']['Ftp'] = get_extension_funcs('ftp')?true:false;
	$data['5io_string']['Mbstring'] = get_extension_funcs('mbstring')?true:false;
	$data['5io_string']['bz2'] = in_array('bz2',$data['modules']);
	$data['5io_string']['xsl'] = in_array('xsl',$data['modules']);

	//网络相关库
	$data['4network'] = array();
	$data['4network']['cURL'] = get_extension_funcs('curl')?true:false;
	$data['4network']['Swoole'] = get_extension_funcs('swoole')?true:false;
	$data['4network']['Sockets'] = get_extension_funcs('sockets')?true:false;

	//图片处理库
	$data['3photo'] = array();
	$data['3photo']['EXIF'] = get_extension_funcs('exif')?true:false;
	$data['3photo']['GD library'] = get_extension_funcs('gd')?true:false;
	$data['3photo']['ImageMagick'] = in_array('imagick',$data['modules']);

	//其它第三方库
	$data['6other'] = array();
	$data['6other']['xDebug'] = get_extension_funcs('xdebug')?true:false;
	$data['6other']['phalcon'] = in_array('phalcon',$data['modules']);
	$data['6other']['yaf'] = in_array('yaf',$data['modules']);


	$data['ini'] = array();
	$data['ini']['memory_limit'] = ini_get('memory_limit');
	$data['ini']['upload_max_filesize'] = ini_get('upload_max_filesize');
	$data['ini']['post_max_size'] = ini_get('post_max_size');
	$data['ini']['max_execution_time'] = ini_get('max_execution_time');
	$data['ini']['max_input_time'] = ini_get('max_input_time');
	$data['ini']['default_socket_timeout'] = ini_get('default_socket_timeout');
	return $data;
}
$result = get_info();
exit(json_encode($result));



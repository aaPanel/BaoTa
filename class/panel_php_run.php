<?php
// +-------------------------------------------------------------------
// | 宝塔Linux面板
// +-------------------------------------------------------------------
// | Copyright (c) 2015-2099 宝塔软件(http://bt.cn) All rights reserved.
// +-------------------------------------------------------------------
// | Author: hwliang <hwl@bt.cn>
// +-------------------------------------------------------------------

// +-------------------------------------------------------------------
// | PHP插件前置处理模块
// +-------------------------------------------------------------------
class bt_panel_plugin
{
	//启动PHP插件
	public function run(){
		$this->init();
		return $this->plugin_main();
	}

	//初始化插件环境
	private function init(){
		//获取命令行参数
		$args_arr = getopt('',array('plugin_name:','args_tmp:','fun:'));
		if(!$args_arr['plugin_name']){
			return_status(false,'指定插件不存在!');
		}
		if(!$args_arr['args_tmp']){
			return_status(false,'请传入正确的参数位置!');
		}
		//初始化插件配置
		define('PLU_PATH', '/www/server/panel/plugin/'.trim($args_arr['plugin_name']));
		define('PLU_NAME',trim($args_arr['plugin_name']));
		define('PLU_ARGS_TMP', trim($args_arr['args_tmp']));
		define('PLU_FUN',trim($args_arr['fun']));

		//检查
		if(!file_exists(PLU_PATH.'/index.php')) return_status(false,'指定插件不存在!');
		if(!preg_match("/^[\w-]+$/",PLU_FUN)) return_status(false,'指定方法不存在!');
		chdir(PLU_PATH);
	}

	//调用插件主程序
	private function plugin_main(){
		include_once PLU_PATH . '/index.php';
		if(!class_exists('bt_main'))  return_status(false,'没有找到bt_main类');

		$plu = new bt_main();
		if(!method_exists($plu, PLU_FUN))  return_status(false,'指定方法不存在');
		return call_user_func(array($plu,PLU_FUN));
	}
}



class db extends SQLite3
{
	function __construct($db_file = '/www/server/panel/data/default.db')
    {
        $this->open($db_file);
    }

	public function queryute($sql){
		$result = $this->query($sql);
		$data = $result->fetchArray(SQLITE3_ASSOC);
		return $data;
	}

	public function execute($sql){
		$result = $this->exec($sql);
		return $result;
	}
}



//取指安参数
function _args($_t,$key){
	if(!file_exists(PLU_ARGS_TMP))  {
		if($key) return null;
		return array();
	}
	$args_tmp = json_decode(file_get_contents(PLU_ARGS_TMP),1);
	if($key){
		if(!array_key_exists($key, $args_tmp[$_t])) return false;
		return $args_tmp[$_t][$key];
	}
	return $args_tmp[$_t];
}

function _version(){
	$comm_body = file_get_contents('/www/server/panel/class/common.py');
	preg_match("/g\.version\s*=\s*'(\d+\.\d+\.\d+)'/",$comm_body,$m_version);
	return $m_version[1];
}

//取GET参数
function _get($key = null){
	return _args('GET',$key);
}

//取POST参数
function _post($key=null){
	return _args('POST',$key);
}

//通用返回状态
function return_status($status,$msg){
	exit(json_encode(array('status'=>$status,'msg'=>$msg)));
}

//返回数据
function _return($data){
	exit(json_encode($data));
}

/**
 * 发起GET请求
 * @param String $url 目标网填，带http://
 * @return bool
 */
function _httpGet($url) {
	$ch = curl_init();
	curl_setopt($ch, CURLOPT_URL, $url);
	curl_setopt($ch, CURLOPT_TIMEOUT, 6);
	curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
	curl_setopt($ch, CURLOPT_HTTPHEADER,array('Accept-Encoding: gzip, deflate'));
	curl_setopt($ch, CURLOPT_ENCODING, 'gzip,deflate');
	curl_setopt($ch, CURLOPT_USERAGENT, "BT-Panel for PHP-Plugin");
	curl_setopt($ch, CURLOPT_HEADER, 0);
	curl_setopt($ch, CURLOPT_FOLLOWLOCATION, 3);
	$output = curl_exec($ch);
	curl_close($ch);
	return $output;
}

//发起POST请求
function _httpPost($url,$data){
	$ch = curl_init();
	curl_setopt($ch, CURLOPT_URL, $url);
	curl_setopt($ch, CURLOPT_TIMEOUT, 30);
	curl_setopt($ch, CURLOPT_POST, 1);
	curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
	curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
	curl_setopt($ch, CURLOPT_USERAGENT, "BT-Panel for PHP-Plugin");
	curl_setopt($ch, CURLOPT_HEADER, 0);
	curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
	curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, FALSE);
	$output = curl_exec($ch);
	curl_close($ch);
	return $output;
}

//启动插件
$p = new bt_panel_plugin();
_return($p->run());
?>
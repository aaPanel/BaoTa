
; (function () { 
	// Description: 预加载文件
	var loadResource = [
		"/static/css/style.css?v=1764728423",
		"/static/js/main.js?v=1764728423",
		"/static/js/base-lib.js?v=1764728423",
		"/static/js/__commonjsHelpers__.js?v=1764728423",
		"/static/js/modulepreload-polyfill.js?v=1764728423",
		"/static/js/utils-lib.js?v=1764728423",
		"/static/js/software.js?v=1764728423",
		"/static/js/jquery-2.2.4.min.js?v=1764728423",
		"/static/js/utils.min.js?v=1764728423",
		"/static/layer/layer.js?v=1764728423",
	]

	/**
	 * @description 封装 AJAX 请求
	 * @param {string} url 请求的 URL
	 * @param {string} method 请求方法（GET, POST, PUT, DELETE 等）
	 * @param {Object} [data] 请求数据（可选）
	 * @returns {Promise<any>} 返回一个 Promise，解析为响应数据
	 */
	var ajax = (url, method, data = null) => {
		return new Promise((resolve, reject) => {
			var xhr = new XMLHttpRequest()
			xhr.open(method, url, true)
			xhr.setRequestHeader('Content-Type', 'application/json;charset=UTF-8')

			xhr.onreadystatechange = () => {
				if (xhr.readyState === 4) {
					if (xhr.status >= 200 && xhr.status < 300) {
						resolve(JSON.parse(xhr.responseText))
					} else {
						reject(new Error(`Request failed with status ${xhr.status}`))
					}
				}
			}

			xhr.onerror = () => {
				reject(new Error('Network error'))
			}

			xhr.send(data ? JSON.stringify(data) : null)
		})
	}

	/**
	 * @description 检查是否已加载过某个
	 * @param {string} str 路径
	 * @returns {boolean}
	 */
	var checkLoadContent = str => {
		var isLoad = false
		for (var i = 0; i < loadResource.length; i++) {
			if (loadResource[i] === str) {
				isLoad = true
				break
			}
		}
		if (!isLoad) {
			loadResource.push(str)
			sessionStorage.setItem('load', JSON.stringify(loadResource))
		}
		return isLoad
	}
	/**
	 * @description 预加载路径
	 * @param {string[]} urls 路径列表
	 */
	var preload = urls => {
		urls.forEach(url => {
			if (!checkLoadContent(url)) {
				ajax(url, 'GET').then(() => {
					checkLoadContent(url)
				})
			}
		})
	}
	// 获取已加载的资源
	preload(loadResource)
})()

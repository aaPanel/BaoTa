function MyAjax() {
	this.serverdata = this.erromsg = this.timeout = this.stop = this.xmlhttp = !1, this.transit = !0
}
MyAjax.prototype.handle = function(d, f) {
	if(4 == d.readyState) {
		if(this.stop === !0) {
			return
		}
		if(this.transit = !0, f.timeout && f.async && (clearTimeout(this.timeout), this.timeout = !1), 200 == d.status) {
			var e = this.serverdata = d.responseText.replace(/(^\s*)|(\s*$)/g, "");
			"function" == typeof f.success && f.success(e)
		} else {
			this.erromsg = d.status, "function" == typeof f.error && f.error(d.status)
		}
	} else {
		if(0 == d.readyState) {
			if(this.stop === !0) {
				return
			}
			f.timeout && f.async && (clearTimeout(this.timeout), this.timeout = !1), this.erromsg = d.readyState, this.transit = !0, "function" == typeof f.error && f.error(d.readyState)
		}
	}
}, MyAjax.prototype.out = function(b) {
	this.transit = !0, this.erromsg = 504, this.stop = !0, "function" == typeof b.error && b.error(504)
}, MyAjax.prototype.carry = function(j) {
	var i, h, g, l;
	if(j.lock && !this.transit) {
		return !1
	}
	this.transit = !1, this.stop = this.erromsg = !1, i = window.XMLHttpRequest ? new XMLHttpRequest : new ActiveXObject("Microsoft.XMLHTTP"), j.type = j.type.toUpperCase(), h = function() {}, "string" == typeof j.data ? (j.data = j.data.replace(/(^\s*)|(\s*$)/g, ""), h = function() {
		i.setRequestHeader("Content-Type", "application/x-www-form-urlencoded")
	}) : "[object FormData]" !== Object.prototype.toString.call(j.data) ? (j.data = "", h = function() {
		i.setRequestHeader("Content-Type", "application/x-www-form-urlencoded")
	}) : ("function" == typeof j.progress && i.upload.addEventListener("progress", j.progress, !1), j.type = "POST"), g = "" == j.data ? [null, ""] : [j.data, "?" + j.data], l = this, "function" == typeof j.complete && j.complete(), j.timeout && j.async && (this.timeout = setTimeout(function() {
		l.out(j)
	}, j.timeout)), j.async === !0 && (i.onreadystatechange = function() {
		l.handle(i, j)
	});
	try {
		switch(j.type) {
			case "POST":
				i.open("POST", j.url, j.async), h();
				break;
			default:
				i.open("GET", j.url + g[1], j.async), j.cache === !0 || i.setRequestHeader("If-Modified-Since", "0")
		}
	} catch(k) {
		return this.erromsg = 505, j.timeout && j.async && (clearTimeout(this.timeout), this.timeout = !1), this.transit = !0, "function" == typeof j.error && j.error(505), void 0
	}
	i.send(g[0]), j.async === !1 && l.handle(i, j)
};

function UploadStart(d) {
	var a = function(e) {
		this.uptype = e.UpType;
		this.url = e.url;
		this.oldurl = e.url;
		this.filessize = e.FilesSize, this.MaxUpNum = e.MaxUpNum, this.str = new MyAjax();
		this.file_input = document.getElementById("file_input");
		this.opt = document.getElementById("opt");
		this.up = document.getElementById("up");
		this.up_box = document.getElementById("up_box");
		this.filesalllength = this.FilesArrayLength = this.up_box_li = FileProgress = 0;
		this.FilesArray = new Array();
		this.num = 0
	};
	a.prototype = {
		SelectFile: function() {
			if(this.FilesArrayLength === 0) {
				this.up_box.innerHTML = "";
				this.un()
			}
			var h = this.file_input.files,
				e, g, f = h.length;
			if(this.filesalllength + f > this.MaxUpNum) {
				f = this.MaxUpNum - this.filesalllength;
				layer.msg(lan.get('update_num',[this.MaxUpNum]), {
					icon: 5
				})
            }

            
			for(var j = 0; j < f; j++) {
				e = h[j];
				g = e.name.split(".");
				g = Object.prototype.toString.call(g) === "[object Array]" ? g[g.length - 1] : "";
				if(d) {
					if(g != "sql" && g != "zip" && g != "gz" && g != "tgz") {
						layer.msg(lan.upload.file_type_err, {
							icon: 5
						});
						return
					}
				}
				if(!e){
					this.up_box.insertAdjacentHTML("beforeEnd", "<li>" + e.name + "<em style='color: red;'>"+lan.upload.file_err+"</em></li>")
                } else {
                    if (this.uptype.length > 0 && this.uptype.indexOf(g.toLowerCase()) === -1) {
						this.up_box.insertAdjacentHTML("beforeEnd", "<li>" + e.name + "<em style='color: red;'>"+lan.upload.file_type_err+"</em></li>")
                    } else {
                        
						if(e.size <= 0) {
							this.up_box.insertAdjacentHTML("beforeEnd", "<li>" + e.name + "<em style='color: red;'>"+lan.upload.file_err_empty+"</em></li>")
						} else {
							this.up_box.insertAdjacentHTML("beforeEnd", "<li><span class='filename'>" + e.name + "</span><span class='filesize'>" + (ToSize(e.size)) + "</span><em>"+lan.upload.up_sleep+"</em></li>");
                            this.FilesArray.push([e, (this.filesalllength - 1 < 0 ? 0 : this.filesalllength) + j])
                            $('#file_input').replaceWith('<input type="file" id="file_input" multiple="true" autocomplete="off">')
						}
					}
				}
			}
			this.filesalllength += f;
			this.FilesArrayLength = this.FilesArray.length
		},
		read: function() {
			if(this.filesalllength == 0) {
				layer.msg(lan.upload.select_file, {
					icon: 5
				});
				return
			}
			this.url = this.oldurl + "&codeing=" + document.getElementById("fileCodeing").value;
			if(this.FilesArrayLength > 0) {
				this.opt.disabled = true;
				this.up.disabled = true;
				this.file_input.disabled = true;
				this.up_box_li = this.up_box.getElementsByTagName("li");
				this.ready(this.FilesArray, 0, this.FilesArrayLength - 1)
			} else {
				layer.msg(an.upload.select_empty, {
					icon: 5
				})
			}
		},
		un: function() {
			this.opt.disabled = this.up.disabled = this.file_input.disabled;
			this.filesalllength = this.FilesArrayLength = this.up_box_li = 0;
			this.FilesArray = new Array()
		},
		ready: function(i, f, h) {
			if(f > h) {
				this.un();
				return
			}
			try {
				var g = new FormData();
				g.append("zunfile", i[f][0])
			} catch(e) {
				this.opt.disabled = true;
				this.up.disabled = true;
				this.file_input.disabled = true;
				layer.msg(lan.upload.ie_err, {
					icon: 5
				})
			}
			if(i.length > 1) {
				$("#totalProgress").html("<p>"+lan.upload.up_the+ this.num + "/" + i.length + "</p><progress value='" + this.num + "' max='" + i.length + "' ></progress>");
				$(".cancel").css("visibility", "hidden")
			}
			this.send(g, i, f, h)
		},
		SetTxt: function(f, g, h) {
			var e = this.up_box_li[f].getElementsByTagName("em")[0];
			e.style.color = h;
			e.innerHTML = g
		},
		send: function(f, i, e, g) {
			if(!this.up_box_li[e].getElementsByTagName("em")[0]) {
				this.ready(i, e + 1, g);
				this.num++;
				return
			}
			var h = this;
			this.FileProgress = 0;
			this.str.carry({
				url: this.url,
				data: f,
				type: "get",
				timeout: 86400000,
				async: true,
				lock: true,
				complete: false,
				progress: function(j) {
					h.FileProgress = Math.floor(j.loaded / j.total * 100) + "%";
					if(h.FileProgress == "100%") {
						h.FileProgress = lan.upload.up_save
					}
					h.SetTxt(i[e][1], lan.upload.up_speed + h.FileProgress, "#005100")
				},
				success: function(j) {
					h.str.serverdata = false;
					h.SetTxt(i[e][1], lan.upload.up_ok, "#005100");
					h.ready(i, e + 1, g);
					h.num++;
					if(i.length > 1) {
						var k = (h.num == i.length) ? lan.upload.up_ok_1 : lan.upload.up_ok_2;
						$("#totalProgress").html("<p>" + k + h.num + "/" + i.length + "</p><progress value='" + h.num + "' max='" + i.length + "' ></progress>")
					}
					if(h.num == i.length) {
						c.opt.disabled = false;
						c.up.disabled = false;
						c.file_input.disabled = false;
						h.num = 0
					}
					if(!d) {
						GetFiles(getCookie("Path"))
					}
				},
				error: function(j) {
					h.SetTxt(i[e][1], lan.upload.up_err, "red");
					h.str.serverdata = false;
					h.ready(i, e + 1, g)
				},
				cache: false
			})
		}
	};
	try {
		var c = new a({
			UpType: new Array(),
			FilesSize: 5242880000,
			MaxUpNum: 100,
			url: "/files?action=UploadFile&path=" + document.getElementById("input-val").value
		});
		c.opt.addEventListener("click", function() {
			c.file_input.click()
		}, false);
		c.up.addEventListener("click", function() {
			c.read()
		}, false);
		c.file_input.addEventListener("change", function() {
			c.SelectFile()
		}, false)
	} catch(b) {
		c.opt.disabled = true;
		c.up.disabled = true;
		c.file_input.disabled = true;
		layer.msg(lan.upload.ie_err, {
			icon: 5
		})
	}
};
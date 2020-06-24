/**********************************
 Directory Upload Proposal Polyfill
 Author: Ali Alabbas (Microsoft)
 **********************************/
(function() {
	// Do not proceed with the polyfill if Directory interface is already natively available,
	// or if webkitdirectory is not supported (i.e. not Chrome, since the polyfill only works in Chrome)
	if (window.Directory || !('webkitdirectory' in document.createElement('input') && 'webkitGetAsEntry' in DataTransferItem.prototype)) {
		return;
	}

	var allowdirsAttr = 'allowdirs',
		getFilesMethod = 'getFilesAndDirectories',
		isSupportedProp = 'isFilesAndDirectoriesSupported',
		chooseDirMethod = 'chooseDirectory';

	var separator = '/';

	var Directory = function() {
		this.name = '';
		this.path = separator;
		this._children = {};
		this._items = false;
	};

	Directory.prototype[getFilesMethod] = function() {
		var that = this;

		// from drag and drop and file input drag and drop (webkitEntries)
		if (this._items) {
			var getItem = function(entry) {
				if (entry.isDirectory) {
					var dir = new Directory();
					dir.name = entry.name;
					dir.path = entry.fullPath;
					dir._items = entry;

					return dir;
				} else {
					return new Promise(function(resolve, reject) {
						entry.file(function(file) {
							resolve(file);
						}, reject);
					});
				}
			};

			if (this.path === separator) {
				var promises = [];
				
				for (var i = 0; i < this._items.length; i++) {
					var entry;

					// from file input drag and drop (webkitEntries)
					if (this._items[i].isDirectory || this._items[i].isFile) {
						entry = this._items[i];
					} else {
						entry = this._items[i].webkitGetAsEntry();
					}
					
					promises.push(getItem(entry));
				}

				return Promise.all(promises);
			} else {
				return new Promise(function(resolve, reject) {
					var dirReader = that._items.createReader();
					var promises = [];

					var readEntries = function() {
						dirReader.readEntries(function(entries) {
							if (!entries.length) {
								resolve(Promise.all(promises));
							} else {
								for (var i = 0; i < entries.length; i++) {
									promises.push(getItem(entries[i]));
								}

								readEntries();
							}
						}, reject);
					};

					readEntries();
				});
			}
		// from file input manual selection
		} else {
			var arr = [];

			for (var child in this._children) {
				arr.push(this._children[child]);
			}

			return Promise.resolve(arr);
		}
	};

	// set blank as default for all inputs
	HTMLInputElement.prototype[getFilesMethod] = function() {
		return Promise.resolve([]);
	};

	// if OS is Mac, the combined directory and file picker is supported
	HTMLInputElement.prototype[isSupportedProp] = navigator.appVersion.indexOf("Mac") !== -1;

	HTMLInputElement.prototype[allowdirsAttr] = undefined;
	HTMLInputElement.prototype[chooseDirMethod] = undefined;

	// expose Directory interface to window
	window.Directory = Directory;

	/********************
	 **** File Input ****
	 ********************/
	var convertInputs = function(nodes) {
		var recurse = function(dir, path, fullPath, file) {
			var pathPieces = path.split(separator);
			var dirName = pathPieces.shift();

			if (pathPieces.length > 0) {
				var subDir = new Directory();
				subDir.name = dirName;
				subDir.path = separator + fullPath;

				if (!dir._children[subDir.name]) {
					dir._children[subDir.name] = subDir;
				}

				recurse(dir._children[subDir.name], pathPieces.join(separator), fullPath, file);
			} else {
				dir._children[file.name] = file;
			}
		};

		for (var i = 0; i < nodes.length; i++) {
			var node = nodes[i];

			if (node.tagName === 'INPUT' && node.type === 'file') {
				var getFiles = function() {
					var files = node.files;

					if (draggedAndDropped) {
						files = node.webkitEntries;
						draggedAndDropped = false;
					} else {
						if (files.length === 0) {
							files = node.shadowRoot.querySelector('#input1').files;

							if (files.length === 0) {
								files = node.shadowRoot.querySelector('#input2').files;

								if (files.length === 0) {
									files = node.webkitEntries;
								}
							}
						}
					}

					return files;
				};

				var draggedAndDropped = false;

				node.addEventListener('drop', function(e) {
					draggedAndDropped = true;
				}, false);

				if (node.hasAttribute(allowdirsAttr)) {
					// force multiple selection for default behavior
					if (!node.hasAttribute('multiple')) {
						node.setAttribute('multiple', '');
					}

					var shadow = node.createShadowRoot();

					node[chooseDirMethod] = function() {
						// can't do this without an actual click
						console.log('This is unsupported. For security reasons the dialog cannot be triggered unless it is a response to some user triggered event such as a click on some other element.');
					};

					shadow.innerHTML = '<div style="border: 1px solid #999; padding: 3px; width: 235px; box-sizing: content-box; font-size: 14px; height: 21px;">'
						+ '<div id="fileButtons" style="box-sizing: content-box;">'
						+ '<button id="button1" style="width: 100px; box-sizing: content-box;">Choose file(s)...</button>'
						+ '<button id="button2" style="width: 100px; box-sizing: content-box; margin-left: 3px;">Choose folder...</button>'
						+ '</div>'
						+ '<div id="filesChosen" style="padding: 3px; display: none; box-sizing: content-box;"><span id="filesChosenText">files selected...</span>'
						+ '<a id="clear" title="Clear selection" href="javascript:;" style="text-decoration: none; float: right; margin: -3px -1px 0 0; padding: 3px; font-weight: bold; font-size: 16px; color:#999; box-sizing: content-box;">&times;</a>'
						+ '</div>'
						+ '</div>'
						+ '<input id="input1" type="file" multiple style="display: none;">'
						+ '<input id="input2" type="file" webkitdirectory style="display: none;">'
						+ '</div>';

					shadow.querySelector('#button1').onclick = function(e) {
						e.preventDefault();
						
						shadow.querySelector('#input1').click();
					};

					shadow.querySelector('#button2').onclick = function(e) {
						e.preventDefault();
						
						shadow.querySelector('#input2').click();
					};

					var toggleView = function(defaultView, filesLength) {
						shadow.querySelector('#fileButtons').style.display = defaultView ? 'block' : 'none';
						shadow.querySelector('#filesChosen').style.display = defaultView ? 'none' : 'block';
						
						if (!defaultView) {
							shadow.querySelector('#filesChosenText').innerText = filesLength + ' file' + (filesLength > 1 ? 's' : '') + ' selected...';
						}
					};

					var changeHandler = function(e) {
						node.dispatchEvent(new Event('change'));

						toggleView(false, getFiles().length);
					};

					shadow.querySelector('#input1').onchange = shadow.querySelector('#input2').onchange = changeHandler;

					var clear = function (e) {
						toggleView(true);

						var form = document.createElement('form');
						node.parentNode.insertBefore(form, node);
						node.parentNode.removeChild(node);
						form.appendChild(node);
						form.reset();

						form.parentNode.insertBefore(node, form);
						form.parentNode.removeChild(form);

						// reset does not instantly occur, need to give it some time
						setTimeout(function() {
							node.dispatchEvent(new Event('change'));
						}, 1);
					};

					shadow.querySelector('#clear').onclick = clear;
				}

				node.addEventListener('change', function() {
					var dir = new Directory();

					var files = getFiles();

					if (files.length > 0) {
						if (node.hasAttribute(allowdirsAttr)) {
							toggleView(false, files.length);
						}

						// from file input drag and drop (webkitEntries)
						if (files[0].isFile || files[0].isDirectory) {
							dir._items = files;
						} else {
							for (var j = 0; j < files.length; j++) {
								var file = files[j];
								var path = file.webkitRelativePath;
								var fullPath = path.substring(0, path.lastIndexOf(separator));

								recurse(dir, path, fullPath, file);
							}
						}
					} else if (node.hasAttribute(allowdirsAttr)) {
						toggleView(true, files.length);
					}

					this[getFilesMethod] = function() {
						return dir[getFilesMethod]();
					};
				});
			}
		}
	};

	// polyfill file inputs when the DOM loads
	document.addEventListener('DOMContentLoaded', function(event) {
		convertInputs(document.getElementsByTagName('input'));
	});

	// polyfill file inputs that are created dynamically and inserted into the body
	var observer = new MutationObserver(function(mutations, observer) {
		for (var i = 0; i < mutations.length; i++) {
			if (mutations[i].addedNodes.length > 0) {
				convertInputs(mutations[i].addedNodes);
			}
		}
	});

	observer.observe(document.body, {childList: true, subtree: true});

	/***********************
	 **** Drag and drop ****
	 ***********************/
	// keep a reference to the original method
	var _addEventListener = EventTarget.prototype.addEventListener;

	DataTransfer.prototype[getFilesMethod] = function() {
		return Promise.resolve([]);
	};

	EventTarget.prototype.addEventListener = function(type, listener, useCapture) {
		if (type === 'drop') {
			var _listener = listener;

			listener = function(e) {
				var dir = new Directory();
				dir._items = e.dataTransfer.items;

				e.dataTransfer[getFilesMethod] = function() {
					return dir[getFilesMethod]();
				};

				_listener(e);
			};
		}

		// call the original method
		return _addEventListener.apply(this, arguments);
	};
}());

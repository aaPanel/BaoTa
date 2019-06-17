/*******************
********************

HTML5 / Javascript: 
get hash of files using drag and drop

Developed by Marco Antonio Alvarez => https://github.com/marcu87/hashme

*******************/

var hashMe = function (file, callbackFunction) {

    var thisObj = this,
        _binStart = "",
        _binEnd = "",
        callback = "",
        fileManager1 = new FileReader,
        fileManager2 = new FileReader;

    this.setBinAndHash = function (startOrEnd, binData) {

        switch (startOrEnd) {
            case 0:
                this._binStart = binData;
                break;
            case 1:
                this._binEnd = binData
        }

        this._binStart && this._binEnd && this.md5sum(this._binStart, this._binEnd)
    };

    this.md5sum = function (start, end) {
        this._hash = rstr2hex(rstr_md5(start + end));
        callback(this._hash);
    };

    this.getHash = function () {
        return this._hash;
    };

    this.calculateHashOfFile = function (file) {

        fileManager1.onload = function (f) {
            thisObj.setBinAndHash(0, f.target.result);
        };

        fileManager2.onload = function (f) {
            thisObj.setBinAndHash(1, f.target.result);
        };

        var start = file.slice(0, 65536);
        var end = file.slice(file.size - 65536, file.size);

        fileManager1.readAsBinaryString(start);
        fileManager2.readAsBinaryString(end);
    };

    this.calculateHashOfFile(file);
    callback = callbackFunction;

};
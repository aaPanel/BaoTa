(function (addon) {
    if (typeof window !== 'undefined' && 'Terminal' in window) {
        addon(window.Terminal);
    }
    else if (typeof exports === 'object' && typeof module === 'object') {
        module.exports = addon(require('../../Terminal').Terminal);
    }
    else if (typeof define === 'function') {
        define(['../../xterm'], addon);
    }
})(function (Terminal) {
    Terminal.prototype.winptyCompatInit = function () {
        var _this = this;
        var isWindows = ['Windows', 'Win16', 'Win32', 'WinCE'].indexOf(navigator.platform) >= 0;
        if (!isWindows) {
            return;
        }
        this.on('lineFeed', function () {
            var line = _this.buffer.lines.get(_this.buffer.ybase + _this.buffer.y - 1);
            var lastChar = line[_this.cols - 1];
            if (lastChar[3] !== 32) {
                var nextLine = _this.buffer.lines.get(_this.buffer.ybase + _this.buffer.y);
                nextLine.isWrapped = true;
            }
        });
    };
});

//# sourceMappingURL=winptyCompat.js.map

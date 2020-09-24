# -*- coding: utf-8 -*-
from time import time
import os,struct
try:
    import cPickle as pickle
except ImportError:  # pragma: no cover
    import pickle

from cachelib.base import BaseCache


class SimpleCache(BaseCache):

    """Simple memory cache for single process environments.  This class exists
    mainly for the development server and is not 100% thread safe.  It tries
    to use as many atomic operations as possible and no locks for simplicity
    but it could happen under heavy load that keys are added multiple times.

    :param threshold: the maximum number of items the cache stores before
                      it starts deleting some.
    :param default_timeout: the default timeout that is used if no timeout is
                            specified on :meth:`~BaseCache.set`. A timeout of
                            0 indicates that the cache never expires.
    """
    __session_key = 'BT_:'
    __session_basedir = '/www/server/panel/data/session'

    def __init__(self, threshold=500, default_timeout=300):
        BaseCache.__init__(self, default_timeout)
        self._cache = {}
        self.clear = self._cache.clear
        self._threshold = threshold

    def _prune(self):
        if len(self._cache) > self._threshold:
            now = time()
            toremove = []
            for idx, (key, (expires, _)) in enumerate(self._cache.items()):
                if (expires != 0 and expires <= now) or idx % 3 == 0:
                    toremove.append(key)
            for key in toremove:
                self._cache.pop(key, None)


    def _normalize_timeout(self, timeout):
        timeout = BaseCache._normalize_timeout(self, timeout)
        if timeout > 0:
            timeout = time() + timeout
        return timeout

    def get(self, key):
        try:
            
            expires, value = self._cache[key]   
            if expires == 0 or expires > time():
                return pickle.loads(value)                        

        except (KeyError, pickle.PickleError):
            try:
                if key[:4] == self.__session_key:
                    filename =  '/'.join((self.__session_basedir,self.md5(key)))                    
                    if not os.path.exists(filename): return None

                    with open(filename, 'rb') as fp:
                        _val = fp.read()
                        fp.close()
      
                        expires = struct.unpack('f',_val[:4])[0] 
                        if expires == 0 or expires > time():
                            value = _val[4:]

                            self._cache[key] = (expires,value)  
                            return pickle.loads(value)
            except :pass
            return None

    def set(self, key, value, timeout=None):
        
        expires = self._normalize_timeout(timeout)
        self._prune()
        
        _val =  pickle.dumps(value, pickle.HIGHEST_PROTOCOL)
        self._cache[key] = (expires,_val)        
        try:
            if key[:4] == self.__session_key:
                if len(_val) < 1280: return True
                from BTPanel import session
                if 'request_token_head' in session:
                    if not os.path.exists(self.__session_basedir): os.makedirs(self.__session_basedir,384)
                    expires = struct.pack('f',expires)
                    filename =  '/'.join((self.__session_basedir,self.md5(key)))                    
                    fp = open(filename, 'wb+')
                    fp.write(expires + _val)
                    fp.close()
                    os.chmod(filename,384)
        except :pass
        return True

    def add(self, key, value, timeout=None):
        expires = self._normalize_timeout(timeout)
        self._prune()
        item = (expires, pickle.dumps(value,
                                      pickle.HIGHEST_PROTOCOL))
        if key in self._cache:
            return False
        self._cache.setdefault(key, item)
        return True

    def delete(self, key):
        result = self._cache.pop(key, None) is not None
        try:
            if key[:4] == self.__session_key:
                filename =  '/'.join((self.__session_basedir,self.md5(key))) 
                if os.path.exists(filename): os.remove(filename)
        except : pass
        return result

    def has(self, key):
        try:
            expires, value = self._cache[key]
            return expires == 0 or expires > time()
        except KeyError:
            return False

    def md5(self,strings):
        """
        生成MD5
        @strings 要被处理的字符串
        return string(32)
        """
        import hashlib
        m = hashlib.md5()
 
        m.update(strings.encode('utf-8'))
        return m.hexdigest()


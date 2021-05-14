import unittest
import sys
import gc

import time
import weakref
import greenlet
import threading


class ArgRefcountTests(unittest.TestCase):
    def test_arg_refs(self):
        args = ('a', 'b', 'c')
        refcount_before = sys.getrefcount(args)
        g = greenlet.greenlet(
            lambda *args: greenlet.getcurrent().parent.switch(*args))
        for i in range(100):
            g.switch(*args)
        self.assertEqual(sys.getrefcount(args), refcount_before)

    def test_kwarg_refs(self):
        kwargs = {}
        g = greenlet.greenlet(
            lambda **kwargs: greenlet.getcurrent().parent.switch(**kwargs))
        for i in range(100):
            g.switch(**kwargs)
        self.assertEqual(sys.getrefcount(kwargs), 2)

    if greenlet.GREENLET_USE_GC:
        # These only work with greenlet gc support

        def recycle_threads(self):
            # By introducing a thread that does sleep we allow other threads,
            # that have triggered their __block condition, but did not have a
            # chance to deallocate their thread state yet, to finally do so.
            # The way it works is by requiring a GIL switch (different thread),
            # which does a GIL release (sleep), which might do a GIL switch
            # to finished threads and allow them to clean up.
            def worker():
                time.sleep(0.001)
            t = threading.Thread(target=worker)
            t.start()
            time.sleep(0.001)
            t.join()

        def test_threaded_leak(self):
            gg = []
            def worker():
                # only main greenlet present
                gg.append(weakref.ref(greenlet.getcurrent()))
            for i in range(2):
                t = threading.Thread(target=worker)
                t.start()
                t.join()
                del t
            greenlet.getcurrent() # update ts_current
            self.recycle_threads()
            greenlet.getcurrent() # update ts_current
            gc.collect()
            greenlet.getcurrent() # update ts_current
            for g in gg:
                self.assertTrue(g() is None)

        def test_threaded_adv_leak(self):
            gg = []
            def worker():
                # main and additional *finished* greenlets
                ll = greenlet.getcurrent().ll = []
                def additional():
                    ll.append(greenlet.getcurrent())
                for i in range(2):
                    greenlet.greenlet(additional).switch()
                gg.append(weakref.ref(greenlet.getcurrent()))
            for i in range(2):
                t = threading.Thread(target=worker)
                t.start()
                t.join()
                del t
            greenlet.getcurrent() # update ts_current
            self.recycle_threads()
            greenlet.getcurrent() # update ts_current
            gc.collect()
            greenlet.getcurrent() # update ts_current
            for g in gg:
                self.assertTrue(g() is None)

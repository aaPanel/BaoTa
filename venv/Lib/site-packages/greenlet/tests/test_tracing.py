import unittest
import threading
import greenlet

class SomeError(Exception):
    pass

class TracingTests(unittest.TestCase):
    if greenlet.GREENLET_USE_TRACING:
        def test_greenlet_tracing(self):
            main = greenlet.getcurrent()
            actions = []
            def trace(*args):
                actions.append(args)
            def dummy():
                pass
            def dummyexc():
                raise SomeError()
            oldtrace = greenlet.settrace(trace)
            try:
                g1 = greenlet.greenlet(dummy)
                g1.switch()
                g2 = greenlet.greenlet(dummyexc)
                self.assertRaises(SomeError, g2.switch)
            finally:
                greenlet.settrace(oldtrace)
            self.assertEqual(actions, [
                ('switch', (main, g1)),
                ('switch', (g1, main)),
                ('switch', (main, g2)),
                ('throw', (g2, main)),
            ])

        def test_exception_disables_tracing(self):
            main = greenlet.getcurrent()
            actions = []
            def trace(*args):
                actions.append(args)
                raise SomeError()
            def dummy():
                main.switch()
            g = greenlet.greenlet(dummy)
            g.switch()
            oldtrace = greenlet.settrace(trace)
            try:
                self.assertRaises(SomeError, g.switch)
                self.assertEqual(greenlet.gettrace(), None)
            finally:
                greenlet.settrace(oldtrace)
            self.assertEqual(actions, [
                ('switch', (main, g)),
            ])

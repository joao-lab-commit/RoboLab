import os
import unittest

from windows_demo.amr_security_demo import is_gui_available, headless_mode


class HeadlessDemoTests(unittest.TestCase):
    def test_is_gui_available_without_display(self):
        original = os.environ.get('DISPLAY')
        os.environ.pop('DISPLAY', None)
        try:
            self.assertFalse(is_gui_available())
        finally:
            if original is not None:
                os.environ['DISPLAY'] = original

    def test_headless_mode_runs(self):
        messages = headless_mode(iterations=2, delay=0.01)
        self.assertTrue(messages)
        self.assertIn('STATUS', messages[0])


if __name__ == '__main__':
    unittest.main()

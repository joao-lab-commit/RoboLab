import unittest
from windows_demo.amr_security_demo import Demo, MAX_LINEAR, MAX_ANGULAR, MAX_ACCEL

class TestSafe4Policy(unittest.TestCase):
    def setUp(self):
        self.demo = Demo.__new__(Demo)
        self.demo.last_v = 0.0

    def test_command_valid(self):
        self.assertTrue(self.demo.validate(0.25, 0.15, 0.1)[0])

    def test_linear_attack_blocked(self):
        self.assertFalse(self.demo.validate(1.8, 0.0, 0.1)[0])

    def test_angular_attack_blocked(self):
        self.assertFalse(self.demo.validate(0.0, 2.0, 0.1)[0])

    def test_acceleration_blocked(self):
        self.assertFalse(self.demo.validate(0.4, 0.0, 0.01)[0])

    def test_nan_blocked(self):
        self.assertFalse(self.demo.validate(float('nan'), 0.0, 0.1)[0])

    def test_invalid_dt_blocked(self):
        self.assertFalse(self.demo.validate(0.0, 0.0, 0)[0])

    def test_limits_unchanged(self):
        self.assertEqual((MAX_LINEAR, MAX_ANGULAR, MAX_ACCEL), (0.45, 1.2, 3.8))

if __name__ == '__main__':
    unittest.main()

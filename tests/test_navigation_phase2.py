"""Executar: python -m unittest discover -s tests -p 'test_navigation_phase2.py' -v"""
import sys
import math
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'windows_demo'))
from navigation_core import (Pose, WaypointController, integrate, wrap_angle,
                             ROUTE_PIXELS, ORIGIN_PX, pixels_to_meters, route_is_clear)

OBSTACLES = [(x, y, x+60, y+70) for y in (55, 275) for x in (195, 315, 435, 555)]

class NavigationTests(unittest.TestCase):
    def test_angle(self):
        self.assertAlmostEqual(wrap_angle(3*math.pi), math.pi)

    def test_route_avoids_shelves(self):
        self.assertTrue(route_is_clear([ORIGIN_PX]+ROUTE_PIXELS, OBSTACLES))

    def test_no_collision_route(self):
        self.assertFalse(route_is_clear([(200, 100), (300, 100)], OBSTACLES))

    def test_finished_stops(self):
        nav = WaypointController([(0.0, 0.0)])
        self.assertEqual(nav.step(Pose()), (0.0, 0.0, 'CONCLUIDA'))
        self.assertEqual(nav.step(Pose()), (0.0, 0.0, 'CONCLUIDA'))

    def test_rotates_toward_goal(self):
        v, w, _ = WaypointController([(0, 1)]).step(Pose())
        self.assertEqual(v, 0)
        self.assertGreater(w, 0)

    def test_full_mission(self):
        nav = WaypointController([pixels_to_meters(p) for p in ROUTE_PIXELS])
        pose = Pose()
        for _ in range(4000):
            v, w, _ = nav.step(pose)
            self.assertLessEqual(abs(v), 0.28+1e-9)
            self.assertLessEqual(abs(w), 0.55+1e-9)
            pose = integrate(pose, v, w, 0.1)
            if nav.finished:
                break
        self.assertTrue(nav.finished, 'Missão não terminou')
        self.assertLess(math.dist((pose.x, pose.y), pixels_to_meters(ROUTE_PIXELS[-1])), 0.18)
        self.assertEqual(nav.step(pose)[:2], (0.0, 0.0))

if __name__ == '__main__':
    unittest.main()

"""Confere consistência estática do mundo SDF e dos tópicos da ponte."""
from pathlib import Path
import unittest
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / 'ros2_ws' / 'src' / 'amr_security_lab'

class WorldConsistencyTests(unittest.TestCase):
    def test_world_models_and_diff_drive(self):
        world = ET.parse(PKG / 'worlds' / 'warehouse.sdf').getroot().find('world')
        self.assertIsNotNone(world)
        models = {m.attrib['name']: m for m in world.findall('model')}
        self.assertGreaterEqual(len(models), 10)
        self.assertTrue({'ground', 'amr', 'shelf_1', 'shelf_2', 'shelf_3', 'shelf_4'} <= set(models))
        self.assertEqual(len(models), len(world.findall('model')))
        drive = models['amr'].find("plugin[@name='gz::sim::systems::DiffDrive']")
        self.assertIsNotNone(drive)
        self.assertEqual(drive.findtext('topic'), '/model/amr/cmd_vel')
        self.assertEqual(drive.findtext('odom_topic'), '/model/amr/odometry')

    def test_blender_world_meshes_and_robot_configuration(self):
        worlds = PKG / 'worlds'
        original = ET.parse(worlds / 'warehouse.sdf').find("world/model[@name='amr']")
        updated = ET.parse(worlds / 'warehouse_blender.sdf').find('world')
        robot = updated.find("model[@name='amr']")

        for path in ('joint', 'link/collision', 'plugin'):
            self.assertEqual(
                [ET.canonicalize(ET.tostring(item), strip_text=True)
                 for item in original.findall(path)],
                [ET.canonicalize(ET.tostring(item), strip_text=True)
                 for item in robot.findall(path)],
            )

        meshes = updated.findall('.//mesh/uri')
        self.assertEqual(len(meshes), 4)
        for mesh in meshes:
            obj = worlds / mesh.text
            with obj.open(encoding='utf-8') as file:
                material_line = next(line for line in file if line.startswith('mtllib '))
            self.assertTrue(obj.with_name(material_line.split(maxsplit=1)[1].strip()).is_file())

        lidar = robot.find("link[@name='base_link']/sensor[@type='gpu_lidar']")
        self.assertEqual(lidar.findtext('topic'), '/model/amr/scan')
        self.assertIsNotNone(updated.find("plugin[@name='gz::sim::systems::Sensors']"))

    def test_wheel_axes_and_floor_support(self):
        for filename in ('warehouse.sdf', 'warehouse_blender.sdf'):
            with self.subTest(filename=filename):
                robot = ET.parse(PKG / 'worlds' / filename).find("world/model[@name='amr']")
                spawn_z = float(robot.findtext('pose').split()[2])
                for side in ('left', 'right'):
                    axis = robot.find(f"joint[@name='{side}_wheel_joint']/axis/xyz")
                    self.assertEqual(axis.attrib['expressed_in'], 'base_link')
                    self.assertEqual(axis.text, '0 1 0')
                    wheel = robot.find(f"link[@name='{side}_wheel']")
                    pose = [float(value) for value in wheel.findtext('pose').split()]
                    self.assertEqual(pose[3:], [0, 0, 0])
                    roll = float(wheel.findtext('collision/pose').split()[3])
                    self.assertAlmostEqual(roll, 1.57079632679)
                    radius = float(wheel.findtext('collision/geometry/cylinder/radius'))
                    self.assertAlmostEqual(spawn_z + pose[2] - radius, 0)

                for name, clearance in (('apoio_traseiro', 0), ('apoio_dianteiro', .002)):
                    support = robot.find(f"link[@name='base_link']/collision[@name='{name}']")
                    center_z = float(support.findtext('pose').split()[2])
                    radius = float(support.findtext('geometry/sphere/radius'))
                    self.assertAlmostEqual(spawn_z + center_z - radius, clearance)

    def test_bridge_topics_and_directions(self):
        launch = (PKG / 'launch' / 'security_lab.launch.py').read_text(encoding='utf-8')
        self.assertIn('/model/amr/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist', launch)
        self.assertIn('/model/amr/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry', launch)
        self.assertIn('/model/amr/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan', launch)
        self.assertIn("('/model/amr/scan', '/scan')", launch)

if __name__ == '__main__':
    unittest.main()

from setuptools import setup
from glob import glob
import os

package_name = 'amr_security_lab'
setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
        (os.path.join('share', package_name, 'worlds'), glob('worlds/*.sdf')),
        (os.path.join('share', package_name, 'worlds', 'meshes'), glob('worlds/meshes/*.obj') + glob('worlds/meshes/*.mtl')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='AMR Security Lab Team',
    maintainer_email='team@example.com',
    description='Cyber-Physical AMR Security Lab',
    license='MIT',
    entry_points={'console_scripts': [
        'sentry = amr_security_lab.sentry:main',
        'attack_demo = amr_security_lab.attack_demo:main',
        'waypoint_nav = amr_security_lab.waypoint_nav:main',
        'dashboard = amr_security_lab.dashboard:main',
    ]},
)

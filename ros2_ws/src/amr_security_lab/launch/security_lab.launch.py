from launch import LaunchDescription
from launch.actions import AppendEnvironmentVariable, DeclareLaunchArgument, ExecuteProcess
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from ament_index_python.packages import get_package_share_directory
import os

def generate_launch_description():
    share = get_package_share_directory('amr_security_lab')
    worlds = os.path.join(share, 'worlds')
    world = PathJoinSubstitution([worlds, LaunchConfiguration('world')])
    return LaunchDescription([
        DeclareLaunchArgument('world', default_value='warehouse_blender.sdf',
                              choices=['warehouse_blender.sdf', 'warehouse.sdf']),
        AppendEnvironmentVariable('GZ_SIM_RESOURCE_PATH', worlds),
        ExecuteProcess(
            cmd=['gz', 'sim', '-r', world],
            output='screen'
        ),
        Node(
            package='ros_gz_bridge',
            executable='parameter_bridge',
            arguments=[
                '/model/amr/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist',
                '/model/amr/odometry@nav_msgs/msg/Odometry[gz.msgs.Odometry',
                '/model/amr/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan',
            ],
            remappings=[
                ('/model/amr/cmd_vel', '/cmd_vel'),
                ('/model/amr/odometry', '/odom'),
                ('/model/amr/scan', '/scan'),
            ],
            output='screen'
        ),
        Node(package='amr_security_lab', executable='sentry', output='screen'),
    ])

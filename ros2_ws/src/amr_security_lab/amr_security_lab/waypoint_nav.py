"""Fase 2: missão finita de waypoints usando /odom e /cmd_vel_untrusted.

Navegação para corredor conhecido, sem desvio dinâmico de obstáculos.
"""
import math
import time
import rclpy
from rclpy.node import Node
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist


def steering(x, y, yaw, goal, tolerance=0.18):
    dx, dy = goal[0]-x, goal[1]-y
    distance = math.hypot(dx, dy)
    if distance <= tolerance:
        return 0.0, 0.0, True
    error = math.atan2(math.sin(math.atan2(dy, dx)-yaw), math.cos(math.atan2(dy, dx)-yaw))
    angular = max(-0.55, min(0.55, 1.1*error))
    linear = min(0.28, 0.35*distance)*max(0.0, math.cos(error)) if abs(error) <= 0.5 else 0.0
    return linear, angular, False


class WaypointNav(Node):
    def __init__(self):
        super().__init__('waypoint_nav')
        self.pub = self.create_publisher(Twist, '/cmd_vel_untrusted', 10)
        self.create_subscription(Odometry, '/odom', self.on_odom, 10)
        self.create_timer(0.1, self.step)
        self.pose = None
        self.last_odom = None
        self.index = 0
        self.finished = False
        self.last_v = 0.0
        self.last_step = time.monotonic()
        # Trajeto no mundo SDF: contorna as prateleiras em y=0.
        self.declare_parameter('waypoints_x', [1.0, 2.0, 3.0, 4.5, 5.5]) #=
        self.declare_parameter('waypoints_y', [0.0, 0.0, 0.0, 0.0, 0.0]) #=
        xs = list(self.get_parameter('waypoints_x').value)
        ys = list(self.get_parameter('waypoints_y').value)
        if not xs or len(xs) != len(ys):
            raise ValueError('waypoints_x e waypoints_y devem ter o mesmo tamanho não nulo')
        self.goals = list(zip(xs, ys))
        self.get_logger().info('Missão iniciada: %d waypoints, sem desvio dinâmico.' % len(self.goals))

    def on_odom(self, msg):
        q = msg.pose.pose.orientation
        yaw = math.atan2(2*(q.w*q.z+q.x*q.y), 1-2*(q.y*q.y+q.z*q.z))
        p = msg.pose.pose.position
        if all(math.isfinite(v) for v in (p.x, p.y, yaw)):
            self.pose = (p.x, p.y, yaw)
            self.last_odom = time.monotonic()

    def publish(self, v=0.0, w=0.0):
        cmd = Twist()
        cmd.linear.x = v
        cmd.angular.z = w
        self.pub.publish(cmd)

    def step(self):
        now = time.monotonic()
        dt = max(0.01, min(0.3, now - self.last_step))
        self.last_step = now
        if self.finished or self.pose is None or self.last_odom is None or now-self.last_odom > 0.7:
            self.last_v = 0.0
            self.publish()
            return
        v, w, reached = steering(*self.pose, self.goals[self.index])
        if reached:
            self.index += 1
            self.last_v = 0.0
            self.publish()
            if self.index >= len(self.goals):
                self.finished = True
                self.get_logger().info('MISSÃO CONCLUÍDA: robô parado na expedição.')
            else:
                self.get_logger().info('Waypoint %d alcançado; próximo %s' % (self.index, self.goals[self.index]))
            return
        # Limita cada incremento para o sentinela aceitar mesmo com atrasos.
        dv = min(0.02, 0.4 * dt)
        v = max(self.last_v-dv, min(self.last_v+dv, v))
        self.last_v = v
        self.publish(v, w)


def main(args=None):
    rclpy.init(args=args)
    node = WaypointNav()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.publish()
        node.destroy_node()
        rclpy.shutdown()

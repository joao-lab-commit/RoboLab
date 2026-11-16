
"""ROS 2 sentry: only validated commands are forwarded to /cmd_vel."""

import math
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from std_msgs.msg import String

MAX_LINEAR = 0.45
MAX_ANGULAR = 1.2
MAX_ACCEL = 0.8


def validate_command(linear, angular, previous_linear, dt,
                     max_linear=MAX_LINEAR):
    """Validate velocity commands according to security policies."""

    values = (linear, angular, previous_linear, dt, max_linear)

    if not all(math.isfinite(v) for v in values) or dt <= 0:
        return False, "invalid_numeric_input"

    if abs(linear) > max_linear:
        return False, "linear_velocity_limit"

    if abs(angular) > MAX_ANGULAR:
        return False, "angular_velocity_limit"

    if abs(linear - previous_linear) / dt > MAX_ACCEL:
        return False, "acceleration_limit"

    return True, "accepted"


class SentryNode(Node):

    def __init__(self):
        super().__init__('amr_security_sentry')

        self.declare_parameter('max_linear', MAX_LINEAR)

        self.max_linear = float(
            self.get_parameter('max_linear').value
        )

        self.publisher = self.create_publisher(
            Twist, '/cmd_vel', 10
        )

        self.status_pub = self.create_publisher(
            String, '/security_status', 10
        )

        self.sub = self.create_subscription(
            Twist,
            '/cmd_vel_untrusted',
            self.on_command,
            10
        )

        self.previous_linear = 0.0
        self.last_ns = self.get_clock().now().nanoseconds

        self.accepted_count = 0
        self.blocked_count = 0

        self.get_logger().info(
            'SENTINELA ATIVO: monitoramento de comandos iniciado.'
        )

    def on_command(self, msg):

        now_ns = self.get_clock().now().nanoseconds

        dt = max(
            (now_ns - self.last_ns) / 1e9,
            0.05
        )

        self.last_ns = now_ns

        ok, reason = validate_command(
            msg.linear.x,
            msg.angular.z,
            self.previous_linear,
            dt,
            self.max_linear
        )

        output = Twist()

        if ok:
            output = msg
            self.previous_linear = msg.linear.x
            self.accepted_count += 1

            status = 'NORMAL:ACCEPTED'

            self.get_logger().info(
                f'Comando autorizado. Total: {self.accepted_count}'
            )

        else:
            self.previous_linear = 0.0
            self.blocked_count += 1

            status = 'ATTACK_BLOCKED:' + reason

            self.get_logger().warning(
                f'AMEACA DETECTADA: {reason} | '
                f'Total bloqueado: {self.blocked_count}'
            )

        self.publisher.publish(output)

        status_msg = String()
        status_msg.data = status
        self.status_pub.publish(status_msg)


def main(args=None):

    rclpy.init(args=args)

    node = SentryNode()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        node.get_logger().info(
            f'Resumo: {node.accepted_count} aceitos, '
            f'{node.blocked_count} bloqueados.'
        )

        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

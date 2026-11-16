
"""Controlled cybersecurity attack simulation for ROS 2."""

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist


class AttackDemo(Node):

    def __init__(self):
        super().__init__('controlled_injection_test')

        self.pub = self.create_publisher(
            Twist,
            '/cmd_vel_untrusted',
            10
        )

        self.count = 0

        # Sequência de testes controlados
        self.scenarios = [
            ("NORMAL", 0.2, 0.1),
            ("NORMAL", 0.3, 0.2),
            ("NORMAL", 0.2, 0.1),

            ("ATTACK_LINEAR", 1.5, 0.1),
            ("ATTACK_ANGULAR", 0.2, 2.0),
            ("ATTACK_LINEAR", -1.5, 0.1),

            ("NORMAL", 0.2, 0.1),

            ("ATTACK_ACCELERATION", 0.45, 0.1),

            ("STOP", 0.0, 0.0),
            ("STOP", 0.0, 0.0),
        ]

        self.timer = self.create_timer(
            1.0,
            self.send
        )

        self.get_logger().info(
            'SIMULADOR DE ATAQUE INICIADO'
        )

    def send(self):

        if self.count >= len(self.scenarios):
            self.timer.cancel()

            self.get_logger().info(
                'SIMULACAO FINALIZADA'
            )

            self.destroy_node()
            rclpy.shutdown()
            return

        attack_type, linear, angular = self.scenarios[self.count]

        msg = Twist()

        msg.linear.x = linear
        msg.angular.z = angular

        self.pub.publish(msg)

        if attack_type == "NORMAL":
            self.get_logger().info(
                'COMANDO LEGITIMO ENVIADO'
            )

        elif attack_type == "STOP":
            self.get_logger().info(
                'COMANDO DE PARADA ENVIADO'
            )

        else:
            self.get_logger().warning(
                f'TENTATIVA DE ATAQUE: {attack_type}'
            )

        self.count += 1


def main(args=None):

    rclpy.init(args=args)

    node = AttackDemo()

    try:
        rclpy.spin(node)

    except KeyboardInterrupt:
        pass

    finally:
        if rclpy.ok():
            node.destroy_node()
            rclpy.shutdown()


if __name__ == '__main__':
    main()

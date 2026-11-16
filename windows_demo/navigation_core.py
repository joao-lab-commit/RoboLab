"""Fase 2: controlador puro de waypoints e odometria cinemática (sem ROS)."""
import math
from dataclasses import dataclass


def wrap_angle(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


@dataclass
class Pose:
    x: float = 0.0
    y: float = 0.0
    theta: float = 0.0


class WaypointController:
    def __init__(self, goals, tolerance=0.18, max_linear=0.28, max_angular=0.55):
        if not goals:
            raise ValueError('A missão precisa de pelo menos um waypoint')
        self.goals = list(goals)
        self.tolerance = tolerance
        self.max_linear = max_linear
        self.max_angular = max_angular
        self.index = 0
        self.finished = False

    def step(self, pose):
        if self.finished:
            return 0.0, 0.0, 'CONCLUIDA'
        gx, gy = self.goals[self.index]
        dx, dy = gx - pose.x, gy - pose.y
        distance = math.hypot(dx, dy)
        if distance <= self.tolerance:
            self.index += 1
            if self.index >= len(self.goals):
                self.finished = True
                return 0.0, 0.0, 'CONCLUIDA'
            return 0.0, 0.0, 'WAYPOINT_ALCANCADO'
        error = wrap_angle(math.atan2(dy, dx) - pose.theta)
        angular = max(-self.max_angular, min(self.max_angular, 1.1 * error))
        if abs(error) > 0.5:
            return 0.0, angular, 'GIRANDO'
        linear = min(self.max_linear, 0.35 * distance) * max(0.0, math.cos(error))
        return linear, angular, 'NAVEGANDO'


def integrate(pose, linear, angular, dt):
    """Odometria ideal 2D: modelo unicíclo, sem sensores reais."""
    theta_mid = pose.theta + angular * dt / 2
    return Pose(pose.x + linear * math.cos(theta_mid) * dt,
                pose.y + linear * math.sin(theta_mid) * dt,
                wrap_angle(pose.theta + angular * dt))


# Coordenadas em pixels da demo Windows; 45 px = 1 metro.
# Corredor central sem atravessar racks, passando por coleta e expedição.
PIXELS_PER_METER = 45.0
ORIGIN_PX = (110.0, 230.0)
ROUTE_PIXELS = [
    (155.0, 230.0),  # saída do dock
    (385.0, 230.0),  # coleta no corredor central
    (640.0, 230.0),  # corredor até expedição
    (690.0, 260.0),  # acesso à área de expedição
    (690.0, 319.0),  # expedição
]


def pixels_to_meters(point):
    return ((point[0] - ORIGIN_PX[0]) / PIXELS_PER_METER,
            (point[1] - ORIGIN_PX[1]) / PIXELS_PER_METER)


def meters_to_pixels(pose):
    return (ORIGIN_PX[0] + pose.x * PIXELS_PER_METER,
            ORIGIN_PX[1] + pose.y * PIXELS_PER_METER)


def route_is_clear(points, obstacles, clearance=14):
    """Validação geométrica conservadora de segmentos versus racks retangulares."""
    for start, end in zip(points, points[1:]):
        length = math.dist(start, end)
        for n in range(max(1, math.ceil(length / 2)) + 1):
            t = n / max(1, math.ceil(length / 2))
            x = start[0] + (end[0] - start[0]) * t
            y = start[1] + (end[1] - start[1]) * t
            for x1, y1, x2, y2 in obstacles:
                if x1-clearance <= x <= x2+clearance and y1-clearance <= y <= y2+clearance:
                    return False
    return True

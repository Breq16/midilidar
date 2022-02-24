import sys
import atexit
import threading
import collections

import mido
import rplidar

import numpy as np

import pygame
from pygame.locals import *

from transform import get_matrix, apply
from axis import Axis

pygame.init()

font = pygame.font.SysFont("Comic Sans MS", 18)

fps = 60
fpsClock = pygame.time.Clock()

width, height = 640, 480
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("BMC LIDAR MIDI")

bounding_boxes = [None, None, None, None, None, None, None, None]

port = mido.open_output("BMC LIDAR", virtual=True)
atexit.register(port.close)

lidar = rplidar.RPLidar("/dev/tty.usbserial-0001")
lidar.start_motor()


def close_lidar():
    lidar.stop()
    lidar.stop_motor()
    lidar.disconnect()


atexit.register(close_lidar)

axes = [
    Axis(port, 0, 16, "note"),
    Axis(port, 1, 17, "cc"),
    Axis(port, 2, 18, "cc"),
    Axis(port, 3, 19, "cc"),
]

zoom = 200.0


def draw_box(box, index):
    pygame.draw.line(
        screen, (255, 0, 0) if index == 0 else (255, 255, 0), box[0], box[1], 5
    )
    pygame.draw.line(
        screen, (0, 255, 0) if index == 0 else (0, 255, 255), box[0], box[2], 5
    )
    pygame.draw.line(screen, (128, 128, 128), box[1], box[3], 5)
    pygame.draw.line(screen, (128, 128, 128), box[2], box[3], 5)


matrices = [None, None]


def calculate_matrices():
    if all(bounding_boxes[:4]):
        matrices[0] = get_matrix(bounding_boxes[:4])
    else:
        matrices[0] = None
    if all(bounding_boxes[4:]):
        matrices[1] = get_matrix(bounding_boxes[4:])
    else:
        matrices[1] = None


measurements = []


def measure():
    global measurements

    for scan in lidar.iter_scans(min_len=50):
        measurements = [(angle, distance) for quality, angle, distance in scan]


threading.Thread(target=measure, daemon=True, name="LIDAR Comms").start()


# Game loop.
while True:
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == MOUSEBUTTONDOWN:
            if event.button != 1:
                continue

            try:
                first_empty = bounding_boxes.index(None)
            except ValueError:
                first_empty = None

            if first_empty is not None:
                bounding_boxes[first_empty] = pygame.mouse.get_pos()

            calculate_matrices()

        elif event.type == KEYDOWN:
            if event.key == K_ESCAPE:
                pygame.quit()
                sys.exit()

            elif event.key == ord("r"):
                bounding_boxes = [None for _ in bounding_boxes]

                calculate_matrices()

            elif event.key == ord("n"):
                axes[0].toggle_mode()

            elif event.key == ord("m"):
                axes[2].toggle_mode()

            elif event.key == ord("z"):
                zoom *= 1.25

            elif event.key == ord("x"):
                zoom //= 1.25

    # Update.

    scale_factor = zoom / 1000

    point_cloud = [
        (
            int(dist * scale_factor * np.cos(angle * np.pi / 180) + width / 2),
            int(dist * scale_factor * np.sin(angle * np.pi / 180) + height / 2),
        )
        for (angle, dist) in measurements
    ]

    box_points = [[] for _ in matrices]

    for point in point_cloud:
        for i, matrix in enumerate(matrices):
            if matrix is None:
                break

            point_in_matrix = apply(point, matrix)

            if all(0 <= coord <= 1 for coord in point_in_matrix):
                box_points[i].append(point_in_matrix)
                break

    average_points = [None, None]

    for i, points in enumerate(box_points):
        if points:
            average_points[i] = (
                sum(point[0] for point in points) / len(points),
                sum(point[1] for point in points) / len(points),
            )

    axes[0].handle_input(average_points[0][0] if average_points[0] else None)
    axes[1].handle_input(average_points[0][1] if average_points[0] else None)
    axes[2].handle_input(average_points[1][0] if average_points[1] else None)
    axes[3].handle_input(average_points[1][1] if average_points[1] else None)

    # Draw.

    # Draw point cloud

    # zoom is for 1m, measurements are in mm

    for point in point_cloud:
        pygame.draw.circle(screen, (0, 255, 0), point, 1)

    # Draw ring at 1m
    pygame.draw.circle(screen, (255, 128, 0), (width // 2, height // 2), zoom, 2)

    # Draw ring at 0.5m
    pygame.draw.circle(screen, (128, 0, 255), (width // 2, height // 2), zoom / 2, 2)

    # Draw window information
    text = font.render(
        "Continuous Laser Harp with Time-of-Flight Axis Control Software",
        False,
        (255, 255, 255),
    )
    screen.blit(text, (10, 10))

    # Draw channel information

    colors = [(255, 0, 0), (0, 255, 0), (255, 255, 0), (0, 255, 255)]

    # Axis 0
    for i, axis in enumerate(axes):
        text = font.render(str(axis), False, colors[i])
        screen.blit(text, (10, 30 + i * 20))

    # Draw center of window
    pygame.draw.circle(screen, (255, 255, 255), (width // 2, height // 2), 5)

    # draw bounding box points
    for i, point in enumerate(bounding_boxes):
        if point:
            pygame.draw.circle(
                screen, (0, 0, 255) if i < 4 else (255, 0, 255), point, 5
            )

    # draw first box
    if all(bounding_boxes[:4]):
        draw_box(bounding_boxes[:4], 0)

    # draw second box
    if all(bounding_boxes[4:]):
        draw_box(bounding_boxes[4:], 1)

    pygame.display.flip()
    fpsClock.tick(fps)

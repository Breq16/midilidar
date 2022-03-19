import sys
import atexit

import numpy as np

import pygame
from pygame.locals import *

from transform import get_matrix, apply
from lidar import Lidar


def draw_box(screen, box, index):
    pygame.draw.line(
        screen, (255, 0, 0) if index == 0 else (255, 255, 0), box[0], box[1], 5
    )
    pygame.draw.line(
        screen, (0, 255, 0) if index == 0 else (0, 255, 255), box[0], box[2], 5
    )
    pygame.draw.line(screen, (128, 128, 128), box[1], box[3], 5)
    pygame.draw.line(screen, (128, 128, 128), box[2], box[3], 5)


matrices = [None, None]


def calculate_matrices(bounding_boxes):
    if all(bounding_boxes[:4]):
        matrices[0] = get_matrix(bounding_boxes[:4])
    else:
        matrices[0] = None
    if all(bounding_boxes[4:]):
        matrices[1] = get_matrix(bounding_boxes[4:])
    else:
        matrices[1] = None


lidar = Lidar()


def main(queue):
    pygame.init()

    fps = 60
    fpsClock = pygame.time.Clock()

    width, height = 640, 480
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Sensor Control")

    bounding_boxes = [None, None, None, None, None, None, None, None]

    zoom = 200.0

    lidar.start()
    atexit.register(lidar.stop)

    lidar.start_measuring()

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

                calculate_matrices(bounding_boxes)

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    pygame.quit()
                    sys.exit()

                elif event.key == ord("r"):
                    bounding_boxes = [None for _ in bounding_boxes]

                    calculate_matrices(bounding_boxes)

                elif event.key == ord("z"):
                    zoom *= 1.25

                elif event.key == ord("x"):
                    zoom //= 1.25

        scale_factor = zoom / 1000
        point_cloud = [
            (
                int(dist * scale_factor * np.cos(angle * np.pi / 180) + width / 2),
                int(dist * scale_factor * np.sin(angle * np.pi / 180) + height / 2),
            )
            for (angle, dist) in lidar.measurements
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

        queue.put(
            [
                average_points[0][0] if average_points[0] else None,
                average_points[0][1] if average_points[0] else None,
                average_points[1][0] if average_points[1] else None,
                average_points[1][1] if average_points[1] else None,
            ]
        )

        for point in point_cloud:
            pygame.draw.circle(screen, (0, 255, 0), point, 1)

        # Zoom reference rings
        pygame.draw.circle(screen, (255, 128, 0), (width // 2, height // 2), zoom, 2)
        pygame.draw.circle(
            screen, (128, 0, 255), (width // 2, height // 2), zoom / 2, 2
        )
        pygame.draw.circle(screen, (255, 255, 255), (width // 2, height // 2), 5)

        # draw bounding boxes
        for i, point in enumerate(bounding_boxes):
            if point:
                pygame.draw.circle(
                    screen, (0, 0, 255) if i < 4 else (255, 0, 255), point, 5
                )

        if all(bounding_boxes[:4]):
            draw_box(screen, bounding_boxes[:4], 0)
        if all(bounding_boxes[4:]):
            draw_box(screen, bounding_boxes[4:], 1)

        pygame.display.flip()
        fpsClock.tick(fps)

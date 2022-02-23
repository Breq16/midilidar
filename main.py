import sys
import atexit

import numpy as np

import mido

import pygame
from pygame.locals import *

from transform import get_matrices, apply

pygame.init()

font = pygame.font.SysFont("Comic Sans MS", 18)

fps = 5  # 60
fpsClock = pygame.time.Clock()

width, height = 640, 480
screen = pygame.display.set_mode((width, height))
pygame.display.set_caption("BMC LIDAR MIDI")

bounding_boxes = [None, None, None, None, None, None, None, None]

port = mido.open_output("BMC LIDAR", virtual=True)
atexit.register(port.close)

modes = ["note", "cc"]


def draw_box(box, index):
    pygame.draw.line(
        screen, (255, 0, 0) if index == 0 else (255, 255, 0), box[0], box[1], 5
    )
    pygame.draw.line(
        screen, (0, 255, 0) if index == 0 else (0, 255, 255), box[0], box[2], 5
    )
    pygame.draw.line(screen, (128, 128, 128), box[1], box[3], 5)
    pygame.draw.line(screen, (128, 128, 128), box[2], box[3], 5)


# def box_to_transformation(box):
#     """
#     Given a box (quadrilateral) in global coordinates, return a transformation
#     matrix that maps vectors in the global basis to vectors in the box basis.
#     """

#     # Based on work by
#     # https://math.stackexchange.com/questions/296794/finding-the-transform-matrix-from-4-projected-points-with-javascript/339033#339033

#     # Convert box coordinates to homogeneous coordinates as numpy arrays
#     homo_box = [np.transpose(np.array([[p[0], p[1], 1]])) for p in box]

#     # Concate three of the box points as column vectors into a matrix
#     three_points = np.concatenate(homo_box[:3], axis=1)
#     fourth_point = homo_box[3]

#     # Solve (three_points) * (coefficients) = (fourth_point)
#     coefficients = np.matmul(np.linalg.inv(three_points), fourth_point)

#     # Scale the each column matrix of three points by the computed coefficients
#     scale = np.array(
#         [
#             [coefficients[0][0], 0, 0],
#             [0, coefficients[1][0], 0],
#             [0, 0, coefficients[2][0]],
#         ]
#     )

#     scaled = np.matmul(three_points, scale)

#     return scaled


# def point_within_box(point, box):
#     # Convert the point to homogeneous coordinates
#     homo_source_point = np.array([[point[0], point[1], 1]])
#     homo_source_vector = np.transpose(homo_source_point)

#     # Matrix which maps a vector to the global basis
#     # map_to_global_basis = box_to_transformation(
#     #     [(0, 0), (width, 0), (0, height), (width, height)]
#     # )
#     # Matrix which maps a vector to the basis of the provided box
#     map_to_box_basis = box_to_transformation(box)

#     # Combined matrix to map a vector in the global basis to the box basis
#     # transform_global_to_box = np.matmul(
#     #     map_to_box_basis, np.linalg.inv(map_to_global_basis)
#     # )
#     transform_global_to_box = map_to_box_basis

#     # Normalize the transformation matrix
#     transform_global_to_box /= transform_global_to_box[2][2]

#     # Use the matrix to transform the point to the box basis
#     homo_dest_vector = np.matmul(transform_global_to_box, homo_source_vector)
#     homo_dest_point = np.transpose(homo_dest_vector)[0]

#     # Convert back to Cartesian
#     return (
#         homo_dest_point[0] / homo_dest_point[2],
#         homo_dest_point[1] / homo_dest_point[2],
#     )

matrices = [None, None]


def calculate_matrices():
    if all(bounding_boxes):
        matrices[0] = get_matrices(bounding_boxes[:4])[0]
        matrices[1] = get_matrices(bounding_boxes[4:])[0]
    else:
        matrices[0] = None
        matrices[1] = None


# Game loop.
while True:
    screen.fill((0, 0, 0))

    for event in pygame.event.get():
        if event.type == QUIT:
            pygame.quit()
            sys.exit()
        elif event.type == MOUSEBUTTONDOWN:
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
                modes[0] = "cc" if modes[0] == "note" else "note"

            elif event.key == ord("m"):
                modes[1] = "cc" if modes[1] == "note" else "note"

    # Update.

    # placeholder: use mouse position instead of lidar
    mousePos = pygame.mouse.get_pos()

    if all(bounding_boxes):
        pointWithinFirst = apply(mousePos, matrices[0])
        pointWithinSecond = apply(mousePos, matrices[1])

        print(mousePos, pointWithinFirst, pointWithinSecond)

    # Draw.

    # Draw window information
    text = font.render(
        "Continuous Laser Harp with Time-of-Flight Axis Control Software",
        False,
        (255, 255, 255),
    )
    screen.blit(text, (10, 10))

    # Draw channel information

    # Axis 0
    if modes[0] == "note":
        text = font.render("Note", False, (255, 0, 0))
    else:
        text = font.render("CC 16", False, (255, 0, 0))
    screen.blit(text, (10, 30))

    # Axis 1
    text = font.render("CC 17", False, (0, 255, 0))
    screen.blit(text, (10, 50))

    # Axis 2
    if modes[1] == "note":
        text = font.render("Note", False, (255, 255, 0))
    else:
        text = font.render("CC 18", False, (255, 255, 0))
    screen.blit(text, (10, 70))

    # Axis 3
    text = font.render("CC 19", False, (0, 255, 255))
    screen.blit(text, (10, 90))

    # Draw center of window
    pygame.draw.circle(screen, (255, 255, 255), (width // 2, height // 2), 5)

    # Draw point cloud
    # TODO

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

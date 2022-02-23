import numpy as np

# Based on work by
# https://math.stackexchange.com/a/339033


def map_basis_to_points(points):
    """
    Return a matrix transforming vectors in the global basis to vectors
    in the basis represented by ``points``.

    Parameters
    ----------
    points
        A list of points (as tuples) in the basis to map to.

    Returns
    -------
    np.ndarray
        A matrix transforming vectors in the global basis to vectors
        in the basis represented by ``points``.
    """

    # Convert points (as a list of tuples)
    # to homogenous coordinates
    # (as a list of numpy arrays representing column vectors)
    homo_points = [np.array([[point[0]], [point[1]], [1]]) for point in points]

    # Concatenate three homogenous coordinate column vectors into matrix
    three_points = np.concatenate(homo_points[:3], axis=1)
    # Store fourth homogenous coordinate
    fourth_point = homo_points[3]

    # Solve (three_points) * (coefficients) = (fourth_point)
    # for the coefficients
    coefficients = np.matmul(np.linalg.inv(three_points), fourth_point)

    # Scale each column of the three points by the computed coefficients

    # Calculate the scale matrix
    scale = np.array(
        [
            [coefficients[0][0], 0, 0],
            [0, coefficients[1][0], 0],
            [0, 0, coefficients[2][0]],
        ]
    )

    # Apply the scale matrix to the three points
    scaled = np.matmul(three_points, scale)

    return scaled


def get_matrix(box):
    """
    Get the transformation matrix from points in the global scene to their
    relative position within the given bounding box (quadrilateral).

    Parameters
    ----------
    box
        A list of four points (as tuples) in the global scene.

    Returns
    -------
    np.ndarray
        A transformation matrix from points in the global scene to their
        relative position within the given bounding box.
    """

    # The order of this is important!!
    relative_corners = (
        (0, 0),
        (1, 0),
        (0, 1),
        (1, 1),
    )

    # Map from the global basis to the pixel basis
    basis_to_pixel = map_basis_to_points(box)
    # Map from the global basis to the relative basis
    basis_to_relative = map_basis_to_points(relative_corners)

    # Map from the pixel basis to the relative basis
    pixel_to_relative = np.matmul(basis_to_relative, np.linalg.inv(basis_to_pixel))

    # Map from the relative basis to the pixel basis
    # relative_to_pixel = np.matmul(basis_to_pixel, np.linalg.inv(basis_to_relative))

    # Normalize the matrices
    pixel_to_relative /= pixel_to_relative[2][2]
    # relative_to_pixel /= relative_to_pixel[2][2]

    return pixel_to_relative


def apply(source_point, matrix):
    """
    Apply a transformation matrix for homogenous coordinates
    to a point in Cartesian coordinates.

    Parameters
    ----------
    source_point
        A tuple representing a point in Cartesian coordinates.
    matrix
        A transformation matrix for homogenous coordinates.

    Returns
    -------
    tuple
        A tuple representing the result of the transformation in Cartesian
        coordinates.
    """

    # Convert the source point to homogenous coordinates
    homo_source_point = np.array([[coord] for coord in source_point] + [[1]])

    # Apply the matrix to the source point
    homo_dest_point = np.matmul(matrix, homo_source_point)

    # Convert the destination point to Cartesian coordinates
    dest_point = (
        homo_dest_point[0][0] / homo_dest_point[2][0],
        homo_dest_point[1][0] / homo_dest_point[2][0],
    )

    return dest_point

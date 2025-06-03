"""Fit an ellipsoid to a set of marker locations."""

from __future__ import annotations

import logging

import numpy as np

from pyrot.eye_modelling.common_methods import getTranslationMatrix

logger = logging.getLogger(__name__)


def ellipsoid_fit(
    markers_in_eye: list[list[float]],
    eye_shape: str,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, float]:
    """Fit an ellipsoid/sphere/paraboloid/hyperboloid to a set of xyz data points.

    Parameters
    ----------
    markers_in_eye : list of [x, y, z]
        Cartesian data, list of three n x 1 vectors.
    eye_shape : str
        Shape to fit:
        - 'sphere' fits a sphere
        - 'ellipsoid' fits an ellipsoid with its axes aligned along [x, y, z] axes
        - 'EYEPLAN' fits an ellipsoid with x- and z- radii equal

    Returns
    -------
    center : ndarray
        Ellipsoid or other conic center coordinates [xc, yc, zc].
    radii : ndarray
        Ellipsoid or other conic radii [a, b, c].
    evecs : ndarray
        The radii directions as columns of the 3x3 matrix.

    Raises
    ------
    NotImplementedError
        If an unsupported eye shape is provided.

    Notes
    -----
    It does not find exactly the best fitting ellipse (see van Vught et al.).
    """

    # Based on a script by:
    # Yury Petrov, Oculus VR
    # https://www.mathworks.com/matlabcentral/fileexchange/24693-ellipsoid-fit
    # Ported from MATLAB to Python by Martin Janson 2022-09-02.
    # Further adapted and extended by Jan-Willem Beenakker and the LUMC-MReye group.

    logger.debug("Starting ellipsoid_fit function")
    logger.debug("eye_shape: %s", eye_shape)
    logger.debug("markers_in_eye: %s", markers_in_eye)

    assert not (
        len(markers_in_eye) < 6 and (eye_shape == r"ellipsoid")  # noqa: PLR2004
    ), r"Must have at least 6 points to fit a unique oriented ellipsoid"

    assert not (
        len(markers_in_eye) < 5 and (eye_shape == r"EYEPLAN")  # noqa: PLR2004
    ), r"Must have at least 5 points to fit a unique oriented (EYEPLAN) ellipsoid with two equal radii"

    assert not (
        len(markers_in_eye) < 4 and (eye_shape == r"sphere")  # noqa: PLR2004
    ), r"Must have at least 4 points to fit a unique sphere"

    x = np.zeros(len(markers_in_eye))
    y = np.zeros(len(markers_in_eye))
    z = np.zeros(len(markers_in_eye))
    for i, m in enumerate(markers_in_eye):
        x[i] = m[0]
        y[i] = m[1]
        z[i] = m[2]

    # fit ellipsoid in the form Ax^2 + By^2 + Cz^2 + 2Gx + 2Hy + 2Iz = 1
    if eye_shape == "ellipsoid":  # all radii are independent
        D = np.array(
            [
                x * x + y * y - 2 * z * z,
                x * x + z * z - 2 * y * y,
                2 * x,
                2 * y,
                2 * z,
                1 + 0 * x,
            ]  # TODO: revert these changes back so these are multi-line and add noqa statement
        )  # ndatapoints x 6 ellipsoid parameters

    # fit ellipsoid in the form Ax^2 + By^2 + Cz^2 = 1
    elif eye_shape == "ellipsoid_fixedCenter":  # radii free, center fixed to 0
        D = np.array(
            [x * x + y * y - 2 * z * z, x * x + z * z - 2 * y * y, 1 + 0 * x]
        )  # ndatapoints x 3 ellipsoid parameters

    # fit ellipsoid in the form Ax^2 + By^2 + Cz^2 + 2Gx + 2Hy + 2Iz = 1,
    # where A = B or B = C or A = C
    elif eye_shape == "EYEPLAN":  # 2equal radii (Rx=Ry)
        D = np.array(
            [x * x + z * z - 2 * y * y, 2 * x, 2 * y, 2 * z, 1 + 0 * x]
        )  # ndatapoints x 5 ellipsoid parameters

    # fit sphere in the form A(x^2 + y^2 + z^2) + 2Gx + 2Hy + 2Iz = 1
    elif eye_shape == "sphere":  # all radii are equal
        D = np.array([2 * x, 2 * y, 2 * z, 1 + 0 * x])  # ndatapoints x 4 ellipsoid parameters
    else:
        raise NotImplementedError("Unknown parameter value")

    Dt = D
    D = np.matrix.transpose(Dt)

    # solve the normal system of equations
    d2 = x * x + y * y + z * z  # the RHS of the llsq problem (y's)
    u = np.linalg.inv(Dt @ D) @ (Dt @ d2)  # solution to the normal equations

    condition_of_inverse = np.linalg.cond(Dt @ D)

    logger.debug("Condition value of the normal system of equations Dt@D= %s", condition_of_inverse)
    logger.debug("u: %s", u)

    v = np.zeros(10)
    if eye_shape == "ellipsoid":
        v[0] = u[0] + u[1] - 1
        v[1] = u[0] - 2 * u[1] - 1
        v[2] = u[1] - 2 * u[0] - 1
        v[3:6] = np.array(
            [
                0,
                0,
                0,
            ]
        )
        v[6:10] = u[2:6]
        # v = [ v[0], v[1], v[2], 0, 0, 0, u[2 : 6] ]
    elif eye_shape == "ellipsoid_fixedCenter":
        v[0] = u[0] + u[1] - 1
        v[1] = u[0] - 2 * u[1] - 1
        v[2] = u[1] - 2 * u[0] - 1
        v[3:9] = np.array([0, 0, 0, 0, 0, 0])
        v[9] = u[2]
        # v = [ v[0], v[1], v[2], 0, 0, 0, 0,0,0 ,u[3] ]
    elif eye_shape == "EYEPLAN":
        v[0] = u[0] - 1
        v[1] = -2 * u[0] - 1
        v[2] = u[0] - 1
        v[3:6] = np.array(
            [
                0,
                0,
                0,
            ]
        )
        v[6:10] = u[1:5]
        # v = [ v[0], v[1], v[2], 0, 0, 0, u[1 : 5] ]
    elif eye_shape == "sphere":
        v[0:6] = np.array(
            [
                -1,
                -1,
                -1,
                0,
                0,
                0,
            ]
        )
        v[6:10] = u[0:4]
        # v = [ -1, -1, -1, 0, 0, 0, u[0 : 4] ]
    else:
        raise NotImplementedError("Unknown parameter value")

    logger.debug("v: %s", v)
    # form the algebraic form of the ellipsoid
    A = np.array(
        [[v[0], v[3], v[4], v[6]],
         [v[3], v[1], v[5], v[7]],
         [v[4], v[5], v[2], v[8]],
         [v[6], v[7], v[8], v[9]]]
    )  # fmt: skip

    center = -np.linalg.inv(A[0:3, 0:3]) @ v[6:9]

    # form the corresponding translation matrix
    T = getTranslationMatrix(center[0], center[1], center[2])
    # translate to the center
    R = np.matrix.transpose(T) @ A @ T
    # solve the eigenproblem
    evals, evecs = np.linalg.eig(R[0:3, 0:3] / -R[3, 3])

    radii = np.sqrt(1.0 / abs(evals))

    sgns = np.sign(evals)
    radii *= sgns

    logger.debug("centers: %s", center)
    logger.debug("radii: %s", radii)

    return center, radii, evecs, condition_of_inverse

"""Common methods for eye modelling."""

from __future__ import annotations

import logging
import math

import numpy as np

logger = logging.getLogger(__name__)


def getTranslationMatrix(x: float, y: float, z: float) -> np.ndarray:
    """Generate a translation matrix for 3D transformations.

    Parameters
    ----------
    x : float
      Translation along the x-axis.
    y : float
      Translation along the y-axis.
    z : float
      Translation along the z-axis.

    Returns
    -------
    numpy.ndarray
      A 4x4 translation matrix.
    """
    return np.array([[1, 0, 0, x], [0, 1, 0, y], [0, 0, 1, z], [0, 0, 0, 1]])


def toRadians(angleDegrees: float) -> float:
    """Convert an angle from degrees to radians.

    Parameters
    ----------
    angleDegrees : float
      Angle in degrees.

    Returns
    -------
    float
      Angle in radians.
    """
    return angleDegrees * math.pi / 180


def toDegrees(angleRadians: float) -> float:
    """Convert an angle from radians to degrees.

    Parameters
    ----------
    angleRadians : float
      Angle in radians.

    Returns
    -------
    float
      Angle in degrees.
    """
    return angleRadians * 180 / math.pi


def getIdentityMatrix() -> np.ndarray:
    """Returns a 4x4 identity matrix.

    Returns
    -------
    numpy.ndarray
      A 4x4 identity matrix.
    """
    return np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])


def getRotationMatrixX(angleDeg: float) -> np.ndarray:
    """Calculate the rotation matrix for a rotation around the X-axis.

    Parameters
    ----------
    angleDeg : float
      The angle of rotation in degrees.

    Returns
    -------
    numpy.ndarray
      A 4x4 rotation matrix representing the rotation around the X-axis.
    """
    angleRad = toRadians(angleDeg)
    sin_a = math.sin(angleRad)
    cos_a = math.cos(angleRad)
    return np.array([[1, 0, 0, 0], [0, cos_a, -sin_a, 0], [0, sin_a, cos_a, 0], [0, 0, 0, 1]])


def getRotationMatrixY(angleDeg: float) -> np.ndarray:
    """Generate a rotation matrix for a rotation around the Y-axis.

    Parameters
    ----------
    angleDeg : float
      The angle of rotation in degrees.

    Returns
    -------
    numpy.ndarray
      A 4x4 rotation matrix representing the rotation around the Y-axis.
    """
    angleRad = toRadians(angleDeg)
    sin_a = math.sin(angleRad)
    cos_a = math.cos(angleRad)
    return np.array([[cos_a, 0, sin_a, 0], [0, 1, 0, 0], [-sin_a, 0, cos_a, 0], [0, 0, 0, 1]])


def getRotationMatrixZ(angleDeg: float) -> np.ndarray:
    """Generate a rotation matrix for a rotation around the Z-axis.

    Parameters
    ----------
    angleDeg : float
      The angle of rotation in degrees.

    Returns
    -------
    numpy.ndarray
      A 4x4 rotation matrix representing the rotation around the Z-axis.
    """
    angleRad = toRadians(angleDeg)
    sin_a = math.sin(angleRad)
    cos_a = math.cos(angleRad)
    return np.array([[cos_a, -sin_a, 0, 0], [sin_a, cos_a, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])


def getEyeModelGeometry(eyeModel: object, structureType: str) -> object:
    """Retrieve the geometry for a specific structure type from the eye model.

    Parameters
    ----------
    eyeModel : object
      The eye model containing the geometries.
    structureType : str
      The type of structure to retrieve the geometry for.

    Returns
    -------
    object
      The geometry corresponding to the specified structure type.
    """
    logger.debug("running getEyeModelGeometry function")

    return next(
        rg
        for rg in eyeModel.EyeModelParameters.AssociatedRoiGeometries
        if rg.GeneratedGeometryStatus.GeneratedStructureType == structureType
    )


def getClipGeometries(eyeModel: object) -> list:
    """Retrieve all clip geometries from the eye model.

    Parameters
    ----------
    eyeModel : object
      The eye model containing the clip geometries.

    Returns
    -------
    list
      A list of clip geometries.
    """
    return list(eyeModel.ClipParameters.AssociatedRoiGeometries)


def getEyeModelToPatientRotationMatrix(rotationXDeg: float, rotationYDeg: float, rotationZDeg: float) -> np.ndarray:
    """Calculate the rotation matrix to transform from eye model coordinates to patient coordinates.

    Parameters
    ----------
    rotationXDeg : float
      Rotation angle around the X-axis in degrees.
    rotationYDeg : float
      Rotation angle around the Y-axis in degrees.
    rotationZDeg : float
      Rotation angle around the Z-axis in degrees.

    Returns
    -------
    numpy.ndarray
      A 4x4 rotation matrix.
    """
    return getRotationMatrixZ(rotationZDeg) @ getRotationMatrixX(rotationXDeg) @ getRotationMatrixY(rotationYDeg)

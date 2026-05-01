"""Data structures for interacting with RayOcular eye models."""

from __future__ import annotations

import json
import logging
from dataclasses import MISSING, asdict, dataclass, fields, is_dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Optional, TypeVar, get_type_hints

from pyrot.eye_modelling.datamodels import validators
from pyrot.eye_modelling.datamodels.validators import (
    RayOcularField,
    ValidatedField,
    Vector3,
)

if TYPE_CHECKING:
    from os import PathLike

logger = logging.getLogger(__name__)

_Self = TypeVar("_Self")


class BaseModel:
    """Abstract base class for RayOcular data models.

    For full functionality, all subclasses must be dataclasses and use the `RayOcularField` descriptor to define fields that correspond to RayOcular properties.

    Methods
    -------
    from_rayocular(cls, rayocular_object)
        Converts a RayOcular object to an instance of the data model.

    to_rayocular(self)
        Converts the data model instance to a RayOcular object.

    to_dict(self)
        Converts the data model instance to a dictionary.

    from_dict(cls, data)
        Creates an instance of the data model from a dictionary.
    """

    @classmethod
    def _get_rayocular_fields(cls) -> dict[str, RayOcularField]:
        if not is_dataclass(cls):
            raise TypeError(f"All classes in the model must be dataclasses, but {cls.__name__} is not.")

        field_names = (f.name for f in fields(cls))

        rayocular_fields = {}

        for name in field_names:
            field_value = cls.__dict__.get(name)

            if isinstance(field_value, RayOcularField):
                rayocular_fields[name] = field_value

        return rayocular_fields

    @classmethod
    def from_rayocular(cls: type[_Self], rayocular_object) -> _Self:
        """Convert a RayOcular object to an instance of the data model.

        Parameters
        ----------
        rayocular_object : Any
            The RayOcular object to convert.

        Returns
        -------
        BaseModel
            An instance of the data model.

        Raises
        ------
        ValueError
            If any field in the data model does not have a corresponding RayOcular name.
        """
        model_fields = {}

        # Iterate over RayOcular fields
        for field_name, field_value in cls._get_rayocular_fields().items():  # type: ignore
            if isinstance(field_value, RayOcularField):
                if field_value.rayocular_name is None:
                    raise ValueError(f"Field {field_name} does not have a RayOcular name.")

                model_fields[field_name] = getattr(rayocular_object, field_value.rayocular_name)

        return cls(**model_fields)

    def to_rayocular(self) -> dict[str, Any]:
        """Convert the data model instance to a RayOcular dictionary.

        Returns
        -------
        dict[str, Any]
            A dictionary that can be used to update the model in RayOcular.
        """
        rayocular_fields = {}

        for field_name, field_value in type(self)._get_rayocular_fields().items():  # noqa: SLF001
            value = getattr(self, field_name)

            if isinstance(value, BaseModel):
                rayocular_fields[field_value.rayocular_name] = value.to_rayocular()
            elif isinstance(value, Vector3):
                rayocular_fields[field_value.rayocular_name] = [value.x, value.y, value.z]
            elif is_dataclass(value):
                rayocular_fields[field_value.rayocular_name] = asdict(value)
            else:
                rayocular_fields[field_value.rayocular_name] = [value]

        return rayocular_fields

    def to_dict(self) -> dict[str, Any]:
        """Convert the data model instance to a dictionary.

        This method is only implemented for dataclasses.

        Returns
        -------
        dict[str, Any]
            A dictionary representation of the data model instance.

        Raises
        ------
        NotImplementedError
            If the data model instance is not a dataclass.
        """
        if is_dataclass(self):
            return asdict(self)

        raise NotImplementedError("to_dict is only implemented for dataclasses.")

    @classmethod
    def from_dict(cls: type[_Self], data: dict[str, Any]) -> _Self:
        """Create an instance of the data model from a dictionary.

        This method is only implemented for dataclasses.

        Parameters
        ----------
        data : dict[str, Any]
            A dictionary representation of the data model instance.

        Returns
        -------
        BaseModel
            An instance of the data model.

        Raises
        ------
        NotImplementedError
            If the data model class is not a dataclass.
        TypeError
            If the type of any field cannot be resolved.
        ValueError
            If any required field is missing from the data.
        """
        if not is_dataclass(cls):
            raise NotImplementedError("from_dict is only implemented for dataclasses.")

        data = data.copy()
        field_types = get_type_hints(cls)

        for field in fields(cls):
            field_type = field_types.get(field.name)

            if field_type is None or isinstance(field_type, str):
                raise TypeError(f"Failed to resolve type for field {field.name} in class {cls.__name__}.")

            if field.name not in data:
                if field.default is MISSING:
                    raise ValueError(f"Missing field {field.name} in data.")

                data[field.name] = field.default

        return cls(**data)


@dataclass
class EyeModelMeasurements(BaseModel):
    """Store measurements for an eye model.

    Attributes
    ----------
    cornea_lens_distance : float
        Distance from cornea to lens.
    eye_length : float
        Total length of the eye.
    eye_width : float
        Width of the eye.
    lens_thickness : float
        Thickness of the lens.
    limbus_diameter : float
        Diameter of the limbus.
    """

    cornea_lens_distance: RayOcularField[float] = RayOcularField(validators.positive_float, "CorneaLensDistance")
    eye_length: RayOcularField[float] = RayOcularField(validators.positive_float, "EyeLength")
    eye_width: RayOcularField[float] = RayOcularField(validators.positive_float, "EyeWidth")
    lens_thickness: RayOcularField[float] = RayOcularField(validators.positive_float, "LensThickness")
    limbus_diameter: RayOcularField[float] = RayOcularField(validators.positive_float, "LimbusDiameter")


@dataclass
class AnteriorChamber(BaseModel):
    """Store anterior chamber parameters for an eye model.

    Attributes
    ----------
    local_rotation : Vector3[float]
        Local rotation of the anterior chamber.
    local_scale : Vector3[float]
        Local scale of the anterior chamber.
    local_translation : Vector3[float]
        Local translation of the anterior chamber.
    """

    local_rotation: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "ChamberLocalRotation")
    local_scale: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(validators.positive_float), "ChamberLocalScale"
    )
    local_translation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "ChamberLocalTranslation"
    )


@dataclass
class CiliaryBody(BaseModel):
    """Store ciliary body parameters for an eye model.

    Attributes
    ----------
    base_curvature : float
        Base curvature of the ciliary body.
    height : float
        Height of the ciliary body.
    local_rotation : Vector3[float]
        Local rotation of the ciliary body.
    local_scale : Vector3[float]
        Local scale of the ciliary body.
    local_translation : Vector3[float]
        Local translation of the ciliary body.
    """

    base_curvature: RayOcularField[float] = RayOcularField(float, "CiliaryBodyBaseCurvature")
    height: RayOcularField[float] = RayOcularField(validators.positive_float, "CiliaryBodyHeight")
    local_rotation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "CiliaryBodyLocalRotation"
    )
    local_scale: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(validators.positive_float), "CiliaryBodyLocalScale"
    )
    local_translation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "CiliaryBodyLocalTranslation"
    )


@dataclass
class Cornea(BaseModel):
    """Store cornea parameters for an eye model.

    Attributes
    ----------
    local_rotation : Vector3[float]
        Local rotation of the cornea.
    local_scale : Vector3[float]
        Local scale of the cornea.
    local_translation : Vector3[float]
        Local translation of the cornea.
    semi_axis : Vector3[float]
        Semi-axes of the cornea.
    thickness : float
        Thickness of the cornea.
    """

    local_rotation: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "CorneaLocalRotation")
    local_scale: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(validators.positive_float), "CorneaLocalScale"
    )
    local_translation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "CorneaLocalTranslation"
    )
    semi_axis: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "CorneaSemiAxis")
    thickness: RayOcularField[float] = RayOcularField(validators.positive_float, "CorneaThickness")


@dataclass
class Eye(BaseModel):
    """Store eye positioning and scale parameters.

    Attributes
    ----------
    pivot : Vector3[float]
        Pivot point of the eye.
    rotation : Vector3[float]
        Rotation of the eye.
    scale : Vector3[float]
        Scale of the eye.
    translation : Vector3[float]
        Translation of the eye.
    """

    pivot: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "EyePivot")
    rotation: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "EyeRotation")
    scale: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(validators.positive_float), "EyeScale")
    translation: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "EyeTranslation")


@dataclass
class Iris(BaseModel):
    """Store iris parameters for an eye model.

    Attributes
    ----------
    inner_semi_axis : RayOcularField[Vector3[float]]
        Inner semi-axes of the iris.
    outer_semi_axis : RayOcularField[Vector3[float]]
        Outer semi-axes of the iris.
    local_rotation : RayOcularField[Vector3[float]]
        Local rotation of the iris.
    local_scale : RayOcularField[Vector3[float]]
        Local scale of the iris.
    local_translation : RayOcularField[Vector3[float]]
        Local translation of the iris.
    thickness : RayOcularField[float]
        Thickness of the iris.
    """

    inner_semi_axis: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "IrisInnerSemiAxis")
    outer_semi_axis: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "IrisOuterSemiAxis")
    local_rotation: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "IrisLocalRotation")
    local_scale: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(validators.positive_float), "IrisLocalScale"
    )
    local_translation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "IrisLocalTranslation"
    )
    thickness: RayOcularField[float] = RayOcularField(validators.positive_float, "IrisThickness")


@dataclass
class Lens(BaseModel):
    """Store lens parameters for an eye model.

    Attributes
    ----------
    curvature : RayOcularField[float]
        Curvature of the lens.
    local_rotation : RayOcularField[Vector3[float]]
        Local rotation of the lens.
    local_scale : RayOcularField[Vector3[float]]
        Local scale of the lens.
    local_translation : RayOcularField[Vector3[float]]
        Local translation of the lens.
    semi_axis : RayOcularField[Vector3[float]]
        Semi-axes of the lens.
    """

    curvature: RayOcularField[float] = RayOcularField(float, "LensCurvature")
    local_rotation: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "LensLocalRotation")
    local_scale: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(validators.positive_float), "LensLocalScale"
    )
    local_translation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "LensLocalTranslation"
    )
    semi_axis: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "LensSemiAxis")


@dataclass
class Macula(BaseModel):
    """Store macula parameters for an eye model.

    Attributes
    ----------
    height : RayOcularField[float]
        Height of the macula.
    local_rotation : RayOcularField[Vector3[float]]
        Local rotation of the macula.
    local_scale : RayOcularField[Vector3[float]]
        Local scale of the macula.
    local_translation : RayOcularField[Vector3[float]]
        Local translation of the macula.
    rotation : RayOcularField[Vector3[float]]
        Rotation of the macula.
    semi_axis : RayOcularField[Vector3[float]]
        Semi-axes of the macula.
    """

    height: RayOcularField[float] = RayOcularField(validators.positive_float, "MaculaHeight")
    local_rotation: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "MaculaLocalRotation")
    local_scale: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(validators.positive_float), "MaculaLocalScale"
    )
    local_translation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "MaculaLocalTranslation"
    )
    rotation: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "MaculaRotation")
    semi_axis: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "MaculaSemiAxis")


@dataclass
class OpticalDisc(BaseModel):
    """Store optical disc parameters for an eye model.

    Attributes
    ----------
    height : RayOcularField[float]
        Height of the optical disc.
    local_rotation : RayOcularField[Vector3[float]]
        Local rotation of the optical disc.
    local_scale : RayOcularField[Vector3[float]]
        Local scale of the optical disc.
    local_translation : RayOcularField[Vector3[float]]
        Local translation of the optical disc.
    semi_axis : RayOcularField[Vector3[float]]
        Semi-axes of the optical disc.
    """

    height: RayOcularField[float] = RayOcularField(validators.positive_float, "OpticalDiscHeight")
    local_rotation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "OpticalDiscLocalRotation"
    )
    local_scale: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(validators.positive_float), "OpticalDiscLocalScale"
    )
    local_translation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "OpticalDiscLocalTranslation"
    )
    semi_axis: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "OpticalDiscSemiAxis")


@dataclass
class OpticalNerve(BaseModel):
    """Store optical nerve parameters for an eye model.

    Attributes
    ----------
    height : RayOcularField[float]
        Height of the optical nerve.
    local_rotation : RayOcularField[Vector3[float]]
        Local rotation of the optical nerve.
    local_scale : RayOcularField[Vector3[float]]
        Local scale of the optical nerve.
    local_translation : RayOcularField[Vector3[float]]
        Local translation of the optical nerve.
    rotation : RayOcularField[Vector3[float]]
        Rotation of the optical nerve.
    semi_axis : RayOcularField[Vector3[float]]
        Semi-axes of the optical nerve.
    """

    height: RayOcularField[float] = RayOcularField(validators.positive_float, "OpticalNerveHeight")
    local_rotation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "OpticalNerveLocalRotation"
    )
    local_scale: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(validators.positive_float), "OpticalNerveLocalScale"
    )
    local_translation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "OpticalNerveLocalTranslation"
    )
    rotation: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "OpticalNerveRotation")
    semi_axis: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "OpticalNerveSemiAxis")


@dataclass
class Retina(BaseModel):
    """Store retina parameters for an eye model.

    Attributes
    ----------
    thickness : RayOcularField[float]
        Thickness of the retina.
    local_rotation : RayOcularField[Vector3[float]]
        Local rotation of the retina.
    local_scale : RayOcularField[Vector3[float]]
        Local scale of the retina.
    local_translation : RayOcularField[Vector3[float]]
        Local translation of the retina.
    """

    thickness: RayOcularField[float] = RayOcularField(validators.positive_float, "RetinaThickness")
    local_rotation: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "RetinaLocalRotation")
    local_scale: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(validators.positive_float), "RetinaLocalScale"
    )
    local_translation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "RetinaLocalTranslation"
    )


@dataclass
class Sclera(BaseModel):
    """Store sclera parameters for an eye model.

    Attributes
    ----------
    thickness : RayOcularField[float]
        Thickness of the sclera.
    local_rotation : RayOcularField[Vector3[float]]
        Local rotation of the sclera.
    local_scale : RayOcularField[Vector3[float]]
        Local scale of the sclera.
    local_translation : RayOcularField[Vector3[float]]
        Local translation of the sclera.
    semi_axis : RayOcularField[Vector3[float]]
        Semi-axes of the sclera.
    """

    thickness: RayOcularField[float] = RayOcularField(validators.positive_float, "ScleraThickness")
    local_rotation: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "ScleraLocalRotation")
    local_scale: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(validators.positive_float), "ScleraLocalScale"
    )
    local_translation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "ScleraLocalTranslation"
    )
    semi_axis: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "ScleraSemiAxis")


@dataclass
class VitreousBody(BaseModel):
    """Store vitreous body parameters for an eye model.

    Attributes
    ----------
    local_rotation : RayOcularField[Vector3[float]]
        Local rotation of the vitreous body.
    local_scale : RayOcularField[Vector3[float]]
        Local scale of the vitreous body.
    local_translation : RayOcularField[Vector3[float]]
        Local translation of the vitreous body.
    """

    local_rotation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "VitreousBodyLocalRotation"
    )
    local_scale: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(validators.positive_float), "VitreousBodyLocalScale"
    )
    local_translation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "VitreousBodyLocalTranslation"
    )


@dataclass
class EyeModelParameters(BaseModel):
    """Store all parameters that define an eye model.

    Attributes
    ----------
    eye : ValidatedField[Eye]
        Eye positioning and scale parameters.
    anterior_chamber : ValidatedField[AnteriorChamber]
        Anterior chamber parameters.
    ciliary_body : ValidatedField[CiliaryBody]
        Ciliary body parameters.
    cornea : ValidatedField[Cornea]
        Cornea parameters.
    iris : ValidatedField[Iris]
        Iris parameters.
    lens : ValidatedField[Lens]
        Lens parameters.
    macula : ValidatedField[Macula]
        Macula parameters.
    optical_disc : ValidatedField[OpticalDisc]
        Optical disc parameters.
    optical_nerve : ValidatedField[OpticalNerve]
        Optical nerve parameters.
    retina : ValidatedField[Retina]
        Retina parameters.
    sclera : ValidatedField[Sclera]
        Sclera parameters.
    vitreous_body : ValidatedField[VitreousBody]
        Vitreous body parameters.
    lens_cornea_distance : ValidatedField[float]
        Distance from lens to cornea.
    level_of_detail : ValidatedField[int]
        Level of detail for geometry rendering.
    """

    eye: ValidatedField[Eye] = ValidatedField(validators.dataclass(Eye))
    anterior_chamber: ValidatedField[AnteriorChamber] = ValidatedField(validators.dataclass(AnteriorChamber))
    ciliary_body: ValidatedField[CiliaryBody] = ValidatedField(validators.dataclass(CiliaryBody))
    cornea: ValidatedField[Cornea] = ValidatedField(validators.dataclass(Cornea))
    iris: ValidatedField[Iris] = ValidatedField(validators.dataclass(Iris))
    lens: ValidatedField[Lens] = ValidatedField(validators.dataclass(Lens))
    macula: ValidatedField[Macula] = ValidatedField(validators.dataclass(Macula))
    optical_disc: ValidatedField[OpticalDisc] = ValidatedField(validators.dataclass(OpticalDisc))
    optical_nerve: ValidatedField[OpticalNerve] = ValidatedField(validators.dataclass(OpticalNerve))
    retina: ValidatedField[Retina] = ValidatedField(validators.dataclass(Retina))
    sclera: ValidatedField[Sclera] = ValidatedField(validators.dataclass(Sclera))
    vitreous_body: ValidatedField[VitreousBody] = ValidatedField(validators.dataclass(VitreousBody))

    lens_cornea_distance: ValidatedField[float] = ValidatedField(validators.positive_float)
    level_of_detail: ValidatedField[int] = ValidatedField(int)

    @classmethod
    def from_rayocular(cls, parameters) -> EyeModelParameters:
        """Create eye model parameters from a RayOcular object.

        Parameters
        ----------
        parameters : object
            The RayOcular eye model parameters object.

        Returns
        -------
        EyeModelParameters
            The created eye model parameters.
        """
        return cls(
            eye=Eye.from_rayocular(parameters),
            anterior_chamber=AnteriorChamber.from_rayocular(parameters),
            ciliary_body=CiliaryBody.from_rayocular(parameters),
            cornea=Cornea.from_rayocular(parameters),
            iris=Iris.from_rayocular(parameters),
            lens=Lens.from_rayocular(parameters),
            macula=Macula.from_rayocular(parameters),
            optical_disc=OpticalDisc.from_rayocular(parameters),
            optical_nerve=OpticalNerve.from_rayocular(parameters),
            retina=Retina.from_rayocular(parameters),
            sclera=Sclera.from_rayocular(parameters),
            vitreous_body=VitreousBody.from_rayocular(parameters),
            lens_cornea_distance=parameters.LensCorneaDistance,
            level_of_detail=parameters.LevelOfDetail,
        )

    def to_rayocular(self) -> dict[str, Any]:
        """Convert eye model parameters to a RayOcular dictionary.

        Returns
        -------
        dict[str, Any]
            A dictionary that can be used to update the model in RayOcular.
        """
        return {
            **self.eye.to_rayocular(),
            **self.anterior_chamber.to_rayocular(),
            **self.ciliary_body.to_rayocular(),
            **self.cornea.to_rayocular(),
            **self.iris.to_rayocular(),
            **self.lens.to_rayocular(),
            **self.macula.to_rayocular(),
            **self.optical_disc.to_rayocular(),
            **self.optical_nerve.to_rayocular(),
            **self.retina.to_rayocular(),
            **self.sclera.to_rayocular(),
            **self.vitreous_body.to_rayocular(),
            "LensCorneaDistance": self.lens_cornea_distance,
            "LevelOfDetail": self.level_of_detail,
        }


EyeLaterality = Literal["Left", "Right"]


@dataclass
class EyeModel(BaseModel):
    """Store a complete eye model with measurements and parameters.

    Attributes
    ----------
    measurements : ValidatedField[EyeModelMeasurements]
        Eye model measurements.
    parameters : ValidatedField[EyeModelParameters]
        Eye model parameters.
    laterality : RayOcularField[EyeLaterality]
        Eye laterality (Left or Right).
    description : RayOcularField[str]
        Description of the eye model.
    inter_pupillary_distance : RayOcularField[Optional[float]]
        Inter-pupillary distance.
    name : RayOcularField[str]
        Name of the eye model.
    """

    measurements: ValidatedField[EyeModelMeasurements] = ValidatedField(validators.dataclass(EyeModelMeasurements))
    parameters: ValidatedField[EyeModelParameters] = ValidatedField(validators.dataclass(EyeModelParameters))
    laterality: RayOcularField[EyeLaterality] = RayOcularField(validators.literal(EyeLaterality), "Laterality")

    description: RayOcularField[str] = RayOcularField(str, "Description", default="")
    inter_pupillary_distance: RayOcularField[Optional[float]] = RayOcularField(
        validators.optional(validators.positive_float), "InterPupillaryDistance", default=None
    )
    name: RayOcularField[str] = RayOcularField(str, "Name", default="Eye Model")

    @classmethod
    def from_rayocular(cls, geometry_generator) -> EyeModel:
        """Create an eye model from a RayOcular geometry generator.

        Parameters
        ----------
        geometry_generator : object
            The RayOcular geometry generator object.

        Returns
        -------
        EyeModel
            The created eye model.
        """
        measurements = geometry_generator.EyeModelMeasurements
        parameters = geometry_generator.EyeModelParameters

        return cls(
            description=geometry_generator.Description,
            inter_pupillary_distance=geometry_generator.InterPupillaryDistance,
            laterality=geometry_generator.Laterality,
            name=geometry_generator.Name,
            measurements=EyeModelMeasurements.from_rayocular(measurements),
            parameters=EyeModelParameters.from_rayocular(parameters),
        )

    def to_rayocular(self) -> dict[str, Any]:
        """Convert the eye model to a RayOcular dictionary.

        Raises
        ------
        NotImplementedError
            This method is not implemented for EyeModel.
        """
        raise NotImplementedError("to_rayocular is not implemented for EyeModel.")

    @classmethod
    def load_json(cls, file_path: PathLike | str) -> EyeModel:
        """Load an eye model from a JSON file.

        Parameters
        ----------
        file_path : PathLike | str
            Path to the JSON file.

        Returns
        -------
        EyeModel
            The loaded eye model.
        """
        file_path = Path(file_path)
        data = json.loads(file_path.read_text(encoding="utf-8"))

        return cls.from_dict(data)

    def save_json(self, file_path: PathLike | str) -> None:
        """Save the eye model to a JSON file.

        Parameters
        ----------
        file_path : PathLike | str
            Path where the JSON file will be saved.
        """
        file_path = Path(file_path)
        file_path.write_text(json.dumps(self.to_dict(), indent=4), encoding="utf-8")

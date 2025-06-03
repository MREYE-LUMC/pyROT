"""Data structures for interacting with RayOcular eye models."""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, fields, is_dataclass
from typing import Any, TypeVar

from pyrot.eye_modelling.datamodels import validators
from pyrot.eye_modelling.datamodels.validators import (
    RayOcularField,
    Vector3,
    rayocular_field,
)

logger = logging.getLogger(__name__)

_Self = TypeVar("_Self")


class BaseModel:
    """Abstract base class for RayOcular data models.

    Methods
    -------
    from_rayocular(cls, rayocular_object)
        Converts a RayOcular object to an instance of the data model.

    to_rayocular(self)
        Converts the data model instance to a RayOcular object.
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
        """Converts a RayOcular object to an instance of the data model.

        Parameters
        ----------
        rayocular_object : Any
            The RayOcular object to convert.

        Returns
        -------
        BaseModel
            An instance of the data model.
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
        """Converts the data model instance to a RayOcular dictionary.

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
            elif is_dataclass(value):
                rayocular_fields[field_value.rayocular_name] = asdict(value)
            else:
                rayocular_fields[field_value.rayocular_name] = value

        return rayocular_fields


@dataclass
class EyeModelMeasurements(BaseModel):
    cornea_lens_distance: float = rayocular_field(validators.positive_float, "CorneaLensDistance")
    eye_length: float = rayocular_field(validators.positive_float, "EyeLength")
    eye_width: float = rayocular_field(validators.positive_float, "EyeWidth")
    lens_thickness: float = rayocular_field(validators.positive_float, "LensThickness")
    limbus_diameter: float = rayocular_field(validators.positive_float, "LimbusDiameter")


@dataclass
class AnteriorChamber(BaseModel):
    local_rotation: Vector3[float] = rayocular_field(validators.vector3(float), "ChamberLocalRotation")
    local_scale: Vector3[float] = rayocular_field(validators.vector3(validators.positive_float), "ChamberLocalScale")
    local_translation: Vector3[float] = rayocular_field(validators.vector3(float), "ChamberLocalTranslation")


@dataclass
class CiliaryBody(BaseModel):
    base_curvature: float = rayocular_field(float, "CiliaryBodyBaseCurvature")
    height: float = rayocular_field(validators.positive_float, "CiliaryBodyHeight")
    local_rotation: Vector3[float] = rayocular_field(validators.vector3(float), "CiliaryBodyLocalRotation")
    local_scale: Vector3[float] = rayocular_field(
        validators.vector3(validators.positive_float), "CiliaryBodyLocalScale"
    )
    local_translation: Vector3[float] = rayocular_field(validators.vector3(float), "CiliaryBodyLocalTranslation")


@dataclass
class Cornea(BaseModel):
    local_rotation: Vector3[float] = rayocular_field(validators.vector3(float), "CorneaLocalRotation")
    local_scale: Vector3[float] = rayocular_field(validators.vector3(validators.positive_float), "CorneaLocalScale")
    local_translation: Vector3[float] = rayocular_field(validators.vector3(float), "CorneaLocalTranslation")
    semi_axis: Vector3[float] = rayocular_field(validators.vector3(float), "CorneaSemiAxis")
    thickness: float = rayocular_field(validators.positive_float, "CorneaThickness")


@dataclass
class Eye(BaseModel):
    pivot: Vector3[float] = rayocular_field(validators.vector3(float), "EyePivot")
    rotation: Vector3[float] = rayocular_field(validators.vector3(float), "EyeRotation")
    scale: Vector3[float] = rayocular_field(validators.vector3(validators.positive_float), "EyeScale")
    translation: Vector3[float] = rayocular_field(validators.vector3(float), "EyeTranslation")


@dataclass
class Iris(BaseModel):
    inner_semi_axis: Vector3[float] = rayocular_field(validators.vector3(float), "IrisInnerSemiAxis")
    outer_semi_axis: Vector3[float] = rayocular_field(validators.vector3(float), "IrisOuterSemiAxis")
    local_rotation: Vector3[float] = rayocular_field(validators.vector3(float), "IrisLocalRotation")
    local_scale: Vector3[float] = rayocular_field(validators.vector3(validators.positive_float), "IrisLocalScale")
    local_translation: Vector3[float] = rayocular_field(validators.vector3(float), "IrisLocalTranslation")
    thickness: float = rayocular_field(validators.positive_float, "IrisThickness")


@dataclass
class Lens(BaseModel):
    curvature: float = rayocular_field(float, "LensCurvature")
    local_rotation: Vector3[float] = rayocular_field(validators.vector3(float), "LensLocalRotation")
    local_scale: Vector3[float] = rayocular_field(validators.vector3(validators.positive_float), "LensLocalScale")
    local_translation: Vector3[float] = rayocular_field(validators.vector3(float), "LensLocalTranslation")
    semi_axis: Vector3[float] = rayocular_field(validators.vector3(float), "LensSemiAxis")


@dataclass
class Macula(BaseModel):
    height: float = rayocular_field(validators.positive_float, "MaculaHeight")
    local_rotation: Vector3[float] = rayocular_field(validators.vector3(float), "MaculaLocalRotation")
    local_scale: Vector3[float] = rayocular_field(validators.vector3(validators.positive_float), "MaculaLocalScale")
    local_translation: Vector3[float] = rayocular_field(validators.vector3(float), "MaculaLocalTranslation")
    rotation: Vector3[float] = rayocular_field(validators.vector3(float), "MaculaRotation")
    semi_axis: Vector3[float] = rayocular_field(validators.vector3(float), "MaculaSemiAxis")


@dataclass
class OpticalDisc(BaseModel):
    height: float = rayocular_field(validators.positive_float, "OpticalDiscHeight")
    local_rotation: Vector3[float] = rayocular_field(validators.vector3(float), "OpticalDiscLocalRotation")
    local_scale: Vector3[float] = rayocular_field(
        validators.vector3(validators.positive_float), "OpticalDiscLocalScale"
    )
    local_translation: Vector3[float] = rayocular_field(validators.vector3(float), "OpticalDiscLocalTranslation")
    semi_axis: Vector3[float] = rayocular_field(validators.vector3(float), "OpticalDiscSemiAxis")


@dataclass
class OpticalNerve(BaseModel):
    height: float = rayocular_field(validators.positive_float, "OpticalNerveHeight")
    local_rotation: Vector3[float] = rayocular_field(validators.vector3(float), "OpticalNerveLocalRotation")
    local_scale: Vector3[float] = rayocular_field(
        validators.vector3(validators.positive_float), "OpticalNerveLocalScale"
    )
    local_translation: Vector3[float] = rayocular_field(validators.vector3(float), "OpticalNerveLocalTranslation")
    rotation: Vector3[float] = rayocular_field(validators.vector3(float), "OpticalNerveRotation")
    semi_axis: Vector3[float] = rayocular_field(validators.vector3(float), "OpticalNerveSemiAxis")


@dataclass
class Retina(BaseModel):
    thickness: float = rayocular_field(validators.positive_float, "RetinaThickness")
    local_rotation: Vector3[float] = rayocular_field(validators.vector3(float), "RetinaLocalRotation")
    local_scale: Vector3[float] = rayocular_field(validators.vector3(validators.positive_float), "RetinaLocalScale")
    local_translation: Vector3[float] = rayocular_field(validators.vector3(float), "RetinaLocalTranslation")


@dataclass
class Sclera(BaseModel):
    thickness: float = rayocular_field(validators.positive_float, "ScleraThickness")
    local_rotation: Vector3[float] = rayocular_field(validators.vector3(float), "ScleraLocalRotation")
    local_scale: Vector3[float] = rayocular_field(validators.vector3(validators.positive_float), "ScleraLocalScale")
    local_translation: Vector3[float] = rayocular_field(validators.vector3(float), "ScleraLocalTranslation")
    semi_axis: Vector3[float] = rayocular_field(validators.vector3(float), "ScleraSemiAxis")


@dataclass
class VitreousBody(BaseModel):
    local_rotation: Vector3[float] = rayocular_field(validators.vector3(float), "VitreousBodyLocalRotation")
    local_scale: Vector3[float] = rayocular_field(
        validators.vector3(validators.positive_float), "VitreousBodyLocalScale"
    )
    local_translation: Vector3[float] = rayocular_field(validators.vector3(float), "VitreousBodyLocalTranslation")


@dataclass
class EyeModelParameters:
    eye: Eye = rayocular_field(validators.dataclass(Eye))
    anterior_chamber: AnteriorChamber = rayocular_field(validators.dataclass(AnteriorChamber))
    ciliary_body: CiliaryBody = rayocular_field(validators.dataclass(CiliaryBody))
    cornea: Cornea = rayocular_field(validators.dataclass(Cornea))
    iris: Iris = rayocular_field(validators.dataclass(Iris))
    lens: Lens = rayocular_field(validators.dataclass(Lens))
    macula: Macula = rayocular_field(validators.dataclass(Macula))
    optical_disc: OpticalDisc = rayocular_field(validators.dataclass(OpticalDisc))
    optical_nerve: OpticalNerve = rayocular_field(validators.dataclass(OpticalNerve))
    retina: Retina = rayocular_field(validators.dataclass(Retina))
    sclera: Sclera = rayocular_field(validators.dataclass(Sclera))
    vitreous_body: VitreousBody = rayocular_field(validators.dataclass(VitreousBody))

    lens_cornea_distance: float = rayocular_field(validators.positive_float)
    level_of_detail: int = rayocular_field(int)

    @classmethod
    def from_rayocular(cls, parameters) -> EyeModelParameters:
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


@dataclass
class EyeModel:
    measurements: EyeModelMeasurements = rayocular_field(validators.dataclass(EyeModelMeasurements))
    parameters: EyeModelParameters = rayocular_field(validators.dataclass(EyeModelParameters))

    @classmethod
    def from_rayocular(cls, geometry_generator) -> EyeModel:
        measurements = geometry_generator.EyeModelMeasurements
        parameters = geometry_generator.EyeModelParameters

        return cls(
            measurements=EyeModelMeasurements.from_rayocular(measurements),
            parameters=EyeModelParameters.from_rayocular(parameters),
        )

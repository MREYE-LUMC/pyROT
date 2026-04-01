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

    def to_dict(self) -> dict[str, Any]:
        """Converts the data model instance to a dictionary.

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
        """Creates an instance of the data model from a dictionary.

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
        """
        if not is_dataclass(cls):
            raise NotImplementedError("from_dict is only implemented for dataclasses.")

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
    cornea_lens_distance: RayOcularField[float] = RayOcularField(validators.positive_float, "CorneaLensDistance")
    eye_length: RayOcularField[float] = RayOcularField(validators.positive_float, "EyeLength")
    eye_width: RayOcularField[float] = RayOcularField(validators.positive_float, "EyeWidth")
    lens_thickness: RayOcularField[float] = RayOcularField(validators.positive_float, "LensThickness")
    limbus_diameter: RayOcularField[float] = RayOcularField(validators.positive_float, "LimbusDiameter")


@dataclass
class AnteriorChamber(BaseModel):
    local_rotation: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "ChamberLocalRotation")
    local_scale: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(validators.positive_float), "ChamberLocalScale"
    )
    local_translation: RayOcularField[Vector3[float]] = RayOcularField(
        validators.vector3(float), "ChamberLocalTranslation"
    )


@dataclass
class CiliaryBody(BaseModel):
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
    pivot: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "EyePivot")
    rotation: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "EyeRotation")
    scale: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(validators.positive_float), "EyeScale")
    translation: RayOcularField[Vector3[float]] = RayOcularField(validators.vector3(float), "EyeTranslation")


@dataclass
class Iris(BaseModel):
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


EyeLaterality = Literal["Left", "Right"]


@dataclass
class EyeModel(BaseModel):
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
        raise NotImplementedError("to_rayocular is not implemented for EyeModel.")

    @classmethod
    def load_json(cls, file_path: PathLike | str) -> EyeModel:
        file_path = Path(file_path)
        data = json.loads(file_path.read_text(encoding="utf-8"))

        return cls.from_dict(data)

    def save_json(self, file_path: PathLike | str) -> None:
        file_path = Path(file_path)
        file_path.write_text(json.dumps(self.to_dict(), indent=4), encoding="utf-8")

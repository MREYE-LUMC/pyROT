"""Data validation and field descriptors for pyROT data models."""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Callable, Generic, Mapping, Sequence, TypeVar

__all__ = ["Vector3", "dataclass", "positive_float", "rayocular_field", "vector3"]

Instance = TypeVar("Instance")
Value = TypeVar("Value")

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised when a validation error occurs."""

    def __init__(self, value: Any, field_name: str) -> None:
        self.message = f"Failed to validate {value=} for field {field_name}."
        super().__init__(self.message)


class RayOcularField(Generic[Instance, Value]):
    """A descriptor class that provides validation for a field.

    Parameters
    ----------
    validator : Callable[[Any], Value]
        A callable object that performs the validation.

    Attributes
    ----------
    public_name : str
        The public name of the field.
    private_name : str
        The private name of the field.

    Methods
    -------
    __get__(self, instance: Instance, owner: type[Instance] | None = None) -> Value:
        Retrieves the value of the field.

    __set__(self, instance: Instance, value: Value):
        Sets the value of the field after validating it.

    validate(self, value):
        Validates the given value using the provided validator.

    Raises
    ------
    ValueError
        If the validation fails.

    Notes
    -----
    Define a `ValidatedField` descriptor for a class attribute and provide a validator function.
    The validator function should take a single argument and return the validated value.

    Examples
    --------
    >>> class Person:
    ...     age = ValidatedField(int)
    ...
    ...     def __init__(self, age):
    ...         self.age = age
    """

    def __init__(self, validator: Callable[[Any], Value], name: str | None) -> None:
        self.rayocular_name = name
        self.validator = validator

    def __set_name__(self, owner: Instance, name: str):
        self.public_name = name
        self.private_name = "_" + name

    def __get__(self, instance: Instance, owner: type[Instance] | None = None) -> Value:
        return getattr(instance, self.private_name)

    def __set__(self, instance: Instance, value: Value):
        setattr(instance, self.private_name, self.validate(value))

    def validate(self, value):
        """Validates the given value using the provided validator.

        Parameters
        ----------
        value : Any
            The value to be validated.

        Returns
        -------
        Value
            The validated value.

        Raises
        ------
        ValueError
            If the validation fails.
        """
        try:
            return self.validator(value)
        except ValueError as e:
            raise ValidationError(value, self.public_name) from e


# Factory function to create a validated field.
# This is needed to make type checkers accept validated fields for type-annotated fields.
def rayocular_field(validator: Callable[[Any], Value], name: str | None = None) -> Value:
    """Creates a validated field with the given validator.

    Parameters
    ----------
    name : str
        The RayOcular name of the field.
    validator : Callable[[Any], Value]
        A callable object that takes any value as input and returns a validated value.

    Returns
    -------
    ValidatedField[Instance, Value]
        The validated field.
    """
    return RayOcularField(validator, name)  # type: ignore


def dataclass(cls: type[Value]) -> Callable[..., Value]:
    def validate(value) -> Value:
        if isinstance(value, cls):
            return value

        if isinstance(value, dict):
            return cls(**value)

        raise ValueError(f"Could not parse {value=} to type {cls.__name__}.")

    return validate


def positive_float(value: Any) -> float:
    if isinstance(value, float) and value >= 0:
        return value

    raise ValueError(f"Expected positive float, got {value}.")


# Use a dataclass because of JSON serialization
@dataclasses.dataclass(frozen=True)
class Vector3(Generic[Value]):
    x: Value
    y: Value
    z: Value


Item = TypeVar("Item")


def vector3(
    item_validator: Callable[..., Item],
) -> Callable[[Any], Vector3[Item]]:
    def validate(value: Any) -> Vector3[Item]:
        if isinstance(value, Vector3):
            return value
        if isinstance(value, Sequence):  # list-like values
            if not len(value) == 3:  # noqa: PLR2004
                raise ValueError(f"Vector should have 3 elements, got {len(value)}.")

            return Vector3(*[item_validator(v) for v in value])
        if isinstance(value, Mapping):  # dict-like values
            if not len(value) == 3:  # noqa: PLR2004
                raise ValueError(f"Vector should have 3 elements, got {len(value)}.")

            return Vector3(**{k: item_validator(v) for (k, v) in value.items()})

        raise ValueError(f"Could not parse {value=} to Vector3. `value` should be Vector3, list or dict.")

    return validate

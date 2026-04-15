"""Data validation and field descriptors for pyROT data models."""

from __future__ import annotations

import dataclasses
import logging
from typing import Any, Callable, Generic, Mapping, Sequence, TypeVar, get_args

__all__ = [
    "RayOcularField",
    "ValidationError",
    "Vector3",
    "dataclass",
    "literal",
    "optional",
    "positive_float",
    "vector3",
]

Value = TypeVar("Value")

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Exception raised when a validation error occurs."""

    def __init__(self, value: Any, field_name: str) -> None:
        self.message = f"Failed to validate {value=} for field {field_name}."
        super().__init__(self.message)


class ValidatedField(Generic[Value]):
    """A descriptor class that provides validation for a field.

    Parameters
    ----------
    validator : Callable[[Any], Value]
        A callable object that performs the validation.
    default : Value, optional
        The default value for the field. If not provided, the field will be required and must be set explicitly.

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

    def __init__(self, validator: Callable[[Any], Value], *, default: Value = ...) -> None:
        self.validator = validator
        self._default = default

    def __set_name__(self, owner, name: str):
        self.public_name = name
        self.private_name = "_" + name

    def __get__(self, instance, owner: type | None = None) -> Value:
        if instance is None and self._default is not ...:
            return self._default

        return getattr(instance, self.private_name)

    def __set__(self, instance, value: Value) -> None:
        setattr(instance, self.private_name, self.validate(value))

    def validate(self, value: Value) -> Value:
        """Validate the given value using the provided validator.

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
        ValidationError
            If the validation fails.
        """
        try:
            return self.validator(value)
        except ValueError as e:
            raise ValidationError(value, self.public_name) from e


class RayOcularField(ValidatedField[Value]):
    """A descriptor class that provides validation for a RayOcular field.

    Parameters
    ----------
    validator : Callable[[Any], Value]
        A callable object that performs the validation.
    name : str
        The RayOcular name of the field. This is used for serialization and deserialization to RayOcular.
    default : Value, optional
        The default value for the field. If not provided, the field will be required and must be set explicitly.

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

    def __init__(self, validator: Callable[[Any], Value], name: str, *, default: Value = ...) -> None:
        self.rayocular_name = name
        self.validator = validator
        self._default = default


T = TypeVar("T")


def dataclass(cls: type[T]) -> Callable[..., T]:
    """Validate dataclasses.

    Checks if the value is an instance of the dataclass or a dict that can be used to create an instance of the dataclass.

    Parameters
    ----------
    cls : type[T]
        The dataclass type to validate against.

    Returns
    -------
    Callable[..., T]
        A validator function that can be used to validate instances of the dataclass.
    """

    def validate(value) -> T:
        """Validate a value as an instance of the dataclass.

        Parameters
        ----------
        value : Any
            The value to validate.

        Returns
        -------
        T
            The validated dataclass instance.

        Raises
        ------
        ValueError
            If the value is not an instance of the dataclass or a dict that can be used to create an instance of the dataclass.
        """
        if isinstance(value, cls):
            return value

        if isinstance(value, dict):
            return cls(**value)

        raise ValueError(f"Could not parse {value=} to type {cls.__name__}.")

    return validate


def positive_float(value: Any) -> float:
    """Validate positive floats.

    Parameters
    ----------
    value : Any
        The value to validate.

    Returns
    -------
    float
        The validated positive float value.

    Raises
    ------
    ValueError
        If the value is not a positive float.
    """
    if isinstance(value, float) and value >= 0:
        return value

    raise ValueError(f"Expected positive float, got {value}.")


# Use a dataclass because of JSON serialization
@dataclasses.dataclass(frozen=True)
class Vector3(Generic[T]):
    """Three-dimensional vector with components of a given type.

    Attributes
    ----------
    x : T
        X component of the vector.
    y : T
        Y component of the vector.
    z : T
        Z component of the vector.
    """

    x: T
    y: T
    z: T


def vector3(
    item_validator: Callable[..., T],
) -> Callable[[Any], Vector3[T]]:
    """Validate Vector3 objects.

    Parameters
    ----------
    item_validator : Callable[..., T]
        A validator function for the individual components of the vector.

    Returns
    -------
    Callable[[Any], Vector3[T]]
        A validator function that can be used to validate Vector3 objects.
    """

    def validate(value: Any) -> Vector3[T]:
        """Validate a value as a Vector3 object.

        Parameters
        ----------
        value : Any
            The value to validate as a Vector3.

        Returns
        -------
        Vector3[T]
            The validated Vector3 object.

        Raises
        ------
        ValueError
            If the value is not a valid Vector3 object.
        """
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


def literal(type_: type[T]) -> Callable[[Any], T]:
    """Validate literal values.

    Parameters
    ----------
    type_ : type[T]
        The type containing the allowed literal values.

    Returns
    -------
    Callable[[Any], T]
        A validator function that can be used to validate literal values.
    """

    def validate(value: Any) -> T:
        allowed = get_args(type_)
        if value in allowed:
            return value

        raise ValueError(f"Expected one of {allowed}, got {value}.")

    return validate


def optional(inner: Callable[..., T]) -> Callable[[Any], T | None]:
    """Validate optional values.

    Parameters
    ----------
    inner : Callable[..., T]
        The validator function for the non-optional value.

    Returns
    -------
    Callable[[Any], T | None]
        A validator function to validate optional values.
    """

    def validate(value: Any) -> T | None:
        if value is None:
            return None

        return inner(value)

    return validate

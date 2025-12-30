"""
Dataclass Serialization Mixin

Provides automatic to_dict() implementation for dataclasses that handles:
- Enum values (converts to .value)
- datetime objects (converts to .isoformat())
- Nested dataclasses (recursively calls to_dict())
- Lists/dicts containing dataclasses
- Optional computed properties to include
"""

from dataclasses import fields, is_dataclass
from datetime import datetime, date
from enum import Enum
from typing import Any, Dict, List, Set


class DataclassMixin:
    """
    Mixin that provides automatic to_dict() for dataclasses.

    Usage:
        @dataclass
        class MyClass(DataclassMixin):
            name: str
            status: MyEnum
            created_at: datetime

        # Optionally include computed properties:
        @dataclass
        class MyClassWithProps(DataclassMixin):
            _include_properties: ClassVar[Set[str]] = {"computed_value"}

            @property
            def computed_value(self) -> int:
                return 42
    """

    # Override in subclass to include computed properties in to_dict()
    _include_properties: Set[str] = set()

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to dictionary with proper serialization."""
        result = {}

        # Serialize all dataclass fields
        for f in fields(self):
            value = getattr(self, f.name)
            result[f.name] = self._serialize_value(value)

        # Include specified computed properties
        include_props = getattr(self.__class__, '_include_properties', set())
        for prop_name in include_props:
            if hasattr(self, prop_name):
                value = getattr(self, prop_name)
                result[prop_name] = self._serialize_value(value)

        return result

    @staticmethod
    def _serialize_value(value: Any) -> Any:
        """Recursively serialize a value to JSON-compatible format."""
        if value is None:
            return None

        # Handle Enums
        if isinstance(value, Enum):
            return value.value

        # Handle datetime/date
        if isinstance(value, (datetime, date)):
            return value.isoformat()

        # Handle dataclasses with to_dict method
        if hasattr(value, 'to_dict') and callable(value.to_dict):
            return value.to_dict()

        # Handle dataclasses without to_dict (use recursion)
        if is_dataclass(value) and not isinstance(value, type):
            result = {}
            for f in fields(value):
                field_value = getattr(value, f.name)
                result[f.name] = DataclassMixin._serialize_value(field_value)
            return result

        # Handle lists
        if isinstance(value, list):
            return [DataclassMixin._serialize_value(item) for item in value]

        # Handle dicts
        if isinstance(value, dict):
            return {
                k: DataclassMixin._serialize_value(v)
                for k, v in value.items()
            }

        # Handle sets (convert to list)
        if isinstance(value, set):
            return [DataclassMixin._serialize_value(item) for item in value]

        # Return primitive values as-is
        return value

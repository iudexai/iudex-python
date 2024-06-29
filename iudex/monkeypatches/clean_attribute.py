import logging
from typing import Optional, Sequence

import opentelemetry.attributes
from opentelemetry.attributes import _clean_attribute_value
from opentelemetry.util import types

logger = logging.getLogger(__name__)


_VALID_ATTR_VALUE_TYPES = (bool, str, bytes, int, float)


def patched_clean_attribute(
    key: str, value: types.AttributeValue, max_len: Optional[int]
) -> Optional[types.AttributeValue]:
    """Checks if attribute value is valid and cleans it if required.

    The function returns the cleaned value or None if the value is not valid.

    An attribute value is valid if it is either:
        - A primitive type: string, boolean, double precision floating
            point (IEEE 754-1985) or integer.
        - An array of primitive type values. The array MUST be homogeneous,
            i.e. it MUST NOT contain values of different types.

    An attribute needs cleansing if:
        - Its length is greater than the maximum allowed length.
        - It needs to be encoded/decoded e.g, bytes to strings.
    """

    if not (key and isinstance(key, str)):
        logger.warning("invalid key `%s`. must be non-empty string.", key)
        return None

    if isinstance(value, _VALID_ATTR_VALUE_TYPES):
        return _clean_attribute_value(value, max_len)

    if isinstance(value, Sequence):
        sequence_first_valid_type = None
        cleaned_seq = []

        for element in value:
            element = _clean_attribute_value(element, max_len)
            if element is None:
                cleaned_seq.append(element)
                continue

            element_type = type(element)
            # Reject attribute value if sequence contains a value with an incompatible type.
            if element_type not in _VALID_ATTR_VALUE_TYPES:
                logger.warning(
                    "Invalid type %s in attribute '%s' value sequence. Expected one of "
                    "%s or None",
                    element_type.__name__,
                    key,
                    [valid_type.__name__ for valid_type in _VALID_ATTR_VALUE_TYPES],
                )
                return None

            # The type of the sequence must be homogeneous. The first non-None
            # element determines the type of the sequence
            if sequence_first_valid_type is None:
                sequence_first_valid_type = element_type
            # use equality instead of isinstance as isinstance(True, int) evaluates to True
            elif element_type != sequence_first_valid_type:
                logger.warning(
                    "Attribute %r mixes types %s and %s in attribute value sequence",
                    key,
                    sequence_first_valid_type.__name__,
                    type(element).__name__,
                )
                return None

            cleaned_seq.append(element)

        # Freeze mutable sequences defensively
        return tuple(cleaned_seq)

    # Fall back to stringify (dict, error, etc.)
    # Rather than warning and returning None as before
    return _clean_attribute_value(str(value), max_len)


def monkeypatch_clean_attribute():
    opentelemetry.attributes._clean_attribute = patched_clean_attribute

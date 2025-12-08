from __future__ import annotations
import typing
import re
from .pymodels import StrFuncParams


def extract_middle_name(input: str | None,
                        params: StrFuncParams):
    """
    Args:
        input: full name string
        params.delimiter: character(s) separating name parts (space)
        params.position: which part to extract (0=first, 1=middle, 2=last)
        params.default: value to return if position doesn't exist
    Returns:
        Extracted name part or default
    """
    if not input:
        return default
    parts = str(input).split(params.delimiter)
    if len(parts) > params.position:
        return parts[params.position]
    return params.default


def strip_pattern(input: str | None,
                  params: StrFuncParams):
    """
    Args:
        value: string to process
        pattern: regex pattern to match and remove
        replacement: string to replace matches with (default empty)
        flags: regex flags (0=none, re.IGNORECASE=2, etc)
    Returns:
        String with pattern removed
    """
    if not value or not pattern:
        return value
    return re.sub(pattern, replacement, str(value), flags=flags)


def normalize_case(value, case_type="sentence", 
                   exceptions=None):
    """
    Args:
        value: string to normalize
        case_type: one of 'upper', 'lower', 'title', 'sentence'
        exceptions: list of words to preserve capitalization 
                   (e.g., ['NOS', 'NEC'] for diagnosis)
    Returns:
        Normalized string
    """
    if not value:
        return value

    exceptions = exceptions or []
    value_str = str(value)

    if case_type == "upper":
        return value_str.upper()
    elif case_type == "lower":
        return value_str.lower()
    elif case_type == "title":
        return value_str.title()
    elif case_type == "sentence":
        words = value_str.split()
        result = []
        for i, word in enumerate(words):
            # Check if word or its core (without punctuation) 
            # is in exceptions
            word_core = word.rstrip('.,;:!?')
            if word_core.upper() in [e.upper() for e in exceptions]:
                result.append(word_core.upper())
            elif i == 0:
                result.append(word.capitalize())
            else:
                result.append(word.lower())
        return " ".join(result)
    return value_str


def split(input: str, params: StrFuncParams) -> list:
    return input.split(sep=params.delimiter)


def add_prefix(input: str, params: StrFuncParams) -> str:
    return params.prefix + input


def render_template(input: List(str), params: StrFuncParams) -> str:

def concat_fields(values, delimiter="_", prefix="", suffix="", 
                  skip_null=True):
    """
    Args:
        values: list/tuple of values to concatenate
        delimiter: string joining values
        prefix: prepend to result
        suffix: append to result
        skip_null: if True, skip None/empty values
    Returns:
        Concatenated string
    """
    if not isinstance(values, (list, tuple)):
        values = [values]

    if skip_null:
        clean_values = [str(v) for v in values 
                       if v is not None and str(v).strip()]
    else:
        clean_values = [str(v) if v is not None else "" 
                       for v in values]

    result = delimiter.join(clean_values)
    if prefix:
        result = f"{prefix}{result}"
    if suffix:
        result = f"{result}{suffix}"
    return result

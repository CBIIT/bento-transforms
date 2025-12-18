from __future__ import annotations
from .pymodels import (
    D2YParams,
    Y2DParams,
)


def days_to_years(input: int | float | None,
                  params: dict) -> int | None:
    """
    Args:
        input: numeric value in days
        params.divisor: conversion factor (default 365 for days->years)
        params.precision: decimal places to round to
        params.sentinel: value representing missing/invalid data
    Returns:
        Converted value or None if sentinel detected
    """
    params = D2YParams(**params)
    if input == params.sentinel or input is None:
        return None
    return round(input / params.divisor, params.precision)


def years_to_days(input: int | float | None,
                  params: dict) -> int:
    """
    Args:
        input: numeric value in years
        params.multiplier: conversion factor (default 365)
        params.sentinel_if_null: value to return if input is None
    Returns:
        Converted value in days, or sentinel if input None
    """
    params = Y2DParams(**params)
    if input is None:
        return params.sentinel_if_null
    return round(input * params.multiplier)

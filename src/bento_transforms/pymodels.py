from __future__ import annotations
from typing import Pattern
from pydantic import BaseModel
from enum import Enum


class UuidNSEnum(str, Enum):
    DNS = 'dns'
    URL = 'url'
    OID = 'oid'
    X500 = 'x500'


class D2YParams(BaseModel):
    divisor: float = 365.0
    precision: int = 2
    sentinel: int = -999


class Y2DParams(BaseModel):
    multiplier: int = 365
    sentinel_if_null: int = -999


class UuidNS(BaseModel):
    namespace: UuidNSEnum = UuidNSEnum.DNS


class StrFuncParams(BaseModel):
    prefix: str | None = None
    suffix: str | None  = None
    delimiter: str = " "
    position: int = 1
    pattern: Pattern | None = None
    replacement: str | None = None
    flags: int = 0
    default: str | None = None
    skip_null: bool = False
    

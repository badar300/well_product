"""Shared enums for units and extra-cost kinds."""

from enum import StrEnum


class Unit(StrEnum):
    PCS = "PCS"
    MTR = "MTR"
    KGS = "KGS"
    CON = "CON"
    NO = "NO"


class ExtraCostKind(StrEnum):
    LOGISTIC = "logistic"
    OTHER = "other"


class MaterialCategory(StrEnum):
    FABRIC = "fabric"
    ACCESSORY = "accessory"
    PACKAGING = "packaging"
    SPECIAL_OPERATION = "special_operation"
    LABOUR = "labour"


class CostingMode(StrEnum):
    FULL = "full"
    CMT = "cmt"


class ProductImageKind(StrEnum):
    FRONT = "front"
    BACK = "back"
    EXTRA = "extra"

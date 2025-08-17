from __future__ import annotations
from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field, conint, constr


# ---------- CSV SCHEMA (v1 minimal spec) ----------

CsvPrimitiveType = Literal[
    "string",
    "integer",
    "number",
    "boolean",
    "date",
    "datetime",
    "uuid",
    "enum",
]

class CsvColumn(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)  # type: ignore
    type: CsvPrimitiveType
    enumValues: Optional[List[str]] = None
    min: Optional[float] = None
    max: Optional[float] = None
    pattern: Optional[str] = None
    nullProb: Optional[float] = Field(default=0.0, ge=0.0, le=1.0)
    unique: Optional[bool] = False

class CsvSchema(BaseModel):
    columns: List[CsvColumn]
    rows: conint(ge=1) = 1  # type: ignore
    delimiter: str = ","
    header: bool = True
    encoding: str = "utf-8"
    constraints: Optional[Dict[str, Any]] = None  # future: unique/composite/foreign


# ---------- XML SCHEMA (v1 minimal spec) ----------

XmlPrimitiveType = Literal[
    "string",
    "integer",
    "number",
    "boolean",
    "date",
    "datetime",
    "uuid",
    "enum",
    "object",
    "array",
]

class XmlAttribute(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)  # type: ignore
    type: XmlPrimitiveType = "string"
    required: bool = False

class XmlElement(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)  # type: ignore
    type: XmlPrimitiveType = "object"
    attributes: Optional[List[XmlAttribute]] = None
    children: Optional[List["XmlElement"]] = None
    enumValues: Optional[List[str]] = None
    minOccurs: Optional[int] = 0
    maxOccurs: Optional[int] = 1
    textPattern: Optional[str] = None

class XmlSchema(BaseModel):
    root: constr(strip_whitespace=True, min_length=1)  # type: ignore
    elements: List[XmlElement]
    namespaces: Optional[Dict[str, str]] = None
    xsdUrl: Optional[str] = None  # placeholder for future XSD ingestion

XmlElement.update_forward_refs()

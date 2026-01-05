from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict
from enum import Enum


class SampleType(str, Enum):
    SEDIMENT = "SEDIMENT"
    WATER_QUALITY = "WATER_QUALITY"


class WaterLayer(str, Enum):
    SURFACE = "SURFACE"
    MIDDLE = "MIDDLE"
    BOTTOM = "BOTTOM"


class SampleBase(BaseModel):
    sample_type: Optional[str] = None
    water_layer: Optional[str] = None
    region: Optional[str] = None
    station: Optional[str] = None
    source_file: Optional[str] = None
    data: Optional[Dict[str, Any]] = None


class SampleResponse(SampleBase):
    id: str = Field(..., alias="_id")
    
    class Config:
        populate_by_name = True


class SamplesListResponse(BaseModel):
    total: int
    limit: int
    skip: int
    data: List[Dict[str, Any]]


class RegionsResponse(BaseModel):
    regions: List[str]
    count: int


class StationsResponse(BaseModel):
    stations: List[str]
    count: int


class StatisticsResponse(BaseModel):
    total_samples: int
    sample_types: Dict[str, int]
    water_layers: Dict[str, int]
    regions: Dict[str, int]
    date_range: Optional[Dict[str, str]] = None


class HealthResponse(BaseModel):
    status: str
    database: str
    message: str


# ==============================
# EAI MODELS
# ==============================
class EAIScoreItem(BaseModel):
    date: Optional[str] = None
    station: str
    region: str
    sample_type: str
    water_layer: str
    eai: Optional[float] = None
    status: str
    status_label: Dict[str, str]
    sub_indices: Dict[str, Optional[float]]


class EAIResponse(BaseModel):
    total: int
    limit: int
    skip: int
    average_eai: Optional[float] = None
    status_distribution: Dict[str, int]
    eai_scores: List[Dict[str, Any]]

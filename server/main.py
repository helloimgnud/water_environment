from fastapi import FastAPI, Query, HTTPException, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from typing import Optional, List, Dict, Any
from bson import ObjectId
from pydantic import BaseModel
import io
import csv

from database import Database, get_samples_collection
from models import (
    SamplesListResponse,
    RegionsResponse,
    StationsResponse,
    StatisticsResponse,
    HealthResponse,
    EAIResponse,
    SampleType,
    WaterLayer
)
from eai_calculator import calculate_sample_eai, get_status_label


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - connect/disconnect from MongoDB"""
    await Database.connect()
    yield
    await Database.disconnect()


app = FastAPI(
    title="Marine Environment API",
    description="API to query marine environment sample data from Hong Kong waters",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==============================
# HEALTH CHECK
# ==============================
@app.get("/", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Check API and database health"""
    try:
        await Database.client.admin.command('ping')
        return HealthResponse(
            status="healthy",
            database="connected",
            message="Marine Environment API is running"
        )
    except Exception as e:
        return HealthResponse(
            status="unhealthy",
            database="disconnected",
            message=str(e)
        )


# ==============================
# SAMPLES ENDPOINTS
# ==============================
@app.get("/samples", response_model=SamplesListResponse, tags=["Samples"])
async def get_samples(
    sample_type: Optional[SampleType] = Query(None, description="Filter by sample type"),
    water_layer: Optional[WaterLayer] = Query(None, description="Filter by water layer"),
    region: Optional[str] = Query(None, description="Filter by region name"),
    station: Optional[str] = Query(None, description="Filter by station ID"),
    start_date: Optional[str] = Query(None, description="Filter by start date (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="Filter by end date (YYYY-MM-DD)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of results to return"),
    skip: int = Query(0, ge=0, description="Number of results to skip")
):
    """Query samples with optional filters and pagination."""
    collection = get_samples_collection()
    
    query = {}
    if sample_type:
        query["sample_type"] = sample_type.value
    if water_layer:
        query["water_layer"] = water_layer.value
    if region:
        query["region"] = {"$regex": region, "$options": "i"}
    if station:
        query["station"] = {"$regex": station, "$options": "i"}
    
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            query["data.thoi_gian"] = date_filter
    
    total = await collection.count_documents(query)
    cursor = collection.find(query).skip(skip).limit(limit)
    samples = []
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        samples.append(doc)
    
    return SamplesListResponse(total=total, limit=limit, skip=skip, data=samples)


@app.get("/samples/{sample_id}", tags=["Samples"])
async def get_sample_by_id(sample_id: str):
    """Get a single sample by its MongoDB ObjectId"""
    collection = get_samples_collection()
    
    try:
        doc = await collection.find_one({"_id": ObjectId(sample_id)})
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid sample ID format")
    
    if not doc:
        raise HTTPException(status_code=404, detail="Sample not found")
    
    doc["_id"] = str(doc["_id"])
    return doc


# ==============================
# EAI ENDPOINT
# ==============================
@app.get("/eai", response_model=EAIResponse, tags=["EAI"])
async def get_eai_scores(
    sample_type: Optional[SampleType] = Query(None, description="Filter by sample type"),
    water_layer: Optional[WaterLayer] = Query(None, description="Filter by water layer"),
    region: Optional[str] = Query(None, description="Filter by region name"),
    station: Optional[str] = Query(None, description="Filter by station ID"),
    start_date: Optional[str] = Query(None, description="Filter by start date"),
    end_date: Optional[str] = Query(None, description="Filter by end date"),
    limit: int = Query(500, ge=1, le=5000, description="Number of results"),
    skip: int = Query(0, ge=0, description="Number of results to skip")
):
    """
    Calculate EAI (Environmental Alert Index) for samples.
    
    Returns EAI scores with sub-indices for each parameter.
    - EAI 80-100: Good (Tốt) - Safe environment
    - EAI 50-79: Warning (Cảnh cáo) - Needs monitoring
    - EAI <50: Bad (Xấu) - Urgent alert
    """
    collection = get_samples_collection()
    
    query = {}
    if sample_type:
        query["sample_type"] = sample_type.value
    if water_layer:
        query["water_layer"] = water_layer.value
    if region:
        query["region"] = {"$regex": region, "$options": "i"}
    if station:
        query["station"] = {"$regex": station, "$options": "i"}
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        if date_filter:
            query["data.thoi_gian"] = date_filter
    
    total = await collection.count_documents(query)
    cursor = collection.find(query).skip(skip).limit(limit)
    
    eai_scores = []
    status_count = {"good": 0, "warning": 0, "bad": 0, "unknown": 0}
    total_eai = 0
    valid_eai_count = 0
    
    async for doc in cursor:
        data = doc.get("data", {})
        eai_result = calculate_sample_eai(data)
        
        score_item = {
            "id": str(doc["_id"]),
            "date": data.get("thoi_gian"),
            "station": doc.get("station"),
            "region": doc.get("region"),
            "sample_type": doc.get("sample_type"),
            "water_layer": doc.get("water_layer"),
            "eai": eai_result["eai"],
            "status": eai_result["status"],
            "status_label": get_status_label(eai_result["status"]),
            "sub_indices": eai_result["sub_indices"]
        }
        
        eai_scores.append(score_item)
        status_count[eai_result["status"]] += 1
        
        if eai_result["eai"] is not None:
            total_eai += eai_result["eai"]
            valid_eai_count += 1
    
    avg_eai = round(total_eai / valid_eai_count, 2) if valid_eai_count > 0 else None
    
    return EAIResponse(
        total=total,
        limit=limit,
        skip=skip,
        average_eai=avg_eai,
        status_distribution=status_count,
        eai_scores=eai_scores
    )


# ==============================
# EAI CALCULATOR ENDPOINTS
# ==============================
class CalculateEAIRequest(BaseModel):
    sample_type: str
    data: Dict[str, Any]


@app.post("/calculate-eai", tags=["Calculator"])
async def calculate_eai_manual(request: CalculateEAIRequest):
    """
    Calculate EAI from manually entered parameters.
    
    - For WATER_QUALITY: ph, do_man, nhiet_do_nuoc, nh3, tss, bod5
    - For SEDIMENT: as, cd, pb, cu, zn
    """
    eai_result = calculate_sample_eai(request.data)
    return {
        "sample_type": request.sample_type,
        "eai": eai_result["eai"],
        "status": eai_result["status"],
        "status_label": get_status_label(eai_result["status"]),
        "sub_indices": eai_result["sub_indices"]
    }


@app.post("/calculate-eai-csv", tags=["Calculator"])
async def calculate_eai_from_csv(
    file: UploadFile = File(...),
    sample_type: str = Form(...)
):
    """Calculate EAI for multiple records from a CSV file."""
    try:
        contents = await file.read()
        decoded = contents.decode('utf-8')
        reader = csv.DictReader(io.StringIO(decoded))
        
        results = []
        status_summary = {"good": 0, "warning": 0, "bad": 0, "unknown": 0}
        
        for row in reader:
            data = {}
            for key, value in row.items():
                try:
                    data[key.strip().lower()] = float(value) if value else None
                except (ValueError, TypeError):
                    data[key.strip().lower()] = value
            
            eai_result = calculate_sample_eai(data)
            results.append({
                "eai": eai_result["eai"],
                "status": eai_result["status"],
                "status_label": get_status_label(eai_result["status"]),
                "sub_indices": eai_result["sub_indices"]
            })
            status_summary[eai_result["status"]] += 1
        
        return {
            "sample_type": sample_type,
            "total": len(results),
            "results": results,
            "summary": status_summary
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error processing CSV: {str(e)}")


# ==============================
# REGIONS ENDPOINT
# ==============================
@app.get("/regions", response_model=RegionsResponse, tags=["Metadata"])
async def get_regions():
    """Get all unique regions in the dataset"""
    collection = get_samples_collection()
    regions = await collection.distinct("region")
    regions = sorted([r for r in regions if r])
    return RegionsResponse(regions=regions, count=len(regions))


# ==============================
# STATIONS ENDPOINT
# ==============================
@app.get("/stations", response_model=StationsResponse, tags=["Metadata"])
async def get_stations(
    region: Optional[str] = Query(None, description="Filter stations by region")
):
    """Get all unique stations, optionally filtered by region"""
    collection = get_samples_collection()
    
    query = {}
    if region:
        query["region"] = {"$regex": region, "$options": "i"}
    
    pipeline = [
        {"$match": query} if query else {"$match": {}},
        {"$group": {"_id": "$station"}},
        {"$sort": {"_id": 1}}
    ]
    
    cursor = collection.aggregate(pipeline)
    stations = [doc["_id"] async for doc in cursor if doc["_id"]]
    return StationsResponse(stations=stations, count=len(stations))


# ==============================
# STATISTICS ENDPOINT
# ==============================
@app.get("/statistics", response_model=StatisticsResponse, tags=["Analytics"])
async def get_statistics(
    region: Optional[str] = Query(None, description="Filter by region"),
    station: Optional[str] = Query(None, description="Filter by station")
):
    """Get aggregated statistics for the dataset"""
    collection = get_samples_collection()
    
    query = {}
    if region:
        query["region"] = {"$regex": region, "$options": "i"}
    if station:
        query["station"] = {"$regex": station, "$options": "i"}
    
    total = await collection.count_documents(query)
    
    sample_type_pipeline = [
        {"$match": query} if query else {"$match": {}},
        {"$group": {"_id": "$sample_type", "count": {"$sum": 1}}}
    ]
    sample_types = {}
    async for doc in collection.aggregate(sample_type_pipeline):
        if doc["_id"]:
            sample_types[doc["_id"]] = doc["count"]
    
    water_layer_pipeline = [
        {"$match": query} if query else {"$match": {}},
        {"$group": {"_id": "$water_layer", "count": {"$sum": 1}}}
    ]
    water_layers = {}
    async for doc in collection.aggregate(water_layer_pipeline):
        if doc["_id"]:
            water_layers[doc["_id"]] = doc["count"]
    
    region_pipeline = [
        {"$match": query} if query else {"$match": {}},
        {"$group": {"_id": "$region", "count": {"$sum": 1}}}
    ]
    regions = {}
    async for doc in collection.aggregate(region_pipeline):
        if doc["_id"]:
            regions[doc["_id"]] = doc["count"]
    
    return StatisticsResponse(
        total_samples=total,
        sample_types=sample_types,
        water_layers=water_layers,
        regions=regions
    )


# ==============================
# PREDICTION ENDPOINTS
# ==============================
import os

# Type indicator mapping
TYPE_INDICATOR_MAP = {
    "SEDIMENT": "Sediment",
    "WATER_QUALITY_SURFACE": "Water_Surface",
    "WATER_QUALITY_MIDDLE": "Water_Middle",
    "WATER_QUALITY_BOTTOM": "Water_Bottom"
}

# Models directory - check Docker path first, then fallback to relative path
_docker_models_path = "/app/models"
_dev_models_path = os.path.join(os.path.dirname(__file__), "..", "models")
MODELS_BASE_DIR = _docker_models_path if os.path.exists(_docker_models_path) else _dev_models_path


@app.get("/prediction/types", tags=["Prediction"])
async def get_prediction_types():
    """Get available prediction types based on existing model folders"""
    types = []
    if os.path.exists(os.path.join(MODELS_BASE_DIR, "prophet_models_sediment")):
        types.append({"id": "SEDIMENT", "label": "Sediment"})
    if os.path.exists(os.path.join(MODELS_BASE_DIR, "prophet_models_water_surface")):
        types.append({"id": "WATER_QUALITY_SURFACE", "label": "Water Quality (Surface)"})
    if os.path.exists(os.path.join(MODELS_BASE_DIR, "prophet_models_water_middle")):
        types.append({"id": "WATER_QUALITY_MIDDLE", "label": "Water Quality (Middle)"})
    if os.path.exists(os.path.join(MODELS_BASE_DIR, "prophet_models_water_bottom")):
        types.append({"id": "WATER_QUALITY_BOTTOM", "label": "Water Quality (Bottom)"})
    return {"types": types}


@app.get("/prediction/areas", tags=["Prediction"])
async def get_prediction_areas(type_indicator: str = Query(..., description="Prediction type")):
    """Get available areas for a given prediction type"""
    type_name = TYPE_INDICATOR_MAP.get(type_indicator)
    if not type_name:
        raise HTTPException(status_code=400, detail="Invalid type_indicator")
    
    if type_name == "Sediment":
        folder = "prophet_models_sediment"
    else:
        folder = f"prophet_models_{type_name.lower()}"
    
    folder_path = os.path.join(MODELS_BASE_DIR, folder)
    if not os.path.exists(folder_path):
        return {"areas": []}
    
    areas = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    return {"areas": sorted(areas)}


@app.get("/prediction/stations", tags=["Prediction"])
async def get_prediction_stations(
    type_indicator: str = Query(..., description="Prediction type"),
    area: str = Query(..., description="Area name")
):
    """Get available stations for a given area"""
    type_name = TYPE_INDICATOR_MAP.get(type_indicator)
    if not type_name:
        raise HTTPException(status_code=400, detail="Invalid type_indicator")
    
    if type_name == "Sediment":
        folder = "prophet_models_sediment"
    else:
        folder = f"prophet_models_{type_name.lower()}"
    
    folder_path = os.path.join(MODELS_BASE_DIR, folder, area)
    if not os.path.exists(folder_path):
        return {"stations": []}
    
    stations = [f for f in os.listdir(folder_path) if os.path.isdir(os.path.join(folder_path, f))]
    return {"stations": sorted(stations)}


@app.get("/prediction/historical", tags=["Prediction"])
async def get_historical_eai(
    region: str = Query(..., description="Region name"),
    station: str = Query(..., description="Station ID"),
    sample_type: Optional[str] = Query(None, description="Sample type filter"),
    water_layer: Optional[str] = Query(None, description="Water layer filter")
):
    """Get historical EAI data for a station to display in chart"""
    collection = get_samples_collection()
    
    query = {
        "region": {"$regex": region, "$options": "i"},
        "station": {"$regex": station, "$options": "i"}
    }
    if sample_type:
        query["sample_type"] = sample_type
    if water_layer:
        query["water_layer"] = water_layer
    
    cursor = collection.find(query).sort("data.thoi_gian", 1).limit(500)
    
    historical_data = []
    async for doc in cursor:
        data = doc.get("data", {})
        eai_result = calculate_sample_eai(data)
        if eai_result["eai"] is not None:
            historical_data.append({
                "date": data.get("thoi_gian"),
                "eai": eai_result["eai"],
                "status": eai_result["status"],
                "is_prediction": False
            })
    
    return {"historical": historical_data}


class PredictionRequest(BaseModel):
    type_indicator: str
    area: str
    station: str


@app.post("/prediction/forecast", tags=["Prediction"])
async def generate_forecast(request: PredictionRequest):
    """Generate 12-month EAI forecast using Prophet models"""
    try:
        # Import inference module
        from inference import get_forecast_df
        
        # Map type indicator
        type_name = TYPE_INDICATOR_MAP.get(request.type_indicator)
        if not type_name:
            raise HTTPException(status_code=400, detail="Invalid type_indicator")
        
        # Get forecast dataframe
        df = get_forecast_df(type_name, request.area, request.station)
        
        # Convert to dict and calculate EAI for each row
        predictions = []
        for _, row in df.iterrows():
            # Convert row to dict for EAI calculation
            data = {col: row[col] for col in df.columns if col != 'thoi_gian' and row[col] is not None}
            
            # Calculate EAI from predicted parameters
            eai_result = calculate_sample_eai(data)
            
            predictions.append({
                "date": row["thoi_gian"],
                "eai": eai_result["eai"],
                "status": eai_result["status"],
                "status_label": get_status_label(eai_result["status"]),
                "sub_indices": eai_result["sub_indices"],
                "is_prediction": True
            })
        
        return {
            "type_indicator": request.type_indicator,
            "area": request.area,
            "station": request.station,
            "predictions": predictions
        }
    
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


# ==============================
# RUN SERVER
# ==============================
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)


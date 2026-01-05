"""
EAI (Environmental Alert Index) Calculator

Formulas:
- Step 1: Sub-Index Qi (0-100 scale)
  - Type 1 "Optimal in middle" (pH, salinity, temp): Qi = 100 × exp(-(x-c)²/(2σ²))
  - Type 2 "Lower is better" (NH3, TSS, BOD, metals): Qi = 100 × (1 - x/max)
  
- Step 2: EAI (Weighted Geometric Mean): EAI = exp(Σ wi · ln(Qi + 1))

Classification:
- 80-100: Good (Tốt) - Safe environment
- 50-79: Warning (Cảnh cáo) - Needs monitoring  
- <50: Bad (Xấu) - Urgent alert
"""

import math
from typing import Dict, List, Optional, Tuple

# ==============================
# PARAMETER THRESHOLDS
# ==============================

# Type 1: Optimal in middle (Gaussian distribution)
# Format: (min_value, max_value) - center and sigma will be calculated
OPTIMAL_MIDDLE_PARAMS = {
    "ph": (6.5, 8.5),           # pH optimal range
    "do_man": (10.0, 35.0),     # Salinity (ppt)
    "nhiet_do_nuoc": (20.0, 30.0),  # Water temperature (°C)
}

# Type 2: Lower is better (linear decrease)
# Format: max_acceptable_value
LOWER_BETTER_PARAMS = {
    # Water quality parameters
    "nh3": 2.0,       # Ammonia (mg/L)
    "tss": 50.0,      # Total Suspended Solids (mg/L)
    "bod5": 5.0,      # BOD5 (mg/L)
    
    # Heavy metals (sediment, mg/kg)
    "as": 20.0,       # Arsenic
    "cd": 1.5,        # Cadmium
    "pb": 60.0,       # Lead
    "cu": 65.0,       # Copper
    "zn": 200.0,      # Zinc
}

# Weights for each parameter (should sum to 1.0 per category)
PARAM_WEIGHTS = {
    # Water quality weights
    "ph": 0.15,
    "do_man": 0.10,
    "nhiet_do_nuoc": 0.10,
    "nh3": 0.20,
    "tss": 0.15,
    "bod5": 0.15,
    "do_sau": 0.05,
    
    # Sediment weights (heavy metals)
    "as": 0.20,
    "cd": 0.25,
    "pb": 0.20,
    "cu": 0.18,
    "zn": 0.17,
}


# ==============================
# SUB-INDEX CALCULATIONS
# ==============================

def calculate_qi_optimal_middle(value: float, min_val: float, max_val: float) -> float:
    """
    Calculate sub-index for 'optimal in middle' parameters.
    Qi = 100 × exp(-(x - c)² / (2σ²))
    where c = (min + max) / 2, σ = (max - min) / 4
    """
    if value is None:
        return None
    
    c = (min_val + max_val) / 2
    sigma = (max_val - min_val) / 4
    
    if sigma == 0:
        return 100.0 if value == c else 0.0
    
    qi = 100 * math.exp(-((value - c) ** 2) / (2 * sigma ** 2))
    return max(0.0, min(100.0, qi))


def calculate_qi_lower_better(value: float, max_val: float) -> float:
    """
    Calculate sub-index for 'lower is better' parameters.
    Qi = 100 × (1 - x / max)
    """
    if value is None or max_val == 0:
        return None
    
    qi = 100 * (1 - value / max_val)
    return max(0.0, min(100.0, qi))


# ==============================
# EAI CALCULATION
# ==============================

def calculate_eai(sub_indices: Dict[str, float], weights: Dict[str, float] = None) -> Tuple[float, str]:
    """
    Calculate EAI using Weighted Geometric Mean.
    EAI = exp(Σ wi · ln(Qi + 1))
    
    Returns: (eai_score, status)
    """
    if weights is None:
        weights = PARAM_WEIGHTS
    
    # Filter out None values
    valid_indices = {k: v for k, v in sub_indices.items() if v is not None}
    
    if not valid_indices:
        return None, "unknown"
    
    # Normalize weights for available parameters
    available_weights = {k: weights.get(k, 0.1) for k in valid_indices.keys()}
    total_weight = sum(available_weights.values())
    
    if total_weight == 0:
        return None, "unknown"
    
    normalized_weights = {k: v / total_weight for k, v in available_weights.items()}
    
    # Calculate weighted geometric mean
    weighted_sum = 0.0
    for param, qi in valid_indices.items():
        w = normalized_weights.get(param, 0)
        weighted_sum += w * math.log(qi + 1)
    
    eai = math.exp(weighted_sum)
    
    # Classify status
    if eai >= 80:
        status = "good"
    elif eai >= 50:
        status = "warning"
    else:
        status = "bad"
    
    return round(eai, 2), status


def calculate_sample_eai(data: Dict) -> Dict:
    """
    Calculate EAI for a single sample data record.
    
    Args:
        data: Sample data dictionary with parameter values
        
    Returns:
        Dictionary with eai, status, and sub_indices
    """
    sub_indices = {}
    
    # Calculate sub-indices for 'optimal in middle' parameters
    for param, (min_val, max_val) in OPTIMAL_MIDDLE_PARAMS.items():
        if param in data and data[param] is not None:
            try:
                value = float(data[param])
                sub_indices[param] = calculate_qi_optimal_middle(value, min_val, max_val)
            except (ValueError, TypeError):
                pass
    
    # Calculate sub-indices for 'lower is better' parameters
    for param, max_val in LOWER_BETTER_PARAMS.items():
        if param in data and data[param] is not None:
            try:
                value = float(data[param])
                sub_indices[param] = calculate_qi_lower_better(value, max_val)
            except (ValueError, TypeError):
                pass
    
    # Calculate final EAI
    eai, status = calculate_eai(sub_indices)
    
    return {
        "eai": eai,
        "status": status,
        "sub_indices": {k: round(v, 2) if v else None for k, v in sub_indices.items()}
    }


def get_status_label(status: str) -> Dict[str, str]:
    """Get Vietnamese and English labels for status"""
    labels = {
        "good": {"vi": "Tốt", "en": "Good", "color": "#22c55e"},
        "warning": {"vi": "Cảnh cáo", "en": "Warning", "color": "#eab308"},
        "bad": {"vi": "Xấu", "en": "Bad", "color": "#ef4444"},
        "unknown": {"vi": "Không xác định", "en": "Unknown", "color": "#6b7280"},
    }
    return labels.get(status, labels["unknown"])

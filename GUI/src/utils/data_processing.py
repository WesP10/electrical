"""Data processing utilities."""
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import sys
from pathlib import Path
# Use PYTHONPATH for imports
from config.log_config import get_logger

logger = get_logger(__name__)


def clean_sensor_data(data: pd.DataFrame, max_age_seconds: int = 300) -> pd.DataFrame:
    """Clean sensor data by removing old entries and invalid values."""
    if data.empty:
        return data
    
    try:
        # Remove old data
        if 'Time' in data.columns:
            cutoff_time = datetime.now() - timedelta(seconds=max_age_seconds)
            data = data[data['Time'] >= cutoff_time]
        
        # Remove invalid values (NaN, inf)
        data = data.replace([float('inf'), float('-inf')], pd.NA).dropna()
        
        return data
        
    except Exception as e:
        logger.error(f"Error cleaning sensor data: {e}")
        return pd.DataFrame()


def aggregate_sensor_data(data: pd.DataFrame, window_size: int = 10) -> Dict[str, float]:
    """Aggregate sensor data to get current statistics."""
    if data.empty:
        return {}
    
    try:
        stats = {}
        numeric_columns = data.select_dtypes(include=['number']).columns
        
        for column in numeric_columns:
            if column != 'Time':
                recent_data = data[column].tail(window_size)
                stats[f"{column}_current"] = recent_data.iloc[-1] if not recent_data.empty else 0
                stats[f"{column}_avg"] = recent_data.mean()
                stats[f"{column}_min"] = recent_data.min()
                stats[f"{column}_max"] = recent_data.max()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error aggregating sensor data: {e}")
        return {}


def format_sensor_value(value: float, precision: int = 2, unit: str = "") -> str:
    """Format a sensor value for display."""
    try:
        if pd.isna(value):
            return "N/A"
        
        formatted = f"{value:.{precision}f}"
        if unit:
            formatted += f" {unit}"
        
        return formatted
        
    except Exception as e:
        logger.error(f"Error formatting sensor value: {e}")
        return "Error"


def validate_sensor_data(data: Dict[str, Any]) -> bool:
    """Validate sensor data structure."""
    try:
        # Check required fields
        if 'Time' not in data:
            return False
        
        # Check if Time is valid
        if not isinstance(data['Time'], datetime):
            return False
        
        # Check if other values are numeric
        for key, value in data.items():
            if key != 'Time':
                try:
                    float(value)
                except (ValueError, TypeError):
                    return False
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating sensor data: {e}")
        return False

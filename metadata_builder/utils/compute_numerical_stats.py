import logging
import pandas as pd
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

def compute_numerical_stats(df: pd.DataFrame, numerical_columns: List[str]) -> Dict[str, Dict[str, float]]:
    """
    Compute statistical metrics for numerical columns.
    
    Args:
        df: DataFrame with the data
        numerical_columns: List of numerical column names
        
    Returns:
        Dictionary mapping column names to their statistics
    """
    stats = {}
    for col in numerical_columns:
        logger.info(f'Identifying numerical range for {col}')
        if col not in df.columns:
            logger.warning(f"Column {col} not found in DataFrame")
            continue
        try:
            numeric_series = pd.to_numeric(df[col], errors='coerce')
            col_stats = {
                'min': numeric_series.min(),
                'p25': numeric_series.quantile(0.25),
                'p50': numeric_series.quantile(0.50),
                'p75': numeric_series.quantile(0.75),
                'max': numeric_series.max()
            }
            stats[col] = col_stats
        except Exception as e:
            logger.error(f"Error computing stats for column {col}: {str(e)}")
            stats[col] = {'error': str(e)}
    return stats 
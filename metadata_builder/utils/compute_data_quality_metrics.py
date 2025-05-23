import pandas as pd
from typing import Dict, Any

def compute_data_quality_metrics(df: pd.DataFrame, schema: Dict[str, str]) -> Dict[str, Any]:
    """
    Compute simplified data quality metrics for a table.
    
    Args:
        df: DataFrame containing the data
        schema: Dictionary mapping column names to their data types
        
    Returns:
        Dictionary with data quality metrics for each column
    """
    metrics = {}
    total_rows = len(df)
    
    for col, dtype in schema.items():
        metrics[col] = {
            "completeness": round(df[col].notnull().mean() * 100, 2),
            "uniqueness": round((df[col].nunique() / total_rows * 100), 2),
            "common_issues": [],
            "recommendations": [],
            "data_type": dtype
        }
        
        # Identify issues and make recommendations
        completeness = metrics[col]["completeness"]
        uniqueness = metrics[col]["uniqueness"]
        
        if completeness < 90:
            metrics[col]["common_issues"].append("High percentage of missing values")
            metrics[col]["recommendations"].append("Investigate source of missing values")
            
        if uniqueness == 100 and total_rows > 100:
            metrics[col]["common_issues"].append("Potentially unique identifier")
            metrics[col]["recommendations"].append("Verify if column should be unique")
            
        if uniqueness < 1 and total_rows > 100:
            metrics[col]["common_issues"].append("Very low cardinality")
            metrics[col]["recommendations"].append("Verify if low variation is expected")
    
    return metrics 
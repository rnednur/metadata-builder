import logging
import pandas as pd
from typing import Dict, List, Tuple, Any

logger = logging.getLogger(__name__)

def identify_column_types(schema: Dict[str, str], df: pd.DataFrame) -> Tuple[List[str], List[str]]:
    """
    Identify categorical and numerical columns
    
    Args:
        schema: Dictionary mapping column names to their data types
        df: DataFrame with sample data
        
    Returns:
        Tuple with lists of categorical and numerical column names
    """
    categorical = []
    numerical = []
    
    for column, dtype in schema.items():
        try:
            # First check if it's explicitly a numeric type in the schema
            if any(num_type in dtype.lower() for num_type in ['int', 'float', 'double', 'decimal', 'numeric']):
                numerical.append(column)
                logger.debug(f"Column '{column}' identified as numerical based on schema dtype: {dtype}")
                continue

            # For other types, check the actual data
            sample = df[column].dropna().head(100)  # Take a sample for efficiency
            
            # Skip empty columns
            if len(sample) == 0:
                categorical.append(column)
                logger.debug(f"Column '{column}' identified as categorical (empty column)")
                continue

            # Check if the column contains lists
            if sample.apply(lambda x: isinstance(x, list)).any():
                categorical.append(column)
                logger.debug(f"Column '{column}' identified as categorical (contains lists)")
                continue

            # Try to convert to numeric, if it fails, it's categorical
            try:
                # If conversion succeeds, check uniqueness ratio
                unique_ratio = df[column].nunique() / len(df)
                if unique_ratio <= 0.03:  # 3% threshold for categorical
                    categorical.append(column)
                    logger.debug(f"Column '{column}' identified as categorical based on uniqueness ratio: {unique_ratio:.4f}")
                else:
                    pd.to_numeric(sample, errors='raise')
                    numerical.append(column)
                    logger.debug(f"Column '{column}' identified as numerical based on uniqueness ratio: {unique_ratio:.4f}")
            except (ValueError, TypeError):
                #categorical.append(column)
                logger.debug(f"Column '{column}' identified as categorical (non-numeric values)")

        except Exception as e:
            logger.warning(f"Error processing column '{column}': {str(e)}. Treating as categorical.")
            categorical.append(column)

    logger.info(f"Identified {len(categorical)} categorical columns and {len(numerical)} numerical columns")
    logger.debug(f"Categorical columns: {categorical}")
    logger.debug(f"Numerical columns: {numerical}")
    
    return categorical, numerical 
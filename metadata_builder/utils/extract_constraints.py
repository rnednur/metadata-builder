from typing import Dict, Any

def extract_constraints(table_name: str, db_name: str) -> Dict[str, Any]:
    """
    Extract database constraints for a table.
    
    Args:
        table_name: Name of the table
        db_name: Database name
        
    Returns:
        Dictionary with constraint information
    """
    from .database_handler import SQLAlchemyHandler  # Import here to avoid circular imports
    
    db = SQLAlchemyHandler(db_name)
    try:
        constraints = {
            'primary_keys': db.get_primary_keys(table_name),
            'foreign_keys': [],  # This will be populated based on database handler capabilities
            'unique_constraints': []  # This will be populated based on database handler capabilities
        }

        # Additional constraint extraction can be implemented in specific database handlers
        if hasattr(db, 'get_foreign_keys'):
            constraints['foreign_keys'] = db.get_foreign_keys(table_name)
        if hasattr(db, 'get_unique_constraints'):
            constraints['unique_constraints'] = db.get_unique_constraints(table_name)

        return constraints
    finally:
        db.close() 
import pandas as pd
from typing import List

class Validator:
    """
    Validates that the standardized DataFrame complies strictly with the Web of Science schema.
    
    This acts as the final gatekeeper in the ETL pipeline. It ensures that 
    the transformed DataFrame possesses all required columns, does not contain
    null values, and adheres strictly to the predefined Type Contracts (e.g., lists 
    for multi-value fields, integers for years/citations).
    """
    
    STANDARD_COLUMNS = [
        "DB", "UT", "DI", "PMID", "TI", "SO", "JI", "PY", "DT", "LA", "TC", 
        "AU", "AF", "C1", "RP", "CR", "DE", "ID", "AB", "VL", "IS", "BP", "EP", "SR"
    ]
    
    LIST_COLUMNS = ["AU", "AF", "C1", "CR", "DE", "ID"]
    INTEGER_COLUMNS = ["TC", "PY"]

    @classmethod
    def validate(cls, df: pd.DataFrame) -> bool:
        """
        Executes strict validation checks on the standardized DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame processed by the Standardizer.

        Returns:
            bool: True if the DataFrame passes all validation checks.

        Raises:
            ValueError: If the DataFrame is empty, is missing mandatory columns, 
                        contains null values, or violates Type Contracts.
        """
        if df.empty:
            raise ValueError("Validation Error: DataFrame is empty.")
            
        # 1. Check Mandatory Columns
        missing_cols = [col for col in cls.STANDARD_COLUMNS if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Validation Error: Missing mandatory columns: {missing_cols}")
            
        # 2. Check for Nulls (NaN or None)
        null_counts = df.isnull().sum()
        if null_counts.sum() > 0:
            raise ValueError(f"Validation Error: DataFrame contains null values:\n{null_counts[null_counts > 0]}")
            
        # 3. Check Data Types
        for col in cls.STANDARD_COLUMNS:
            sample_val = df[col].iloc[0] if not df.empty else None
            if col in cls.LIST_COLUMNS:
                if not df[col].apply(lambda x: isinstance(x, list)).all():
                    raise ValueError(f"Validation Error: Column '{col}' must be a list of strings.")
            elif col in cls.INTEGER_COLUMNS:
                if not pd.api.types.is_integer_dtype(df[col]) and not df[col].apply(lambda x: isinstance(x, int)).all():
                    # Check if all can be cast to int, but standardizer should have enforced it
                    try:
                        df[col].astype(int)
                    except ValueError:
                        raise ValueError(f"Validation Error: Column '{col}' must contain integers.")
            else:
                if not pd.api.types.is_string_dtype(df[col]) and not df[col].apply(lambda x: isinstance(x, str)).all():
                    raise ValueError(f"Validation Error: Column '{col}' must contain strings.")
                    
        return True

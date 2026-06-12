import pandas as pd
from typing import List, Dict, Any, Union

class Standardizer:
    """
    Standardizes bibliographic data from heterogeneous sources to the Web of Science (WoS) schema.
    
    This class implements the Lookup Strategy pattern via a predefined MAPPING dictionary 
    to translate proprietary column names (e.g., OpenAlex's 'referenced_works') into 
    standardized WoS tags (e.g., 'CR'). It also enforces Type Contracts, ensuring 
    that all output data adheres to expected types (e.g., lists of strings for authors, 
    integers for years) and gracefully handles null values.
    """
    
    # WoS Standard Schema
    STANDARD_COLUMNS = [
        "DB", "UT", "DI", "PMID", "TI", "SO", "JI", "PY", "DT", "LA", "TC", 
        "AU", "AF", "C1", "RP", "CR", "DE", "ID", "AB", "VL", "IS", "BP", "EP", "SR"
    ]
    
    LIST_COLUMNS = ["AU", "AF", "C1", "CR", "DE", "ID"]
    INTEGER_COLUMNS = ["TC", "PY"]
    
    # Mapping Dictionary (Lookup Strategy)
    # Maps proprietary column names to WoS tags.
    # Extend this as needed for Scopus, Dimensions, etc.
    MAPPING = {
        # OpenAlex Mapping
        "id": "UT",
        "doi": "DI",
        "title": "TI",
        "publication_year": "PY",
        "type": "DT",
        "language": "LA",
        "cited_by_count": "TC",
        "referenced_works": "CR",
        # PubMed Mapping
        "uid": "PMID",
        # "title" is already mapped above to "TI"
        "source": "SO",
        "pubdate": "PY",
        "pubtype": "DT",
        "lang": "LA",
        "pmc": "UT",
        "volume": "VL",
        "issue": "IS",
        "pages": "BP",
        # Scopus Mapping
        "Authors": "AU",
        "Author(s) ID": "AF",
        "Title": "TI",
        "Year": "PY",
        "Source title": "SO",
        "Volume": "VL",
        "Issue": "IS",
        "Page start": "BP",
        "Page end": "EP",
        "Cited by": "TC",
        "DOI": "DI",
        "Document Type": "DT",
        "Source": "DB",
        "Affiliations": "C1",
        "Author Keywords": "DE",
        "Index Keywords": "ID",
        "Abstract": "AB",
        # Dimensions Mapping
        "Publication ID": "UT",
        "PubYear": "PY",
        "Journal": "SO",
        "Times cited": "TC",
    }
    
    @staticmethod
    def _parse_multi_value(val: Any, delimiter: str = ";") -> List[str]:
        """Parses a multi-value string or list into a list of strings."""
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return []
        if isinstance(val, list):
            return [str(v).strip() for v in val if v is not None and not (isinstance(v, float) and pd.isna(v))]
        if isinstance(val, str):
            if val.strip() == "":
                return []
            return [v.strip() for v in val.split(delimiter) if v.strip()]
        return [str(val).strip()]

    @staticmethod
    def _parse_scalar_str(val: Any) -> str:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return ""
        if isinstance(val, list):
            return str(val[0]) if len(val) > 0 else ""
        return str(val).strip()
        
    @staticmethod
    def _parse_scalar_int(val: Any) -> Union[int, str]:
        if val is None or (isinstance(val, float) and pd.isna(val)):
            return 0
        if isinstance(val, list):
            val = val[0] if len(val) > 0 else 0
        try:
            # Handle float values like 2024.0 or strings like "2024"
            if isinstance(val, str):
                import re
                match = re.search(r'\d{4}', val)
                if match:
                    return int(match.group())
            return int(float(val))
        except (ValueError, TypeError):
            return 0

    @classmethod
    def apply_mapping_and_types(cls, data: Union[pd.DataFrame, List[Dict[str, Any]]], db_source: str) -> pd.DataFrame:
        """
        Main method to standardize the input data.

        Executes the standardization pipeline:
        1. Translates columns using the MAPPING dictionary.
        2. Ensures all standard WoS columns are present.
        3. Extracts nested JSON fields for specific APIs (like OpenAlex/PubMed).
        4. Enforces strict type contracts via parsing methods.

        Args:
            data (Union[pd.DataFrame, List[Dict[str, Any]]]): The raw data fetched from an API or file.
            db_source (str): The source identifier (e.g., "OPENALEX", "PUBMED", "SCOPUS").

        Returns:
            pd.DataFrame: A normalized DataFrame strictly conforming to the WoS schema.
        """
        if isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            df = data.copy()
            
        # 1. Rename columns using mapping
        df.rename(columns=cls.MAPPING, inplace=True)
        
        # 2. Ensure all standard columns exist
        for col in cls.STANDARD_COLUMNS:
            if col not in df.columns:
                df[col] = None
                
        # 3. Explicitly set DB if not present
        df["DB"] = db_source.upper()
        
        # Extract features from nested JSON for OpenAlex and PubMed if needed
        # OpenAlex authors
        if db_source.upper() == "OPENALEX":
            if "authorships" in df.columns:
                df["AU"] = df["authorships"].apply(
                    lambda x: [author.get("author", {}).get("display_name", "") for author in x] if isinstance(x, list) else []
                )
                df["C1"] = df["authorships"].apply(
                    lambda x: [inst.get("display_name", "") for author in x for inst in author.get("institutions", [])] if isinstance(x, list) else []
                )
            if "host_venue" in df.columns: # Older API format
                df["SO"] = df["host_venue"].apply(lambda x: x.get("display_name", "") if isinstance(x, dict) else "")
            elif "primary_location" in df.columns: # Newer API format
                df["SO"] = df["primary_location"].apply(lambda x: x.get("source", {}).get("display_name", "") if isinstance(x, dict) and x.get("source") else "")

        # PubMed authors
        elif db_source.upper() == "PUBMED":
            if "authors" in df.columns:
                df["AU"] = df["authors"].apply(
                    lambda x: [author.get("name", "") for author in x] if isinstance(x, list) else []
                )
        
        # 4. Type Enforcement and Null Handling
        for col in cls.STANDARD_COLUMNS:
            if col in cls.LIST_COLUMNS:
                df[col] = df[col].apply(cls._parse_multi_value)
            elif col in cls.INTEGER_COLUMNS:
                df[col] = df[col].apply(cls._parse_scalar_int)
            else:
                df[col] = df[col].apply(cls._parse_scalar_str)
                
        # Return only the standard columns
        return df[cls.STANDARD_COLUMNS]

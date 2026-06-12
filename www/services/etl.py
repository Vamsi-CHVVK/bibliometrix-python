import pandas as pd
from typing import Union, List, Dict, Any
from .api_retriever import APIRetriever
from .standardizer import Standardizer
from .validator import Validator
from .format_functions import format_sr_column

class ETLPipeline:
    """
    Main ETL Pipeline dispatcher for Bibliometrix.
    
    This class acts as a central Dispatcher. It evaluates the type and origin of 
    the input source data, routes it to the appropriate Extractor (API or file parser),
    passes it through the Standardizer to enforce the schema, calculates secondary
    tags (like SR), and finally validates the output.
    """

    @classmethod
    def convert2df(cls, source_data: Union[str, pd.DataFrame, List[Dict[str, Any]]], 
                   source_type: str, 
                   is_api: bool = False, 
                   query: str = "",
                   original_filename: str = "") -> pd.DataFrame:
        """
        The main dispatcher function executing the Extract -> Transform -> Validate -> Load pipeline.
        
        Args:
            source_data (Union[str, pd.DataFrame, List[Dict[str, Any]]]): The raw data source. 
                Can be a filepath, a raw DataFrame, or a list of dictionaries.
            source_type (str): The origin of the data (e.g., "Scopus", "Dimensions", "PubMed", "OpenAlex").
            is_api (bool, optional): Flag indicating whether extraction should occur via live API query. Defaults to False.
            query (str, optional): The API search query, required if is_api is True. Defaults to "".
            original_filename (str, optional): Preserved filename used to infer data formats for manual uploads. Defaults to "".
            
        Returns:
            pd.DataFrame: A fully standardized, validated Bibliometrix-compatible DataFrame.
            
        Raises:
            ValueError: If the source type, file format, or API is unsupported.
        """
        # Phase 1: EXTRACT
        raw_data = None
        if is_api:
            if source_type.upper() == "OPENALEX":
                raw_data = APIRetriever.get_openalex(query)
            elif source_type.upper() == "PUBMED":
                raw_data = APIRetriever.get_pubmed(query)
            else:
                raise ValueError(f"API extraction not supported for {source_type}")
        else:
            if isinstance(source_data, str):
                # Use original_filename if provided, otherwise fallback to source_data path
                file_to_check = original_filename if original_filename else source_data
                
                # Manual download parsing
                if source_type.upper() == "SCOPUS" and file_to_check.lower().endswith('.csv'):
                    raw_data = pd.read_csv(source_data)
                elif source_type.upper() == "DIMENSIONS" and (file_to_check.lower().endswith('.xlsx') or file_to_check.lower().endswith('.csv')):
                    if file_to_check.lower().endswith('.xlsx'):
                        raw_data = pd.read_excel(source_data, skiprows=1)
                    else:
                        raw_data = pd.read_csv(source_data, skiprows=1)
                elif source_type.upper() == "PUBMED" and file_to_check.lower().endswith('.txt'):
                    from .parsers import parse_pubmed_data
                    raw_data = parse_pubmed_data(source_data)
                elif source_type.upper() == "WOS":
                    from .parsers import parse_wos_data
                    raw_data = parse_wos_data(source_data)
                else:
                    raise ValueError(f"Unsupported manual file format for {source_type} (file: {file_to_check})")
            elif isinstance(source_data, pd.DataFrame):
                raw_data = source_data
            elif isinstance(source_data, list):
                raw_data = source_data
            else:
                raise ValueError("Invalid source_data format")
                
        if len(raw_data) == 0:
            raise ValueError("No data extracted.")

        # Phase 2: TRANSFORM
        standardized_df = Standardizer.apply_mapping_and_types(raw_data, source_type)
        
        # Phase 3 & 4: CALCULATED FIELDS (SR)
        # We need to apply format_sr_column. 
        # format_sr_column expects the entry in the specific database format.
        # But we already standardized. To reuse format_sr_column, we must pass it 
        # simulating WoS format or the original source format.
        # The easiest way is to use the original raw data row to generate SR if possible, 
        # or simulate a WoS entry since our dataframe is now in WoS standard schema.
        
        sr_list = []
        for i in range(len(standardized_df)):
            row = standardized_df.iloc[i]
            # Create a mock WoS entry for format_sr_column
            # format_sr_column for Web_of_Science .txt expects:
            # AU: list of strings (first author comma separated)
            # PY: string (it takes [0], so we provide a list or string)
            # SO: list of strings or a single string
            
            mock_entry = {}
            if len(row["AU"]) > 0:
                # Ensure author is comma separated (Surname, Initials)
                author = row["AU"][0]
                if "," not in author:
                    parts = author.split()
                    if len(parts) > 1:
                        author = f"{parts[-1]}, {' '.join(parts[:-1])}"
                mock_entry["AU"] = [author]
            else:
                mock_entry["AU"] = ["Unknown, U."]
                
            mock_entry["PY"] = [str(row["PY"])]
            mock_entry["SO"] = [str(row["SO"])]
            
            try:
                sr = format_sr_column(mock_entry, 'Web_of_Science', '.txt')
            except Exception as e:
                sr = "Unknown, 0000, Unknown"
                
            sr_list.append(sr)
            
        standardized_df["SR"] = sr_list

        # Phase 5: VALIDATION
        Validator.validate(standardized_df)

        return standardized_df

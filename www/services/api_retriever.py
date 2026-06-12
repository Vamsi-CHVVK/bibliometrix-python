import requests
import time
import math
from typing import List, Dict, Any

class APIRetriever:
    """
    Handles data extraction from bibliographic APIs such as OpenAlex and PubMed.
    
    This class abstracts the raw HTTP requests, pagination, and rate limiting 
    associated with fetching metadata from external sources.
    """
    
    @staticmethod
    def get_openalex(query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Fetches bibliographic records from the OpenAlex API based on a search query.
        Handles API pagination and basic rate limiting to politely extract data.

        Args:
            query (str): The keyword search string to query OpenAlex works.
            max_results (int, optional): The maximum number of records to retrieve. Defaults to 100.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries, where each dictionary represents 
                                  a single bibliographic record retrieved from OpenAlex.
        """
        base_url = "https://api.openalex.org/works"
        results = []
        per_page = min(max_results, 50)
        
        try:
            # Initial request to get total count
            params = {
                "search": query,
                "per-page": per_page,
                "page": 1,
                "mailto": "test@example.com"  # Polite pool
            }
            response = requests.get(base_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            meta = data.get("meta", {})
            total_count = meta.get("count", 0)
            if total_count == 0:
                return results
                
            results.extend(data.get("results", []))
            
            # Fetch remaining pages if needed
            pages_needed = math.ceil(min(total_count, max_results) / per_page)
            for page in range(2, pages_needed + 1):
                time.sleep(0.1) # Rate limit respect
                params["page"] = page
                response = requests.get(base_url, params=params, timeout=10)
                if response.status_code == 200:
                    data = response.json()
                    results.extend(data.get("results", []))
                
            # Limit exactly to max_results
            return results[:max_results]
        except Exception as e:
            print(f"Error retrieving from OpenAlex: {e}")
            return results

    @staticmethod
    def get_pubmed(query: str, max_results: int = 100) -> List[Dict[str, Any]]:
        """
        Fetches bibliographic records from the PubMed API using NCBI E-utilities.
        This is a two-step process: first fetching PMIDs via esearch, then fetching 
        document summaries via esummary, adhering to the NIH limit of 3 requests per second.

        Args:
            query (str): The keyword search string to query PubMed.
            max_results (int, optional): The maximum number of records to retrieve. Defaults to 100.

        Returns:
            List[Dict[str, Any]]: A list of dictionaries representing PubMed summaries 
                                  mapped directly from the JSON response.
        """
        search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        summary_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
        results = []
        
        try:
            # Step 1: Get PMIDs
            search_params = {
                "db": "pubmed",
                "term": query,
                "retmax": max_results,
                "retmode": "json"
            }
            search_response = requests.get(search_url, params=search_params, timeout=10)
            search_response.raise_for_status()
            search_data = search_response.json()
            id_list = search_data.get("esearchresult", {}).get("idlist", [])
            
            if not id_list:
                return results
                
            # Step 2: Get summaries for these PMIDs
            # PubMed limits to 200-300 ids per GET request, we'll chunk by 100
            chunk_size = 100
            for i in range(0, len(id_list), chunk_size):
                chunk = id_list[i:i + chunk_size]
                time.sleep(0.34) # NIH allows 3 requests per second
                summary_params = {
                    "db": "pubmed",
                    "id": ",".join(chunk),
                    "retmode": "json"
                }
                sum_response = requests.get(summary_url, params=summary_params, timeout=10)
                if sum_response.status_code == 200:
                    sum_data = sum_response.json()
                    result_dict = sum_data.get("result", {})
                    # uids are stored in result["uids"], actual data in result[uid]
                    for uid in result_dict.get("uids", []):
                        if uid in result_dict:
                            results.append(result_dict[uid])
                            
            return results
        except Exception as e:
            print(f"Error retrieving from PubMed: {e}")
            return results

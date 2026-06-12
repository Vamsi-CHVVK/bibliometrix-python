import sys
import os
import pandas as pd

# Add the project root to sys.path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from www.services.etl import ETLPipeline
from functions.get_annualproduction import get_annual_production
from functions.get_relevantauthors import get_relevant_authors
from functions.get_frequentwords import get_frequent_words
from functions.get_wordcloud import get_wordcloud
from functions.get_averagecitations import get_average_citations

class MockReactive:
    def __init__(self, df):
        self.df = df
    def get(self):
        return self.df
    def set(self, value):
        self.df = value

def test_api_extraction():
    print("=== Testing ETL Pipeline with OpenAlex API ===")
    try:
        # Extract and standardize
        query = "machine learning bibliometrics"
        print(f"Querying OpenAlex for: '{query}'...")
        df = ETLPipeline.convert2df(source_data="API", source_type="OpenAlex", is_api=True, query=query)
        print(f"Successfully extracted and standardized {len(df)} records.")
        print("Columns:", df.columns.tolist())
        print("Sample of SR column:", df['SR'].head(3).tolist())
        
        # Wrap the DataFrame to simulate Shiny's reactive.Value.get()
        reactive_df = MockReactive(df)
        
        # Test analytical functions
        print("\n--- Testing Analytical Functions ---")
        
        # 1. Annual Production
        try:
            print("1. get_annual_production...")
            res = get_annual_production(reactive_df)
            print("Success!")
        except Exception as e:
            print(f"Failed: {e}")

        # 2. Relevant Authors
        try:
            print("2. get_relevant_authors...")
            res = get_relevant_authors(reactive_df, num_of_authors=10)
            print("Success!")
        except Exception as e:
            print(f"Failed: {e}")

        # 3. Frequent Words
        try:
            print("3. get_frequent_words...")
            # We need to simulate the parameters the function expects
            res = get_frequent_words(reactive_df, ngram=1, num_of_words=10, word_type="TI", file_upload_terms=None, file_upload_synonyms=None)
            print("Success!")
        except Exception as e:
            print(f"Failed: {e}")

        # 4. WordCloud
        try:
            print("4. get_wordcloud...")
            res = get_wordcloud(reactive_df, ngram=1, num_of_words_wc=10, field_wc="TI", file_upload_terms_wc=None, file_upload_synonyms_wc=None)
            print("Success!")
        except Exception as e:
            print(f"Failed: {e}")

        # 5. Average Citations
        try:
            print("5. get_average_citations...")
            res = get_average_citations(reactive_df)
            print("Success!")
        except Exception as e:
            print(f"Failed: {e}")

    except Exception as e:
        print(f"Pipeline execution failed: {e}")

if __name__ == "__main__":
    test_api_extraction()

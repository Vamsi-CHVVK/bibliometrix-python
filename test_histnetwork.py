import sys
sys.path.append('.')
from www.services.etl import ETLPipeline
from www.services.histnetwork import histNetwork
import pandas as pd
from shiny import reactive

def test_histnetwork():
    # 1. Fetch data from OpenAlex API
    query = "machine learning"
    print(f"Fetching data for query: {query}")
    df = ETLPipeline.convert2df(source_data="API", source_type="OpenAlex", is_api=True, query=query)
    
    print("\nStarting histNetwork test...")
    # histNetwork requires a reactive.Value according to standard implementation, 
    # but the function itself calls df.get(). 
    # Let's wrap it in a mock object with a .get() method if necessary, 
    # but looking at histNetwork: M = df.get() if hasattr(df, 'get') else df
    class MockReactive:
        def __init__(self, val):
            self.val = val
        def get(self):
            return self.val

    rv_df = MockReactive(df)
    results = histNetwork(rv_df, network=True)
    
    if results is not None:
        print("\nhistNetwork executed successfully!")
        print(f"NetMatrix shape: {results['NetMatrix'].shape}")
    else:
        print("\nhistNetwork failed.")

if __name__ == '__main__':
    test_histnetwork()

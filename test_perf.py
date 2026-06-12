import time
import sys
sys.path.append('.')
from www.services.etl import ETLPipeline
from www.services.histnetwork import histNetwork

def test_perf():
    print("Fetching...")
    t0 = time.time()
    df = ETLPipeline.convert2df(source_data='API', source_type='OpenAlex', is_api=True, query='machine learning')
    t1 = time.time()
    print(f"Fetched {len(df)} rows in {t1-t0:.2f}s")
    
    class MockReactive:
        def __init__(self, val):
            self.val = val
        def get(self):
            return self.val
            
    rv_df = MockReactive(df)
    print("Running histNetwork...")
    t2 = time.time()
    res = histNetwork(rv_df, network=True)
    t3 = time.time()
    print(f"histNetwork completed in {t3-t2:.2f}s")

if __name__ == '__main__':
    test_perf()

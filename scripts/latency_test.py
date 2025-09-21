### latency_test
## Executes a simple test of the latency of an SearXNG server in Docker

import time
from pyfiles.searxng_utils import SearxngClient
from pyfiles.logger import logger

logger.info(f'⚙️ Starting latency test in `./scripts/latency_test.py`')

query = 'searxng'

def measure_run_latency(client, query=query):
    start = time.perf_counter()
    response = client.run(query=query)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(f"Latency: {elapsed_ms:.1f} ms")
    return elapsed_ms

def measure_results_latency(client, query=query, num_results=1):
    start = time.perf_counter()
    response = client.results(query=query, num_results=num_results)
    elapsed_ms = (time.perf_counter() - start) * 1000
    logger.info(f"Latency: {elapsed_ms:.1f} ms | Number of results: {len(response)}")
    return elapsed_ms

def run_test(client, n_tests, method_name, num_results=1):
    latency_sum = 0
    for i in range(n_tests):
        if method_name=='run':
            latency = measure_run_latency(client)
        elif method_name=='results':
            latency = measure_results_latency(client, num_results=num_results)
        latency_sum += latency
        logger.info(f"Test {i}")

    latency_avg = latency_sum/n_tests
    logger.info(f"Latency average for {method_name}: {latency_avg:.1f}")


n_tests = 10
## Initialize SearXNG client
# Defaults to host on url 'http://localhost:8080'
client: SearxngClient = SearxngClient()
# Warmup client
client.run()
run_test(client, n_tests, 'run')
run_test(client, n_tests, 'results')
run_test(client, 1, 'results', 25)

logger.info(f'✅ Finished latency test in `./scripts/latency_test.py` \n\n')
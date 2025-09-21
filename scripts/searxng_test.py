### searxng_test
## Executes a test of the available LangChain functions to query the SearXNG server.
## The script runs as follows:
#   - Initialize SearXNGClient (initialize class and test response with requests)
#   - Test the run and results methods of LangChain's SearxSearchWrapper

from pyfiles.searxng_utils import SearxngClient
from pyfiles.logger import logger

logger.info(f'⚙️ Starting SearXNG test in `./scripts/searxng_test.py`')

## Initialize SearXNG client
# Defaults to host on url 'http://localhost:8080'
client = SearxngClient()

## Get responses using Lanchain's SearxSearchWrapper
# Default query = 'Python programming' and default num_results=2
client.run()
client.results()

logger.info(f'✅ Finished SearXNG test in `./scripts/searxng_test.py` \n\n')
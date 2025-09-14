### searxng_utils
## Defines functions needed to setup and query SearXNG server.

import time
import requests
from requests.models import Response
from langchain_community.utilities import SearxSearchWrapper
from typing import List, Optional, Any
import pprint

from logger import logger, with_spinner

## Define constants
# URL | SearXNG server url from Docker setup
url: str = 'http://localhost:8080'

# Query | Default query to search
query: str = 'Python programming'

# Number of results | Default number of results for `results` method
num_results: int = 2


class SearxngClient:
    """A SearXNG client that can be used to search the web.

    The user can search the web by initializing the client then using the `requests_search`, `run` or, `results` methods to get search results.

    For example, to initialize the client for a given url:
    ```python
    url = 'http://localhost:8080'
    client = SearxngClient(url=url)
    ```

    To get the entire HTML structure from Requests, use the `requests_search` method:
    ```python
    query = 'Python programming'
    client.requests_search(query=query)
    ```

    To get a single search result (with summary) for a given query, use the `run` method:
    ```python
    query = 'Python programming'
    client.run(query=query)
    ```

    To get some number of more detailed search results, use the `results` method:
    ```python
    num_results = 2
    query = 'Python programming'
    client.results(query=query)
    ```
    
    Attributes
    ------------
        url: str, Optional
            The url on which to host the Ollama client.
            Defaults to 'http://localhost:8080'
        client: SearxSearchWrapper (LangChain), Optional
            The Searxng search wrapper to use to get search results
    """
    def __init__(
        self, 
        url: str = url,
        client: SearxSearchWrapper | None = None
    ) -> None:
        """Initialize the SearXNG client hosted on the given url.
        
        Args
        ------------
            url: str, Optional
                The url on which to host the SearXNG client.
                Defaults to 'http://localhost:8080'
            
        Raises
        ------------
            Exception: 
                If initialization fails, error is logged and raised.
        """
        try:
            self.url = url
            # Test the response from the SearXNG server on initialization
            self._test_searxng()

            # Initialize SearXNG wrapper that will utilize our SearXNG server
            if client is None:
                self.client: SearxSearchWrapper = SearxSearchWrapper(searx_host=self.url)
            else:
                self.client = client
        except Exception as e:
            logger.error(f"❌ Failed to initialize SearxngClient: {str(e)}\n")
            raise


    ## Ensure SearXNG server can be reached
    def _test_searxng(
        self
    ) -> None:
        """Test the response from the SearXNG server using Requests by checking the status code and the expected content.
            
        Raises
        ------------
            Exception: 
                If testing the SearXNG server fails, error is logged and raised.
        """
        max_retries: int = 5    # Maximum number of retry attempts
        retry_delay: int = 10   # Delay in seconds between retries

        # Test the response
        logger.info(f"⚙️ Testing SearXNG server at `{url}`")
        for attempt in range(max_retries):
            try:
                with with_spinner(description=f"📶 Checking connection ..."):
                    # Send HTTP GET request with a timeout of 30 seconds
                    response: Response = requests.get(self.url, timeout=30)

                # Success if status code == 200
                if response.status_code == 200:
                    logger.info("✅ SearXNG server is up.")
                    logger.info("⚙️ Getting test response...")
                    # Check for expected content in the response text
                    if "SearXNG" in response.text:
                        logger.info("✅ Found expected content in the response.\n")
                    else:
                        logger.warning("⚠️ Content not found, but status code OK.\n")
                    return  # Exit successfully if all checks pass
                # Failure if status code != 200
                else:
                    logger.error(f"❌ Received unexpected status code: {response.status_code}\n")

            except requests.exceptions.RequestException as e:
                logger.error(f"❌ Request failed: {e}\n")
                raise

            # Retry logic: Delay before next attempt, unless it's the last one
            if attempt < max_retries - 1:
                logger.info(f"⏳ Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)

        # Final failure case after all retries
        logger.error("❌ Failed to connect to SearXNG server after multiple attempts.\n")
        exit(1)


    ## Get search results using Requests
    def requests_search(
        self, 
        query: str = query
    ) -> str | None:
        """Use the search endpoint of the SearXNG server with requests for a given query.
           This will output the entire HTML of the search result.

           For example, to get a search results for a given query:
           ```python
            url = 'http://localhost:8080'
            client = SearxngClient(url=url)

            query = 'Python programming'
            client._searxng_search(query=query) 
           ```

        Args
        ------------
            query: str, Optional 
                Query to send to search endpoint.
                Defaults to 'Python programming'.

        Returns
        ------------
            str: 
                The response from the SearXNG server.
            
        Raises
        ------------
            Exception: 
                If get a search results fails, error is logged and raised.
        """
        ## Validate query
        # Even though requests takes many different objects and converts them to a URL string, 
        # seems better to make clear what query should be
        # (e.g. What if someone passes a list? Could expect to get a list of results back.)
        if not isinstance(query, str):
            raise TypeError(f"Query must be a string, got {type(query)}.")
        # Must not be empty string
        if query=='':
            raise ValueError(f"Query must not be an empty string.")

        try:
            logger.info(f"⚙️ Performing search for query through requests: {query}")
            # Send a GET request with the search query as a parameter
            params: dict = {'q': query}
            timeout: int = 30 # How long in seconds to wait for a response
            # Get results
            response: Response = requests.get(
                self.url, 
                params=params, 
                timeout=timeout
            )

            if response.status_code == 200:
                logger.info("✅ Search successful.")
                # Log response
                # This will be entire html content - pretty nice for learning purposes
                logger.info(f'📝 Response: `{response.text}`\n\n')
                return response.text
            else:
                logger.error(f"❌ Search failed. Status code: {response.status_code}\n")
                return None

        except Exception as e:
            logger.error(f"❌ Failed to perform search: {str(e)}\n")
            raise


    ## Get search result summary using LangChain's `SearxSearchWrapper.run` method
    def run(
        self, 
        query: str = query
    ) -> str | dict:
        """Use the run method of the SearxSearchWrapper class of the LangChain library. 
        Get a search result for a given query. 

        For example, to get a search result for a given query:
        ```python
        url = 'http://localhost:8080'
        client = SearxngClient(url=url)

        query = 'Python programming'
        client.run(query=query)
        ```

        Args
        ------------
            query: str, Optional 
                Query to send to LangChain SearxSearchWrapper.
                Defaults to 'Python programming'.

        Returns
        ------------
            str: 
                The response from the SearXNG server.
            
        Raises
        ------------
            Exception: 
                If getting a search results fails, error is logged and raised.
        """
        ## Validate query
        # Must be string
        if not isinstance(query, str):
            raise TypeError(f"Query must be a string, got {type(query)}.")
        # Must not be empty string
        if query=='':
            raise ValueError(f"Query must not be an empty string.")

        logger.info(f"⚙️ Performing search for query through LangChain: {query}")
        try:
            with with_spinner(description=f"🔎 Getting results..."):            
                # Get results
                results: str | dict = self.client.run(
                    query=query
                )
            if results is not None:
                if isinstance(results, str):
                    logger.info(f'📝 Results:')
                    logger.info(f'{results}\n')
                else:
                    logger.info(f'📝 Results:')
                    logger.info(f'{pprint.pformat(results, indent=0, width=500)}\n')
                return results
            else:
                error_message = (f'❌ Problem getting results. Found None response.')
                logger.error(error_message)
                raise ValueError(error_message)
        except Exception as e:
            logger.error(f'❌ Problem getting search run: `{str(e)}`\n')
            raise

    
    ## Get search results using LangChain's `SearxSearchWrapper.results` method
    def results(
        self, 
        query: str = query, 
        num_results: int = num_results
    ) -> List[dict]:
        """Use the result method of the SearxSearchWrapper class of the LangChain library. 
        Get a list of search results for a given query. 

        For example, to get some number of results for a given query:
        ```python
        url = 'http://localhost:8080'
        client = SearxngClient(url=url)

        num_results = 2
        query = 'Python programming'
        client.results(query=query, num_results=num_results)
        ```

        Args
        ------------
            query: str, Optional 
                Query to send to LangChain SearxSearchWrapper.
                Defaults to 'Python programming'
            num_results: int, Optional 
                Number of results to get.
                Defaults to 2.

        Returns
        ------------
            List[dict]: 
                The response from the SearXNG server. 
                A list of search results for the given query.
            
        Raises
        ------------
            Exception: 
                If getting search results fails, error is logged and raised.
        """
        ## Validate query
        # Must be string
        if not isinstance(query, str):
            raise TypeError(f"Query must be a string, got {type(query)}.")
        # Must not be empty string
        if query=='':
            raise ValueError(f"Query must not be an empty string.")

        logger.info(f"⚙️ Performing search for query through LangChain: {query}")
        try:
            with with_spinner(description=f"🔎 Getting results..."): 
                # Get results
                results: List[dict] = self.client.results(
                    query=query,
                    num_results=num_results
                )
            if results is not None:
                logger.info(f'📝 Results:')
                logger.info(f'{pprint.pformat(results, indent=0, width=500)}\n')
                return results
            else:
                error_message = (f'❌ Problem getting results. Found None response.')
                logger.error(error_message)
                raise ValueError(error_message)
        except Exception as e:
            logger.error(f'❌ Problem getting search run: `{str(e)}`\n')
            raise
### tests/test_unit.py
## Defines unit tests for methods in ./searxng_utils.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

## For unit testing, we don't want to rely on real Searxng API calls, we just want 
## to test the logic of our code

import requests
import responses
from unittest import TestCase
from unittest.mock import call, patch, MagicMock, Mock
from langchain_community.utilities import SearxSearchWrapper

# Import modules
from searxng_utils import SearxngClient, url, query, num_results

# Sample mock HTML response from a SearXNG search result
MOCK_SEARCH_RESPONSE = """
<html>
  <body>
    <div class="result">
      <h3><a href="http://example.com">SearXNG</a></h3>
      <p>Summary of the example result.</p>
    </div>
  </body>
</html>
"""

## Now let's test everything
class TestSearxngClientUnit(TestCase):
    """
    Unit tests for `SearxngClient` class.
    
    This test suite contains unit tests for the `SearxngClient` class of 
    `searxng_utils.py`, covering initialization and response handling.

    All tests use mocking to isolate the class under test from external dependencies.
    """

    ## Test successful client initialization
    @responses.activate
    @patch('searxng_utils.SearxSearchWrapper')
    def test_init_client_success(self, mock_client):
        """
        Test successful initialization of SearxngClient with a custom URL.
        
        Verifications
        ------------
            The client is initialized with the correct URL
            The underlying SearxSearchWrapper client is instantiated with the provided host
            The correct host parameter is passed to the SearxSearchWrapper constructor
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            client.searx_host matches the provided URL
            SearxSearchWrapper (LangChain) is called exactly once with correct host parameter
        """
        ## Arrange
        # SearxSearchWrapper | Create a mock instance of the client
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance

        # Clear responses just in case
        responses.reset()
        # requests.get | Create a mock response
        responses.add(
            responses.GET,
            url,
            body=MOCK_SEARCH_RESPONSE,
            status=200
        )

        ## Act
        # Responses mocks requests
        # SearxSearchWrapper call replaced with mock_client
        client = SearxngClient(url=url)

        ## Assert
        self.assertEqual(client.url, url)
        mock_client.assert_called_once_with(searx_host=url)


    ## Test unsuccessful client initialization
    @patch('requests.get')
    def test_init_client_unavailable(self, mock_get):
        """
        Test error handling of SearxngClient when SearXNG server unavailable.
        
        Verifications
        ------------
            Initializing the SearxngClient raises an exception when the SearXNG server is unavailable
            Exception is propagated correctly
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            ConnectionError is raised when response has no content
        """
        ## Arrange
        # requests.get | Create error
        error = requests.exceptions.ConnectionError
        mock_get.side_effect = error

        ## Act and Assert
        with self.assertRaises(error):
            client = SearxngClient(url=url)


    ## Test server errors
    @patch('requests.get')
    @patch('searxng_utils.SearxSearchWrapper')
    def test_retry_on_server_error(self, mock_client, mock_get):
        """
        Test handling of SearxngClient initialization when Requests gives server errors.
        
        Verifications
        ------------
            Initializing the SearxngClient correctly retries with server errors
            SearxSearchWrapper client is successfully initalized after successful status code
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            GET (requests) is retried each time a server error is encountered
            client.searx_host matches the provided URL
            SearxSearchWrapper (LangChain) is called exactly once with correct host parameter
        """
        ## Arrange
        # SearxSearchWrapper | Create a mock instance of the client
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        # requests.get | Create two server errors and one success
        mock_get.side_effect = [
            MagicMock(status_code=500, text="Server Error"),
            MagicMock(status_code=600, text="Server Error"),
            MagicMock(status_code=200, text="SearXNG")
        ]

        ## Act and Assert
        with patch('searxng_utils.time.sleep') as mock_sleep:
            client = SearxngClient(url=url)
            
            # Verify sleep was called twice
            self.assertEqual(mock_sleep.call_count, 2)
            
            # Verify sleep was called with the correct argument each time
            expected_calls = [call(10)] * 2
            mock_sleep.assert_has_calls(expected_calls)

            self.assertEqual(client.url, url)
            mock_client.assert_called_once_with(searx_host=url)

    @patch('requests.get')
    @patch('searxng_utils.SearxSearchWrapper')
    def test_retry_on_server_error_then_fail(self, mock_client, mock_get):
        """
        Test handling of SearxngClient initialization when Requests gives server errors then fails.
        
        Verifications
        ------------
            Initializing the SearxngClient correctly retries with server errors
            SearxSearchWrapper client is not initalized after max number of retry attempts fail
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            GET (requests) is retried each time a server error is encountered
            SearxSearchWrapper (LangChain) is never called
        """
        ## Arrange
        # SearxSearchWrapper | Create a mock instance of the client
        mock_client_instance = MagicMock()
        mock_client.return_value = mock_client_instance
        # requests.get | Create 5 server errors
        mock_get.side_effect = [
            MagicMock(status_code=500, text="Server Error")
        ] * 5

        ## Act & Assert
        with patch('searxng_utils.time.sleep') as mock_sleep:
            with self.assertRaises(SystemExit):
                client = SearxngClient(url=url)

            # Verify sleep was called 4 times
            self.assertEqual(mock_sleep.call_count, 4)
            expected_calls = [call(10)] * 4
            mock_sleep.assert_has_calls(expected_calls)

        # Ensure SearXNG client wasn't initialized if it failed
        mock_client.assert_not_called()


    #//////////////////////////////////////////////////////////#
    ### Testing requests //////////////////////////////////////#
    ## Test successful response from `requests_search`
    @responses.activate
    def test_requests_success(self): 
        """
        Test getting response from `requests_search` method.
        
        Verifications
        ------------
            The result has the expected content
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            Response is not none
            'SearXNG' in response
        """
        ## Arrange    
        # Clear responses just in case
        responses.reset()
        # requests.get | Create a mock response  
        responses.add(
            responses.GET,
            url,
            body=MOCK_SEARCH_RESPONSE,
            status=200
        )

        ## Act
        client = SearxngClient(url=url)
        # requests.get will be replaced with responses mock
        result = client.requests_search(query=query)
        
        ## Assert
        self.assertIsNotNone(result)
        self.assertIn("SearXNG", result)


    ## Test unsuccessful response from `requests_search`
    @responses.activate
    def test_requests_error_code(self): 
        """
        Test error handling when given code other than success.
        
        Verifications
        ------------
            Recieving a code other than success results in None output
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            None output is obtained for status code other than success
        """
        ## Arrange
        status_codes = [404, 500]
    
        for code in status_codes:
            with self.subTest(status_code=code):
                # Clear responses just in case
                responses.reset()
                # requests.get | Create a mock response for SearxngClient initialization  
                responses.add(
                    responses.GET,
                    url,
                    body=MOCK_SEARCH_RESPONSE,
                    status=200
                )
                # Create a mock response for the status code
                responses.add(
                    responses.GET,
                    url,
                    body='',
                    status=code
                )

                ## Act
                client = SearxngClient(url=url)
                result = client.requests_search(query=query)
                
                ## Assert
                self.assertIsNone(result)


    #///////////////////////////////////////////////////////////#
    ### Generic test runners ///////////////////////////////////#
    # Test successful response from method
    @responses.activate
    def _test_method_success(self, method_name):
        """
        Test success response from a method.
        
        Verifications
        ------------
            Expected response is obtained from method for a given query
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            Mock result is equal to result obtained from method
        """
        ## Arrange
        mock_result = "This is a mocked search result"
        # SearxSearchWrapper | Create a mock instance
        mock_client = Mock(spec=SearxSearchWrapper)
        # SearxSearchWrapper.run | Create a mock instance
        method = getattr(mock_client, method_name)
        method.return_value = mock_result

        # Clear responses just in case
        responses.reset()
        # requests.get | Create a mock response  
        responses.add(
            responses.GET,
            url,
            body=MOCK_SEARCH_RESPONSE,
            status=200
        )

        ## Act
        client = SearxngClient(url=url, client=mock_client)
        method = getattr(client, method_name)
        result = method(query=query)

        ## Assert
        self.assertEqual(result, mock_result)

    # Test unsuccessful response from method
    @responses.activate
    def _test_method_none_response(self, method_name):
        """
        Test error handling when method returns None response.
        
        Verifications
        ------------
            The method raises ValueError when response content is None
            Exception is raised appropriately when no content is returned
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            ValueError is raised when response has no content
        """
        ## Arrange
        mock_result = None
        # SearxSearchWrapper | Create a mock instance
        mock_client = Mock(spec=SearxSearchWrapper)
        # SearxSearchWrapper.run | Create a mock instance
        method = getattr(mock_client, method_name)
        method.return_value = mock_result

        # Clear responses just in case
        responses.reset()
        # requests.get | Create a mock response  
        responses.add(
            responses.GET,
            url,
            body=MOCK_SEARCH_RESPONSE,
            status=200
        )

        ## Act
        client = SearxngClient(url=url, client=mock_client)

        ## Assert
        with self.assertRaises(ValueError):
            method = getattr(client, method_name)
            result = method(query=query)

    # Test response from method with query different from default
    @responses.activate
    def _test_method_diff_query(self, method_name):
        """
        Test response from method with a different query from the default.
        
        Verifications
        ------------
            Expected response is obtained from method for a given query
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            Mock result is equal to result obtained from method
        """
        ## Arrange
        query_example = 'Python programming with LangChain'
        mock_result = 'LangChain allows users to build AI agents.'
        # SearxSearchWrapper | Create a mock instance
        mock_client = Mock(spec=SearxSearchWrapper)
        # SearxSearchWrapper.run | Create a mock instance
        method = getattr(mock_client, method_name)
        method.return_value = mock_result

        # Clear responses just in case
        responses.reset()
        # requests.get | Create a mock response  
        responses.add(
            responses.GET,
            url,
            body=MOCK_SEARCH_RESPONSE,
            status=200
        )

        ## Act
        client = SearxngClient(url=url, client=mock_client)
        method = getattr(client, method_name)
        result = method(query=query_example)

        ## Assert
        self.assertEqual(result, mock_result)

    ## Test response with empty query
    @responses.activate
    def _test_method_no_query(self, method_name):
        """
        Test error handling of method with an empty query.
        
        Verifications
        ------------
            Invoking the method with an empty string raises an exception
            Exception is propagated correctly
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            ValueError is raised when query is empty
        """
        ## Arrange
        query_example = ''
        # SearxSearchWrapper | Create a mock instance
        mock_client = Mock(spec=SearxSearchWrapper)
        # SearxSearchWrapper.run | Create a mock instance
        method = getattr(mock_client, method_name)
        method.side_effect = ValueError(f"Query must not be an empty string.")

        # Clear responses just in case
        responses.reset()
        # requests.get | Create a mock response  
        responses.add(
            responses.GET,
            url,
            body=MOCK_SEARCH_RESPONSE,
            status=200
        )

        ## Act
        client = SearxngClient(url=url, client=mock_client)

        ## Assert
        with self.assertRaises(ValueError):
            method = getattr(client, method_name)
            response = method(query=query_example)

    ## Test response with an incorrect query type 
    @responses.activate
    def _test_method_bad_query_type(self, method_name):
        """
        Test error handling of method when the query type is not a string.

        Verifications
        ------------
            Invoking the method raises an exception when passed an incorrect query type
            Exception is propagated correctly
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance

        Asserts
        ------------
            TypeError is raised when passed wrong query type
        """
        ## Arrange
        invalid_queries = [
            ([1], "list"),
            ([1, 'Hi'], "list with mixed types"),
            ({'key': 1, 'value': 'Hi'}, "dictionary"),
            ({1, 'Hi'}, "set"),
            (1, "integer"),
            (3.14, "float"),
            (None, "NoneType"),
            (True, "boolean")
        ]
        # SearxSearchWrapper | Create a mock instance
        mock_client = Mock(spec=SearxSearchWrapper)
        # SearxSearchWrapper.run | Create a mock instance
        method = getattr(mock_client, method_name)
        method.side_effect = TypeError

        # Clear responses just in case
        responses.reset()
        # requests.get | Create a mock response  
        responses.add(
            responses.GET,
            url,
            body=MOCK_SEARCH_RESPONSE,
            status=200
        )

        ## Act
        client = SearxngClient(url=url, client=mock_client)        
        
        ## Run through each query
        for query, description in invalid_queries:
            with self.subTest(query_type=description):
                with self.assertRaises(TypeError):
                    method = getattr(client, method_name)
                    response = method(query=query)
  

    #//////////////////////////////////////////////////////////#
    ### Testing run ///////////////////////////////////////////#
    # Test successful response from `run`
    def test_run_success(self):
        """
        Test success response from `run` method.
        
        Verifications
        ------------
            Expected response is obtained from method for a given query
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            Mock result is equal to result obtained from `run` method
        """
        self._test_method_success(method_name='run')

    # Test unsuccessful response from `run`
    def test_run_none_response(self):
        """
        Test error handling when `run` method returns None response.
        
        Verifications
        ------------
            The method raises ValueError when response content is None
            Exception is raised appropriately when no content is returned
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            ValueError is raised when response has no content
        """
        self._test_method_none_response(method_name='run')

    # Test response with different query from `run`
    def test_run_diff_query(self):
        """
        Test response from `run` method with a different query from the default.
        
        Verifications
        ------------
            Expected response is obtained from method for a given query
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            Mock result is equal to result obtained from `run` method
        """
        self._test_method_diff_query(method_name='run')

    # Test `run` method with passed empty query
    def test_run_no_query(self):
        """
        Test error handling of `run` method with an empty query.
        
        Verifications
        ------------
            Invoking the method with an empty string raises an exception
            Exception is propagated correctly
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            ValueError is raised when query is empty
        """
        self._test_method_no_query(method_name='run')

    def test_run_bad_query_type(self):
        """
        Test error handling of `run` method when the query type is not a string.

        Verifications
        ------------
            Invoking the method raises an exception when passed an incorrect query type
            Exception is propagated correctly
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance

        Asserts
        ------------
            TypeError is raised when passed wrong query type
        """
        self._test_method_bad_query_type(method_name='run')


    #//////////////////////////////////////////////////////////#
    ### Testing results ///////////////////////////////////////#
    # Test successful response from `results`
    @responses.activate
    def test_results_success(self):
        """
        Test success response from `results` method.
        
        Verifications
        ------------
            Expected response is obtained from method for a given query
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            Mock result is equal to result obtained from `results` method
        """
        self._test_method_success(method_name='results')

    # Test unsuccessful response from `results`
    @responses.activate
    def test_results_none_response(self):
        """
        Test error handling when `results` method returns None response.
        
        Verifications
        ------------
            The method raises ValueError when response content is None
            Exception is raised appropriately when no content is returned
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            ValueError is raised when response has no content
        """
        self._test_method_none_response(method_name='results')

    # Test response with different query from `results`
    def test_results_diff_query(self):
        """
        Test response from `results` method with a different query from the default.
        
        Verifications
        ------------
            Expected response is obtained from method for a given query
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            Mock result is equal to result obtained from `results` method
        """
        self._test_method_diff_query(method_name='results')

    # Test `results` method with passed empty query
    def test_results_no_query(self):
        """
        Test error handling of `results` method with an empty query.
        
        Verifications
        ------------
            Invoking the method with an empty string raises an exception
            Exception is propagated correctly
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance
        
        Asserts
        ------------
            ValueError is raised when query is empty
        """
        self._test_method_no_query(method_name='results')

    def test_results_bad_query_type(self):
        """
        Test error handling of `results` method when the query type is not a string.

        Verifications
        ------------
            Invoking the method raises an exception when passed an incorrect query type
            Exception is propagated correctly
        
        Mocks
        ------------
            GET (requests) is mocked and returns a mock instance
            SearxSearchWrapper (LangChain) is mocked and returns a mock instance

        Asserts
        ------------
            TypeError is raised when passed wrong query type
        """
        self._test_method_bad_query_type(method_name='results')
### tests/test_integration.py
## Defines integration tests for making sure methods in ./pyfiles/searxng_utils.py can be properly used with SearXNG server

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
import requests
from unittest import TestCase
from langchain_community.utilities import SearxSearchWrapper

# Import modules
from pyfiles.searxng_utils import SearxngClient, url, query, num_results


class TestSearxngClientIntegration(TestCase):
    """
    Integration tests for SearxngClient against a real Searxng server.

    These tests ensure that the methods in `pyfiles/searxng_utils.py` work correctly when communicating 
    with a running instance of the Searxng server. They verify basic functionality such as:
    
    - Client initialization
    - Search result generation from the client
    
    All tests require a running Searxng server at http://localhost:8080.
    """

    ## Class resources
    # This sets up resources that are used for each test in the class
    @classmethod
    def setUpClass(cls):
        """
        Set up class-level fixtures once for all tests.

        Variables
        ------------
            url: str
                URL of the Searxng server
                Defaults to 'http://localhost:8080'
            query: str
                Example query to use.
                Defaults to 'Python programming'
            num_results: int
                Example number of results to get.
                Defaults to 2.
        """
        cls.test_url = url
        cls.test_query = query
        cls.test_num_results = num_results


    ## Set up for each test
    # Make sure the Searxng server is available,
    # and if it isn't we skip the current test and move onto the next
    def setUp(self):
        """
        Set up test fixtures before each test method.

        Verifications
        ------------
            Searxng server is accessible by attempting a request to its URL.
            If the server is unreachable, this test will be skipped with a descriptive message.

        Raises
        ------------
            unittest.SkipTest
                When the Searxng server is not reachable at http://localhost:8080
        """
        error_message = "Searxng server not accessible at http://localhost:8080"
        # Verify Searxng server is accessible before running tests
        try:
            # Try to get a response from Searxng server using requests
            response = requests.get(self.test_url, timeout=5)
            # If don't get success status code, print error message
            self.assertTrue(response.status_code == 200, error_message)
        # If we get connection error, skip the test
        except requests.exceptions.ConnectionError:
            self.skipTest(error_message)


    ## Test initializing client
    # Can run this test 1st because client will need to be initialized
    # for every other test
    @pytest.mark.order(1)
    def test_client_init(self):
        """
        Test that SearxngClient can be initialized successfully.

        This ensures that the `SearxngClient` class can be instantiated correctly with a given URL.

        Verifications
        ------------
            SearxngClient object is not None
            URL matches the expected value
            Internal SearxSearchWrapper (LangChain) has been created
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        try:
            client = SearxngClient(url=self.test_url)
            self.assertIsNotNone(client)
            self.assertEqual(client.url, self.test_url)
            self.assertIsInstance(client.client, SearxSearchWrapper)
        except Exception as e:
            self.fail(f"Failed to initialize SearxngClient: {e}")

    
    ## Test client initialization for unreachable URL
    def test_client_init_bad_url(self):
        """
        Test error handling when the SearxngClient is passed an unreachable URL.

        Verifications
        ------------
            Initializing the SearxngClient raises an exception when passed a bad URL
            Exception is propagated correctly
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        url = 'https://badurl'
        with self.assertRaises(requests.exceptions.RequestException):
            client = SearxngClient(url=url)  


    #///////////////////////////////////////////////////////////#
    ### Generic test runners ///////////////////////////////////#
    # Test basic response
    def _test_method_basic(self, method_name):
        """
        Test basic functionality of getting response.

        Verifications
        ------------
            Output: 
                string for `requests_search`, 
                string or dictionary for `run`, 
                list of dictionaries for `results` 
            Length of output is greater than zero
            Each item in response is dictionary for `results`
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        client = SearxngClient(url=self.test_url)
        try:
            method = getattr(client, method_name)
            response = method(query=self.test_query)

            # Test response type
            if method_name=='requests_search':
                self.assertIsInstance(response, str)
            elif method_name=='run':
                self.assertIsInstance(response, (str, dict))
            else:
                self.assertIsInstance(response, list)

            # Test response length
            self.assertGreater(len(response), 0)

            # Test items type in response
            if method_name=='results':
                self.assertTrue(all(isinstance(item, dict) for item in response))

        except Exception as e:
            self.fail(f"Failed to get response: {e}")

    ## Test response with different query
    def _test_method_diff_query(self, method_name):
        """
        Test basic functionality of getting results with a different query from the default.

        Verifications
        ------------
            Output: 
                string for `requests_search`, 
                string or dictionary for `run`, 
                list of dictionaries for `results` 
            Length of output is greater than zero
            Each item in response is dictionary for `results`
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        query = 'Integration tests software development'
        client = SearxngClient(url=self.test_url)
        try:
            method = getattr(client, method_name)
            response = method(query=query)
            
            # Test response type
            if method_name=='requests_search':
                self.assertIsInstance(response, str)
            elif method_name=='run':
                self.assertIsInstance(response, (str, dict))
            else:
                self.assertIsInstance(response, list)

            # Test response length
            self.assertGreater(len(response), 0)

            # Test items type in response
            if method_name=='results':
                self.assertTrue(all(isinstance(item, dict) for item in response))

        except Exception as e:
            self.fail(f"Failed to get response: {e}")

    ## Test response with empty query
    def _test_method_no_query(self, method_name):
        """
        Test error handling of method with an empty query.

        Verifications
        ------------
            Invoking the method with an empty string raises an exception
            Exception is propagated correctly
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        query = ''
        client = SearxngClient(url=self.test_url)
        with self.assertRaises(ValueError):
            method = getattr(client, method_name)
            response = method(query=query)

    ## Test response with an incorrect query type 
    def _test_method_bad_query_type(self, method_name):
        """
        Test error handling of method when the query type is not a string.

        Verifications
        ------------
            Invoking the method raises an exception when passed an incorrect query type
            Exception is propagated correctly
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        client = SearxngClient(url=self.test_url)
        ## Define various invalid query types
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
        
        ## Run through each query
        for query, description in invalid_queries:
            with self.subTest(query_type=description):
                with self.assertRaises(TypeError):
                    method = getattr(client, method_name)
                    response = method(query=query)

    ## Test method for multiple queries to the same client
    def _test_method_multiple(self, method_name):
        """
        Test multiple sequential queries to ensure client reusability.

        Verifications
        ------------
            Output: 
                string for `requests_search`, 
                string or dictionary for `run`, 
                list of dictionaries for `results` 
            Length of output is greater than zero
            Each item in response is dictionary for `results`
            Length of the total number of responses is equal to three (for three messages)
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        client = SearxngClient(url=self.test_url)
        responses = []
        for i in range(3):
            try:
                method = getattr(client, method_name)
                response = method(query=query)
                responses.append(response)

                # Test response type
                if method_name=='requests_search':
                    self.assertIsInstance(response, str)
                elif method_name=='run':
                    self.assertIsInstance(response, (str, dict))
                else:
                    self.assertIsInstance(response, list)

                # Test response length
                self.assertGreater(len(response), 0)

                # Test items type in response
                if method_name=='results':
                    self.assertTrue(all(isinstance(item, dict) for item in response))

            except Exception as e:
                self.fail(f"Failed request {i}: Type: {type(response)} {e}")

        # Want to make sure valid response was appended for each message
        self.assertEqual(len(responses), 3)
    

    #//////////////////////////////////////////////////////////#
    ### Testing requests //////////////////////////////////////#
    ## Test getting results from Requests with default message
    def test_get_requests_basic(self):
        """
        Test basic functionality of getting results from Requests.

        Validates that the `requests_search` method correctly returns a string response given a query.

        Verifications
        ------------
            Output is a string
            Length of output is greater than zero
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        self._test_method_basic(method_name='requests_search')

    ## Test getting results from Requests with different query
    def test_get_requests_diff_query(self):
        """
        Test basic functionality of getting results from Requests with a different query from the default.

        Validates that the `requests_search` method correctly returns a string response given a query.

        Verifications
        ------------
            Output is a string
            Length of output is greater than zero
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        self._test_method_diff_query(method_name='requests_search')

    ## Test getting results from Requests with empty query
    def test_get_requests_no_query(self):
        """
        Test basic functionality of getting results from Requests with an empty query.

        Validates that the `requests_search` method correctly returns a string response given a query.

        Verifications
        ------------
            Invoking the `run` method with an empty string raises an exception
            Exception is propagated correctly
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        self._test_method_no_query(method_name='requests_search')

    ## Test getting results from Requests with an incorrect query type 
    def test_get_requests_bad_query_type(self):
        """
        Test error handling of the `requests_search` method when the query type is not a string.

        Verifications
        ------------
            Invoking the `requests_search` method raises an exception when passed an incorrect query type
            Exception is propagated correctly
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        self._test_method_bad_query_type(method_name='requests_search')

    ## Test getting results from Requests for multiple queries to the same client
    def test_get_requests_multiple(self):
        """
        Test multiple sequential queries with Requests to ensure client reusability.

        Validates that the same `SearxngClient` instance can make several calls with Requests without issues.

        Verifications
        ------------
            Response for each message is a string
            Length of response for each message is greater than zero
            Length of the total number of responses is equal to three (for three messages)
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        self._test_method_multiple(method_name='requests_search')


    #//////////////////////////////////////////////////////////#
    ### Testing LangChain run /////////////////////////////////#
    ## Test getting results from `run` method with default message
    def test_get_run_basic(self):
        """
        Test basic functionality of getting results from LangChain's SearxSearchWrapper.

        Validates that the `run` method correctly returns a string or dictionary response given a query.

        Verifications
        ------------
            Output is a string or dictionary
            Length of output is greater than zero
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        self._test_method_basic(method_name='run')

    ## Test getting results from `run` method with different query
    def test_get_run_diff_query(self):
        """
        Test basic functionality of getting results from LangChain's SearxSearchWrapper with a different query from the default.

        Validates that the `run` method correctly returns a string or dictionary response given a query.

        Verifications
        ------------
            Output is a string or dictionary
            Length of output is greater than zero
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        self._test_method_diff_query(method_name='run')

    ## Test getting results from `run` method with empty query
    def test_get_run_no_query(self):
        """
        Test basic functionality of getting results from LangChain's SearxSearchWrapper with an empty query.

        Validates that the `run` method correctly returns a string or dictionary response given a query.

        Verifications
        ------------
            Invoking the `run` method with an empty string raises an exception
            Exception is propagated correctly
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        self._test_method_no_query(method_name='run')

    ## Test getting results from `run` method with an incorrect query type 
    def test_get_run_bad_query_type(self):
        """
        Test error handling of the `run` method when the query type is not a string.

        Verifications
        ------------
            Invoking the `run` method raises an exception when passed an incorrect query type
            Exception is propagated correctly
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        self._test_method_bad_query_type(method_name='run')

    ## Test getting results from `run` method for multiple queries to the same client
    def test_get_run_multiple(self):
        """
        Test multiple sequential queries with Langchain's SearxSearchWrapper to ensure client reusability.

        Validates that the same `SearxngClient` instance can make several calls with the `run` method without issues.

        Verifications
        ------------
            Response for each message is a string or dictionary
            Length of response for each message is greater than zero
            Length of the total number of responses is equal to three (for three messages)
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        self._test_method_multiple(method_name='run')


    #//////////////////////////////////////////////////////////#
    ### Testing LangChain results /////////////////////////////#
    ## Test getting results from `results` method with default message
    def test_get_results_basic(self):
        """
        Test basic functionality of getting results from LangChain's SearxSearchWrapper.

        Validates that the `results` method correctly returns a list of dictionaries response given a query.

        Verifications
        ------------
            Response is a list
            Length of response is greater than zero
            Each item in response is a dictionary
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        self._test_method_basic(method_name='results')

    ## Test getting results from `results` method with different query
    def test_get_results_diff_query(self):
        """
        Test basic functionality of getting results from LangChain's SearxSearchWrapper with a different query from the default.

        Validates that the `results` method correctly returns a list of dictionaries response given a query.

        Verifications
        ------------
            Response is a list
            Length of response is greater than zero
            Each item in response is a dictionary
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        self._test_method_diff_query(method_name='run')

    ## Test getting results from `results` method with empty query
    def test_get_results_no_query(self):
        """
        Test basic functionality of getting results from LangChain's SearxSearchWrapper with an empty query.

        Validates that the `results` method correctly returns a list of dictionaries response given a query.

        Verifications
        ------------
            Invoking the `run` method with an empty string raises an exception
            Exception is propagated correctly
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        self._test_method_no_query(method_name='results')

    ## Test getting results from `results` method with an incorrect query type 
    def test_get_results_bad_query_type(self):
        """
        Test error handling of the `results` method when the query type is not a string.

        Verifications
        ------------
            Invoking the `results` method raises an exception when passed an incorrect query type
            Exception is propagated correctly
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        self._test_method_bad_query_type(method_name='requests_search')

    ## Test getting results from `results` method for multiple queries to the same client
    def test_get_results_multiple(self):
        """
        Test multiple sequential queries with Langchain's SearxSearchWrapper to ensure client reusability.

        Validates that the same `SearxngClient` instance can make several calls with the `results` method without issues.

        Verifications
        ------------
            Response for each message is a list
            Length of response for each message is greater than zero
            Each item in response for each message is a dictionary
            Length of the total number of responses is equal to three (for three messages)
        
        Raises
        ------------
            Exception: 
                If any verifications fail
        """
        self._test_method_multiple(method_name='results')


    ## Tear down after finishing each test
    def tearDown(self):
        """
        Clean up after each test method.

        Currently performs no actions but serves as a placeholder for future cleanup logic.
        """
        # Nothing special to clean up for this test
        pass

    ## Tear down after finishing all tests
    @classmethod
    def tearDownClass(cls):
        """
        Clean up class-level fixtures.

        Currently performs no actions but serves as a placeholder for any global cleanup needed.
        """
        # Nothing special to clean up for this class
        pass
### tests/test_unit_logger.py
## Defines unit tests for methods in ./pyfiles/logger.py

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

## Imports
# Third-party modules
from unittest import TestCase
from unittest.mock import (
    call, 
    patch, 
    MagicMock
)
from datetime import datetime
from logging import Formatter, LogRecord
from rich.progress import Progress

# Internal modules
from pyfiles.logger import ElapsedFormatter, with_spinner


## Now let's test everything
class TestLoggerUnit(TestCase):
    """
    Unit tests for `pyfiles.logger`.
    
    This test suite contains unit tests for the `ElapsedFormatter` class and `with_spinner` method of `pyfiles.logger`, covering:

        - Class initialization
        - Method invoking

    All tests use mocking to isolate the class under test from external dependencies.
    """

    ## Test failed invoking of format
    def test_format_failure(self):
        """
        Test failed invoking of format.
        
        Verifications
        ------------
            Invoking the method raises an exception when a failure is introduced.
            Exception is propagated correctly.

        Mocks
        ------------
            `LogRecord` is mocked and returns a mock instance.
            `Formatter` is mocked and returns a mock instance.
        
        Asserts
        ------------
            Exception is raised when the `format` method fails.
        """
        ## Arrange
        # LogRecord | Create a mock instance of the record for the formatter
        record = MagicMock(spec=LogRecord)
        # Formatter | Create a mock instance of the Formatter parent class
        mock_formatter = MagicMock(spec=Formatter)
        mock_formatter.format.side_effect = Exception

        ## Act
        formatter = ElapsedFormatter(start_time=datetime.now())

        ## Assert
        with self.assertRaises(Exception):
            formatter.format(record)


    ## Test failure of spinner
    def test_with_spinner_failure(self):
        """
        Test failed invoking of spinner.
        
        Verifications
        ------------
            Invoking the method raises an exception when a failure is introduced.
            Exception is propagated correctly.

        Mocks
        ------------
            `pyfiles.logger.logger` is mocked and returns a mock instance.
            `Progress` is mocked and returns a mock instance.
        
        Asserts
        ------------
            Exception is raised when the `with_spinner` method fails.
        """
        ## Arrange
        description = "Test task"
        # logger | Create a mock instance of the logger
        mock_logger = MagicMock()
        with patch("pyfiles.logger.logger", mock_logger):
            # Progress | Create a mock instance of the Progress class
            mock_progress_cls = MagicMock()
            mock_progress_instance = MagicMock()
            mock_progress_cls.return_value.__enter__.return_value = mock_progress_instance
            mock_progress_instance.add_task.side_effect = Exception("spinner error")

            ## Act and assert
            with patch("pyfiles.logger.Progress", mock_progress_cls):
                with self.assertRaises(Exception):
                    with with_spinner(description):
                        pass
# ------------------------------------------------------------------
# This file contains pytest fixtures (test configurations). It consists of fixtures that are to be used across multiple test files.
# These fixtures are automatically discovered by pytest and can be used in any test file without explicit import.
# 
# A fixture is the ready-made setup (or known-correct example) a test uses, so it need not be built fresh every time.
# ------------------------------------------------------------------

import pytest

@pytest.fixture
def config_data():
    return {
        "startDay": "2022-02-01",
        "endDay": "2022-05-31",
        "useCustomLogs": "tests/testdata/raw_logs_valid.txt",
    }


"""An invalid --output value must be rejected by argparse, not crash later."""
import sys
from unittest import mock

import pytest

import __init__ as ga


def test_invalid_output_rejected_at_parse_time():
    with mock.patch.object(sys, "argv", ["prog", "--output", "bogus"]):
        with pytest.raises(SystemExit) as excinfo:
            ga.create_arguments()
    assert excinfo.value.code == 2


def test_valid_output_values_still_parse():
    for value in ("terminal", "html"):
        with mock.patch.object(sys, "argv", ["prog", "--output", value]):
            args = ga.create_arguments()
            assert args.output == value

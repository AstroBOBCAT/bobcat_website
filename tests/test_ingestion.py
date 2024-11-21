import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), "..")) # this seems to be the only one that actually works


import pytest
from ingest_utils import *

def test_create_url():
    key = "abc"
    url = create_url(key)
    assert url == "https://docs.google.com/spreadsheet/ccc?key=abc&output=csv"


def test_create_url_error():
    key = 3
    with pytest.raises(TypeError) as excinfo:
        create_url(key)
    assert str(excinfo.value) == "key must be a string"
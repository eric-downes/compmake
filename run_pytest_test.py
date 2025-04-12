#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to run a single pytest test file.
"""

import os
import sys
import pytest

# Add the source directory to sys.path
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, src_dir)

if __name__ == "__main__":
    # Run the test_blocked_pytest.py file
    test_path = os.path.join('src', 'compmake', 'unittests', 'test_blocked_pytest.py')
    result = pytest.main(["-v", test_path])
    sys.exit(result)
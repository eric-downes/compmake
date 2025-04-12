#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Script to run pytest tests during migration without interfering with nose.

This script:
1. Temporarily replaces the __init__.py with a pytest-friendly version
2. Sets up the proper Python path for imports
3. Runs specified test(s) with pytest
4. Restores the original __init__.py

Usage:
    python run_pytest_test.py [test_path]

Arguments:
    test_path - Optional path to specific test file or directory to test
                Default: src/compmake/unittests/test_blocked_pytest.py
Examples:
    python run_pytest_test.py
    python run_pytest_test.py src/compmake/unittests/test_dynamic_1_pytest.py
"""

import os
import sys
import pytest
import shutil
import atexit

# Directory paths
root_dir = os.path.dirname(os.path.abspath(__file__))
src_dir = os.path.join(root_dir, 'src')
test_dir = os.path.join(src_dir, 'compmake', 'unittests')

# Add the source directory to sys.path
sys.path.insert(0, src_dir)

# File paths for __init__.py swapping
init_path = os.path.join(test_dir, '__init__.py')
init_nose_path = os.path.join(test_dir, '__init__.py.nose')  
init_pytest_path = os.path.join(test_dir, '__init__.py.pytest')
init_backup_path = os.path.join(test_dir, '__init__.py.backup')

def swap_init_files():
    """Swap the __init__.py file to use the pytest-friendly version."""
    # Backup current __init__.py if it doesn't already have a backup
    if not os.path.exists(init_backup_path) and os.path.exists(init_path):
        shutil.copy2(init_path, init_backup_path)
        print(f"Backed up original __init__.py to {init_backup_path}")
        
    # Install pytest version
    if os.path.exists(init_pytest_path):
        shutil.copy2(init_pytest_path, init_path)
        print(f"Installed pytest-friendly __init__.py")
    else:
        print(f"Warning: Could not find {init_pytest_path}")

def restore_init_files():
    """Restore the original __init__.py file."""
    if os.path.exists(init_backup_path):
        shutil.copy2(init_backup_path, init_path)
        print(f"Restored original __init__.py")
        os.remove(init_backup_path)
    else:
        print(f"Warning: No backup found at {init_backup_path}, could not restore")

# Register cleanup function to always restore files
atexit.register(restore_init_files)

if __name__ == "__main__":
    # Default test path
    test_path = os.path.join('src', 'compmake', 'unittests', 'test_blocked_pytest.py')
    
    # Allow command-line override
    if len(sys.argv) > 1:
        test_path = sys.argv[1]
    
    # Ensure test_path is a path relative to the root directory
    if os.path.isabs(test_path):
        test_path = os.path.relpath(test_path, root_dir)
    
    print(f"Running pytest on: {test_path}")
    
    # Swap init files before running tests
    swap_init_files()
    
    try:
        # Run the test(s)
        result = pytest.main(["-v", test_path])
        sys.exit(result)
    except Exception as e:
        print(f"Error running tests: {e}")
        sys.exit(1)
    finally:
        # restore_init_files() will be called by atexit
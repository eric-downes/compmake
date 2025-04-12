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
        print(f"Removed backup file")
    else:
        # This happens when the function is called twice (by sys.exit and by atexit)
        # So we just silently ignore it
        pass

# Register cleanup function to always restore files
atexit.register(restore_init_files)

if __name__ == "__main__":
    # Default: run all pytest tests individually
    if len(sys.argv) > 1:
        # Allow command-line override for specific test
        test_path = sys.argv[1]
        
        # Ensure test_path is a path relative to the root directory
        if os.path.isabs(test_path):
            test_path = os.path.relpath(test_path, root_dir)
            
        # Run the specific test
        print(f"Running pytest on: {test_path}")
        
        # Swap init files before running tests
        swap_init_files()
        
        try:
            # Run the test
            result = pytest.main(["-v", test_path])
            sys.exit(result)
        except Exception as e:
            print(f"Error running tests: {e}")
            sys.exit(1)
        finally:
            # This empty block is intentional
            # restore_init_files() will be called by atexit
            pass
    else:
        # Run all _pytest.py files in the unittests directory
        import glob
        
        # Get all pytest test files
        test_dir = os.path.join(src_dir, 'compmake', 'unittests')
        test_files = glob.glob(os.path.join(test_dir, '*_pytest.py'))
        
        if not test_files:
            print("No pytest files found in", test_dir)
            sys.exit(1)
        
        # Sort the files to ensure consistent execution order
        test_files.sort()
        
        print(f"Found {len(test_files)} pytest files to run")
        
        # Convert to paths relative to root directory
        test_files = [os.path.relpath(f, root_dir) for f in test_files]
        
        # Swap init files before running tests
        swap_init_files()
        
        try:
            # Run the tests one by one
            failed = []
            for test_file in test_files:
                print(f"\nRunning pytest on: {test_file}")
                result = pytest.main(["-v", test_file])
                if result != 0:
                    failed.append(test_file)
            
            # Report results
            if failed:
                print(f"\nFAILED TESTS ({len(failed)}/{len(test_files)}):")
                for test in failed:
                    print(f"  - {test}")
                sys.exit(1)
            else:
                print(f"\nAll {len(test_files)} tests passed!")
                sys.exit(0)
        except Exception as e:
            print(f"Error running tests: {e}")
            sys.exit(1)
        finally:
            # This empty block is intentional
            # restore_init_files() will be called by atexit
            pass
# Migrating from nose to pytest: A Practical Guide

## Introduction

This guide documents the process of migrating a Python project's test suite from the now-unmaintained nose framework to pytest. As of Python 3.12, nose is no longer compatible due to its dependency on the removed `imp` module and other deprecated features. This guide captures lessons learned during the migration of compmake's test suite, but the principles can be applied to any project.

## Quick Start: Running Tests During Migration

To run tests during migration without breaking existing code, we recommend creating a dedicated test runner script (e.g., `run_pytest_test.py`):

```python
#!/usr/bin/env python
import os
import sys
import pytest

# Add source directory to path
src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
sys.path.insert(0, src_dir)

if __name__ == "__main__":
    # Run a specific test file or directory
    test_path = os.path.join('src', 'path', 'to', 'test_file.py')
    result = pytest.main(["-v", test_path])
    sys.exit(result)
```

This approach:
1. Allows you to run converted tests independently of nose
2. Avoids import conflicts between nose and pytest
3. Provides a consistent test environment during migration
4. Lets you verify each conversion without affecting other tests

## Why Migrate to pytest?

- **Maintainability**: nose is no longer maintained, and pytest is the most actively maintained Python testing framework
- **Python compatibility**: nose doesn't work with Python 3.12 and has compatibility issues with newer Python versions
- **Better features**: pytest provides powerful fixtures, parameterization, and plugin ecosystem
- **Improved readability**: pytest's assertion system is more readable (using plain `assert` statements)
- **Better parallel execution**: pytest has better support for running tests in parallel

## Migration Process Overview

1. **Preparation**: Create infrastructure for pytest
2. **Conversion**: Convert tests file by file
3. **Compatibility**: Address any compatibility issues discovered during migration
4. **Testing**: Ensure converted tests work properly
5. **Integration**: Replace original tests with pytest versions
6. **Cleanup**: Remove nose-specific code and dependencies

## Step 1: Preparation

### 1.1 Create Basic pytest Infrastructure

Create these basic files to set up pytest:

#### `pytest.ini` (in project root)

```ini
[pytest]
testpaths = path/to/tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

#### `conftest.py` (in test directory)

```python
# -*- coding: utf-8 -*-
import pytest

# Add shared fixtures here if needed
```

### 1.2 Create a Base Test Class

If your project uses a common base test class, convert it to use pytest fixtures:

```python
# -*- coding: utf-8 -*-
import pytest
from shutil import rmtree
from tempfile import mkdtemp

class BaseTestClass:
    """Base class for pytest-based tests."""
    
    @pytest.fixture(autouse=True)
    def setup_teardown(self):
        """Setup and teardown for each test."""
        # Setup code here
        self.temp_dir = mkdtemp()
        
        yield  # This is where the test will run
        
        # Teardown code here
        rmtree(self.temp_dir)
        
    # Helper methods used by multiple tests
    def helper_method(self):
        pass
```

### 1.3 Add pytest to Requirements

Update your requirements file to include pytest:

```
pytest>=7.0.0
```

### 1.4 Create a Migration Tracking Document

Create a document to track migration progress:

```markdown
# Migration Tracking

| Test File | Converted | Pytest File | Working | Notes |
|-----------|-----------|-------------|---------|-------|
| test_1.py | ✅ Done | test_1_pytest.py | ✅ Passing | - |
| test_2.py | 🔄 Not Started | - | - | - |
```

## Step 2: Converting Tests

### 2.1 Basic Changes for Each Test

For each test file:

1. Replace nose-specific imports with pytest
2. Convert class-based tests to use pytest fixtures
3. Replace nose assertions with pytest assertions
4. Rename test methods to follow pytest conventions (test_*)

#### Example Conversion

**Original nose test:**
```python
# -*- coding: utf-8 -*-
from nose.tools import istest
from myproject.base_test import BaseTest

@istest
class TestFeature(BaseTest):
    def setUp(self):
        super(TestFeature, self).setUp()
        self.specific_setup()
        
    def test_some_functionality(self):
        result = self.run_function()
        self.assertEqual(result, expected_value)
        self.assertTrue(condition)
```

**Converted pytest test:**
```python
# -*- coding: utf-8 -*-
import pytest
from myproject.pytest_base import BaseTestClass

class TestFeature(BaseTestClass):
    def specific_setup(self):
        # Specific setup code
        pass
        
    @pytest.fixture(autouse=True)
    def setup(self, setup_teardown):
        self.specific_setup()
        
    def test_some_functionality(self):
        result = self.run_function()
        assert result == expected_value
        assert condition
```

### 2.2 Handling Test Discovery

pytest and nose discover tests differently. If you encounter issues:

- Change test classes to start with `Test`
- Change test methods to start with `test_`
- Remove nose-specific `__init__.py` files

## Step 3: Addressing Compatibility Issues

During migration, you may encounter Python compatibility issues beyond the nose framework itself.

### 3.1 Common Issues

#### Removed Modules and Functions

- **Issue**: Removed modules like `imp` or functions like `time.clock()`
- **Solution**: Create compatibility layers that provide alternatives based on Python version

Example compatibility layer for `time.clock()`:

```python
# -*- coding: utf-8 -*-
import time

# time.clock() was removed in Python 3.8, use time.perf_counter() instead
if hasattr(time, 'perf_counter'):
    # Python 3.3+
    def get_cpu_time():
        return time.perf_counter()
elif hasattr(time, 'clock'):
    # Python 2.x and early Python 3.x
    def get_cpu_time():
        return time.clock()
else:
    # Fallback to time.time() if neither is available
    def get_cpu_time():
        return time.time()
```

#### Circular Import Issues

- **Issue**: Test discovery in `__init__.py` causes circular imports with nose
- **Solution**: Create a clean `__init__.py` for pytest that doesn't import test modules

#### Multiprocessing Issues in Python 3.12

- **Issue**: Python 3.12 made changes to the multiprocessing module that can cause errors with existing code
- **Solution**: 
  - For test purposes, you may need to temporarily switch from parallel to sequential execution
  - For permanent fixes, review the Python 3.12 multiprocessing module changes and update code accordingly
  - Watch for KeyError exceptions in resource tracking or memory-shared dictionaries

### 3.2 Running Tests Standalone

Create a way to run individual tests without depending on the test discovery system:

```python
if __name__ == "__main__":
    # Run this specific test file directly
    pytest.main(["-xvs", __file__])
```

## Step 4: Testing the Migration

Test your migration as you go:

1. Test individual files first:
   ```bash
   python -m pytest path/to/test_file.py -v
   ```

2. Test groups of related tests next:
   ```bash
   python -m pytest path/to/test_dir -v
   ```

3. Run the full test suite at the end:
   ```bash
   python -m pytest
   ```

## Step 5: Final Integration

Once all tests have been migrated and verified:

1. Remove nose from requirements
2. Clean up any remaining nose-specific code or imports
3. Update CI/CD pipelines to use pytest

## Common Conversions

| nose | pytest |
|------|--------|
| `from nose.tools import istest` | Use name convention `class Test*` |
| `from nose.tools import raises` | `with pytest.raises(Exception):` |
| `self.assertEqual(a, b)` | `assert a == b` |
| `self.assertNotEqual(a, b)` | `assert a != b` |
| `self.assertTrue(x)` | `assert x` |
| `self.assertFalse(x)` | `assert not x` |
| `self.assertRaises(ExcType, func, *args)` | `with pytest.raises(ExcType): func(*args)` |
| `@nose.tools.raises(ExcType)` | `@pytest.mark.xfail(raises=ExcType)` |
| `setUp()` | `@pytest.fixture(autouse=True)` |
| `tearDown()` | Yield fixture teardown |

## Examples from Our Migration

### Basic Test Conversion

**Original nose test:**
```python
from nose.tools import istest
from .compmake_test import CompmakeTest

def job_success(*args, **kwargs):
    pass

def job_failure(*args, **kwargs):
    raise ValueError('This job fails')

@istest
class TestBlocked(CompmakeTest):
    def mySetUp(self):
        pass

    def testAdding(self):
        comp = self.comp
        A = comp(job_success, job_id='A')
        B = comp(job_failure, A, job_id='B')
        comp(job_success, B, job_id='C')
        
        def run():
            self.cc.batch_command('make')
        self.assertMakeFailed(run, nfailed=1, nblocked=1)
```

**Converted pytest test:**
```python
import pytest
from .pytest_base import CompmakeTestBase

def job_success(*args, **kwargs):
    pass

def job_failure(*args, **kwargs):
    raise ValueError('This job fails')

class TestBlocked(CompmakeTestBase):
    def mySetUp(self):
        pass

    def test_adding(self):
        comp = self.comp
        A = comp(job_success, job_id='A')
        B = comp(job_failure, A, job_id='B')
        comp(job_success, B, job_id='C')
        
        def run():
            self.cc.batch_command('make')
        self.assertMakeFailed(run, nfailed=1, nblocked=1)
```

### Compatibility Layer Example 

When we found code using the removed `time.clock()` function, we created a compatibility layer:

```python
# -*- coding: utf-8 -*-
import time

# time.clock() was removed in Python 3.8, use time.perf_counter() instead
if hasattr(time, 'perf_counter'):
    # Python 3.3+
    def get_cpu_time():
        return time.perf_counter()
elif hasattr(time, 'clock'):
    # Python 2.x and early Python 3.x
    def get_cpu_time():
        return time.clock()
else:
    # Fallback to time.time() if neither is available
    def get_cpu_time():
        return time.time()
```

## Conclusion

Migrating from nose to pytest is a methodical process that can be done incrementally. The migration not only improves test maintainability but also uncovers and addresses potential compatibility issues in your codebase. This guide will be updated as we continue our migration journey.

---

*This guide is a work in progress and will be updated as we learn more during our migration process.*
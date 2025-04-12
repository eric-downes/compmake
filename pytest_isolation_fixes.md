# Fixing Test Isolation Issues in Compmake Pytest Tests

This document explains the fixes applied to address test isolation issues in the pytest-converted tests.

## Overview of Issues

When running all tests together, several test files failed that worked when run individually:

1. `test_dynamic_5_pytest.py`
2. `test_dynamic_6_pytest.py`
3. `test_dynamic_failure_pytest.py`
4. `test_old_jobs_pytest.py`
5. `test_plugins_pytest.py`

These failures were primarily due to:

- Shared state between tests through class variables
- File system operations without proper cleanup
- Use of global configuration settings
- Shared database paths between tests
- Lambda function pickling errors

## Improved Base Test Class

The `improved_pytest_base.py` file contains an enhanced version of `CompmakeTestBase` with:

1. Better temporary directory handling using pytest's `tmp_path` fixture
2. Unique test identifiers for each test run
3. Configuration state preservation
4. Improved teardown processes to clean up resources
5. Child process termination

## Key Fixes Applied

### 1. Replacing Class Variables with Function Parameters

**Before**:
```python
class TestDynamicFailure(CompmakeTestBase):
    do_fail = False

    def test_dynamic_failure1(self):
        TestDynamicFailure.do_fail = ValueError
        # test code...
```

**After**:
```python
def fd(context, do_fail=None):
    # Use parameter instead of class variable
    if do_fail is not None:
        raise do_fail()
    # rest of function...

def test_dynamic_failure1(self):
    # Pass parameter directly
    mockup8(self.cc, do_fail=ValueError)
    # test code...
```

### 2. Using Isolated Directories for Each Test

**Before**:
```python
root = mkdtemp()
# Use the same directory for multiple test phases
```

**After**:
```python
def test_cleaning2(self, tmp_path):
    # Use a unique path for each test
    root = os.path.join(str(tmp_path), "test_cleaning2")
    os.makedirs(root, exist_ok=True)
    # test code...
```

### 3. Managing Configuration State

**Before**:
```python
# Modify global config
set_compmake_config('check_params', True)
# No restoration of original value
```

**After**:
```python
@pytest.fixture(autouse=True)
def save_config(self):
    # Save original config
    original_check_params = set_compmake_config('check_params')
    # Set for this test
    set_compmake_config('check_params', True)
    yield
    # Restore after test
    set_compmake_config('check_params', original_check_params)
```

### 4. Creating Fresh Contexts Between Test Phases

**Before**:
```python
# Modifying the same database for different test phases
self.db = StorageFilesystem(self.root, compress=True)
self.cc = Context(db=self.db)
```

**After**:
```python
# Create a fresh context for the second part to ensure isolation
test_dir2 = os.path.join(str(tmp_path), "test_dynamic6_2")
os.makedirs(test_dir2, exist_ok=True)
self.db = StorageFilesystem(test_dir2, compress=True)
self.cc = Context(db=self.db)
```

### 5. Avoiding Lambda Functions in Dynamic Contexts

**Before**:
```python
# This causes pickling errors
context.comp_dynamic(lambda ctx: fd(ctx, do_fail))
```

**After**:
```python
# Use a named function instead
def fd_wrapper(context):
    test_class = TestDynamicFailure.current_test
    # The rest of the function...

# Call the named function
context.comp_dynamic(fd_wrapper)
```

## Implementing the Fixes

To implement these fixes:

1. Add the `improved_pytest_base.py` file to the project
2. Migrate to the fixed versions of failing tests:
   - `test_dynamic_5_pytest_fixed.py`
   - `test_dynamic_6_pytest_fixed.py`
   - `test_dynamic_failure_pytest_fixed.py`
   - `test_old_jobs_pytest_fixed.py`
   - `test_plugins_pytest_fixed.py`

Or gradually update the existing files with the fixes shown in these examples.

## General Best Practices for Test Isolation

When writing or converting tests:

1. Never use class variables to share state between tests
2. Always use fresh, isolated directories for each test
3. Use pytest fixtures to set up and tear down resources
4. Save and restore any global state you modify
5. Use `pytest.raises()` instead of trying to catch exceptions manually
6. Create unique contexts for different test phases
7. Clean up resources in teardown, even if tests fail

By following these practices, tests will run successfully both individually and in batch mode.
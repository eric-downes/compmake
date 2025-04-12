# Test Isolation Fixes in Compmake Pytest Migration

This document explains the test isolation fixes that were applied during the pytest migration, which are now part of the final test suite.

## Overview of Issues Addressed

During the migration, we discovered that several test files would pass when run individually but fail when run as part of the full test suite:

1. `test_dynamic_5.py`
2. `test_dynamic_6.py`
3. `test_dynamic_failure.py`
4. `test_old_jobs.py`
5. `test_plugins.py`

These failures were primarily due to:

- Shared state between tests through class variables
- File system operations without proper cleanup
- Use of global configuration settings without restoration
- Shared database paths between tests
- Lambda function pickling errors in multiprocessing contexts

The fixes we implemented are now part of our standard test patterns and should be followed when writing new tests.

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

## Implementation Status

These fixes have now been fully incorporated into our test suite:

1. The `improved_pytest_base.py` patterns are used throughout the test suite
2. All previously failing tests have been fixed and integrated:
   - `test_dynamic_5.py`
   - `test_dynamic_6.py`
   - `test_dynamic_failure.py`
   - `test_old_jobs.py`
   - `test_plugins.py`

All tests now run successfully both individually and as part of the full test suite.

## Best Practices for Future Test Development

Based on our experience, these best practices should be followed when writing new tests or updating existing ones:

1. **Never use class variables for test state**
   - Class variables can cause state to leak between tests
   - Use instance variables or parameters instead

2. **Use isolated directories for each test**
   - Use pytest's `tmp_path` fixture to create unique directories
   - Example: `root = os.path.join(str(tmp_path), "test_name")`

3. **Manage configuration state properly**
   - Save original values before modifying
   - Restore values in teardown using fixtures
   - Use a fixture with `yield` to ensure restoration even if the test fails

4. **Create fresh contexts for different test phases**
   - Don't reuse database connections between test phases
   - Create new contexts with new directories for different phases

5. **Avoid lambda functions in serialized contexts**
   - Use named functions instead of lambdas in any code that might be pickled
   - Be careful with closures capturing local variables

6. **Use pytest's assertions and fixtures**
   - Use `pytest.raises()` instead of try/except blocks
   - Use pytest fixtures for setup/teardown logic

7. **Clean up resources properly**
   - Ensure cleanup happens even if tests fail
   - Use `with` statements or teardown fixtures

By following these practices, you'll avoid subtle test isolation issues and create more reliable test suites that can run both individually and as part of larger test runs.
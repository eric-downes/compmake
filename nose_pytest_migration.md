# Migrating compmake tests from nose to pytest

## Background

Currently, compmake's test suite uses the nose testing framework, which is no longer maintained and has compatibility issues with Python 3.12, specifically:

```
ModuleNotFoundError: No module named 'imp'
```

This is because nose depends on the deprecated `imp` module which was completely removed in Python 3.12.

## Migration Plan

This document outlines a comprehensive plan to migrate compmake's test suite from nose to pytest.

### 1. Understanding the Current Test Structure

The test suite uses:
- `unittest.TestCase` as the base class
- `@istest` from nose to mark test classes
- Custom assertion methods in `CompmakeTest`
- `nose.tools` for test decorators and assertions
- Test classes with `mySetUp()` rather than standard `setUp()`

### 2. Migration Steps

#### Step 1: Create a pytest equivalent of CompmakeTest

First, we'll create a pytest-compatible base class:

```python
# src/compmake/unittests/pytest_base.py
import os
import pytest
from shutil import rmtree
from tempfile import mkdtemp

from compmake import set_compmake_config, logger
from compmake.context import Context
from compmake.exceptions import CommandFailed, MakeFailed
from compmake.jobs import get_job, parse_job_list
from compmake.scripts.master import compmake_main
from compmake.storage import StorageFilesystem
from compmake.structures import Job
from contracts import contract

class CompmakeTestBase:
    """Base class for pytest-based compmake tests."""
    
    @pytest.fixture(autouse=True)
    def setup_method(self):
        """Setup method that runs before each test method."""
        self.root0 = mkdtemp()
        self.root = os.path.join(self.root0, 'compmake')
        self.db = StorageFilesystem(self.root, compress=True)
        self.cc = Context(db=self.db)
        # don't use '\r'
        set_compmake_config('interactive', False)
        set_compmake_config('console_status', False)

        from compmake.constants import CompmakeConstants
        CompmakeConstants.debug_check_invariants = True
        
        # Call the user-defined setup if it exists
        if hasattr(self, "mySetUp"):
            self.mySetUp()
        
        yield  # This is where the test will run
        
        # Teardown logic (former tearDown method)
        if True:
            print('not deleting %s' % self.root0)
        else:
            rmtree(self.root0)
        from multiprocessing import active_children
        c = active_children()
        print('active children: %s' % c)
        if c:
            if True:
                msg = 'Still active children: %s' % c
                logger.warning(msg)
            else:
                raise Exception(msg)

    # Keep the same helper methods
    def comp(self, *args, **kwargs):
        return self.cc.comp(*args, **kwargs)

    @contract(job_id=str, returns=Job)
    def get_job(self, job_id):
        db = self.cc.get_compmake_db()
        return get_job(job_id=job_id, db=db)

    def get_jobs(self, expression):
        """Returns the list of jobs corresponding to the given expression."""
        return list(parse_job_list(expression, context=self.cc))

    def assert_cmd_success(self, cmds):
        """Executes the (list of) commands and checks it was successful."""
        print('@ %s' % cmds)
        try:
            self.cc.batch_command(cmds)
        except MakeFailed as e:
            print('Detected MakeFailed')
            print('Failed jobs: %s' % e.failed)
            for job_id in e.failed:
                self.cc.interpret_commands_wrap('details %s' % job_id)
            raise
        except CommandFailed:
            raise

        self.cc.interpret_commands_wrap('check_consistency raise_if_error=1')

    def assert_cmd_fail(self, cmds):
        """Executes the (list of) commands and checks it was supposed to fail."""
        print('@ %s     [supposed to fail]' % cmds)
        try:
            self.cc.batch_command(cmds)
        except CommandFailed:
            pass
        else:
            msg = 'Command %r did not fail.' % cmds
            raise Exception(msg)

    @contract(cmd_string=str)
    def assert_cmd_success_script(self, cmd_string):
        """This runs the "compmake_main" script which recreates the DB and
        context from disk."""
        ret = compmake_main([self.root, '--nosysexit', '-c', cmd_string])
        assert ret == 0

    # Convert assertion methods to use pytest's assert
    def assert_defined_by(self, job_id, expected):
        assert self.get_job(job_id).defined_by == expected

    def assertEqualSet(self, a, b):
        assert set(a) == set(b)

    @contract(expr=str)
    def assertJobsEqual(self, expr, jobs, ignore_dyn_reports=True):
        js = self.get_jobs(expr)
        if ignore_dyn_reports:
            js = [x for x in js if not 'dynreports' in x]
        try:
            self.assertEqualSet(js, jobs)
        except:
            print('expr %r -> %s' % (expr, js))
            print('differs from %s' % jobs)
            raise

    def assertMakeFailed(self, func, nfailed, nblocked):
        try:
            func()
            pytest.fail("Expected MakeFailed but no exception was raised")
        except MakeFailed as e:
            if len(e.failed) != nfailed:
                msg = 'Expected %d failed, got %d: %s' % (
                    nfailed, len(e.failed), e.failed)
                pytest.fail(msg)
            if len(e.blocked) != nblocked:
                msg = 'Expected %d blocked, got %d: %s' % (
                    nblocked, len(e.blocked), e.blocked)
                pytest.fail(msg)
        except Exception as e:
            pytest.fail('unexpected: %s' % e)

    def assert_job_uptodate(self, job_id, status):
        res = self.up_to_date(job_id)
        assert res == status, 'Want %r uptodate? %s' % (job_id, status)

    @contract(returns=bool)
    def up_to_date(self, job_id):
        from compmake.jobs.uptodate import CacheQueryDB
        cq = CacheQueryDB(db=self.db)
        up, reason, timestamp = cq.up_to_date(job_id)
        print('up_to_date(%r): %s, %r, %s' %
              (job_id, up, reason, timestamp))
        return up
```

#### Step 2: Convert a Single Test File as an Example

Let's convert `test_blocked.py`:

```python
# src/compmake/unittests/test_blocked.py
import pytest
from ..structures import Cache
from ..jobs import get_job_cache
from .pytest_base import CompmakeTestBase

def job_success(*args, **kwargs):
    pass

def job_failure(*args, **kwargs):
    raise ValueError('This job fails')

def check_job_states(db, **expected):
    for job_id, expected_status in expected.items():
        status = get_job_cache(job_id, db=db).state
        if status != expected_status:
            msg = ('For job %r I expected status %s but got status %s.' % 
                   (job_id, expected_status, status))
            raise Exception(msg)

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

        check_job_states(self.db, A=Cache.DONE, B=Cache.FAILED, C=Cache.BLOCKED)
```

#### Step 3: Update __init__.py

Remove the import statements for test modules from `__init__.py`:

```python
# -*- coding: utf-8 -*-
# Empty file - no need to import test modules in pytest
```

#### Step 4: Create a conftest.py file

Add a `conftest.py` file in the test directory for shared pytest fixtures:

```python
# src/compmake/unittests/conftest.py
import pytest

# Add shared fixtures here if needed
```

#### Step 5: Create requirements for the test migration

Update the requirements file to include pytest:

```
# Add to requirements.txt or create a test-requirements.txt
pytest>=7.0.0
```

#### Step 6: Create a pytest.ini file

Add a `pytest.ini` file to configure pytest:

```ini
[pytest]
testpaths = src/compmake/unittests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
```

### 3. Migration Process

The migration should be done methodically:

1. **Create the pytest infrastructure files**:
   - `pytest_base.py`
   - `conftest.py`
   - `pytest.ini`

2. **Migrate tests in batches**:
   - Start with simpler tests
   - Convert the class-based structure to pytest style
   - Replace nose.tools imports with pytest assertions
   - Rename test methods to follow pytest conventions (test_*)
   - Update the __init__.py file to remove unused imports

3. **Common changes required**:
   - Replace `@istest` with pytest class naming conventions
   - Replace `self.assertEqual(a, b)` with `assert a == b`
   - Replace `self.assertTrue(x)` with `assert x`
   - Replace `self.assertRaises` with `pytest.raises`
   - Replace `mySetUp` with setup in pytest fixtures

4. **Test progressively**:
   - After converting each batch, run pytest to ensure they work
   - Start with running individual test files, then run groups
   - Resolve any issues before proceeding to more tests

### 4. Benefits of this Approach

1. **Maintainability**: Migrating to pytest makes the tests more maintainable and future-proof
2. **Readability**: Pytest-style assertions are more readable than unittest style
3. **Parallelism**: Pytest has better support for parallel test execution
4. **Fixtures**: Pytest fixtures are more flexible than setUp/tearDown
5. **Compatibility**: Pytest works well with newer Python versions
6. **Plugins**: Access to a rich ecosystem of pytest plugins

### 5. Migration Progress Tracking

This table tracks the status of each test file's migration from nose to pytest:

| Test File | Converted | Pytest File | Working | Notes |
|-----------|-----------|-------------|---------|-------|
| test_assertions.py | 🔄 Not Started | - | - | - |
| test_blocked.py | ✅ Done | test_blocked_pytest.py | ✅ Passing | Fixed `time.clock()` issue with compatibility layer |
| test_delegation.py | 🔄 Not Started | - | - | - |
| test_delegation_2.py | 🔄 Not Started | - | - | - |
| test_delegation_3.py | 🔄 Not Started | - | - | - |
| test_delegation_4.py | 🔄 Not Started | - | - | - |
| test_delegation_5.py | 🔄 Not Started | - | - | - |
| test_dynamic_1.py | 🔄 Not Started | - | - | - |
| test_dynamic_2.py | 🔄 Not Started | - | - | - |
| test_dynamic_2rec.py | 🔄 Not Started | - | - | - |
| test_dynamic_2rec_par.py | 🔄 Not Started | - | - | - |
| test_dynamic_3.py | 🔄 Not Started | - | - | - |
| test_dynamic_4.py | 🔄 Not Started | - | - | - |
| test_dynamic_5.py | 🔄 Not Started | - | - | - |
| test_dynamic_6.py | 🔄 Not Started | - | - | - |
| test_dynamic_7.py | 🔄 Not Started | - | - | - |
| test_dynamic_8.py | 🔄 Not Started | - | - | - |
| test_dynamic_9.py | 🔄 Not Started | - | - | - |
| test_dynamic_9_redefinition.py | 🔄 Not Started | - | - | - |
| test_dynamic_failure.py | 🔄 Not Started | - | - | - |
| test_dynamic_new_process.py | 🔄 Not Started | - | - | - |
| test_dynamic_re.py | 🔄 Not Started | - | - | - |
| test_examples.py | 🔄 Not Started | - | - | - |
| test_invalid_functions.py | 🔄 Not Started | - | - | - |
| test_more.py | 🔄 Not Started | - | - | - |
| test_old_jobs.py | 🔄 Not Started | - | - | - |
| test_plugins.py | 🔄 Not Started | - | - | - |
| test_priorities.py | 🔄 Not Started | - | - | - |
| test_progress.py | 🔄 Not Started | - | - | - |
| test_stats.py | 🔄 Not Started | - | - | - |
| test_storage.py | 🔄 Not Started | - | - | - |
| test_syntax.py | 🔄 Not Started | - | - | - |
| test_unpickable_result.py | 🔄 Not Started | - | - | - |

**Status Key:**
- ✅ Done: Test has been converted to pytest
- 🔄 Not Started: Conversion not yet begun
- 🟠 In Progress: Conversion started but not complete
- ❌ Failed: Conversion attempted but has issues

**Working Key:**
- ✅ Passing: Test runs and passes with pytest
- ⚠️ Untested: Converted but not yet tested
- ❌ Failing: Test converted but fails when run
- 🐛 Issues: Test has specific issues that need addressing

### 6. Testing Commands

Test individual file:
```bash
python -m pytest src/compmake/unittests/test_blocked.py -v
```

Test all files:
```bash
python -m pytest
```

### 7. Issues and Solutions

This section will be updated as we encounter issues during the migration.

| Issue | Solution |
|-------|----------|
| `AttributeError: module 'time' has no attribute 'clock'` | `time.clock()` was removed in Python 3.8. Fixed by creating a compatibility layer in `utils/compat.py` with a `get_cpu_time()` function that uses `time.perf_counter()` in Python 3 and falls back to `time.clock()` in Python 2. Updated all calls in `structures.py` and `time_track.py`. |
| nose imports causing test failures | Created a clean `__init__.py.pytest` without nose imports that can be swapped in for pytest. Added a `run_pytest_test.py` script to run tests in a controlled environment with the clean __init__. |
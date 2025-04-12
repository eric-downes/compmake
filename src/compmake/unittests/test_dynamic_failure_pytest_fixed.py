# -*- coding: utf-8 -*-
import pytest
from .improved_pytest_base import CompmakeTestBase

def g2():
    pass

def g(context):
    context.comp(g2)

def h2():
    pass

def h(context):
    context.comp(h2)

def fd(context, do_fail=None):
    context.comp_dynamic(g)

    if do_fail is not None:
        raise do_fail()

    context.comp_dynamic(h)

def mockup8(context, do_fail=None):
    context.comp_dynamic(lambda ctx: fd(ctx, do_fail))

class TestDynamicFailure(CompmakeTestBase):
    
    def test_dynamic_failure1(self):
        # Each test uses a local variable instead of class variable
        mockup8(self.cc, do_fail=ValueError)
        # run it
        self.assert_cmd_fail('make recurse=1')
        # we have three jobs defined
        self.assertJobsEqual('all', ['fd'])

    def test_dynamic_failure2(self):
        # Create an isolated test with local variables
        mockup8(self.cc)  # No failure here
        self.assert_cmd_success('make recurse=1')
        # we have three jobs defined
        self.assertJobsEqual('all', ['fd', 'fd-h', 'fd-h-h2',
                                    'fd-g', 'fd-g-g2'])
        self.assertJobsEqual('done', ['fd', 'fd-h', 'fd-h-h2',
                                     'fd-g', 'fd-g-g2'])

        # Create a new context when we want to simulate failure
        # This avoids interference between test stages
        self.db = StorageFilesystem(self.root, compress=True)
        self.cc = Context(db=self.db)
        mockup8(self.cc, do_fail=ValueError)
        self.assert_cmd_fail('make recurse=1')
        self.assertJobsEqual('all', ['fd'])

    def test_dynamic_failure3(self):
        # Each test uses completely isolated state
        mockup8(self.cc, do_fail=KeyboardInterrupt)
        self.assert_cmd_fail('make recurse=1')
        # we have three jobs defined
        self.assertJobsEqual('all', ['fd'])
# -*- coding: utf-8 -*-
import pytest
from .pytest_base import CompmakeTestBase
from .mockup import mockup2_nofail


class TestPlugins(CompmakeTestBase):

    def mySetUp(self):
        mockup2_nofail(self.cc)

    def test_details(self):
        jobs = self.get_jobs('all')
        for job_id in jobs:
            self.assert_cmd_success('details %s' % job_id)
        self.assert_cmd_success('details %s %s' % (jobs[0], jobs[1]))

    def test_list(self):
        jobs = self.get_jobs('all')
        self.assert_cmd_success('ls')
        self.assert_cmd_success('ls %s' % jobs[0])

        # empty list
        #self.assert_cmd_success('ls block* and done')

    # @pytest.mark.skip(reason="Test disabled in original code")
    # def test_credits(self):
    #     self.assert_cmd_success('credits')

    def test_check_consistency(self):
        self.assert_cmd_success('check-consistency')

    def test_dump(self):
        dirname = self.cc.get_compmake_db().basepath
        jobs = self.get_jobs('done')
        for job_id in jobs:
            self.assert_cmd_success('dump directory=%s %s' % (dirname, job_id))

        # TODO: add check that it fails for not done
        jobs = self.get_jobs('not done')
        for job_id in jobs:
            self.assert_cmd_success('dump directory=%s %s' % (dirname, job_id))
import pytest

from pytest_data import Results, Test

class PytestResultsReporter:
    def __init__(self):
        self.results = Results()
        self.tests = {}
        self.last_err = None
        self.config = None

    def pytest_configure(self, config):
        config.addinivalue_line("markers", "task(taskno): this marks the exercise task number.")
        self.config = config

    def pytest_collection_modifyitems(self, session, config, items):
        """
        Sorts the tests in definition order & extracts task_id
        """
        for item in items:
            test_id = item.nodeid
            name = '.'.join(test_id.split("::")[1:])

            for mark in item.iter_markers(name='task'):
                self.tests[name] = Test(name=name, task_id=mark.kwargs['taskno'])


    def pytest_runtest_logreport(self, report):
        """
        Process a test setup / call / teardown report.
        """

        name = report.head_line if report.head_line else ".".join(report.nodeid.split("::")[1:])
        name = report.nodeid
        if name not in self.tests:
            self.tests[name] = Test(name)

        state = self.tests[name]

        # Store duration
        state.duration = report.duration

        # ignore successful setup and teardown stages
        if report.passed and report.when != "call":
            return

        # Update tests that have already failed with capstdout and return.
        if not state.is_passing():
            if report.capstdout.rstrip('FFFFFFFF ').rstrip('uuuuu'):
                state.output = report.capstdout.rstrip('FFFFFFFF ').rstrip('uuuuu')
            return

        # Record captured relevant stdout content for passed tests.
        if report.capstdout:
            state.output = report.capstdout

        # Handle details of test failure
        if report.failed:

            # traceback that caused the issued, if any
            message = None
            if report.longrepr:
                trace = report.longrepr.reprtraceback
                crash = report.longrepr.reprcrash
                message = self._make_message(trace, crash)

            # test failed due to a setup / teardown error
            if report.when != "call":
                state.error(message)
            else:
                state.fail(message)

        # Looks up test_ids from parent when the test is a subtest.
        if state.task_id == 0 and 'variation' in state.name:
            parent_test_name = state.name.split(' ')[0]
            parent_task_id = self.tests[parent_test_name].task_id
            state.task_id = parent_task_id


            # Changes status of parent to fail if any of the subtests fail.
            if state.fail:
                self.tests[parent_test_name].fail(
                    message="One or more variations of this test failed. Details can be found under each [variant#]."
                )
                self.tests[parent_test_name].test_code = state.test_code


    def pytest_sessionfinish(self, session, exitstatus):
        """
        Processes the results into a report.
        """
        exitcode = pytest.ExitCode(int(exitstatus))

        # at least one of the tests has failed
        if exitcode is pytest.ExitCode.TESTS_FAILED:
            self.results.fail()

        # an error has been encountered
        elif exitcode is not pytest.ExitCode.OK:
            message = None
            if self.last_err is not None:
                message = self.last_err
            else:
                message = f"Unexpected ExitCode.{exitcode.name}: check logs for details"
            self.results.error(message)

        for test in self.tests.values():
            self.results.add(test)

    def pytest_exception_interact(self, node, call, report):
        """
        Catch the last exception handled in case the test run itself errors.
        """
        if report.outcome == "failed":
            excinfo = call.excinfo
            err = excinfo.getrepr(style="no", abspath=False)

            trace = err.chain[-1][0]
            crash = err.chain[0][1]
            self.last_err = self._make_message(trace, crash)

    def _make_message(self, trace, crash):
        """
        Make a formatted message for reporting.
        """

        if crash:
            message = ''
            if '<string>' in crash.path:
                message = f'Error at line {crash.lineno}:\n'
            elif 'unittest/case.py' not in crash.path:
                message = f'Error in {crash.path} at line {crash.lineno}:\n'
            message += crash.message
        else:
            message = '\n'.join(trace.reprentries[-1].lines)

        return message


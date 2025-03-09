import pytest
from pytest import TestReport

from .pytest_data import Results, NodeId, TestClass, Test, SubTest


class PytestResultsReporter:
    """
    Custom results reporter that formats results as JSON suitable for reporting
    to students.
    """

    def __init__(self):
        self.results = Results()
        self.last_err = None
        self.config = None

    # def pytest_report_teststatus(self, report: TestReport):
    #     '''
    #     Basically just want to eliminate the 1 character results printing
    #     '''
    #     category, short, verbose = '', '', ''
    #     if hasattr(report, 'wasxfail'):
    #         if report.skipped:
    #             category = 'xfailed'
    #             verbose = 'xfail'
    #         elif report.passed:
    #             category = 'xpassed'
    #             verbose = ('XPASS', {'yellow': True})
    #         return (category, short, verbose)
    #     elif report.when in ('setup', 'teardown'):
    #         if report.failed:
    #             category = 'error'
    #             verbose = 'ERROR'
    #         elif report.skipped:
    #             category = 'skipped'
    #             verbose = 'SKIPPED'
    #         return (category, short, verbose)
    #     category = report.outcome
    #     verbose = category.upper()
    #     return (category, short, verbose)

    def pytest_runtest_logreport(self, report: TestReport):
        """
        Process a test setup / call / teardown report.
        """

        # ignore successful setup and teardown stages
        if report.passed and report.when != "call":
            return

        test = self.results.get_test(report.nodeid)
        state = test
        sub_name = SubTest.parse_head_line(report.head_line)
        if sub_name:
            sub_test = test.get_subtest(sub_name)
            state = sub_test

        # Store duration
        state.duration = report.duration

        # Update tests that have already failed with capstdout and return.
        if not state.is_passing():
            if report.capstdout.rstrip("FFFFFFFF ").rstrip("uuuuu"):
                state.output = report.capstdout.rstrip("FFFFFFFF ").rstrip("uuuuu")
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

    def pytest_sessionfinish(self, session, exitstatus):
        """Processes the results into a report."""
        exitcode = pytest.ExitCode(int(exitstatus))

        # at least one of the tests has failed
        if (
            exitcode is not pytest.ExitCode.TESTS_FAILED
            and exitcode is not pytest.ExitCode.OK
        ):
            message = None
            if self.last_err is not None:
                message = self.last_err
            else:
                message = f"Unexpected ExitCode.{exitcode.name}: check logs for details"
            self.results.error(message)
        self.results.update()

    def pytest_exception_interact(self, node, call, report):
        """Catch the last exception handled in case the test run itself errors."""
        if report.outcome == "failed":
            excinfo = call.excinfo
            err = excinfo.getrepr(style="no", abspath=False)

            trace = err.chain[-1][0]
            crash = err.chain[0][1]
            self.last_err = self._make_message(trace, crash)

    def _make_message(self, trace, crash):
        """Make a formatted message for reporting."""
        if crash:
            message = ""
            if "<string>" in crash.path:
                message = f"Error at line {crash.lineno}:\n"
            elif "unittest/case.py" not in crash.path:
                message = f"Error in {crash.path} at line {crash.lineno}:\n"
            message += crash.message
        else:
            message = "\n".join(trace.reprentries[-1].lines)
        return message

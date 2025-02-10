from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import json
from typing import List

class Status(Enum):
    """
    The status of a given test or test session.
    """

    PASS = auto()
    FAIL = auto()
    ERROR = auto()



@dataclass
class SubTest:
    name: str
    status: Status = Status.PASS
    message: str = None

@dataclass
class Test:
    """
    An individual test's results.
    """

    name: str
    status: Status = Status.PASS
    message: str = None
    sub_tests: List[SubTest] = field(default_factory=list)
    task_id: int = 0
    duration: float = 0.0
    pass_pct: float = 1.0

    def _update(self):
        if not self.sub_tests:
            self.pass_pct = 1.0 if self.status == Status.PASS else 0
        else:
            tot = 0
            for test in self.sub_tests:
                tot += (1.0 if test.status == Status.PASS else 0)
            self.pass_pct = tot / len(self.sub_tests)


    def fail(self, message: str = None) -> None:
        """
        Indicate this test failed.
        """
        self.status = Status.FAIL
        self.message = message
        self._update()

    def error(self, message: str = None) -> None:
        """
        Indicate this test encountered an error.
        """
        self.status = Status.ERROR
        self.message = message
        self._update()


    def is_passing(self):
        """
        Check if the test is currently passing.
        """
        return self.status is Status.PASS



@dataclass
class Results:
    """
    Overall results of a test run.
    """

    status: Status = Status.PASS
    message: str = None
    tests: List[Test] = field(default_factory=list)
    pass_pct: float = 1.0

    def _update(self) -> float:
        if not self.tests:
            self.pass_pct = 1.0 if self.status == Status.PASS else 0
        else:
            tot = 0
            for test in self.tests:
                test._update()
                tot += test.pass_pct
            self.pass_pct = tot / len(self.tests)

    def add(self, test: Test) -> None:
        """
        Add a Test to the list of tests.
        """
        if test.status is Status.FAIL:
            self.fail()
        self.tests.append(test)
        self._update()

    def fail(self) -> None:
        """
        Indicate the test run had at least one failure.
        """
        self.status = Status.FAIL
        self._update()

    def error(self, message: str = None) -> None:
        """
        Indicate the test run fatally errored.
        """
        self.status = Status.ERROR
        self.message = message
        self._update()

    @staticmethod
    def _dict_factory(items):
        result = {}
        for key, value in items:
            if isinstance(value, Status):
                value = value.name.lower()

            result[key] = value
        
        return result
    
    def as_dict(self):
        self._update()
        return asdict(self, dict_factory=self._dict_factory)

    def as_json(self):
        results = self.as_dict()
        results["tests"] = sorted(results["tests"], key=lambda item: item["task_id"])
        return json.dumps(results, indent=2)
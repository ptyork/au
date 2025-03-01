from typing import List, Dict
from dataclasses import dataclass, field, asdict
from enum import Enum, auto
import json
import re
from dacite import from_dict, Config

class Status(Enum):
    """The status of a given test or test session."""
    PASS = "pass"
    FAIL = "fail"
    ERROR = "error"

@dataclass
class NodeId:
    test_file: str
    test_class: str
    test_name: str

    @staticmethod
    def parse(nodeid: str) -> 'NodeId':
        # TEST_FILE::TEST_CLASS::TEST_METHOD
        parts = nodeid.split('::')
        return NodeId(parts[0], parts[1], parts[2].replace('_', ' ').title())

_head_line_re = re.compile(r'^(\w*)\.(\w*)(?:\s+\[(.*)\])?(?:\s+\((.*)\))?$')

@dataclass
class SubTest:
    name: str
    parent_test_name: str
    parent_test_class: str
    status: Status = Status.PASS
    message: str|None = None
    output: str|None = None
    duration: float = 0.0

    def fail(self, message: str = None) -> None:
        """Indicate this test failed."""
        self.status = Status.FAIL
        self.message = message

    def error(self, message: str = None) -> None:
        """Indicate this test encountered an error."""
        self.status = Status.ERROR
        self.message = message

    def is_passing(self):
        """Check if the test is currently passing."""
        return self.status is Status.PASS


    @staticmethod
    def parse_head_line(head_line: str) -> str:
        """
        Returns either a subtest name or None depending on whether the head_line
        shows this to be a subtest or not. If the name is empty, "Unnamed
        Subtest" will be returned. There is no guarantee that subtests will have
        unique names.

        format:
            `TEST_CLASS.TEST_METHOD [SUBTEST_NAME] (SUBTEST_ARGS)`
        """
        parts = _head_line_re.match(head_line).groups()
        if parts[2] is None:
            return None
        else:
            name = parts[2].strip()
            if not name:
                name = "Unnamed Subtest"
            if parts[3]:
                name = f"{name} ({parts[3]})"
            return name


@dataclass
class Test:
    """An individual test's results."""

    name: str
    parent_test_class: str
    status: Status = Status.PASS
    message: str|None = None
    output: str|None = None
    duration: float = 0.0
    sub_tests: List[SubTest] = field(default_factory=list)
    pass_pct: float = 1.0

    def _update(self):
        if not self.sub_tests:
            self.pass_pct = 1.0 if self.status == Status.PASS else 0
        else:
            self.pass_pct = 1.0
            for sub_test in self.sub_tests:
                if not sub_test.is_passing():
                    self.pass_pct = 0.0
                    break

            # No way to get all subtests, only the ones that failed. So this is
            # if fruitless. Just 1 or 0 is all we get. I.e., avoid subtests.

            # tot = 0
            # for test in self.sub_tests:
            #     tot += (1.0 if test.status == Status.PASS else 0)
            # self.pass_pct = tot / len(self.sub_tests)
        self.status = Status.PASS if self.pass_pct == 1 else Status.FAIL

    def get_subtest(self, name: str) -> SubTest:
        subtest = SubTest(name, self.name, self.parent_test_class)
        self.sub_tests.append(subtest)
        return subtest

    def get_pass_pct(self) -> float:
        self._update()
        return self.pass_pct

    def fail(self, message: str = None) -> None:
        """Indicate this test failed."""
        self.status = Status.FAIL
        self.message = message
        self._update()

    def error(self, message: str = None) -> None:
        """Indicate this test encountered an error."""
        self.status = Status.ERROR
        self.message = message
        self._update()

    def is_passing(self):
        """Check if the test is currently passing."""
        return self.status is Status.PASS


@dataclass
class TestClass:
    name: str
    status: Status = Status.PASS
    tests: Dict[str, Test] = field(default_factory=dict)
    pass_pct: float = 1.0
    pass_count: int = 0

    def _update(self):
        self.pass_count = 0
        tot = 0
        for test in self.tests.values():
            tot += test.get_pass_pct()
            if test.is_passing():
                self.pass_count += 1
        self.pass_pct = tot / len(self.tests)
        self.status = Status.PASS if self.pass_pct == 1 else Status.FAIL

    def get_test(self, name: str):
        """Retrieve the test object"""
        return self.tests.setdefault(name, Test(name, self.name))

    def is_passing(self):
        """Check if the test is currently passing."""
        self._update()
        return self.status is Status.PASS

    def get_pass_pct(self) -> float:
        self._update()
        return self.pass_pct

@dataclass
class Results:
    """Overall results of a test run."""

    status: Status = Status.PASS
    message: str|None = None
    test_classes: Dict[str, TestClass] = field(default_factory=dict)
    pass_pct: float = 1.0

    def get_test(self, nodeid: str):
        """Create or retrieve a Test instance for a given test."""
        node = NodeId.parse(nodeid)
        # Create or receive the parent TestClass
        test_class = self.test_classes.setdefault(node.test_class, TestClass(node.test_class))
        return test_class.get_test(node.test_name)

    def update(self) -> None:
        if not self.test_classes:
            self.pass_pct = 1.0 if self.status == Status.PASS else 0
        else:
            tot = 0
            for test_class in self.test_classes.values():
                tot += test_class.get_pass_pct()
            self.pass_pct = tot / len(self.test_classes)
        self.status = Status.PASS if self.pass_pct == 1 else Status.FAIL

    def error(self, message: str = None) -> None:
        """Indicate the test run fatally errored."""
        self.status = Status.ERROR
        self.message = message
        self.update()

    @staticmethod
    def _dict_factory(items):
        result = {}
        for key, value in items:
            if isinstance(value, Status):
                value = value.name.lower()

            result[key] = value
        
        return result
    
    def as_dict(self):
        self.update()
        return asdict(self, dict_factory=self._dict_factory)

    def as_json(self):
        results = self.as_dict()
        return json.dumps(results, indent=2)
    
    @staticmethod
    def from_dict(results_d: Dict[str, any]) -> 'Results':
        return from_dict(Results, results_d, config=Config(cast=[Enum]))
    
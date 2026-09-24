from training.evaluation.sandbox.code_runner import run_code_tests


def test_code_execution_pass():
    result = run_code_tests(
        "def add(a, b):\n    return a + b",
        (
            "import unittest\nfrom solution import add\n\n"
            "class TestAdd(unittest.TestCase):\n"
            "    def test_add(self):\n"
            "        self.assertEqual(add(1, 2), 3)\n"
        ),
        timeout_sec=5.0,
    )
    assert result.passed
    assert result.pass_rate == 1.0


def test_code_execution_fail():
    result = run_code_tests(
        "def add(a, b):\n    return a - b",
        (
            "import unittest\nfrom solution import add\n\n"
            "class TestAdd(unittest.TestCase):\n"
            "    def test_add(self):\n"
            "        self.assertEqual(add(1, 2), 3)\n"
        ),
        timeout_sec=5.0,
    )
    assert not result.passed
    assert result.pass_rate < 1.0


def test_code_execution_timeout():
    result = run_code_tests(
        "import time\n\ndef add(a, b):\n    time.sleep(10)\n    return a + b",
        (
            "import unittest\nfrom solution import add\n\n"
            "class TestAdd(unittest.TestCase):\n"
            "    def test_add(self):\n"
            "        self.assertEqual(add(1, 2), 3)\n"
        ),
        timeout_sec=1.0,
    )
    assert result.timed_out
    assert result.error == "EXECUTION_TIMEOUT"

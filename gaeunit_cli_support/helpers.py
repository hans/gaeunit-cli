import re
import sys

class DummyTest:
    # @see unittest.TestCase.failureException
    failureException = AttributeError

    testName = ''
    shortDescription_ = ''

    def shortDescription(self):
        return self.shortDescription_

    def __repr__(self):
        return self.testName


class DummyStdout:
    """unittest tries to call sys.stdout.writeln(), which does not exist (!).
    Get around this!"""

    def writeln(self, data=''):
        sys.stdout.write("%s\n" % data)

    def __getattr__(self, name):
        """Forward any other methods to sys.stdout."""

        def method_missing(*args, **kwargs):
            getattr(sys.stdout, name)(*args, **kwargs)

        return method_missing


class DummyTraceback:
    class DummyTracebackFrame:
        f_globals = ['__unittest']

    tb_frame = DummyTracebackFrame()
    tb_next = None

    def __init__(self, traceback_str):
        self.traceback_str = traceback_str

    def format_exception(self, type, value, tb, limit=None):
        return self.traceback_str


class GAEError: pass


def get_error_message(traceback_str):
    # Grab from the penultimate line of the
    # traceback string, minus the exception label at start.
    try:
        desc = traceback_str.split("\n")[-2]
    except IndexError, e:
        return ''
    else:
        desc = re.compile(r"^\w+: (.*)$").match(desc).group(1) or desc

        return traceback_str
import collections
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
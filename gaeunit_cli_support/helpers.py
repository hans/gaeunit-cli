import collections
import sys

class DummyTest:
    # @see unittest.TestCase.failureException
    failureException = AttributeError

    def shortDescription(self):
        return ''

class DummyStdout:
    """unittest tries to call sys.stdout.writeln(), which does not exist (!).
    Get around this!"""

    def writeln(self, data=''):
        sys.stdout.write("\n%s" % data)

    def __getattr__(self, name):
        """Forward any other methods to sys.stdout."""

        def method_missing(*args, **kwargs):
            getattr(sys.stdout, name)(*args, **kwargs)

        return method_missing
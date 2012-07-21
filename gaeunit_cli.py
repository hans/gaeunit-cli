import json
import optparse
import re
import sys
import time
import unittest.runner
import urllib2

from gaeunit_cli_support.helpers import DummyTest, DummyStdout

def main():
    parser = optparse.OptionParser(usage='%prog -u URL [options]',
                                   version='%prog 0.1.0')
    parser.add_option('-u', '--url', help='URL to access GAEUnit', dest='url')

    (options, args) = parser.parse_args(sys.argv)

    # TODO: allow for setting URL in an .rc file
    # TODO: validate URL
    url = options.url or 'http://localhost:8080/test'

    # Get a list of test call names from the server
    tests = get_tests(options.url)

    # Go!
    run_tests(options.url, tests)


def get_tests(url):
    """Get a list of test names given the GAEUnit access point"""

    u = urllib2.urlopen('%s/list' % url)
    dict = json.loads(u.read())

    # GAEUnit outputs a data structure like this:
    #
    # {
    #   "module": {
    #     "SomeTestClass": [
    #       "test_abc",
    #       "test_xyz"
    #     ]
    #   }
    # }
    #
    # We simply need a list of <module>.<class>.<method> strings.

    tests = []

    for module, classes in dict.iteritems():
      for klass, methods in classes.iteritems():
        for method in methods:
          tests.append("%s.%s.%s" % (module, klass, method))

    return tests


def run_tests(url, tests, stream=None):
    """Run a list of tests"""

    if not stream:
        stream = DummyStdout()

    # Use a standard unittest output mechanism
    result = unittest.runner.TextTestResult(stream=stream,
                                            descriptions=True,
                                            verbosity=1)

    # Pass this dummy object (standing in for unittest.TestCase) to the test
    # result object.
    dummy = DummyTest()

    # Start timing
    start_time = time.time()

    # TODO: mod GAEUnit to run multiple tests w/ single request
    # see unittest.loadTestsFromNames
    for test in tests:
        # Trigger the test run and receive results
        u = urllib2.urlopen('%s/run?name=%s' % (url, test))
        data = json.loads(u.read())

        # TODO: reproduce error properly
        if len(data['failures']) > 0:
            # Update the dummy test's description to describe the current test
            failure = data['failures'][0]

            dummy.testName = test
            dummy.shortDescription_ = failure['desc']

            # Fake exception description. Grab from the penultimate line of the
            # traceback string, minus the exception label at start.
            desc = failure['detail'].split("\n")[-2]
            desc = re.compile(r"^\w+: (.*)$").match(desc).group(1) or desc

            # Fake an exception tuple
            # TODO: spoof a traceback based on string contained in failure
            #   response
            exc = (AssertionError, desc, None)

            result.addFailure(dummy, exc)
        else:
            result.addSuccess(dummy)

    result.printErrors()

    totalTime = time.time() - start_time
    stream.writeln("Ran %d test%s in %.3fs\n" %
                   (len(tests), len(tests) != 1 and "s" or "", totalTime))

    expectedFails = unexpectedSuccesses = skipped = 0
    try:
        results = map(len, (result.expectedFailures,
                          result.unexpectedSuccesses,
                          result.skipped))
    except AttributeError:
        pass
    else:
        expectedFails, unexpectedSuccesses, skipped = results

    infos = []
    if not result.wasSuccessful():
        stream.write("FAILED")
        failed, errored = map(len, (result.failures, result.errors))
        if failed:
            infos.append("failures=%d" % failed)
        if errored:
            infos.append("errors=%d" % errored)
    else:
        stream.write("OK")
    if skipped:
        infos.append("skipped=%d" % skipped)
    if expectedFails:
        infos.append("expected failures=%d" % expectedFails)
    if unexpectedSuccesses:
        infos.append("unexpected successes=%d" % unexpectedSuccesses)

    if infos:
        stream.writeln(" (%s)" % (", ".join(infos),))
    else:
        stream.writeln()


if __name__ == '__main__':
    main()
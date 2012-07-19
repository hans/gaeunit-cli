import json
import optparse
import re
import sys
import unittest.runner
import urllib2

from gaeunit_cli_support.helpers import DummyTest, DummyStdout

def main():
    parser = optparse.OptionParser(usage='%prog -u URL [options]',
                                   version='%prog 0.1.0')
    parser.add_option('-u', '--url', help='URL to access GAEUnit', dest='url')

    (options, args) = parser.parse_args(sys.argv)

    # Die if we aren't given the URL.
    # TODO: allow for setting URL in an .rc file
    # TODO: validate URL
    if not options.url:
        parser.print_usage()
        exit()

    # Get a list of test call names from the server
    tests = get_tests(options.url)

    # Go!
    run_tests(options.url, tests)


# Get a list of test names given the GAEUnit access point
def get_tests(url):
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
    # We simply need a list of <module>.<class>.<method>.

    tests = []

    for module, classes in dict.iteritems():
      for klass, methods in classes.iteritems():
        for method in methods:
          tests.append("%s.%s.%s" % (module, klass, method))

    return tests


# Run a list of tests
def run_tests(url, tests):
    # Use a standard unittest output mechanism
    result = unittest.runner.TextTestResult(stream=DummyStdout(),
                                            descriptions=True,
                                            verbosity=1)

    # Pass this dummy object (standing in for unittest.TestCase) to the test
    # result object.
    dummy = DummyTest()

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

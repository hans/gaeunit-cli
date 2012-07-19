import json
import optparse
import sys
import unittest.runner
import urllib2

from gaeunit_cli_support.helpers import DummyTest

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
    results = unittest.runner.TextTestResult(stream=sys.stderr,
                                             descriptions=True,
                                             verbosity=1)

    # TODO: mod GAEUnit to run multiple tests w/ single request
    # see unittest.loadTestsFromNames
    for test in tests:
        # Trigger the test run and receive results
        u = urllib2.urlopen('%s/run?name=%s' % (url, test))
        result = json.loads(u.read())

        # TODO: reproduce error properly
        if len(result['failures']) > 0:
          exc = (AssertionError, 'Hi', None)
          results.addFailure(test, exc)
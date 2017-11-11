
import unittest
import errno
import sys
import os
import HTMLTestRunner

sys.path.append(os.path.join("..", "src"))

from universal_forwarder_compatiblity import UF_MODE, make_splunkhome_path

def runOnlyIfSplunkPython(func):
    def _decorator(self, *args, **kwargs):
        try:
            import splunk
            return func(self, *args, **kwargs)
        except ImportError:
            self.skipTest('Skipping test since this is on system Python')
            return

    return _decorator

def runOnlyIfSystemPython(func):
    def _decorator(self, *args, **kwargs):
        try:
            import splunk
            self.skipTest('Skipping test since this is on Splunk Python')
            return
        except ImportError:
            return func(self, *args, **kwargs)

    return _decorator

class TestShortcuts(unittest.TestCase):
    """
    Test the shortcuts module that provides some generic helpers.
    """

    @runOnlyIfSplunkPython
    def test_is_uf_mode(self):
        """
        Make sure the UF_MODE variable can be imported.
        """
        print "UF_MODE:%r" % UF_MODE
        self.assertEquals(UF_MODE, False)

    @runOnlyIfSystemPython
    def test_is_uf_mode_system(self):
        """
        Make sure the UF_MODE variable can be imported.
        """
        print "UF_MODE:%r" % UF_MODE
        self.assertEquals(UF_MODE, True)

    def test_make_splunkhome_path_builtin(self):
        """
        Ensure that make_splunkhome_path works using the built-in function.
        """

        if 'SPLUNK_HOME' not in os.environ:
            os.environ['SPLUNK_HOME'] = '/opt/splunk'

        self.assertTrue(make_splunkhome_path(['var', 'log', 'splunk', 'test.log'], True).endswith('/var/log/splunk/test.log'))

    @runOnlyIfSplunkPython
    def test_make_splunkhome_path_default(self):
        """
        Ensure that make_splunkhome_path works using core Splunk's function.
        """

        self.assertTrue(make_splunkhome_path(['var', 'log', 'splunk', 'test.log'], False).endswith('/var/log/splunk/test.log'))

if __name__ == '__main__':
    report_path = os.path.join('..', os.environ.get('TEST_OUTPUT', 'tmp/test_report.html'))

    # Make the test directory
    try:
        os.makedirs(os.path.dirname(report_path))
    except OSError as exception:
        if exception.errno != errno.EEXIST:
            raise

    with open(report_path, 'w') as report_file:
        test_runner = HTMLTestRunner.HTMLTestRunner(
            stream=report_file
        )
        unittest.main(testRunner=test_runner)

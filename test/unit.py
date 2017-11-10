
import unittest
import errno
import sys
import os
import HTMLTestRunner

sys.path.append(os.path.join("..", "src"))

from shortcuts import UF_MODE, make_splunkhome_path

class TestShortcuts(unittest.TestCase):
    """
    Test the shortcuts module that provides some generic helpers.
    """

    def test_is_uf_mode(self):
        """
        Make sure the UF_MODE variable can be imported.
        """

        self.assertEquals(UF_MODE, False)

    def test_make_splunkhome_path_builtin(self):
        """
        Ensure that make_splunkhome_path works using the built-in function.
        """

        self.assertTrue(make_splunkhome_path(['var', 'log', 'splunk', 'test.log'], True).endswith('/var/log/splunk/test.log'))

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

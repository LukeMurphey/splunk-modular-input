
import unittest
import errno
import sys
import os
import HTMLTestRunner


sys.path.append(os.path.join("..", "tmp", "packages", "modular_input.zip"))
from modular_input.universal_forwarder_compatiblity import UF_MODE, make_splunkhome_path, normalizeBoolean
from modular_input.fields import IPNetworkField, ListField, DomainNameField, MultiValidatorField
from modular_input.exceptions import FieldValidationException

def runOnlyIfSplunkPython(func):
    """
    Run the given test only if Splunk's Python is running this test.
    """

    def _decorator(self, *args, **kwargs):
        try:
            import splunk
            return func(self, *args, **kwargs)
        except ImportError:
            self.skipTest('Skipping test since this is on system Python')
            return

    return _decorator

def runOnlyIfSystemPython(func):
    """
    Run the given test only if Splunk's Python is _not_ running this test.
    """

    def _decorator(self, *args, **kwargs):
        try:
            import splunk
            self.skipTest('Skipping test since this is on Splunk Python')
            return
        except ImportError:
            return func(self, *args, **kwargs)

    return _decorator

class TestUniversalForwarder(unittest.TestCase):
    """
    Test the universal forwarder module that provides some generic helpers in case Splunk's
    libraries are not available (like on Universal Forwarders which lack Splunk's Python).
    """

    @runOnlyIfSplunkPython
    def test_is_uf_mode(self):
        """
        Make sure the UF_MODE variable can be imported.
        """
        self.assertEquals(UF_MODE, False)

    @runOnlyIfSystemPython
    def test_is_uf_mode_system(self):
        """
        Make sure the UF_MODE variable can be imported.
        """
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

    def test_normalize_boolean(self):
        """
        Ensure that make_splunkhome_path works using the built-in function.
        """

        self.assertTrue(normalizeBoolean(1), True)
        self.assertTrue(normalizeBoolean(1, False), True)

    @runOnlyIfSplunkPython
    def test_normalize_boolean_default(self):
        """
        Ensure that make_splunkhome_path works using core Splunk's function.
        """

        self.assertTrue(normalizeBoolean(1), True)

class TestIPNetworkField(unittest.TestCase):
    """
    Test the field for defining IP Network fields.
    """

    field = None

    def setUp(self):
        self.field = IPNetworkField('name', 'title', 'description')

    def test_valid_range(self):
        value = self.field.to_python(u'10.0.0.0/28')

        self.assertEquals(value.num_addresses, 16)

    def test_valid_range_not_string(self):
        # Note: this has host bits set and this test will verify that strict mode isn't set
        value = self.field.to_python(u'10.0.0.0/4')

        self.assertEquals(value.num_addresses, 268435456)

    def test_to_string(self):
        value = self.field.to_python(u'10.0.0.0/28')

        self.assertEquals(self.field.to_string(value), '10.0.0.0/28')

    def test_invalid_range(self):
        with self.assertRaises(FieldValidationException):
            self.field.to_python(u'10.0.0.X')

    def test_single_ip(self):
        value = self.field.to_python(u'10.0.0.6')
        self.assertEquals(value.num_addresses, 1)

class TestDomainNameField(unittest.TestCase):
    """
    Test the domain name field.
    """

    field = None

    def setUp(self):
        self.field = DomainNameField('name', 'title', 'description')

    def test_convert_values(self):
        self.field.to_python('google.com')

    def test_convert_invalid(self):
        with self.assertRaises(FieldValidationException):
            self.field.to_python('____')

    def test_convert_invalid_ip(self):
        with self.assertRaises(FieldValidationException):
            self.field.to_python('1.2.3.4')

class TestMultiValidatorField(unittest.TestCase):
    """
    Test the field validator that allows you to use multiple validators to validate input.
    """
    field = None

    def setUp(self):
        self.field = MultiValidatorField('name', 'title', 'description', validators=[DomainNameField, IPNetworkField])

    def test_convert_values_invalid(self):
        try:
            self.field.to_python(u' ')
        except FieldValidationException as exception:
            self.assertEqual(str(exception), "The value of ' ' for the 'name' parameter is not a valid domain name;u' ' does not appear to be an IPv4 or IPv6 network")

    def test_convert_values_first_validator(self):
        self.assertEqual(self.field.to_python('google.com'), 'google.com')

    def test_convert_values_second_validator(self):
        self.assertEqual(self.field.to_python(u'1.2.3.4/31').num_addresses, 2)

class TestFieldList(unittest.TestCase):
    """
    Test the list field and its ability to instantiate particular types of objects.
    """

    field = None

    def setUp(self):
        self.field = ListField('name', 'title', 'description', instance_class=IPNetworkField, trim_values=True)

    def test_convert_values(self):
        values = self.field.to_python(u'10.0.0.0/28,1.2.3.4,10.0.1.0/28')

        self.assertEquals(len(values), 3)
        self.assertEquals(values[0].num_addresses, 16)

    def test_convert_values_with_extra_spaces(self):
        values = self.field.to_python(u'10.0.0.0/28, 1.2.3.4, 10.0.1.0/28')

        self.assertEquals(len(values), 3)
        self.assertEquals(values[0].num_addresses, 16)

    def test_convert_invalid_values(self):
        with self.assertRaises(FieldValidationException):
            self.field.to_python(u'10.0.0.0/28, 1.2.3.X, 10.0.1.0/28')

    def test_to_string(self):
        values = self.field.to_python(u'10.0.0.0/28,1.2.3.4,10.0.1.0/28')
        to_string = self.field.to_string(values)

        self.assertEquals(to_string, '10.0.0.0/28,1.2.3.4,10.0.1.0/28')

    def test_to_string_plain(self):
        field = ListField('name', 'title', 'description')

        values = field.to_python(u'A,B,C')
        self.assertEquals(values, ['A', 'B', 'C'])

        to_string = field.to_string(values)
        self.assertEquals(to_string, 'A,B,C')

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

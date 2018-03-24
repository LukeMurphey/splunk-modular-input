
import unittest
import errno
import sys
import os
import re
import HTMLTestRunner


sys.path.append(os.path.join("..", "tmp", "packages", "modular_input.zip"))
from modular_input.universal_forwarder_compatiblity import UF_MODE, make_splunkhome_path, normalizeBoolean
from modular_input.fields import IPNetworkField, ListField, DomainNameField, MultiValidatorField
from modular_input.exceptions import FieldValidationException
from modular_input.server_info import ServerInfo

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

def runOnlyIfSplunkIsRunning(func):
    pass

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

    def test_various_input(self):

        test_values = [
                        # ipv4
                       [True, "123.23.34.2"],
                       [True, "172.26.168.134"],
                       [True, "1.2.3.4"],
                       [False, " 01.102.103.104  "],
                       # ipv6 
                       [True, "2001:db8:3333:4444:5555:6666:1.2.3.4"],
                       [True, "::11.22.33.44"],
                       [True, "2001:db8::123.123.123.123"],
                       [True, "::1234:5678:91.123.4.56"],
                       [True, "::1234:5678:1.2.3.4"],
                       [True, "2001:db8::1234:5678:5.6.7.8"],
                       [False, ""],
                       #[True, "2001:0000:1234:0000:0000:C1C0:ABCD:0876"],
                       [True, "2001:0:1234::C1C0:ABCD:876"],
                       [True, "3ffe:0b00:0000:0000:0001:0000:0000:000a"],
                       [True, "3ffe:b00::1:0:0:a"],
                       [True, "FF02:0000:0000:0000:0000:0000:0000:0001"],
                       [True, "FF02::1"],
                       [True, "0000:0000:0000:0000:0000:0000:0000:0001"],
                       [True, "0000:0000:0000:0000:0000:0000:0000:0000"],
                       [True, "::"],
                       [True, "::ffff:192.168.1.26"],
                       [False, "02001:0000:1234:0000:0000:C1C0:ABCD:0876"],
                       [False, "2001:0000:1234:0000:00001:C1C0:ABCD:0876"],
                       [False, "2001:1:1:1:1:1:255Z255X255Y255"],
                       [False, "3ffe:0b00:0000:0001:0000:0000:000a"],
                       [False, "FF02:0000:0000:0000:0000:0000:0000:0000:0001"],
                       [False, "3ffe:b00::1::a"],
                       [False, "::1111:2222:3333:4444:5555:6666::"],
                       [True, "2::10"],
                       [True, "ff02::1"],
                       [True, "fe80::"],
                       [True, "2002::"],
                       [True, "2001:db8::"],
                       [True, "2001:0db8:1234::"],
                       [True, "::ffff:0:0"],
                       [True, "::ffff:192.168.1.1"],
                       [True, "1:2:3:4:5:6:7:8"],
                       [True, "1:2:3:4:5:6::8"],
                       [True, "1:2:3:4:5::8"],
                       [True, "1:2:3:4::8"],
                       [True, "1:2:3::8"],
                       [True, "1:2::8"],
                       [True, "1::8"],
                       [True, "1::2:3:4:5:6:7"],
                       [True, "1::2:3:4:5:6"],
                       [True, "1::2:3:4:5"],
                       [True, "1::2:3:4"],
                       [True, "1::2:3"],
                       [True, "::2:3:4:5:6:7:8"],
                       [True, "::2:3:4:5:6:7"],
                       [True, "::2:3:4:5:6"],
                       [True, "::2:3:4:5"],
                       [True, "::2:3:4"],
                       [True, "::2:3"],
                       [True, "::8"],
                       [True, "1:2:3:4:5:6::"],
                       [True, "1:2:3:4:5::"],
                       [True, "1:2:3:4::"],
                       [True, "1:2:3::"],
                       [True, "1:2::"],
                       [True, "1::"],
                       [True, "1:2:3:4:5::7:8"],
                       [False, "1:2:3::4:5::7:8"],
                       [False, "12345::6:7:8"],
                       [True, "1:2:3:4::7:8"],
                       [True, "1:2:3::7:8"],
                       [True, "1:2::7:8"],
                       [True, "1::7:8"],
                       [True, "1:2:3:4:5:6:1.2.3.4"],
                       [True, "1:2:3:4:5::1.2.3.4"],
                       [True, "1:2:3:4::1.2.3.4"],
                       [True, "1:2:3::1.2.3.4"],
                       [True, "1:2::1.2.3.4"],
                       [True, "1::1.2.3.4"],
                       [True, "1:2:3:4::5:1.2.3.4"],
                       [True, "1:2:3::5:1.2.3.4"],
                       [True, "1:2::5:1.2.3.4"],
                       [True, "1::5:1.2.3.4"],
                       [True, "1::5:11.22.33.44"],
                       [False, "1::5:400.2.3.4"],
                       [False, "1::5:260.2.3.4"],
                       [False, "1::5:256.2.3.4"],
                       [False, "1::5:1.256.3.4"],
                       [False, "1::5:1.2.256.4"],
                       [False, "1::5:1.2.3.256"],
                       [False, "1::5:300.2.3.4"],
                       [False, "1::5:1.300.3.4"],
                       [False, "1::5:1.2.300.4"],
                       [False, "1::5:1.2.3.300"],
                       [False, "1::5:900.2.3.4"],
                       [False, "1::5:1.900.3.4"],
                       [False, "1::5:1.2.900.4"],
                       [False, "1::5:1.2.3.900"],
                       [False, "1::5:300.300.300.300"],
                       [False, "1::5:3000.30.30.30"],
                       [False, "1::400.2.3.4"],
                       [False, "1::260.2.3.4"],
                       [False, "1::256.2.3.4"],
                       [False, "1::1.256.3.4"],
                       [False, "1::1.2.256.4"],
                       [False, "1::1.2.3.256"],
                       [False, "1::300.2.3.4"],
                       [False, "1::1.300.3.4"],
                       [False, "1::1.2.300.4"],
                       [False, "1::1.2.3.300"],
                       [False, "1::900.2.3.4"],
                       [False, "1::1.900.3.4"],
                       [False, "1::1.2.900.4"],
                       [False, "1::1.2.3.900"],
                       [False, "1::300.300.300.300"],
                       [False, "1::3000.30.30.30"],
                       [False, "::400.2.3.4"],
                       [False, "::260.2.3.4"],
                       [False, "::256.2.3.4"],
                       [False, "::1.256.3.4"],
                       [False, "::1.2.256.4"],
                       [False, "::1.2.3.256"],
                       [False, "::300.2.3.4"],
                       [False, "::1.300.3.4"],
                       [False, "::1.2.300.4"],
                       [False, "::1.2.3.300"],
                       [False, "::900.2.3.4"],
                       [False, "::1.900.3.4"],
                       [False, "::1.2.900.4"],
                       [False, "::1.2.3.900"],
                       [False, "::300.300.300.300"],
                       [False, "::3000.30.30.30"],
                       [True, "fe80::217:f2ff:254.7.237.98"],
                       [True, "fe80::217:f2ff:fe07:ed62"],
                       [True, "2001:DB8:0:0:8:800:200C:417A"],
                       [True, "FF01:0:0:0:0:0:0:101"],
                       [True, "FF01::101"],
                       [True, "0:0:0:0:0:0:0:1"],
                       [True, "0:0:0:0:0:0:0:0"],
                       [True, "2001:2:3:4:5:6:7:134"],
                       [True, "1111:2222:3333:4444:5555:6666:7777:8888"],
                       [True, "1111:2222:3333:4444:5555:6666:7777::"]]

        for test_value in test_values:
            if test_value[0] is False:
                with self.assertRaises(FieldValidationException):
                    self.field.to_python(unicode(test_value[1]))
            else:
                self.field.to_python(unicode(test_value[1]))

class TestDomainNameField(unittest.TestCase):
    """
    Test the domain name field.
    """

    field = None

    def setUp(self):
        self.field = DomainNameField('name', 'title', 'description')

    def test_various_input(self):
        """
        This test checks a series of known good and bad input.
        """

        test_values = [[True, "something.else.army.mil"],
                       [True, "mydomain.com"],
                       [True, "test.mydomain.com"],
                       [True, "en.wikipedia.org"],
                       #[False, "28999"],
                       [True, "abc"],
                       [True, "3abc"],
                       #[False, "192.168.0.2000000000"],
                       [False, "*hi*"],
                       [False, "-hi-"],
                       [False, "_domain"],
                       [False, "____"],
                       [False, ":54:sda54"]]

        for test_value in test_values:
            if test_value[0] is False:
                with self.assertRaises(FieldValidationException):
                    self.field.to_python(test_value[1])
                    print "Exception not raised for:", test_value[1]
            else:
                self.field.to_python(test_value[1])

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

class LiveSplunkTestCase(unittest.TestCase):
    """
    This loads information from local.properties that is useful for testing against a live Splunk install.
    """

    username = None
    password = None

    def changeEncodingToAscii(self, s):
        if s is not None:
            return s.encode("ascii")
        else:
            return s

    def loadConfig(self, properties_file=None):
        
        if properties_file is None:
            properties_file = os.path.join( "..", "local.properties")
        
        try:
            fp = open(properties_file)
        except IOError:
            return

        regex = re.compile("(?P<key>[^=]+)[=](?P<value>.*)")
        
        settings = {}
        
        for l in fp.readlines():
            r = regex.search(l)
            
            if r is not None:
                d = r.groupdict()
                settings[ d["key"] ] = d["value"]
        
        self.username = self.changeEncodingToAscii(settings.get("test.splunk.username", None))
        self.password = self.changeEncodingToAscii(settings.get("test.splunk.password", None))

    def setUp(self):
        self.loadConfig()

class TestServerInfo(LiveSplunkTestCase):
    """
    Test the ServerInfo class.
    """
    
    def test_get_dict_object(self):
        d = {
            'a': {
                'b': {
                    'c': 'C'
                }
            }
        }

        self.assertEquals(ServerInfo.get_dict_object(d, ['a', 'b', 'c']), 'C')

    @runOnlyIfSplunkPython
    def test_is_shc_enabled(self):
        if self.username is not None and self.password is not None:
            import splunk
            try:
                session_key = splunk.auth.getSessionKey(username=self.username, password=self.password)

                # This assumes you are testing against a non-SHC environment
                self.assertFalse(ServerInfo.is_on_shc(session_key))
            except splunk.SplunkdConnectionException:
                pass
        else:
            self.skipTest('Skipping test since Splunk authentication data is not available')

    @runOnlyIfSplunkPython
    def test_is_shc_captain(self):
        if self.username is not None and self.password is not None:
            import splunk
            try:
                session_key = splunk.auth.getSessionKey(username=self.username, password=self.password)

                # This assumes you are testing against a non-SHC environment
                self.assertEquals(ServerInfo.is_shc_captain(session_key), None)
            except splunk.SplunkdConnectionException:
                pass
        else:
            self.skipTest('Skipping test since Splunk authentication data is not available')

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

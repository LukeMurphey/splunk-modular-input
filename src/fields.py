
import re
import os

try:
    from urlparse import urlparse
except:
    from urllib.parse import urlparse

from .exceptions import FieldValidationException
from .universal_forwarder_compatiblity import UF_MODE, make_splunkhome_path
from .contrib.ipaddress import ip_network

try:
    from .server_info import ServerInfo
except ImportError:
    ServerInfo = None

class Field(object):
    """
    This is the base class that should be used to for field validators. Sub-class this and
    override to_python if you need custom validation.
    """

    DATA_TYPE_STRING = 'string'
    DATA_TYPE_NUMBER = 'number'
    DATA_TYPE_BOOLEAN = 'boolean'

    def get_data_type(self):
        """
        Get the type of the field.
        """

        return Field.DATA_TYPE_STRING

    def __init__(self, name, title, description, none_allowed=False, empty_allowed=True,
                 required_on_create=None, required_on_edit=None):
        """
        Create the field.

        Arguments:
        name -- Set the name of the field (e.g. "database_server")
        title -- Set the human readable title (e.g. "Database server")
        description -- Set the human readable description of the field (e.g. "The IP or domain name
                       of the database server")
        none_allowed -- Is a value of none allowed?
        empty_allowed -- Is an empty string allowed?
        required_on_create -- Is this field required when creating?
        required_on_edit -- Is this field required when editing?
        """

        # Try to set required_on_create and required_on_edit to sane defaults if not defined
        if required_on_create is None and none_allowed:
            required_on_create = False
        elif required_on_create is None and not none_allowed:
            required_on_create = True

        if required_on_edit is None and required_on_create is not None:
            required_on_edit = required_on_create

        if name is None:
            raise ValueError("The name parameter cannot be none")

        if len(name.strip()) == 0:
            raise ValueError("The name parameter cannot be empty")

        if title is None:
            raise ValueError("The title parameter cannot be none")

        if len(title.strip()) == 0:
            raise ValueError("The title parameter cannot be empty")

        if description is None:
            raise ValueError("The description parameter cannot be none")

        if len(description.strip()) == 0:
            raise ValueError("The description parameter cannot be empty")

        self.name = name
        self.title = title
        self.description = description

        self.none_allowed = none_allowed
        self.empty_allowed = empty_allowed
        self.required_on_create = required_on_create
        self.required_on_edit = required_on_edit

    def to_python(self, value, session_key=None):
        """
        Convert the field to a Python object. Should throw a FieldValidationException if the data
        is invalid.

        Arguments:
        value -- The value to convert
        session_key- The session key to access Splunk (if needed)
        """

        if not self.none_allowed and value is None:
            raise FieldValidationException("The value for the '%s' parameter cannot be empty" % (self.name))

        if not self.empty_allowed and len(str(value).strip()) == 0:
            raise FieldValidationException("The value for the '%s' parameter cannot be empty" % (self.name))

        return value

    def to_string(self, value):
        """
        Convert the field to a string value that can be returned. Should throw a
        FieldValidationException if the data is invalid.

        Arguments:
        value -- The value to convert
        """

        return str(value)

class BooleanField(Field):
    """
    A validator that converts string versions of boolean to a real boolean.
    """

    def to_python(self, value, session_key=None):
        Field.to_python(self, value, session_key)

        if value in [True, False]:
            return value

        elif str(value).strip().lower() in ["true", "1"]:
            return True

        elif str(value).strip().lower() in ["false", "0"]:
            return False

        raise FieldValidationException("The value of '%s' for the '%s' parameter is not a valid boolean" % (str(value), self.name))

    def to_string(self, value):

        if value == True:
            return "1"

        elif value == False:
            return "0"

        return str(value)

    def get_data_type(self):
        return Field.DATA_TYPE_BOOLEAN

class ListField(Field):
    """
    A validator that converts a comma seperated string to an array.

    You can use the instance_class argument to convert individual items in the array to particular
    type. That way, you can have a list of Python objects that are already converted to the values
    you want. Consider this example that will include a list of parsed IP network ranges:

        list_field = ListField('name', 'title', 'description', instance_class=IPNetworkField)
        parsed_ip_ranges = list_field.to_python(u'10.0.0.0/28,1.2.3.4,10.0.1.0/28')
    """

    def __init__(self, name, title, description, none_allowed=False, empty_allowed=True,
                 required_on_create=None, required_on_edit=None, instance_class=None,
                 trim_values=False):
        """
        Create the field.

        Arguments:
        name -- Set the name of the field (e.g. "database_server")
        title -- Set the human readable title (e.g. "Database server")
        description -- Set the human readable description of the field (e.g. "The IP or domain name
                       of the database server")
        none_allowed -- Is a value of none allowed?
        empty_allowed -- Is an empty string allowed?
        required_on_create -- Is this field required when creating?
        required_on_edit -- Is this field required when editing?
        instance_class -- The name of the class to use for constructing individual objects
        trim_values -- Trim whitespace off of the ends of the values in case that spaces between
                       the list are not included
        """

        super(ListField, self).__init__(name, title, description, none_allowed, empty_allowed, required_on_create, required_on_edit)
        self.instance_class = instance_class
        self.trim_values = trim_values

        # Create an instance for converting the values
        if self.instance_class is not None:
            self.instance = self.instance_class(self.name, self.title, self.description)
        else:
            self.instance = None

    def to_python(self, value, session_key=None):
        Field.to_python(self, value, session_key)

        # Convert the value into an array
        values_list = None

        if value is not None:
            values_list = value.split(",")
        else:
            values_list = []

        # Trim the values if requested
        if self.trim_values:
            values_list = [value.strip() for value in values_list]

        # If we have no instances class, then just return the plain list
        if self.instance_class is None:
            return values_list

        # Otherwise, convert the instances accordingly
        else:
            # Convert the value
            instances_list = []
            for instance_value in values_list:
                instances_list.append(self.instance.to_python(instance_value))

            return instances_list

    def to_string(self, value):

        if value is not None:

            # Use the instance to_string if we have an instance
            if self.instance is not None:
                values_list = []

                for individual_value in value:
                    values_list.append(self.instance.to_string(individual_value))
                
                return ",".join(values_list)

            # Otherwise, process it as a string
            else:
                return ",".join(value)

        return ""

class StaticListField(Field):
    """
    This allows you to specify a list of field values that are allowed.
    All other values will be rejected.
    """

    _valid_values = None
    
    def __init__(self, name, title, description, none_allowed=False, empty_allowed=True, required_on_create=None, required_on_edit=None, valid_values=None):
        super(StaticListField, self).__init__(name, title, description, none_allowed, empty_allowed, required_on_create, required_on_edit)
        
        self.valid_values = valid_values

    @property
    def valid_values(self):
        return self._valid_values

    @valid_values.setter
    def valid_values(self, values):
        self._valid_values = values

    def to_python(self, value, session_key=None):

        Field.to_python(self, value, session_key)

        if value is None:
            return None
        elif value not in self.valid_values:
            raise FieldValidationException('The value of the "' + self.name + '" field is invalid, it must be one of:' + ','.join(self.valid_values))
        else:
            return value

class RegexField(Field):
    """
    A validator that validates input matches a regular expression.
    """

    def to_python(self, value, session_key=None):

        Field.to_python(self, value, session_key)

        if value is not None:
            try:
                return re.compile(value)
            except Exception as exception:
                raise FieldValidationException(str(exception))
        else:
            return None

    def to_string(self, value):

        if value is not None:
            return value.pattern

        return ""

class WildcardField(Field):
    """
    Much like a regular expression field but takes wildcards. This will return a regular expression.
    """

    def to_python(self, value, session_key=None):
    
        Field.to_python(self, value, session_key)

        if value is not None:
            try:
                regex_escaped = re.escape(value)
                regex_escaped = regex_escaped.replace('\*', ".*")
                return re.compile(regex_escaped)
            except Exception as exception:
                raise FieldValidationException(str(exception))
        else:
            return None

    def to_string(self, value):

        if value is not None:
            return value.pattern

        return ""

class IntegerField(Field):
    """
    A validator that converts string input to an integer.
    """

    def to_python(self, value, session_key=None):

        Field.to_python(self, value, session_key)

        if value is not None:
            try:
                return int(value)
            except ValueError as exception:
                raise FieldValidationException(str(exception))
        else:
            return None

    def to_string(self, value):

        if value is not None:
            return str(value)

        return ""

    def get_data_type(self):
        return Field.DATA_TYPE_NUMBER

class FloatField(Field):
    """
    A validator that converts string input to a float.
    """

    def to_python(self, value, session_key=None):

        Field.to_python(self, value, session_key)

        if value is not None:
            try:
                return float(value)
            except ValueError as exception:
                raise FieldValidationException(str(exception))
        else:
            return None

    def to_string(self, value):

        if value is not None:
            return str(value)

        return ""

    def get_data_type(self):
        return Field.DATA_TYPE_NUMBER

class RangeField(Field):
    """
    A validator that converts string input to a pair of integers indicating a range.
    """

    def __init__(self, name, title, description, low, high, none_allowed=False, empty_allowed=True, required_on_create=None, required_on_edit=None):

        super(RangeField, self).__init__(name, title, description, none_allowed,
                                         empty_allowed, required_on_create, required_on_edit)

        self.low = low
        self.high = high

    def to_python(self, value, session_key=None):

        Field.to_python(self, value, session_key)

        if value is not None:
            try:
                tmp = int(value)
                if tmp < self.low:
                    raise FieldValidationException("The value of '%s' for the '%s' parameter must be greater than or equal to '%r'" % (str(value), self.name, self.low))
                if tmp > self.high:
                    raise FieldValidationException("The value of '%s' for the '%s' parameter must be less than or equal to '%r'" % (str(value), self.name, self.high))

                return tmp
            except ValueError as exception:
                raise FieldValidationException(str(exception))
        else:
            return None

    def to_string(self, value):

        if value is not None:
            return str(value)

        return ""

    def get_data_type(self):
        return Field.DATA_TYPE_NUMBER

class URLField(Field):
    """
    Represents a URL. The URL is converted to a Python object that was created via urlparse.
    """

    require_https_on_cloud = False

    def __init__(self, name, title, description, none_allowed=False, empty_allowed=True,
                 required_on_create=None, required_on_edit=None, require_https_on_cloud=False):

        super(URLField, self).__init__(name, title, description, none_allowed,
                                       empty_allowed, required_on_create, required_on_edit)

        self.require_https_on_cloud = require_https_on_cloud

    @classmethod
    def parse_url(cls, value, name):
        """
        Parse a URL and generation an exception if it is invalid.BaseException
        Otherwise, return a parsed URL (via urlparse).
        """

        parsed_value = urlparse(value)

        if parsed_value.hostname is None or len(parsed_value.hostname) <= 0:
            raise FieldValidationException("The value of '%s' for the '%s' parameter does not contain a host name" % (str(value), name))

        if parsed_value.scheme not in ["http", "https"]:
            raise FieldValidationException("The value of '%s' for the '%s' parameter does not contain a valid protocol (only http and https are supported)" % (str(value), name))

        return parsed_value

    def to_python(self, value, session_key=None):
        Field.to_python(self, value, session_key)

        parsed_value = URLField.parse_url(value.strip(), self.name)

        if self.require_https_on_cloud and parsed_value.scheme == "http" and session_key is not None and ServerInfo.is_on_cloud(session_key):
            raise FieldValidationException("The value of '%s' for the '%s' parameter must use encryption (be HTTPS not HTTP)" % (str(value), self.name))

        return parsed_value

    def to_string(self, value):
        return value.geturl()

class DurationField(Field):
    """
    The duration field represents a duration as represented by a string such as 1d for a 24 hour
    period.

    The string is converted to an integer indicating the number of seconds.
    """

    DURATION_RE = re.compile("(?P<duration>[0-9]+)\s*(?P<units>[a-z]*)", re.IGNORECASE)

    MINUTE = 60
    HOUR = 60 * MINUTE
    DAY = 24 * HOUR
    WEEK = 7 * DAY

    UNITS = {
        'w' : WEEK,
        'week' : WEEK,
        'd' : DAY,
        'day' : DAY,
        'h' : HOUR,
        'hour' : HOUR,
        'm' : MINUTE,
        'min' : MINUTE,
        'minute' : MINUTE,
        's' : 1
    }

    def to_python(self, value, session_key=None):
        Field.to_python(self, value, session_key)

        # Parse the duration
        duration_match = DurationField.DURATION_RE.match(value)

        # Make sure the duration could be parsed
        if duration_match is None:
            raise FieldValidationException("The value of '%s' for the '%s' parameter is not a valid duration" % (str(value), self.name))

        # Get the units and duration
        match_dict = duration_match.groupdict()

        units = match_dict['units']

        # Parse the value provided
        try:
            duration = int(match_dict['duration'])
        except ValueError:
            raise FieldValidationException("The duration '%s' for the '%s' parameter is not a valid number" % (match_dict['duration'], self.name))

        # Make sure the units are valid
        if len(units) > 0 and units not in DurationField.UNITS:
            raise FieldValidationException("The unit '%s' for the '%s' parameter is not a valid unit of duration" % (units, self.name))

        # Convert the units to seconds
        if len(units) > 0:
            return duration * DurationField.UNITS[units]
        else:
            return duration

    def to_string(self, value):
        return str(value)

class DeprecatedField(Field):
    """
    Represents a field that is no longer used. This should be used when you want the input to pass
    validation with arguments that are no longer used.
    """

    def __init__(self, name, title, description, none_allowed=True, empty_allowed=True,
                 required_on_create=False, required_on_edit=False):
        """
        Create the field.

        Arguments:
        name -- Set the name of the field (e.g. "database_server")
        title -- Set the human readable title (e.g. "Database server")
        description -- Set the human readable description of the field (e.g. "The IP or domain name of the database server")
        none_allowed -- Is a value of none allowed?
        empty_allowed -- Is an empty string allowed?
        required_on_create -- Is this field required when creating?
        required_on_edit -- Is this field required when editing?
        """

        super(DeprecatedField, self).__init__(name, title, description,
                                              none_allowed=none_allowed,
                                              empty_allowed=empty_allowed,
                                              required_on_create=required_on_create,
                                              required_on_edit=required_on_edit)

    def to_python(self, value, session_key=None):
        return None

    def to_string(self, value):
        return ""

class FilePathField(Field):
    '''
    Represents a path to file.
    '''

    def __init__(self, name, title, description, none_allowed=False, empty_allowed=True,
                 required_on_create=None, required_on_edit=None, validate_file_existence=True):
        """
        Create the field.

        Arguments:
        name -- Set the name of the field (e.g. "database_server")
        title -- Set the human readable title (e.g. "Database server")
        description -- Set the human readable description of the field (e.g. "The IP or domain name
                       of the database server")
        none_allowed -- Is a value of none allowed?
        empty_allowed -- Is an empty string allowed?
        required_on_create -- Is this field required when creating?
        required_on_edit -- Is this field required when editing?
        validate_file_existence -- If true, this field will generate an error if the file doesn't exist
        """
        super(FilePathField, self).__init__(name, title, description, none_allowed, empty_allowed, required_on_create, required_on_edit)

        self.validate_file_existence = validate_file_existence

    def to_python(self, value, session_key=None):

        Field.to_python(self, value, session_key)

        # Don't bother validating if the parameter wasn't provided
        if value is None or len(value.strip()) == 0:
            return value

        # Resolve the file path as necessary
        resolved_path = None

        if value is not None:
            if os.path.isabs(value) or UF_MODE:
                resolved_path = value
            else:
                path = os.path.join(make_splunkhome_path([value]))
                resolved_path = path

        # Validate the file existence if requested
        if self.validate_file_existence and not os.path.isfile(resolved_path):
            raise FieldValidationException("The parameter '%s' is not a valid path; '%s' does not exist" % (self.name, resolved_path))

        return resolved_path

    def to_string(self, value):
        return value

class DomainNameField(Field):
    """
    A validator that accepts domain names.
    """

    def is_valid_hostname(self, dn):
        """
        Determine if the given hostname is valid.
        See https://stackoverflow.com/questions/2532053/validate-a-hostname-string
        """
        if dn.endswith('.'):
            dn = dn[:-1]
        if len(dn) < 1 or len(dn) > 253:
            return False
        ldh_re = re.compile('^[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?$',
                            re.IGNORECASE)
        return all(ldh_re.match(x) for x in dn.split('.'))

    def to_python(self, value, session_key=None):
        Field.to_python(self, value, session_key)

        if value is not None:
            
            if not self.is_valid_hostname(value):
                raise FieldValidationException("The value of '%s' for the '%s' parameter is not a valid domain name" % (value, self.name))

            return value
        else:
            return None

class MultiValidatorField(Field):
    
    def __init__(self, name, title, description, none_allowed=False, empty_allowed=True,
                 required_on_create=None, required_on_edit=None, validators=None, default_message=None):
        """
        Create the field.

        Arguments:
        name -- Set the name of the field (e.g. "database_server")
        title -- Set the human readable title (e.g. "Database server")
        description -- Set the human readable description of the field (e.g. "The IP or domain name
                       of the database server")
        none_allowed -- Is a value of none allowed?
        empty_allowed -- Is an empty string allowed?
        required_on_create -- Is this field required when creating?
        required_on_edit -- Is this field required when editing?
        validate_file_existence -- If true, this field will generate an error if the file doesn't exist
        """
        super(MultiValidatorField, self).__init__(name, title, description, none_allowed, empty_allowed, required_on_create, required_on_edit)

        # Stop if no validators were supplied
        if validators is None or len(validators) == 0:
            raise Exception("A list of the validators is required for the MultiValidatorField to test against")

        # Here is where all of the instances of the validators will be stored
        self.validators = []

        # Construct the validator instances
        for validator in validators:
            self.validators.append(validator(self.name, self.title, self.description, self.none_allowed, self.empty_allowed, self.required_on_create, self.required_on_edit))

        # This will point to the last validator instance that accepted the last value
        self.last_used_validator = None

        # Persist the error message
        self.default_message = default_message

    def to_python(self, value, session_key=None):
        Field.to_python(self, value, session_key)

        if value is not None:
            messages =[]

            for validator in self.validators:
                try:
                    python_value = validator.to_python(value, session_key)
                    self.last_used_validator = validator
                    return python_value
                except FieldValidationException as e:
                    messages.append(str(e))

            # Generate an exception since the field could not be validated
            if self.default_message is None:
                raise FieldValidationException(";".join(messages))
            else:
                raise FieldValidationException(self.default_message)
        else:
            return None

    def to_string(self, value):
        if value is not None:
            return self.last_used_validator.to_string(value)

        return ""

class IPNetworkField(Field):
    """
    A validator that accepts IP addresses.
    """

    def to_python(self, value, session_key=None):
        Field.to_python(self, value, session_key)

        if value is not None:
            # Convert the incoming string to bytes
            # For Python 2, str works fine since it is just bytes. Python 3 defaults to unicode which needs to be converted.
            try:
                unicode
                if not isinstance(value, unicode):
                    value = unicode(value)
                # The interpreter is Python 2
            except NameError:
                # The interpreter is Python 3, it is unicode already
                pass
            
            try:
                return ip_network(value, strict=False)
            except ValueError as exception:
                raise FieldValidationException(str(exception))
        else:
            return None

    def to_string(self, value):
        if value is not None:
            # Get the main address if this is a single address
            if value.num_addresses == 1:
                return str(value.network_address)
            else:
                return str(value)

        return ""

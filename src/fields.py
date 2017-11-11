
import re
import os
from urlparse import urlparse

from .exceptions import FieldValidationException
from .modular_input_base_class import ModularInput
from .universal_forwarder_compatiblity import UF_MODE, make_splunkhome_path

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
    """

    def to_python(self, value, session_key=None):

        Field.to_python(self, value, session_key)

        if value is not None:
            return value.split(",")
        else:
            return []

    def to_string(self, value):

        if value is not None:
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

    def __init__(self, name, title, description, low, high, none_allowed=False, empty_allowed=True):

        super(RangeField, self).__init__(name, title, description, none_allowed=False,
                                         empty_allowed=True)

        self.low = low
        self.high = high

    def to_python(self, value, session_key=None):

        Field.to_python(self, value, session_key)

        if value is not None:
            try:
                tmp = int(value)
                return tmp >= self.low and tmp <= self.high
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

        if self.require_https_on_cloud and parsed_value.scheme == "http" and session_key is not None and ModularInput.is_on_cloud(session_key):
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

"""
This module includes a series of libraries that are useful for allowing modular inputs to work on
Univeral Forwarder instances that don't include the Python interpeter and thus don't have access
to Splunk's libraries.

The functions provided will default to using the Splunk function if available. Otherwise, the
built-in function will be used.
"""

import os

# Try to load Splunk's libraries. An inability to do so likely means we are running on a universal
# forwarder (since it doesn't include Python). We will proceed but will be unable to access
# Splunk's endpoints via simple request which means we will not able to load secure credentials.
try:
    from splunk.clilib.bundle_paths import make_splunkhome_path as core_make_splunkhome_path
    from splunk.util import normalizeBoolean as core_normalizeBoolean
    UF_MODE = False
except:
    UF_MODE = True

def make_splunkhome_path(path, use_built_in=None):
    """
    This wraps Splunk's make_splunkhome_path in case this host is running a Universal Forwarder
    and doesn't have access to the built-in make_splunkhome_path function.
    """

    if use_built_in is True or UF_MODE:
        return os.path.join(os.environ['SPLUNK_HOME'], *path)
    else:
        return core_make_splunkhome_path(path)

def normalizeBoolean(value, use_built_in=None):
    """
    This wraps Splunk's normalizeBoolean in case this host is running a Universal Forwarder
    and doesn't have access to the built-in normalizeBoolean function.
    """

    if use_built_in is True or UF_MODE:
        if str(value).strip().lower() in ['1', 'true']:
            return True
        else:
            return False
    else:
        return core_normalizeBoolean(value)

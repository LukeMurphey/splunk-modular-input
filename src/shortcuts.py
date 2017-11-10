
import os

# Try to load Splunk's libraries. An inability to do so likely means we are running on a universal
# forwarder (since it doesn't include Python). We will proceed but will be unable to access
# Splunk's endpoints via simple request which means we will not able to load secure credentials.
try:
    from splunk.appserver.mrsparkle.lib.util import make_splunkhome_path as core_make_splunkhome_path
    from splunk.util import normalizeBoolean
    import splunk.rest
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
    if use_built_in is True and UF_MODE:
        if str(value).strip().lower() in ['1', 'true']:
            return True
        else:
            return False
    else:
        return normalizeBoolean(value)

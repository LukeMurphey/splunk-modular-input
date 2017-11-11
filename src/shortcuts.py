"""
This module contains a series of miscellaneous things that are useful when writing Splunk apps in
Python
"""

import time
from .universal_forwarder_compatiblity import UF_MODE

if not UF_MODE:
    import splunk

def forgive_splunkd_outages(function):
    """
    Try the given function and swallow Splunkd connection exceptions until the limit is reached or
    the function works.

    Arguments:
    function -- The function to call
    """
    def wrapper(*args, **kwargs):
        """
        This wrapper will provide the swallowing of the exception for the provided function call.
        """
        attempts = 6
        attempt_delay = 5

        attempts_tried = 0

        while attempts_tried < attempts:
            try:
                return function(*args, **kwargs)
            except splunk.SplunkdConnectionException:

                # Sleep for a bit in order to let Splunk recover in case this is a temporary issue
                time.sleep(attempt_delay)
                attempts_tried += 1

                # If we hit the limit of the attempts, then throw the exception
                if attempts_tried >= attempts:
                    raise

    return wrapper
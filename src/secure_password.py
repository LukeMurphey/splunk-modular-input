"""
This module provides some helper functions for accessing secure credentials in Splunk.

The two main functions that you may want to use are:

    1) get_secure_password_by_realm
    2) get_secure_password
"""

import json

from .universal_forwarder_compatiblity import UF_MODE
from .shortcuts import forgive_splunkd_outages

if not UF_MODE:
    import splunk

def escape_colons(string_to_escape):
    """
    Escape the colons. This is necessary for secure password stanzas.
    """
    return string_to_escape.replace(":", "\\:")

def get_secure_password_stanza(username, realm=""):
    """
    Make the stanza name for a entry in the storage/passwords endpoint from the username and
    realm.
    """
    return escape_colons(realm) + ":" + escape_colons(username) + ":"

@forgive_splunkd_outages
def get_secure_password(realm, username=None, session_key=None, logger=None):
    """
    Get the secure password that matches the given realm and username. If no username is
    provided, the first entry with the given realm will be returned.
    """

    if UF_MODE:
        if logger:
            logger.warn("Unable to retrieve the secure credential since the input appears " +
                        "to be running in a Univeral Forwarder")
        # Cannot get the secure password in universal forwarder mode since we don't
        # have access to Splunk libraries
        return None

    # Look up the entry by realm only if no username is provided.
    if username is None or len(username) == 0:
        return get_secure_password_by_realm(realm, session_key)

    # Get secure password
    stanza = get_secure_password_stanza(username, realm)
    try:
        server_response, server_content = splunk.rest.simpleRequest('/services/storage/passwords/' + stanza + '?output_mode=json', sessionKey=session_key)
    except splunk.ResourceNotFound:
        return None

    if server_response['status'] == '404':
        return None
    elif server_response['status'] != '200':
        raise Exception("Could not get the secure passwords")

    passwords_content = json.loads(server_content)
    password = passwords_content['entry']

    return password[0]

@forgive_splunkd_outages
def get_secure_password_by_realm(realm, session_key):
    """
    Get the secure password that matches the given realm.
    """

    # Get secure passwords
    server_response, server_content = splunk.rest.simpleRequest('/services/storage/passwords?output_mode=json', sessionKey=session_key)

    if server_response['status'] != '200':
        raise Exception("Could not get the secure passwords")

    passwords_content = json.loads(server_content)
    passwords = passwords_content['entry']

    # Filter down output to the ones matching the realm
    matching_passwords = filter(lambda x: x['content']['realm'] == realm, passwords)

    if len(matching_passwords) > 0:
        return matching_passwords[0]
    else:
        return None

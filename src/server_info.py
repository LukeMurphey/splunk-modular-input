import json
import socket

from .universal_forwarder_compatiblity import UF_MODE
from .shortcuts import forgive_splunkd_outages

if not UF_MODE:
    from splunk.rest import simpleRequest
class ServerInfo(object):
    """
    This class returns information about the Splunk server that is running this code.
    """

    server_info = None

    shc_info = None
    shc_enabled = None

    @classmethod
    @forgive_splunkd_outages
    def get_server_info(cls, session_key, force_refresh=False):
        """
        Get the server information object.
        """

        # This isn't supported on a universal forwarder
        if UF_MODE:
            return None

        # Use the cached server information if possible
        if not force_refresh and cls.server_info is not None:
            return cls.server_info

        # Get the server info
        _, server_content = simpleRequest('/services/server/info/server-info?output_mode=json', sessionKey=session_key)

        info_content = json.loads(server_content)
        cls.server_info = info_content['entry'][0]

        return cls.server_info

    @classmethod
    @forgive_splunkd_outages
    def is_on_cloud(cls, session_key):
        """
        Determine if the host is running on cloud.
        """

        server_info = cls.get_server_info(session_key)

        return server_info['content'].get('instance_type', None) == 'cloud'

    @classmethod
    @forgive_splunkd_outages
    def get_shc_cluster_info(cls, session_key):
        """
        Get the SHC cluster information.
        """

        # This isn't supported on a universal forwarder
        if UF_MODE:
            return None

        # Get the shc cluster info
        try:
            response, server_content = simpleRequest('/services/shcluster/status?output_mode=json', sessionKey=session_key)

            # If we get a 200 code then this is using SHC
            if response.status == 200:
                cls.shc_enabled = True

                info_content = json.loads(server_content)
                cls.shc_info = info_content['entry'][0]
            else:
                cls.shc_enabled = False

        except splunk.ResourceNotFound:
            # This shouldn't generate a 404 from what I can tell but if it does then I would say
            # SHC is disabled
            cls.shc_enabled = False
        except splunk.LicenseRestriction:
            # This host may be using the dev license
            cls.shc_enabled = False

        return cls.shc_info

    @classmethod
    @forgive_splunkd_outages
    def is_on_shc(cls, session_key):
        """
        Determine if the host is running on SHC.
        """

        # This isn't supported on a universal forwarder
        if UF_MODE:
            return False

        # Use the cached server information if possible
        if cls.shc_enabled is not None:
            return cls.shc_enabled

        # Get the shc cluster info
        try:
            response, _ = simpleRequest('/services/shcluster/status?output_mode=json', sessionKey=session_key)

            # If we get a 200 code then this is using SHC
            if response.status == 200:
                cls.shc_enabled = True
            else:
                cls.shc_enabled = False
        except splunk.ResourceNotFound:
            # This shouldn't generate a 404 from what I can tell but if it does then I would say
            # SHC is disabled
            cls.shc_enabled = False
        except splunk.LicenseRestriction:
            # This host may be using the dev license
            cls.shc_enabled = False

        return cls.shc_enabled

    @classmethod
    def get_dict_object(cls, dict, keys, default_value=None):
        """
        Get the object with the given set of nested dictionaries with the given name. If the item
        cannot be found, return the provided default value.
        """

        current_value = dict

        for key in keys:
            if key in current_value:
                current_value = current_value[key]
            else:
                return default_value

        return current_value    

    @classmethod
    @forgive_splunkd_outages
    def is_shc_captain(cls, session_key):
        """
        Determine if the host is the SHC captain.

        This will be done by comparing the label from /services/shcluster/status to the serverName
        field from /services/server/info and the host name.

        This function will return one of the following:
            - None: this host isn't running SHC
            - True: this host is running SHC and it is the captain
            - False: this host is running SHC and but it is not the captain
        """

        # Determine if this host is running on SHC
        if not cls.is_on_shc(session_key):
            return None

        # Get the server information
        server_info = cls.get_server_info(session_key)
        server_name = server_info['content'].get('serverName', None)

        # Get the host name
        host_name = socket.gethostname()

        # Get the SHC captain name
        shc_info = cls.get_shc_cluster_info(session_key)

        if shc_info is not None:
            shc_captain = cls.get_dict_object(shc_info, ['content', 'captain', 'label'])
  
            if shc_captain == host_name or shc_captain == server_name:
                return True

        return False

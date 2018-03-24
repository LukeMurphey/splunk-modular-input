import json
import splunk

from .shortcuts import forgive_splunkd_outages

class ServerInfo(object):
    """
    This class returns information about the Splunk server that is running this code.
    """

    server_info = None
    shc_enabled = None

    @classmethod
    @forgive_splunkd_outages
    def get_server_info(cls, session_key, force_refresh=False):
        """
        Get the server information object.
        """

        # Use the cached server information if possible
        if not force_refresh and cls.server_info is not None:
            return cls.server_info

        # Get the server info
        _, server_content = splunk.rest.simpleRequest('/services/server/info/server-info?output_mode=json', sessionKey=session_key)

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
    def is_on_shc(cls, session_key):
        """
        Determine if the host is running on SHC.
        """

        # Use the cached server information if possible
        if cls.shc_enabled is not None:
            return cls.shc_enabled

        # Get the shc cluster info
        try:
            response, _ = splunk.rest.simpleRequest('/services/shcluster/status?output_mode=json', sessionKey=session_key)

            # If we get a 200 code then this is using SHC
            if response.status == 200:
                cls.shc_enabled = True
            else:
                cls.shc_enabled = False
        except splunk.ResourceNotFound:
            # This shouldn't generate a 404 from what I can tell but if it does then I would say
            # SHC is disabled
            cls.shc_enabled = False

        return cls.shc_enabled

import json
import splunk

from .shortcuts import forgive_splunkd_outages

class ServerInfo(object):
    """
    This class returns information about the Splunk server that is running this code.
    """

    server_info = None

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

# Splunk Modular Input
This project builds a base class that makes it simple to write Python modular inputs for Splunk.

## How to use this library

To make a modular input based on this class, you should follow the steps defined below.

Note that this example assumes you are making an input named "my_input_name".

### 1) Define the input in inputs.conf.spec

You will need to define you input in a spec file within the following directory within your app:

    README/inputs.conf.spec

You should define your input in the inputs.conf.spec by declaring the fields your input accepts.
This file should look something like this:

    [my_input_name://default]
    * Configure an input for do something

    title = <value>
    * The title of the input

    url = <value>
    * The URL to be checked

### 2) Include this module in your app

Put this module within your app. You can put this within you bin directory or within a
sub-directory of the bin directory. I generally recommend putting python modules under the bin
directory with a directory that is specific to your app. Something like:

    bin/my_app_name/modular_input.zip

## 3) Define defaults for your inputs in inputs.conf

You can define default values for your inputs within the inputs.conf file. This file would be:

    default/inputs.conf

The contents of the file would be something like this:

    [my_input_name]
    url = http://mydefaulturl.com


## 4) Create your modular input class

Create your modular input class. This class must be named the same as your input name and it must
be placed within the bin directory. In this example, the input should be in the following path
since the input is named "my_input_name":

    bin/my_input_name.py

Below is an example of a modular input class. This class does the following:

 1. Defines the scheme_args which provides some info about the modular input
 2. Defines the parameters that the input accepts
 3. Runs the modular input

```python
    import sys
    import os
    path_to_mod_input_lib = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modular_input.zip')
    sys.path.insert(0, path_to_mod_input_lib)

    from modular_input import Field, ModularInput, URLField

    class MyInput(ModularInput):
        def __init__(self, timeout=30):

            scheme_args = {'title': "My input name",
                           'description': "This input is an example",
                           'use_external_validation': "true",
                           'streaming_mode': "xml",
                           'use_single_instance': "true"}

            args = [
                    Field("title", "Title", "A short description of the input", empty_allowed=False),
                    URLField("url", "URL", "The URL to connect to", empty_allowed=False)
            ]

            ModularInput.__init__(self, scheme_args, args, logger_name='my_input_modular_input')

        def run(self, stanza, cleaned_params, input_config):

            interval = cleaned_params["interval"]
            title = cleaned_params["title"]
            host = cleaned_params.get("host", None)
            index = cleaned_params.get("index", "default")
            sourcetype = cleaned_params.get("sourcetype", "my_app_name")

            url = cleaned_params["url"]

            if self.needs_another_run(input_config.checkpoint_dir, stanza, interval):
                self.logger.debug("Your input should do something here, stanza=%s", stanza)

    if __name__ == '__main__':
        MyInput.instantiate_and_execute()
```

## Other projects that may be of interest

 * Admin XML modules for customizing modular input page: https://github.com/LukeMurphey/splunk-admin-xml-modules
 * Example of creating a simpleXML setup script: https://github.com/LukeMurphey/splunk-simplexml-setup-example
 * Example of writing a search command in Splunk: https://github.com/LukeMurphey/splunk-search-command-example
 * Splunk apps build / delivery script: https://github.com/LukeMurphey/splunk-ant-build-script
 * Splunk Javascript tutorial: https://github.com/LukeMurphey/splunk-hello-splunkjs
 * Example of using Splunk's step control wizard: https://github.com/LukeMurphey/splunk-step-wizard-control-example
 * Splunk modular alert example: https://github.com/LukeMurphey/splunk-modular-alert-example

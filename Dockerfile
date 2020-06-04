FROM netboxcommunity/netbox:latest-ldap

COPY ./nextbox_ui_plugin /source/nextbox-ui-plugin/nextbox_ui_plugin/
COPY ./setup.py /source/nextbox-ui-plugin/
COPY ./MANIFEST.in /source/nextbox-ui-plugin/
COPY ./README.md /source/nextbox-ui-plugin/
RUN pip3 install nextbox-ui-plugin

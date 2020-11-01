ARG FROM_IMAGE=netboxcommunity/netbox
ARG FROM_TAG=latest-ldap
ARG FROM=${FROM_IMAGE}:${FROM_TAG}
FROM ${FROM}

COPY ./nextbox_ui_plugin /source/nextbox-ui-plugin/nextbox_ui_plugin/
COPY ./setup.py /source/nextbox-ui-plugin/
COPY ./MANIFEST.in /source/nextbox-ui-plugin/
COPY ./README.md /source/nextbox-ui-plugin/
RUN pip3 install --no-cache-dir nextbox-ui-plugin

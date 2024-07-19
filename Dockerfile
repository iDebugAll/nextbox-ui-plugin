ARG FROM_IMAGE=netboxcommunity/netbox
ARG FROM_TAG=latest-ldap
ARG FROM=${FROM_IMAGE}:${FROM_TAG}
FROM ${FROM}

ENV VIRTUAL_ENV=/opt/netbox/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY ./nextbox_ui_plugin /source/nextbox-ui-plugin/nextbox_ui_plugin/
COPY ./setup.py /source/nextbox-ui-plugin/
COPY ./MANIFEST.in /source/nextbox-ui-plugin/
COPY ./README.md /source/nextbox-ui-plugin/
COPY --chown=100:101 --chmod=644 ./nextbox_ui_plugin/static/nextbox_ui_plugin /opt/netbox/netbox/static/nextbox_ui_plugin
RUN pip3 install --no-cache-dir nextbox-ui-plugin
RUN find  /opt/netbox/netbox/static/nextbox_ui_plugin -type d -exec chmod 755 {} +


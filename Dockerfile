ARG FROM_IMAGE=netboxcommunity/netbox
ARG FROM_TAG=latest-ldap
ARG FROM=${FROM_IMAGE}:${FROM_TAG}
FROM ${FROM}

ENV VIRTUAL_ENV=/opt/netbox/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"
COPY netbox_topology_plugin /source/netbox-topology-plugin/netbox_topology_plugin/
COPY ./setup.py /source/netbox-topology-plugin/
COPY ./MANIFEST.in /source/netbox-topology-plugin/
COPY ./README.md /source/netbox-topology-plugin/
COPY --chown=1000:1000 --chmod=644 netbox_topology_plugin/static/netbox_topology_plugin /opt/netbox/netbox/static/netbox_topology_plugin
RUN pip3 install --no-cache-dir netbox-topology-plugin

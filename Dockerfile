#
# MIT License
#
# (C) Copyright 2021-2023 Hewlett Packard Enterprise Development LP
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included
# in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR
# OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE,
# ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR
# OTHER DEALINGS IN THE SOFTWARE.
#
# This microservice is intended to be a dynamic ipxe building service. The
# purpose of this service is to respond to changes in the requested ipxe build
# environment and dynamically generate ipxe binaries used for booting.

# The most common form of this building environment is in support of https
# for downloading ipxe binaries from a secure location. The ipxe binaries
# themselves need to be dynamically recreated whenever the public CA cert
# changes.
ARG Upstream=artifactory.algol60.net
ARG IpxeTag=@CRAY-TPSW-IPXE-VERSION@
ARG Stable=stable
FROM $Upstream/csm-docker/$Stable/cray-tpsw-ipxe:$IpxeTag as base
RUN mkdir /app
WORKDIR /app
COPY requirements.txt requirements_test.txt constraints.txt /app/
RUN apt -y update && \
    apt -y install \
      build-essential \
      python3-dev \
      python3-venv \
      python3-pip \
      python3-setuptools \
      python3-wheel \
      libyaml-dev \
      openssl \
      coreutils \
    && python3 -m venv /app/venv \
    && /app/venv/bin/pip install --upgrade pip \
    && /app/venv/bin/pip install --no-cache-dir --upgrade wheel setuptools cython build \
    && /app/venv/bin/pip install --no-cache-dir -r /app/requirements.txt
RUN echo 'alias ll="ls -l"' > ~/.bashrc
RUN chown 65534:65534 -R /ipxe
COPY /src/crayipxe /app/crayipxe
ENTRYPOINT ["/app/venv/bin/python", "-m", "crayipxe.builds.x86-64"]
USER 65534:65534

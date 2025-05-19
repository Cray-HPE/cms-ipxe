#
# MIT License
#
# (C) Copyright 2021-2023, 2025 Hewlett Packard Enterprise Development LP
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

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl git make build-essential libssl-dev zlib1g-dev \
    libbz2-dev libreadline-dev libsqlite3-dev wget llvm \
    libncurses5-dev libncursesw5-dev xz-utils tk-dev \
    libffi-dev liblzma-dev python3-openssl coreutils ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PYENV_ROOT="/opt/pyenv"
ENV PATH="$PYENV_ROOT/bin:$PYENV_ROOT/shims:$PATH"

RUN curl https://pyenv.run | bash && \
    /opt/pyenv/bin/pyenv install 3.8.10 && \
    /opt/pyenv/bin/pyenv global 3.8.10 && \
    ln -sf /opt/pyenv/versions/3.8.10/bin/python3 /usr/local/bin/python3 && \
    python3 -m ensurepip && python3 -m pip install --upgrade pip

RUN chmod -R a+rX /opt/pyenv
RUN python3 -m pip install --no-cache-dir -r /app/requirements.txt
RUN echo 'alias ll="ls -l"' > ~/.bashrc
RUN chown 65534:65534 -R /ipxe
COPY src/crayipxe /app/crayipxe
ENTRYPOINT ["python3", "-m", "crayipxe.builds.x86-64"]
USER 65534:65534

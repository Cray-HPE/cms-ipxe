# This microservice is intended to be a dynamic ipxe building service. The
# purpose of this service is to respond to changes in the requested ipxe build
# environment and dynamically generate ipxe binaries used for booting.

# The most common form of this building environment is in support of https
# for downloading ipxe binaries from a secure location. The ipxe binaries
# themselves need to be dynamically recreated whenever the public CA cert
# changes.
FROM dtr.dev.cray.com/cray/cray-tpsw-ipxe:2.2.0-20210309205020_0b7ba7b
RUN mkdir /app
WORKDIR /app
COPY requirements.txt requirements_test.txt constraints.txt /app/

RUN apk add py3-pip openssl coreutils && \
    python3 -m pip install --upgrade pip && \
    python3 -m pip install --no-cache-dir -r /app/requirements.txt

RUN echo 'alias ll="ls -l"' > ~/.bashrc

COPY /src/crayipxe /app/crayipxe
CMD ["/usr/bin/python3", "-m", "crayipxe.service"]

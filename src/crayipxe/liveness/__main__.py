#
# MIT License
#
# (C) Copyright 2020-2023 Hewlett Packard Enterprise Development LP
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
'''
This entrypoint is used to determine if this service is still active/alive
from a kubernetes liveness probe perspective.

For the iPXE micro-service, it is deemed to be 'alive' and healthy if either
there is currently no iPXE binary being built or if the current build is
within the established time limit. 

Created on April 3rd, 2020

@author: jason.sollom
'''

import logging
import os
import sys

from crayipxe.liveness.ipxe_timestamp import ipxeTimestamp, LIVENESS_PATH, ipxeTimestampNoEnt

LOGGER = logging.getLogger(__name__)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    try:
        timestamp = ipxeTimestamp.byref(LIVENESS_PATH)
        if timestamp.alive:
            sys.exit(0)
        else:
            LOGGER.warning("Timestamp %s has expired")
            sys.exit(1)
    except ipxeTimestampNoEnt:
        LOGGER.warning("No timestamp information has been made available yet.")
        sys.exit(1)
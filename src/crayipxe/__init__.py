#
# MIT License
#
# (C) Copyright 2019-2022 Hewlett Packard Enterprise Development LP
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

import os
import logging

LOGGER = logging.getLogger(__name__)
IPXE_BUILD_DIR = '/ipxe'

# Use the HPC iPXE configuration.
# https://github.com/Cray-HPE/ipxe/tree/master/src/config/hpc
IPXE_CONFIG = 'hpc'

# Format logs and set the requested log level.
log_format = "%(asctime)-15s - %(levelname)-7s - %(name)s - %(message)s"
requested_log_level = os.environ.get('LOG_LEVEL', 'INFO')
log_level = logging.getLevelName(requested_log_level)

bad_log_level = None
if type(log_level) != int:
    bad_log_level = requested_log_level
    log_level = logging.INFO

logging.basicConfig(level=log_level, format=log_format)
if bad_log_level:
    LOGGER.warning('Log level %r is not valid. Falling back to INFO',
                   bad_log_level)



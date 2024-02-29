#!/usr/bin/env python3
#
# MIT License
#
# (C) Copyright 2023 Hewlett Packard Enterprise Development LP
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
import time
import os
import logging
import shutil
import threading
import subprocess
from yaml import safe_load
from tempfile import NamedTemporaryFile
from urllib.parse import urlparse

from crayipxe import IPXE_BUILD_DIR
from crayipxe.k8s_client import api_instance, client
from crayipxe.tokens import fetch_token, token_expiring_soon, TOKEN_HOST
from crayipxe.liveness.ipxe_timestamp import ipxeTimestamp, LIVENESS_PATH, liveliness_heartbeat

LOGGER = logging.getLogger(__name__)


class BinaryBuilder(object):
    """
    A binary builder is an abstraction for building one or more flavors of a given binary. Each binary serves a specific
    purpose. While it is possible to build all of these binaries in parallel, some of the generated build class .o files
    are common between the build/make scripts involved. As such, it is safer to build serially.
    """
    PUBLISHING_DIR = '/shared_tftp'

    # Builders make extensive use of configmaps to inform the overall build process.
    # Instead of reading/parsing the configmap each time, cache on read and invalidate
    # after this many seconds. The goal is to read the configmap exactly once per build
    # iteration, so any value less than the overall build time is suitable.
    CONFIGMAP_CACHE_TIMEOUT = 600

    # To be set by inheriting classes
    ARCH_BUILD_DIR = None
    ARCH = None
    ENABLED_TAG = None
    ENABLED_DEBUG_TAG = None
    BINARY_NAME_TAG = None
    DEBUG_BINARY_NAME_TAG = None

    # Additional flags to pass in to Make
    MAKE_ADDENDUM = []

    # The typical period of time we wait between checks to see if we need to rebuild
    TIME_BETWEEN_BUILDCHECKS = 60

    def __init__(self):
        self._build_options = ['httpcore', 'x509', 'efi_time']
        self._build_debug_options = ['httpcore:2', 'x509:2', 'efi_time']

        # Options and structures unique to the global configmap
        self.global_settings_configmap_name = 'cray-ipxe-settings'
        self._global_settings = None
        self._global_settings_timestamp = None

        # Builder specific BSS settings configmap name (derived from arch). Tells the ipxe environment how to get to
        # BSS to make the next request specific to the node in question.
        self._configmap_name = None
        self._bss_script_path = None

        # Local tracking variable for previously pulled copies of the debug script
        self._debug_script_path = None

        # JWT Token control and generation for this builder
        self._bearer_token = None

        # Certificate information
        self._cert_path = None

        self.namespace = 'services'
        self._arch_build_dir = None

        # Create a liveness probe that can be updated periodically to indicate that we're alive and kicking
        self.liveness_probe = ipxeTimestamp(LIVENESS_PATH, os.getenv('IPXE_BUILD_TIME_LIMIT', 40))
        self.heartbeat = threading.Thread(target=liveliness_heartbeat, args=(LIVENESS_PATH,))


        # This is a flag for the whole builder that indicates if a new ipxe binary should be built. Its' value is
        # changed dynamically through behavior defined by timeout expiration and change of settings.
        self.recreation_necessary = True

    @property
    def build_options(self):
        return ','.join(self._build_options)

    @property
    def build_debug_options(self):
        return ','.join(self._build_debug_options)

    @property
    def global_settings(self):
        """
        Obtains and compares copies of the upstream global settings. When checking for new upstream content, a change in
        settings forces a new build to happen.
        :return:
        """
        # Invalidate the cache when old
        local_settings = self._global_settings
        if self._global_settings and self._global_settings_timestamp:
            if time.time() - self._global_settings_timestamp > self.CONFIGMAP_CACHE_TIMEOUT:
                self._global_settings = None
                self._global_settings_timestamp = None
        if not self._global_settings:
            self._global_settings = safe_load(api_instance.read_namespaced_config_map(
                self.global_settings_configmap_name, self.namespace).data['settings.yaml'])
            self._global_settings_timestamp = time.time()
        if local_settings != self._global_settings:
            # Either this is the first time we've accessed the global settings, or the settings have changed.
            # in either case, an update to this value indicates we should rebuild to pick up the new values.
            LOGGER.info("New global settings cached; rebuild is possible if enabled.")
            self.recreation_necessary = True
        return self._global_settings

    @property
    def enabled(self):
        """
        An arch specific flag for a builder to determine if it should publish any artifacts.
        """
        return self.global_settings.get(self.ENABLED_TAG, True)

    @property
    def debug_enabled(self):
        """
        An arch specific flag for a builder to create a debug version of the binary
        """
        return self.global_settings.get(self.ENABLED_DEBUG_TAG, True)

    @property
    def binary_name(self):
        """
        The resultant filename that a builder produces. For reasons of security, this
        name is configurable because the JWT embedded into the artifact is considered sensitive.
        """
        binary_name = self.global_settings.get(self.BINARY_NAME_TAG, None)
        assert binary_name is not None
        return binary_name

    @property
    def debug_binary_name(self):
        """
        The resultant filename that a builder produces. Debug binaries do not typically contain
        a sensitive JWT, but for reasons of multi-architecture and parity, they are configurable.
        """
        binary_name = self.global_settings.get(self.DEBUG_BINARY_NAME_TAG, None)
        assert binary_name is not None
        return binary_name

    @property
    def build_with_certs(self):
        """
        :return: A Boolean value corresponding to global settings around certs.
        If enabled, embed and trust the associated certificate during build
        """
        return self.global_settings.get('cray_ipxe_build_with_cert', None)

    @property
    def token_min_remaining_valid_time(self):
        """
        This is a string containing an integer value that a user can set in the global settings. Any existing token that
        will expire in a period of time shorter than the configured value (in seconds) will force a new token to be
        generated.
        :return: a string of an integer value that affects when a JWT/token is recreated.
        """
        return self.global_settings.get('cray_ipxe_token_min_remaining_valid_time', '1800')

    @property
    def cray_ipxe_token_host(self):
        """
        This is a global setting that directs the token acquisition process.
        """
        return self.global_settings.get('cray_ipxe_token_host', TOKEN_HOST)

    @property
    def s3_host(self):
        """
        # Determine the S3 host name and pass this to the iPXE build.  If the hostname
        # can not be determined then the default value for S3_HOST will be used as
        # defined in the ipxe makefile.
        :returns: - None if S3 host is the ipxe default
                  - A string value representing the new s3 host to use
        """
        try:
            sts_rados_raw = api_instance.read_namespaced_config_map('sts-rados-config', self.namespace)
            sts_rados_conf = safe_load(sts_rados_raw.data['rados_conf'])
            sts_rados_internal_endpoint = sts_rados_conf.get('int_endpoint_url')
            parsed_uri = urlparse(sts_rados_internal_endpoint)
            rgw_s3_host = parsed_uri.hostname
            if rgw_s3_host:
                # Override the default S3_HOST ipxe makefile parameter value.
                LOGGER.debug("Using custom S3_HOST=%s" % rgw_s3_host)
                return rgw_s3_host
        except KeyError as kex:
            LOGGER.error("Error reading the sts-rados-config map.  Unable to override S3_HOST")
            LOGGER.error("The specific error was: %s" % kex)
        except client.rest.ApiException as rex:
            LOGGER.error("Error getting the sts-rados-config map.  Unable to override S3_HOST")
            LOGGER.error("The specific error was: %s" % rex)

    @property
    def cert_path(self):
        """
        This is the cluster's public certificate information. If so requested, the certificate is bundled and trusted
        as part of the created binary artifact.
        :side-effect: If the certificate has changed, write the new cert to disk and flag the build to be recreated.
        """
        existing_cert = None
        if self._cert_path:
            with open(self._cert_path, 'r') as cert_file:
                existing_cert = cert_file.read()
        upstream_cert = api_instance.read_namespaced_config_map('cray-configmap-ca-public-key', 'services').data[
            'certificate_authority.crt']
        if existing_cert != upstream_cert:
            LOGGER.info("An update to the upstream certificate is available, rebuild is flagged.")
            self.recreation_necessary = True
            # Clean up the old file, we don't want to be sloppy
            if self._cert_path and os.path.exists(self._cert_path):
                os.unlink(self._cert_path)
                self._cert_path = None
            with NamedTemporaryFile(dir=IPXE_BUILD_DIR, delete=False, mode='w') as cert_file:
                cert_file.write(upstream_cert)
                self._cert_path = cert_file.name
        return self._cert_path

    @property
    def bss_script_path(self):
        """
        :return: returns an absolute path to a file located in the build dir containing the bss script.
        :side-effect:
        Creates a local copy of the bss script to file, compares any existing bss file against the upstream version,
        and flags for rebuild if a change is detected.
        """
        local_bss_script = None
        if self._bss_script_path:
            with open(self._bss_script_path, 'r') as bss_script_file:
                local_bss_script = bss_script_file.read()
        upstream_bss_script = api_instance.read_namespaced_config_map(self.configmap_name,
                                                                      self.namespace).data.get('bss.ipxe')
        if local_bss_script != upstream_bss_script:
            if not self._bss_script_path:
                LOGGER.info("New BSS script available; first time build is flagged.")
            else:
                LOGGER.info("Change in upstream BSS script detected; rebuild is flagged.")
                os.unlink(self._bss_script_path)
            with NamedTemporaryFile(dir=IPXE_BUILD_DIR, delete=False, mode='w') as ntf:
                ntf.write(upstream_bss_script)
                self._bss_script_path = ntf.name
            self.recreation_necessary = True
        return self._bss_script_path

    @property
    def debug_script_path(self):
        """
        :return: returns an absolute path to a file located in the build dir containing the debug interactive shell
        script.
        :side-effect: Creates a local copy of the debug script to file, compares any existing debug file
        against the upstream version, and flags for rebuild if a change is detected.
        """
        local_debug_script = None
        if self._debug_script_path:
            with open(self._debug_script_path, 'r') as debug_script_file:
                local_debug_script = debug_script_file.read()
        upstream_debug_script = safe_load(api_instance.read_namespaced_config_map('cray-ipxe-shell-ipxe',
                                                                        self.namespace).data.get('shell.ipxe'))
        if local_debug_script != upstream_debug_script:
            if not self._debug_script_path:
                LOGGER.info("New Debug script available; first time build is flagged.")
            else:
                LOGGER.info("Change in upstream Debug script detected; rebuild is flagged.")
                os.unlink(self._debug_script_path)
            with NamedTemporaryFile(dir=IPXE_BUILD_DIR, delete=False, mode='w') as ntf:
                ntf.write(upstream_debug_script)
                self._debug_script_path = ntf.name
            self.recreation_necessary = True
        return self._debug_script_path

    @property
    def arch_build_dir(self):
        """
        An arch build dir is a directory inside the ipxe build environment that corresponds to a specific build arch.
        All artifacts and compiled sources live within this directory.
        :return:
        """
        if not self._arch_build_dir:
            self._arch_build_dir = 'bin-%s-efi' % self.ARCH
        return self._arch_build_dir

    @property
    def bearer_token(self):
        """
        A bearer token is a secure authorization header that the ipxe environment uses when making requests to
        authenticated endpoints (specifically, s3).
        :return: a token string that is valid and will be valid for the planned lifecycle of the ipxe binary.
        :side-effect: When the token is accessed and regenerated, the build source for httpcore is updated for recompile
        """
        if token_expiring_soon(self._bearer_token, self.token_min_remaining_valid_time):
            # Time to grab a new token and force the next build to pick up the value
            self._bearer_token = fetch_token(self.cray_ipxe_token_host)
            os.utime('%s/net/tcp/httpcore.c' % IPXE_BUILD_DIR, None)
            self.recreation_necessary = True
        return self._bearer_token

    @property
    def build_command(self):
        """
        The build command represents the logical collection of command line arguments passed to the make command to
        generate the respective ipxe binaries.
        :return: - A modified os.environment with a token set
                 - A list of strings representing the necessary build command to use.
        :side-effect: Referencing this property calls other property definitions that may dynamically update the local
        filesystem, stage new content from configmaps, and generally set the build in motion. Do not invoke the command
        lightly, and capture the result instead of calling this multiple times.
        """
        build_command = ['make']
        build_command.append('%s/ipxe.efi' % self.arch_build_dir)
        # To apply any builder specific additions, if any
        build_command.extend(self.MAKE_ADDENDUM)
        build_command.append('DEBUG=%s' % self.build_options)
        if self.build_with_certs:
            cert_path_filename = os.path.basename(self.cert_path)
            build_command.append('CERT=%s' % cert_path_filename)
            build_command.append('TRUST=%s' % cert_path_filename)
        build_command.append('EMBED=%s' % os.path.basename(self.bss_script_path))
        s3_host = self.s3_host
        if s3_host:
            build_command.append('S3_HOST=%s' % s3_host)
        build_command.append('BEARER_TOKEN=%s' % self.bearer_token)
        LOGGER.debug("Build command generated as: [%s]" % ' '.join(build_command[:-1]))
        LOGGER.debug("BEARER_TOKEN=<omitted> for reasons of security.")
        return build_command

    @property
    def debug_command(self):
        """
        The debug command represents the logical collection of command line arguments passed to the make command to
        generate a debug environment for the builder in question.
        :return: - A list of strings representing the necessary build command to use for generating a debug image.
        :side-effect: Referencing this property calls other property definitions that may dynamically update the local
        filesystem, stage new content from configmaps, and generally set the build in motion. Do not invoke the command
        lightly, and capture the result instead of calling this multiple times.
        """
        debug_command = ['make']
        debug_command.append('%s/ipxe.efi' % self.arch_build_dir)
        # To apply any builder specific additions, if any
        debug_command.extend(self.MAKE_ADDENDUM)
        debug_command.append('DEBUG=%s' % self.build_debug_options)
        if self.build_with_certs:
            cert_path_filename = os.path.basename(self.cert_path)
            debug_command.append('CERT=%s' % cert_path_filename)
            debug_command.append('TRUST=%s' % cert_path_filename)
        debug_command.append('EMBED=%s' % os.path.basename(self.debug_script_path))
        s3_host = self.s3_host
        if s3_host:
            debug_command.append('S3_HOST=%s' % s3_host)
        debug_command.append('BEARER_TOKEN=%s' % self.bearer_token)
        LOGGER.debug("Debug build command generated as: [%s]" % ' '.join(debug_command[:-1]))
        LOGGER.debug("BEARER_TOKEN=<omitted> for reasons of security.")
        return debug_command

    @property
    def built_binary_abs_path(self):
        """
        The full path of the artifact that is built out into the build dir after the make command succeeds.
        """
        return os.path.join(IPXE_BUILD_DIR, self.arch_build_dir, 'ipxe.efi')

    @property
    def destination_abs_path(self):
        """
        The full absolute path to where the published binary will reside.
        """
        destination = os.path.join(self.PUBLISHING_DIR, self.binary_name)
        assert destination is not None
        return destination

    @property
    def debug_destination_abs_path(self):
        """
        The full absolute path to where the published debug binary will reside.
        """
        destination = os.path.join(self.PUBLISHING_DIR, self.debug_binary_name)
        assert destination is not None
        return destination

    def set_log_level(self):
        """
        Query the desired log level from the global settings file and honor it until it is set differently.
        :return: None
        """
        cray_ipxe_build_debug = self.global_settings.get('cray_ipxe_build_service_log_level', "DEBUG")
        try:
            root_logger = logging.getLogger()
            root_logger.setLevel(cray_ipxe_build_debug)
        except ValueError as ve:
            root_logger.setLevel("DEBUG")
            LOGGER.warning("Unknown log level '%s'; defaulting to DEBUG.")

    def build_binary(self, command, environment, debug=False):
        if not debug:
            LOGGER.info("Preparing to build new %s binary." % self.ARCH)
        else:
            LOGGER.info("Preparing to build new %s DEBUG binary." % self.ARCH)
        subprocess.check_call(command, env=environment)

    def publish_binary(self):
        shutil.move(self.built_binary_abs_path, self.destination_abs_path)
        LOGGER.info('New ipxe binary has been published.')

    def publish_debug(self):
        shutil.move(self.built_binary_abs_path, self.debug_destination_abs_path)
        LOGGER.info('New DEBUG ipxe binary has been published.')

    def __call__(self):
        """
        Sets the build in motion.
        :return: Never, but if it does exit, cleanup any existing files that are temporary in nature.
        """
        LOGGER.info("Cray BSS iPXE binary builder initializing...")
        os.chdir(IPXE_BUILD_DIR)
        self.heartbeat.start()
        first_time = True
        while True:
            self.set_log_level()
            # On the first pass through, we don't want to wait.
            if not first_time:
                time.sleep(self.TIME_BETWEEN_BUILDCHECKS)
            first_time = False
            if not self.enabled:
                continue

            # Generate a set of build commands for binary and debug versions to determine if recreation is necessary
            build_command, build_environment = self.build_command
            debug_command, debug_environment = self.debug_command
            if not self.recreation_necessary:
                continue

            self.build_binary(build_command, build_environment)
            self.publish_binary()
            self.liveness_probe.refresh_build()
            self.build_binary(debug_command, debug_environment, debug=True)
            self.publish_debug()
            self.liveness_probe.refresh_build()

            # Until next time...
            self.recreation_necessary = False


class X86Builder(BinaryBuilder):
    ARCH = 'x86_64'
    ENABLED_TAG = 'cray_ipxe_build_x86'
    ENABLED_DEBUG_TAG = 'cray_ipxe_debug_enabled'
    BINARY_NAME_TAG = 'cray_ipxe_binary_name'
    DEBUG_BINARY_NAME_TAG = 'cray_ipxe_debug_binary_name'

    @property
    def configmap_name(self):
        if not self._configmap_name:
            base_name = 'cray-ipxe-bss-ipxe'
            if self.ARCH == 'aarch64':
                base_name = '%s-aarch64'
            self._configmap_name = base_name
        return self._configmap_name


class Arm64builder(BinaryBuilder):
    ARCH = 'arm64'
    ENABLED_TAG = 'cray_ipxe_build_aarch64'
    ENABLED_DEBUG_TAG = 'cray_ipxe_aarch64_debug_enabled'
    BINARY_NAME_TAG = 'cray_ipxe_aarch64_binary_name'
    DEBUG_BINARY_NAME_TAG = 'cray_ipxe_aarch64_debug_binary_name'
    MAKE_ADDENDUM = ['CROSS_COMPILE=aarch64-linux-gnu-',
                     'ARCH=arm64']

    @property
    def configmap_name(self):
        if not self._configmap_name:
            base_name = 'cray-ipxe-bss-ipxe'
            if self.ARCH == 'aarch64':
                base_name = '%s-aarch64'
            self._configmap_name = base_name
        return self._configmap_name


if __name__ == '__main__':
    x86_builder = BinaryBuilder()
    arm64_builder = Arm64builder()

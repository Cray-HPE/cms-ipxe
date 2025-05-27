#
# MIT License
#
# (C) Copyright 2020-2023, 2025 Hewlett Packard Enterprise Development LP
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
A set of routines for creating or reading from an existing timestamp file.
Created on April 2nd, 2020

@author: jason.sollom
'''
import datetime
import json
import logging
import os
import threading
import time

LOGGER = logging.getLogger(__name__)
LIVENESS_PATH = '/tmp/ipxe_build_in_progress'

MAIN_THREAD = threading.current_thread()

class BaseipxeTimestampException(BaseException):
    pass


class ipxeTimestampNoEnt(BaseipxeTimestampException):
    """
    The Timestamp does not exist. 
    """
    pass


class ipxeTimestamp(object):
    def __init__(self, path, max_age, when=None):
        '''
        Creates a new timestamp representation to <path>; on initialization,
        this timestamp is written to disk in a persistent fashion.

        Newly initialized timestamps with a path reference to an existing file
        overwrites the file in question.
        
        Args:
        path (string): path to file containing the timestamp
        max_age (int): number of seconds before the timestamp is considered invalid 
        when (datetime Object): A datetime instance
        '''
        self.path = path
        try:
            os.makedirs(os.path.dirname(path))
        except FileExistsError:
            pass

        if not when:
            timestamp = datetime.datetime.now().timestamp()
        else:
            timestamp = when.timestamp()

        with open(self.path, 'w') as timestamp_file:
            data = {'timestamp': float(timestamp),
                    'max_age': float(max_age),
                    'last_build': None}
            json.dump(data, timestamp_file)

    @classmethod
    def byref(cls, path):
        """
        Creates a new instance of a Timestamp without initializing it to disk.
        This is useful if you simply want to check the existence of a timestamp
        without altering it.
        
        If the timestamp file does not exist, return None.
        
        Returns:
          A Timestamp object, if one exists
        
        Raises:
          ipxeTimestampNoEnt -- If path does not exist
        """
        if os.path.exists(path):
            self = cls.__new__(cls)
            self.path = path
            return self
        else:
            raise ipxeTimestampNoEnt

    @property
    def _data(self):
        """
        A read-only, non-caching method for parsing information from disk.
        :return: A dictionary from the parsed timestamp file.
        """
        if os.path.exists(self.path):
            with open(self.path, 'r') as timestamp_file:
                data = json.load(timestamp_file)
                return data
        else:
            # Newly instantiated objects will have no persistent data on disk.
            return {'timestamp': None, 'max_age': None, 'last_build': None}

    @_data.setter
    def _data(self, dict_obj):
        """
        :param dict_obj: A dictionary to be written to disk.
        :return: None.
        """
        with open(self.path, 'w') as timestamp_file:
            json.dump(dict_obj, timestamp_file)

    @property
    def value(self):
        """
        The float value of when the timestamp was last pressed to disk.
        :return: A float value as stored in a file.
        """
        try:
            return datetime.datetime.fromtimestamp(float(self._data['timestamp']))
        except KeyError:
            return None

    @value.setter
    def value(self, when=None):
        """
        :param when: A float timestamp or nothing at all
        :return: None.
        """
        if not when:
            # How?
            when = datetime.datetime.now().timestamp()
        data = self._data
        data['timestamp'] = when
        self._data = data

    @property
    def value_age(self):
        return datetime.datetime.now() - self.value

    @property
    def last_build(self):
        """
        :return: A datetime value representing the last time the deployment was refreshed.
        """
        try:
            return datetime.datetime.fromtimestamp(float(self._data['last_build']))
        except (KeyError, TypeError):
            return None

    @last_build.setter
    def last_build(self, when=None):
        """
        :param when: a float timestamp representing when the last build was a success, or None, representing right now.
        :return: None
        """
        if not when:
            # How?
            when = datetime.datetime.now().timestamp()
        data = self._data
        data['last_build'] = when
        self._data = data

    @property
    def last_build_age(self):
        """
        :return: a timedelta object showing how long ago a build was made, or 'Never' if the build has never been
        completed.
        """
        last_build = self.last_build
        if not last_build:
            return 'Never'
        else:
            return datetime.datetime.now() - self.last_build

    @property
    def max_age(self):
        """
        The maximum age that a timestamp is considered valid in the form of a float representing seconds.
        :return: a timedelta value
        """
        return float(self._data['max_age'])

    @max_age.setter
    def max_age(self, val):
        """
        Sets a new maximum age for the heartbeat/build value (in seconds)
        :param val: a float value (in seconds)
        :return: None
        """
        data = self._data
        data['max_age'] = val
        self._data = data

    @property
    def max_delta(self):
        """
        A representation of the amount of time a timestamp can be considered valid based on a timedelta interpretation.
        :return: a timedelta object instance
        """
        return datetime.timedelta(seconds=self.max_age)

    @property
    def expiration_date(self):
        """
        The datetime value when the timestamp will next expire.
        :return: a datetime.datetime object
        """
        return self.value + self.max_delta

    @property
    def expired(self):
        """
        A Boolean value indicating if a timestamp has expired based on thread update from self.value.
        :return: A bool value indicating overall expiration of the thread timestamp
        """
        return datetime.datetime.now() > self.expiration_date

    @property
    def recent_build(self):
        """
        :return: Boolean value indicating that we have had a recent build.
        """
        last_build_age = self.last_build_age
        if not isinstance(last_build_age, datetime.timedelta):
            return False
        return self.last_build_age < self.max_delta

    @property
    def alive(self):
        """
        Return
          True -- The timestamp has not expired or we have a recent build
          False -- The timestamp has expired and no evidence of a recent build
        """
        # Any recent signs of life
        return any([not self.expired,
                    self.recent_build])

    def refresh(self):
        """
        Update the timestamp with the current time, giving the timestamp object a new lease on life. Does not modify
        existing max_age values set.
        :return: None
        """
        self.value = float(datetime.datetime.now().timestamp())

    def refresh_build(self):
        """
        Signals to the builder that a new build has just been created.
        :return: None
        """
        self.last_build = None

    def delete(self):
        """
        Delete the timestamp file
        """
        os.remove(self.path)

    def __repr__(self):
        buffer = ['Timestamp (%s):' % self.path]
        buffer.append('\tLast Touched: %s - Age: %s' % (self.value, self.value_age))
        buffer.append('\tLast Build: %s - Age: %s' % (self.last_build, self.last_build_age))
        buffer.append('\tExpires: %s' % self.expiration_date)
        buffer.append('\tAlive: %s' % (bool(self.alive)))
        return '\n'.join(buffer)


def liveliness_heartbeat(path):
    """
    Periodically add a timestamp to disk; this allows for reporting of basic
    health at a minimum rate. This prevents the pod being marked as dead if
    a period of no events have been monitored from k8s for an extended
    period of time.
    """
    timestamp = ipxeTimestamp.byref(path)
    while True:
        if not MAIN_THREAD.is_alive():
            # All hope abandon ye who enter here
            return
        timestamp.refresh()
        time.sleep(10)

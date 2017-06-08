# Copyright 2010-2015 MongoDB, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Test suite for pymongo, bson, and gridfs.
"""

import os
import socket
import sys
from pymongo.common import partition_node

if sys.version_info[:2] == (2, 6):
    import unittest2 as unittest
    from unittest2 import SkipTest
else:
    import unittest
    from unittest import SkipTest
import warnings

from functools import wraps

import pymongo
import pymongo.errors

from bson.py3compat import _unicode
from pymongo import common
from pymongo.ssl_support import HAVE_SSL, validate_cert_reqs
from test.version import Version

if HAVE_SSL:
    import ssl

# The host and port of a single mongod or mongos, or the seed host
# for a replica set. Hostnames retrieved from isMaster will be of
# unicode type in Python 2, so ensure these hostnames are unicodes,
# too. It makes tests like `test_repr` predictable.
host = _unicode(os.environ.get("DB_IP", 'localhost'))
port = int(os.environ.get("DB_PORT", 27017))

db_user = _unicode(os.environ.get("DB_USER", "user"))
db_pwd = _unicode(os.environ.get("DB_PASSWORD", "password"))

CERT_PATH = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                         'certificates')
CLIENT_PEM = os.environ.get('CLIENT_PEM',
                            os.path.join(CERT_PATH, 'client.pem'))
CA_PEM = os.environ.get('CA_PEM', os.path.join(CERT_PATH, 'ca.pem'))
CERT_REQS = validate_cert_reqs('CERT_REQS', os.environ.get('CERT_REQS'))

_SSL_OPTIONS = dict(ssl=True)
if CLIENT_PEM:
    _SSL_OPTIONS['ssl_certfile'] = CLIENT_PEM
if CA_PEM:
    _SSL_OPTIONS['ssl_ca_certs'] = CA_PEM
if CERT_REQS is not None:
    _SSL_OPTIONS['ssl_cert_reqs'] = CERT_REQS


def is_server_resolvable():
    """Returns True if 'server' is resolvable."""
    socket_timeout = socket.getdefaulttimeout()
    socket.setdefaulttimeout(1)
    try:
        try:
            socket.gethostbyname('server')
            return True
        except socket.error:
            return False
    finally:
        socket.setdefaulttimeout(socket_timeout)


def _connect(host, port, **kwargs):
    try:
        client = pymongo.MongoClient(
            host, port, serverSelectionTimeoutMS=100, **kwargs)
        client.admin.command('ismaster')  # Can we connect?
        # If connected, then return client with default timeout
        return pymongo.MongoClient(host, port, **kwargs)
    except pymongo.errors.ConnectionFailure:
        return None


class client_knobs(object):
    def __init__(
            self,
            heartbeat_frequency=None,
            min_heartbeat_interval=None,
            kill_cursor_frequency=None,
            events_queue_frequency=None):
        self.heartbeat_frequency = heartbeat_frequency
        self.min_heartbeat_interval = min_heartbeat_interval
        self.kill_cursor_frequency = kill_cursor_frequency
        self.events_queue_frequency = events_queue_frequency

        self.old_heartbeat_frequency = None
        self.old_min_heartbeat_interval = None
        self.old_kill_cursor_frequency = None
        self.old_events_queue_frequency = None

    def enable(self):
        self.old_heartbeat_frequency = common.HEARTBEAT_FREQUENCY
        self.old_min_heartbeat_interval = common.MIN_HEARTBEAT_INTERVAL
        self.old_kill_cursor_frequency = common.KILL_CURSOR_FREQUENCY
        self.old_events_queue_frequency = common.EVENTS_QUEUE_FREQUENCY

        if self.heartbeat_frequency is not None:
            common.HEARTBEAT_FREQUENCY = self.heartbeat_frequency

        if self.min_heartbeat_interval is not None:
            common.MIN_HEARTBEAT_INTERVAL = self.min_heartbeat_interval

        if self.kill_cursor_frequency is not None:
            common.KILL_CURSOR_FREQUENCY = self.kill_cursor_frequency

        if self.events_queue_frequency is not None:
            common.EVENTS_QUEUE_FREQUENCY = self.events_queue_frequency

    def __enter__(self):
        self.enable()

    def disable(self):
        common.HEARTBEAT_FREQUENCY = self.old_heartbeat_frequency
        common.MIN_HEARTBEAT_INTERVAL = self.old_min_heartbeat_interval
        common.KILL_CURSOR_FREQUENCY = self.old_kill_cursor_frequency
        common.EVENTS_QUEUE_FREQUENCY = self.old_events_queue_frequency

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disable()


class ClientContext(object):

    def __init__(self):
        """Create a client and grab essential information from the server."""
        self.connected = False
        self.ismaster = {}
        self.w = None
        self.nodes = set()
        self.replica_set_name = None
        self.cmd_line = None
        self.version = Version(-1)  # Needs to be comparable with Version
        self.auth_enabled = False
        self.test_commands_enabled = False
        self.is_mongos = False
        self.is_rs = False
        self.has_ipv6 = False
        self.ssl = False
        self.ssl_cert_none = False
        self.ssl_certfile = False
        self.server_is_resolvable = is_server_resolvable()
        self.ssl_client_options = {}
        self.client = _connect(host, port)

        if HAVE_SSL and not self.client:
            # Is MongoDB configured for SSL?
            self.client = _connect(host, port, **_SSL_OPTIONS)
            if self.client:
                self.ssl = True
                self.ssl_client_options = _SSL_OPTIONS
                self.ssl_certfile = True
                if _SSL_OPTIONS.get('ssl_cert_reqs') == ssl.CERT_NONE:
                    self.ssl_cert_none = True

        if self.client:
            self.connected = True
            ismaster = self.client.admin.command('ismaster')
            if 'setName' in ismaster:
                self.replica_set_name = ismaster['setName']
                self.is_rs = True
                # It doesn't matter which member we use as the seed here.
                self.client = pymongo.MongoClient(
                    host,
                    port,
                    replicaSet=self.replica_set_name,
                    **self.ssl_client_options)
                # Get the authoritative ismaster result from the primary.
                self.ismaster = self.client.admin.command('ismaster')
                nodes = [partition_node(node.lower())
                         for node in self.ismaster.get('hosts', [])]
                nodes.extend([partition_node(node.lower())
                              for node in self.ismaster.get('passives', [])])
                nodes.extend([partition_node(node.lower())
                              for node in self.ismaster.get('arbiters', [])])
                self.nodes = set(nodes)
            else:
                self.ismaster = ismaster
                self.nodes = set([(host, port)])
            self.w = len(self.ismaster.get("hosts", [])) or 1
            self.version = Version.from_client(self.client)

            try:
                self.cmd_line = self.client.admin.command('getCmdLineOpts')
            except pymongo.errors.OperationFailure as e:
                msg = e.details.get('errmsg', '')
                if e.code == 13 or 'unauthorized' in msg or 'login' in msg:
                    # Unauthorized.
                    self.auth_enabled = True
                else:
                    raise
            else:
                self.auth_enabled = self._server_started_with_auth()

            if self.auth_enabled:
                # See if db_user already exists.
                self.user_provided = self._check_user_provided()
                if not self.user_provided:
                    roles = {}
                    if self.version.at_least(2, 5, 3, -1):
                        roles = {'roles': ['root']}
                    self.client.admin.add_user(db_user, db_pwd, **roles)
                    self.client.admin.authenticate(db_user, db_pwd)

                # May not have this if OperationFailure was raised earlier.
                self.cmd_line = self.client.admin.command('getCmdLineOpts')

            if 'enableTestCommands=1' in self.cmd_line['argv']:
                self.test_commands_enabled = True
            elif 'parsed' in self.cmd_line:
                params = self.cmd_line['parsed'].get('setParameter', [])
                if 'enableTestCommands=1' in params:
                    self.test_commands_enabled = True
                else:
                    params = self.cmd_line['parsed'].get('setParameter', {})
                    if params.get('enableTestCommands') == '1':
                        self.test_commands_enabled = True

            self.is_mongos = (self.ismaster.get('msg') == 'isdbgrid')
            self.has_ipv6 = self._server_started_with_ipv6()

    @property
    def host(self):
        if self.is_rs:
            primary = self.client.primary
            return primary[0] if primary is not None else host
        return host

    @property
    def port(self):
        if self.is_rs:
            primary = self.client.primary
            return primary[1] if primary is not None else port
        return port

    @property
    def pair(self):
        return "%s:%d" % (self.host, self.port)

    @property
    def has_secondaries(self):
        return bool(len(self.client.secondaries))

    def _check_user_provided(self):
        try:
            self.client.admin.authenticate(db_user, db_pwd)
            return True
        except pymongo.errors.OperationFailure as e:
            msg = e.details.get('errmsg', '')
            if e.code == 18 or 'auth fails' in msg:
                # Auth failed.
                return False
            else:
                raise

    def _server_started_with_auth(self):
        # MongoDB >= 2.0
        if 'parsed' in self.cmd_line:
            parsed = self.cmd_line['parsed']
            # MongoDB >= 2.6
            if 'security' in parsed:
                security = parsed['security']
                # >= rc3
                if 'authorization' in security:
                    return security['authorization'] == 'enabled'
                # < rc3
                return (security.get('auth', False) or
                        bool(security.get('keyFile')))
            return parsed.get('auth', False) or bool(parsed.get('keyFile'))
        # Legacy
        argv = self.cmd_line['argv']
        return '--auth' in argv or '--keyFile' in argv

    def _server_started_with_ipv6(self):
        if not socket.has_ipv6:
            return False

        if 'parsed' in self.cmd_line:
            if not self.cmd_line['parsed'].get('net', {}).get('ipv6'):
                return False
        else:
            if '--ipv6' not in self.cmd_line['argv']:
                return False

        # The server was started with --ipv6. Is there an IPv6 route to it?
        try:
            for info in socket.getaddrinfo(self.host, self.port):
                if info[0] == socket.AF_INET6:
                    return True
        except socket.error:
            pass

        return False

    def _require(self, condition, msg, func=None):
        def make_wrapper(f):
            @wraps(f)
            def wrap(*args, **kwargs):
                # Always raise SkipTest if we can't connect to MongoDB
                if not self.connected:
                    raise SkipTest(
                        "Cannot connect to MongoDB on %s" % (self.pair,))
                if condition:
                    return f(*args, **kwargs)
                raise SkipTest(msg)
            return wrap

        if func is None:
            def decorate(f):
                return make_wrapper(f)
            return decorate
        return make_wrapper(func)

    def require_connection(self, func):
        """Run a test only if we can connect to MongoDB."""
        return self._require(
            self.connected,
            "Cannot connect to MongoDB on %s" % (self.pair,),
            func=func)

    def require_version_min(self, *ver):
        """Run a test only if the server version is at least ``version``."""
        other_version = Version(*ver)
        return self._require(self.version >= other_version,
                             "Server version must be at least %s"
                             % str(other_version))

    def require_version_max(self, *ver):
        """Run a test only if the server version is at most ``version``."""
        other_version = Version(*ver)
        return self._require(self.version <= other_version,
                             "Server version must be at most %s"
                             % str(other_version))

    def require_auth(self, func):
        """Run a test only if the server is running with auth enabled."""
        return self.check_auth_with_sharding(
            self._require(self.auth_enabled,
                          "Authentication is not enabled on the server",
                          func=func))

    def require_no_auth(self, func):
        """Run a test only if the server is running without auth enabled."""
        return self._require(not self.auth_enabled,
                             "Authentication must not be enabled on the server",
                             func=func)

    def require_replica_set(self, func):
        """Run a test only if the client is connected to a replica set."""
        return self._require(self.is_rs,
                             "Not connected to a replica set",
                             func=func)

    def require_secondaries_count(self, count):
        """Run a test only if the client is connected to a replica set that has
        `count` secondaries.
        """
        sec_count = len(self.client.secondaries)
        return self._require(sec_count >= count,
                             "Need %d secondaries, %d available"
                             % (count, sec_count))

    def require_no_replica_set(self, func):
        """Run a test if the client is *not* connected to a replica set."""
        return self._require(
            not self.is_rs,
            "Connected to a replica set, not a standalone mongod",
            func=func)

    def require_ipv6(self, func):
        """Run a test only if the client can connect to a server via IPv6."""
        return self._require(self.has_ipv6,
                             "No IPv6",
                             func=func)

    def require_no_mongos(self, func):
        """Run a test only if the client is not connected to a mongos."""
        return self._require(not self.is_mongos,
                             "Must be connected to a mongod, not a mongos",
                             func=func)

    def require_mongos(self, func):
        """Run a test only if the client is connected to a mongos."""
        return self._require(self.is_mongos,
                             "Must be connected to a mongos",
                             func=func)

    def check_auth_with_sharding(self, func):
        """Skip a test when connected to mongos < 2.0 and running with auth."""
        condition = not (self.auth_enabled and
                         self.is_mongos and self.version < (2,))
        return self._require(condition,
                             "Auth with sharding requires MongoDB >= 2.0.0",
                             func=func)

    def require_test_commands(self, func):
        """Run a test only if the server has test commands enabled."""
        return self._require(self.test_commands_enabled,
                             "Test commands must be enabled",
                             func=func)

    def require_ssl(self, func):
        """Run a test only if the client can connect over SSL."""
        return self._require(self.ssl,
                             "Must be able to connect via SSL",
                             func=func)

    def require_no_ssl(self, func):
        """Run a test only if the client can connect over SSL."""
        return self._require(not self.ssl,
                             "Must be able to connect without SSL",
                             func=func)

    def require_ssl_cert_none(self, func):
        """Run a test only if the client can connect with ssl.CERT_NONE."""
        return self._require(self.ssl_cert_none,
                             "Must be able to connect with ssl.CERT_NONE",
                             func=func)

    def require_ssl_certfile(self, func):
        """Run a test only if the client can connect with ssl_certfile."""
        return self._require(self.ssl_certfile,
                             "Must be able to connect with ssl_certfile",
                             func=func)

    def require_server_resolvable(self, func):
        """Run a test only if the hostname 'server' is resolvable."""
        return self._require(self.server_is_resolvable,
                             "No hosts entry for 'server'. Cannot validate "
                             "hostname in the certificate",
                             func=func)

# Reusable client context
client_context = ClientContext()


class IntegrationTest(unittest.TestCase):
    """Base class for TestCases that need a connection to MongoDB to pass."""

    @classmethod
    @client_context.require_connection
    def setUpClass(cls):
        cls.client = client_context.client
        cls.db = cls.client.pymongo_test


class MockClientTest(unittest.TestCase):
    """Base class for TestCases that use MockClient.

    This class is *not* an IntegrationTest: if properly written, MockClient
    tests do not require a running server.

    The class temporarily overrides HEARTBEAT_FREQUENCY to speed up tests.
    """

    def setUp(self):
        super(MockClientTest, self).setUp()

        self.client_knobs = client_knobs(
            heartbeat_frequency=0.001,
            min_heartbeat_interval=0.001)

        self.client_knobs.enable()

    def tearDown(self):
        self.client_knobs.disable()
        super(MockClientTest, self).tearDown()


def setup():
    warnings.resetwarnings()
    warnings.simplefilter("always")


def teardown():
    c = client_context.client
    c.drop_database("pymongo-pooling-tests")
    c.drop_database("pymongo_test")
    c.drop_database("pymongo_test1")
    c.drop_database("pymongo_test2")
    c.drop_database("pymongo_test_mike")
    c.drop_database("pymongo_test_bernie")
    if client_context.auth_enabled and not client_context.user_provided:
        c.admin.remove_user(db_user)


class PymongoTestRunner(unittest.TextTestRunner):
    def run(self, test):
        setup()
        result = super(PymongoTestRunner, self).run(test)
        try:
            teardown()
        finally:
            return result


def test_cases(suite):
    """Iterator over all TestCases within a TestSuite."""
    for suite_or_case in suite._tests:
        if isinstance(suite_or_case, unittest.TestCase):
            # unittest.TestCase
            yield suite_or_case
        else:
            # unittest.TestSuite
            for case in test_cases(suite_or_case):
                yield case

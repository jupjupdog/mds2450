# Copyright 2015 MongoDB, Inc.
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

"""Test the collection module."""

import json
import os
import re
import sys

sys.path[0:0] = [""]

from bson.py3compat import iteritems
from pymongo.command_cursor import CommandCursor
from pymongo.cursor import Cursor
from pymongo.results import _WriteResult
from pymongo.operations import UpdateOne, UpdateMany, DeleteOne, DeleteMany, InsertOne, ReplaceOne

from test import unittest, client_context, IntegrationTest

# Location of JSON test specifications.
_TEST_PATH = os.path.join(
    os.path.dirname(os.path.realpath(__file__)), 'crud')


class TestAllScenarios(IntegrationTest):
    pass


def camel_to_snake(camel):
    # Regex to convert CamelCase to snake_case.
    snake = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', camel)
    return re.sub('([a-z0-9])([A-Z])', r'\1_\2', snake).lower()


def check_result(expected_result, result):
    if isinstance(result, Cursor) or isinstance(result, CommandCursor):
        return list(result) == expected_result

    elif isinstance(result, _WriteResult):
        for res in expected_result:
            prop = camel_to_snake(res)
            return getattr(result, prop) == expected_result[res]
    else:
        if not expected_result:
            return result is None
        else:
            return result == expected_result


def create_test(scenario_def, test):
    def run_scenario(self):
        # Load data.
        assert scenario_def['data'], "tests must have non-empty data"
        self.db.test.drop()
        self.db.test.insert_many(scenario_def['data'])

        # Convert command from CamelCase to pymongo.collection method.
        operation = camel_to_snake(test['operation']['name'])
        cmd = getattr(self.db.test, operation)

        # Convert arguments to snake_case and handle special cases.
        arguments = test['operation']['arguments']
        for arg_name in list(arguments):
            c2s = camel_to_snake(arg_name)
            # PyMongo accepts sort as list of tuples. Asserting len=1
            # because ordering dicts from JSON in 2.6 is unwieldy.
            if arg_name == "sort":
                sort_dict = arguments[arg_name]
                assert len(sort_dict) == 1, 'test can only have 1 sort key'
                arguments[arg_name] = list(iteritems(sort_dict))
            # Named "key" instead not fieldName.
            if arg_name == "fieldName":
                arguments["key"] = arguments.pop(arg_name)
            # Aggregate uses "batchSize", while find uses batch_size.
            elif arg_name == "batchSize" and operation == "aggregate":
                continue
            # Requires boolean returnDocument.
            elif arg_name == "returnDocument":
                arguments[c2s] = arguments[arg_name] == "After"
            else:
                arguments[c2s] = arguments.pop(arg_name)

        result = cmd(**arguments)

        # Assert final state is expected.
        expected_c = test['outcome'].get('collection')
        if expected_c is not None:
            expected_name = expected_c.get('name')
            if expected_name is not None:
                db_coll = self.db[expected_name]
            else:
                db_coll = self.db.test
            self.assertEqual(list(db_coll.find()), expected_c['data'])
        else:
            check_result(test['outcome'].get('result'), result)

    return run_scenario


def create_tests():
    for dirpath, _, filenames in os.walk(_TEST_PATH):
        dirname = os.path.split(dirpath)[-1]

        for filename in filenames:
            with open(os.path.join(dirpath, filename)) as scenario_stream:
                scenario_def = json.load(scenario_stream)

            test_type = os.path.splitext(filename)[0]

            min_ver, max_ver = None, None
            if 'minServerVersion' in scenario_def:
                min_ver = tuple(
                    int(elt) for
                    elt in scenario_def['minServerVersion'].split('.'))
            if 'maxServerVersion' in scenario_def:
                max_ver = tuple(
                    int(elt) for
                    elt in scenario_def['maxServerVersion'].split('.'))

            # Construct test from scenario.
            for test in scenario_def['tests']:
                new_test = create_test(scenario_def, test)
                if min_ver is not None:
                    new_test = client_context.require_version_min(*min_ver)(
                        new_test)
                if max_ver is not None:
                    new_test = client_context.require_version_max(*max_ver)(
                        new_test)

                test_name = 'test_%s_%s_%s' % (
                    dirname,
                    test_type,
                    str(test['description'].replace(" ", "_")))

                new_test.__name__ = test_name
                setattr(TestAllScenarios, new_test.__name__, new_test)


create_tests()


class TestWriteOpsComparison(unittest.TestCase):
    def test_InsertOneEquals(self):
        self.assertEqual(InsertOne({'foo': 42}), InsertOne({'foo': 42}))

    def test_InsertOneNotEquals(self):
        self.assertNotEqual(InsertOne({'foo': 42}), InsertOne({'foo': 23}))

    def test_DeleteOneEquals(self):
        self.assertEqual(DeleteOne({'foo': 42}), DeleteOne({'foo': 42}))

    def test_DeleteOneNotEquals(self):
        self.assertNotEqual(DeleteOne({'foo': 42}), DeleteOne({'foo': 23}))

    def test_DeleteManyEquals(self):
        self.assertEqual(DeleteMany({'foo': 42}), DeleteMany({'foo': 42}))

    def test_DeleteManyNotEquals(self):
        self.assertNotEqual(DeleteMany({'foo': 42}), DeleteMany({'foo': 23}))

    def test_DeleteOneNotEqualsDeleteMany(self):
        self.assertNotEqual(DeleteOne({'foo': 42}), DeleteMany({'foo': 42}))

    def test_ReplaceOneEquals(self):
        self.assertEqual(ReplaceOne({'foo': 42}, {'bar': 42}, upsert=False),
                         ReplaceOne({'foo': 42}, {'bar': 42}, upsert=False))

    def test_ReplaceOneNotEquals(self):
        self.assertNotEqual(ReplaceOne({'foo': 42}, {'bar': 42}, upsert=False),
                            ReplaceOne({'foo': 42}, {'bar': 42}, upsert=True))

    def test_UpdateOneEquals(self):
        self.assertEqual(UpdateOne({'foo': 42}, {'$set': {'bar': 42}}),
                         UpdateOne({'foo': 42}, {'$set': {'bar': 42}}))

    def test_UpdateOneNotEquals(self):
        self.assertNotEqual(UpdateOne({'foo': 42}, {'$set': {'bar': 42}}),
                            UpdateOne({'foo': 42}, {'$set': {'bar': 23}}))

    def test_UpdateManyEquals(self):
        self.assertEqual(UpdateMany({'foo': 42}, {'$set': {'bar': 42}}),
                         UpdateMany({'foo': 42}, {'$set': {'bar': 42}}))

    def test_UpdateManyNotEquals(self):
        self.assertNotEqual(UpdateMany({'foo': 42}, {'$set': {'bar': 42}}),
                            UpdateMany({'foo': 42}, {'$set': {'bar': 23}}))

    def test_UpdateOneNotEqualsUpdateMany(self):
        self.assertNotEqual(UpdateOne({'foo': 42}, {'$set': {'bar': 42}}),
                            UpdateMany({'foo': 42}, {'$set': {'bar': 42}}))

if __name__ == "__main__":
    unittest.main()

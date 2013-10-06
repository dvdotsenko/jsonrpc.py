import json
import time

from unittest import TestCase

from jsonrpcparts import JSONPRCCollection, errors

class JSONPRCCollectionTestSuite(TestCase):

    def test_collection_dict_api(self):
        """
        Making sure noone messes up dict-like behavior of our collection

        We expect "in", ".get()" and other dict-appropriate fns to work.

        """

        def handler(*args, **kw):
            return [args, kw]

        collection = JSONPRCCollection(method_name=handler)

        self.assertEqual(
            collection['method_name'],
            handler
        )

        self.assertEqual(
            collection.get('method_name'),
            handler
        )

        collection['another_method_name'] = handler

        self.assertEqual(
            collection['another_method_name'],
            handler
        )

        self.assertEqual(
            collection.get('another_method_name'),
            handler
        )

    def test_collection_register_function(self):

        def handler(*args, **kw):
            return [args, kw]

        collection = JSONPRCCollection()

        collection.register_function(handler)

        # if no name specified, register_function takes name from obj
        self.assertEqual(
            collection.get('handler'),
            handler
        )

        collection.register_function(handler, "another.name")

        # if no name specified, register_function takes name from obj
        self.assertEqual(
            collection.get('another.name'),
            handler
        )

    def test_collection_register_class(self):

        class A(object):

            def handler_one(self, *args, **kw):
                return [args, kw]

            def handler_two(self, *args, **kw):
                return [args, kw]

            def _should_not_be_found(self):
                pass

        collection = JSONPRCCollection()

        collection.register_class(A())

        # if no name specified, register_function takes name from obj
        self.assertEqual(
            set(collection.keys()),
            {'A.handler_one', 'A.handler_two'}
        )

        collection.register_class(A(), 'alternate_prefix')

        # if no name specified, register_function takes name from obj
        self.assertEqual(
            set(collection.keys()),
            {
                'A.handler_one', 'A.handler_two',
                'alternate_prefix.handler_one', 'alternate_prefix.handler_two'
            }
        )

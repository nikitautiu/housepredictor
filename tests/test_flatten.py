from unittest import TestCase

from scraper.helpers import flatten


class TestFlatten(TestCase):
    def test_flatten(self):
        dict_to_flatten = {'a': {'b': 'b', 'c': 'b'}, 'c': 'd'}
        flattened_dict = {'a_b': 'b', 'a_c': 'b', 'c': 'd'}
        self.assertDictEqual(flatten(dict_to_flatten), flattened_dict)

        flattened_dict = {'a.b': 'b', 'a.c': 'b', 'c': 'd'}
        self.assertDictEqual(flatten(dict_to_flatten, sep='.'), flattened_dict)

        flattened_dict = {'p.a.b': 'b', 'p.a.c': 'b', 'p.c': 'd'}
        self.assertDictEqual(flatten(dict_to_flatten, sep='.', parent_key='p'),
                             flattened_dict)

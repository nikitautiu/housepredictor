from unittest import TestCase

from extractor import flatten, DictExtractor, DictMultiExtractor


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


def simp_postproc(x):
    yield ('a', x * 2)


class TestDictExtractor(TestCase):
    def test_dict_extractor(self):
        extractor = DictExtractor('a', 'new_a')
        input = {'a': 3, 'b': '5'}
        result = set(extractor(input))
        expected = {('new_a', 3), }
        self.assertSetEqual(result, expected)

        extractor = DictExtractor('a')
        input = {'a': 3, 'b': '5'}
        result = set(extractor(input))
        expected = {('a', 3), }
        self.assertSetEqual(result, expected)

        extractor = DictExtractor('a', 'new_a', default=5)
        input = {'b': '5'}
        result = set(extractor(input))
        expected = {('new_a', 5), }
        self.assertSetEqual(result, expected)

        extractor = DictExtractor('a', default=5)
        input = {'b': '5'}
        result = set(extractor(input))
        expected = {('a', 5), }
        self.assertSetEqual(result, expected)

        extractor = DictExtractor('a', default=5)
        input = {'b': '5'}
        result = set(extractor(input))
        expected = {('a', 5), }
        self.assertSetEqual(result, expected)

        extractor = DictExtractor('a', post_func=simp_postproc)
        input = {'a': 2}
        result = set(extractor(input))
        expected = {('a', 4), }
        self.assertSetEqual(result, expected)

        with self.assertRaises(KeyError):
            extractor = DictExtractor('a')
            input = {'b': 2}
            list(extractor(input))  # genertor, avoid lazy evaluation


class TestDictMultiExtractor(TestCase):
    def test_dict_multi(self):
        extractor = DictMultiExtractor([
            {
                'key': 'a_a_b',
                'new_key': 'aab'
            },
            {
                'key': 'a_b',
                'default': 1
            }
        ])

        # normal usage
        input = {
            'a': {
                'a': {
                    'b': 3
                },
                'b': 10
            }
        }
        expected = {
            'aab': 3,
            'a_b': 10
        }
        self.assertDictEqual(extractor(input), expected)

        # same but with default value
        input = {
            'a': {
                'a': {
                    'b': 3
                },
            }
        }
        expected = {
            'aab': 3,
            'a_b': 1
        }
        self.assertDictEqual(extractor(input), expected)

        # same but missing non-defaultable value
        input = {
            'a': {
                'b': 10
            }
        }
        with self.assertRaises(KeyError):
            extractor(input)

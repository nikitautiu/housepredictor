import collections
import itertools


def flatten(d, parent_key='', sep='_'):
    """Flattens a dictionary concatenating nested keys
    with the given separator.
    :param d: dictionary to flatten
    :param parent_key: the key of the root
    :param sep: separator"""
    items = []
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, collections.MutableMapping):
            items.extend(flatten(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


class DictExtractor(object):
    """Callable which can be used to parse dictionaries. A key to extract can be
    specified,a default value if it is not found, if it is not specified in
    any way, assume it should raise an exception.

    Calling it on a dict yields pairs of (key, values) extracted. If post func
    is used, values will be yielded from it, otherwise return the values with
    the new_key.
    """

    def __init__(self, key, new_key=None, post_func=None, **kwargs):

        self.key = key
        # new_key is the same name if unspecified
        self.new_key = new_key if new_key is not None else key
        self.post_func = post_func

        # check for default value, if none, use throw
        if 'default' not in kwargs:
            self.throw = True
        else:
            self.throw = False
            self.default = kwargs['default']

    def __call__(self, dictionary):
        if self.key not in dictionary:
            if self.throw:
                raise KeyError('value with key {} not found in dictionary')
            yield (self.new_key, self.default)
        else:
            # execution resumes so else is necessary
            yield from self.post_process(dictionary[self.key])

    def post_process(self, extracted_value):
        if self.post_func is not None:
            yield from self.post_func(extracted_value)
        else:
            yield (self.new_key, extracted_value)


class DictMultiExtractor(object):
    """Class that receives a list of specs like the ones passed to
    Dict extractor. When called, returns the new dictionary"""

    def __init__(self, specs):
        self.extractors = [DictExtractor(**spec) for spec in specs]

    def __call__(self, dictionary):
        # call it on the flattened dict
        fattened_dict = flatten(dictionary)
        extrct_iter = (extrct(fattened_dict) for extrct in self.extractors)
        return dict(itertools.chain(*extrct_iter))

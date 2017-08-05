import collections
import itertools
import re

import datetime
import pandas as pd
import numpy as np

from scipy import sparse
from sklearn.base import TransformerMixin, BaseEstimator
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import LabelEncoder, OneHotEncoder, FunctionTransformer


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
                raise KeyError('value with key {} not found in dictionary'.format(self.key))
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

    def __init__(self, specs, sep='_'):
        self.extractors = [DictExtractor(**spec) for spec in specs]
        self.sep = sep

    def __call__(self, dictionary):
        # call it on the flattened dict
        fattened_dict = flatten(dictionary, sep=self.sep)
        extrct_iter = (extrct(fattened_dict) for extrct in self.extractors)
        return dict(itertools.chain(*extrct_iter))


KEY_NAMES = [
    'AantalBadkamers',
    'AantalKamers',
    'AantalWoonlagen',
    'Aanvaarding',
    'Adres',
    'BalkonDakterras',
    'BijdrageVVE',
    'Bijzonderheden',
    'Bouwjaar',
    'Bouwvorm',
    'BronCode',
    'EigendomsSituatie',
    'Energielabel.Definitief',
    'Energielabel.Index',
    'Energielabel.Label',
    'Energielabel.NietBeschikbaar',
    'Energielabel.NietVerplicht',
    'ErfpachtBedrag',
    'Garage',
    'GarageIsolatie',
    'GarageVoorzieningen',
    'GelegenOp',
    'GlobalId',
    'Inhoud',
    'Isolatie',
    'Koopprijs',
    'Ligging',
    'PerceelOppervlakte',
    'Perceeloppervlakte',
    'PermanenteBewoning',
    'Postcode',
    'ShortURL',
    'PublicatieDatum',
    'SchuurBerging',
    'SchuurBergingIsolatie',
    'SchuurBergingVoorzieningen',
    'ServiceKosten',
    'Soort-aanbod',
    'SoortDak',
    'SoortParkeergelegenheid',
    'SoortPlaatsing',
    'SoortWoning',
    'TuinLigging',
    'Verwarming',
    'VolledigeOmschrijving',
    'Voorzieningen',
    'WGS84_X',
    'WGS84_Y',
    'WarmWater',
    'WoonOppervlakte',
    'Woonoppervlakte',
    'Woonplaats'
]


def extract_preliminary(data, keys):
    """Extract a subset of keys from a dictionary, like the one returned
    by the crawler. Basially selects only the relevant keys from the dict
    like the one above."""
    extraction_specs = [{'key': key} for key in keys]
    extractor = DictMultiExtractor(extraction_specs, sep='.')
    df = pd.DataFrame(data.apply(extractor).tolist())
    return df[df['Koopprijs'].notnull()]  # return those that do not miss the Y


def extract_examples(data):
    """Extract and split data into X and Y"""
    df = extract_preliminary(data, KEY_NAMES)
    return df.drop('Koopprijs', axis='columns'), df['Koopprijs']


def mark_nans(df):
    """Extract additional features that indicate whether a feature is null or not.
    Good for preserving variance after missing value imputation."""
    nulls = df.isnull().astype(float)

    # suffix them with null
    null_cols = nulls.rename(columns={col: col + '_null' for col in df.columns})
    return null_cols


def extract_nums(series):
    """Extracts numbers from the given string Series. Returns a list of them for each record."""
    vals = series.apply(lambda x: re.findall(r'[0-9]+', x) if x else None)

    # return arrays for easier manipulation
    return vals.apply(lambda num_list: np.array([int(num) for num in num_list]) if num_list else np.array([]))


string_num_cols = ['PublicatieDatum', 'GelegenOp', 'Bouwjaar', 'AantalWoonlagen']


def extract_string_nums(df):
    """Extract string-formatted numerical columns. They can be dates, or
    columns containg filler info"""
    extracted = [extract_nums(df[col]) for col in string_num_cols]

    df = pd.concat(extracted, axis=1)

    # the years are sometimes given as intervals. do the mean
    df['Bouwjaar'] = df['Bouwjaar'].apply(lambda x: x.mean() if len(x) > 0 else None)

    # for the dates, transform the to datetime from UNIX seconds
    # ugly hack, but the format actually appends 3 zeroes at the end for no apparent reason
    date_func = lambda l: datetime.datetime.fromtimestamp(l[0] / 1000) if len(l) > 0 else None
    df['PublicatieDatum'] = df['PublicatieDatum'].apply(date_func)

    # it's just a single number
    extr_func = lambda x: x[0] if len(x) > 0 else None
    df['AantalWoonlagen'] = df['AantalWoonlagen'].apply(extr_func)
    df['GelegenOp'] = df['GelegenOp'].apply(extr_func)

    return df


cat_cols = ['Aanvaarding', 'Bouwvorm',
            'BronCode', 'Energielabel.Label', 'PermanenteBewoning',
            'SchuurBerging', 'Soort-aanbod', 'TuinLigging', 'Woonplaats']


def extract_int_cat(df):
    # extract int categorical data. simple normalized labels
    int_cat_cols = [LabelEncoder().fit_transform(df[col].fillna('')) for col in cat_cols]
    labels = np.stack(int_cat_cols, axis=1).astype(float)
    return labels


def extract_categorical(df):
    """Extracts categorical data as one-hot encoded features """
    num_cats = extract_int_cat(df)  # get the labels with NaNs accordingly
    features = []
    for i in range(num_cats.shape[1]):
        enc_cats = OneHotEncoder(handle_unknown='ignore').fit_transform(num_cats[:, i][:, np.newaxis])
        enc_cats[num_cats[:, i] == 0, :] = None  # nullify missing features
        features.append(enc_cats)

    return sparse.hstack(features)


short_text_cols = ['VolledigeOmschrijving',
                   'Voorzieningen',
                   'GarageVoorzieningen',
                   'SoortDak',
                   'GarageIsolatie',
                   'Ligging',
                   'EigendomsSituatie',
                   'SchuurBergingIsolatie',
                   'Bijzonderheden',
                   'BalkonDakterras',
                   'WarmWater',
                   'SoortWoning',
                   'Verwarming',
                   'Garage',
                   'Isolatie',
                   'SchuurBergingVoorzieningen']
descr_text_cols = ['VolledigeOmschrijving']


def unprefix_dict(d, pref):
    filtered_dict = {k[len(pref):]: v for k, v in d.items() if k.startswith(pref)}
    return filtered_dict


def extract_tf_idf(data, **kwargs):
    """Extract textual features """
    return TfidfVectorizer(**kwargs).fit_transform(data)


def extract_textual(df, use_short=True, use_long=True, **kwargs):
    """Extract textual features from the data as tf rows"""
    short_kwargs = unprefix_dict(kwargs, 'short_')
    descr_kwargs = unprefix_dict(kwargs, 'descr_')

    feats = []
    if use_short:
        feats.extend([extract_tf_idf(df[col].fillna(''),
                                           **short_kwargs)
                            for col in short_text_cols])
    if use_long:
        feats.extend([extract_tf_idf(df[col].fillna(''),
                                           **descr_kwargs)
                            for col in descr_text_cols])

    return sparse.hstack(feats)


num_cols = ['AantalBadkamers', 'AantalKamers', 'BijdrageVVE',
            'Energielabel.Definitief', 'Energielabel.Index',
            'Energielabel.NietBeschikbaar', 'Energielabel.NietVerplicht',
            'ErfpachtBedrag', 'Inhoud',
            'PerceelOppervlakte', 'ServiceKosten',
            'SoortPlaatsing', 'WoonOppervlakte',
            'WGS84_X', 'WGS84_Y', 'Koopprijs']


def extract_features(df, use_text=True, **kwargs):
    """Extracts features from the input data, returning a sparse matrix with all
    of them. Can specify whether to use textual data or not. All features starting
    with "text_" will be passed  to the Tf-Idf extractor. More specifically
    those starting wiht "text_short_" are passed to the one for non-paragraph
    data(short descriptions) and "text_descr_" ones are passed to the one
    used for prsing the description texts."""

    nan_features = mark_nans(df).values  # boolean feature for nans
    date_features = extract_string_nums(df)  # date features, not imputed
    num_features = df[num_cols].astype(float)  # numeric values(some bool, convert em)
    cat_features = extract_categorical(df)  # one-hot categorical features
    features = [num_features, cat_features, nan_features, date_features]

    # check whether to use textual features
    if use_text:
        text_kwargs = unprefix_dict(kwargs, 'text_')
        text_features = extract_textual(df, **text_kwargs)
        features.append(text_features)

    return sparse.hstack(features)


meta_cols = ['GlobalId', 'ShortURL']


def sanitize_data(df):
    """Returns a dataframe of sanitized data """
    date_features = extract_string_nums(df)  # date features, not imputed
    num_features = df[num_cols].astype(float)  # (some bool, convert em)
    cat_features = df[cat_cols]  # categorical features
    text_featues = df[descr_text_cols + short_text_cols]  # text features
    meta_features = df[meta_cols]  # additional columns used just as metadata

    return pd.concat([num_features, date_features, cat_features, text_featues, meta_features], axis='columns')


def sanitize_record(data_dict):
    """Given a dict of data, return a sanitized version of it,
    unlike the other functions which work with DataFrames.
    Used by the pipeline."""
    df = extract_preliminary(pd.Series([data_dict]), KEY_NAMES)
    # sanitize it
    return sanitize_data(df).iloc[0].to_dict()  # convert back to dict

class FeatureExtractor(BaseEstimator, TransformerMixin):
    def __init__(self, **kwargs):
        self.pass_kwargs = kwargs

    def transform(self, df, y=None):
        """The workhorse of this feature extractor"""
        return extract_features(df, **self.pass_kwargs)

    def fit(self, df, y=None):
        """Returns `self` unless something different happens in train and test"""
        return self
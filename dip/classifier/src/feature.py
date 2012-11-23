#!/usr/bin/env python

class Feature():
    '''
    This object contains one specific feature.
    '''
    def __init__(self, data):
        self.data = data
    def __str__(self):
        return 'Feature {0} ({1})'.format(self.__class__.__name__, self.data)
    def get_data(self):
        'Returns value stored in the Feature object'''
        return self.data

class Url(Feature):
    pass

class Email(Feature):
    pass

class Emoticon(Feature):
    pass

class Tag(Feature):
    pass

class SentenceCount(Feature):
    pass

class Ntuple(Feature):
    pass
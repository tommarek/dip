#!/usr/bin/env python

import logging
import numpy as np
import sqlite3
from ...common.entry import Entry

class Data():
    '''
    class used for data extraction and preparation
    '''
    def __init__(self, dbfile=None, n_fold_cv=10, max_token_size=1):
        '''
        init method
        @param dbfile: source db file containing table docs
        @param n_fold_cv: cross-validation specification
        @param max_token_size: set tokenization parameter
        '''
        # add and setup logger
        self._logger = logging.getLogger()
        logging.basicConfig(level=logging.DEBUG)
        # dbfile with labeled data
        self.dbfile = dbfile
        self.n_fold_cv = n_fold_cv
        self.max_token_size=max_token_size
        # load data
        if not dbfile:
            self.load_X1_X2()
        self.token_list = []

    def _get_data_from_db(self, count=1000):
        '''
        Method gets entries from database and
        @param count: count of relevant and irelevant entries (2*count)
        @return: list of entry objects
        '''
        # connect to database
        try:
            conn = sqlite3.connect(self.dbfile)
            cur = conn.cursor()
        except:
            print 'DB file {0} was not loaded!'.format(self.dbfile)
            return

        # load entries from database
        cur.execute('select distinct lang, text from docs where (annotation=1)')
        all_relevant = cur.fetchall()
        cur.execute('select distinct lang, text from docs where (annotation=0)')
        all_irelevant = cur.fetchall()

        # we need same amount of relevant and irelevnant
        count = min(len(all_relevant), len(all_irelevant), count)
        relevant = all_relevant[:count]
        irelevant = all_irelevant[:count]

        # join all entries together and set 1 and -1 to relevant and irelevant
        self._logger.info('Generating entries...')
        entries = []
        for data in relevant:
            entries.append(Entry(entry=data[1], language=data[0], label=1, max_token_size=self.max_token_size))
        for data in irelevant:
            entries.append(Entry(entry=data[1], language=data[0], label=-1, max_token_size=self.max_token_size))
        return entries

    def _generate_X1_X2(self, entries):
        '''
        Method generates X1 (vectors in feature space labeled 1) and X2 (vectors
        in feature space labeled -1) matrices svm classifier.
        @param entries: list of input entries
        @return matrices X1 and X2
        '''
        self.token_list = [] # all encountered tokens
        relevant_mapping = [] # mapping of articles into tokens
        irelevant_mapping = []

        # generate all possible token list
        self._logger.info('Generating all possible token list...')
        for entry in entries:
            for token in entry.get_token_all():
                self.token_list.append(token.get_data_str())
        self.token_list = list(set(self.token_list))

        # create mapping
        self._logger.info('Generating token mapping...')
        for entry in entries:
            to_tokens_mapping = []
            for token in entry.get_token_all():
                to_tokens_mapping.append(self.token_list.index(token.get_data_str()))
            if entry.label==1:
                relevant_mapping.append((to_tokens_mapping, entry.label))
            else:
                irelevant_mapping.append((to_tokens_mapping, entry.label))

        # generate X1 and X2 matrices (entry_count, token_count)
        self._logger.info('Generating X matrices...')
        relevant_mapping_count = len(relevant_mapping)
        irelevant_mapping_count = len(irelevant_mapping)
        dimensions = len(self.token_list)
        X1 = np.zeros((relevant_mapping_count, dimensions))
        X2 = np.zeros((irelevant_mapping_count, dimensions))
        self._logger.info('Generating X1 matrix...')
        for i,x1 in enumerate(X1):
            for index in relevant_mapping[i][0]:
                x1[index] = 1
        self._logger.info('Generating X2 matrix...')
        for i,x2 in enumerate(X2):
            for index in irelevant_mapping[i][0]:
                x2[index] = 1
        return (X1, X2)

    def _split_X1_X2(self, X1, X2, i=None):
        '''
        Splits X1 and X2 (vectors in feature space)to training and testing set,
        generates Y1 and Y2 vectors (labels).
        If i is not specified, all currently loaded data are returned
        @param X1: relevant vectors
        @param X2: irelevant vectors
        @param i: iteration in n-fold cross-validation
        @return: matrices X1, Y1 and if i is specified then also X2, Y2
        '''
        # number of X1 and X2 vectors
        count_1 = X1.shape[0]
        count_2 = X2.shape[0]

        # generate Y1 and Y2
        Y1 = np.ones(count_1)
        Y2 = -np.ones(count_2)

        if i is None:
            # create training set
            X_train = np.vstack((X1, X2))
            Y_train = np.hstack((Y1, Y2))

            return (X_train, Y_train)
        else:
            # create test set
            X_test = X1[i*(count_1/self.n_fold_cv):(i+1)*(count_1/self.n_fold_cv)]
            X_test = np.vstack((X_test, X2[i*(count_2/self.n_fold_cv):(i+1)*(
                count_1/self.n_fold_cv)]))
            Y_test = Y1[i*(count_1/self.n_fold_cv):(i+1)*(count_1/self.n_fold_cv)]
            Y_test = np.hstack((Y_test, Y2[i*(count_2/self.n_fold_cv):(i+1)*(
                count_1/self.n_fold_cv)]))
            # create training set
            X_train = X1[:i*(count_1/self.n_fold_cv)]
            X_train = np.vstack((X_train, X2[:i*(count_2/self.n_fold_cv)]))
            X_train = np.vstack((X_train, X1[(i+1)*(count_1/self.n_fold_cv):]))
            X_train = np.vstack((X_train, X2[(i+1)*(count_2/self.n_fold_cv):]))
            Y_train = Y1[:i*(count_1/self.n_fold_cv)]
            Y_train = np.hstack((Y_train, Y2[:i*(count_2/self.n_fold_cv)]))
            Y_train = np.hstack((Y_train, Y1[(i+1)*(count_1/self.n_fold_cv):]))
            Y_train = np.hstack((Y_train, Y2[(i+1)*(count_2/self.n_fold_cv):]))

            return (X_train, Y_train, X_test, Y_test)

    def regenerate_X1_X2(self, count):
        '''
        Method regenerates X1 and X2 values from database file.
        @param count: specifies number of slected entries
        '''
        self.X1, self.X2 = self._generate_X1_X2(self._get_data_from_db(count=count))
        X1_output = open('models/svm/X1_X2/X1.npy', 'wb')
        X2_output = open('models/svm/X1_X2/X2.npy', 'wb')
        np.save(X1_output, self.X1)
        np.save(X2_output, self.X2)

    def load_X1_X2(self):
        '''
        Method uses previously generated file from ../models/svm/X1_X2 directory
        '''
        self.X1 = np.load('models/svm/X1_X2/X1.npy')
        self.X2 = np.load('models/svm/X1_X2/X2.npy')

    def get(self, i=None):
        '''
        Get training and testing set for n-fold cross-validation.
        If i is not specified, all currently loaded data are returned
        @param i: iteration in n-fold cross-validation
        @return: tuple X_train, Y_train, X_test, Y_test
        '''
        if i is None:
            return self._split_X1_X2(self.X1, self.X2)
        else:
            return self._split_X1_X2(self.X1, self.X2, i)

    def get_token_list(self):
        '''
        Get token mapping list
        @return: token mapping list
        '''
        return self.token_list

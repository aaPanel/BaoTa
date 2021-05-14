#!/usr/bin/python
# -*- coding: utf-8 -*-
import re
import bson
import pymongo


class cached_classmethod(object):
    def __init__(self, f):
        self.f = f

    def __get__(self, instance, owner):
        value = self.f(owner)
        setattr(owner, self.f.__name__, value)
        return value


class Cursor(pymongo.cursor.Cursor):
    def __init__(self, *args, **kwargs):
        self._wrapper_class = kwargs.pop('wrap')
        super(Cursor, self).__init__(*args, **kwargs)

    def next(self):
        data = super(Cursor, self).next()
        return self._wrapper_class(data)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return super(Cursor, self).__getitem__(index)
        else:
            return self._wrapper_class(super(Cursor, self).__getitem__(index))


class Collection(pymongo.collection.Collection):
    document_class = None

    def __init__(self, *args, **kwargs):
        self.document_class = kwargs.pop('document_class')
        super(Collection, self).__init__(*args, **kwargs)

    def find(self, *args, **kwargs):
        return Cursor(self, *args, wrap=self.document_class, **kwargs)

    def find_one(self, *args, **kwargs):
        data = super(Collection, self).find_one(*args, **kwargs)
        if data:
            return self.document_class(data)
        return None

    def from_dbref(self, dbref):
        if not dbref.collection == self.name:
            raise ValueError('DBRef points to an invalid collection.')
        elif dbref.database and not dbref.database == self.database.name:
            raise ValueError('DBRef points to an invalid database.')
        else:
            return self.find_one(dbref.id)


class DocumentBase(type):
    _connections = {} # {(host, port): connection}

    def __new__(mcs, name, bases, attrs):
        # Define all cached classmethods here
        # for correct inheritance if it already cached
        new_class = super(DocumentBase, mcs).__new__(
                mcs, name, bases, attrs)
        parents = [b for b in bases if isinstance(b, DocumentBase)]
        if not parents:
            return new_class

        @cached_classmethod
        def conn(cls):
            kwargs = getattr(cls, '__connection__',
                    {'host': 'localhost', 'port': 27017})
            hostport = kwargs['host'], kwargs['port']
            if hostport not in cls._connections:
                cls._connections[hostport] = pymongo.Connection(**kwargs)
            return cls._connections[hostport]
        new_class.conn = conn

        @cached_classmethod
        def db(cls):
            assert hasattr(cls, '__database__'), (
                'Attribute __database__ is required for class %s' % cls.__name__)
            db = cls.conn[cls.__database__]
            if hasattr(cls, '__auth__'):
                assert db.authenticate(*cls.__auth__), 'Failed authenticate'
            return db
        new_class.db = db

        @cached_classmethod
        def coll(cls):
            '''Collection with object wrapper'''
            coll_name = getattr(cls, '__collection__', to_underscore(cls.__name__))
            coll = Collection(cls.db, coll_name, document_class=cls)
            for index in getattr(cls, '__indexes__', []):
                index.ensure(coll)
            if getattr(cls, '__safe__', False):
                coll.safe = True
            return coll
        new_class.coll = coll

        @cached_classmethod
        def find_one(cls):
            return cls.coll.find_one
        new_class.find_one = find_one

        @cached_classmethod
        def find(cls):
            return cls.coll.find
        new_class.find = find

        @cached_classmethod
        def update(cls):
            return cls.coll.update
        new_class.update = update

        @cached_classmethod
        def remove(cls):
            return cls.coll.remove
        new_class.remove = remove

        @cached_classmethod
        def count(cls):
            return cls.coll.count
        new_class.count = count

        return new_class


class Document(dict):
    __metaclass__ = DocumentBase

    def __init__(self, *args, **kwargs):
        super(Document, self).__init__(*args, **kwargs)
        self.__dict__['update'] = super(Document, self).update

    def __eq__(self, other):
        return '_id' in self and self['_id'] == other.get('_id')

    @classmethod
    def get_or_create(cls, spec, defaults=None):
        '''Find or create single document. Return (doc, created_now).'''
        docs = list(cls.find(spec).limit(2))
        assert len(docs) < 2, 'multiple docs returned'
        if docs:
            return docs[0], False
        else:
            kwargs = defaults or {}
            kwargs.update(spec)
            doc = cls(**kwargs)
            doc.save()
            return doc, True

    @classmethod
    def get_by_id(cls, id):
        try:
            return cls.find_one({'_id': bson.ObjectId(id)})
        except bson.errors.InvalidId:
            pass

    def save(self, *args, **kwargs):
        self.coll.save(self, *args, **kwargs)

    def save_fields(self, keys, *args, **kwargs):
        if isinstance(keys, basestring):
            keys = [keys]
        doc = dict((k, dotted_get(self, k)) for k in keys)
        self.coll.update({'_id': self['_id']}, {'$set': doc}, *args, **kwargs)

    def delete(self):
        '''Remove this object from the database'''
        ret = self.coll.remove(self['_id'])
        del self['_id']
        return ret

    def delete_fields(self, keys, *args, **kwargs):
        if isinstance(keys, basestring):
            keys = [keys]
        doc = dict((k, 1) for k in keys)
        self.coll.update({'_id': self['_id']}, {'$unset': doc}, *args, **kwargs)


    def atomic_update(self, doc, **kwargs):
        self.coll.update({'_id': self['_id']}, doc, **kwargs)

    @property
    def id(self):
        try:
            return unicode(self['_id'])
        except KeyError:
            pass


class Index(object):
    def __init__(self, *args, **kwargs):
        self._args = args
        self._kwargs = kwargs

    def __eq__(self, other):
        return self.__dict__ == other.__dict__

    def ensure(self, collection):
        return collection.ensure_index(*self._args, **self._kwargs)

def dotted_get(src, key):
    for subkey in key.split('.'):
        src = src[subkey]
    return src

def to_underscore(string):
    new_string = re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', string)
    new_string = re.sub(r'([a-z\d])([A-Z])', r'\1_\2', new_string)
    return new_string.lower()

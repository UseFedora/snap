#!/usr/bin/env python


import csv
import common


class NoSuchTargetFieldException(Exception):
    def __init__(self, field_name):
        Exception.__init__(self,
                           'RecordTransformer does not contain the target field %s.' % field_name)


class NoDatasourceForFieldException(Exception):
    def __init__(self, field_name):
        Exception.__init__(self,
                           'No datasource registered for target field name %s.' % field_name)


class NoSuchLookupMethodException(Exception):
    def __init__(self, method_name):
        Exception.__init__(self,
                           'Registered datasource of type %s has no lookup method "%s(...)' % (method_name))






class FieldValueResolver(object):
    def __init__(self, field_name_string):
        self._field_names = field_name_string.split('|')

    def resolve(self, source_record):
        for name in self._field_names:
            if source_record.get(name):
                return source_record[name]


class ConstValueResolver(object):
    def __init__(self, value):
        self._value = value

    def resolve(self, source_record):
        return self._value



class RecordTransformer:
    def __init__(self):
        self.target_record_fields = set()
        self.datasources = {}
        self.field_map = {}


    def add_target_field(self, target_field_name):
        self.target_record_fields.add(target_field_name)


    def map_source_to_target_field(self, source_field_designator, target_field_name):
        if not target_field_name in self.target_record_fields:
            raise NoSuchTargetFieldException(target_field_name)
        self.field_map[target_field_name] = FieldValueResolver(source_field_designator)


    def map_const_to_target_field(self, target_field_name, value):
        if not target_field_name in self.target_record_fields:
            raise NoSuchTargetFieldException(target_field_name)
        self.field_map[target_field_name] = ConstValueResolver(value)


    def register_datasource(self, target_field_name, datasource):
        if not target_field_name in self.target_record_fields:
            raise Exception()
        self.datasources[target_field_name] = datasource


    def lookup(self, target_field_name):
        datasource = self.datasources.get(target_field_name)
        if not datasource:
            raise NoDatasourceForFieldException(target_field_name)

        transform_func_name = 'lookup_%s' % (target_field_name)
        if not hasattr(datasource, transform_func_name):
            raise NoSuchLookupMethodException(transform_func_name)

        transform_func = getattr(datasource, transform_func_name)
        return transform_func(target_field_name)


    def transform(self, source_record, **kwargs):
        target_record = {}
        for key, value in kwargs.iteritems():
            target_record[key] = value

        for target_field_name in self.target_record_fields:
            if self.datasources.get(target_field_name):
                target_record[target_field_name] = self.lookup(target_field_name)
            elif self.field_map.get(target_field_name):
                source_field_resolver = self.field_map[target_field_name]
                target_record[target_field_name] = source_field_resolver.resolve(source_record)

        return target_record



class ConsoleProcessor(object):
    def __init__(self, processor=None):
        self._processor = processor

    def process(self, record):
        if self._processor:
            data = self._processor.process(record)
        else:
            data = record
        print common.jsonpretty(data)
        return data



class WhitespaceCleanupProcessor(object):
    def __init__(self):
        pass


    def process(self, record):
        data = {}
        for key, value in record.iteritems():
            data[key] = value.strip()

        return data



class CSVFileDataExtractor(object):
    def __init__(self, processor, **kwargs):
        self._data_handler = kwargs.get('data_handler')
        self._delimiter = kwargs.get('delimiter', ',')
        self._quote_char = kwargs.get('quotechar')
        self._processor = processor



    def extract(self, filename):
        with open(filename, 'rb') as datafile:
            csv_reader = csv.DictReader(datafile,
                                        delimiter=self._delimiter,
                                        quotechar=self._quote_char)
            for record in csv_reader:
                if self._data_handler:
                    self._processor.process(record)



    
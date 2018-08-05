# -*- coding: utf-8 -*-
# vim:fenc=utf-8
#
# Copyright © 2018 rmad17 <souravbasu17@gmail.com>
#
# Distributed under terms of the MIT license.
from abc import ABCMeta, abstractmethod

from django.core.exceptions import ValidationError
from django.db import IntegrityError


class AbstractBaseSerializer(metaclass=ABCMeta):
    @property
    @abstractmethod
    def model(self):
        raise NotImplementedError('missing model!')

    def _iterate_fields(self, kwargs):
        fields = [f.name for f in self.model._meta.get_fields()]
        for k, v in kwargs.items():
            if k in fields or k.split('__')[0] in fields:
                yield k, v

    def _clean_save_object(self, obj):
        obj.full_clean()
        obj.save()
        return obj

    def _get_clean_data(self, kwargs):
        clean_data = {}
        for k, v in self._iterate_fields(kwargs):
            clean_data[k] = v

        if not clean_data:
            raise ModelOperationError(
                INVALID_PARAMS.format(self.model.__name__))
        return clean_data

    def create_objects(self, kwargs, **extra):
        try:
            clean_data = {}
            for k, v in self._iterate_fields(kwargs):
                clean_data[k] = v
            obj = self.model(**clean_data)
            return self._clean_save_object(obj)
        except IntegrityError:
            msg = FAILED_OPS.format('save', self.model.__name__)
            self._raise_error(msg, **extra)

    def update_objects(self, obj, kwargs, **extra):
        try:
            for k, v in self._iterate_fields(kwargs):
                setattr(obj, k, v)
            return self._clean_save_object(obj)
        except (TypeError, ValueError, ValidationError):
            msg = FAILED_OPS.format('update', self.model.__name__)
            self._raise_error(msg, **extra)

    def get_object(self, kwargs, **extra):
        clean_data = self._get_clean_data(kwargs)
        try:
            return self.model.objects.get(**clean_data)
        except self.model.DoesNotExist:
            msg = OBJ_NOT_FOUND.format(self.model.__name__)
            self._raise_error(msg, **extra)

    def filter_objects(self, kwargs):
        clean_data = self._get_clean_data(kwargs)
        return self.model.objects.filter(**clean_data)

    @staticmethod
    def _raise_error(msg, **kwargs):
        if not kwargs.get('fail_silently', False):
            raise ModelOperationError(msg)

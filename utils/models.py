# -*- coding: utf-8 -*-
import django.db.models.fields.files

class FieldsToCleanMixin(object):
    """
    Mixin for Django models,
    allows to collect image & file fields which requires file removal. 
    """
    def file_fields_to_clean(self):
        """File fields to delete, when deleting news item"""
        out = []
        for field_name in self._meta.get_all_field_names():
            try:
                field = getattr(self, field_name)
            except Exception:
                continue
            if isinstance(field, (django.db.models.fields.files.FieldFile,
                                  django.db.models.fields.files.ImageFieldFile)):
                out.append(field)
        return out

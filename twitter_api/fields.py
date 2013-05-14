# -*- coding: utf-8 -*-
from django.db import models
from django.core import validators
from django.utils.translation import ugettext_lazy as _
from annoying.fields import JSONField
from picklefield.fields import PickledObjectField
import re

class PositiveSmallIntegerRangeField(models.PositiveSmallIntegerField):
    '''
    Range integer field with max_value and min_value properties
    from here http://stackoverflow.com/questions/849142/how-to-limit-the-maximum-value-of-a-numeric-field-in-a-django-model
    '''
    def __init__(self, verbose_name=None, name=None, min_value=None, max_value=None, **kwargs):
        self.min_value, self.max_value = min_value, max_value
        models.IntegerField.__init__(self, verbose_name, name, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'min_value': self.min_value, 'max_value':self.max_value}
        defaults.update(kwargs)
        return super(PositiveSmallIntegerRangeField, self).formfield(**defaults)

comma_separated_string_list_re = re.compile(u'^(?u)[\w#\[\], ]+$')
validate_comma_separated_string_list = validators.RegexValidator(comma_separated_string_list_re, _(u'Enter values separated by commas.'), 'invalid')

class CommaSeparatedCharField(models.CharField):
    '''
    Field for comma-separated strings
    TODO: added max_number validator
    '''
    default_validators = [validate_comma_separated_string_list]
    description = _("Comma-separated strings")

    def formfield(self, **kwargs):
        defaults = {
            'error_messages': {
                'invalid': _(u'Enter values separated by commas.'),
            }
        }
        defaults.update(kwargs)
        return super(CommaSeparatedCharField, self).formfield(**defaults)

try:
    from south.modelsinspector import add_introspection_rules
    add_introspection_rules([], ["^facebook_api\.fields"])
    add_introspection_rules([], ["^annoying\.fields"])
except ImportError:
    pass
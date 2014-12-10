# -*- coding: utf-8 -*-
from django.utils.functional import wraps

def opt_arguments(func):
    '''
    Meta-decorator for ablity use decorators with optional arguments
    from here http://www.ellipsix.net/blog/2010/08/more-python-voodoo-optional-argument-decorators.html
    '''
    def meta_wrapper(*args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            # No arguments, this is the decorator
            # Set default values for the arguments
            return func(args[0])
        else:
            def meta_func(inner_func):
                return func(inner_func, *args, **kwargs)
            return meta_func
    return meta_wrapper

@opt_arguments
def fetch_all(func, max_count):
    """
    Class method decorator for fetching all items. Add parameter `all=False` for decored method.
    If `all` is True, method runs as many times as it returns any results.
    Decorator receive 2 parameters:
      * integer `max_count` - max number of items method able to return
    Usage:

    @fetch_all(max_count=200)
    def fetch_something(self, ..., *kwargs):
        ....
    """
    def wrapper(self, all=False, return_instances=None, *args, **kwargs):
        if all:
            if not return_instances:
                return_instances = []
            kwargs['count'] = max_count
            instances = func(self, *args, **kwargs)
            instances_count = len(instances)
            return_instances += instances

            if instances_count > 1:
                # TODO: make protection somehow from endless loop
                kwargs['max_id'] = instances[instances_count-1].id
                return wrapper(self, all=True, return_instances=return_instances, *args, **kwargs)
            else:
                return self.model.objects.filter(id__in=[instance.id for instance in return_instances])
        else:
            return func(self, *args, **kwargs)

    return wraps(func)(wrapper)
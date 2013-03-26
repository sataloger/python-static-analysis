# -*- coding: utf-8 -*-
from analyzer.objects.unknown_object import UnknownObject


class BaseObject(UnknownObject):

    def __init__(self, *args, **kwargs):
        raise NotImplementedError("%s doesn't implement __init__()" % self.clsname)

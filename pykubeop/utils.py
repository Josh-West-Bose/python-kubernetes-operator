import collections

def _wrap(obj, obj_wrapper=None):
    if isinstance(obj, collections.Mapping):
        return AttrDict(obj) if obj_wrapper is None else obj_wrapper(obj)
    if isinstance(obj, list):
        return AttrList(obj)
    return obj

class AttrList(object):
    def __init__(self, l, obj_wrapper=None):
        if not isinstance(l, list):
            l = list(l)
        self._l_ = l
        self._obj_wrapper = obj_wrapper
    
    def __repr__(self):
        repr(self._l_)
    
    def __eq__(self, other):
        if isinstance(other, AttrList):
            return other._l_ == self._l_
        return other == self._l_
    
    def __ne__(self, other):
        return not self == other
    
    def __getitem__(self, k):
        l = self._l_[k]
        if isinstance(k, slice):
            return AttrList(l, self._obj_wrapper)
        return _wrap(l, self._obj_wrapper)
    
    def __setitem__(self, k, value):
        self._l_[k] = value

    def __iter__(self):
        return map(lambda i: _wrap(i, self._obj_wrapper), self._l_)
    
    def __len__(self):
        return len(self._l_)
    
    def __nonzero__(self):
        return bool(self._l_)    
    
    __bool__ = __nonzero__

    def __getattr__(self, name):
        return getattr(self._l_, name)
    
    def __getstate__(self):
        return (self._l_, self._obj_wrapper)
    
    def __setstate__(self, state):
        self._l_, self._obj_wrapper = state


class AttrDict(object):
    def __init__(self, d):
        super(AttrDict, self).__setattr__('_d_', d)
    
    def __contains__(self, key):
        return key in self._d_
    
    def __nonzero__(self):
        return bool(self._d_)
    
    __bool__ = __nonzero__

    def __dir__(self):
        return list(self._d_.keys())
    
    def __eq__(self, other):
        if isinstance(other, AttrDict):
            return other._d_ == self._d_
        return other == self._d_
    
    def __ne__(self, other):
        return not self == other
    
    def __repr__(self):
        r = repr(self._d_)
        if len(r) > 60:
            r = r[:60] + '...}'
        return r
    
    def __getstate__(self):
        return (self._d_, )

    def __setstate__(self, state):
        super(AttrDict, self).__setattr__('_d_', state[0])
    
    def __getattr__(self, attr):
        try:
            return self.__getitem__(attr)
        except KeyError:
            return None
        
    def __delattr__(self, attr):
        try:
            del self._d_[attr]
        except KeyError:
            return
    
    def __getitem__(self, key):
        return _wrap(self._d_[key])
    
    def __setitem__(self, key, value):
        self._d_[key] = value
    
    def __delitem__(self, key):
        del self._d_[key]
    
    def __setattr__(self, key, value):
        if key in self._d_ or not hasattr(self.__class__, key):
            self._d_[key] = value
        else:
            super(AttrDict, self).__setattr__(key, value)

    def __iter__(self):
        return iter(self._d_)
    
    def to_dict(self):
        return self._d_

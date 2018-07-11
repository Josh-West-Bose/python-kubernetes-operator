import unittest
import op.utils

class TestAttrList(unittest.TestCase):
    def test_slice(self):
        class MyAttrDict(op.utils.AttrDict):
            pass

        l = op.utils.AttrList([{}, {}], obj_wrapper=MyAttrDict)
        self.assertIsInstance(l[:][0], MyAttrDict)
    
    def test_items_get_wrapped_during_iteration(self):
        al = op.utils.AttrList([1, object(), [1], {}])
        l = list(iter(al))
        self.assertIsInstance(l[2], op.utils.AttrList)
        self.assertIsInstance(l[3], op.utils.AttrDict)
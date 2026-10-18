# Copyright (C) 2022 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only WITH Qt-GPL-exception-1.0
from __future__ import annotations

import os
import sys
import unittest

from pathlib import Path
sys.path.append(os.fspath(Path(__file__).resolve().parents[1]))
from shiboken_paths import init_paths  # noqa: E402
init_paths()

from shiboken6 import Shiboken  # noqa: E402
from sample import BlackBox, ObjectType, ObjectModel, ObjectView, Point  # noqa: E402


class MultipleInherited (ObjectType, Point):
    def __init__(self):
        ObjectType.__init__(self)
        Point.__init__(self)


class TestShiboken(unittest.TestCase):
    def testIsValid(self):
        self.assertTrue(Shiboken.isValid(object()))
        self.assertTrue(Shiboken.isValid(None))

        bb = BlackBox()
        item = ObjectType()
        ticket = bb.keepObjectType(item)
        bb.disposeObjectType(ticket)
        self.assertFalse(Shiboken.isValid(item))

    def testWrapInstance(self):
        addr = ObjectType.createObjectType()
        obj = Shiboken.wrapInstance(addr, ObjectType)
        self.assertFalse(Shiboken.createdByPython(obj))
        obj.setObjectName("obj")
        self.assertEqual(obj.objectName(), "obj")
        self.assertEqual(addr, obj.identifier())
        self.assertFalse(Shiboken.createdByPython(obj))

        # avoid mem leak =]
        bb = BlackBox()
        self.assertTrue(Shiboken.createdByPython(bb))
        bb.disposeObjectType(bb.keepObjectType(obj))

    def testWrapInstancePreserveId(self):
        """PYSIDE-31: Verify that wrapInstance() returns the existing wrapper
           even if a base class type is specified."""
        v = ObjectView()  # inherits ObjectType
        addresses = Shiboken.getCppPointer(v)
        self.assertTrue(addresses)
        address = addresses[0]
        wrapped = Shiboken.wrapInstance(address, ObjectType)
        self.assertEqual(id(wrapped), id(v))

    def testIsOwnedByPython(self):
        obj = ObjectType()
        self.assertTrue(Shiboken.ownedByPython(obj))
        p = ObjectType()
        obj.setParent(p)
        self.assertFalse(Shiboken.ownedByPython(obj))

    def testDump(self):
        """Just check if dump doesn't crash on certain use cases"""
        p = ObjectType()
        obj = ObjectType(p)
        obj2 = ObjectType(obj)
        obj3 = ObjectType(obj)  # noqa: F841
        self.assertEqual(Shiboken.dump(None), "Ordinary Python type.")
        Shiboken.dump(obj)

        model = ObjectModel(p)
        v = ObjectView(model, p)
        Shiboken.dump(v)

        m = MultipleInherited()
        Shiboken.dump(m)
        self.assertEqual(len(Shiboken.getCppPointer(m)), 2)

        # Don't crash even after deleting an object
        Shiboken.invalidate(obj)
        Shiboken.dump(obj)   # deleted
        Shiboken.dump(p)     # child deleted
        Shiboken.dump(obj2)  # parent deleted

    def testDelete(self):
        obj = ObjectType()
        child = ObjectType(obj)
        self.assertTrue(Shiboken.isValid(obj))
        self.assertTrue(Shiboken.isValid(child))
        # Note: this test doesn't assure that the object dtor was really called
        Shiboken.delete(obj)
        self.assertFalse(Shiboken.isValid(obj))
        self.assertFalse(Shiboken.isValid(child))

    def testInvalidateSequenceItemError(self):
        for sequence_type in (list, tuple):
            class BrokenItem(sequence_type):
                def __getitem__(self, index):
                    raise ValueError("sequence item error")

            with self.subTest(sequence_type=sequence_type):
                with self.assertRaisesRegex(ValueError, "sequence item error"):
                    Shiboken.invalidate(BrokenItem([None]))

    def testInvalidateSequenceLengthError(self):
        for sequence_type in (list, tuple):
            class BrokenLength(sequence_type):
                def __len__(self):
                    raise ValueError("sequence length error")

            with self.subTest(sequence_type=sequence_type):
                with self.assertRaisesRegex(ValueError, "sequence length error"):
                    Shiboken.invalidate(BrokenLength([None]))

    def testInvalidateSequenceOverReportedLength(self):
        for sequence_type in (list, tuple):
            class OverReportedLength(sequence_type):
                def __len__(self):
                    return super().__len__() + 1

            with self.subTest(sequence_type=sequence_type):
                with self.assertRaises(IndexError):
                    Shiboken.invalidate(OverReportedLength([None]))

    def testVersionAttr(self):
        self.assertEqual(type(Shiboken.__version__), str)
        self.assertTrue(len(Shiboken.__version__) >= 5)
        self.assertEqual(type(Shiboken.__version_info__), tuple)
        self.assertEqual(len(Shiboken.__version_info__), 5)

    def testAllWrappers(self):
        obj = ObjectType()
        self.assertTrue(obj in Shiboken.getAllValidWrappers())
        Shiboken.delete(obj)
        self.assertFalse(obj in Shiboken.getAllValidWrappers())


if __name__ == '__main__':
    unittest.main()

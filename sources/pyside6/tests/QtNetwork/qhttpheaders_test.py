# Copyright (C) 2026 The Qt Company Ltd.
# SPDX-License-Identifier: LicenseRef-Qt-Commercial OR GPL-3.0-only WITH Qt-GPL-exception-1.0

'''Test case for QHttpHeaders'''

import os
import sys
import unittest

from pathlib import Path
sys.path.append(os.fspath(Path(__file__).resolve().parents[1]))
from init_paths import init_test_paths
init_test_paths(False)

from PySide6.QtCore import qVersion
from PySide6 import QtNetwork
from PySide6.QtNetwork import QHttpHeaders


HAS_QT_612 = tuple(int(part) for part in qVersion().split('.')[:2]) >= (6, 12)
if HAS_QT_612:
    from PySide6.QtNetwork import QHttpHeaderRangeSet


class QHttpHeadersTest(unittest.TestCase):
    '''Test case for QHttpHeaders.'''

    def setRanges(self, headers, ranges):
        headers.setRangeValues(QHttpHeaderRangeSet(ranges) if HAS_QT_612 else ranges)

    def ranges(self, headers):
        result = headers.rangeValues()
        return result.ranges() if HAS_QT_612 and result is not None else result

    def testRange(self):
        h = QHttpHeaders()
        r = [(1, 2), (3, 4), (5, None), (None, 500)]
        self.setRanges(h, r)
        self.assertEqual(self.ranges(h), r)
        self.assertEqual(bytes(h.value("Range")), b"bytes=1-2, 3-4, 5-, -500")

    def testVersionedApis(self):
        self.assertTrue(hasattr(QHttpHeaders, "rangeValues"))
        self.assertTrue(hasattr(QHttpHeaders, "setRangeValues"))
        self.assertEqual(hasattr(QtNetwork, "QHttpHeaderRangeSet"), HAS_QT_612)
        self.assertEqual(hasattr(QtNetwork, "QSslKeyingMaterial"), HAS_QT_612)

    def testExistingHeadersApi(self):
        h = QHttpHeaders()
        self.assertTrue(h.append("Content-Type", "text/plain"))
        self.assertEqual(bytes(h.value("Content-Type")), b"text/plain")

    def testNoRange(self):
        self.assertEqual(self.ranges(QHttpHeaders()), [])

    def testMultipleRangeHeaders(self):
        h = QHttpHeaders()
        h.append("Range", "bytes= 0 - 499 , 1000- ")
        h.append("range", "seconds=1-2")
        h.append("Range", "bytes=-500")
        self.assertEqual(self.ranges(h), [(0, 499), (1000, None), (None, 500)])

    def testMalformedRanges(self):
        for value in ("bytes=", "bytes=-", "bytes=garbage", "bytes=a-2",
                      "bytes=2-a", "bytes=5-4", "bytes=1--2", "bytes=1-2,",
                      "bytes=9223372036854775808-", "bytes=0-9223372036854775808"):
            with self.subTest(value=value):
                h = QHttpHeaders()
                h.append("Range", value)
                self.assertIsNone(h.rangeValues())

    def testUnknownRangeUnitsAreIgnored(self):
        h = QHttpHeaders()
        h.append("Range", "seconds=1-2")
        self.assertEqual(self.ranges(h), [])

    def testSetRangeReplacesDuplicatesAndPreservesOtherHeaders(self):
        h = QHttpHeaders()
        h.append("Content-Type", "text/plain")
        h.append("Range", "bytes=1-2")
        h.append("Range", "bytes=3-4")
        self.setRanges(h, [(0, 0), (2**63 - 1, None)])
        self.assertEqual(len(h.values("Range")), 1)
        self.assertEqual(self.ranges(h), [(0, 0), (2**63 - 1, None)])
        self.assertEqual(bytes(h.value("Content-Type")), b"text/plain")
        self.setRanges(h, [])
        self.assertFalse(h.contains("Range"))
        self.assertEqual(self.ranges(h), [])
        self.assertTrue(h.contains("Content-Type"))

    def testRangeOverflowDoesNotChangeHeaders(self):
        h = QHttpHeaders()
        self.setRanges(h, [(1, 2)])
        with self.assertRaises(OverflowError):
            self.setRanges(h, [(2**63, None)])
        self.assertEqual(self.ranges(h), [(1, 2)])

    @unittest.skipUnless(HAS_QT_612, "QHttpHeaderRangeSet requires Qt 6.12")
    def testRangeSet(self):
        hs = QHttpHeaderRangeSet()
        r = [(1, 2), (3, 4), (5, None), (None, 500)]
        hs.setRanges(r)
        h = QHttpHeaders()
        h.setRangeValues(hs)
        self.assertEqual(h.rangeValues().ranges(), r)

    @unittest.skipUnless(HAS_QT_612, "QHttpHeaderRangeSet requires Qt 6.12")
    def testRangeSetOverflowDoesNotChangeRanges(self):
        hs = QHttpHeaderRangeSet([(1, 2)])
        with self.assertRaises(OverflowError):
            hs.setRanges([(2**63, None)])
        self.assertEqual(hs.ranges(), [(1, 2)])

    def testSequenceErrorsArePropagated(self):
        class BrokenLength:
            def __iter__(self):
                return iter([(1, 2)])

            def __len__(self):
                raise ValueError("broken length")

            def __getitem__(self, index):
                return (1, 2)

        class BrokenItem:
            def __iter__(self):
                return iter([(1, 2)])

            def __len__(self):
                return 1

            def __getitem__(self, index):
                raise ValueError("broken item")

        for sequence in (BrokenLength(), BrokenItem()):
            with self.subTest(sequence=type(sequence).__name__):
                h = QHttpHeaders()
                self.setRanges(h, [(1, 2)])
                with self.assertRaises(ValueError):
                    self.setRanges(h, sequence)
                self.assertEqual(self.ranges(h), [(1, 2)])
                if HAS_QT_612:
                    hs = QHttpHeaderRangeSet([(1, 2)])
                    with self.assertRaises(ValueError):
                        hs.setRanges(sequence)
                    self.assertEqual(hs.ranges(), [(1, 2)])

    @unittest.skipUnless(HAS_QT_612, "QHttpHeaderRangeSet requires Qt 6.12")
    def testRangesDoNotLeakReferences(self):
        hs = QHttpHeaderRangeSet([(1000, 2000)])
        # Small integers and None can be immortal; use live integers to detect leaks.
        for _ in range(10):
            r = hs.ranges()
            self.assertEqual(sys.getrefcount(r[0][0]), 2)
            self.assertEqual(sys.getrefcount(r[0][1]), 2)


if __name__ == '__main__':
    unittest.main()

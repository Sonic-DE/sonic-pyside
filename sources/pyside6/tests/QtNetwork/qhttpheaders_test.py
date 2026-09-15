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


def range_list(headers):
    '''rangeValues() as a list: Qt 6.12 returns a QHttpHeaderRangeSet, older Qt a list.'''
    ranges = headers.rangeValues()
    if HAS_QT_612 and ranges is not None:
        return ranges.ranges()
    return ranges


class QHttpHeadersTest(unittest.TestCase):
    '''Test case for QHttpHeaders.'''

    def testRange(self):
        h = QHttpHeaders()
        r = [(1, 2), (3, 4), (5, None), (None, 500)]
        h.setRangeValues(r)
        self.assertEqual(range_list(h), r)
        self.assertEqual(bytes(h.value("Range")), b"bytes=1-2, 3-4, 5-, -500")

    @unittest.skipUnless(HAS_QT_612, "QHttpHeaderRangeSet needs Qt 6.12")
    def testRangeSet(self):
        hs = QtNetwork.QHttpHeaderRangeSet()
        r = [(1, 2), (3, 4), (5, None)]
        hs.setRanges(r)
        h = QHttpHeaders()
        h.setRangeValues(hs)
        self.assertEqual(h.rangeValues().ranges(), r)

    def testVersionedApis(self):
        self.assertTrue(hasattr(QHttpHeaders, "rangeValues"))
        self.assertTrue(hasattr(QHttpHeaders, "setRangeValues"))
        self.assertEqual(hasattr(QtNetwork, "QSslKeyingMaterial"), HAS_QT_612)
        self.assertEqual(hasattr(QtNetwork, "QHttpHeaderRangeSet"), HAS_QT_612)

    def testExistingHeadersApi(self):
        h = QHttpHeaders()
        self.assertTrue(h.append("Content-Type", "text/plain"))
        self.assertEqual(bytes(h.value("Content-Type")), b"text/plain")

    def testNoRange(self):
        self.assertEqual(range_list(QHttpHeaders()), [])

    def testMultipleRangeHeaders(self):
        h = QHttpHeaders()
        h.append("Range", "bytes= 0 - 499 , 1000- ")
        h.append("range", "seconds=1-2")
        h.append("Range", "bytes=-500")
        self.assertEqual(range_list(h), [(0, 499), (1000, None), (None, 500)])

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
        self.assertEqual(range_list(h), [])

    def testSetRangeReplacesDuplicatesAndPreservesOtherHeaders(self):
        h = QHttpHeaders()
        h.append("Content-Type", "text/plain")
        h.append("Range", "bytes=1-2")
        h.append("Range", "bytes=3-4")
        h.setRangeValues([(0, 0), (2**63 - 1, None)])
        self.assertEqual(len(h.values("Range")), 1)
        self.assertEqual(range_list(h), [(0, 0), (2**63 - 1, None)])
        self.assertEqual(bytes(h.value("Content-Type")), b"text/plain")
        h.setRangeValues([])
        self.assertFalse(h.contains("Range"))
        self.assertEqual(range_list(h), [])
        self.assertTrue(h.contains("Content-Type"))

    def testRangeOverflowDoesNotChangeHeaders(self):
        h = QHttpHeaders()
        h.setRangeValues([(1, 2)])
        with self.assertRaises(OverflowError):
            h.setRangeValues([(2**63, None)])
        self.assertEqual(range_list(h), [(1, 2)])


if __name__ == '__main__':
    unittest.main()

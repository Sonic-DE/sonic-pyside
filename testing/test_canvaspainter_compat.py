# Copyright (C) 2026 SonicDE contributors
# SPDX-License-Identifier: BSD-3-Clause
"""Check versioned grabCanvas injections without requiring a Qt GPU backend."""

from pathlib import Path
import re
import unittest
import xml.etree.ElementTree as ET


PYSIDE = Path(__file__).resolve().parents[1] / "sources/pyside6/PySide6"


def version_tuple(value):
    parts = tuple(map(int, value.split(".")))
    return parts + (0,) * (3 - len(parts))


class CanvasPainterCompatibilityTest(unittest.TestCase):
    def test_grab_canvas_injections(self):
        root = ET.parse(PYSIDE / "QtCanvasPainter/typesystem_canvaspainter.xml").getroot()
        glue = (PYSIDE / "glue/qtcanvaspainter.cpp").read_text(encoding="utf-8")
        for qt_version in ("6.11.0", "6.11.2", "6.11.10", "6.12.0", "6.13.0"):
            version = version_tuple(qt_version)
            for name in ("QCanvasPainterWidget", "QCanvasRhiPaintDriver"):
                with self.subTest(qt_version=qt_version, name=name):
                    obj = root.find(f"object-type[@name='{name}']")
                    functions = [
                        f for f in obj.findall("add-function")
                        if f.attrib["signature"].startswith("grabCanvas(")
                        and version_tuple(f.get("since", "0")) <= version
                        <= version_tuple(f.get("until", "999"))
                    ]
                    self.assertEqual(len(functions), 1)
                    function = functions[0]
                    snippet = function.find("inject-code").attrib["snippet"]
                    marker = f"// @snippet {snippet}\n"
                    self.assertEqual(glue.count(marker), 2)
                    body = glue.split(marker)[1]
                    with_context = version >= (6, 12, 0)
                    self.assertEqual("QObject*@context@" in function.attrib["signature"],
                                     with_context)
                    self.assertEqual(re.findall(r"%PYARG_\d+", body),
                                     ["%PYARG_3" if with_context else "%PYARG_2"])
                    arguments = "%1, %2, callback" if with_context else "%1, callback"
                    self.assertIn(f"%CPPSELF.%FUNCTION_NAME({arguments});", body)


if __name__ == "__main__":
    unittest.main()

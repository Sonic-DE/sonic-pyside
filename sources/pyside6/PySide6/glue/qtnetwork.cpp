// Copyright (C) 2018 The Qt Company Ltd.
// SPDX-License-Identifier: LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only
// Qt-Security score:significant reason:default

// @snippet qudpsocket-readdatagram
Shiboken::ArrayPointer<char> data(%ARGUMENT_NAMES);
QHostAddress ha;
quint16 port;
%BEGIN_ALLOW_THREADS
%RETURN_TYPE retval = %CPPSELF.%FUNCTION_NAME(data, %ARGUMENT_NAMES, &ha, &port);
%END_ALLOW_THREADS
QByteArray ba(data, retval);
%PYARG_0 = PyTuple_New(3);
PyTuple_SetItem(%PYARG_0, 0, %CONVERTTOPYTHON[QByteArray](ba));
PyTuple_SetItem(%PYARG_0, 1, %CONVERTTOPYTHON[QHostAddress](ha));
PyTuple_SetItem(%PYARG_0, 2, %CONVERTTOPYTHON[quint16](port));
// @snippet qudpsocket-readdatagram

// @snippet qhostinfo-lookuphost-functor
struct QHostInfoFunctor : public Shiboken::PyObjectHolder
{
public:
    using Shiboken::PyObjectHolder::PyObjectHolder;

    void operator()(const QHostInfo &hostInfo);
};

void QHostInfoFunctor::operator()(const QHostInfo &hostInfo)
{
    Shiboken::GilState state;
    Shiboken::AutoDecRef arglist(PyTuple_New(1));
    auto *pyHostInfo = %CONVERTTOPYTHON[QHostInfo](hostInfo);
    PyTuple_SetItem(arglist.object(), 0, pyHostInfo);
    Shiboken::AutoDecRef ret(PyObject_CallObject(object(), arglist));
    release(); // single shot
}
// @snippet qhostinfo-lookuphost-functor

// @snippet qhostinfo-lookuphost-callable
%CPPSELF.%FUNCTION_NAME(%1, QHostInfoFunctor(%PYARG_2));
// @snippet qhostinfo-lookuphost-callable

// @snippet qhttpheaderrange-from-sequence
#if QT_VERSION >= QT_VERSION_CHECK(6, 12, 0)
using HttpHeaderRange = QHttpHeaderRangeSpec;
#else
// Temporary compatibility for Qt < 6.12. Mirror qtbase/5b1c236825's
// QHttpHeaders range helpers using the existing raw-header API.
struct HttpHeaderRange
{
    std::optional<qint64> start;
    std::optional<qint64> end;

    bool isValid() const
    {
        return (start || end) && (!start || *start >= 0) && (!end || *end >= 0)
            && (!start || !end || *start <= *end);
    }
};

static std::optional<QList<HttpHeaderRange>> httpHeaderRanges(const QHttpHeaders &headers)
{
    QList<HttpHeaderRange> result;
    const auto values = headers.values(QHttpHeaders::WellKnownHeader::Range);
    for (const QByteArray &value : values) {
        if (!value.startsWith("bytes="))
            continue;
        const auto parts = value.mid(6).split(',');
        for (const QByteArray &partBytes : parts) {
            const QLatin1StringView part(partBytes);
            const auto dash = part.indexOf(u'-');
            if (dash == -1)
                return std::nullopt;
            const auto start = part.first(dash).trimmed();
            const auto end = part.sliced(dash + 1).trimmed();
            HttpHeaderRange range;
            bool ok = false;
            if (!start.isEmpty()) {
                range.start = start.toLongLong(&ok);
                if (!ok)
                    return std::nullopt;
            }
            if (!end.isEmpty()) {
                range.end = end.toLongLong(&ok);
                if (!ok)
                    return std::nullopt;
            }
            if (!range.isValid())
                return std::nullopt;
            result.append(range);
        }
    }
    return result;
}

static void setHttpHeaderRanges(QHttpHeaders &headers, const QList<HttpHeaderRange> &ranges)
{
    if (ranges.isEmpty()) {
        headers.removeAll(QHttpHeaders::WellKnownHeader::Range);
        return;
    }
    QByteArray value("bytes=");
    for (qsizetype i = 0; i < ranges.size(); ++i) {
        if (i)
            value += ", ";
        if (ranges[i].start)
            value += QByteArray::number(*ranges[i].start);
        value += '-';
        if (ranges[i].end)
            value += QByteArray::number(*ranges[i].end);
    }
    headers.replaceOrAppend(QHttpHeaders::WellKnownHeader::Range, value);
}
#endif

using RangeType = qint64;

static std::optional<RangeType> rangeValueFromPython(PyObject *t)
{
    if (PyLong_Check(t) != 0)
        return PyLong_AsLongLong(t);
    return std::nullopt;
}

static HttpHeaderRange qHttpHeaderRangeFromSequence(PyObject *t)
{
    if (PySequence_Check(t) == 0 || PySequence_Size(t) != 2)
        return {};

    Shiboken::AutoDecRef start(PySequence_GetItem(t, 0));
    Shiboken::AutoDecRef end(PySequence_GetItem(t, 1));
    if (start.isNull() || end.isNull())
        return {};
    return {rangeValueFromPython(start), rangeValueFromPython(end)};
}

static PyObject *rangeValueToPython(const std::optional<RangeType> &v)
{
    if (v.has_value())
        return PyLong_FromLongLong(v.value());
    Py_RETURN_NONE;
}

static bool rangeSequenceToQList(PyObject *sequence, QList<HttpHeaderRange> *result)
{
    const auto size = PySequence_Size(sequence);
    if (size < 0)
        return false;
    result->reserve(size);
    for (Py_ssize_t i = 0; i < size; ++i) {
        Shiboken::AutoDecRef item(PySequence_GetItem(sequence, i));
        if (item.isNull())
            return false;
        result->append(qHttpHeaderRangeFromSequence(item.object()));
        if (PyErr_Occurred())
            return false;
    }
    return true;
}
// @snippet qhttpheaderrange-from-sequence

// @snippet qhttpheaderrangeset-sequence-constructor
QList<HttpHeaderRange> ranges;
if (!rangeSequenceToQList(%PYARG_1, &ranges))
    return -1;
%0 = new QHttpHeaderRangeSet(ranges);
// @snippet qhttpheaderrangeset-sequence-constructor

// @snippet qhttpheaderrangeset-ranges
const QSpan<const QHttpHeaderRangeSpec> ranges = %CPPSELF.%FUNCTION_NAME();
const auto size = ranges.size();
%PYARG_0 = PyList_New(size);
if (%PYARG_0 == nullptr)
    return nullptr;
for (Py_ssize_t i = 0; i < size; ++i) {
    const auto &range = ranges[i];
    Shiboken::AutoDecRef start(rangeValueToPython(range.start));
    Shiboken::AutoDecRef end(rangeValueToPython(range.end));
    if (start.isNull() || end.isNull()) {
        Py_DECREF(%PYARG_0);
        return nullptr;
    }
    PyObject *ob = PyTuple_Pack(2, start.object(), end.object());
    if (ob == nullptr) {
        Py_DECREF(%PYARG_0);
        return nullptr;
    }
    PyList_SetItem(%PYARG_0, i, ob);
}
// @snippet qhttpheaderrangeset-ranges

// @snippet qhttpheaderrangeset-setranges
QList<HttpHeaderRange> ranges;
if (!rangeSequenceToQList(%PYARG_1, &ranges))
    return nullptr;
%CPPSELF.%FUNCTION_NAME(ranges);
// @snippet qhttpheaderrangeset-setranges

// @snippet qhttpheaders-rangevalues-612
const std::optional<QHttpHeaderRangeSet> rangesOpt = %CPPSELF.%FUNCTION_NAME();
if (rangesOpt.has_value()) {
    const QHttpHeaderRangeSet &ranges = rangesOpt.value();
    %PYARG_0 = %CONVERTTOPYTHON[QHttpHeaderRangeSet](ranges);
} else {
    %PYARG_0 = Py_None;
    Py_INCREF(Py_None);
}
// @snippet qhttpheaders-rangevalues-612

// @snippet qhttpheaders-rangevalues
const auto rangesOpt = httpHeaderRanges(*%CPPSELF);
if (rangesOpt.has_value()) {
    const auto &ranges = rangesOpt.value();
    const auto size = ranges.size();
    %PYARG_0 = PyList_New(size);
    if (%PYARG_0 == nullptr)
        return nullptr;
    for (Py_ssize_t i = 0; i < size; ++i) {
        const auto &range = ranges[i];
        Shiboken::AutoDecRef start(rangeValueToPython(range.start));
        Shiboken::AutoDecRef end(rangeValueToPython(range.end));
        if (start.isNull() || end.isNull()) {
            Py_DECREF(%PYARG_0);
            return nullptr;
        }
        PyObject *ob = PyTuple_Pack(2, start.object(), end.object());
        if (ob == nullptr) {
            Py_DECREF(%PYARG_0);
            return nullptr;
        }
        PyList_SetItem(%PYARG_0, i, ob);
    }
} else {
    %PYARG_0 = Py_None;
    Py_INCREF(Py_None);
}
// @snippet qhttpheaders-rangevalues

// @snippet qhttpheaders-setrangevalues
QList<HttpHeaderRange> values;
if (!rangeSequenceToQList(%PYARG_1, &values))
    return nullptr;
setHttpHeaderRanges(*%CPPSELF, values);
// @snippet qhttpheaders-setrangevalues

// @snippet qipv6address-len
return 16;
// @snippet qipv6address-len

// @snippet qipv6address-getitem
if (_i >= 16) {
    PyErr_SetString(PyExc_IndexError, "index out of bounds");
    return nullptr;
}
if (_i < 0)
    _i = 16 - qAbs(_i);

uint item = %CPPSELF.c[_i];
return %CONVERTTOPYTHON[uint](item);
// @snippet qipv6address-getitem

// @snippet qipv6address-setitem
if (_i >= 16) {
    PyErr_SetString(PyExc_IndexError, "index out of bounds");
    return -1;
}
if (_i < 0)
    _i = 16 - qAbs(_i);
quint8 item = %CONVERTTOCPP[quint8](_value);
%CPPSELF.c[_i] = item;
return 0;
// @snippet qipv6address-setitem

// @snippet qrestaccessmanager-functor
class QRestFunctor
{
public:
    explicit QRestFunctor(PyObject *callable) noexcept : m_callable(callable)
    {
        Py_INCREF(callable);
    }

    void operator()(QRestReply &restReply);

private:
    PyObject *m_callable;
};

void QRestFunctor::operator()(QRestReply &restReply)
{
    Q_ASSERT(m_callable);
    Shiboken::GilState state;
    Shiboken::AutoDecRef arglist(PyTuple_New(1));
    auto *restReplyPtr = &restReply;
    auto *pyRestReply = %CONVERTTOPYTHON[QRestReply*](restReplyPtr);
    PyTuple_SetItem(arglist.object(), 0, pyRestReply);
    Shiboken::AutoDecRef ret(PyObject_CallObject(m_callable, arglist));
    Py_DECREF(m_callable);
    m_callable = nullptr;
}
// @snippet qrestaccessmanager-functor

// @snippet qrestaccessmanager-callback
auto *networkReply = %CPPSELF.%FUNCTION_NAME(%1, %2, QRestFunctor(%PYARG_3));
%PYARG_0 = %CONVERTTOPYTHON[%RETURN_TYPE](networkReply);
// @snippet qrestaccessmanager-callback

// @snippet qrestaccessmanager-data-callback
auto *networkReply = %CPPSELF.%FUNCTION_NAME(%1, %2, %3, QRestFunctor(%PYARG_4));
%PYARG_0 = %CONVERTTOPYTHON[%RETURN_TYPE](networkReply);
// @snippet qrestaccessmanager-data-callback

// @snippet qrestaccessmanager-method-data-callback
auto *networkReply = %CPPSELF.%FUNCTION_NAME(%1, %2, %3, %4, QRestFunctor(%PYARG_5));
%PYARG_0 = %CONVERTTOPYTHON[%RETURN_TYPE](networkReply);
// @snippet qrestaccessmanager-method-data-callback

// @snippet qrestreply-readjson
QJsonParseError jsonParseError;
std::optional<QJsonDocument> documentOptional = %CPPSELF.%FUNCTION_NAME(&jsonParseError);

PyObject *pyDocument{};
if (documentOptional.has_value()) {
    const auto &document = documentOptional.value();
    pyDocument = %CONVERTTOPYTHON[QJsonDocument](document);
} else {
    pyDocument = Py_None;
    Py_INCREF(Py_None);
}

%PYARG_0 = PyTuple_New(2);
PyTuple_SetItem(%PYARG_0, 0, pyDocument);
PyTuple_SetItem(%PYARG_0, 1, %CONVERTTOPYTHON[QJsonParseError](jsonParseError));
// @snippet qrestreply-readjson

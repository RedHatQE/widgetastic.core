# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import re
from xml.sax.saxutils import quoteattr, unescape


def quote(s):
    """Quotes a string in such a way that it is usable inside XPath expressions."""
    return unescape(quoteattr(s))


def normalize_space(text):
    """Works in accordance with the XPath's normalize-space() operator.

    `Description <https://developer.mozilla.org/en-US/docs/Web/XPath/Functions/normalize-space>`_:

        *The normalize-space function strips leading and trailing white-space from a string,
        replaces sequences of whitespace characters by a single space, and returns the resulting
        string.*
    """
    return re.sub(r'\s+', ' ', text.strip(), flags=re.UNICODE)

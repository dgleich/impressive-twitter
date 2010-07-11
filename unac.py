#!/usr/bin/env python
# -*- coding: utf-8 -*-

# By Joe Wreschnig, to show how stupid python-unac is.
# Released into the public domain.

"""unac - Remove accents from a string

This module contains one function. It removes accents and otherwise
decomposes Unicode characters within a Python str or unicode object.
"""

import unicodedata

def _notcomb(char):
    return not unicodedata.combining(char)

def unac_string(text, charset='utf-8', errors='strict'):
    """Unaccent a string.

    Pass in a unicode or a str object. For str objects a second
    argument that specifies the encoding of the string is
    required. This function returns an unaccented unicode or string
    object, depending on what was passed in.
    """
    was_str = False
    if isinstance(text, str):
        was_str = True
        text = text.decode(charset, errors)
    text = unicodedata.normalize("NFKD", text)
    text = filter(_notcomb, text)
    if was_str:
        text = text.encode(charset, errors)
    return text

if __name__ == "__main__":
    def assert_equal(a, b, enc='utf-8'):
        assert unac_string(a, enc) == b, "%r != %r" % (unac_string(a, enc), b)
    assert_equal("test", "test")
    assert_equal("\xe9t\xe9", "ete", 'latin1')

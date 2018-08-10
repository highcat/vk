# -*- coding: utf-8 -*-
import re
"""Text utils used by various algorithms

TODO cover with automated tests
"""

def are_words_in_text(words, text, case_sensitive=False):
    for w in words:
        # apply tags by simple match
        if is_word_in_text(w, text, case_sensitive):
            return True
    return False

def remove_word(word, text, case_sensitive=False):
    flags = re.U if case_sensitive else re.U|re.I
    return re.sub(r'(^|\s)%s([\s,:;.\-]|$)' % re.escape(word), ' ', text, flags=flags)

def is_word_in_text(word, text, case_sensitive=False):
    flags = re.U if case_sensitive else re.U|re.I
    return bool(re.search(r'(^|\s)%s([\s,:;.\-]|$)' % re.escape(word), text, flags=flags))

def split_comma_separated(line):
    return filter(
        lambda t:t,
        [norm(t) for t in line.split(',')],
    )

def norm(text):
    return re.sub('\s+', ' ', text, flags=re.U|re.M|re.S).strip()

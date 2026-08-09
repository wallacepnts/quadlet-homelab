#!/usr/bin/env python3
"""Language and colour for the terminal, shared by the three tools.

It lives in one file because the three have to agree: `qh` speaking Portuguese
while `qh-check` answers in English is worse than either alone.

Translation runs over the composed line, not over each f-string. The keys are
whole phrases, long enough that they cannot collide with a path or a service
name, and adding a message costs one dictionary entry either way.

No dependencies: stdlib only.
"""

import os
import sys

# QH_LANG wins, so a single run can be forced either way without touching the
# locale; otherwise the environment decides.
_lang = (os.environ.get("QH_LANG")
         or os.environ.get("LC_ALL") or os.environ.get("LANG") or "")
PTBR = _lang.lower().startswith("pt")


def translator(phrases):
    """A loc(s) for this script's phrases, longest first.

    Longest first matters: "the services" is a substring of "act on ALL the
    services in apps/", and translating the short one first leaves the line
    half English.
    """
    order = sorted(phrases.items(), key=lambda kv: -len(kv[0]))

    def loc(s):
        if not PTBR:
            return s
        for en, pt in order:
            if en in s:
                s = s.replace(en, pt)
        return s

    return loc


# Colour only when a person is looking: piped into a file or a grep, the escape
# codes are noise that breaks the very matching the pipe was for. NO_COLOR is
# the convention every tool that does this respects.
COLOR = sys.stdout.isatty() and not os.environ.get("NO_COLOR")


def _c(code):
    def pinta(s):
        return f"\033[{code}m{s}\033[0m" if COLOR else s
    return pinta


red = _c("31")
green = _c("32")
yellow = _c("33")
blue = _c("34")
dim = _c("2")
bold = _c("1")

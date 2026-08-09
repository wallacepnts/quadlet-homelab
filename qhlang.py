#!/usr/bin/env python3
"""Language detection and phrase translation, shared by the three tools.

It lives in one file because the three have to agree: `qh` speaking Portuguese
while `qh-check` answers in English is worse than either alone.

Translation runs over the composed line, not over each f-string. The keys are
whole phrases, long enough that they cannot collide with a path or a service
name, and adding a message costs one dictionary entry either way.

No dependencies: stdlib only.
"""

import os

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

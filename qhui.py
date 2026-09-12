#!/usr/bin/env python3
"""Language and colour for the terminal, shared by the three tools.

It lives in one file because the three have to agree: `qh` speaking Portuguese
while `qh-check` answers in English is worse than either alone.

Translation runs over the composed line, not over each f-string. The keys are
whole phrases, long enough that they cannot collide with a path or a service
name, and adding a message costs one dictionary entry either way.

Usage:
    python3 qhui.py --selftest  # test the translation and the colour

No dependencies: stdlib only.
"""

import os
import sys

def ptbr_from(env):
    """Whether to speak Portuguese, from the environment.

    QH_LANG wins, so a single run can be forced either way without touching the
    locale; otherwise LC_ALL, then LANG. A variable set to the empty string is
    not an answer — it falls through to the next, the way the shell means it.
    """
    lang = env.get("QH_LANG") or env.get("LC_ALL") or env.get("LANG") or ""
    return lang.lower().startswith("pt")


PTBR = ptbr_from(os.environ)


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


# argparse's own words: the `usage:` line, the section headings, `-h` and every
# error it raises. They come from gettext, and there is no pt_BR catalogue
# shipped with Python, so the lookup is replaced instead — the keys are the
# literals in the stdlib's argparse, and a miss falls back to English.
_ARGPARSE = {
    "usage: ": "uso: ",
    "positional arguments": "argumentos posicionais",
    "options": "opções",
    "show this help message and exit": "mostra esta ajuda e sai",
    "the following arguments are required: %s": "faltam estes argumentos: %s",
    "unrecognized arguments: %s": "argumentos desconhecidos: %s",
    "one of the arguments %s is required": "é preciso um destes argumentos: %s",
    "not allowed with argument %s": "não pode junto com %s",
    "expected one argument": "esperava um argumento",
    "expected at least one argument": "esperava ao menos um argumento",
    "expected at most one argument": "esperava no máximo um argumento",
    "ignored explicit argument %r": "argumento %r ignorado",
    "invalid choice: %(value)r (choose from %(choices)s)":
        "opção inválida: %(value)r (escolha entre %(choices)s)",
    "invalid %(type)s value: %(value)r": "valor inválido para %(type)s: %(value)r",
    "ambiguous option: %(option)s could match %(matches)s":
        "opção ambígua: %(option)s pode ser %(matches)s",
    "unexpected option: %(option)s": "opção inesperada: %(option)s",
    "argument %(argument_name)s: %(message)s": "argumento %(argument_name)s: %(message)s",
    "%(prog)s: error: %(message)s\n": "%(prog)s: erro: %(message)s\n",
    " (default: %(default)s)": " (padrão: %(default)s)",
    "expected %s argument": "esperava %s argumento",
    "expected %s arguments": "esperava %s argumentos",
}


def argparse_ptbr():
    """Translates argparse itself. Call before building the parser.

    `-h`'s own help text is translated when `add_argument` runs, which is inside
    `ArgumentParser.__init__` — patching afterwards leaves that one line English.
    """
    if not PTBR:
        return
    import argparse
    argparse._ = lambda s: _ARGPARSE.get(s, s)
    argparse.ngettext = lambda um, varios, n: _ARGPARSE.get(
        um if n == 1 else varios, um if n == 1 else varios)


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


def selftest():
    """The three things here that can be wrong without anyone noticing.

    Nothing tested this file, and it speaks for all three tools: a bug here is
    a line half in one language, or escape codes written into a pipe.
    """
    global PTBR, COLOR

    # Longest first. "the services" is inside "act on ALL the services", and
    # replacing the short one first leaves the rest of the phrase English --
    # the reason `translator` sorts at all.
    antes = PTBR
    PTBR = True
    try:
        loc = translator({"the services": "os serviços",
                          "act on ALL the services": "age em TODOS os serviços"})
        assert loc("act on ALL the services") == "age em TODOS os serviços"
        assert loc("the services in apps/") == "os serviços in apps/"
        # A key that is not in the line leaves it alone, and an unknown line
        # comes back whole rather than half-translated.
        assert loc("nothing to replace here") == "nothing to replace here"
        # Substitution is on the composed line, so a path inside it survives.
        assert loc("the services at /home/x") == "os serviços at /home/x"
    finally:
        PTBR = antes

    PTBR = False
    try:
        loc = translator({"hello": "olá"})
        assert loc("hello") == "hello", "English mode must not translate"
    finally:
        PTBR = antes

    # The environment, in the order the shell means it.
    assert ptbr_from({"QH_LANG": "pt_BR.UTF-8"}) is True
    assert ptbr_from({"QH_LANG": "en", "LANG": "pt_BR.UTF-8"}) is False, "QH_LANG wins"
    assert ptbr_from({"LC_ALL": "pt_BR.UTF-8", "LANG": "en_US"}) is True, "LC_ALL beats LANG"
    assert ptbr_from({"QH_LANG": "", "LANG": "pt_BR"}) is True, "empty is not an answer"
    assert ptbr_from({}) is False
    assert ptbr_from({"LANG": "C.UTF-8"}) is False

    # Colour only when a person is looking: piped or NO_COLOR, the escape codes
    # are noise that breaks the matching the pipe was for.
    cor = COLOR
    try:
        COLOR = True
        assert red("x") == "\033[31mx\033[0m"
        COLOR = False
        assert red("x") == "x", "no colour must leave the string byte for byte"
        assert dim("x") == "x"
    finally:
        COLOR = cor

    print("selftest: ok")


if __name__ == "__main__":
    # The flag is required, like the other three: a bare `python3 qhui.py`
    # running the tests would make the CI line read as something it is not.
    if "--selftest" not in sys.argv:
        print("usage: qhui.py --selftest", file=sys.stderr)
        raise SystemExit(2)
    selftest()

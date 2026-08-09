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

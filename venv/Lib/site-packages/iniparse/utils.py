from . import compat
from .ini import LineContainer, EmptyLine


def tidy(cfg):
    """Clean up blank lines.

    This functions makes the configuration look clean and
    handwritten - consecutive empty lines and empty lines at
    the start of the file are removed, and one is guaranteed
    to be at the end of the file.
    """

    if isinstance(cfg, compat.RawConfigParser):
        cfg = cfg.data
    cont = cfg._data.contents
    i = 1
    while i < len(cont):
        if isinstance(cont[i], LineContainer):
            tidy_section(cont[i])
            i += 1
        elif (isinstance(cont[i-1], EmptyLine) and
              isinstance(cont[i], EmptyLine)):
            del cont[i]
        else:
            i += 1

    # Remove empty first line
    if cont and isinstance(cont[0], EmptyLine):
        del cont[0]

    # Ensure a last line
    if cont and not isinstance(cont[-1], EmptyLine):
        cont.append(EmptyLine())


def tidy_section(lc):
    cont = lc.contents
    i = 1
    while i < len(cont):
        if isinstance(cont[i-1], EmptyLine) and isinstance(cont[i], EmptyLine):
            del cont[i]
        else:
            i += 1

    # Remove empty first line
    if len(cont) > 1 and isinstance(cont[1], EmptyLine):
        del cont[1]

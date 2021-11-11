# This file is part of UMAPINFO Designer.
#
# UMAPINFO Designer is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# UMAPINFO Designer is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with UMAPINFO Designer.  If not, see <https://www.gnu.org/licenses/>.
#
# Copyright 2021 Jading Tsunami
"""Parses UMAPINFO and returns a key/value list.

Does NOT care if the key/value pairs are valid.

Will only fail against an improperly-structured UMAPINFO file."""

import sys
import io
import re
import UMAPINFODesigner.structure as structure
from collections import defaultdict

def is_tuple(val):
    skip = False
    quote = False
    for c in val:
        if skip:
            skip = False
        elif c == "\\":
            skip = True
        elif c == '"':
            quote = not quote
        elif c == ',' and not quote:
            return True
    return False

def parse_value(val):
    """Parse a single UMAPINFO value of any type."""
    utype = structure.utypes.UType.UNKNOWN
    valstring = str(val)
    valprocessed = None
    if valstring.isnumeric():
        utype = structure.utypes.UType.NUMBER
        valprocessed = int(val)
    elif ",|" in valstring:
        # multiline string is the only value with a newline
        utype = structure.utypes.UType.MULTISTRING
        valprocessed = valstring.split(",|")
        for v in range(len(valprocessed)):
            # remove quote wraps
            vs = valprocessed[v].strip()[1:-1]
            # un-escape remaining quotes (will be re-added when
            # exported.
            vs = vs.replace('\\"', '"')
            valprocessed[v] = vs
    elif is_tuple(valstring):
        utype = structure.utypes.UType.TUPLE
        valprocessed = valstring.split(',')
        for v in range(len(valprocessed)):
            valprocessed[v] = valprocessed[v].strip()
    elif valstring.lower() in ['clear', 'true', 'false']:
        utype = structure.utypes.UType.KEYWORD
        valprocessed = valstring
    elif '"' in valstring:
        utype = structure.utypes.UType.STRING
        valprocessed = valstring.strip().strip('"')

    return structure.utypes.UMAPINFOValue(valprocessed, utype)

def parse_umapinfo(umapinfo):
    """Parses a full umapinfo. Expects a UMAPINFO as a string."""
    import re
    parsed_umapinfo = {}

    # Delete all comments
    umapinfo = re.sub(re.compile(r"/\*.*?\*/",re.DOTALL|re.MULTILINE),'',umapinfo)
    umapinfo = re.sub(r'//.*','',umapinfo)

    # Parse maps
    maps = re.split('{|}',umapinfo)
    inmap = False
    for m in maps:
        m = m.strip()
        if not m:
            continue
        if not inmap and m[:4].upper() == "MAP ":
            inmap = m[4:].strip()
        else:
            # FIXME: Don't rely on a magic character combo here
            m = re.sub(r',[\r\n]+',',|',m,flags=re.MULTILINE)
            m = m.split("\n")
            keyvals = defaultdict(list)
            for kv in m:
                (k,v) = kv.split('=')
                keyvals[k.strip().lower()].append(parse_value(v.strip()))
            parsed_umapinfo[inmap] = keyvals
            inmap = False

    return parsed_umapinfo

def stringify_value(val):
    stringified = ""
    if val.utype == structure.utypes.UType.KEYWORD or val.utype == structure.utypes.UType.NUMBER:
        stringified = str(val.value)
    elif val.utype == structure.utypes.UType.STRING:
        s = re.sub(r'([^\\])"', r'\1\"', val.value)
        stringified = '"' + s + '"'
    elif val.utype == structure.utypes.UType.MULTISTRING:
        for s in val.value:
            s = re.sub(r'([^\\])"', r'\1\"', s)
            stringified += '\t\t"' + s + '",\n'
        # strip off leading tabs and last comma and newline
        stringified = stringified[2:-2]
    elif val.utype == structure.utypes.UType.TUPLE:
        for t in val.value:
            stringified += str(t) + ", "
        # strip off last comma and space
        stringified = stringified[:-2]
    return stringified

def generate_umapinfo(umapinfo):
    """Takes in a set of umapinfo maps and generates a full UMAPINFO as a multiline string.
    Expects the UMAPINFO is a dictionary of key/value pairs with each key a map, and each
    value a dictionary of that map's keys."""
    processed_umapinfo = io.StringIO()
    processed_umapinfo.write("/* Created with UMAPINFO Designer by JadingTsunami */\n")
    for umap in umapinfo:
        processed_umapinfo.write("MAP " + umap + "\n{\n")
        for key in umapinfo[umap]:
            for subkey in umapinfo[umap][key]:
                processed_umapinfo.write("\t" + key + " = " + stringify_value(subkey) + "\n")
        processed_umapinfo.write("} //" + umap + "\n")
    retstring = processed_umapinfo.getvalue()
    processed_umapinfo.close()
    return retstring

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
"""Reads UMAPINFO from a WAD file (if present)."""
import omg
import re
from PIL import Image, ImageDraw, ImageTk

import os
import sys
from UMAPINFODesigner.structure.waddata import waddata

def read_umapinfo_from_wad(wadfile, encoding='ascii'):
    """Read UMAPINFO from WAD file.
    Expects string filename or open file record.
    Returns UMAPINFO as string.
    Throws KeyError if no UMAPINFO.
    Throws ValueError if UMAPINFO doesn't parse."""
    w = wadfile
    if not isinstance(wadfile, omg.WAD):
        w = omg.WAD(from_file=wadfile)
    # Raises KeyError if not found
    umapinfo_lump = w.data['UMAPINFO']
    return umapinfo_lump.data.decode(encoding)

def usafe(chars):
    return str(chars[:8]).upper()

def read_waddata_from_wad_if_match(wadfile, doom, doom2, clean=False):

    wad = wadfile
    if not isinstance(wadfile, omg.WAD):
        wad = omg.WAD(from_file=wadfile)

    umapinfo = None
    try:
        umapinfo = read_umapinfo_from_wad(wad)
    except KeyError:
        # no UMAPINFO, so ignore Doom vs. Doom 2 checks
        doom = True
        doom2 = True
    
    # if it has a umapinfo, check if it's compatible
    if doom and not doom2:
        if not re.search("MAP E[0-9]+M[0-9]+", umapinfo, re.IGNORECASE|re.MULTILINE):
            return False
    elif doom2 and not doom:
        if not re.search("MAP MAP[0-9]+", umapinfo, re.IGNORECASE|re.MULTILINE):
            return False

    if clean:
        waddata.clear()
    omg.util.safe_name = usafe
    waddata.merge(os.path.basename(wadfile), wad)
    return True

def is_wad_loaded(wadfile):
    return os.path.basename(wadfile) in waddata.wad

def read_waddata_from_wad(wadfile, clean=False):
    if clean:
        waddata.clear()
    omg.util.safe_name = usafe
    wad = wadfile
    if not isinstance(wadfile, omg.WAD):
        wad = omg.WAD(from_file=wadfile)
    waddata.merge(os.path.basename(wadfile), wad)

def get_waddata_umapinfo():
    return waddata.process_umapinfo()

def is_iwad(wadfile):
    with open(wadfile, "rb") as f:
        return f.read(4).decode('ascii') == 'IWAD'

def get_waddata(category):
    if category and hasattr(waddata, category):
        return getattr(waddata, category)
    else:
        return None

def get_waddata_map_image(mapn, width=192):
    # adapted from:
    # https://github.com/devinacker/omgifol/blob/master/demo/drawmaps.py
    mapw = waddata.get_map(mapn)
    if not mapw:
        return None
    edit = omg.MapEditor(mapw)
    if not edit:
        return None
    xmin = ymin = 32767
    xmax = ymax = -32768
    for v in edit.vertexes:
        xmin = min(xmin, v.x)
        xmax = max(xmax, v.x)
        ymin = min(ymin, -v.y)
        ymax = max(ymax, -v.y)

    xscale = width / float(xmax - xmin)
    yscale = width / float(ymax - ymin)
    xmax = int(xmax * xscale)
    xmin = int(xmin * xscale)
    ymax = int(ymax * yscale)
    ymin = int(ymin * yscale)

    for v in edit.vertexes:
        # smeghammer
        _x = round( v.x * xscale, None)
        _y = round(-v.y * yscale, None)

        v.x = _x
        v.y = _y

    im = Image.new('RGB', ((xmax - xmin) + 8, (ymax - ymin) + 8), (0,0,0))
    draw = ImageDraw.Draw(im)

    edit.linedefs.sort(key=lambda a: not a.two_sided)

    for line in edit.linedefs:
         p1x = edit.vertexes[line.vx_a].x - xmin + 4
         p1y = edit.vertexes[line.vx_a].y - ymin + 4
         p2x = edit.vertexes[line.vx_b].x - xmin + 4
         p2y = edit.vertexes[line.vx_b].y - ymin + 4

         color = (52, 235, 131)
         if line.two_sided:
             color = (206, 224, 214)
         if line.action:
             color = (217, 214, 50)

         draw.line((p1x, p1y, p2x, p2y), fill=color)

    del draw

    return ImageTk.PhotoImage(im)

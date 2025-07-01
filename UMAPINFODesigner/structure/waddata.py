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
from UMAPINFODesigner.uio import parser
from collections import OrderedDict

def get_chunk(d, offset, string=False):
    if string:
        return str(d[offset:offset+8], 'ascii').strip('\0')
    else:
        return int.from_bytes(d[offset:offset+4], 'little', signed=False)

def process_textures(tex):
    numtextures = get_chunk(tex, 0)
    textures = set()
    for i in range(numtextures):
        offs = get_chunk(tex, 4*i+4)
        name = get_chunk(tex, offs, True)
        textures.update([name])
    return textures


class waddata():
    wad = OrderedDict()
    graphics = set()
    glumps = {}
    music = set()
    flats = set()
    flumps = {}
    maps = set()
    data = set()
    textures = set()
    umapinfo = None

    def merge(newname, newwad):
        if newname not in waddata.wad:
            waddata.wad[newname] = newwad
            waddata.graphics.update(newwad.graphics.keys())
            waddata.glumps = {**waddata.glumps, **newwad.graphics}
            waddata.music.update(newwad.music.keys())
            waddata.flats.update(newwad.flats.keys())
            waddata.flumps = {**waddata.flumps, **newwad.flats}
            waddata.maps.update(newwad.maps.keys())
            waddata.data.update(newwad.data.keys())
            if 'UMAPINFO' in newwad.data:
                try:
                    waddata.umapinfo = newwad.data['UMAPINFO'].data.decode('ascii')
                except UnicodeDecodeError:
                    waddata.umapinfo = newwad.data['UMAPINFO'].data.decode('utf-8')

            for t in newwad.txdefs.keys():
                if t.startswith("TEXTURE"):
                    waddata.textures.update(process_textures(newwad.txdefs[t].data))
        else:
            # do nothing if already loaded
            pass

    def clear():
        waddata.wad = OrderedDict()
        waddata.graphics = set()
        waddata.glumps = {}
        waddata.music = set()
        waddata.flats = set()
        waddata.flumps = {}
        waddata.maps = set()
        waddata.data = set()
        waddata.umapinfo = None

    def process_umapinfo():
        if not waddata.umapinfo: return None
        return parser.parse_umapinfo(waddata.umapinfo)

    def get_map(mapname):
        """Get the most recent loaded map matching the supplied name."""
        for wad in reversed(waddata.wad):
            if mapname in waddata.wad[wad].maps:
                return waddata.wad[wad].maps[mapname]

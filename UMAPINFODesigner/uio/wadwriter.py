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
"""Writes UMAPINFO to a WAD file."""
import omg
import os

def write_umapinfo_to_wad(wadfile, umapinfo_string):
    """Write UMAPINFO to WAD file.
    Expects string UMAPINFO."""
    if os.path.exists(wadfile):
        w = omg.WAD(from_file=wadfile)
        os.replace(os.path.realpath(wadfile), os.path.realpath(wadfile) + ".umapinfo.bak")
    else:
        w = omg.WAD()

    w.data['UMAPINFO'] = omg.Lump(umapinfo_string.encode('ascii'))
    w.to_file(wadfile)

def write_umapinfo_to_file(filename, umapinfo_string):
    """Write UMAPINFO to file as a raw lump.
    Expects string UMAPINFO."""
    # Raises KeyError if not found
    omg.Lump(umapinfo_string.encode('ascii')).to_file(filename)

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
from enum import Enum

class IWADType(Enum):
    """Note this is ExMy or MAPxx style, not
    necessarily that it is a DOOM or DOOM2 wad."""
    UNKNOWN = 0
    DOOM = 1
    DOOM2 = 2

class UType(Enum):
    UNKNOWN = 0
    KEYWORD = 1
    NUMBER = 2
    STRING = 3
    MULTISTRING = 4
    TUPLE = 5

class UMAPINFOValue():
    def __init__(self,value,utype):
        self.utype = utype
        self.value = value

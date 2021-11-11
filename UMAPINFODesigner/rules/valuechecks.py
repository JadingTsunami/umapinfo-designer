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
"""Contains *_is_valid functions for each key."""
import re
import sys
from UMAPINFODesigner.rules import keys
from UMAPINFODesigner.structure.utypes import UMAPINFOValue
from UMAPINFODesigner.structure.utypes import UType
from UMAPINFODesigner.structure.waddata import waddata

def add_message(message, string):
    if isinstance(message, list):
        message.append(string)

def check_graphic(v, message):
    check_type(v, UType.STRING, message)
    if v.value not in waddata.graphics and not v.value in waddata.data:
        add_message(message, "Graphic lump " + str(v.value) + " not in WAD.")
        return False
    else:
        return True

def check_music(v, message):
    check_type(v, UType.STRING, message)
    if v.value in waddata.music:
        return True
    elif v.value in waddata.data:
        add_message(message, "WARNING: Could not verify lump " + str(v.value) + " is music.")
        return True
    else:
        add_message(message, "Music lump " + str(v.value) + " not in WAD.")
        return False

def check_flat(v, message):
    check_type(v, UType.STRING, message)
    if v.value not in waddata.flats:
        add_message(message, "Flat lump " + str(v.value) + " not in WAD.")
        return False
    else:
        return True

def check_map(v, message):
    check_type(v, UType.STRING, message)
    if v.value not in waddata.maps:
        add_message(message, "Map " + str(v.value) + " not in WAD.")
        return False
    else:
        return True

def check_bossaction_bossdeath(ttype, message):
    if ttype not in ["Fatso", "BaronOfHell", "Arachnotron", "SpiderMastermind", "Cyberdemon"]:
        t_name = keys.thing_types[ttype]
        add_message(message, "Warning! Thing type " + str(t_name) + " (ZDoom Type: " + str(ttype) + ") does not natively have an A_BossDeath call.\nUnless you have supplied a DeHackEd patch to add A_BossDeath checks to the enemy's death frames, this Boss Action WILL NOT WORK.\n\nThing Types with default A_BossDeath calls are:\n\nMancubus\nBaron of Hell\nArachnotron\nSpider Mastermind\nCyberdemon")

def check_bossaction_linespecial(spc, tag, message):
    # Tag can only be 0 for exits.
    # WARNING: Crossable types DO NOT work, see:
    # https://github.com/coelckers/prboom-plus/issues/176
    # "Use" (SR/S1) types do work.
    if spc <= 0:
        add_message(message, "BossAction Line special must be greater than 0.")
        return False
    elif tag < 0:
        add_message(message, "BossAction tag must be greater than or equal to 0.")
        return False
    elif tag == 0:
        if spc in [11, 51, 52, 124]:
            return True
        else:
            add_message(message, "BossAction tag 0 only allowed for exits.")
            return False
    else:
        if spc in keys.crossable_specials or (spc > 8192 and (spc & 0x7) <= 1):
            add_message(message, "WARNING: Crossable specials do not work due to a bug in PrBoom.\n\nChoose a \"usable\" (S1/SR) type instead.")
            return True
        # NOTE: Ordering of these 'if'/'elif' statements matters
        # NOTE: Locked doors are not filtered out here.
        elif spc in keys.usable_specials or (spc > 8192 and (spc & 0x7) <= 3):
            return True
        else:
            add_message(message, "Invalid BossAction line special: " + str(spc))
            return False
        return True

def check_boolean(value, message):
    if check_type(value, UType.KEYWORD, message):
        if value.value.lower() == 'true' or value.value.lower() == 'false':
            return True
        else:
            add_message(message, "Keyword " + str(value.value) + " is not a boolean.")
    return False

def check_clear(value, message):
    if check_type(value, UType.KEYWORD, message):
        if value.value.lower() == 'clear':
            return True
        else:
            add_message(message, "Keyword " + str(value.value) + " only allowed to be 'clear' for this field.")
    return False

def check_map_syntax(mapname, doom=True, doom2=True):
    match_doom = bool(re.match(r'^E[0-9]+M[0-9]+$', mapname.upper()))
    match_doom2 = bool(re.match(r'^MAP[0-9][0-9]+$', mapname.upper()))
    return (doom and match_doom) or (doom2 and match_doom2)

def check_type(value, expected_type, message=None):
    if isinstance(value, UMAPINFOValue):
        if value.utype == expected_type:
            return True
        else:
            add_message(message, "Expected a " + str(expected_type) + ", got " + str(value.utype))
            return False
    else:
        add_message(message,"Expected a UMAPINFOValue, got " + str(value))
        return False

def levelname_is_valid(value, message):
    return check_type(value, UType.STRING, message)

def label_is_valid(value, message):
    if check_type(value, UType.STRING, message):
        return True
    elif check_type(value, UType.KEYWORD):
        if message: message.pop()
        return check_clear(value, message)
    else:
        return False

def levelpic_is_valid(value, message):
    return check_graphic(value, message)

def next_is_valid(value, message):
    if not check_type(value, UType.STRING, message):
        return False
    elif not check_map_syntax(value.value):
        add_message(message, "Map syntax invalid, must be MAPxx or ExMy, got: " + str(value.value))
        return False
    else:
        return check_map(value, message)

def nextsecret_is_valid(value, message):
    return next_is_valid(value, message)

def skytexture_is_valid(value, message):
    # FIXME: Check against textures
    return check_type(value, UType.STRING, message)

def music_is_valid(value, message):
    return check_music(value, message)

def exitpic_is_valid(value, message):
    return check_graphic(value, message)

def enterpic_is_valid(value, message):
    return check_graphic(value, message)

def partime_is_valid(value, message):
    if check_type(value, UType.NUMBER, message):
        if value.value < 0:
            add_message(message, "Par time cannot be less than 0.")
            return False
        else:
            return True
    else:
        return False

def endgame_is_valid(value, message):
    return check_boolean(value, message)

def endpic_is_valid(value, message):
    return check_graphic(value, message)

def endbunny_is_valid(value, message):
    return check_boolean(value, message)

def endcast_is_valid(value, message):
    return check_boolean(value, message)

def nointermission_is_valid(value, message):
    return check_boolean(value, message)

def intertext_is_valid(value, message):
    if check_type(value, UType.STRING, message):
        return True
    elif check_type(value, UType.MULTISTRING, message):
        if message: message.pop()
        return True
    elif check_type(value, UType.KEYWORD, message):
        if message: 
            message.pop()
            message.pop()
        return check_clear(value, message)
    else:
        return False

def intertextsecret_is_valid(value, message):
    return intertext_is_valid(value, message)

def interbackdrop_is_valid(value, message):
    if check_graphic(value, message):
        return True
    elif check_flat(value, message):
        if message: message.pop()
        return True
    else:
        return False

def intermusic_is_valid(value, message):
    return music_is_valid(value, message)

def episode_is_valid(value, message):
    if check_type(value, UType.TUPLE, message):
        if not len(value.value) == 3:
            add_message(message, "Episode must be a tuple of 3, got: " + str(len(value.value)))
            return False
        else:
            for e in value.value:
                if not isinstance(e, str):
                    add_message(message, "Episode must be a tuple of 3 strings, got: " + str(e))
                    return False
            return True
    elif check_type(value, UType.KEYWORD):
        if message: message.pop()
        return check_clear(value, message)
    return False

def bossaction_is_valid(value, message):
    if check_type(value, UType.TUPLE, message):
        if not len(value.value) == 3:
            add_message(message, "BossAction must be a tuple of 3, got: " + str(len(value.value)))
            return False
        else:
            try:
                ttype = str(value.value[0])
            except ValueError:
                add_message(message, "BossAction ThingType was not a string.")
                return False
            try:
                linespecial = int(value.value[1])
            except ValueError:
                add_message(message, "BossAction line special was not an integer.")
                return False
            try:
                tag = int(value.value[2])
            except ValueError:
                add_message(message, "BossAction tag was not an integer.")
                return False

            if not ttype in keys.thing_types:
                add_message(message, str(ttype) + " is not a valid Thing type for BossActions.")
                return False
            elif not check_bossaction_linespecial(linespecial, tag, message):
                return False
            else:
                check_bossaction_bossdeath(ttype, message)
                return True
    elif check_type(value, UType.KEYWORD):
        if message: message.pop()
        return check_clear(value, message)
    return False

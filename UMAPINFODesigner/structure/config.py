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
import os
from configparser import ConfigParser
from UMAPINFODesigner.rules import keys
from UMAPINFODesigner.structure.utypes import IWADType

class settings:
    current_iwad = None
    current_iwad_type = IWADType.UNKNOWN

    def is_doom():
        return settings.current_iwad_type == IWADType.DOOM

    def is_doom2():
        return settings.current_iwad_type == IWADType.DOOM2

class configdata:
    config_file='.umapinfo-designer'
    config_section='umapinfo-designer'
    iwads_section='iwads'
    config_initialized = False
    config = None
    iwads = None

def validate_iwad_list():
    assert configdata.config_initialized
    for iwad in configdata.config[configdata.iwads_section]:
        if not os.path.exists(get_iwad(iwad)):
            remove_iwad(iwad)
    iwads = list(configdata.config[configdata.iwads_section].keys())
    if len(iwads) == 0:
        return False
    if get_last_iwad() not in iwads:
        set_iwad(iwads[0])
    return True

def initialize():
    configdata.config_file = os.path.join(os.path.expanduser("~"), configdata.config_file)
    configdata.config = ConfigParser()
    if os.path.exists(configdata.config_file):
        configdata.config.read(configdata.config_file)
        configdata.iwads = configdata.config[configdata.iwads_section]
    else:
        configdata.config.add_section(configdata.config_section)
        configdata.config.add_section(configdata.iwads_section)
    configdata.config_initialized = True

def set(setting, value):
    assert configdata.config_initialized
    configdata.config.set(configdata.config_section, setting, value)

def add_iwad(iwad, path):
    assert configdata.config_initialized
    configdata.config.set(configdata.iwads_section, iwad, path)
    configdata.iwads = configdata.config[configdata.iwads_section]

def remove_iwad(iwad):
    assert configdata.config_initialized
    configdata.config.remove_option(configdata.iwads_section, iwad)

def set_iwad(iwad):
    assert configdata.config_initialized
    settings.current_iwad = get_iwad(iwad)
    if iwad in keys.supported_iwads:
        settings.current_iwad_type = keys.supported_iwads[iwad]
    else:
        settings.current_iwad_type = IWADType.UNKNOWN
    configdata.config.set(configdata.config_section, "last_iwad", iwad)

def get_last_iwad():
    assert configdata.config_initialized
    return configdata.config.get(configdata.config_section, "last_iwad")

def get_iwad(iwad):
    assert configdata.config_initialized
    return configdata.config.get(configdata.iwads_section, iwad)
    
def get(setting):
    assert configdata.config_initialized
    return configdata.config.get(configdata.config_section, setting)

def write_config():
    assert configdata.config_initialized
    with open(configdata.config_file, 'w') as f:
        configdata.config.write(f)

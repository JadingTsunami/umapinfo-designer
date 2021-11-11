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
"""Verify or return a list of valid values for a given key.
Does NOT check validity in terms of rules, just whether the value is expected for the key type."""
from UMAPINFODesigner.rules import keys
from UMAPINFODesigner.rules import valuechecks

def is_valid(key, value, message=None):
    """Checks if a key/value pair is valid.
    Returns True/False.
    Optionally provides an informational message if an empty list is given as an argument."""
    if key not in keys.umapinfo_keys:
        # unrecognized key
        if isinstance(message, list):
            message.append("Unrecognized key: " + str(key))
        return False

    return getattr(valuechecks, str(key) + "_is_valid")(value, message)

def check_map_keys_valid(umap, messages=None):
    if not isinstance(messages, dict):
        messages = {}
    valid = True
    for key in umap:
        messages[key] = list()
        for value in umap[key]:
            valid &= is_valid(key, value, messages[key])
    return valid
        
def check_all_keys_valid(umapinfo, messages=None):
    if not isinstance(messages, dict):
        messages = {}
    valid = True
    for umap in umapinfo:
        messages[umap] = {}
        valid &= check_map_keys_valid(umapinfo[umap], messages[umap])
    return valid


def check_all_keys_and_remove_bad(umapinfo, warnings=None, errors=None):
    if not isinstance(warnings, dict):
        warnings = {}

    if not isinstance(errors, dict):
        errors = {}

    for umap in umapinfo:
        warnings[umap] = {}
        errors[umap] = {}
        for key in list(umapinfo[umap]):
            for value in list(umapinfo[umap][key]):
                messages = []
                if not is_valid(key, value, messages):
                    umapinfo[umap].pop(key, None)
                    if key not in errors[umap]:
                        errors[umap][key] = list()
                    errors[umap][key].extend(messages)
                elif messages:
                    if key not in warnings[umap]:
                        warnings[umap][key] = list()
                    warnings[umap][key].extend(messages)

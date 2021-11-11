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
from UMAPINFODesigner.structure import utypes
from UMAPINFODesigner.structure.utypes import UMAPINFOValue
from collections import defaultdict
from collections import OrderedDict

class umapinfo:
    """Memory-resident version of UMAPINFO being edited"""
    modified = False
    u = OrderedDict()

def load_umapinfo(um):
    umapinfo.u = um

def clear_umapinfo():
    umapinfo.u = OrderedDict()
    umapinfo.modified = False

# map access and manipulation
def add_map(newmap):
    if not newmap: return
    newmap = newmap.upper()
    if newmap not in umapinfo.u:
        umapinfo.u[newmap] = defaultdict(list)
    umapinfo.modified = True

def has_map(umap):
    if not umap: return False
    return umap.upper() in umapinfo.u

def sub_map(removemap):
    if umapinfo.u.pop(removemap, None):
        umapinfo.modified = True

def has_episodes():
    episodic = False
    for umap in umapinfo.u:
        ep = get_key(umap, 'episode')
        if ep and ep.utype == utypes.UType.TUPLE:
            episodic = True
            break
    return episodic

# episode handler
def resolve_episodes():
    """This function finds and resolves the episode
    definitions. Typically this would be called after
    making changes to the episode definitions within a
    WAD. It makes the assumption that the only
    valid KEYWORD type for episodes is 'clear'."""
    # first, find if there are any
    # defined episodes.
    # if there are, ensure the
    # first map has a "clear" as
    # the first entry

    # if it has episodes, ensure the first map
    # has a "clear" keyword as the first episode
    # entry.
    if has_episodes():
        first_map = next(iter(umapinfo.u))
        first_map_episode = get_key(first_map, 'episode')
        del_key(first_map, "episode")
        add_key(first_map, "episode", utypes.UType.KEYWORD, "clear")
        if first_map_episode and first_map_episode.utype == utypes.UType.TUPLE:
            add_key(first_map, "episode", utypes.UType.TUPLE, first_map_episode.value, append=True)
    else:
        # there are no episodes defined.
        # make sure all straggling episode clears are
        # removed if necessary.
        for umap in umapinfo.u:
            del_key(umap, "episode")

def num_episodes():
    ep_count = 0
    for umap in umapinfo.u:
        if has_key(umap, "episode") and get_key(umap, "episode").utype == utypes.UType.TUPLE:
            ep_count += 1
    return ep_count

def get_episodes():
    """Returns episode and its first map as an array of arrays."""
    eps = {}
    for umap in umapinfo.u:
        ep = get_key(umap, "episode")
        if ep and ep.utype == utypes.UType.TUPLE:
            # assumes no duplicates
            epname = ep.value[1]
            if not epname or len(epname) < 2: continue
            epname = epname[1:-1] # strip quotes
            eps[epname] = [umap]
    return eps

def get_episode_levels():
    """Returns array of levels that start episodes."""
    eps = []
    for umap in umapinfo.u:
        ep = get_key(umap, "episode")
        if ep and ep.utype == utypes.UType.TUPLE:
            eps.append(umap)
    return eps

# key access and manipulation
def map_episode(umap):
    ep = get_key(umap, 'episode')
    if ep:
        if ep.utype == utypes.UType.TUPLE:
            return ep.value[1].strip("\"")
        elif ep.utype == utypes.UType.KEYWORD:
            return ep.value
    else:
        return None

def map_name(umap):
    name = get_key(umap, 'levelname')
    if name:
        return name.value
    return None

def get_episode_tree():
    episode_tree = get_episodes()
    umaps = list(umapinfo.u.keys())
    # This has to be two-pass in case progression spans
    # episodes
    for eplevel in episode_tree:
        umaps.remove(episode_tree[eplevel][0])

    for eplevel in episode_tree:
        epstart = episode_tree[eplevel][0]
        nodes = [epstart]
        secretnodes = []
        visited = []
        while nodes or secretnodes:
            if nodes:
                curr_map = nodes.pop()
            elif secretnodes:
                curr_map = secretnodes.pop()
            if curr_map in visited:
                continue
            visited.append(curr_map)
            if curr_map not in episode_tree[eplevel]:
                episode_tree[eplevel].append(curr_map)
            if curr_map in umaps:
                umaps.remove(curr_map)
            nextsecret = get_key_value(curr_map, "nextsecret")
            nextlevel = get_key_value(curr_map, "next")
            if nextsecret: secretnodes.insert(0, nextsecret)
            if nextlevel: nodes.append(nextlevel)
    episode_tree["__noepisode"] = list(umaps)
    return episode_tree

def rename_map(oldmap, newmap):
    newmap = newmap.upper()
    if not has_map(oldmap):
        return None
    umapinfo.u = OrderedDict((newmap if k == oldmap else k, v) for k, v in umapinfo.u.items())
    umapinfo.modified = True

def has_key(umap, key):
    if not has_map(umap):
        return False
    return (key in umapinfo.u[umap]) and len(umapinfo.u[umap][key]) > 0

def add_key(umap, key, utype, val, append=False):
    assert isinstance(utype, utypes.UType)
    if not has_map(umap):
        return None

    ud = umapinfo.u[umap]
    uv = UMAPINFOValue(val, utype)

    if key not in ud or append:
        ud[key].append(uv)
    else:
        ud[key] = [uv]
    umapinfo.modified = True
    return uv

def del_key(umap, key):
    if not has_map(umap):
        return None

    ud = umapinfo.u[umap]

    if key in ud:
        ud[key] = list()
    umapinfo.modified = True

def get_key(umap, key, full_list=False):
    """Returns UMAPINFOValue"""
    value = None
    umap = umap.upper()
    if not has_key(umap, key):
        return None

    ukv = umapinfo.u[umap]

    if full_list:
        return ukv[key]
    elif len(ukv[key]) > 0:
        return ukv[key][-1]
    else:
        return None

def get_key_value(umap, key):
    # Can't return full list if one value is desired
    v = get_key(umap, key, False)
    if v:
        v = v.value
    return v


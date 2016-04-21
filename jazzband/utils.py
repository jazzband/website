def sub_dict(map, keys):
    if not keys:
        return map
    return {key: map[key] for key in keys if key in map}

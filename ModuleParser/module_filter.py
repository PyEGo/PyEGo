def apart_top_levels(top_levels, parts):
    in_parts = list()
    out_parts = list()
    for item in top_levels:
        if item in parts:
            in_parts.append(item)
        else:
            out_parts.append(item)
    return in_parts, out_parts


def apart_second_levels(second_levels, parts):
    in_parts = list()
    out_parts = list()
    for item in second_levels:
        top_level = item.split(".")[0]
        if top_level in parts:
            in_parts.append(item)
        else:
            out_parts.append(item)
    return in_parts, out_parts


def filter_custom_modules(top_levels, second_levels, custom_top_levels):
    _, filtered_tops = apart_top_levels(top_levels, custom_top_levels)
    _, filtered_seconds = apart_second_levels(second_levels, custom_top_levels)
    return filtered_tops, filtered_seconds


def apart_standard_modules(top_levels, second_levels, standard_top_levels):
    standard_tops, third_party_tops = apart_top_levels(top_levels, standard_top_levels)
    standard_seconds, third_party_seconds = apart_second_levels(second_levels, standard_top_levels)
    return standard_tops, standard_seconds, third_party_tops, third_party_seconds



def extract_int_parameter(params, key, default_value):
    if (key in params and len(params[key]) == 1 and params[key][0].isnumeric()):
        return int(params[key][0])
    return default_value

def extract_string_parameter(params, key, default_value):
    if key in params:
        if isinstance(params[key], str):
            return params[key]
        else:
            return params[key][0]
    return default_value


def parse_filters(params):
    if ("filter" in params):
        filters_arr = params.getlist('filter')
        result = {}
        for f in filters_arr:
            kv = f.strip().split(":")
            result[kv[0]] = kv[1]
        return result

    return None

def parse_sorting(params):
    if ("sort" in params):
        sort = params.getlist('sort')[0].strip()
        kv = sort.split(";")
        asc = True
        if (len(kv) > 1):
            if (kv[1] == "desc"):
                asc = False
        result = {
            "sort": kv[0],
            "ascending": asc
        }
        
        return result

    return None

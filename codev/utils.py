

def parse_options(inp):
    parsed = inp.split(':', 1)
    name = parsed[0]
    options = parsed[1] if len(parsed) == 2 else ''
    return name, options

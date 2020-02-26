def dictify(h):

    def next2yield(h):
        while True:
            n = h.next()
            if not n:
                break
            yield n

    result = {}
    for key in next2yield(h.keys()):
        if hasattr(h, 'h'):
            # haxe version change
            result[key] = h.h.get(key)
        else:
            result[key] = h.get(key)

    return result

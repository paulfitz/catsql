def dictify(h):

    def next2yield(h):
        while True:
            n = h.next()
            if not n:
                break
            yield n

    result = {}
    for key in next2yield(h.keys()):
        result[key] = h.get(key)

    return result

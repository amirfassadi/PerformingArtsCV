class LimitedFileIterator:
    def __init__(self, handle, length):
        self.handle = handle
        self.remaining = length

    def __iter__(self):
        return self

    def __next__(self):
        if self.remaining <= 0:
            raise StopIteration
        chunk = self.handle.read(min(self.remaining, 64 * 1024))
        if not chunk:
            raise StopIteration
        self.remaining -= len(chunk)
        return chunk

    def close(self):
        self.handle.close()

def parse_range(value, size):
    import re
    match = re.fullmatch(r'bytes=(\d*)-(\d*)', value)
    if not match or size == 0:
        raise ValueError('Invalid range')
    first, last = match.groups()
    if not first:
        if not last or int(last) <= 0:
            raise ValueError('Invalid suffix')
        start, end = max(0, size - int(last)), size - 1
    else:
        start = int(first)
        end = min(int(last), size - 1) if last else size - 1
    if start >= size or end < start:
        raise ValueError('Unsatisfiable range')
    return start, end

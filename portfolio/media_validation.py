import io
import binascii
import struct
import zlib

MAX_IMAGE_PIXELS = 40_000_000
MAX_IMAGE_DECODED_BYTES = 100_000_000
IMAGE_TYPES = {
    '.jpg': ('image/jpeg', 'jpeg'),
    '.jpeg': ('image/jpeg', 'jpeg'),
    '.png': ('image/png', 'png'),
    '.webp': ('image/webp', 'webp'),
}
VIDEO_TYPES = {'.mp4': ('video/mp4', 'mp4'), '.webm': ('video/webm', 'webm')}


class InvalidMedia(ValueError):
    pass


class MediaDecoderUnavailable(RuntimeError):
    pass


def validate_media(payload, suffix):
    if suffix in IMAGE_TYPES:
        content_type, kind = IMAGE_TYPES[suffix]
        validators = {'jpeg': _validate_jpeg, 'png': _validate_png, 'webp': _validate_webp}
    elif suffix in VIDEO_TYPES:
        content_type, kind = VIDEO_TYPES[suffix]
        validators = {'mp4': _validate_mp4, 'webm': _validate_webm}
    else:
        raise InvalidMedia
    try:
        validators[kind](payload)
        if kind in ('jpeg', 'png', 'webp'):
            _decode_image(payload, content_type)
        else:
            _decode_video(payload)
    except (InvalidMedia, IndexError, OverflowError, struct.error, zlib.error):
        raise InvalidMedia from None
    return content_type


def _decode_image(payload, expected_content_type):
    try:
        from PIL import Image, UnidentifiedImageError, features
    except ImportError as error:
        raise MediaDecoderUnavailable(
            'Pillow is required to validate uploaded images; install the declared runtime requirements.',
        ) from error

    expected_format = {
        'image/jpeg': 'JPEG',
        'image/png': 'PNG',
        'image/webp': 'WEBP',
    }[expected_content_type]
    if expected_format == 'WEBP' and not features.check('webp'):
        raise MediaDecoderUnavailable('The installed Pillow build does not include WebP decoding support.')
    try:
        with Image.open(io.BytesIO(payload)) as image:
            if image.format != expected_format:
                raise InvalidMedia
            width, height = image.size
            _dimensions(width, height)
            if width * height * len(image.getbands()) > MAX_IMAGE_DECODED_BYTES:
                raise InvalidMedia
            image.load()
    except (Image.DecompressionBombError, OSError, SyntaxError, UnidentifiedImageError, ValueError):
        raise InvalidMedia from None


def _decode_video(payload):
    try:
        import av
    except ImportError as error:
        raise MediaDecoderUnavailable(
            'PyAV is required to decode uploaded video; install the declared runtime requirements.',
        ) from error

    try:
        with av.open(io.BytesIO(payload), mode='r') as container:
            video_streams = container.streams.video
            if not video_streams:
                raise InvalidMedia
            stream = video_streams[0]
            codec = stream.codec_context
            _video_frame_size(codec.width, codec.height)
            codec.thread_count = 1
            frame = next(container.decode(stream), None)
            if frame is None or frame.is_corrupt:
                raise InvalidMedia
            _video_frame_size(frame.width, frame.height)
    except (av.error.FFmpegError, EOFError, OSError, ValueError):
        raise InvalidMedia from None


def _video_frame_size(width, height):
    _dimensions(width, height)
    if width * height * 4 > MAX_IMAGE_DECODED_BYTES:
        raise InvalidMedia


def _dimensions(width, height):
    if width < 1 or height < 1 or width * height > MAX_IMAGE_PIXELS:
        raise InvalidMedia


def _validate_png(data):
    if len(data) < 45 or data[:8] != b'\x89PNG\r\n\x1a\n':
        raise InvalidMedia

    offset = 8
    width = height = bit_depth = color_type = interlace = None
    compressed = []
    seen_idat = False
    idat_ended = False
    seen_iend = False
    channels_by_type = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}
    valid_depths = {0: {1, 2, 4, 8, 16}, 2: {8, 16}, 3: {1, 2, 4, 8}, 4: {8, 16}, 6: {8, 16}}

    while offset < len(data):
        if offset + 12 > len(data):
            raise InvalidMedia
        length = struct.unpack_from('>I', data, offset)[0]
        chunk_type = data[offset + 4:offset + 8]
        end = offset + 12 + length
        if end > len(data) or not all(65 <= byte <= 90 or 97 <= byte <= 122 for byte in chunk_type):
            raise InvalidMedia
        chunk = data[offset + 4:offset + 8 + length]
        expected_crc = struct.unpack_from('>I', data, offset + 8 + length)[0]
        if binascii.crc32(chunk) & 0xFFFFFFFF != expected_crc:
            raise InvalidMedia
        payload = data[offset + 8:offset + 8 + length]

        if width is None:
            if chunk_type != b'IHDR' or length != 13:
                raise InvalidMedia
            width, height, bit_depth, color_type, compression, filtering, interlace = struct.unpack(
                '>IIBBBBB', payload,
            )
            _dimensions(width, height)
            if (color_type not in valid_depths or bit_depth not in valid_depths[color_type]
                    or compression != 0 or filtering != 0 or interlace not in (0, 1)):
                raise InvalidMedia
        elif chunk_type == b'IHDR':
            raise InvalidMedia
        elif chunk_type == b'IDAT':
            if idat_ended:
                raise InvalidMedia
            seen_idat = True
            compressed.append(payload)
        else:
            if seen_idat:
                idat_ended = True
            if chunk_type == b'IEND':
                if length or not seen_idat or offset + 12 != len(data):
                    raise InvalidMedia
                seen_iend = True
                break
            if chunk_type == b'PLTE' and (length == 0 or length % 3 or length > 768):
                raise InvalidMedia
            if chunk_type[0] & 0x20 == 0 and chunk_type not in (b'PLTE',):
                raise InvalidMedia
        offset = end

    if not seen_iend or (color_type == 3 and not _png_has_palette(data)):
        raise InvalidMedia
    bits_per_pixel = channels_by_type[color_type] * bit_depth
    passes = [(0, 0, 1, 1)] if interlace == 0 else [
        (0, 0, 8, 8), (4, 0, 8, 8), (0, 4, 4, 8),
        (2, 0, 4, 4), (0, 2, 2, 4), (1, 0, 2, 2), (0, 1, 1, 2),
    ]
    expected_size = 0
    pass_sizes = []
    for x_start, y_start, x_step, y_step in passes:
        pass_width = max(0, (width - x_start + x_step - 1) // x_step)
        pass_height = max(0, (height - y_start + y_step - 1) // y_step)
        if pass_width and pass_height:
            row_size = (pass_width * bits_per_pixel + 7) // 8
            size = pass_height * (row_size + 1)
            expected_size += size
            pass_sizes.append((pass_height, row_size))
    if expected_size > MAX_IMAGE_DECODED_BYTES:
        raise InvalidMedia
    decoder = zlib.decompressobj()
    decoded = decoder.decompress(b''.join(compressed), expected_size + 1)
    if len(decoded) != expected_size or not decoder.eof or decoder.unused_data or decoder.unconsumed_tail:
        raise InvalidMedia
    cursor = 0
    for rows, row_size in pass_sizes:
        for _ in range(rows):
            if decoded[cursor] > 4:
                raise InvalidMedia
            cursor += row_size + 1


def _png_has_palette(data):
    offset = 8
    while offset + 12 <= len(data):
        length = struct.unpack_from('>I', data, offset)[0]
        chunk_type = data[offset + 4:offset + 8]
        if chunk_type == b'PLTE':
            return length > 0
        if chunk_type in (b'IDAT', b'IEND'):
            return False
        offset += length + 12
    return False


def _validate_jpeg(data):
    if len(data) < 16 or data[:2] != b'\xff\xd8':
        raise InvalidMedia
    offset = 2
    has_frame = False
    has_scan = False
    has_entropy = False
    frame_markers = {
        0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
        0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF,
    }

    while offset < len(data):
        if data[offset] != 0xFF:
            raise InvalidMedia
        while offset < len(data) and data[offset] == 0xFF:
            offset += 1
        if offset >= len(data):
            raise InvalidMedia
        marker = data[offset]
        offset += 1
        if marker == 0xD9:
            if not has_frame or not has_scan or not has_entropy or offset != len(data):
                raise InvalidMedia
            return
        if marker in (0xD8, 0x00) or 0xD0 <= marker <= 0xD7:
            if marker == 0xD8:
                raise InvalidMedia
            continue
        if offset + 2 > len(data):
            raise InvalidMedia
        segment_length = struct.unpack_from('>H', data, offset)[0]
        if segment_length < 2 or offset + segment_length > len(data):
            raise InvalidMedia
        segment = data[offset + 2:offset + segment_length]
        if marker in frame_markers:
            if len(segment) < 6:
                raise InvalidMedia
            precision, height, width, components = struct.unpack_from('>BHHB', segment)
            _dimensions(width, height)
            if precision not in (8, 12, 16) or components < 1 or len(segment) != 6 + 3 * components:
                raise InvalidMedia
            has_frame = True
        if marker == 0xDA:
            if not has_frame or len(segment) < 4:
                raise InvalidMedia
            components = segment[0]
            if components < 1 or len(segment) != 4 + 2 * components:
                raise InvalidMedia
            has_scan = True
            offset += segment_length
            scan_start = offset
            while offset < len(data):
                if data[offset] != 0xFF:
                    offset += 1
                    continue
                marker_start = offset
                offset += 1
                while offset < len(data) and data[offset] == 0xFF:
                    offset += 1
                if offset >= len(data):
                    raise InvalidMedia
                following = data[offset]
                if following == 0x00 or 0xD0 <= following <= 0xD7:
                    offset += 1
                    continue
                has_entropy = has_entropy or offset > scan_start
                offset = marker_start
                break
            if offset >= len(data) and not data.endswith(b'\xff\xd9'):
                raise InvalidMedia
            continue
        offset += segment_length
    raise InvalidMedia


def _validate_webp(data):
    if len(data) < 30 or data[:4] != b'RIFF' or data[8:12] != b'WEBP':
        raise InvalidMedia
    if struct.unpack_from('<I', data, 4)[0] + 8 != len(data):
        raise InvalidMedia
    offset = 12
    chunks = []
    while offset < len(data):
        if offset + 8 > len(data):
            raise InvalidMedia
        kind = data[offset:offset + 4]
        length = struct.unpack_from('<I', data, offset + 4)[0]
        end = offset + 8 + length + (length & 1)
        if end > len(data):
            raise InvalidMedia
        payload = data[offset + 8:offset + 8 + length]
        if length & 1 and data[end - 1] != 0:
            raise InvalidMedia
        chunks.append((kind, payload))
        offset = end
    image_chunks = [(kind, payload) for kind, payload in chunks if kind in (b'VP8 ', b'VP8L')]
    extensions = [payload for kind, payload in chunks if kind == b'VP8X']
    if len(image_chunks) != 1 or len(extensions) > 1:
        raise InvalidMedia
    if extensions:
        header = extensions[0]
        if len(header) != 10 or header[0] & 0xC1 or header[1:4] != b'\0\0\0':
            raise InvalidMedia
        width = 1 + int.from_bytes(header[4:7], 'little')
        height = 1 + int.from_bytes(header[7:10], 'little')
        _dimensions(width, height)
    kind, image = image_chunks[0]
    if kind == b'VP8 ':
        if len(image) <= 10 or image[0] & 1 or image[3:6] != b'\x9d\x01\x2a':
            raise InvalidMedia
        width, height = struct.unpack_from('<HH', image, 6)
        _dimensions(width & 0x3FFF, height & 0x3FFF)
    else:
        if len(image) < 6 or image[0] != 0x2F or image[4] & 0xE0:
            raise InvalidMedia
        width = 1 + image[1] + ((image[2] & 0x3F) << 8)
        height = 1 + ((image[2] & 0xC0) >> 6) + (image[3] << 2) + ((image[4] & 0x0F) << 10)
        _dimensions(width, height)


def _mp4_boxes(data, start, end, depth=0):
    if depth > 12:
        raise InvalidMedia
    boxes = []
    offset = start
    while offset < end:
        if offset + 8 > end:
            raise InvalidMedia
        size = struct.unpack_from('>I', data, offset)[0]
        kind = data[offset + 4:offset + 8]
        header_size = 8
        if size == 1:
            if offset + 16 > end:
                raise InvalidMedia
            size = struct.unpack_from('>Q', data, offset + 8)[0]
            header_size = 16
        elif size == 0:
            size = end - offset
        if size < header_size or offset + size > end:
            raise InvalidMedia
        box_end = offset + size
        boxes.append((kind, offset + header_size, box_end))
        offset = box_end
    if offset != end:
        raise InvalidMedia
    return boxes


def _validate_mp4(data):
    if len(data) < 32:
        raise InvalidMedia
    top = _mp4_boxes(data, 0, len(data))
    if not any(kind == b'ftyp' and end - start >= 8 for kind, start, end in top):
        raise InvalidMedia
    if not any(kind == b'mdat' and end > start for kind, start, end in top):
        raise InvalidMedia
    moov = [(start, end) for kind, start, end in top if kind == b'moov']
    if len(moov) != 1:
        raise InvalidMedia
    moov_children = _mp4_boxes(data, *moov[0], depth=1)
    has_video_track = False
    for kind, trak_start, trak_end in moov_children:
        if kind != b'trak':
            continue
        trak_children = _mp4_boxes(data, trak_start, trak_end, depth=2)
        mdia = [(start, end) for child, start, end in trak_children if child == b'mdia']
        if len(mdia) != 1:
            continue
        mdia_children = _mp4_boxes(data, *mdia[0], depth=3)
        handlers = [(start, end) for child, start, end in mdia_children if child == b'hdlr']
        minf = [(start, end) for child, start, end in mdia_children if child == b'minf']
        if len(handlers) != 1 or len(minf) != 1:
            continue
        hdlr_start, hdlr_end = handlers[0]
        if hdlr_end - hdlr_start < 12 or data[hdlr_start + 8:hdlr_start + 12] != b'vide':
            continue
        minf_children = _mp4_boxes(data, *minf[0], depth=4)
        stbl = [(start, end) for child, start, end in minf_children if child == b'stbl']
        if len(stbl) != 1:
            continue
        tables = _mp4_boxes(data, *stbl[0], depth=5)
        table_contents = {child: (start, end) for child, start, end in tables}
        required_tables = {b'stsd', b'stts', b'stsc', b'stsz'}
        if (required_tables.issubset(table_contents)
                and (b'stco' in table_contents or b'co64' in table_contents)
                and _mp4_table_has_entries(data, table_contents[b'stsd'], 4)
                and _mp4_table_has_entries(data, table_contents[b'stsz'], 8)
                and _mp4_table_has_entries(data, table_contents[b'stts'], 4)
                and _mp4_table_has_entries(data, table_contents[b'stsc'], 4)
                and _mp4_table_has_entries(
                    data, table_contents.get(b'stco', table_contents.get(b'co64')), 4,
                )):
            has_video_track = True
            break
    if not has_video_track:
        raise InvalidMedia


def _mp4_table_has_entries(data, bounds, count_offset):
    start, end = bounds
    count_position = start + count_offset
    return count_position + 4 <= end and struct.unpack_from('>I', data, count_position)[0] > 0


def _ebml_vint(data, offset, identifier=False):
    if offset >= len(data) or data[offset] == 0:
        raise InvalidMedia
    first = data[offset]
    mask = 0x80
    length = 1
    while not first & mask:
        mask >>= 1
        length += 1
        if length > (4 if identifier else 8):
            raise InvalidMedia
    if offset + length > len(data):
        raise InvalidMedia
    value = first if identifier else first & (mask - 1)
    for byte in data[offset + 1:offset + length]:
        value = (value << 8) | byte
    unknown = not identifier and value == (1 << (7 * length)) - 1
    return value, length, unknown


def _ebml_elements(data, start, end):
    elements = []
    offset = start
    while offset < end:
        element_id, id_length, _ = _ebml_vint(data, offset, identifier=True)
        size, size_length, unknown = _ebml_vint(data, offset + id_length)
        payload_start = offset + id_length + size_length
        payload_end = end if unknown else payload_start + size
        if payload_end > end or payload_end < payload_start:
            raise InvalidMedia
        elements.append((element_id, payload_start, payload_end))
        offset = payload_end
        if unknown:
            break
    if offset != end:
        raise InvalidMedia
    return elements


def _uint(data, start, end):
    if not 1 <= end - start <= 8:
        raise InvalidMedia
    return int.from_bytes(data[start:end], 'big')


def _validate_webm(data):
    if len(data) < 32:
        raise InvalidMedia
    top = _ebml_elements(data, 0, len(data))
    ebml = [(start, end) for kind, start, end in top if kind == 0x1A45DFA3]
    segments = [(start, end) for kind, start, end in top if kind == 0x18538067]
    if len(ebml) != 1 or len(segments) != 1:
        raise InvalidMedia
    ebml_elements = _ebml_elements(data, *ebml[0])
    if not any(kind == 0x4282 and data[start:end] == b'webm' for kind, start, end in ebml_elements):
        raise InvalidMedia
    segment_elements = _ebml_elements(data, *segments[0])
    tracks = [(start, end) for kind, start, end in segment_elements if kind == 0x1654AE6B]
    clusters = [(start, end) for kind, start, end in segment_elements if kind == 0x1F43B675]
    infos = [(start, end) for kind, start, end in segment_elements if kind == 0x1549A966]
    if len(tracks) != 1 or not clusters or len(infos) != 1:
        raise InvalidMedia
    video_track_numbers = set()
    track_entries = [
        (start, end) for kind, start, end in _ebml_elements(data, *tracks[0]) if kind == 0xAE
    ]
    for entry_start, entry_end in track_entries:
        fields = _ebml_elements(data, entry_start, entry_end)
        kinds = {kind: (start, end) for kind, start, end in fields}
        if (0xD7 not in kinds or 0x83 not in kinds
                or _uint(data, *kinds[0x83]) != 1 or 0x86 not in kinds):
            continue
        codec = data[kinds[0x86][0]:kinds[0x86][1]]
        if codec not in (b'V_VP8', b'V_VP9', b'V_AV1'):
            continue
        video_track_numbers.add(_uint(data, *kinds[0xD7]))
        if 0xE0 in kinds:
            video_fields = _ebml_elements(data, *kinds[0xE0])
            dimensions = {kind: (start, end) for kind, start, end in video_fields}
            if 0xB0 in dimensions and 0xBA in dimensions:
                _dimensions(
                    _uint(data, *dimensions[0xB0]),
                    _uint(data, *dimensions[0xBA]),
                )
    if not video_track_numbers:
        raise InvalidMedia
    has_frame = False
    for cluster_start, cluster_end in clusters:
        for kind, element_start, element_end in _ebml_elements(data, cluster_start, cluster_end):
            blocks = [(element_start, element_end)] if kind == 0xA3 else []
            if kind == 0xA0:
                blocks = [
                    (start, end) for child, start, end in _ebml_elements(data, element_start, element_end)
                    if child == 0xA1
                ]
            for start, end in blocks:
                if end - start < 5:
                    continue
                track_number, track_length, _ = _ebml_vint(data, start)
                frame_start = start + track_length + 3
                if track_number in video_track_numbers and frame_start < end:
                    has_frame = True
                    break
            if has_frame:
                break
        if has_frame:
            break
    if not has_frame:
        raise InvalidMedia

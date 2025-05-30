import argparse
import base64
import datetime
import hashlib
import io
import json
import zipfile
from zoneinfo import ZoneInfo

import cv2
import numpy
import pymupdf
import zxingcpp

BARCODES = {
    zxingcpp.BarcodeFormat.Aztec: 'PKBarcodeFormatAztec',
    zxingcpp.BarcodeFormat.Code128: 'PKBarcodeFormatCode128',
    zxingcpp.BarcodeFormat.PDF417: 'PKBarcodeFormatPDF417',
    zxingcpp.BarcodeFormat.QRCode: 'PKBarcodeFormatQR',
}
BARCODE_FORMATS = zxingcpp.BarcodeFormats(
    zxingcpp.BarcodeFormat.Aztec
    or zxingcpp.BarcodeFormat.Code128
    or zxingcpp.BarcodeFormat.PDF417
    or zxingcpp.BarcodeFormat.QRCode
)

ICON = base64.b64decode("""
iVBORw0KGgoAAAANSUhEUgAAAEAAAABACAMAAACdt4HsAAAAAXNSR0IArs4c6QAAAARnQU1BAACx
jwv8YQUAAAAgY0hSTQAAeiYAAICEAAD6AAAAgOgAAHUwAADqYAAAOpgAABdwnLpRPAAAADNQTFRF
AAAA/gAD/xAT/x8h/y4v/01O/2Rk/319/5OU/5ub/6+w/8LC/9HQ/9zd/ubm//Pz////JXIqAwAA
AAF0Uk5TAEDm2GYAAAABYktHRACIBR1IAAAACXBIWXMAAA7EAAAOxAGVKw4bAAAAB3RJTUUH6QUe
DTAymvC7FgAAAWZJREFUWMPtls2ahSAIho+l+Q/d/9XOaJnlhDm6OYu+XQnvowjI5/Pq1bdoZp2a
N/+JdWsa9I8EzoY0xw1wBx1yPG4hYPTaJR18I8D0AcwFACpLGwfZzqrrEt4DXBEd6ZKdKiOvsAXA
WLJTf1YENAGYRALAFiQBE+c5s/QZwIXIOWNJgFxXBJMs/QngYqTZYUYDguFy+joBjg/xAFhhPweU
gHRSfAAkL1sCYAc87SB9KmIHyyMA81kvANlwC5v2NoX5NIjo5dmqDhAl4G+G1QHLcQ0lgJtaMR0A
SQIUDAKOMusHMOE7gqjtr9SeoQL/f41bHvj9v3kCQM64C2DrpFuGVQGWSOW0ELZWBUiimFoBqcEB
dYSpDgBBNRTgOTj3gFAyty3NXlZsS1eOIbxNpEoetLV17gcfFj/0tAmD/Y+rNhaI13noeR8aMEJ9
zrZnxLFzHHGGh6yxMY+FQXHUf3zUffXqC/QDnptJNAYwk4oAAAAASUVORK5CYII=
""".strip())


def dump_pkpass(files: dict[str, bytes]) -> bytes:
    # https://developer.apple.com/documentation/walletpasses
    # https://file-extensions.com/docs/pkpass

    buf = io.BytesIO()
    manifest = {}

    with zipfile.ZipFile(buf, 'w') as zfh:
        for path, content in files.items():
            with zfh.open(path, 'w') as fh:
                fh.write(content)
            manifest[path] = hashlib.sha1(content).hexdigest()

        manifest_bytes = json.dumps(manifest).encode('utf-8')
        with zfh.open('manifest.json', 'w') as fh:
            fh.write(manifest_bytes)

    return buf.getvalue()


def pdf_iter_text_lines(pdf):
    for i in range(len(pdf)):
        text = pdf.get_page_text(i)
        yield from text.split('\n')


def extract_barcodes(pdf):
    barcodes = []
    for i in range(len(pdf)):
        for xref in pdf.get_page_images(i):
            img_data = pdf.extract_image(xref[0])
            arr = numpy.frombuffer(img_data['image'], numpy.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            results = zxingcpp.read_barcodes(img, formats=BARCODE_FORMATS)
            for result in results:
                barcodes.append((result.bytes, BARCODES[result.format]))
    return barcodes


def parse_leg_dt(datestr, timestr, prefix):
    tz = ZoneInfo('Europe/Berlin')
    now = datetime.datetime.now(tz=tz)
    year = now.year

    f = f'%Y %d.%m. {prefix} %H:%M'
    s = f'{year} {datestr} {timestr}'
    dt = datetime.datetime.strptime(s, f).astimezone(tz)
    if dt < now:
        s = f'{year + 1} {datestr} {timestr}'
        dt = datetime.datetime.strptime(s, f).astimezone(tz)
    return dt


def extract_legs(pdf):
    raw = []
    started = False
    lines = pdf_iter_text_lines(pdf)
    for line in lines:
        line = line.strip()
        if line.startswith('Ihre Reiseverbindung und Reservierung'):
            assert next(lines) == 'Halt'
            assert next(lines) == 'Datum'
            assert next(lines) == 'Zeit'
            assert next(lines) == 'Gleis'
            assert next(lines) == 'Produkte'
            assert next(lines) == 'Reservierung / Hinweise'
            started = True
        elif started and not line:
            break
        elif started:
            raw.append(line)

    i = 0
    legs = []
    while True:
        legs.append({
            'train': raw[i + 8],
            'start': {
                'station': raw[i],
                'datetime': parse_leg_dt(raw[i + 2], raw[i + 4], 'ab'),
                'platform': raw[i + 6],
            },
            'destination': {
                'station': raw[i + 1],
                'datetime': parse_leg_dt(raw[i + 3], raw[i + 5], 'an'),
                'platform': raw[i + 7],
            },
        })

        if i + 13 >= len(raw):
            break
        elif raw[i + 13].startswith('ab '):
            i += 9
        else:
            legs[-1]['comment'] = raw[i + 9]
            i += 10

    return legs


def extract_order_id(pdf):
    key = 'Auftragsnummer: '
    for line in pdf_iter_text_lines(pdf):
        if line.startswith(key):
            return line[len(key):]


def format_stop(stop, train=None):
    t = stop['datetime'].strftime('%H:%M')
    s = f'{t} {stop["station"]} #{stop["platform"]}'
    if train:
        s = f'{s} - {train}'
    return s


def format_legs(legs):
    s = ''
    for leg in legs:
        s += format_stop(leg['start'], train=leg['train']) + '\n'
        s += format_stop(leg['destination']) + '\n'
    return s


def extract_content(pdf):
    # https://developer.apple.com/documentation/walletpasses/pass

    order_id = extract_order_id(pdf)

    legs = extract_legs(pdf)
    start = legs[0]['start']['station']
    destination = legs[-1]['destination']['station']
    date = legs[0]['start']['datetime']

    return {
        'formatVersion': 1,
        'organizationName': 'Deutsche Bahn AG',
        'passTypeIdentifier': 'ticket.ce9e.org',
        'teamIdentifier': 'XXXXXXXXXX',
        'serialNumber': order_id,
        'description': f'{start} → {destination} ({date.date().isoformat()})',
        'barcodes': [
            {
                'format': _format,
                'message': message.decode('iso-8859-1'),
                'messageEncoding': 'iso-8859-1',
            }
            for message, _format in extract_barcodes(pdf)
        ],
        'boardingPass': {
            'transitType': 'PKTransitTypeTrain',
            'secondaryFields': [
                {
                    'key': 'date',
                    'label': 'Datum',
                    'dateStyle': 'PKDateStyleFull',
                    'timeStyle': 'PKDateStyleNone',
                    'value': date.isoformat(),
                },
                {
                    'key': 'legs',
                    'label': 'Reiseplan',
                    'value': format_legs(legs),
                },
                {
                    'key': 'order-id',
                    'label': 'Auftragsnummer',
                    'value': order_id,
                },
            ],
        },
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    args = parser.parse_args()

    with open(args.path, 'rb') as fh:
        pdf = pymupdf.open(stream=fh.read())
    content = extract_content(pdf)

    output_path = args.path.replace('.pdf', '.pkpass')
    with open(output_path, 'wb') as fh:
        fh.write(dump_pkpass({
            'pass.json': json.dumps(content).encode('utf-8'),
            'icon.png': ICON,
            'logo.png': ICON,
        }))

    print(f'written to {output_path}')

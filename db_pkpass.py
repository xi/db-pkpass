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

TZ = ZoneInfo('Europe/Berlin')

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


def strptime(s, _format):
    return datetime.datetime.strptime(s, _format).astimezone(TZ)


def extract_barcodes(pdf):
    barcodes = []
    for page in pdf:
        for xref in page.get_images():
            img_data = pdf.extract_image(xref[0])
            arr = numpy.frombuffer(img_data['image'], numpy.uint8)
            img = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            results = zxingcpp.read_barcodes(img, formats=BARCODE_FORMATS)
            for result in results:
                barcodes.append((result.bytes, BARCODES[result.format]))
    return barcodes


def parse_leg_dt(datestr, timestr, prefix, start):
    f = f'%d.%m.%Y {prefix} %H:%M'
    dt = strptime(f'{datestr}{start.year} {timestr}', f)
    if dt < start:
        dt = strptime(f'{datestr}{start.year + 1} {timestr}', f)
    return dt


def iter_lines(pdf):
    last_x = 0
    last_y = 0
    line = []
    for page in pdf:
        for x, y, _, _, text, _, _ in page.get_text('blocks'):
            text = text.rstrip('\n').replace(',\n', ', ')
            if x <= last_x or y > last_y:
                if line:
                    yield line
                line = [text]
            else:
                line.append(text)
            last_x = x
            last_y = y
    if line:
        yield line


def extract_legs(pdf):
    legs = []
    started = False
    validity = extract_validity(pdf)
    for line in iter_lines(pdf):
        text = ' '.join(line)
        if text.startswith('Halt\nDatum\nZeit\nGleis'):
            started = True
        elif not started or text.startswith('Ihre Reiseverbindung '):
            pass
        elif text.startswith('Wichtige Nutzungshinweise') or not text.strip():
            break
        else:
            station1, station2 = (v.strip() for v in line[0].split('\n'))
            date1, date2 = (v.strip() for v in line[1].split('\n'))
            time1, time2 = (v.strip() for v in line[2].split('\n'))
            legs.append({
                'start': {
                    'station': station1,
                    'datetime': parse_leg_dt(date1, time1, 'ab', validity[0])
                },
                'destination': {
                    'station': station2,
                    'datetime': parse_leg_dt(date2, time2, 'an', validity[0])
                },
            })

            if len(line) > 3:
                platform1, platform2 = (v.strip() for v in line[3].split('\n'))
                if platform1:
                    legs[-1]['start']['platform'] = platform1
                if platform2:
                    legs[-1]['destination']['platform'] = platform2

            if len(line) > 4:
                legs[-1]['train'] = line[4].strip().replace('\n', ' ')
            else:
                legs[-1]['train'] = legs[-1]['destination'].pop('platform')

            if len(line) > 5:
                legs[-1]['comment'] = line[5].strip().replace('\n', ' ')

    return legs


def extract_id(pdf):
    for page in pdf:
        for text in page.get_text().split('\n'):
            for label in ['Auftragsnummer', 'BahnCard-Nr.']:
                key = f'{label}: '
                if text.startswith(key):
                    return label, text[len(key):]
    raise ValueError('No ID found')


def extract_title(pdf):
    return pdf[0].get_text('blocks')[1][4].strip()


def extract_validity(pdf):
    key1 = 'Gültigkeit: '
    key2 = 'Fahrtantritt am '
    for page in pdf:
        for text in page.get_text().split('\n'):
            if text.startswith(key1):
                s_start, s_end = text[len(key1):].split(' bis ')
                try:
                    start = strptime(s_start, '%d.%m.%Y %H:%M Uhr')
                    end = strptime(s_end, '%d.%m.%Y %H:%M Uhr')
                except ValueError:
                    start = strptime(s_start, '%d.%m.%Y')
                    end = strptime(s_end, '%d.%m.%Y')
                return start, end
            elif text.startswith(key2):
                s_start = text[len(key2):]
                start = strptime(s_start, '%d.%m.%Y')
                end = start + datetime.timedelta(days=1)
                return start, end
    raise ValueError('No validity information found')


def format_stop(stop, train=None):
    t = stop['datetime'].strftime('%H:%M')
    s = f'{t} {stop["station"]}'
    if stop.get('platform'):
        s += f' #{stop["platform"]}'
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
    title = extract_title(pdf)
    id_label, id_value = extract_id(pdf)
    validity = extract_validity(pdf)

    data = {
        'formatVersion': 1,
        'organizationName': 'Deutsche Bahn AG',
        'passTypeIdentifier': 'ticket.ce9e.org',
        'teamIdentifier': 'XXXXXXXXXX',
        'serialNumber': id_value,
        'description': title,
        'expirationDate': validity[1].isoformat(),
        'relevantDates': [
            {
                'startDate': validity[0].isoformat(),
                'endDate': validity[1].isoformat(),
            },
        ],
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
            'auxiliaryFields': [
                {
                    'key': 'id',
                    'label': id_label,
                    'value': id_value,
                },
            ],
        },
    }

    legs = extract_legs(pdf)
    if legs:
        start = legs[0]['start']['station']
        destination = legs[-1]['destination']['station']
        date = legs[0]['start']['datetime']
        data['description'] = f'{start} → {destination} ({date.date().isoformat()})'
        data['boardingPass']['secondaryFields'] = [
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
        ]

    return data


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('path')
    parser.add_argument('--debug', action='store_true')
    args = parser.parse_args()

    with open(args.path, 'rb') as fh:
        pdf = pymupdf.open(stream=fh.read())
    content = extract_content(pdf)

    if args.debug:
        print(json.dumps(content, indent=2))
    else:
        output_path = args.path.replace('.pdf', '.pkpass')
        with open(output_path, 'wb') as fh:
            fh.write(dump_pkpass({
                'pass.json': json.dumps(content).encode('utf-8'),
                'icon.png': ICON,
                'logo.png': ICON,
            }))
        print(f'written to {output_path}')

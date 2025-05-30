import unittest
import datetime
from zoneinfo import ZoneInfo

import pymupdf

import db_pkpass

TZ = ZoneInfo(key='Europe/Berlin')


class ExtractLegsTests(unittest.TestCase):
    maxDiff = None

    def _test_extract_leg(self, path, expected):
        with open(path, 'rb') as fh:
            pdf = pymupdf.open(stream=fh.read())
        _header, legs = db_pkpass.extract(pdf)
        self.assertEqual(legs, expected)

    def test_normalpreis(self):
        self._test_extract_leg('muster/Muster 918-9 Normalpreis.pdf', [
            {
                'start': {
                    'station': 'Mainz Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 15, 51, tzinfo=TZ),
                    'platform': '3a/b',
                },
                'destination': {
                    'station': 'Koblenz Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 16, 54, tzinfo=TZ),
                    'platform': '1',
                },
                'train': 'RE 2 (4260)',
            },
        ])

    def test_supersparpreis(self):
        self._test_extract_leg('muster/Muster 918-9 FV_SuperSparpreis.pdf', [
            {
                'start': {
                    'station': 'Mannheim ARENA/Maimarkt',
                    'datetime': datetime.datetime(2022, 4, 22, 11, 45, tzinfo=TZ),
                    'platform': '1',
                },
                'destination': {
                    'station': 'Mannheim Hbf',
                    'datetime': datetime.datetime(2022, 4, 22, 11, 51, tzinfo=TZ),
                    'platform': '1',
                },
                'train': 'S 2',
            },
            {
                'start': {
                    'station': 'Mannheim Hbf',
                    'datetime': datetime.datetime(2022, 4, 22, 11, 59, tzinfo=TZ),
                    'platform': '5',
                },
                'destination': {
                    'station': 'Stuttgart Hbf',
                    'datetime': datetime.datetime(2022, 4, 22, 12, 38, tzinfo=TZ),
                    'platform': '5',
                },
                'train': 'ICE 573',
            },
            {
                'start': {
                    'station': 'Stuttgart Hbf',
                    'datetime': datetime.datetime(2022, 4, 22, 12, 50, tzinfo=TZ),
                    'platform': '15 B-C',
                },
                'destination': {
                    'station': 'Nürtingen',
                    'datetime': datetime.datetime(2022, 4, 22, 13, 24, tzinfo=TZ),
                    'platform': '2',
                },
                'train': 'RE 12 (19223)',
            },
            {
                'start': {
                    'station': 'Bahnhof, Nürtingen',
                    'datetime': datetime.datetime(2022, 4, 22, 13, 35, tzinfo=TZ),
                },
                'destination': {
                    'station': 'Hauptbahnhof Listplatz, Reutlingen',
                    'datetime': datetime.datetime(2022, 4, 22, 14, 16, tzinfo=TZ),
                },
                'train': 'Bus SEV',
            },
        ])

    def test_supersparpreis_young(self):
        self._test_extract_leg('muster/Muster 918-9 FV_SuperSparpreisYoung.pdf', [
            {
                'start': {
                    'station': 'Essen Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 16, 21, tzinfo=TZ),
                    'platform': '1',
                },
                'destination': {
                    'station': 'Duisburg Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 16, 34, tzinfo=TZ),
                    'platform': '3',
                },
                'train': 'RE 2 (10222)',
            },
            {
                'start': {
                    'station': 'Duisburg Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 16, 42, tzinfo=TZ),
                    'platform': '3',
                },
                'destination': {
                    'station': 'Köln Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 17, 29, tzinfo=TZ),
                    'platform': '9 D-G',
                },
                'train': 'RE 5 (28525)',
            },
            {
                'start': {
                    'station': 'Köln Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 17, 53, tzinfo=TZ),
                    'platform': '7',
                },
                'destination': {
                    'station': 'Mainz Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 19, 39, tzinfo=TZ),
                    'platform': '4a/b',
                },
                'train': 'ICE 929',
            },
            {
                'start': {
                    'station': 'Mainz Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 19, 49, tzinfo=TZ),
                    'platform': '4a',
                },
                'destination': {
                    'station': 'Darmstadt Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 20, 21, tzinfo=TZ),
                    'platform': '8',
                },
                'train': 'HLB RB75 (28731)',
            },
            {
                'start': {
                    'station': 'Darmstadt Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 20, 37, tzinfo=TZ),
                    'platform': '10',
                },
                'destination': {
                    'station': 'Stuttgart Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 21, 55, tzinfo=TZ),
                    'platform': '15',
                },
                'train': 'IC 1999',
            },
        ])

    def test_supersparpreis_2erw(self):
        self._test_extract_leg('muster/Muster 918-9 FV_SuperSparpreis_2Erw.pdf', [
            {
                'start': {
                    'station': 'Köln Hbf',
                    'datetime': datetime.datetime(2022, 10, 20, 14, 36, tzinfo=TZ),
                    'platform': '3',
                },
                'destination': {
                    'station': 'Essen Hbf',
                    'datetime': datetime.datetime(2022, 10, 20, 15, 33, tzinfo=TZ),
                    'platform': '6',
                },
                'train': 'ICE 1059',
            },
        ])

    def test_supersparpreis_3erw_rueckfahrt(self):
        self._test_extract_leg('muster/Muster 918-9 FV_SuperSparpreis_3Erw_InklR\udcfcckfahrt.pdf', [
            {
                'start': {
                    'station': 'Hamburg Hbf',
                    'datetime': datetime.datetime(2022, 11, 4, 3, 20, tzinfo=TZ),
                    'platform': '14',
                },
                'destination': {
                    'station': 'Fulda',
                    'datetime': datetime.datetime(2022, 11, 4, 6, 46, tzinfo=TZ),
                    'platform': '4',
                },
                'train': 'ICE 591',
            },
            {
                'start': {
                    'station': 'Fulda',
                    'datetime': datetime.datetime(2022, 11, 4, 6, 56, tzinfo=TZ),
                    'platform': '4',
                },
                'destination': {
                    'station': 'Nürnberg Hbf',
                    'datetime': datetime.datetime(2022, 11, 4, 9, 6, tzinfo=TZ),
                    'platform': '8',
                },
                'train': 'ICE 781',
            },
            {
                'start': {
                    'station': 'Nürnberg Hbf',
                    'datetime': datetime.datetime(2022, 11, 4, 9, 17, tzinfo=TZ),
                    'platform': '9',
                },
                'destination': {
                    'station': 'München Hbf',
                    'datetime': datetime.datetime(2022, 11, 4, 10, 20, tzinfo=TZ),
                    'platform': '19',
                },
                'train': 'ICE 1121',
            },
            {
                'start': {
                    'station': 'München Hbf Gl.5-10',
                    'datetime': datetime.datetime(2022, 11, 4, 10, 43, tzinfo=TZ),
                    'platform': '10',
                },
                'destination': {
                    'station': 'Rosenheim',
                    'datetime': datetime.datetime(2022, 11, 4, 11, 27, tzinfo=TZ),
                    'platform': '5',
                },
                'train': 'BRB RB54 (79065)',
            },
            {
                'start': {
                    'station': 'Rosenheim',
                    'datetime': datetime.datetime(2022, 11, 4, 16, 32, tzinfo=TZ),
                    'platform': '3',
                },
                'destination': {
                    'station': 'München Hbf Gl.5-10',
                    'datetime': datetime.datetime(2022, 11, 4, 17, 18, tzinfo=TZ),
                    'platform': '10',
                },
                'train': 'BRB RB54 (79082)',
            },
            {
                'start': {
                    'station': 'München Hbf',
                    'datetime': datetime.datetime(2022, 11, 4, 17, 35, tzinfo=TZ),
                    'platform': '16',
                },
                'destination': {
                    'station': 'Nürnberg Hbf',
                    'datetime': datetime.datetime(2022, 11, 4, 18, 39, tzinfo=TZ),
                    'platform': '9',
                },
                'train': 'ICE 1120',
            },
            {
                'start': {
                    'station': 'Nürnberg Hbf',
                    'datetime': datetime.datetime(2022, 11, 4, 18, 53, tzinfo=TZ),
                    'platform': '6',
                },
                'destination': {
                    'station': 'Hamburg Hbf',
                    'datetime': datetime.datetime(2022, 11, 5, 0, 5, tzinfo=TZ),
                    'platform': '13',
                },
                'train': 'ICE 782',
            },
        ])

    def test_supersparpreis_senior_rueckfahrt(self):
        self._test_extract_leg('muster/Muster 918-9 FV_SuperSparpreisSenior_InklR\udcfcckfahrt.pdf', [
            {
                'start': {
                    'station': 'Flensburg',
                    'datetime': datetime.datetime(2022, 10, 30, 15, 15, tzinfo=TZ),
                    'platform': '2',
                },
                'destination': {
                    'station': 'Hamburg Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 17, 16, tzinfo=TZ),
                    'platform': '11D-F',
                },
                'train': 'RE 7 (21077)',
            },
            {
                'start': {
                    'station': 'Hamburg Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 17, 35, tzinfo=TZ),
                    'platform': '5',
                },
                'destination': {
                    'station': 'Berlin Hbf (tief)',
                    'datetime': datetime.datetime(2022, 10, 30, 19, 22, tzinfo=TZ),
                    'platform': '1',
                },
                'train': 'ICE 803',
            },
            {
                'start': {
                    'station': 'Berlin Hbf (tief)',
                    'datetime': datetime.datetime(2022, 10, 30, 20, 5, tzinfo=TZ),
                    'platform': '1',
                },
                'destination': {
                    'station': 'München Hbf',
                    'datetime': datetime.datetime(2022, 10, 31, 0, 2, tzinfo=TZ),
                    'platform': '18',
                },
                'train': 'ICE 1109',
            },
            {
                'start': {
                    'station': 'München Hbf (tief)',
                    'datetime': datetime.datetime(2022, 10, 31, 0, 17, tzinfo=TZ),
                    'platform': '1',
                },
                'destination': {
                    'station': 'München Ost',
                    'datetime': datetime.datetime(2022, 10, 31, 0, 26, tzinfo=TZ),
                    'platform': '4',
                },
                'train': 'S 1 S 1',
            },
            {
                'start': {
                    'station': 'München Ost',
                    'datetime': datetime.datetime(2022, 10, 31, 0, 52, tzinfo=TZ),
                    'platform': '8',
                },
                'destination': {
                    'station': 'Rosenheim',
                    'datetime': datetime.datetime(2022, 10, 31, 1, 29, tzinfo=TZ),
                    'platform': '4',
                },
                'train': 'BRB RB54 (79569)',
            },
            {
                'start': {
                    'station': 'Rosenheim',
                    'datetime': datetime.datetime(2022, 11, 1, 12, 32, tzinfo=TZ),
                    'platform': '3',
                },
                'destination': {
                    'station': 'München Ost',
                    'datetime': datetime.datetime(2022, 11, 1, 13, 6, tzinfo=TZ),
                    'platform': '6',
                },
                'train': 'BRB RB54 (79074)',
            },
            {
                'start': {
                    'station': 'München Ost',
                    'datetime': datetime.datetime(2022, 11, 1, 13, 15, tzinfo=TZ),
                    'platform': '2',
                },
                'destination': {
                    'station': 'München Hbf (tief)',
                    'datetime': datetime.datetime(2022, 11, 1, 13, 23, tzinfo=TZ),
                    'platform': '2',
                },
                'train': 'S 1 S 1',
            },
            {
                'start': {
                    'station': 'München Hbf',
                    'datetime': datetime.datetime(2022, 11, 1, 13, 35, tzinfo=TZ),
                },
                'destination': {
                    'station': 'Hamburg Hbf',
                    'datetime': datetime.datetime(2022, 11, 1, 19, 53, tzinfo=TZ),
                    'platform': '12',
                },
                'train': 'ICE 786',
            },
            {
                'start': {
                    'station': 'Hamburg Hbf',
                    'datetime': datetime.datetime(2022, 11, 1, 20, 43, tzinfo=TZ),
                    'platform': '12C-F',
                },
                'destination': {
                    'station': 'Flensburg',
                    'datetime': datetime.datetime(2022, 11, 1, 22, 40, tzinfo=TZ),
                    'platform': '2',
                },
                'train': 'RE 7 (21082)',
            },
        ])

    def test_city_ticket(self):
        self._test_extract_leg('muster/Muster 918-9 CityTicket.pdf', [
            {
                'start': {
                    'station': 'Kassel-Harleshausen',
                    'datetime': datetime.datetime(2022, 4, 21, 12, 12, tzinfo=TZ),
                    'platform': '1',
                },
                'destination': {
                    'station': 'Kassel Hbf (tief)',
                    'datetime': datetime.datetime(2022, 4, 21, 12, 18, tzinfo=TZ),
                },
                'train': 'RT 1',
            },
            {
                'start': {
                    'station': 'Kassel Hbf',
                    'datetime': datetime.datetime(2022, 4, 21, 12, 23, tzinfo=TZ),
                    'platform': '7',
                },
                'destination': {
                    'datetime': datetime.datetime(2022, 4, 21, 12, 28, tzinfo=TZ),
                    'platform': '7',
                    'station': 'Kassel-Wilhelmshöhe',
                },
                'train': 'RE 30 (4159)',
            },
            {
                'start': {
                    'datetime': datetime.datetime(2022, 4, 21, 12, 37, tzinfo=TZ),
                    'platform': '2',
                    'station': 'Kassel-Wilhelmshöhe',
                },
                'destination': {
                    'datetime': datetime.datetime(2022, 4, 21, 14, 0, tzinfo=TZ),
                    'platform': '5',
                    'station': 'Frankfurt(Main)Süd',
                },
                'train': 'ICE 75',
            },
            {
                'start': {
                    'datetime': datetime.datetime(2022, 4, 21, 14, 5, tzinfo=TZ),
                    'station': 'Südbahnhof, Frankfurt a.M.',
                },
                'destination': {
                    'datetime': datetime.datetime(2022, 4, 21, 14, 7, tzinfo=TZ),
                    'station': 'Willy-Brandt-Platz, Frankfurt a.M.',
                },
                'train': 'U 1',
            },
        ])

    def test_city_ticket_international(self):
        self._test_extract_leg('muster/Muster 918-9 CityTicket_International.pdf', [
            {
                'start': {
                    'station': 'Mainz Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 16, 13, tzinfo=TZ),
                    'platform': '6a',
                },
                'destination': {
                    'station': 'Karlsruhe Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 17, 53, tzinfo=TZ),
                    'platform': '1',
                },
                'train': 'RE 4 (4481)',
            },
            {
                'start': {
                    'station': 'Karlsruhe Hbf',
                    'datetime': datetime.datetime(2022, 10, 30, 18, 0, tzinfo=TZ),
                    'platform': '2',
                },
                'destination': {
                    'station': 'Basel SBB',
                    'datetime': datetime.datetime(2022, 10, 30, 19, 47, tzinfo=TZ),
                    'platform': '4',
                },
                'train': 'ICE 373',
            },
            {
                'start': {
                    'station': 'Basel SBB',
                    'datetime': datetime.datetime(2022, 10, 30, 20, 33, tzinfo=TZ),
                    'platform': '7',
                },
                'destination': {
                    'station': 'Chur',
                    'datetime': datetime.datetime(2022, 10, 30, 22, 52, tzinfo=TZ),
                    'platform': '7',
                },
                'train': 'IC 587',
            },
        ])

    def test_laenderticket_bayern_nacht(self):
        self._test_extract_leg('muster/Muster 918-9 L\udce4nderticket Bayern Nacht.pdf', [
            {
                'start': {
                    'station': 'Augsburg Hbf',
                    'datetime': datetime.datetime(2022, 4, 25, 21, 39, tzinfo=TZ),
                    'platform': '9',
                },
                'destination': {
                    'station': 'München Hbf',
                    'datetime': datetime.datetime(2022, 4, 25, 22, 31, tzinfo=TZ),
                    'platform': '17',
                },
                'train': 'RE 9 (57167) RE 8 (57067)',
            },
            {
                'start': {
                    'station': 'München Hbf',
                    'datetime': datetime.datetime(2022, 4, 25, 23, 24, tzinfo=TZ),
                    'platform': '24',
                },
                'destination': {
                    'station': 'Plattling',
                    'datetime': datetime.datetime(2022, 4, 26, 0, 54, tzinfo=TZ),
                    'platform': '3',
                },
                'train': 'RE 3 (4092)',
            },
            {
                'start': {
                    'station': 'Plattling',
                    'datetime': datetime.datetime(2022, 4, 26, 1, 1, tzinfo=TZ),
                    'platform': '5',
                },
                'destination': {
                    'station': 'Deggendorf Hbf',
                    'datetime': datetime.datetime(2022, 4, 26, 1, 9, tzinfo=TZ),
                    'platform': '2',
                },
                'train': 'WBA RB35 (83957)',
            },
        ])

    def test_laenderticket_rheinland_pfalz(self):
        self._test_extract_leg('muster/Muster 918-9 L\udce4nderticket Rheinland-Pfalz.pdf', [
            {
                'start': {
                    'station': 'Bingen(Rhein) Hbf',
                    'datetime': datetime.datetime(2022, 4, 25, 21, 56, tzinfo=TZ),
                    'platform': '203',
                },
                'destination': {
                    'station': 'Bad Kreuznach',
                    'datetime': datetime.datetime(2022, 4, 25, 22, 16, tzinfo=TZ),
                    'platform': '1',
                },
                'train': 'RB 65 (12750)',
            },
            {
                'start': {
                    'station': 'Bad Kreuznach',
                    'datetime': datetime.datetime(2022, 4, 25, 22, 24, tzinfo=TZ),
                    'platform': '3',
                },
                'destination': {
                    'station': 'Saarbrücken Hbf',
                    'datetime': datetime.datetime(2022, 4, 26, 0, 10, tzinfo=TZ),
                    'platform': '1',
                },
                'train': 'RE 3 (29536)',
            },
        ])

    def test_laenderticket_saarland(self):
        self._test_extract_leg('muster/Muster 918-9 L\udce4nderticket Saarland.pdf', [
            {
                'start': {
                    'station': 'Saarbrücken Hbf',
                    'datetime': datetime.datetime(2022, 4, 25, 21, 51, tzinfo=TZ),
                    'platform': '1',
                },
                'destination': {
                    'station': 'Gau Algesheim',
                    'datetime': datetime.datetime(2022, 4, 25, 23, 57, tzinfo=TZ),
                    'platform': '1',
                },
                'train': 'RE 3 (29535) RB 33 (29589)',
            },
            {
                'start': {
                    'station': 'Gau Algesheim',
                    'datetime': datetime.datetime(2022, 4, 26, 0, 29, tzinfo=TZ),
                    'platform': '4',
                },
                'destination': {
                    'station': 'Bingen(Rhein) Hbf',
                    'datetime': datetime.datetime(2022, 4, 26, 0, 40, tzinfo=TZ),
                    'platform': '201',
                },
                'train': 'RB 26 (25398)',
            },
        ])

    def test_laenderticket_sachsen_anhalt(self):
        self._test_extract_leg('muster/Muster 918-9 L\udce4nderticket Sachsen-Anhalt.pdf', [
            {
                'start': {
                    'station': 'Magdeburg Hbf',
                    'datetime': datetime.datetime(2022, 4, 25, 21, 4, tzinfo=TZ),
                    'platform': '7',
                },
                'destination': {
                    'station': 'Dessau Hbf',
                    'datetime': datetime.datetime(2022, 4, 25, 21, 57, tzinfo=TZ),
                    'platform': '2',
                },
                'train': 'RE 13 (16133)',
            },
        ])

    def test_laenderticket_thueringen(self):
        self._test_extract_leg('muster/Muster 918-9 L\udce4nderticket Th\udcfcringen.pdf', [
            {
                'start': {
                    'station': 'Erfurt Hbf',
                    'datetime': datetime.datetime(2022, 10, 20, 14, 37, tzinfo=TZ),
                    'platform': '8a',
                },
                'destination': {
                    'station': 'Weimar',
                    'datetime': datetime.datetime(2022, 10, 20, 14, 50, tzinfo=TZ),
                    'platform': '2',
                },
                'train': 'RE 16 (74511)',
            },
        ])

    def test_quer_durchs_land_ticket(self):
        self._test_extract_leg('muster/Muster 918-9 Quer-durchs-Land Ticket.pdf', [
            {
                'start': {
                    'station': 'Groß Gerau-Dornberg',
                    'datetime': datetime.datetime(2022, 10, 6, 14, 36, tzinfo=TZ),
                    'platform': '3',
                },
                'destination': {
                    'station': 'Mannheim Hbf',
                    'datetime': datetime.datetime(2022, 10, 6, 15, 19, tzinfo=TZ),
                    'platform': '7a',
                },
                'train': 'RE 70 (4571)',
            },
        ])

    def test_schleswig_holstein_ticket(self):
        self._test_extract_leg('muster/Muster 918-9 Schleswig-Holstein Ticket.pdf', [
            {
                'start': {
                    'station': 'Schleswig',
                    'datetime': datetime.datetime(2022, 10, 20, 15, 7, tzinfo=TZ),
                    'platform': '3',
                },
                'destination': {
                    'station': 'Kiel Hbf',
                    'datetime': datetime.datetime(2022, 10, 20, 15, 57, tzinfo=TZ),
                    'platform': '6a',
                },
                'train': 'RE 74 (21225)',
            },
        ])

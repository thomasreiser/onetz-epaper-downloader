#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
    Onetz E-Paper Downloader
    Copyright (C) 2016,2019 Thomas Reiser

    https://github.com/thomasreiser/onetz-epaper-downloader

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''




# Imports
import requests # pip install requests
from bs4 import BeautifulSoup # pip install beautifulsoup4
from fake_useragent import UserAgent # pip install fake-useragent
from workalendar.europe import Bavaria # pip install workalendar
import time
import datetime
import random
import os
import os.path
import shutil
import json
import argparse
import sys
import platform
import logging
import re




# Interne Konstanten
VERSION = '2.0'
LOGIN_URL_PREFIX = 'https://epapersso.onetz.de/auth/authorize'
LOGIN_URL = LOGIN_URL_PREFIX + '?client_id=epaper' # Onetz Login-URL
EPAPER_CONTINOUS_URL = 'https://zeitung.onetz.de/continous.act?lastDate=%d&daysBack=%d&region=%s' # Pfad zum Abholen der verfügbaren E-Paper
EPAPER_ISSUE_URL = 'https://zeitung.onetz.de/issue.act?issueId=%s&mutationShortcut=%s&issueDate=%s&pdf=PDF' # Pfad zum Autorisieren des PDF-Downloads
DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36" # User Agent (Default-Wert)
DEFAULT_HTTP_TIMEOUT = 360 # HTTP Timeout in Sekunden (Default-Wert)
DEFAULT_MIN_SLEEP = 1 # Minimale Wartezeit/Sleep zwischen den Requests in Sekunden (Default-Wert)
DEFAULT_MAX_SLEEP = 5 # Maximale Wartezeit/Sleep zwischen den Requests in Sekunden (Default-Wert)
A_HREF_PATTERN = re.compile(r"\s*javascript:openIssue\s*\(\s*'(\w+)'\s*,\s*'(\d{8})'\s*,\s*'(\w{3})'\s*,\s*null\s*,\s*'.+'\s*,.*\)\s*;?\s*") # Regex zum Prüfen der Download-Links
A_TITLE_PATTERN = re.compile(".*Hauptausgabe.*laden.*") # Regex zum Prüfen der Download-Link-Titel




# Logger
logging.getLogger('fake_useragent').addHandler(logging.NullHandler())




# Programmlogik
def download(configFile, timestamp, overwrite):
    print('Initialisiere Logik zum Herunterladen der Gesamtausgabe...')

    # Timestamp prüfen
    if not timestamp or len(timestamp) != 8 or not timestamp.isdigit():
        print('Achtung: Übergebener Datumsparameter ist ungültig! Bitte Format YYYYMMDD verwenden!')
        return

    # Wenn der übergebene Timestamp ein Sonntag/Feiertag ist, dann den Benutzer warnen und automatisch auf den Samstag springen
    requestedDate = fixDate(timestamp, True)
    today = fixDate(time.strftime('%Y%m%d'), False)

    # Delta zwischen heute und dem angefragten Datum anfordern
    delta = (today - requestedDate).days
    if delta < 0:
        print('Achtung: Übergebener Datumsparameter ist in der Zukunft. Setze Datum auf heute...')
        delta = 0
        requestedDate = today

    requestedTimestamp = requestedDate.strftime('%Y%m%d')
    todayTimestamp = today.strftime('%Y%m%d')
    print('Zu herunterladende Gesamtausgabe: ' + requestedTimestamp)

    # Konfiguration laden
    if not os.path.isfile(configFile):
        print('Achtung: Übergebene Config-Datei existiert nicht! -> Abbruch')
        return

    config = None
    try:
        with open(configFile, 'r') as f:
            config = json.load(f)
    except:
        print('Achtung: Übergebene Config-Datei kann nicht gelesen werden! -> Abbruch')
        return

    if not config or not config['username'] or not config['password']:
        print('Es wurden keine Zugangsdaten angegeben. Bitte newpaper.json korrekt befüllen -> Abbruch')
        return

    if not config['epaper_edition']:
        print('Es wurden keine Zeitungsedition (z.B. "9wn" für Weiden; siehe README.md) angegeben. Bitte JSON Config korrekt befüllen -> Abbruch')
        return

    if not config['http_timeout']:
        config['http_timeout'] = DEFAULT_HTTP_TIMEOUT

    if not config['min_sleep'] or config['min_sleep'] < 0:
        config['min_sleep'] = DEFAULT_MIN_SLEEP

    if not config['max_sleep'] or config['max_sleep'] < 0:
        config['max_sleep'] = DEFAULT_MAX_SLEEP

    # Aktuelle, reale User-Agents von useragentstring.com laden und zufälligen UA setzen
    try:
        ua = UserAgent(cache=False)
        userAgent = ua.chrome
    except:
        userAgent = DEFAULT_USER_AGENT

    # Eigene, angepasste HTTP-Header
    headers = {'User-Agent': userAgent, 'DNT': '1'}

    # Prüfen, ob PDF-Zielverzeichnis existiert, wenn nicht versuche, es zu erstellen
    try:
        os.makedirs(config['pdf_base'])
    except OSError:
        if not os.path.isdir(config['pdf_base']):
            print('Zielverzeichnis "' + config['pdf_base'] + '" existiert nicht und kann nicht angelegt werden -> Abbruch')
            return

    # Prüfen, ob PDF schon vorhanden ist
    pdfFile = config['pdf_base'] + timestamp + '.pdf'
    if not overwrite and os.path.isfile(pdfFile):
        print('E-Paper für ' + timestamp + ' wurde bereits heruntergeladen -> Abbruch')
        return

    # Bei Onetz anmelden
    print('Melde mich an mit Benutzer ' + config['username'] + '...')
    s = requests.Session()
    r = s.post(LOGIN_URL, data={'username': config['username'], 'password': config['password']}, timeout=config['http_timeout'], headers=headers, allow_redirects=True)
    if not r.ok:
        print('Anmeldung fehlgeschlagen! -> Abbruch')
        return

    # Warten (Echten Benutzer vorgaukeln; nicht notwendig, aber sieht für den Server "besser" aus)
    print('Suche nach passendem E-Paper...')
    time.sleep(random.uniform(config['min_sleep'], config['max_sleep']))

    # Abholen des Download-Links für das PDF
    r = s.get(EPAPER_CONTINOUS_URL % (delta, 1, config['epaper_edition']), timeout=config['http_timeout'], headers=headers, allow_redirects=True)
    if not r.ok:
        print('Download-Links für E-Paper konnten nicht geladen werden! -> Abbruch')
        return

    # Jetzt muss die Rückgabe geparsed werden, da dort ein spezieller Link zum E-Paper gezogen werden muss
    soup = BeautifulSoup(r.text, 'html.parser')
    epaperLink = None
    for link in soup.find_all('a'):
        epaperLink = tryGetEPaper(str(link.get('href')), str(link.get('title')), requestedTimestamp, config['epaper_edition'])
        if epaperLink is not None:
            break
    if epaperLink is None:
        print('Link zum E-Paper nicht gefunden! -> Abbruch')
        return

    # Warten (Echten Benutzer vorgaukeln; nicht notwendig, aber sieht für den Server "besser" aus)
    print('E-Paper gefunden -> Lade Tagesausgabe herunter...')
    time.sleep(random.uniform(config['min_sleep'], config['max_sleep']))

    # Zeitung downloaden
    deletePdf = True
    try:
        with open(pdfFile, 'wb') as handle:
            r = s.get(epaperLink, timeout=config['http_timeout'], headers=headers, allow_redirects=True)
            if not r.ok:
                # TODO: 404-Check?
                print('Kann E-Paper PDF nicht herunterladen! -> Abbruch')
                deletePdf = True
            else:
                handle.write(r.content)
                deletePdf = False
    except IOError:
        print('Fehler beim Lesen/Schreiben der PDF-Datei -> Abbruch')
        deletePdf = True
    except:
        print('Fehler beim Herunterladen der PDF-Datei -> Abbruch')
        deletePdf = True

    if deletePdf:
        if os.path.isfile(pdfFile):
            os.remove(pdfFile)
    elif config['current_epaper_filename'] and requestedTimestamp == todayTimestamp:
        symLink = False
        if config['current_epaper_symlink']:
            if platform.system().lower() != 'windows':
                symLink = True
            else:
                print('Warnung: Konfigurationsvariable "current_epaper_symlink" kann auf Windows-Systemen nicht angewandt werden -> Normale Kopie wird erstellt!')
        if symLink:
            if os.path.isfile(config['pdf_base'] + config['current_epaper_filename']):
                os.remove(config['pdf_base'] + config['current_epaper_filename'])
            os.symlink(pdfFile, config['pdf_base'] + config['current_epaper_filename'])
        else:
            shutil.copy2(pdfFile, config['pdf_base'] + config['current_epaper_filename'])

    if not deletePdf:
        print('Zeitung erfolgreich heruntergeladen!')



# Methode zum prüfen, ob der übergebene Link der passende für den übergebenen Timestamp ist bzw. ob der Link überhaupt eine passende Hauptausgabe enthält
def tryGetEPaper(href, title, timestamp, edition):
    if href is None or title is None or timestamp is None:
        return None

    # Prüfen title-Tag auf Hauptausgabe
    m = A_TITLE_PATTERN.match(title)
    if m is None:
        return None

    # Prüfe href-Tag auf Download-JS
    m = A_HREF_PATTERN.match(href)
    if m is None:
        return None
    
    # Auslesen der JS-Paramter
    issueId = m.group(1)
    date = m.group(2)
    mutation = m.group(3)

    # Ungültigen Link verwerfen
    if date != timestamp or mutation.lower() != edition.lower():
        return None

    # Link zum PDF generieren
    return EPAPER_ISSUE_URL % (issueId, mutation, date)




# Methode zum Korrigieren eines Datums (Sonntag -> Samstag + Korrektur bei Feiertagen). Liefert ein datetime-Objekt zurück
def fixDate(timestamp, printWarning):
     t = datetime.datetime.strptime(timestamp, '%Y%m%d')
     holidayCalendar = Bavaria()
     if t.isoweekday() == 7 or holidayCalendar.is_holiday(t):
         if printWarning:
             print('Achtung: Der übergebene Tag ist ein Sonn- oder Feiertag! -> Lade die Zeitung für den letzen Werktag vor diesem Datum herunter')
         while t.isoweekday() == 7 or holidayCalendar.is_holiday(t):
             t = t - datetime.timedelta(days=1)
     return t




# Eigener ArgParser zum Anzeigen der Hilfe-Nachricht beim Aufruf des Scripts ohne Argumente
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)




# Konsolen Text der in der Help-Message angezeigt wird
def argDesc():
    d = []
    d.append('#####################################################################')
    d.append('## ONETZ EPAPER DOWNLOADER V' + VERSION.ljust(39, ' ') + '##')
    d.append('##                                                                 ##')
    d.append('##     https://github.com/thomasreiser/onetz-epaper-downloader     ##')
    d.append('##                                                                 ##')
    d.append('## Benutzung auf eigenes Risiko und nur für den privaten Gebrauch! ##')
    d.append('## Der Autor steht in keiner Beziehung mit Onetz bzw. dem Medien-  ##')
    d.append('## haus "Der Neue Tag" sowie anderen beteiligten Unternehmen.      ##')
    d.append('##                                                                 ##')
    d.append('## (c) 2016,2019 Thomas Reiser                                     ##')
    d.append('##               reiser.thomas@gmail.com                           ##')
    d.append('##               thomas.reiser.zone                                ##')
    d.append('##                                                                 ##')
    d.append('## Licensed under the GNU General Public License v3                ##')
    d.append('#####################################################################')
    return '\n'.join(d)


if __name__ == '__main__':
    parser = MyParser(description=argDesc(), formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-c', '--config', help='Pfad zur Config-Datei (z.B. newspaper.json)', nargs='?', default='newspaper.json', required=True)
    parser.add_argument('-d', '--date', help='Datum der zu ladenden Zeitung, z.B. 20190914 (nicht gesetzt = heute)', nargs='?', required=False)
    parser.add_argument('-o', '--overwrite', help='Falls notwendig, bestehendes PDF überschreiben', action='store_true', required=False)
    args = vars(parser.parse_args())

    download(args['config'], args['date'] or time.strftime('%Y%m%d'), args['overwrite'])

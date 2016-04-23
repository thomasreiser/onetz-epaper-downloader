#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''
    Onetz E-Paper Downloader
    Copyright (C) 2016 Thomas Reiser

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
import time
import random
import os
import os.path
import shutil
import json
import argparse
import sys
import platform




# Interne Konstanten
LOGIN_URL = 'https://service.onetz.de/register/login/' # Onetz Login-URL
EPAPER_DOMAIN = 'http://service.onetz.de' # Domain des E-Paper-Dienstes
EPAPER_LINK_START = '/epaper/validation/index.adp?tmp=' # Start des Links zum E-Paper ("Ihr E-Paper")
EPAPER_PDF_LINK_START = 'http://epaper.oberpfalznetz.de/download/?edition=%s&date=%s' # Links zum E-Paper Download der Gesamtausgabe
DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36" # User Agent (Default-Wert)
DEFAULT_HTTP_TIMEOUT = 360 # HTTP Timeout in Sekunden (Default-Wert)
DEFAULT_MIN_SLEEP = 1 # Minimale Wartezeit/Sleep zwischen den Requests in Sekunden (Default-Wert)
DEFAULT_MAX_SLEEP = 5 # Maximale Wartezeit/Sleep zwischen den Requests in Sekunden (Default-Wert)




# Programmlogik
def download(configFile, timestamp, overwrite):
    print 'Initialisiere Logik zum Herunterladen der Gesamtausgabe für ' + timestamp + '...'

    # Konfiguration laden
    if not os.path.isfile(configFile):
        print 'Achtung: Übergebene Config-Datei existiert nicht! -> Abbruch'
        return

    try:
        with open(configFile, 'r') as f:
            config = json.load(f)
    except:
        print 'Achtung: Übergebene Config-Datei kann nicht gelesen werden! -> Abbruch'
        return

    if not config or not config['username'] or not config['password']:
        print 'Es wurden keine Zugangsdaten angegeben. Bitte newpaper.json korrekt befüllen -> Abbruch'
        return

    if not config['epaper_edition']:
        print 'Es wurden keine Zeitungsedition (z.B. "WN" für Weiden) angegeben. Bitte newpaper.json korrekt befüllen -> Abbruch'
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

    # Prüfen, ob PDF schon vorhanden ist
    pdfFile = config['pdf_base'] + timestamp + '.pdf'
    if not overwrite and os.path.isfile(pdfFile):
        print 'E-Paper für ' + timestamp + ' wurde bereits heruntergeladen -> Abbruch'
        return

    # Bei ONetz anmelden
    s = requests.Session()
    r = s.post(LOGIN_URL, data={'lg': config['username'], 'pw': config['password']}, timeout=config['http_timeout'], headers=headers, allow_redirects=True)
    if not r.ok:
        print 'Anmeldung fehlgeschlagen! -> Abbruch'
        return

    # Jetzt muss die Rückgabe geparsed werden, da dort ein spezieller Link zum E-Paper gezogen werden muss
    soup = BeautifulSoup(r.text, 'html.parser')
    newspaperLink = ''
    for link in soup.find_all('a'):
        href = str(link.get('href'))
        if href.startswith(EPAPER_LINK_START):
            newspaperLink = href
            break
    if not newspaperLink:
        if soup.findAll('div', { 'class' : 'warn' }):
            print 'Anmeldung fehlgeschlagen! -> Abbruch'
        else:
            print 'Link zum E-Paper nicht gefunden! -> Abbruch'
        return

    # Warten (Echten Benutzer vorgaukeln; nicht notwendig, aber sieht für den Server "besser" aus)
    print 'Anmeldung erfolgreich. Warte...'
    time.sleep(random.uniform(config['min_sleep'], config['max_sleep']))

    # Link zum E-Paper aufrufen
    r = s.get(EPAPER_DOMAIN + newspaperLink, timeout=config['http_timeout'], headers=headers, allow_redirects=True)
    if not r.ok:
        print 'Aufruf der E-Paper-Seite fehlgeschlagen! -> Abbruch'
        return

    # Warten (Echten Benutzer vorgaukeln; nicht notwendig, aber sieht für den Server "besser" aus)
    print 'E-Paper Portal aufgerufen. Warte...'
    time.sleep(random.uniform(config['min_sleep'], config['max_sleep']))

    # Zeitung downloaden
    deletePdf = True
    #try:
    with open(pdfFile, 'wb') as handle:
        r = s.get(EPAPER_PDF_LINK_START % (config['epaper_edition'], timestamp), stream=True, timeout=config['http_timeout'], headers=headers)
        if not r.ok:
            # TODO: 404-Check?
            print 'Kann E-Paper PDF nicht heruntenladen! -> Abbruch'
            deletePdf = True
        else:
            contentLength = int(r.headers['content-length'])
            print 'Lade Tagesausgabe herunter...'
            written = 0
            for block in r.iter_content(1024):
                written += len(block)
                handle.write(block)
                printProgress(written, contentLength)
            deletePdf = False
    #except:
    #    deletePdf = True

    if deletePdf:
        if os.path.isfile(pdfFile):
            os.remove(pdfFile)
    elif config['current_epaper_filename'] and timestamp == time.strftime('%Y%m%d'):
        symLink = False
        if config['current_epaper_symlink']:
            if platform.system().lower() != 'windows':
                symLink = True
            else:
                print 'Warnung: Konfigurationsvariable "current_epaper_symlink" kann auf Windows-Systemen nicht angewandt werden -> Normale Kopie wird erstellt!'
        if symLink:
            if os.path.isfile(config['pdf_base'] + config['current_epaper_filename']):
                os.remove(config['pdf_base'] + config['current_epaper_filename'])
            os.symlink(pdfFile, config['pdf_base'] + config['current_epaper_filename'])
        else:
            shutil.copy2(pdfFile, config['pdf_base'] + config['current_epaper_filename'])

    if not deletePdf:
        print 'Zeitung erfolgreich heruntergeladen!'




# Helper zum Anzeigen des Download-Fortschritts
def printProgress(progress, total):
    filledLength = int(round(30 * progress / float(total)))
    percents = round(100.0 * (progress / float(total)), 2)
    bar = '#' * filledLength + '-' * (30 - filledLength)
    sys.stdout.write('Status [%s] %s%s abgeschlossen\r' % (bar, percents, '%')),
    sys.stdout.flush()
    if progress >= total:
        print('\n')




# Eigener ArgParser zum Anzeigen der Hilfe-Nachricht beim Aufruf des Scripts ohne Argumente
class MyParser(argparse.ArgumentParser):
    def error(self, message):
        sys.stderr.write('error: %s\n' % message)
        self.print_help()
        sys.exit(2)




def argDesc():
    d = []
    d.append('#####################################################################')
    d.append('## ONETZ EPAPER DOWNLOADER V1.0                                    ##')
    d.append('##                                                                 ##')
    d.append('##     https://github.com/thomasreiser/onetz-epaper-downloader     ##')
    d.append('##                                                                 ##')
    d.append('## Benutzung auf eigenes Risiko und nur für den privaten Gebrauch! ##')
    d.append('## Der Autor steht in keiner Beziehung mit Onetz bzw. dem Medien-  ##')
    d.append('## haus "Der Neue Tag" sowie anderen beteiligten Unternehmen.      ##')
    d.append('##                                                                 ##')
    d.append('## (c) 2016 Thomas Reiser                                          ##')
    d.append('##          reiser.thomas@gmail.com                                ##')
    d.append('##          thomas.reiser.zone                                     ##')
    d.append('##                                                                 ##')
    d.append('## Licensed under the GNU General Public License v3                ##')
    d.append('#####################################################################')
    return '\n'.join(d)


if __name__ == '__main__':
    parser = MyParser(description=argDesc(), formatter_class=argparse.RawTextHelpFormatter)
    parser.add_argument('-c', '--config', help='Pfad zur Config-Datei (z.B. newspaper.json)', nargs='?', default='newspaper.json', required=True)
    parser.add_argument('-d', '--date', help='Datum der zu ladenden Zeitung (nicht gesetzt = heute)', nargs='?', required=False)
    parser.add_argument('-o', '--overwrite', help='Falls notwendig, bestehendes PDF überschreiben', action='store_true', required=False)
    args = vars(parser.parse_args())

    timestamp = time.strftime('%Y%m%d')
    if args['date']:
        if len(args['date']) == 8 and args['date'].isdigit():
            timestamp = args['date']
        else:
            print 'Achtung: Übergebener Datumsparameter ist ungültig! Bitte Format YYYYMMDD verwenden!'
            sys.exit(2)

    download(args['config'], timestamp, args['overwrite'])

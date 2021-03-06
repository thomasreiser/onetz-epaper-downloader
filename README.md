# onetz-epaper-downloader
Ein einfaches Python-Script zum Herunterladen der aktuellen Tagesausgabe des Medienhauses "Der Neue Tag".

## Installation
#### Installation notwendiger 3rd-Party Libraries
```
sudo pip install requests beautifulsoup4 fake-useragent workalendar
```

## Aufruf des Scripts
#### Notwendige Parameter
Setzen der JSON-Konfigurationsdatei:
```
-c [Pfad zur JSON-Config], --config [Pfad zur JSON-Config]
```

#### Optionale Parameter
Anzeigen der Hilfe:
```
-h, --help
```
Setzen des Erscheinungsdatums der zu ladenen Zeitung (Format: YYYYMMDD, nicht gesetzt = heute):
```
-d [Datum], --date [Datum]
```
Überschreiben der Zeitungs-PDF, falls die Ausgabe bereits heruntergeladen wurde:
```
-o, --overwrite
```

#### Beispielaufruf des Scripts
```
./newspaper.py -c /home/thomas/newspaper.json -d 20160309 -o
```
Erklärung:
In diesem Fall lädt das Script die Gesamtausgabe vom 09.03.2016 herunter und überschreibt die bestehende PDF, falls diese schon existiert. Es wird die Konfiguration /home/thomas/newspaper.json gelesen.

## JSON Konfigurationsdatei
#### Notwendige Einstellungen
```
username
```
Benutzername / E-Mail-Adresse des Onetz-Accounts
```
password
```
Password des Onetz-Accounts
```
epaper_edition
```
E-Paper Edition die geladen werden soll. Mögliche Werte:
* 1sr (Sulzbach Rosenberger Zeitung)
* 2az (Amberger Zeitung)
* 3st (Tirschenreuth)
* 4eb (Eschenbach)
* 5ek (Erbendorf Kemnath)
* 6sn (Schwandorf Nabburg)
* 7so (Schwandorf Grenzwarte)
* 8vo (Vohenstrauß)
* 9wn (Weiden)
```
pdf_base
```
Verzeichnis, in das die E-Paper PDF-Dateien geschrieben werden sollen

#### Optionale Einstellungen
```
http_timeout
```
Timeout für HTTP-Requests in Sekunden. Wenn nicht gesetzt, wird ein Default von 360 Sekunden verwendet
```
min_sleep
```
Minimale Sleep/Wartezeit zwischen den einzelnen HTTP-Requests (wird verwendet um den Server nicht zu sehr zu belasten). Wenn nicht gesetzt, wird ein Default von 1 Sekunde verwendet
```
max_sleep
```
Maximale Sleep/Wartezeit zwischen den einzelnen HTTP-Requests (wird verwendet um den Server nicht zu sehr zu belasten). Wenn nicht gesetzt, wird ein Default von 5 Sekunden verwendet
```
current_epaper_filename
```
Dateiname für die aktuelle Tagesausgabe. Ist z.B. "current.pdf" hinterlegt, so kann die aktuelle Zeitung immer über current.pdf im *pdf_base* gefunden werden. Wenn nicht gesetzt, so wird keine solche Datei/Verknüpfung angelegt
```
current_epaper_symlink
```
Ist ein Wert bei *current_epaper_filename* hinterlegt und *current_epaper_symlink* auf **true**, so wird ein Symlink anstatt einer echten Kopie der aktuellen Ausgabe angelegt. Achtung: Funktioniert nicht bei Windows-Systemen!

## Offene Punkte / TODO's
- Unterstützung für HTTP/SOCKS-Proxies
- Implementierung einer Logik zur automatisierten Generierung der JSON-Config

## Changelog

#### 12.09.2020
- Dockerfile zum Ausführen des Scripts in einem Container
- Kleine Codeoptimierungen

#### 01.02.2020
- Kompatibilität zu Redesign des Onetz E-Paper-Bereichs

#### 20.09.2019
- Unterstützung für neues Server-Backend (SSO etc.) von Onetz
- Aktualisierung aller möglichen Codes für Zeitungseditionen

#### 17.02.2016
- Anpassung der Onetz Server-URLs
- Unterstützung von Python 3

#### 15.05.2016
- Automatische Erkennung von Feiertagen

#### 24.04.2016
- Initiale Version

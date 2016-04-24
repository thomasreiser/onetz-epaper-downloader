# onetz-epaper-downloader
Ein einfaches Python-Script zum Heruntenladen der aktuellen Tagesausgabe des Medienhauses "Der Neue Tag".

###### Aufruf des Scripts
**Notwendige Parameter**
Setzen der JSON-Konfigurationsdatei:
```
-c [Pfad zur JSON-Config], --config [Pfad zur JSON-Config]
```

**Optionale Parameter**
Anzeigen der Hilfe:
```
-h, --help
```
Setzen des Erscheinungsdatums der zu ladenen Zeitung (Format: YYYMMDD, nicht gesetzt = heute):
```
-d [Datum], --date [Datum]
```
Überschreiben der Zeitungs-PDF, falls die Ausgabe bereits heruntergeladen wurde:
```
-o, --overwrite
```

**Beispielaufruf des Scripts**
```
./newspaper.py -c /home/thomas/newspaper.json -d 20160903 -o
```
Erklärung:
In diesem Fall lädt das Script die Gesamtausgabe vom 09.03.2016 herunter und überschreibt die bestehende PDF, falls diese schon existiert. Es wird die Konfiguration /home/thomas/newspaper.json gelesen.

###### JSON Konfigurationsdatei
**Notwendige Einstellungen**
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
E-Paper Edition (WN = Weiden, andere Editionen lassen sich aus dem Link "Gesamtausgabe herunterladen" ziehen. Falls jemand hierzu andere Editionscodes hat (z.B. für Tirschenreuth, Amberg, ..), würde es mich freuen, wenn Ihr Sie mir zukommen lassen würdet. Danke!)
```
pdf_base
```
Verzeichnis, in das die E-Paper PDF-Dateien geschrieben werden sollen

**Optionale Einstellungen**
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

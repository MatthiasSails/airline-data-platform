# DB API Marketplace – Setup & Authentifizierung

Quelle: https://developers.deutschebahn.com/db-api-marketplace/apis/start

---

## Schritt 1: Registrierung ✅

- DB Kundenkonto erstellen (einmalig)
- E-Mail-Verifizierung abschließen
- Zustimmung zur Datenweitergabe (Name, E-Mail, Anrede)

---

## Schritt 2: Anwendung erstellen

### Was ist eine "Anwendung"?

Eine **Anwendung** ist ein technischer Client – vergleichbar mit einem "Projekt" oder "App-Eintrag" im Portal. Sie braucht man, damit das System weiß, *wer* die API aufruft. Jede Anwendung bekommt eigene Zugangsdaten.

**Analogie:** Wie ein Benutzername/Passwort-Paar, aber für ein Programm statt für einen Menschen.

### Anwendung anlegen

1. Im Portal einloggen
2. "Anwendung erstellen" wählen
3. **Titel** vergeben (z.B. `airline-project`)
4. Beschreibung optional
5. OAuth-Umleitungs-URL kann leer bleiben

### Die zwei Zugangsdaten

| Feld | Name | Bedeutung |
|------|------|-----------|
| `DB-Client-Id` | Client ID | Identifiziert die Anwendung (nicht geheim) |
| `DB-Api-Key` | Client Secret / API Key | Passwort der Anwendung – **geheim halten!** |

> **WICHTIG:** Das Client Secret wird **nur einmalig** beim Erstellen angezeigt.
> Sofort kopieren und sicher ablegen (z.B. `.env`-Datei, Passwortmanager).
> Danach ist es nicht mehr einsehbar – nur ein Reset ist möglich.

---

## Schritt 3: API abonnieren

- Im Katalog ein **Produkt** wählen (z.B. Fahrplan, Timetables, StaDa)
- Einen **Plan** abonnieren (Free / kostenpflichtig)
- Abo ist an die erstellte Anwendung gebunden

---

## Schritt 4: API aufrufen

### Header-Parameter

Alle API-Anfragen benötigen diese zwei Header:

```
DB-Client-Id: <deine-client-id>
DB-Api-Key:   <dein-api-key>
```

### Beispiel mit curl

```bash
curl -X GET "https://apis.deutschebahn.com/db-api-marketplace/apis/<endpoint>" \
  -H "DB-Client-Id: DEINE_CLIENT_ID" \
  -H "DB-Api-Key: DEIN_API_KEY"
```

### Beispiel mit Python (requests)

```python
import requests

headers = {
    "DB-Client-Id": "DEINE_CLIENT_ID",
    "DB-Api-Key":   "DEIN_API_KEY",
}

response = requests.get(
    "https://apis.deutschebahn.com/db-api-marketplace/apis/<endpoint>",
    headers=headers,
)
print(response.json())
```

### Beispiel mit Postman

1. Neue Request anlegen
2. Tab "Headers" öffnen
3. `DB-Client-Id` und `DB-Api-Key` eintragen
4. Request abschicken

---

## Zugangsdaten sicher ablegen (.env)

```env
# .env  –  NICHT ins Git einchecken!
DB_CLIENT_ID=xxxxxxxxxxxxxxxxxxxx
DB_API_KEY=xxxxxxxxxxxxxxxxxxxx
```

```python
from dotenv import load_dotenv
import os

load_dotenv()
client_id = os.getenv("DB_CLIENT_ID")
api_key   = os.getenv("DB_API_KEY")
```

Sicherstellen, dass `.env` in der `.gitignore` steht:

```
.env
```

---

## Organisationen (optional)

- Bei Registrierung wird automatisch eine **Konsumentenorganisation** angelegt
- Weitere Organisationen möglich (z.B. für Team-Zugang)
- Mitglieder können eingeladen werden

---

## Links

- Portal: https://developers.deutschebahn.com/db-api-marketplace/apis/start
- API-Katalog: https://developers.deutschebahn.com/db-api-marketplace/apis/product/list

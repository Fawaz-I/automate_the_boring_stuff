# Automate The Boring Stuff Offline Bundle

Offline reading + practice workspace for:

- Automate the Boring Stuff with Python (3rd ed): `https://automatetheboringstuff.com/`
- Automate the Boring Stuff Workbook: `https://inventwithpython.com/automate3workbook/`

## What's in this repo

- `offline_content/` - offline mirrored pages and assets
- `offline_content/index.html` - interleaved reading order (book chapter, then workbook chapter)
- `offline_content/refresh.py` - rebuild/update offline bundle
- `exercises/` - per-chapter practice folders
- `build_offline_bundle.py` - builder script used to generate the bundle

## Usage

Open `offline_content/index.html` in your browser.

To refresh/update the offline bundle:

```bash
python3 offline_content/refresh.py
```

## Licensing Note

The book content is authored by Al Sweigart and provided online under Creative Commons terms.
Before publishing this repo publicly, review and comply with the source license requirements
(attribution, non-commercial restrictions, and share-alike, where applicable).

# Automate The Boring Stuff Offline Bundle

Offline reading + practice workspace for:

- Automate the Boring Stuff with Python (3rd ed): `https://automatetheboringstuff.com/`
- Automate the Boring Stuff Workbook: `https://inventwithpython.com/automate3workbook/`

## What's in this repo

- `build_offline_bundle.py` - builder script that downloads and generates local offline content
- `setup_offline.sh` - one-command bootstrap to generate local offline content
- `BEGIN_HERE.command` - double-click launcher for macOS users
- `BEGIN_HERE.bat` - double-click launcher for Windows users
- `exercises/` - per-chapter practice folders

Generated locally (not committed):

- `offline_content/` - mirrored pages and assets
- `offline_content/index.html` - interleaved reading order (book chapter, then workbook chapter)

## Usage

### Prerequisite

- Python 3 must be installed.

Quick check:

```bash
python3 --version
```

Beginner no-terminal option:

- macOS: double-click `BEGIN_HERE.command`
- Windows: double-click `BEGIN_HERE.bat`

This generates `offline_content/` and opens `offline_content/index.html` automatically.

If macOS blocks the script on first run, right-click `BEGIN_HERE.command` and choose **Open**.

If Python is missing, install it from `https://www.python.org/downloads/` and run again.

Terminal option:

Generate the local offline bundle:

```bash
./setup_offline.sh
```

Or run the builder directly:

```bash
python3 build_offline_bundle.py
```

Then open `offline_content/index.html` in your browser.

## Licensing Note

- `LICENSE` (MIT) covers original repository code/scripts.
- Mirrored book/workbook content remains third-party content and follows its original Creative Commons terms.
- See `THIRD_PARTY_LICENSES.md` for attribution and licensing details.

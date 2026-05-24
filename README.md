# Name Tag Generator

Fill a printable name tag PDF template from a CSV. Each page holds 8 tags (2 columns × 4 rows).

## Quick start

```bash
./setup.sh   # once: venv, deps, example CSV + placeholder template
./run.sh     # writes nametags_filled.pdf
```

Defaults live in [`config.py`](config.py). Edit paths there, or override on the CLI:

```bash
python generate_nametags.py --csv attendees.csv --template my_template.pdf --out output.pdf
```

## CSV format

```csv
first_name,last_name,type,school
Jane,Doe,Guest,Example Org
```

Column names are case-insensitive.

## Templates

Sample layouts are in [`example_template/`](example_template/). Copy one to `nametag_template.pdf` (or point `config.TEMPLATE` at your own file).

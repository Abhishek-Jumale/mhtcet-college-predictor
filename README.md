# MHT-CET College Predictor

Predicts the engineering colleges and branches an MHT-CET candidate can realistically expect a seat in,
based on official **CAP Round 1** cutoff data for **2022, 2023, and 2024**.

Given a student's percentile, social category, gender, home-university status, and optional branch/region
filters, the tool returns reachable college-branch options bucketed into **Safe / Target / Reach**, ranked
by competitiveness. Cutoffs are projected to the next year using each option's year-over-year trend.

## What's inside

| Path | Description |
|------|-------------|
| `mhtcet_college_predictor.ipynb` | Main notebook: data loading, EDA, trend projection, predictor, and an ML model |
| `data/mhtcet_20XX_cap1_cutoffs.csv` | Cleaned cutoff datasets (one row per college-branch-seat-category) |
| `scripts/parse_cutoff_pdf.py` | Parser that converts the official CAP cutoff PDFs into the CSV format |

## Dataset columns

`college_code, college_name, branch_code, branch_name, seat_type, category, closing_merit_no, closing_percentile`

Category codes encode three things: gender (**G** = General/gender-neutral, **L** = Ladies), social
category (OPEN, SC, ST, OBC, EWS, VJ, NT1/2/3, SEBC…), and seat scope (**S** = State, **H** = Home
university, **O** = Other-than-home). Example: `GOPENH` = General-Open, Home-university seat.

## Quick start

```bash
pip install -r requirements.txt
jupyter notebook mhtcet_college_predictor.ipynb
```

Then run all cells and edit the profile cell:

```python
predict_colleges(
    percentile=99.0,
    social='OPEN',          # OPEN, SC, ST, OBC, EWS, VJ, NT1, NT2, NT3, SEBC
    gender='male',          # 'male' or 'female'
    home_university=True,
    branch=['Information Technology', 'Computer Engineering'],   # str or list, optional
    region='Pune',          # Pune, Mumbai, Nagpur, Nashik, Amravati, Chhatrapati Sambhajinagar
).head(15)
```

## Regenerating the data from PDFs

`scripts/parse_cutoff_pdf.py` reads each official PDF using word coordinates (`pdftotext -bbox` from
poppler-utils) so columns align correctly even when categories have blank cells.

```bash
sudo apt install poppler-utils      # or: brew install poppler
python scripts/parse_cutoff_pdf.py  # edit the file paths inside to point at your PDFs
```

## Notes & limitations

- Eligibility logic is simplified (no minority / PWD / Defence / TFW sub-quotas).
- Based on CAP Round 1 only; later rounds shift seats, so treat "Reach" options generously.
- `region` is the **college's location**, which is separate from **home-university** seat eligibility.
- The next-year projection is based on three years of history and is indicative, not guaranteed.

This is an educational project and is not an official source of admission information.

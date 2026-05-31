import subprocess, re, csv, sys, html as _html, os

SEAT_TYPES = {
    "State Level",
    "Home University Seats Allotted to Home University Candidates",
    "Home University Seats Allotted to Other Than Home University Candidates",
    "Other Than Home University Seats Allotted to Home University Candidates",
    "Other Than Home University Seats Allotted to Other Than Home University Candidates",
}
WORD_RE = re.compile(
    r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">(.*?)</word>')
PAGE_RE = re.compile(r'<page ')
ROMAN = {'I','II','III','IV','V'}

def extract_words(pdf_path):
    """Return list of (page, xmin, ymin, xmax, text) using pdftotext -bbox."""
    out = subprocess.run(['pdftotext', '-bbox', pdf_path, '-'],
                         capture_output=True, text=True).stdout
    words, page = [], -1
    for line in out.split('\n'):
        if '<page ' in line:
            page += 1
        for m in WORD_RE.finditer(line):
            x0, y0, x1, y1, t = m.groups()
            t = _html.unescape(t).strip()
            if t:
                words.append((page, float(x0), float(y0), float(x1), t))
    return words

def group_rows(words):
    """Group words into visual rows. pdftotext -bbox does NOT emit words in reading
    order, so sort by (page, yMin, xMin) first, then cluster by yMin proximity."""
    words = sorted(words, key=lambda w: (w[0], round(w[2], 1), w[1]))  # page, y, x
    rows = []
    cur, cur_page, cur_y = [], None, None
    for page, x0, y0, x1, t in words:
        if cur and (page != cur_page or abs(y0 - cur_y) > 3):
            rows.append(sorted(cur, key=lambda w: w[0]))
            cur = []
        if not cur:
            cur_page, cur_y = page, y0
        cur.append((x0, (x0 + x1) / 2, t))
    if cur:
        rows.append(sorted(cur, key=lambda w: w[0]))
    return rows

def row_text(row):
    return ' '.join(w[2] for w in row).strip()

def nearest_col(centers, c):
    return min(range(len(centers)), key=lambda k: abs(centers[k] - c))

def parse_pdf(pdf_path):
    rows = group_rows(extract_words(pdf_path))
    out = []
    cc = cn = bc = bn = st = None
    n = len(rows)
    i = 0
    while i < n:
        row = rows[i]
        txt = row_text(row)

        mb = re.match(r'^(\d{9,10})\s*-\s*(.+)$', txt)
        mc = re.match(r'^(\d{4,5})\s*-\s*(.+)$', txt)
        if mb:
            bc, bn = mb.group(1).zfill(10), mb.group(2).strip(); i += 1; continue
        if mc:
            cc, cn = mc.group(1).zfill(5), mc.group(2).strip(); i += 1; continue
        if txt in SEAT_TYPES:
            st = txt; i += 1; continue

        if row and row[0][2] == 'Stage' and len(row) > 1:
            # category columns = words after 'Stage'
            cats = [(w[2], w[1]) for w in row[1:]]            # (label, center)
            labels = [c[0] for c in cats]
            centers = [c[1] for c in cats]

            j = i + 1
            # merge wrapped header fragments (short alpha tokens on following rows)
            while j < n:
                r = rows[j]
                first = r[0][2] if r else ''
                is_data = first in ROMAN and any(re.fullmatch(r'\d+', w[2]) for w in r[1:])
                if is_data:
                    break
                if r and all(re.fullmatch(r'[A-Za-z]{1,3}', w[2]) for w in r):
                    for _, c, t in r:
                        k = nearest_col(centers, c)
                        labels[k] += t
                    j += 1; continue
                break

            if j >= n:
                i += 1; continue
            data_row = rows[j]
            val_items = [(w[1], w[2]) for w in data_row[1:]      # skip stage numeral
                         if re.fullmatch(r'\d+', w[2])]
            # percentile row = next row containing parenthesised floats
            k = j + 1
            pct_items = []
            while k < min(j + 4, n):
                pr = rows[k]
                floats = [(w[1], re.sub(r'[()]', '', w[2])) for w in pr
                          if re.fullmatch(r'\(?[\d.]+\)?', w[2]) and '.' in w[2]]
                if floats:
                    pct_items = floats; break
                k += 1

            vmap, pmap = {}, {}
            for c, t in val_items:
                vmap[nearest_col(centers, c)] = t
            for c, t in pct_items:
                pmap[nearest_col(centers, c)] = t

            for idx, lab in enumerate(labels):
                out.append([cc, cn, bc, bn, st, lab,
                            vmap.get(idx, ''), pmap.get(idx, '')])
            i = k + 1 if pct_items else j + 1
            continue
        i += 1
    return out

def write_csv(rows, path):
    with open(path, 'w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['college_code','college_name','branch_code','branch_name',
                    'seat_type','category','closing_merit_no','closing_percentile'])
        w.writerows(rows)

if __name__ == '__main__':
    jobs = [
        ('/mnt/user-data/uploads/2022ENGG_CAP1_CutOff.pdf', 'mhtcet_2022_cap1_cutoffs.csv'),
        ('/mnt/user-data/uploads/2023ENGG_CAP1_CutOff.pdf', 'mhtcet_2023_cap1_cutoffs.csv'),
        ('/mnt/user-data/uploads/2024ENGG_CAP1_CutOff.pdf', 'mhtcet_2024_cap1_cutoffs.csv'),
    ]
    for pdf, name in jobs:
        rows = parse_pdf(pdf)
        out_path = os.path.join('/mnt/user-data/outputs', name)
        write_csv(rows, out_path)
        filled = sum(1 for r in rows if r[6] and r[7])
        cats = set(r[5] for r in rows)
        bad = [c for c in cats if not re.fullmatch(r'[A-Z0-9]+', c)]
        print(f"{name}: rows={len(rows)} | both merit+pct={100*filled/len(rows):.1f}% | "
              f"colleges={len(set(r[0] for r in rows))} | cats={len(cats)} | malformed_labels={len(bad)}")

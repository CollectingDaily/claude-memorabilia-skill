#!/usr/bin/env python3
"""Build the research document for an article from the checked log and the notes.

    python3 build_research.py "<folder>"            # check, then write the research document
    python3 build_research.py "<folder>" --check    # check only; write nothing
    python3 build_research.py "<folder>" --items    # the log, one line per item
    python3 build_research.py --probe URL [URL ...]  # will the checker open these pages?
    python3 build_research.py "<folder>" --fewer-houses   # build although fewer than three houses
                                                          # could be checked; the document says so

<folder> is the run's working folder. It holds:

    sources-log.md   every verified item, in the format verify_sources.py reads
    rejected.md      candidates dropped, one per line: name, URL, the reason
    notes.md         the research notes, written by Claude (format below)

The document is written beside them as "<title> research.md", and as a .docx
too when pandoc is installed. Every item of sources-log.md is copied into it in
full, never retyped; the notes say which section each item serves.

Before it writes anything it checks the log against the pages: priced items
through verify_sources.py (every page fetched again, every price and quote
found on it, no duplicates, at least three houses), facts with no price and
prices written in words by finding their quote on the page. A log that has
passed is remembered by its fingerprint, so a rebuild with an unchanged log
does not fetch everything again.

notes.md, one paragraph or bullet per line (a table row is a line):

    # <title of the article this is research for>
    Type: Top 10 | Beginners guide | Dealer guide
    Field: <field>. Source files read: <files>

    ## <section of the article, in article order>
    Items: 1, 3-5          (optional; the items printed under this section)
    - <a fact, each figure naming its item on the same line: (Item 3)>

    ## Conflicts            (required: every sale two items disagree on, or "None found.")
    ## Gaps                 (required: what the article needs and the research did not find)

It refuses to write the document, printing one FAIL line each, when the notes
name an item the log does not hold; carry a price or percentage that is not in
the Price or Quote of an item named on the same line, in the same currency;
carry a count of a hundred or more, other than a year, that no named item holds;
carry a URL that is in no item and not in rejected.md, or one of our own sites;
lack the Conflicts or Gaps section, or a section the article type needs; or when
an item cites one of our own sites or a Paul Fraser Collectibles blog post, or
fewer than three different houses carry the prices (unless --fewer-houses). A line starting "Rate:" is fx rate
furniture and is not checked. Nothing in the notes is converted or computed.
"""
import collections, datetime, hashlib, pathlib, re, shutil, subprocess, sys

HERE = pathlib.Path(__file__).resolve().parent
ITEM = re.compile(r"^\*\*Item\s+(\d+)\s*:\s*(.+?)\*\*\s*$", re.M)
FIELD = re.compile(r"^\s*[-*•]\s*([A-Za-z][A-Za-z ]*?)\s*:\s*(.*?)\s*$")
OURS = ('justcollecting.com', 'collectingdaily.com', 'paulfrasercollectibles.com/blogs')
CUR = r'(US\$|HK\$|A\$|C\$|S\$|NZ\$|\$|£|€|¥|CHF|USD|GBP|EUR|HKD|JPY|AUD|CAD)'
MONEY = re.compile(CUR + r'\s?(\d[\d,]*(?:\.\d+)?)(?:\s?(million|billion|thousand|mn|bn|m|k)\b)?', re.I)
PCT = re.compile(r'(?<![\d.,])(\d+(?:\.\d+)?)\s?(%|per\s?cent\b|percent\b)', re.I)
COUNT = re.compile(r'(?<![\w$£€¥.,#/-])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?\s?(?:million|billion)\b|\d{3,})(?![\w%.,]*\d)', re.I)
REF = re.compile(r'\bItems?\s+(\d+(?:\s*(?:,|and|&|to|–|-)\s*\d+)*)', re.I)
URL = re.compile(r'https?://[^\s<>|`"\])]+')
TRIM = '.,;:!?'
GATE_MONEY = re.compile(r"(?:US\$|\$|£|GBP|USD|EUR|€|HK\$)\s?([\d][\d,\.]{2,})")
WORDS_MONEY = re.compile(r"((?:US\$|\$|£|€)\s?\d{1,3}(?:\.\d+)?)\s?(million|billion)\b", re.I)
PRICELESS = ('', 'not stated', 'none', 'n/a')
MULT = {'million': 1e6, 'mn': 1e6, 'm': 1e6, 'billion': 1e9, 'bn': 1e9, 'thousand': 1e3, 'k': 1e3}


def cur(sym):
    s = sym.upper()
    return {'US$': '$', 'USD': '$', '$': '$', '£': '£', 'GBP': '£', '€': '€', 'EUR': '€', '¥': '¥', 'JPY': '¥',
            'HKD': 'HK$', 'AUD': 'A$', 'CAD': 'C$'}.get(s, s)


def num(text, unit=''):
    return float(text.replace(',', '')) * MULT.get((unit or '').lower(), 1)


def monies(text):
    return {(cur(m.group(1)), round(num(m.group(2), m.group(3)), 4)) for m in MONEY.finditer(text)}


def pcts(text):
    return {round(float(m.group(1)), 4) for m in PCT.finditer(text)}


def numbers(text):
    """Every number a text holds, commas removed: lenient, for counts and lot numbers."""
    return {round(float(x), 4) for x in re.findall(r'\d+(?:\.\d+)?', re.sub(r'(?<=\d),(?=\d{3})', '', text))}


def item_list(text):
    out = set()
    for a, b in re.findall(r'(\d+)\s*(?:[-–]\s*(\d+))?', text):
        out.update(range(int(a), int(b or a) + 1))
    return out


def refs(text):
    out = set()
    for m in REF.finditer(text):
        out |= item_list(re.sub(r'\b(and|to)\b|&', ',', m.group(1)))
    return out


def parse_log(path):
    raw = path.read_text(encoding='utf-8', errors='replace')
    marks = list(ITEM.finditer(raw))
    items = collections.OrderedDict()
    for i, m in enumerate(marks):
        end = marks[i + 1].start() if i + 1 < len(marks) else len(raw)
        fields = {}
        for line in raw[m.end():end].splitlines():
            fm = FIELD.match(line)
            if fm:
                fields.setdefault(fm.group(1).strip().lower(), fm.group(2))
        items[int(m.group(1))] = {'name': m.group(2).strip(), 'f': fields}
        items[int(m.group(1))]['block'] = raw[m.start():end].strip()
    return items, raw[:marks[0].start()] if marks else raw


def quote_on(page, quote):
    """The check_log rule: the quote's first 60 characters on the page, or its digits."""
    q = re.sub(r"\s+", " ", re.sub(r"\[.*?\]", " ", quote.strip().strip('"\''))).strip()[:60]
    norm = lambda t: re.sub(r"[,\s  ]", "", t)
    return bool(q) and (q.lower() in page.lower() or norm(q) in norm(page))


def parse_notes(path):
    pre, secs, head = [], collections.OrderedDict(), None
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith('## '):
            head = line[3:].strip()
            secs[head] = []
        elif head is None:
            pre.append(line)
        else:
            secs[head].append(line)
    return pre, secs


def spaced(lines):
    """One paragraph per line: a blank line between paragraphs, none inside a table or a list."""
    out, prev = [], ''
    for l in lines:
        if not l.strip():
            continue
        kind = '|' if l.lstrip().startswith('|') else '-' if re.match(r'\s*([-*]|\d+\.) ', l) else 'p'
        if out and not (kind == prev and kind in '|-'):
            out.append('')
        out.append(l)
        prev = kind
    return out


def verified(folder, log, items, min_sources=3):
    """Check the log against the pages, unless this exact log has already passed.

    Priced items go through verify_sources.py, which fetches each page again, finds the price and the quote,
    catches duplicates and needs at least three houses. A fact with no price, and a price written in words
    ("$6 million"), which verify_sources.py cannot read, have their quote (and phrase) found on the page here,
    with verify_sources.py's own fetcher, as the market research log check does."""
    digest = hashlib.sha256(log.read_bytes()).hexdigest()
    mark = folder / '.verified'
    if mark.exists() and mark.read_text().strip() == digest:
        print('verify    the log has not changed since it was last checked against the pages')
        return True
    priced, words, facts = [], [], []
    for n, it in items.items():
        p = it['f'].get('price', '').strip()
        (facts if p.lower() in PRICELESS else priced if GATE_MONEY.search(p) or not WORDS_MONEY.search(p)
         else words).append(n)
    ok = True
    if priced:
        print(f'verify    {len(priced)} priced item(s) through verify_sources.py (it fetches every page again)...')
        tmp = folder / '.priced-log.md'
        tmp.write_text('\n\n'.join(items[n]['block'] for n in priced) + '\n', encoding='utf-8')
        r = subprocess.run([sys.executable, str(HERE / 'verify_sources.py'), '--log', str(tmp),
                            '--min-sources', str(min_sources)],
                           capture_output=True, text=True)
        tmp.unlink()
        print('\n'.join('          ' + l for l in (r.stdout + r.stderr).strip().splitlines()[-14:]))
        ok = r.returncode == 0
    else:
        print('verify    no priced items, so the three-house check does not apply')
    if words or facts:
        sys.path.insert(0, str(HERE))
        from verify_sources import fetch_text
        print(f'verify    {len(facts)} fact(s) and {len(words)} price(s) in words, quotes found on their pages...')
        pages = {}
        for n in words + facts:
            it = items[n]
            url, quote = it['f'].get('url', '').strip(), it['f'].get('quote', '')
            if url not in pages:
                pages[url] = fetch_text(url)
            page, err = pages[url]
            tag = f'          {n:02d}  {it["name"][:46]}'
            if page is None:
                print(f'{tag}  DEAD/BLOCKED {str(err)[:60]}: find it on a page that opens, or move it to Gaps')
                ok = False
                continue
            if n in words:
                m = WORDS_MONEY.search(it['f'].get('price', ''))
                if re.sub(r'\s+', '', (m.group(1) + m.group(2)).lower()) not in re.sub(r'\s+', '', page.lower()):
                    print(f'{tag}  NOT ON PAGE {m.group(0)!r}')
                    ok = False
            if not quote_on(page, quote):
                print(f'{tag}  QUOTE NOT ON PAGE {quote[:50]!r}')
                ok = False
    if ok:
        mark.write_text(digest)
    return ok


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    if sys.argv[1] == '--probe':                     # the checker's own fetcher, before a page is relied on
        sys.path.insert(0, str(HERE))
        from verify_sources import fetch_text
        for url in sys.argv[2:]:
            page, err = fetch_text(url)
            if page and len(page.strip()) >= 400:
                print(f'OPENS    {url}  ({len(page)} characters)')
            elif page is not None:
                print(f'EMPTY    {url}  ({len(page.strip())} characters): a page built by JavaScript; the checker sees '
                      f'nothing on it, so it cannot go in the log')
            else:
                print(f'BLOCKED  {url}  ({str(err)[:70]}): the checker cannot read it, so it cannot go in the log')
        return
    flags = {a for a in sys.argv[1:] if a.startswith('--')}
    paths = [a for a in sys.argv[1:] if not a.startswith('--')]
    if len(paths) != 1:
        sys.exit('give one working folder, in quotes, and any options before or after it')
    fewer = '--fewer-houses' in flags
    folder = pathlib.Path(paths[0]).expanduser().resolve()
    log, notes, rej = folder / 'sources-log.md', folder / 'notes.md', folder / 'rejected.md'
    if not log.exists():
        sys.exit(f'no {log}')
    items, log_head = parse_log(log)
    if '--items' in flags:
        for i, it in items.items():
            g = it['f'].get
            print(f'{i} | {it["name"][:70]} | {g("price", "")} | {g("basis", "")[:30]} | {g("house", "")} | '
                  f'{g("date", "")} | {g("url", "")[:70]}')
        return
    if not notes.exists():
        sys.exit(f'no {notes}: write the notes first (format in this script\'s docstring)')
    pre, secs = parse_notes(notes)
    title = next((l[2:].strip() for l in pre if l.startswith('# ')), '')
    fails, warns = [], []
    if not title:
        fails.append('FAIL notes.md has no "# <title>" first line')
    kind = next((l.split(':', 1)[1].strip().lower() for l in pre if l.lower().startswith('type:')), '')
    needs = ['Conflicts', 'Gaps'] + (['Background', 'Genuine versus copies', 'The market today', 'The candidates']
                                     if 'top' in kind else ['Background'] if 'guide' in kind and 'dealer' not in kind
                                     else ['The market'] if 'dealer' in kind else [])
    if not kind:
        fails.append('FAIL notes.md has no "Type:" line (Top 10, Beginners guide or Dealer guide)')
    for need in needs:
        if need not in secs:
            fails.append(f'FAIL notes.md has no "## {need}" section, which a {kind or "this"} article needs')
        elif not any(l.strip() and not l.startswith('Items:') for l in secs[need]):
            fails.append(f'FAIL "## {need}" is empty: write what was found, or say in one line why there is nothing')
    for i, it in items.items():
        u = it['f'].get('url', '')
        if any(d in u for d in OURS):
            fails.append(f'FAIL Item {i} cites {u}: our own sites and Paul Fraser Collectibles blog posts are never '
                         'sources. Find the house\'s own page, or move it to rejected.md')
    rejected = [l.strip().lstrip('-* ').strip() for l in rej.read_text(encoding='utf-8').splitlines()
                if l.strip() and not l.lstrip().startswith('#')] if rej.exists() else []
    known = set()
    for it in items.values():
        known |= {u.rstrip(TRIM) for u in URL.findall(' '.join(it['f'].values()))}
    known |= {u.rstrip(TRIM) for l in rejected for u in URL.findall(l)}

    listed = collections.OrderedDict()
    for h, lines in secs.items():
        for line in lines:
            if not line.strip():
                continue
            named = refs(line) | (item_list(line[6:]) if line.startswith('Items:') else set())
            for i in sorted(named - set(items)):
                fails.append(f'FAIL "## {h}": Item {i} is not in sources-log.md')
            if line.startswith('Items:'):
                for i in sorted(item_list(line[6:]) & set(items)):
                    listed.setdefault(i, []).append(h)
                continue
            for u in URL.findall(line):
                u = u.rstrip(TRIM)
                if any(d in u for d in OURS):
                    fails.append(f'FAIL "## {h}": {u} is one of our own sites, never cited')
                elif u not in known:
                    fails.append(f'FAIL "## {h}": {u} is in no logged item and not in rejected.md')
            if line.startswith('Rate:'):
                continue
            text = re.sub(r'(?i)\b(?:HTTP|error|status)(?: code)?\s*\d{3}\b', ' ', REF.sub(' ', URL.sub(' ', line)))
            cited = [items[i] for i in named if i in items]
            pool = ' '.join(it['f'].get('price', '') + ' ' + it['f'].get('quote', '') for it in cited)
            allf = ' '.join(it['name'] + ' ' + ' '.join(it['f'].values()) for it in cited)
            got_m, got_p, got_c = monies(pool), pcts(pool), numbers(allf)
            where = f'Item {", ".join(map(str, sorted(named)))}' if named else ''
            for m in MONEY.finditer(text):
                if (cur(m.group(1)), round(num(m.group(2), m.group(3)), 4)) not in got_m:
                    fails.append(f'FAIL "## {h}": "{m.group(0).strip()}" ' + (
                        f'is not in the Price or Quote of {where}, in that currency' if named else 'names no item on its line'))
            for m in PCT.finditer(text):
                if round(float(m.group(1)), 4) not in got_p:
                    fails.append(f'FAIL "## {h}": "{m.group(0).strip()}" ' + (
                        f'is not in the Price or Quote of {where}' if named else 'names no item on its line'))
            for m in COUNT.finditer(PCT.sub(' ', MONEY.sub(' ', text))):
                t = m.group(1)
                if re.fullmatch(r'1[0-9]\d\d|20\d\d|21\d\d', t):
                    continue                                    # a year
                w = re.match(r'([\d.]+)\s?(million|billion)', t, re.I)
                v = round(num(w.group(1), w.group(2)), 4) if w else round(num(t), 4)
                if v >= 100 and v not in got_c:
                    fails.append(f'FAIL "## {h}": the count "{t}" ' + (
                        f'is in no field of {where}' if named else 'names no item on its line'))
    for i, it in items.items():
        if i not in listed:
            warns.append(f'WARN Item {i} ({it["name"][:60]}) is in no section\'s Items line: printed under "Other evidence"')

    for f in fails + warns:
        print(f)
    if fails:
        print(f'FAILED: {len(fails)} failure(s); nothing written. Fix the notes, or the log from the pages; never a script.')
        sys.exit(1)
    priced_houses = sorted({it['f'].get('house', '').strip() for it in items.values()
                            if it['f'].get('price', '').strip().lower() not in PRICELESS
                            and it['f'].get('house', '').strip().lower() not in ('', 'not stated')})
    if len(priced_houses) < 3 and not fewer:
        print(f'FAILED: the prices come from {len(priced_houses)} house(s) ({", ".join(priced_houses) or "none named"}); '
              f'at least three are needed. Work through the rest of the field\'s list and the majors. Only when every '
              f'house on them has been tried, build with --fewer-houses, and tell the user.')
        sys.exit(1)
    if not verified(folder, log, items, 1 if fewer else 3):
        print('FAILED: verify_sources.py did not pass. Fix the log from the pages, or drop the item into rejected.md.')
        sys.exit(1)
    if '--check' in flags:
        print(f'PASS (check only): {len(items)} items, {len(warns)} warning(s)')
        return

    # ---- the document --------------------------------------------------------------------------------------
    def block(i):
        it, g = items[i], items[i]['f'].get
        out = [f'**Item {i}: {it["name"]}**', '']
        price = (g('price') or '').strip()
        if price and price.lower() not in ('not stated', 'none', 'n/a'):
            out.append(f'- **{price}**' + (f', {g("basis")}' if g('basis') else ', basis not recorded')
                       + (f' ({g("unit")})' if g('unit') else ''))
        place = ', '.join(v for v in (g('house'), g('date')) if v and v.lower() != 'not stated')
        if place:
            out.append(f'- {place}')
        for k in ('copy', 'note'):
            if g(k):
                out.append(f'- {k.capitalize()}: {g(k)}')
        if g('quote'):
            out += ['', f'> {g("quote").strip(chr(34))}']
        out += ['', f'Check it: <{g("url")}>', '']
        return out

    houses = sorted({re.sub(r'^www\.', '', u.split('/')[2]) for it in items.values()
                     for u in URL.findall(it['f'].get('url', ''))})
    meta = [l.strip() for l in pre if l.strip() and not l.startswith('# ')]
    out = [f'# {title}: research', '',
           f'Research for an article, gathered and checked {datetime.date.today().isoformat()}. '
           f'{len(items)} items, each read on the page it links to and checked again by the source checker; '
           f'{len(rejected)} candidates rejected, listed at the end with the reason. Every price is as its page '
           f'states it: nothing is converted or rounded. The article is yours to write.', '']
    out += meta + [''] if meta else []
    out += [f'**Prices from:** {", ".join(priced_houses) or "no priced items"}. **Pages used:** {", ".join(houses)}', '']
    if len(priced_houses) < 3:
        out += [f'> **Fewer than three auction houses.** Only {len(priced_houses)} could be checked, so this is not yet '
                f'a survey of the market: a ranking drawn from it shows what these houses sold, not the highest prices '
                f'in the field. Gaps lists the houses that could not be read.', '']
    printed = set()
    for h, lines in secs.items():
        if h in ('Conflicts', 'Gaps'):
            continue
        out += [f'## {h}', ''] + spaced([l for l in lines if not l.startswith('Items:')]) + ['']
        nums = [i for i in sorted(item_list(next((l[6:] for l in lines if l.startswith('Items:')), ''))) if i in items]
        if nums:
            out += [f'### Evidence ({len(nums)})', '']
            for i in nums:
                if i in printed:
                    out.append(f'- Item {i}: {items[i]["name"]} (in full under {listed[i][0]})')
                else:
                    out += block(i)
                    printed.add(i)
            out.append('')
    for h in ('Conflicts', 'Gaps'):
        out += [f'## {h}', ''] + spaced(secs.get(h, [])) + ['']
    out += ['## Rejected candidates', '']
    out += [f'- {l}' for l in rejected] or ['None.']
    other = [i for i in items if i not in listed]
    if other:
        out += ['', '## Other evidence', '']
        for i in other:
            out += block(i)
    md = folder / (re.sub(r'[\\/:*?"<>|]+', '', title).strip() + ' research.md')
    md.write_text(re.sub(r'\n{3,}', '\n\n', '\n'.join(out)).rstrip() + '\n', encoding='utf-8')
    docx = ''
    if shutil.which('pandoc'):
        ref = HERE.parent / 'assets' / 'research-reference.docx'
        r = subprocess.run(['pandoc', str(md), '-f', 'markdown-tex_math_dollars-raw_tex', '-o', str(md.with_suffix('.docx'))]
                           + ([f'--reference-doc={ref}'] if ref.exists() else []), capture_output=True, text=True)
        docx = f' and {md.with_suffix(".docx").name}' if r.returncode == 0 else f' (no .docx: {r.stderr.strip()[:160]})'
    print(f'PASS: {len(items)} items ({len(other)} under Other evidence), {len(rejected)} rejected, '
          f'{len(houses)} sources, {len(warns)} warning(s) -> {md}{docx}')


if __name__ == '__main__':
    main()

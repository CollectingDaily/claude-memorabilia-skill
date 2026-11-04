---
name: memorabilia-research
description: "Research an article about collectibles and hand the writer a checked research document, so they write the article themselves: art, coins, comics, music and entertainment memorabilia, stamps, trading cards, wine and spirits, toys, autographs and historical documents, political, sports and royal memorabilia, space and aviation, photography and rare books. Three article types: Top 10 artefacts, beginners' guide, and dealer/where-to-buy guide. Every price, date and claim is read on the page it links to and checked again before the document is built. Never writes the article and never finds images. Use when asked to research an article, or for the background, facts or sources for one."
---

# Memorabilia research: the research behind an article, for the writer

You research one article about collectibles and deliver a research document: everything the article needs, organised the way the article will be, every fact with the link to check it. **A person writes the article. You never do.**

## What this skill never does

- **Never write the article**, or any part of it: no intro, no paragraphs for the reader, no headline, no excerpt, no meta description, no suggested wording. Your notes are facts and where they come from, in plain bullet points.
- **Never find, download or suggest images.** The writer chooses the pictures.
- **Never offer to write it afterwards.** The research document is the deliverable.

## Why this skill is strict about sourcing

The failure that destroys these articles is a fabricated auction record or a dead link. A plausible lot with an invented price is worse than no lot at all: the writer publishes under an auction house's name, and readers click the links. So:

**A URL you have not opened and read in this session does not exist.** You may not cite it, quote a price from it, or list it.

Open the page and read it: the item description, the price, the sale date and the provenance. If the page does not state something, it does not go in. Never fill a gap with a "typical" or remembered price. If you cannot verify enough, deliver what you verified and say plainly what fell short: that is a successful outcome.

A search result is a summary written by a model, not the page: use it only to find the URL, then read the page. Our own sites (collectingdaily.com, justcollecting.com, news.justcollecting.com) are not sources: research from the houses and publishers themselves.

**A price comes from a party to the sale**: anything the selling house publishes itself (its lot page, results page, press release, or an article on its own site), or the page of a dealer on the allowlist that bought or sold the lot itself. The House line is always the house that held the sale; say in the Note whose page it is. A news or blog page reporting someone else's sale is press, background only. That includes Paul Fraser Collectibles' blog, which the build refuses as a source. Where the house shows the price only to signed-in visitors (Sotheby's lot pages say "Log in to view results"), look for the house's own press release or results page, or a party's page, before giving up on the figure.

**The checker reads pages its own way, and some houses refuse it even when you can read the page** (RR Auction does; Julien's and Heritage often do). Test a page before you rely on it:

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/build_research.py" --probe "<url>" "<url>" ...
```

Put every URL in double quotes: a `?` in an unquoted URL stops the command. A page that comes back BLOCKED, or EMPTY (built by JavaScript, so the checker sees nothing on it), cannot go in the log. The access notes in the source files can be out of date: the probe decides. Find the same figure on another allowed page, or put the page in `rejected.md` ("would not open for the checker") and name it under Gaps, so the writer can check it in their own browser.

## The three article types

**Type 1: Top 10 artefacts.** Ten notable items with verified prices and auction records. Example: "Ozzy Osbourne memorabilia: 10 great artefacts from the Prince of Darkness".

**Type 2: Beginners' guide.** An in-depth guide with sections, advice and historical context, about education rather than specific lots. Example: "A beginners' guide to coin collecting".

**Type 3: Where to buy / dealer guide.** A guide to the top dealers, auction houses or specialists. Example: "The world's top 10 coin dealers: where to buy?".

Choosing the type:
- Type 1 only when the request asks for a list, a ranking or a "top X".
- Type 2 for educational, explanatory or "how to" articles.
- Type 3 for "where to buy" or directory-style articles.
- Never force a Type 1 list on a request for a guide. If the request could be either, ask in one line.

## Where the files go

`<root>` is the folder the session is working in. Create the working folder first, its name starting with today's date so runs sort by date (run `date +%Y.%m.%d` once and reuse that literal string):

```
<root>/Article research/<YYYY.MM.DD> — <topic-slug>/
    sources-log.md                  every verified item (Phase 2)
    rejected.md                     every candidate dropped, with the reason
    notes.md                        your notes, organised like the article (Phase 3)
    <title> research.md             the deliverable, built by build_research.py
    <title> research.docx           the same, for Word and Google Docs (when pandoc is installed)
```

The folder name contains spaces: quote the path in every command.

## Approved sources: read them before you search

**Before a single search, identify the subject field and read its source file in full**, including the verification notes at its foot. It is an allowlist: a house or dealer not on it may not be cited for a price.

| Subject field | Read |
|---|---|
| Art: paintings, prints, sculpture, works on paper | `references/sources-art.md` |
| Coins, gold, silver, bullion | `references/sources-coins.md` |
| Comics and original comic art | `references/sources-comics.md` |
| Music, entertainment, film, general memorabilia | `references/sources-music-memorabilia.md` |
| Stamps and postal history | `references/sources-stamps.md` |
| Trading cards, sports cards, TCGs | `references/sources-trading-cards.md` |
| Wine, whisky, cognac, spirits | `references/sources-wine-spirits.md` |
| Toys: action figures, diecast, tinplate, trains, bears, dolls | `references/sources-toys.md` |
| Autographs and historical documents | `references/sources-autographs.md` |
| Political memorabilia | `references/sources-political.md` (plus `sources-autographs.md` for signed material) |
| Sports memorabilia | `references/sources-sports.md` (plus `sources-trading-cards.md` for cards) |
| Royal memorabilia | `references/sources-royal.md` (plus `sources-autographs.md` for signed material) |
| Space and aviation | `references/sources-space-aviation.md` (plus `sources-autographs.md` for signed material) |
| Photography, photobooks, cameras | `references/sources-photography.md` (plus `sources-art.md` for fine art photography) |
| Rare books, first editions, maps | `references/sources-books.md` (plus `sources-autographs.md` for signed copies) |
| **Every field**: the major houses | `references/sources-major-houses.md` |
| **Every field**: press and context | `references/sources-press.md` |

Every run reads **three** files: the field's own, `sources-major-houses.md` and `sources-press.md`. The press may support context, provenance and narrative but never carries a price on its own. Some field files also have a **context tier** (museums, institutional scholarship, trade magazines): research it freely for history, technique and background, but it never supplies a price.

**The allowlist is a list to work through, not to pick one from.** A topic spanning two fields reads both files and uses the union. A topic that fits no file: say so and stop. Never improvise a source list.

## Phase 1: research

Run several WebSearch queries combining the subject with auction terms, using `site:` filters against the allowlist you read.

**Search at least four different houses, and never stop at the first one that yields enough results.** A house the checker cannot open counts as tried: list it under Gaps. One house's archive will happily fill a whole top ten, and the research then reads as that house's catalogue rather than a survey of the market. Work through the field file house by house, then the majors.

Probe each candidate page as you find it (above), so the research is built on pages the checker can read.

- **Type 1:** aim for 15 to 18 candidate items (about a third fail verification). Prefer variety across kinds of object: instruments, worn clothing, signed records, documents, jewellery, ephemera. Also gather the background the introduction will need: the subject's story and legacy, how mass merchandise differs from authentic material, and the state of the market.
- **Type 2:** gather authoritative information from the approved sources and reputable institutions (the Royal Mint for coins, the British Museum and the like): history, technical detail, collecting advice, practical guidance. Cover the topic thoroughly, section by section.
- **Type 3:** identify 10 to 12 dealer candidates from the approved sources. For each: history, location and specialisms; notable sales with verified prices; reputation and clients; website and contact details.

## Phase 2: verification

For each candidate, open the actual lot, result or dealer page, read it, and record it in `sources-log.md` in exactly this format (`verify_sources.py` parses it):

```
**Item 1: Romanée-Conti 1945 (1 bottle, 750ml)**
- URL: https://example.com/lot/123
- Status: VERIFIED
- Price: $812,500
- Basis: total including buyer's premium, stated on the page
- Unit: 1 bottle (750ml)
- House: Sotheby's
- Date: 27 March 2026
- Quote: "sold for $812,500"
- Note: anything the writer needs to know about this item
```

- **Quote** is text copied from the page, never a paraphrase. Keep the page's own punctuation.
- **Price** is exactly as the page states it, in its own currency. **Never convert, round or compute**: the writer does that. A fact with no price (a date, a definition, a dealer's founding year) is logged the same way with `Price: not stated`, and its Quote must be on the page.
- **Basis**: whether the price is the hammer price or the total with buyer's premium, as the page says, or `not stated by the source`. The two are never compared.
- **A sale and an estimate are different things.** A verified result and an estimate never share a ranking; say which each is.
- **Unit** is required whenever items are ranked by price: it is what tells a single bottle from a case.
- **House** and **Date** are figures too: only what the page states. If the page gives no sale date, log `Date: not stated`; if it shows its own publication date, you may add it: `Date: not stated (page published 13 May 2018)`.
- **One object sold twice is two items**, one per sale, named alike with the year: "One-cent magenta (2014 sale)", "One-cent magenta (2021 sale)". **One sale reported on two pages is one item**: put the second URL in its Note.
- **Name each item by the object first**: "Gold-leaf piano (Elvis Presley)", not "Elvis Presley gold-leaf piano". The checker flags items whose names start alike as possible duplicates.
- Prices only from houses and dealers on the allowlist. The press supports context, never a price on its own.
- **At least three different houses must carry the verified prices.** Where one house still carries more than about 60% of the items, widen the search.
- A candidate that fails (the page does not state the price, it will not open, it is a duplicate, it is off the allowlist) goes to `rejected.md`, one line each: the name, the URL and the reason. Only verified items stay in `sources-log.md`.
- Two sources disagree on a figure: log both items. The notes list both under Conflicts; decide nothing.

State at the top of `sources-log.md` which source files you read.

**PASS with a quote worth an eye** means the price is on the page but the quote's wording has moved: copy it again from the page.

**A ONE-HOUSE failure is not a paperwork problem**: it means the research stopped at the first archive with enough lots. Go back to Phase 1. **A NOT ON PAGE failure** means the figure is not on the page you cited: re-source it from a page that states it in text, or move the item to `rejected.md`. **A DUPLICATE** is one object logged twice: it is one entry. **MIXED UNITS** is a notice, not a failure: check that the ranked items are comparable (a single bottle against a case is not).

**Fewer than three houses.** If, after trying every house on the field's list and the majors, fewer than three can be checked, the build stops. Only then build with `--fewer-houses`: the document then says at the top which houses it rests on, and that it is not yet a survey of the market. Tell the user.

## Phase 3: the notes

Write `notes.md`, organised the way the article will be, in plain factual bullet points. You are telling the writer what the research found and where, never how to word it. Its format:

```
# <working title of the article>
Type: Top 10 | Beginners guide | Dealer guide
Field: <field>. Source files read: <the three files>

## <section of the article>
Items: 1, 3-5
- <a fact, with the item it comes from: (Item 3)>
```

- **Every figure names its item on the same line**, written "Item 3", in tables too: the Item column holds "Item 3", never a bare 3. Copy the figure exactly as the item's Price or Quote states it. A fact from a context page is logged as an item too (`Price: not stated`), so it can be named.
- **Every link in the notes is in the log or in `rejected.md`**, with a space after it: never a colon or a bracket against it.
- One bullet per fact, one paragraph or table row per line: the build checks a line at a time.
- `Items:` lists the items whose full evidence is printed under that section.

What the notes cover, by type:

- **Type 1:** `## Background` (the subject's story and legacy, for the introduction), `## Genuine versus copies` (what separates the real thing from merchandise, reprints, replicas and fakes; the field's context tier, such as expertising bodies, societies and museums, is where this comes from), `## The market today`, then `## The candidates` with a ranking table of **every** verified candidate, not only ten (Rank | Item | Name | Price as stated | Basis | House | Date). Rank items that share one basis. Items on another basis, and items whose basis is not stated, each form their own group, ranked among themselves and labelled, never ranked against the first. Rank only the kind of object the title names: a related object (a cover in a list of stamps, a poster in a list of props) goes in a separate list saying what it is. Where currencies differ, the ranking may be worked out at the day's rate, pasted on a line starting `Rate:`, but only the prices as stated are printed. The writer chooses the ten.
- **Type 2:** `## Background` (the topic, its historical roots, why it matters), then one section per part of the guide the topic needs, each with its facts and items.
- **Type 3:** `## The market`, then one section per dealer: history, location, specialisms, reputation, website and contact details, and two or three example sales with their items.
- **Background facts** come from the press and context tiers of the source files (museums, institutions, the serious press): log each as an item. The build refuses an empty required section: write what was found, or one line saying why there is nothing.
- **Every type:** `## Conflicts` (every sale two items disagree on, both figures, both items, or "None found.") and `## Gaps` (what the article needs that the research could not find or check, with any page the writer could check by hand).

## Phase 4: build and check

```bash
python3 "${CLAUDE_SKILL_DIR}/scripts/build_research.py" "<the working folder>"
```

(`python` on Windows.) It first runs `verify_sources.py` on the log: every page is fetched again, every price and quote must be found on it, the same object may not appear twice, and at least three houses must carry the prices. Then it checks the notes: every item named exists, every price and percentage is in the item named on its line, in the same currency, and every link is in the log. It refuses to build while anything fails. Fix the log from the pages, or the notes, and run it again. Never edit the script to get past it.

Options can come before or after the folder. `build_research.py "<folder>" --items` prints the log one line per item, which is how to look at it without reading it whole. `--probe <url> ...` tests pages, and `--fewer-houses` builds with fewer than three houses (Phase 2 says when).

## Phase 5: deliver

Give the user, in plain words:
- where the research document is (the `.md`, and the `.docx` for Word and Google Docs);
- how many items were verified, from how many houses, and how many were rejected;
- the conflicts and the gaps, so they know what to check before writing;
- anything you could not open.

Then stop. The article is theirs to write.

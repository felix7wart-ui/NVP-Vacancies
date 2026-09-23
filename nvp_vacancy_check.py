"""
NVP member vacancy checker.
Visits each NVP member website, looks for a careers/vacancies page,
and reports whether that page mentions openings.

Run:  pip install requests beautifulsoup4
      python nvp_vacancy_check.py
Output: nvp_vacancies.csv  (one row per member, with links to check by hand)
        feed.xml           (RSS feed of firms with likely openings, for Meltwater)
"""
import csv, re, time
from urllib.parse import urljoin, urlparse
import requests
from bs4 import BeautifulSoup

MEMBERS = [['365 Capital', 'https://365capital.com/'], ['3i Benelux', 'http://www.3i.com'], ['4impact capital', 'https://www.4impact.vc/'], ['5square', 'http://www.5square.nl'], ['819 Capital Partners', 'https://www.819-capital.com'], ['AAC Capital Partners Holding', 'http://www.aaccapital.com'], ['Abenex', 'https://www.abenex.com/'], ['ABN AMRO Corporate Investments', 'https://www.abnamro.nl/en/commercialbanking/corporates-institutionals/products/expand-your-business/private-equity.html'], ['Active Capital Company', 'https://www.activecapitalcompany.com/'], ['Advent International plc', 'https://www.adventinternational.com/'], ['Alder Tree Investments', 'https://www.aldertreecharity.nl'], ['AlpInvest Partners', 'https://www.alpinvest.com/'], ['Antea Participaties', 'http://www.antea.nl'], ['Anterra Capital', 'https://anterracapital.com/'], ['Argos Wityu', 'https://argos.wityu.fund/'], ['Avedon Capital Partners', 'http://www.avedoncapital.com'], ['AVerest Capital', 'https://www.averest.nl/'], ['AXECO Participaties', 'https://www.axeco.nl/participaties/'], ['BB Capital Investments', 'http://www.bbcapital.nl'], ['Beek Capital', 'https://www.beekcapital.nl/en/'], ['Bencis Capital Partners', 'http://www.bencis.nl'], ['Berk Partners', 'http://www.berkpartners.nl'], ['BioGeneration Ventures', 'http://www.biogenerationventures.com'], ['Bolster Investment Partners', 'http://www.bolsterinvestments.nl/'], ['Brabantse Ontwikkelings Maatschappij', 'http://www.bom.nl'], ['Bridgepoint Netherlands', 'http://www.bridgepoint.eu'], ['Brightlands Venture Partners', 'https://brightlandsventurepartners.com/'], ['Cape Investment Partners', 'https://www.capeinvestments.nl/'], ['Capital A', 'https://www.capitalapartners.nl/'], ['Capricorn Partners NV', 'https://www.capricorn.be/en'], ['Carlyle Group', 'https://www.carlyle.com/'], ['Chrysalix Venture Capital', 'http://www.chrysalix.com/'], ['Cinven Partners', 'https://www.cinven.com/'], ['Committed Capital Management', 'https://committedcapital.nl/'], ['Convent Capital', 'https://conventcapital.nl/en/'], ['Cottonwood Technology Fund', 'https://www.cottonwood.vc'], ['Craft Capital B.V.', 'https://www.craftcapital.nl'], ['Curie Capital', 'https://www.curiecapital.nl/'], ['CVC Advisers', 'https://www.cvc.com/'], ['CVC DIF', 'https://www.dif.eu/'], ['Damen Maritime Ventures Participations', 'https://www.damen.com'], ['DeepTechXL Fund Management', 'https://www.deeptechxl.com/'], ['Dei Capital Management', 'https://www.dei-capital.com/'], ['DELTA Equity Partners', 'https://delta-equitypartners.com/'], ['DFF Ventures', 'https://www.dff.ventures/'], ['Dolfin', 'http://www.dolfincapital.com/'], ['Écart Invest', 'http://www.ecart.nl'], ['ECFG Venture Capital', 'https://ecfg.nl/en/venture-capital/'], ['Egeria Capital Management', 'http://www.egeria.nl'], ['EQT Life Sciences', 'https://eqtgroup.com/private-capital/eqt-life-sciences'], ['EQT Partners Netherlands', 'https://eqtgroup.com/private-capital/private-equity/'], ['Esses Capital Partners', 'https://www.essescapitalpartners.com/'], ['Fairtree Elevant Management B.V.', 'https://www.fairtree.com/elevantventures/'], ['Forbion', 'http://www.forbion.com'], ['Freshstream Netherlands', 'https://freshstream.com/'], ['Gilde Equity Management', 'http://www.gembenelux.com'], ['Gilde Healthcare Partners', 'http://www.gildehealthcare.com'], ['Gimv Nederland Holding', 'http://www.gimv.nl'], ['Graduate Ventures Pre-Seed', 'https://www.graduate.nl/'], ['Health Investment Partners', 'http://healthinvestmentpartners.nl/'], ['Holland Capital Management', 'https://hollandcapital.nl/'], ['Horizon Flevoland', 'https://www.horizonflevoland.nl/ik-zoek-geld'], ['Horticoop', 'https://www.horticoop.nl/'], ['HPE Growth', 'http://www.hpegrowthcapital.com'], ['IBS Fund Management', 'https://ibsca.nl/'], ['IceLake Capital', 'https://www.icelakecapital.com/'], ['ICOS Capital Management', 'http://www.icoscapital.com'], ['Imec.istart', 'https://www.imecistart.com/'], ['imecXpand', 'https://imecxpand.com/'], ['Impuls Zeeland', 'https://www.impulszeeland.nl/nl/het-Zeeuws-Participatiefonds'], ['Indofin Group', 'https://www.indofin.com/'], ['Infinity Recycling', 'http://www.infinity-recycling.com/'], ['Inflexion', 'https://www.inflexion.com/'], ['ING Corporate Investments B.V.', 'https://www.ingwb.com/en/strategic-finance/corporate-investments'], ['Innovatiefonds Noord-Holland', 'https://www.innovatiefondsnoordholland.nl'], ['Innovation Industries', 'http://www.innovationindustries.com'], ['InnovationQuarter', 'https://www.innovationquarter.nl/'], ['Intersaction', 'http://www.intersaction.com/'], ['Invest NL', 'https://www.invest-nl.nl/'], ['Karmijn Kapitaal', 'http://www.karmijnkapitaal.nl'], ['Knop Investments B.V.', 'https://www.knopinvestments.com'], ['Kohlberg Kravis Roberts & Co Partners', 'https://www.kkr.com/'], ['Levine Leichtman Capital Partners', 'http://www.llcp.com'], ['Lexar Partners', 'https://lexarpartners.com/'], ['LIOF', 'http://www.liof.nl'], ['LUMO Labs', 'https://lumolabs.io/'], ['Main Capital Partners', 'http://www.main.nl'], ['Marktlink Capital', 'https://www.marktlinkcapital.com/nl/'], ['Mentha Capital', 'https://mentha.eu/'], ['MGF', 'https://www.mgf.nl/'], ['Move Energy Fund Management B.V.', 'https://www.moveenergy.vc'], ['Navitas Capital', 'http://www.navitascapital.nl'], ['Newion Partners', 'https://newion.com/'], ['NewPort Capital', 'https://www.newport.capital/nl/'], ['NextGen Ventures', 'https://nextgenventures.nl/'], ['NLC Health', 'https://nlc.health/'], ['NLI Capital', 'https://www.nlinvesteert.nl/fondsen/nli-capital/'], ['Nobel Capital Partners', 'https://nobelcapital.com/'], ['NOM', 'https://www.nom.nl/'], ['Nordian Capital Partners', 'http://www.nordian.nl'], ['NPM Capital N.V.', 'http://www.npm-capital.com'], ['O2 Capital Partners B.V.', 'https://o2capital.nl/'], ['One Two Capital', 'https://www.onetwocapital.com/nl/'], ['Oost NL', 'https://oostnl.nl/nl'], ['Panta Holdings B.V.', 'https://www.pantaholdings.nl'], ['Parcom', 'http://www.parcom.com'], ['Photon Capital Partners', 'https://www.photoncapital.com'], ['Plain Vanilla Investments', 'http://www.plainvanilla.nl'], ['Pontex Investment Partners', 'https://pontex-ip.nl/'], ['Pride Capital Partners', 'https://www.pridecapital.nl/'], ['Prime Ventures', 'http://www.primeventures.com'], ['Quadrum Capital', 'http://www.quadrum-capital.nl/'], ['Rabo Investments', 'https://raboinvestments.com/nl/'], ['Rivean Capital', 'https://riveancapital.com/'], ['Riverside Europe', 'https://www.riversideeurope.com/'], ['Rockstart', 'https://rockstart.com/'], ['ROM InWest', 'https://rominwest.nl/'], ['ROM Utrecht Region', 'https://www.romutrechtregion.nl/investeren/'], ['Rubio', 'https://www.rubio.vc/'], ['SEAM Investments', 'https://seaminvestments.nl/'], ['SET Ventures', 'http://www.setventures.com'], ['SHIFT Invest', 'http://www.shiftinvest.com'], ['Smile Invest', 'http://www.smile-invest.com'], ['Smile Sail & AI N.V.', 'https://www.smile-sail.com/'], ['Sofindev Management N.V.', 'https://www.sofindev.com'], ['StartGreen Capital', 'http://www.startgreen.nl'], ['Strong Root Capital', 'https://www.strongrootcapital.nl/'], ['Synergia Capital Partners', 'http://www.synergia.nl'], ['Thuja Capital Management', 'http://www.thujacapital.com'], ['TIN Capital', 'http://www.tiincapital.nl'], ['TNO Ventures Holding B.V.', 'https://ventures.tno.nl/'], ['Torqx Capital Partners', 'https://www.torqxcapital.com/nl/'], ['TransEquity Network', 'http://www.transequity.nl'], ['Triton', 'http://www.triton-partners.com'], ['Twinning Participaties', 'https://www.twinningparticipaties.nl/'], ['Ufenau Capaital Partners B.V.', 'https://www.ucp.ch'], ['VADO Beheer', 'https://www.vado.nl/'], ['Value Creation Capital B.V.', 'https://www.vcxc.com/'], ['Value Enhancement Partners', 'http://www.vepartners.com'], ['Value Factory Management B.V.', 'https://www.valuefactory.vc'], ['Vendis Capital Management', 'http://www.vendiscapital.com'], ['Victus Participations', 'https://victusparticipations.com/'], ['Volve Capital', 'https://www.volve.capital/'], ['Vortex Capital Partners', 'http://www.vortexcp.com'], ['VP Capital', 'https://vpcapital.eu/en/'], ['Wadinko', 'http://www.wadinko.nl'], ['Warburg Pincus B.V.', 'https://www.warburgpincus.com/'], ['Waterland Private Equity Investments', 'http://www.waterland.nu']]

# Links whose URL or text contains one of these are treated as a careers page
CAREER_LINK = re.compile(r"career|carri|vacanc|vacature|jobs?\b|werken[- ]bij|join[- ]us|join[- ]our|werkenbij|stage|internship|team/join", re.I)
# Words on the careers page that suggest an actual opening
OPENING = re.compile(r"internship|intern\b|stagiair|stagiaire|stage\b|afstudeer|traineeship|werkstudent|praktikum|analyst|associate|vacature|vacancy|vacancies|we are (looking|hiring)|we zoeken|wij zoeken|job opening|open position", re.I)
# Phrases that say there is currently nothing open
NO_OPENING = re.compile(r"no (current |open )?(vacancies|openings|positions)|currently (no|not)|geen (openstaande )?vacatures|momenteel geen|open (application|sollicitatie)", re.I)
# External job platforms: the jobs live there, not on the firm's site
ATS = re.compile(r"homerun\.co|recruitee\.com|teamtailor|workable\.com|greenhouse\.io|lever\.co|smartrecruiters|workday|personio|join\.com|jobs\.ashbyhq", re.I)

HEAD = {"User-Agent": "Mozilla/5.0 (NVP research; vacancy check)"}

def get(url):
    r = requests.get(url, headers=HEAD, timeout=20)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser")

def text_of(soup):
    for t in soup(["script", "style", "noscript"]):
        t.decompose()
    return " ".join(soup.get_text(" ").split())

def check(name, url):
    row = {"firm": name, "website": url, "status": "", "careers_page": "",
           "external_job_platform": "", "opening_words_found": "",
           "no_opening_phrase": "", "result": "", "snippets": []}
    try:
        home = get(url)
    except Exception as e:
        row["status"] = f"error: {type(e).__name__}"
        row["result"] = "CHECK BY HAND"
        return row
    row["status"] = "ok"
    links = []
    for a in home.find_all("a", href=True):
        href, label = a["href"], a.get_text(" ", strip=True)
        if CAREER_LINK.search(href) or CAREER_LINK.search(label):
            full = urljoin(url, href)
            if ATS.search(full):
                row["external_job_platform"] = full
            elif urlparse(full).scheme.startswith("http") and full not in links:
                links.append(full)
    if not links and not row["external_job_platform"]:
        row["result"] = "NO CAREERS PAGE FOUND"
        return row
    found, none_phrase = set(), ""
    for link in links[:3]:
        try:
            page = get(link)
        except Exception:
            continue
        row["careers_page"] = row["careers_page"] or link
        for a in page.find_all("a", href=True):
            if ATS.search(a["href"]):
                row["external_job_platform"] = urljoin(link, a["href"])
        t = text_of(page)
        found |= {m.group(0).lower() for m in OPENING.finditer(t)}
        for s in re.split(r"(?<=[.!?|])\s+", t):
            if OPENING.search(s) and len(s) < 250 and s not in row["snippets"]:
                row["snippets"].append(s)
        m = NO_OPENING.search(t)
        if m and not none_phrase:
            none_phrase = m.group(0)
    row["opening_words_found"] = ", ".join(sorted(found))
    row["no_opening_phrase"] = none_phrase
    if row["external_job_platform"]:
        row["result"] = "JOBS ON EXTERNAL PLATFORM - CHECK LINK"
    elif found and not none_phrase:
        row["result"] = "LIKELY OPENINGS"
    elif found and none_phrase:
        row["result"] = "UNCLEAR - CHECK BY HAND"
    else:
        row["result"] = "CAREERS PAGE, NO OPENINGS DETECTED"
    return row

# ---------- RSS output ----------
import hashlib, json, os
from datetime import datetime, timezone
from email.utils import format_datetime
from xml.sax.saxutils import escape

FEED_TITLE = "NVP members - vacancies and internships"
FEED_LINK = "https://nvp.nl/over/ledenoverzicht/leden/"
IN_FEED = ("LIKELY OPENINGS", "UNCLEAR - CHECK BY HAND", "JOBS ON EXTERNAL PLATFORM - CHECK LINK")
STATE = "seen.json"   # remembers when each item was first seen

def write_rss(rows):
    seen = json.load(open(STATE)) if os.path.exists(STATE) else {}
    now = datetime.now(timezone.utc)
    items = []
    for r in rows:
        if r["result"] not in IN_FEED:
            continue
        link = r["careers_page"] or r["external_job_platform"] or r["website"]
        snips = r["snippets"][:10]
        # New id when the vacancy text changes, so Meltwater sees it as a new item
        guid = hashlib.sha1((link + "|".join(snips)).encode()).hexdigest()
        first = seen.setdefault(guid, now.isoformat())
        desc = (f"Result: {r['result']}. Words found: {r['opening_words_found']}. "
                + " | ".join(snips))
        items.append((first, f"""  <item>
    <title>{escape(r['firm'])}: vacancy / internship</title>
    <link>{escape(link)}</link>
    <guid isPermaLink="false">{guid}</guid>
    <pubDate>{format_datetime(datetime.fromisoformat(first))}</pubDate>
    <description>{escape(desc)}</description>
  </item>"""))
    items.sort(reverse=True)
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
<channel>
  <title>{FEED_TITLE}</title>
  <link>{FEED_LINK}</link>
  <description>Automated weekly check of NVP member websites for vacancies and internships</description>
  <lastBuildDate>{format_datetime(now)}</lastBuildDate>
{chr(10).join(i for _, i in items)}
</channel>
</rss>
"""
    open("feed.xml", "w", encoding="utf-8").write(xml)
    json.dump(seen, open(STATE, "w"), indent=1)
    return len(items)

if __name__ == "__main__":
    out = []
    for i, (name, url) in enumerate(MEMBERS, 1):
        print(f"[{i}/{len(MEMBERS)}] {name}")
        out.append(check(name, url))
        time.sleep(1)  # be polite to the sites
    with open("nvp_vacancies.csv", "w", newline="", encoding="utf-8") as f:
        fields = [k for k in out[0] if k != "snippets"]
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader(); w.writerows(out)
    n = write_rss(out)
    print("\nSummary:")
    for r in sorted({r["result"] for r in out}):
        print(f"  {r}: {sum(1 for x in out if x['result']==r)}")
    print(f"Saved nvp_vacancies.csv and feed.xml ({n} items)")

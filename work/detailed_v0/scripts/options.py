"""Post-process the v0 build: kept-detail sectors, building split, and option B merged codes.

Run after build.py (which rewrites industries_v0.csv / products_v0.csv from scratch):
    python -I scripts/build.py && python -I scripts/options.py

Option A = every leaf as built. Option B = tier D leaves merged to (NACE division x EXIO3 code).
Construction (41-43), transport and storage (49-53) and data processing / hosting (63) keep full
detail in BOTH options, at Richard's request (2026-11-10).

Tiers below cite only sources held locally on 2026-11-10. A tier says what data separates a leaf from its siblings,
not what covers its parent: rail classes are tier D even though IEA covers the rail mode total. Leaves kept at full detail with no
separating source stay tier D and say so in their notes.
"""
from pathlib import Path
import pandas as pd

W = Path(__file__).resolve().parents[1]
ind = pd.read_csv(W / "industries_v0.csv", dtype=str).fillna("")
pro = pd.read_csv(W / "products_v0.csv", dtype=str).fillna("")
if "option_b_code" in ind.columns:
    raise SystemExit("industries_v0.csv already post-processed; run build.py first.")

heads = pd.read_csv(W / "refs" / "nace21_headings.tsv", sep="\t", dtype=str, usecols=["NACE_CODE", "EN_DESC"])
def _nm(n):
    n = n.strip('"')
    return n[:1] + n[1:].lower() if n.isupper() else n
NAME = {c.strip('"'): _nm(n) for c, n in zip(heads.NACE_CODE, heads.EN_DESC)}
KEEP_DIVS = {"41", "42", "43", "49", "50", "51", "52", "53", "63"}
KEPT = "Kept at full detail by request (construction, transport, data centres). "


def add(a, *new):
    s = [x for x in a.split(";") if x]
    s += [n for n in new if n and n not in s]
    return ";".join(s)


def note(r, text):
    r["notes"] = (r["notes"] + " | " if r["notes"] else "") + text


# ---------------------------------------------------------------- building split (41.00)
i41 = ind.index[ind.code == "41.00"]
p41 = pro.index[pro.code == "41.00"]
if len(i41) == 1 and len(p41) == 1:
    bi, bp = ind.loc[i41[0]].copy(), pro.loc[p41[0]].copy()
    ind = ind.drop(i41); pro = pro.drop(p41)
    rows_i, rows_p = [], []
    for suf, label, cpa in [("a", "residential", "41.00.1;41.00.3"), ("b", "non-residential", "41.00.2;41.00.4")]:
        r = bi.copy()
        r["code"] = f"41.00.{suf}"; r["name"] = f"Construction of {label} buildings"
        r["split_reason"] = "product-type"; r["principal_products"] = f"41.00.{suf}"
        rows_i.append(r)
        p = bp.copy()
        p["code"] = f"41.00.{suf}"; p["name"] = f"{label.capitalize()} buildings and construction works"
        p["cpa_code"] = cpa; p["producing_industries"] = f"41.00.{suf}"
        p["source_detail"] = f"CPA 2.2 categories {cpa.replace(';', ', ')}"
        rows_p.append(p)
    ind = pd.concat([ind, pd.DataFrame(rows_i)]).sort_values("code", kind="stable").reset_index(drop=True)
    pro = pd.concat([pro, pd.DataFrame(rows_p)]).reset_index(drop=True)
    for idx in pro.index:  # any other product listing 41.00 as producer now points at both
        if "41.00" in pro.at[idx, "producing_industries"].split(";"):
            pro.at[idx, "producing_industries"] = ";".join(
                x for y in pro.at[idx, "producing_industries"].split(";") for x in (["41.00.a", "41.00.b"] if y == "41.00" else [y]))

# ---------------------------------------------------------------- tiers for kept sectors
SUT_CONSTR = ("Detailed SUTs held separate construction by type (e.g. ABS IOPC: new houses, other residential, alterations, "
              "non-residential, roads and bridges, non-building nec, repair and maintenance). Candidate EU/global sources not held: "
              "Eurostat STS buildings vs civil engineering, Eurostat SBS by NACE class.")
RULES = [  # (class prefix, tier, anchors, note); first match wins, longest prefixes first
    ("41.00", "C", ["SUT-detailed"], SUT_CONSTR),
    ("42.1", "C", ["SUT-detailed"], SUT_CONSTR),
    ("42.", "C", ["SUT-detailed"], SUT_CONSTR),
    ("43.", "D", [], KEPT + "Detailed SUTs show construction trade services only as a whole; no source separates individual trades."),
    ("49.1", "D", ["IEA"], KEPT + "Rail mode total from IEA rail fuel use (all countries). Passenger vs freight rail: no source held (candidates: Eurostat rail_pa_total / rail_go_total, ITF)."),
    ("49.20", "D", ["IEA"], KEPT + "Rail mode total from IEA rail fuel use (all countries). Freight vs passenger share: candidates Eurostat rail_go_total, ITF (not held)."),
    ("49.41", "B", ["IEA", "Eurostat-transport"], "Road freight tonne-km from Eurostat road_go_ta_tott (EU, held); road mode total from IEA."),
    ("49.42", "B", ["IEA", "Eurostat-transport"], "Road freight tonne-km from Eurostat road_go_ta_tott (EU, held); road mode total from IEA."),
    ("49.3", "D", ["IEA"], KEPT + "Road mode total from IEA road fuel use (all countries). Passenger vs freight road split outside the EU needs ITF or vehicle-stock data (not held)."),
    ("49.50", "A", ["IEA"], "Pipeline transport: IEA pipeline transport flow (all countries)."),
    ("50.", "B", ["IEA", "OECD-maritime", "UNCTAD-fleet"], "Water transport: IEA domestic navigation and bunkers, OECD maritime transport, UNCTAD merchant fleet (held). Passenger vs freight split weakly supported."),
    ("51.10", "A", ["IEA", "WDI-air"], "Air passengers: World Bank WDI passengers carried (about 177 countries, held); IEA aviation fuel."),
    ("51.21", "A", ["IEA", "WDI-air"], "Air freight: World Bank WDI freight tonne-km (about 177 countries, held); IEA aviation fuel."),
    ("51.22", "D", [], KEPT + "Space transport: no source held."),
    ("52.", "D", ["PEFA"], KEPT + "PEFA energy accounts (EU/OECD, held) give division 52 as a whole; no source held separates the classes."),
    ("53.", "D", [], KEPT + "No source held separates the postal and courier classes."),
    ("63.10", "C", ["SUT-detailed"], "Data processing and hosting is separate in detailed SUTs held (ABS IOPC 59210020, BEA 518200). Candidate energy source not held: IEA data-centre electricity estimates."),
    ("63.9", "D", [], KEPT + "No source held separates web portals and other information services."),
]
RULES.sort(key=lambda t: -len(t[0]))


def retier(r, cls_col):
    c = (r[cls_col] or r["code"]).lstrip("c")
    if c[:2] not in KEEP_DIVS:
        return r
    for pre, tier, anc, txt in RULES:
        if c.startswith(pre):
            r["tier"] = tier
            r["data_anchors"] = add(r["data_anchors"], *anc)
            note(r, txt)
            break
    return r


ind = ind.apply(lambda r: retier(r, "nace21_class"), axis=1)

# ---------------------------------------------------------------- upgrades from sources fetched 2026-11-10
# Eurostat SBS (sbs_ovw_act, NACE Rev 2 class level, 2021-2024, EU/EEA): a NACE 2.1 class counts as separated
# only if it is the sole main destination of a NACE Rev 2 class reported in SBS (see rule below).
SBS = Path(r"D:\data\00-sources\eurostat\sbs_ovw_act\v2026\sbs_ovw_act.tsv.gz")
ORDER = {"A": 0, "B": 1, "C": 2, "D": 3}
PHYS = {  # NACE 2.1 class -> (anchors, note) from ITF / Eurostat physical activity data (held)
    "49.20": (["ITF", "Eurostat-rail"], "Rail freight tonne-km: ITF DF_TRENDSFREIGHT (54 countries) and Eurostat rail_go_total (37)."),
    "49.11": (["ITF", "Eurostat-rail"], "Rail passenger-km (all passenger rail together): ITF DF_STPASS (50 countries), Eurostat rail_pa_total (38). Heavy vs other passenger rail not separated."),
    "49.12": (["ITF", "Eurostat-rail"], "Rail passenger-km (all passenger rail together): ITF DF_STPASS (50 countries), Eurostat rail_pa_total (38). Heavy vs other passenger rail not separated."),
    "49.41": (["ITF"], "Road freight tonne-km: ITF DF_TRENDSFREIGHT (53 countries)."),
    "50.40": (["ITF"], "Inland waterway freight tonne-km: ITF (30 countries)."),
    "63.10": (["CSO-IE"], "Data-centre metered electricity: Ireland CSO MEC02 (quarterly 2015-2025). IEA Energy and AI data needs an IEA account (manual)."),
}
TIER_UP = {"49.20": "B", "49.41": "B", "50.40": "B"}  # physical data separating these leaves from siblings
if SBS.exists():
    s = pd.read_csv(SBS, sep="\t", dtype=str)
    k = s.columns[0]
    s[["freq", "nace", "ind", "geo"]] = s[k].str.split(",", expand=True)
    yc = [c for c in s.columns if c.strip().isdigit()]
    has = s[yc].apply(lambda c: c.str.strip().str.match(r"^[\d.]+")).any(axis=1)
    s = s[has & (s.ind == "NETTUR_MEUR") & ~s.geo.str.match(r"^(EU|EA)")]
    sbs_geos = s.groupby("nace").geo.nunique().to_dict()
    corr = pd.read_csv(W / "refs" / "nace21_nace2.tsv", sep="\t", dtype=str)
    corr = corr[corr.LEVEL == "4"]
    # Main destination of each NACE Rev 2 class X: the NACE 2.1 class with the same code if X feeds it;
    # else the only class X feeds; else the only class whose Common_Content for X has no "NN.NN:" prefix.
    # A NACE 2.1 class is separated in SBS if it is the main destination of a NACE Rev 2 class that SBS reports.
    pref = corr.Common_Content.fillna("").str.match(r"^\s*'?\d\d\.\d\d:")
    main = {}
    for x, g in corr.assign(pref=pref).groupby("NACE2_Code"):
        dest = g.NACE21_Code.unique().tolist()
        if x in dest:
            main[x] = x
        elif len(dest) == 1:
            main[x] = dest[0]
        else:
            u = g[~g.pref].NACE21_Code.unique().tolist()
            if len(u) == 1:
                main[x] = u[0]
    SEC = {"41": "F", "42": "F", "43": "F", "49": "H", "50": "H", "51": "H", "52": "H", "53": "H", "63": "J"}

    def sbs_up(r):
        c = r["nace21_class"]
        if c[:2] not in SEC or r["split_reason"]:  # SBS is class level: it cannot separate our sub-splits
            return r
        ded = [x for x, d in main.items() if d == c and x[:2] in SEC and sbs_geos.get(SEC[x[:2]] + x.replace(".", ""), 0) >= 20]
        if ded and ORDER[r["tier"]] > ORDER["B"]:
            g = max(sbs_geos.get(SEC[x[:2]] + x.replace(".", ""), 0) for x in ded)
            r["tier"] = "B"
            r["data_anchors"] = add(r["data_anchors"], "Eurostat-SBS")
            note(r, f"Eurostat SBS turnover, value added and employment for NACE Rev 2 {', '.join(ded)} ({g} EU/EEA countries, 2021-2024).")
        return r
    ind = ind.apply(sbs_up, axis=1)

def phys(r):
    c = r["nace21_class"]
    if c in PHYS:
        anc, txt = PHYS[c]
        r["data_anchors"] = add(r["data_anchors"], *anc)
        note(r, txt)
        if c in TIER_UP and ORDER[r["tier"]] > ORDER[TIER_UP[c]]:
            r["tier"] = TIER_UP[c]
    return r
ind = ind.apply(phys, axis=1)

pro["_cls"] = pro["code"].str.lstrip("c").str[:5]
pro = pro.apply(lambda r: retier(r, "_cls"), axis=1).drop(columns="_cls")
_itier = dict(zip(ind.code, ind.tier)); _ianc = dict(zip(ind.code, ind.data_anchors))
def follow(r):
    ps = [x for x in r["producing_industries"].split(";") if x]
    if ps and all(p[:2] in KEEP_DIVS for p in ps) and all(p in _itier for p in ps):
        best = min((_itier[p] for p in ps), key=lambda t: ORDER.get(t, 3))
        if ORDER.get(best, 3) < ORDER.get(r["tier"], 3):
            r["tier"] = best
            r["data_anchors"] = add(r["data_anchors"], *[a for p in ps for a in _ianc[p].split(";") if a])
    return r
pro = pro.apply(follow, axis=1)


# ---------------------------------------------------------------- option B merged codes
def merge_codes(df, div, ex_col, ex_name_col, prefix):
    df["option_b_code"] = df["code"]
    df["option_b_name"] = df["name"]
    m = (df["tier"] == "D") & ~div.isin(KEEP_DIVS) & (div != "")
    groups = {}
    for (d, ex), g in df[m].groupby([div[m], df.loc[m, ex_col]]):
        groups.setdefault(d, []).append((ex, list(g.index)))
    for d, items in groups.items():
        items.sort(key=lambda t: t[0] or "~")
        for k, (ex, idx) in enumerate(items):
            if len(idx) == 1:
                continue
            code = prefix + (d if len(items) == 1 else f"{d}.m{chr(97 + k)}")
            exlab = f"{ex} {df.at[idx[0], ex_name_col]}".strip() if ex else "no EXIOBASE 3 map"
            df.loc[idx, "option_b_code"] = code
            df.loc[idx, "option_b_name"] = NAME.get(d, d) + ("" if len(items) == 1 else f" (part in {exlab})")
    return df


ind = merge_codes(ind, ind["nace21_class"].str[:2], "exio3_industry_code", "exio3_industry_name", "")
pro = merge_codes(pro, pro["code"].str.lstrip("c").str[:2].where(pro["code"].str.lstrip("c").str[:2].str.isdigit(), ""),
                  "exio3_product_code", "exio3_product_name", "c")

ind.to_csv(W / "industries_v0.csv", index=False)
pro.to_csv(W / "products_v0.csv", index=False)
print("industries: option A", len(ind), "| option B", ind.option_b_code.nunique())
print("products:   option A", len(pro), "| option B", pro.option_b_code.nunique())
print("industry tiers", ind.tier.value_counts().sort_index().to_dict())
print("product tiers ", pro.tier.value_counts().sort_index().to_dict())

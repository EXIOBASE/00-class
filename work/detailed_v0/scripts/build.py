"""Build detailed EXIOBASE classification draft v0 (industries_v0.csv, products_v0.csv)."""
import os
import sys
import string
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from refs import *  # noqa
import nace_isic

OUT = r"D:\GitHub\EXIOBASE\00-class\work\detailed_v0"
os.makedirs(OUT, exist_ok=True)
LOG = []


def log(*a):
    LOG.append(" ".join(str(x) for x in a))


# ------------------------------------------------------------------ references
N21 = nace21()
NCLS = N21[N21.level == "class"].set_index("code")
NNAME = dict(zip(N21.code, N21.name))
CPA = cpa22()
CPANAME = dict(zip(CPA.code, CPA.name))
CPA6 = CPA[CPA.level == 6].code.tolist()
CPA6_BY_CLASS = defaultdict(list)
for c in CPA6:
    CPA6_BY_CLASS[c[:5]].append(c)
CPAHS = cpa22_hs()
CPA_HS6 = CPAHS.groupby("cpa").hs6.apply(lambda s: sorted(set(s))).to_dict()
CPC = cpc21()
CPCNAME = dict(zip(CPC.code, CPC.label))
CPCHS = cpc21_hs()
HS_CPC = CPCHS.groupby("hs6").cpc.apply(lambda s: sorted(set(s))).to_dict()
CPC_HS = CPCHS.groupby("cpc").hs6.apply(lambda s: sorted(set(s))).to_dict()
HS_CPA = CPAHS.groupby("hs6").cpa.apply(lambda s: sorted(set(s))).to_dict()
cpc3 = pd.read_csv(DL + r"\cpc3.csv", encoding="utf-8-sig", dtype=str)
cpc3.columns = ["code", "title"]
CPC3NAME = dict(zip(cpc3.code, cpc3.title))

EP, EI = exio3()
EPNAME = dict(zip(EP.CodeNr, EP.Name))
EINAME = dict(zip(EI.CodeNr, EI.Name))
p2i_df = conc(r"exiobase\exiobase3p_exiobase3i.csv")
P2I = dict(zip(p2i_df.source_code, p2i_df.target_code))
n2p = conc(r"international\nace2_exiobase3p.csv")
N2P = n2p.groupby("source_code").target_code.apply(set).to_dict()
hs96 = conc(r"international\hs1996_exiobase3p.csv")
HS96P = hs96.groupby("source_code").target_code.apply(list).to_dict()
enc5 = conc(r"encore\isic5_exiobase3i.csv")
ENC5 = enc5.groupby("source_code").target_code.apply(set).to_dict()
N21N2 = nace21_nace2().groupby("NACE21_Code").NACE2_Code.apply(list).to_dict()
I4CPC = pd.read_csv(CONC + r"\ISIC_Rev4__to__CPC_2.1.csv", dtype=str)
I4CPC = I4CPC.groupby("source_code").target_code.apply(lambda s: sorted(set(s))).to_dict()

NI = nace_isic.build().set_index("nace21_class")
# manual NACE 2.1 -> ISIC 5 assignments where name/structure matching was not conclusive
ISIC5_MANUAL = {
    "01.63": "0163;0164", "10.71": "1071", "10.72": "1071", "10.73": "1074", "10.83": "1076",
    "10.84": "1079", "10.86": "1079", "11.07": "1105", "13.96": "1399", "14.21": "1410", "14.22": "1410",
    "14.23": "1410", "14.24": "1410;1420", "14.29": "1410", "16.27": "1629", "20.51": "2011;2029",
    "20.11": "2011", "20.12": "2011", "20.13": "2011", "20.14": "2011", "20.16": "2013",
    "24.20": "2410", "24.31": "2410", "24.32": "2410", "24.33": "2410", "24.34": "2410",
    "26.11": "2611;2619", "26.12": "2619", "26.70": "2670;2680", "29.31": "2930", "29.32": "2930",
    "31.00": "3101;3102", "33.15": "3315", "33.17": "3315", "33.18": "3315",
    "35.11": "3511", "35.12": "3512", "35.13": "3513", "35.14": "3513", "35.15": "3513", "35.16": "3513",
    "35.24": "3520", "38.21": "3830", "38.22": "3821;3822", "38.23": "3821;3822", "38.31": "3821;3822",
    "38.32": "3821;3822", "38.33": "3821;3822", "43.13": "4312", "43.23": "4329", "43.41": "4390",
    "43.42": "4390", "43.50": "4390", "43.60": "4340", "43.91": "4390", "43.99": "4390",
    "46.43": "4649", "46.44": "4649", "46.45": "4649", "46.46": "4649", "46.48": "4649",
    "46.50": "4651;4652", "46.62": "4659", "46.63": "4659", "46.89": "4679",
    "47.11": "4711", "47.12": "4719", "47.21": "4721", "47.22": "4721", "47.23": "4721", "47.24": "4721",
    "47.27": "4721", "47.54": "4759", "47.55": "4759", "47.61": "4761", "47.62": "4761", "47.71": "4771",
    "47.72": "4771", "47.73": "4772", "47.74": "4772", "47.75": "4772", "47.76": "4773", "47.77": "4773",
    "47.78": "4773", "62.10": "6211;6219", "64.31": "6431;6432", "64.92": "6492;6495",
    "64.99": "6493;6494;6499", "68.20": "6810", "68.31": "6821", "84.12": "8412", "85.69": "8569",
    "86.91": "8699", "86.92": "8699", "86.93": "8699", "86.94": "8699", "86.95": "8699", "86.96": "8699",
    "90.39": "9039", "93.12": "9312", "93.13": "9311", "93.19": "9319", "93.29": "9329",
    "95.25": "9529", "95.29": "9529", "96.91": "9690", "10.11": "1010", "10.12": "1010", "10.13": "1010",
}
I45 = isic4_5()
I5I4 = I45.groupby("isic5").isic4.apply(set).to_dict()
I4N2 = isic4_nace2().groupby("isic4").nace2.apply(set).to_dict()
N2I4 = isic4_nace2().groupby("nace2").isic4.apply(set).to_dict()


def isic_for(cls):
    """Return (isic5 string, isic4 string, basis) for a NACE 2.1 class."""
    r = NI.loc[cls]
    if cls in ISIC5_MANUAL:
        i5s, basis = ISIC5_MANUAL[cls], "manual"
    else:
        i5s, basis = r.isic5_class, r.isic5_basis.split(":")[0]
        if basis in ("fuzzy",):
            basis = "manual-check"
    i4n21 = set()
    for n2 in N21N2.get(cls, []):
        i4n21 |= N2I4.get(n2, set())
    i4 = set()
    for i5 in i5s.split(";"):
        a = I5I4.get(i5, set())
        i4 |= (a & i4n21) or a
    return i5s, ";".join(sorted(i4)), basis


def nace2_exio_products(cls):
    s = set()
    for n2 in N21N2.get(cls, []):
        s |= N2P.get(n2, set()) | N2P.get(n2[:4], set())
    return s


def is_w(code):
    return ".w" in code


# ------------------------------------------------------------------ containers
PRODUCTS = []   # dicts
INDUSTRIES = []  # dicts
COVERED = set()  # CPA6 codes covered by domain product leaves


def add_product(**k):
    d = dict(base="", force_suffix=False, residual=False, name="", cpc21="", cpa_set=[], cpa_cover=[], exio3p="",
             nace_class="", ind_keys=None, source_detail="", anchors=set(), notes="", domain="", map_basis="")
    d.update(k)
    d["anchors"] = set(d["anchors"])
    PRODUCTS.append(d)
    return d


def add_industry(**k):
    d = dict(key="", nace_class="", name="", exio3i="", basis="", split_reason="", anchors=set(), notes="",
             force_suffix=False, isic5=None)
    d.update(k)
    d["anchors"] = set(d["anchors"])
    INDUSTRIES.append(d)
    return d


def hs_exio(cpa6_list):
    c = Counter()
    for cp in cpa6_list:
        for h in CPA_HS6.get(cp, []):
            for p in HS96P.get(h, []):
                c[p] += 1
    return c


def cpc_for_cpa(cpa6_list):
    s = set()
    for cp in cpa6_list:
        for h in CPA_HS6.get(cp, []):
            s |= set(HS_CPC.get(h, []))
    return sorted(s)


def common_prefix(codes):
    if not codes:
        return ""
    p = os.path.commonprefix(codes)
    return p


def cpc_label(codes, isic4=""):
    """cpc21 column: single subclass, short list, or the common CPC node."""
    if not codes and isic4:
        s = set()
        for i4 in isic4.split(";"):
            s |= set(I4CPC.get(i4, []))
        codes = sorted(s)
    if not codes:
        return ""
    if len(codes) <= 3:
        return ";".join(codes)
    cp = common_prefix(codes)
    if len(cp) >= 2:
        return cp
    return ";".join(codes[:3]) + ";..."


def cpa_node(cpa6_list):
    """Lowest CPA 2.2 node containing all codes."""
    cs = sorted(set(cpa6_list))
    if not cs:
        return ""
    if len(cs) == 1:
        return cs[0]
    cp = os.path.commonprefix(cs)
    for L in (7, 5, 4, 2):  # 'dd.dd.d', 'dd.dd', 'dd.d', 'dd'
        if len(cp) >= L and cp[:L] in CPANAME:
            return cp[:L]
    return ""


# ================================================================== PRODUCTS
# ---- A. FAO crops and livestock (SUA + QCL item lists, CPC 2.1 coded)
F = r"D:\indecol\Data\fao\data" + "\\"
fs = pd.read_csv(F + "SUA_Crops_Livestock_E_ItemCodes.csv", dtype=str, encoding="latin-1")
fq = pd.read_csv(F + "Production_Crops_Livestock_E_ItemCodes.csv", dtype=str, encoding="latin-1")
fs["src"] = "SUA"
fq["src"] = "QCL"
fao = pd.concat([fs, fq]).dropna(subset=["CPC Code"])
fao["cpc"] = fao["CPC Code"].str.lstrip("'")
fao = fao[~fao.cpc.str.startswith("F")]
fao = fao.groupby("Item Code").agg(cpc=("cpc", "first"), item=("Item", "first"), src=("src", lambda s: "+".join(sorted(set(s))))).reset_index()
pp = pd.read_csv(r"D:\GitHub\EXIOBASE\01-fao_balance\aux_data\Primary_production.csv", dtype=str)
PP = dict(zip(pp["FAO item code"], pp["EXIOBASE product code"]))
fe = conc(r"international\fao_exiobase3p.csv")
FE = {norm(a): b for a, b in zip(fe.source_name, fe.target_code)}
log("FAO items with CPC (SUA+QCL union, no F-aggregates):", len(fao))

FAO_CPC_RULE = {  # manual: CPC 2.1 prefix -> EXIO3 product, for items the EXIOBASE FAO map does not cover
    "0211": "p01.i", "0212": "p01.l", "0213": "p01.l", "0214": "p01.j", "0215": "p01.k", "0219": "p01.l",
    "022": "p01.n", "023": "p01.m", "0291": "p01.m", "0292": "p01.m", "0293": "p01.m", "0294": "p01.o",
    "0296": "p01.m", "02951": "p15.a", "0295": "p15.d", "21117": "p15.d", "21511": "p15.b", "21512": "p15.a",
    "21513": "p15.a", "21514": "p15.d", "21515": "p15.d", "21521": "p15.b", "21183": "p15.d", "2351": "p15.h",
}
fao_rows = []
for r in fao.itertuples():
    cpc = r.cpc
    base5 = re.match(r"\d+", cpc).group(0)[:5]
    subcl = [k for k in CPC_HS if k.startswith(base5)] if len(base5) < 5 else [base5]
    hs = sorted({h for k in subcl for h in CPC_HS.get(k, [])})
    cpa = sorted({c for h in hs for c in HS_CPA.get(h, [])})
    # primary FAO items (CPC divisions 01-04) stay on CPA divisions 01-03; processed items leave them
    if cpc[0] == "0":
        cpa = [c for c in cpa if c[:2] in ("01", "02", "03")]
    else:
        cpa = [c for c in cpa if c[:2] not in ("01", "02", "03")] or cpa
    rule = [v for k, v in sorted(FAO_CPC_RULE.items(), key=lambda kv: -len(kv[0])) if base5.startswith(k)]
    if r._1 in PP:
        p, basis = PP[r._1], "FAO-EXIO map (Primary_production.csv)"
    elif rule:
        p, basis = rule[0], "manual CPC-prefix rule (livestock and by-products)"
    elif norm(r.item) in FE:
        p, basis = FE[norm(r.item)], "fao_exiobase3p.csv name match"
    else:
        c = Counter(p for h in hs for p in HS96P.get(h, []))
        if c:
            p, basis = c.most_common(1)[0][0], "HS chain (CPC2.1-HS2017-HS1996 code identity)"
        else:
            cls = Counter(x[:5] for x in cpa)
            p, basis = "", "unmapped"
            if cls:
                ch = {q for q in nace2_exio_products(cls.most_common(1)[0][0]) if not is_w(q)}
                if len(ch) == 1:
                    p, basis = ch.pop(), "NACE chain of CPA class"
    fao_rows.append(dict(code=r._1, item=r.item, cpc=cpc, base5=base5, cpa=cpa, p=p, basis=basis, src=r.src))
fao_df = pd.DataFrame(fao_rows)

for (b5, p), g in fao_df.groupby(["base5", "p"], dropna=False):
    cpa = sorted({c for l in g.cpa for c in l})
    items = list(zip(g.code, g.item))
    if len(items) == 1:
        name = items[0][1].replace(";", ",")
    else:
        lbl = CPCNAME.get(b5, "")
        name = (lbl or items[0][1]) + " (" + str(len(items)) + " FAO items)"
    cls = Counter(c[:5] for c in cpa).most_common(1)
    cls = cls[0][0] if cls else ""
    node = cpa_node(cpa) if cpa else ""
    if node and len(node) < 5:
        # FAO group spans CPA classes: anchor on the majority class
        node = cls
    notes = []
    if not p:
        notes.append("EXIO3 product not determinable from FAO maps or chains")
    if any(b != g.basis.iloc[0] for b in g.basis):
        notes.append("mixed EXIO3 basis")
    notes.append("exio3 basis: " + ";".join(sorted(set(g.basis))))
    if len({c[:5] for c in cpa}) > 1:
        notes.append("CPC-HS-CPA chain reaches CPA classes " + ",".join(sorted({c[:5] for c in cpa})))
    add_product(base=node if node else "c" + b5, name=name, cpc21=b5, cpa_set=cpa if len(cpa) <= 6 else [],
                cpa_cover=cpa, exio3p=p, nace_class=cls,
                source_detail="FAO items " + "; ".join(f"{c} {n}" for c, n in items),
                anchors={"FAO"}, notes="; ".join(notes), domain="FAO", map_basis="manual" if p else "ambiguous")
log("FAO product leaves:", sum(1 for x in PRODUCTS if x["domain"] == "FAO"))

# ---- B. IEA energy products
IEA = [
    # code, name, cpa6 list, exio3p, producing industry keys, note
    ("ANTHRACITE", "Anthracite", ["05.10.01"], "p10.a", ["05.10"], ""),
    ("COKING_COAL", "Coking coal", ["05.10.02"], "p10.b", ["05.10"], ""),
    ("OTH_BITCOAL", "Other bituminous coal", ["05.10.02"], "p10.c", ["05.10"], ""),
    ("SUB_BITCOAL", "Sub-bituminous coal", ["05.10.02"], "p10.d", ["05.10"], "CPA 05.10.02 bituminous and other coal"),
    ("LIGNITE", "Lignite", ["05.20.00"], "p10.f", ["05.20"], ""),
    ("PEAT", "Peat", ["08.92.00"], "p10.h", ["08.92"], "also PV peat"),
    ("PATENT_FUEL", "Patent fuel", ["19.20.11"], "p10.e", ["19.20.b"], "EXIO3 books p10.e in i10"),
    ("BKB", "BKB (lignite briquettes)", ["19.20.12"], "p10.g", ["19.20.c"], ""),
    ("PEAT_PRODUCTS", "Peat products (peat briquettes)", ["19.20.13"], "p10.h", ["19.20.c"],
     "IEA_products_MRIO_products maps peat products to Peat (p10.h); p10.g BKB/Peat Briquettes may be more apt"),
    ("COKE_OVEN_COKE_OTH", "Coke oven coke", ["19.10.11"], "p23.1.a", ["19.10"], ""),
    ("GAS_COKE", "Gas coke", ["19.10.11"], "p23.1.b", ["35.21.a"], "EXIO3 supplies p23.1.b from i23.2"),
    ("COAL_TAR", "Coal tar", ["19.10.20"], "p23.1.c", ["19.10"], "EXIO3 supplies p23.1.c from i23.2"),
    ("CRUDE_OIL", "Crude oil", ["06.10.12"], "p11.a", ["06.10"], ""),
    ("OIL_SHALE", "Oil shale and oil sands", ["06.10.20"], "p11.a", ["06.10"], ""),
    ("NGL", "Natural gas liquids", ["06.10.11"], "p11.b.1", ["06.20"],
     "CPA 06.10.11 condensates sit in NACE 06.10; EXIO3 supplies NGL from i11.b"),
    ("NATURAL_GAS", "Natural gas", ["06.20.00"], "p11.b", ["06.20"], ""),
    ("HYDROCARBONS_OTHER", "Other hydrocarbons", [], "p11.c", ["19.20.d"], "no CPA subcategory; base CPA class 19.20"),
    ("REFINERY_FEEDSTOCKS", "Refinery feedstocks", [], "p23.20.j", ["19.20.a"], "no CPA subcategory; base CPA class 19.20"),
    ("ADDITIVES", "Additives/blending components", ["20.59.42"], "p24.f", ["20.59"], "also PV additives_blending"),
    ("REFINERY_GAS", "Refinery gas", ["19.20.33"], "p23.20.h", ["19.20.a"], ""),
    ("ETHANE", "Ethane", ["19.20.33"], "p23.20.k", ["19.20.a"], ""),
    ("LPG", "Liquefied petroleum gases (LPG)", ["19.20.31"], "p23.20.i", ["19.20.a"], ""),
    ("MOTOR_GASOLINE_NONBIO", "Motor gasoline excl. biofuels", ["19.20.21"], "p23.20.a", ["19.20.a"], ""),
    ("AVIATION_GASOLINE", "Aviation gasoline", ["19.20.21"], "p23.20.b", ["19.20.a"], ""),
    ("GASOLINE_JET", "Gasoline type jet fuel", ["19.20.23"], "p23.20.c", ["19.20.a"], ""),
    ("KEROSENE_JET_NONBIO", "Kerosene type jet fuel excl. biofuels", ["19.20.23"], "p23.20.d", ["19.20.a"], ""),
    ("KEROSENE_OTHER", "Other kerosene", ["19.20.26"], "p23.20.e", ["19.20.a"], "CPA 19.20.26 medium oils"),
    ("GAS_DIESEL_OIL_NONBIO", "Gas/diesel oil excl. biofuels", ["19.20.25"], "p23.20.f", ["19.20.a"], ""),
    ("FUEL_OIL_RESIDUAL", "Fuel oil", ["19.20.27"], "p23.20.g", ["19.20.a"], ""),
    ("NAPHTHA", "Naphtha", ["19.20.24"], "p23.20.l", ["19.20.a"], ""),
    ("WHITE_SPIRIT", "White spirit and SBP", ["19.20.22"], "p23.20.m", ["19.20.a"], ""),
    ("LUBRICANTS", "Lubricants", ["19.20.28"], "p23.20.n", ["19.20.a"], ""),
    ("BITUMEN", "Bitumen", ["19.20.42"], "p23.20.o", ["19.20.a"], ""),
    ("PARAFFIN_WAXES", "Paraffin waxes", ["19.20.41"], "p23.20.p", ["19.20.a"], ""),
    ("PETROLEUM_COKE", "Petroleum coke", ["19.20.42"], "p23.20.q", ["19.20.a"], ""),
    ("OTH_SEC_OIL_PRODS_ND", "Other oil products (incl. refinery olefins)", ["19.20.32", "19.20.99"], "p23.20.r",
     ["19.20.a"], "CPA 19.20.32 olefins placed here"),
    ("BIOGASOLINE", "Biogasoline", ["20.51.10"], "p24.g", ["20.51"], ""),
    ("BIODIESEL", "Biodiesels", ["20.51.10"], "p24.h", ["20.51"], ""),
    ("KEROSENE_JET_BIO", "Bio jet kerosene", ["20.51.10"], "p23.20.d", ["20.51"],
     "EXIO3 has no bio-jet product; IEA map sends it to p23.20.d (n:1 flagged)"),
    ("LIQBIOFUEL_OTHER", "Other liquid biofuels", ["20.51.10"], "p24.i", ["20.51"], ""),
    ("CHARCOAL", "Charcoal", ["20.14.72"], "p24.e", ["20.14.a"], ""),
    ("GASWORKS_GAS", "Gas works gas", ["35.21.01"], "p40.2.d", ["35.21.a"], ""),
    ("BIOGASES", "Biogases", ["35.21.02"], "p40.2.e", ["35.21.b"], ""),
    ("COKE_OVEN_GAS", "Coke oven gas", ["35.21.03"], "p40.2.a", ["35.21.c"], "physically a coke-oven by-product"),
    ("BLAST_FURNACE_GAS", "Blast furnace gas", ["35.21.03"], "p40.2.b", ["35.21.c"], "physically a blast-furnace by-product"),
    ("OSF_GAS", "Oxygen steel furnace gas", ["35.21.03"], "p40.2.c", ["35.21.c"],
     "not in IEA_internal product list; leaf kept because EXIO3 separates it"),
    ("OTH_RECOVGASES", "Other recovered gases", ["35.21.03"], "p40.2.d", ["35.21.c"], "IEA map sends to Gas Works Gas"),
    ("HEAT", "Heat (steam and hot water)", ["35.30.11", "35.30.12"], "p40.3", ["35.30", "CHP"], ""),
]
for code, name, cpa, p, ind, note in IEA:
    base = cpa_node(cpa) if cpa else "19.20"
    anchors = {"IEA"} if code != "OSF_GAS" else set()
    add_product(base=base, force_suffix=(not cpa), name=name, cpa_set=cpa, cpa_cover=cpa, exio3p=p,
                nace_class=(cpa[0][:5] if cpa else "19.20"), ind_keys=ind,
                source_detail=("IEA product " + code) if code != "OSF_GAS" else "EXIO3 p40.2.c",
                anchors=anchors, notes=note, domain="IEA", map_basis="manual")

# electricity by technology (EXIO3 p40.11.a-l) split by ISIC5 3511 / 3512
ELEC = [
    ("35.11.00", "coal", "p40.11.a", "COAL"), ("35.11.00", "natural gas", "p40.11.b", "GAS"),
    ("35.11.00", "nuclear", "p40.11.c", "NUC"), ("35.11.00", "petroleum and other oil derivatives", "p40.11.f", "OIL"),
    ("35.11.00", "non-renewable waste", "p40.11.g", "WNR"), ("35.11.00", "other sources n.e.c.", "p40.11.l", "NEC"),
    ("35.12.00", "hydro", "p40.11.d", "HYD"), ("35.12.00", "wind", "p40.11.e", "WND"),
    ("35.12.00", "solar photovoltaic", "p40.11.h", "SPV"), ("35.12.00", "solar thermal", "p40.11.i", "STH"),
    ("35.12.00", "tide, wave and ocean", "p40.11.j", "TID"), ("35.12.00", "geothermal", "p40.11.k", "GEO"),
    ("35.12.00", "biomass and renewable waste", "p40.11.g", "BIO"),
]
for cpa, tech, p, key in ELEC:
    note = ""
    if key == "NEC":
        note = "IEA 'other sources' placed under non-renewable (3511) by default; review"
    if key in ("WNR", "BIO"):
        note = "EXIO3 p40.11.g straddles ISIC5 3511/3512; split here (n:1 into p40.11.g)"
    add_product(base=cpa, force_suffix=True, name="Electricity by " + tech, cpa_set=[cpa], cpa_cover=[cpa],
                exio3p=p, nace_class=cpa[:5], ind_keys=["ELEC:" + key], cpc21="17100",
                source_detail="IEA electricity output by technology (" + key + ")", anchors={"IEA"},
                notes=note, domain="IEA", map_basis="manual")
for cpa, name, p, ind in [
    ("35.13.00", "Transmission services of electricity", "p40.12", ["35.13"]),
    ("35.14.00", "Distribution services of electricity", "p40.13", ["35.14"]),
    ("35.15.01", "Trade services of electricity for electric mobility", "p40.13", ["35.15"]),
    ("35.15.02", "Trade services of electricity, other", "p40.13", ["35.15"]),
    ("35.16.00", "Storage services of electricity", "", ["35.16"]),
    ("35.22.00", "Distribution services of gaseous fuels through mains", "p40.2.1", ["35.22"]),
    ("35.23.00", "Trade services of gas through mains", "p40.2.1", ["35.23"]),
    ("35.24.00", "Storage services of gas as part of network supply", "p40.2.1", ["35.24"]),
]:
    add_product(base=cpa, name=name, cpa_set=[cpa], cpa_cover=[cpa], exio3p=p, nace_class=cpa[:5], ind_keys=ind,
                source_detail="CPA 2.2 " + cpa, anchors={"IEA"} if cpa[:5] in ("35.13", "35.14") else set(),
                notes="" if p else "no EXIO3 counterpart for electricity storage; candidates p40.12/p40.13",
                domain="IEA", map_basis="manual" if p else "ambiguous")
add_product(base="35.40.00", force_suffix=True, name="Brokerage services for electric power", cpa_set=["35.40.00"],
            cpa_cover=["35.40.00"], exio3p="p40.13", nace_class="35.40", ind_keys=["35.40.a"],
            source_detail="CPA 2.2 35.40.00 (electricity part)", notes="plan 6.3: brokerage under p40.13",
            domain="IEA", map_basis="manual")
add_product(base="35.40.00", force_suffix=True, name="Brokerage services for natural gas", cpa_set=["35.40.00"],
            cpa_cover=["35.40.00"], exio3p="p40.2.1", nace_class="35.40", ind_keys=["35.40.b"],
            source_detail="CPA 2.2 35.40.00 (gas part)", notes="plan 6.3: gas brokerage under gas trade code",
            domain="IEA", map_basis="manual")

# ---- C. Production volumes (PV) minerals and metals
PVDEF = [
    # (pv label, name, cpa6 list, exio3p, industry key, anchors, note)
    ("iron_ore", "Iron ores", ["07.10.00"], "p13.1", ["07.10"], {"PV"}, ""),
    ("uranium", "Uranium and thorium ores", ["07.21.00"], "p12", ["07.21"], {"PV"}, ""),
    ("copper/ore", "Copper ores and concentrates", ["07.29.01"], "p13.20.11", ["07.29.a"], {"PV"}, ""),
    ("nickel/ore", "Nickel ores and concentrates", ["07.29.02"], "p13.20.12", ["07.29.b"], {"PV"}, ""),
    ("aluminium/bauxite", "Aluminium ores (bauxite)", ["07.29.03"], "p13.20.13", ["07.29.c"], {"PV"}, ""),
    ("gold", "Gold ores and concentrates", ["07.29.04"], "p13.20.14", ["07.29.d"], {"PV"}, ""),
    ("silver", "Silver ores and concentrates", ["07.29.04"], "p13.20.14", ["07.29.d"], {"PV"}, ""),
    ("pgm", "Platinum-group metal ores and concentrates", ["07.29.04"], "p13.20.14", ["07.29.d"], {"PV"}, ""),
    ("lead/ore", "Lead ores and concentrates", ["07.29.05"], "p13.20.15", ["07.29.e"], {"PV"}, ""),
    ("zinc/ore", "Zinc ores and concentrates", ["07.29.05"], "p13.20.15", ["07.29.e"], {"PV"}, ""),
    ("tin/ore", "Tin ores and concentrates", ["07.29.05"], "p13.20.15", ["07.29.e"], {"PV"}, ""),
]
for m in ["chromium", "manganese", "cobalt", "molybdenum", "tungsten", "lithium", "rare_earths", "vanadium",
          "titanium", "antimony", "beryllium", "mercury", "niobium", "tantalum", "strontium", "zirconium"]:
    PVDEF.append((m, m.replace("_", " ").capitalize() + " ores and concentrates", ["07.29.09"], "p13.20.16",
                  ["07.29.f"], {"PV"}, ""))
PVDEF.append(("bismuth;cadmium;arsenic;gallium;germanium;indium;rhenium;selenium;tellurium",
              "By-product minor metals (Bi, Cd, As, Ga, Ge, In, Re, Se, Te)", ["07.29.09"], "p13.20.16", ["07.29.f"],
              {"PV"}, "PV maps these to p13.20.16 ores; they are mostly refinery by-products, stage to review"))
PVDEF.append(("other_non_ferrous", "Other non-ferrous metal ores n.e.c.", ["07.29.09"], "p13.20.16", ["07.29.f"],
              {"PV"}, "residual"))
PVDEF += [
    ("phosphate_rock", "Phosphate rock", ["08.91.01"], "p14.3", ["08.91"], {"PV"}, ""),
    ("sulfur", "Sulphur and unroasted iron pyrites", ["08.91.02"], "p14.3", ["08.91"], {"PV"}, ""),
    ("potash", "Potash (natural potassium salts)", ["08.91.09"], "p14.3", ["08.91"], {"PV"}, "CPA placement manual"),
    ("boron", "Natural borates", ["08.91.09"], "p14.3", ["08.91"], {"PV"}, "CPA placement manual"),
    ("barite;fluorspar", "Barytes and fluorspar", ["08.91.09"], "p14.3", ["08.91"], {"PV"}, "CPA placement manual"),
    ("magnesite;magnesium_compounds", "Magnesite and natural magnesium compounds", ["08.91.09"], "p14.3", ["08.91"],
     {"PV"}, "CPA placement manual"),
    ("bromine;iodine", "Bromine and iodine from brines", ["08.91.09"], "p14.3", ["08.91"], {"PV"},
     "CPA placement manual; may belong to CPA 20.13"),
    ("soda_ash", "Natural sodium carbonate (trona)", ["08.91.09"], "p14.3", ["08.91"], {"PV"}, "CPA placement manual"),
    ("salt", "Salt", ["08.93.00"], "p14.3", ["08.93"], {"PV"}, ""),
    ("graphite;diatomite;talc;mica;feldspar;asbestos;perlite;vermiculite;wollastonite",
     "Other industrial minerals (graphite, diatomite, talc, mica, feldspar, asbestos, perlite, vermiculite, wollastonite)",
     ["08.99.23"], "p14.3", ["08.99"], {"PV"}, "PV separates each mineral; grouped in v0"),
    ("diamond", "Diamonds (gem and industrial)", ["08.99.21", "08.99.22"], "p14.3", ["08.99"], {"PV"}, ""),
    ("gypsum", "Gypsum and anhydrite (mined)", ["08.11.10"], "p14.1", ["08.11"], {"PV"},
     "PV maps mined gypsum to p26.d; NACE chain gives p14.1; v0 follows the chain"),
    ("limestone", "Limestone (excl. gypsum)", ["08.11.10"], "p14.1", ["08.11"], {"PRODCOM"}, ""),
    ("stone", "Ornamental and building stone, slate", ["08.11.31", "08.11.32", "08.11.40"], "p14.1", ["08.11"],
     {"PV"}, ""),
    ("aggregates_construction/crushed_rock", "Crushed stone and chippings", ["08.11.50"], "p14.1", ["08.11"],
     {"PV"}, ""),
    ("sand_gravel;aggregates_construction/sand_and_gravel", "Sand and gravel", ["08.12.11", "08.12.12", "08.12.13"],
     "p14.2", ["08.12"], {"PV"}, ""),
    ("clay;sillimanite", "Clays, kaolin, andalusite, kyanite, sillimanite", ["08.12.21", "08.12.22"], "p14.2",
     ["08.12"], {"PV"}, ""),
    ("helium", "Helium", ["06.20.00"], "p11.b", ["06.20"], {"PV"},
     "PV maps helium to p11.b; CPA placement in 06.20 is an assumption (helium is CPA 20.11 when purified)"),
]
# metals: stages and routes
PVDEF += [
    ("iron_pig", "Pig iron and spiegeleisen", ["24.10.11"], "p27.a", ["24.10.a"], {"PV", "PRODCOM"}, ""),
    ("ferroalloys;silicon", "Ferro-alloys (incl. silicon metal per PV)", ["24.10.12"], "p27.a", ["24.10.d"],
     {"PV", "PRODCOM"}, "PV maps silicon to p27.a"),
    ("steel/primary_BOF;primary_OHF", "Crude steel, primary route (BOF, OHF), ingots and semi-finished",
     ["24.10.21", "24.10.22", "24.10.23"], "p27.a", ["24.10.a", "24.10.b"], {"PV", "PRODCOM"}, ""),
    ("steel/secondary_EAF", "Crude steel, secondary route (EAF re-processing of scrap)",
     ["24.10.21", "24.10.22", "24.10.23"], "p27.a.w", ["24.10.c"], {"PV"},
     "route split of the same CPA codes, because EXIO3 separates p27.a.w"),
    ("aluminium/alumina", "Alumina (aluminium oxide)", ["24.42.12"], "p27.42", ["24.42.a"], {"PV", "PRODCOM"}, ""),
    ("aluminium/primary_Al", "Aluminium, unwrought, primary", ["24.42.11"], "p27.42", ["24.42.b"], {"PV", "PRODCOM"}, ""),
    ("aluminium/secondary_Al", "Aluminium, unwrought, secondary (re-processing)", ["24.42.11"], "p27.42.w",
     ["24.42.c"], {"PV"}, "route split of the same CPA code"),
    ("copper/smelter", "Copper mattes, unrefined copper and anodes", ["24.44.11", "24.44.12"], "p27.44", ["24.44.a"],
     {"PV", "PRODCOM"}, ""),
    ("copper/refined_primary", "Refined copper, primary", ["24.44.13"], "p27.44", ["24.44.a"], {"PV", "PRODCOM"}, ""),
    ("copper/refined_secondary", "Refined copper, secondary (re-processing)", ["24.44.13"], "p27.44.w", ["24.44.b"],
     {"PV"}, "route split of the same CPA code"),
    ("lead/refined_primary", "Lead, unwrought, primary", ["24.43.11"], "p27.43", ["24.43.a"], {"PV", "PRODCOM"}, ""),
    ("lead/refined_secondary", "Lead, unwrought, secondary", ["24.43.11"], "p27.43.w", ["24.43.b"], {"PV"}, ""),
    ("zinc/refined_primary", "Zinc, unwrought, primary", ["24.43.12"], "p27.43", ["24.43.a"], {"PV", "PRODCOM"}, ""),
    ("zinc/refined_secondary", "Zinc, unwrought, secondary", ["24.43.12"], "p27.43.w", ["24.43.b"], {"PV"},
     "PV maps secondary zinc to 'Secondary lead' p27.43.w"),
    ("tin/refined_primary", "Tin, unwrought, primary", ["24.43.13"], "p27.43", ["24.43.a"], {"PV", "PRODCOM"}, ""),
    ("tin/refined_secondary", "Tin, unwrought, secondary", ["24.43.13"], "p27.43.w", ["24.43.b"], {"PV"}, ""),
    ("precious_metals", "Precious metals, unwrought or semi-manufactured, primary",
     ["24.41.10", "24.41.20", "24.41.30"], "p27.41", ["24.41.a"], {"PV", "PRODCOM"}, ""),
    ("(EXIO3 p27.41.w)", "Precious metals, secondary (re-processing)", ["24.41.10", "24.41.20", "24.41.30"],
     "p27.41.w", ["24.41.b"], set(), "no PV secondary split for precious metals; kept because EXIO3 separates it"),
    ("nickel/refined", "Nickel, unwrought, and intermediate products", ["24.45.11", "24.45.12"], "p27.45", ["24.45.a"],
     {"PV", "PRODCOM"}, ""),
    ("magnesium;other_non_ferrous/products", "Other non-ferrous metals and articles", ["24.45.30"], "p27.45",
     ["24.45.a"], {"PV", "PRODCOM"}, ""),
    ("(EXIO3 p27.45.w)", "Other non-ferrous metals, secondary (re-processing)", ["24.45.11", "24.45.30"], "p27.45.w",
     ["24.45.b"], set(), "no PV secondary split; kept because EXIO3 separates it"),
    ("nuclear_fuel", "Natural uranium compounds and nuclear fuel", ["24.46.10"], "p23.3", ["24.46"], {"PV"}, ""),
    ("cement/clinker", "Cement clinker, primary", ["23.51.11"], "p26.d", ["23.51.a"], {"PV"}, ""),
    ("(EXIO3 p26.d.w)", "Clinker from re-processed ash", ["23.51.11"], "p26.d.w", ["23.51.c"], set(),
     "kept because EXIO3 separates it"),
    ("cement/cement", "Portland, aluminous and slag cement", ["23.51.12"], "p26.d", ["23.51.b"], {"PV", "PRODCOM"}, ""),
    ("ammonia", "Ammonia", ["20.15.10"], "p24.d", ["20.15.c"], {"PV", "PRODCOM"},
     "PV maps ammonia to p24.d chemicals nec; physically split from nitric acid in the same CPA code"),
    ("fertiliser_n (nitric acid part)", "Nitric acid and sulphonitric acids", ["20.15.10"], "p24.b", ["20.15.a"],
     {"PRODCOM"}, ""),
    ("soda_ash/synthetic", "Synthetic sodium carbonate (soda ash)", ["20.13.43"], "p24.d", ["20.13"], {"PV", "PRODCOM"},
     "CPA 20.13.43 carbonates (soda ash is part)"),
]
for lab, name, cpa, p, ind, anc, note in PVDEF:
    shared = sum(1 for x in PVDEF if x[2] == cpa) > 1 or any(set(cpa) & set(x[2]) for x in PVDEF if x[2] != cpa)
    add_product(base=cpa_node(cpa), force_suffix=shared, name=name, cpa_set=cpa, cpa_cover=cpa, exio3p=p,
                nace_class=cpa[0][:5], ind_keys=ind, source_detail="PV " + lab, anchors=anc, notes=note,
                domain="PV", map_basis="manual")

# secondary materials, waste (EXIO3 .w and p90 codes)
WREC = [
    ("38.21.3", "Secondary raw materials (recovered non-metal and metal materials)", ["38.21.21", "38.21.22", "38.21.23",
     "38.21.24", "38.21.25", "38.21.26", "38.21.31", "38.21.32", "38.21.33", "38.21.34", "38.21.35", "38.21.37",
     "38.21.11", "38.21.12", "38.21.13", "38.21.41", "38.21.42", "38.21.43", "38.21.50"], "p37", ["38.21.a"], ""),
    ("38.21.3", "Bottles for direct re-use", [], "p37.w.1", ["38.21.b"], "no CPA subcategory; EXIO3 p37.w.1"),
    ("38.21.36", "Aggregates from re-processed construction and demolition waste", ["38.21.36"], "p45.w", ["38.21.c"], ""),
    ("16.21", "Wood material re-processed from secondary wood", [], "p20.w", ["16.21.b"], "EXIO3 p20.w; placement manual"),
    ("17.11", "Pulp from recovered paper", [], "p21.w.1", ["17.11.b"], "EXIO3 p21.w.1"),
    ("20.16", "Plastics in primary forms from secondary plastic", [], "p24.a.w", ["20.16.b"], "EXIO3 p24.a.w"),
    ("23.13", "Glass from re-processed cullet", [], "p26.a.w", ["23.13.b"], "EXIO3 p26.a.w; placement in 23.13 manual"),
]
for base, name, cpa, p, ind, note in WREC:
    add_product(base=base, force_suffix=True, name=name, cpa_set=cpa, cpa_cover=cpa, exio3p=p,
                nace_class=(cpa[0][:5] if cpa else base[:5]), ind_keys=ind, source_detail="EXIO3 " + p,
                notes=note, domain="WASTE", map_basis="manual")
# waste treatment services: p90.x by treatment and NACE 2.1 class
WT = {"1": ("incineration", ["38.22", "38.31"]), "2": ("biogasification", ["38.22"]),
      "3": ("composting", ["38.23"]), "4": ("waste water treatment", ["37.00"]), "5": ("landfill", ["38.32"])}
for p in EP.CodeNr:
    if not p.startswith("p90."):
        continue
    t = p.split(".")[1]
    tname, classes = WT[t]
    for cls in classes:
        cpa = {"38.22": ["38.22.10"], "38.31": ["38.31.10", "38.31.20"], "38.23": ["38.23.00"],
               "37.00": ["37.00.11", "37.00.12"], "38.32": ["38.32.11", "38.32.12", "38.32.26"]}[cls]
        nm = EPNAME[p]
        if cls == "38.22":
            nm += " (with energy recovery)" if t == "1" else ""
        if cls == "38.31":
            nm += " (without energy recovery)"
        add_product(base=cls, force_suffix=True, name=nm, cpa_set=cpa, cpa_cover=cpa, exio3p=p, nace_class=cls,
                    ind_keys=["W:" + cls + ":" + p], source_detail="EXIO3 " + p, anchors={"IEA"} if cls == "38.22" else set(),
                    notes="split by waste type follows EXIO3; NACE 2.1 class by treatment", domain="WASTE",
                    map_basis="manual")

# ---- D. PRODCOM-derived CPA 6-digit leaves for divisions 20, 23, 24 (from PV classification_reference)
cr = pd.read_csv(r"D:\data\01-production_volumes\EXIOBASE_3_12_0\final\exio\classification_reference.csv", dtype=str)
pvmap = pd.read_csv(r"D:\GitHub\EXIOBASE\01-production_volumes\processing_classification\commodity_to_exio.csv", dtype=str)
num2p = dict(zip(range(1, 201), EP.CodeNr))
cpa21_to_22 = pd.read_csv(DN + r"\cpa22_cpa21.tsv", sep="\t", dtype=str)
cpa21_to_22 = cpa21_to_22[cpa21_to_22.LEVEL == "6"].groupby("CPA_Ver_21_Code").CPA_Ver_22_Code.apply(set).to_dict()
PRODCOM_CPA = defaultdict(set)  # cpa22 -> set of (pv label, exio3p)
for r in cr.itertuples():
    if pd.isna(r.cpa_2008_codes):
        continue
    p = num2p[int(r.exio_product_num)]
    lab = r.commodity + ("/" + r.sub_type if isinstance(r.sub_type, str) else "")
    for c in r.cpa_2008_codes.split(","):
        c = c.strip()
        for c22 in cpa21_to_22.get(c, {c} if c in CPANAME else set()):
            PRODCOM_CPA[c22].add((lab, p))
log("PRODCOM-derived CPA 2.2 subcategories (all divisions):", len(PRODCOM_CPA))
COVERED = set()
for d in PRODUCTS:
    COVERED |= set(d.get("cpa_cover", []))
for c22 in sorted(PRODCOM_CPA):
    if c22[:2] not in ("20", "23", "24") or c22 in COVERED:
        continue
    labs = PRODCOM_CPA[c22]
    ps = {p for _, p in labs}
    if len(ps) == 1:
        p, basis, note = ps.pop(), "manual", ""
    else:
        h = hs_exio([c22])
        cand = [q for q, _ in h.most_common() if q in ps]
        p = cand[0] if cand else ""
        basis = "manual" if p else "ambiguous"
        note = "PV pairs disagree (" + ",".join(sorted(ps)) + "); HS chain used"
    # fertiliser and chemical codes: refine via HS chain within the NACE chain set
    if c22.startswith("20.15"):
        h = hs_exio([c22])
        cand = [q for q, _ in h.most_common() if q in ("p24.b", "p24.c", "p24.d")]
        if cand:
            p, note = cand[0], "EXIO3 product from HS chain (fertiliser split)"
    add_product(base=c22, name=CPANAME[c22], cpa_set=[c22], cpa_cover=[c22], exio3p=p, nace_class=c22[:5],
                source_detail="PRODCOM via PV " + ";".join(sorted(l for l, _ in labs)), anchors={"PRODCOM", "PV"} if
                c22[:2] == "24" else {"PRODCOM"}, notes=note, domain="PRODCOM", map_basis=basis)

# ---- E. generic leaves for everything not covered
# manure treatment and extraterritorial outputs (EXIO3 codes without a CPA subcategory)
add_product(base="01.62", force_suffix=True, name="Manure treatment services (conventional), storage and land application",
            exio3p="p01.w.1", nace_class="01.62", ind_keys=["01.62.b"], source_detail="EXIO3 p01.w.1",
            notes="no CPA subcategory", domain="WASTE", map_basis="manual")
add_product(base="01.62", force_suffix=True, name="Manure treatment services (biogas), storage and land application",
            exio3p="p01.w.2", nace_class="01.62", ind_keys=["01.62.c"], source_detail="EXIO3 p01.w.2",
            notes="no CPA subcategory", domain="WASTE", map_basis="manual")
COVERED = set()
for d in PRODUCTS:
    COVERED |= set(d.get("cpa_cover", []))
# FAO leaves without a CPA link: place by EXIO3 product (class of the chain that names it)
CPC_I4 = defaultdict(set)
for i4, cs in I4CPC.items():
    for c in cs:
        CPC_I4[c].add(i4)
for d in PRODUCTS:
    if d["domain"] == "FAO" and not d["nace_class"]:
        i4s = {i4 for c, v in CPC_I4.items() if c.startswith(d["cpc21"]) for i4 in v}
        cl = sorted({c for c in NCLS.index if set(NI.loc[c].isic4_classes.split(";")) & i4s})
        if len(cl) == 1:
            d["nace_class"] = cl[0]
            d["notes"] += "; NACE class via official ISIC4-CPC2.1 table (no CPA link)"
for d in PRODUCTS:
    if d["domain"] == "FAO" and not d["nace_class"] and d["exio3p"]:
        cl = sorted(c for c in NCLS.index if d["exio3p"] in nace2_exio_products(c))
        if cl:
            d["nace_class"] = cl[0]
            d["notes"] += "; NACE class from NACE2 chain of the EXIO3 product (no CPA link)"
MANUAL_P = {  # service / mixed classes where the NACE chain gives several EXIO3 products
    "46.11": "p51", "46.12": "p51", "46.13": "p51", "46.14": "p51", "46.15": "p51", "46.16": "p51", "46.17": "p51",
    "46.18": "p51", "46.19": "p51", "47.91": "p52", "47.92": "p52", "52.24": "p63", "52.32": "p63",
    "60.39": "p72", "68.12": "p45", "77.51": "p74", "81.22": "p74", "91.30": "p92", "93.13": "p93",
    "95.10": "p72", "95.29": "p52", "96.91": "p95", "03.30": "p05", "18.12": "p22", "11.07": "p15.j",
    "14.10": "p18", "10.61": "p15.i", "10.62": "p15.i", "47.11": "p52", "47.12": "p52", "99.00": "p99",
}
# CPA subcategories whose CPA class is not a NACE 2.1 class (CPA 03.00, 72.30): manual class placement
FISH = {"03.00.11": "03.11", "03.00.12": "03.22", "03.00.13": "03.11", "03.00.14": "03.22", "03.00.21": "03.11",
        "03.00.22": "03.12", "03.00.23": "03.21", "03.00.24": "03.22", "03.00.31": "03.11", "03.00.32": "03.21",
        "03.00.41": "03.11", "03.00.42": "03.11", "03.00.43": "03.21", "03.00.44": "03.21", "03.00.45": "03.21",
        "03.00.46": "03.11", "03.00.51": "03.11", "03.00.52": "03.21", "03.00.61": "03.11", "03.00.62": "03.11",
        "03.00.63": "03.11", "03.00.64": "03.21", "03.00.65": "03.11", "03.00.66": "03.21", "03.00.69": "03.11",
        "03.00.71": "03.30", "03.00.72": "03.30", "72.30.00": "72.10"}
CLS_CPA = defaultdict(list)
for c in CPA6:
    CLS_CPA[FISH.get(c, c[:5])].append(c)
if set(CLS_CPA) - set(NCLS.index):
    log("CPA classes without NACE class:", sorted(set(CLS_CPA) - set(NCLS.index)))


def short_name(cs, cls):
    if len(cs) == 1:
        return CPANAME[cs[0]]
    node = cpa_node(cs)
    if node and len(node) >= 7:
        return CPANAME[node]
    return CPANAME.get(cls, NNAME.get(cls, cls)) + ", part (" + str(len(cs)) + " subcategories)"


DROPPED_P = []  # (class, minor exio3p, n subcategories) merged into the dominant product
for cls in sorted(NCLS.index):
    allc = CLS_CPA.get(cls, [])
    left = [c for c in allc if c not in COVERED]
    partial = len(left) < len(allc)
    sec = NCLS.loc[cls].section
    anchors = {"PRODCOM"} if sec in ("B", "C") else {"SUT-64"}
    chain = {q for q in nace2_exio_products(cls) if not is_w(q) and q not in ("p37", "p37.w.1")}
    chain_i = {P2I[q] for q in chain}
    if not allc:
        q = MANUAL_P.get(cls, next(iter(chain)) if len(chain) == 1 else "")
        add_product(base=cls, name=NNAME[cls] + " (services)", exio3p=q, nace_class=cls,
                    source_detail="NACE 2.1 class " + cls + " (no CPA 2.2 class of its own)", anchors=anchors,
                    notes="" if q else "EXIO3 candidates: " + ",".join(sorted(chain)), domain="generic",
                    map_basis=("manual" if cls in MANUAL_P else "official_chain") if q else "ambiguous")
        continue
    if not left:
        continue
    assign = {}
    for c in left:
        if cls in MANUAL_P:
            assign[c] = MANUAL_P[cls]
        elif len(chain) == 1:
            assign[c] = next(iter(chain))
        else:
            h = hs_exio([c])
            cand = [x for x, _ in h.most_common() if (x in chain or not chain)]
            assign[c] = cand[0] if cand else ""
    # dominant EXIO3 industry over domain leaves of the class and the generic subcategories
    dom = Counter()
    for d in PRODUCTS:
        if d["nace_class"] == cls and d["exio3p"]:
            dom[P2I[d["exio3p"]]] += max(1, d["source_detail"].count(";") + 1 if d["domain"] == "FAO" else len(d["cpa_cover"]))
    for c, q in assign.items():
        if q:
            dom[P2I[q]] += 1
    de = dom.most_common(1)[0][0] if dom else ""
    gq = Counter(q for q in assign.values() if q and P2I[q] == de)
    dq = gq.most_common(1)[0][0] if gq else ""
    if not dq:
        anyq = Counter(q for q in assign.values() if q)
        dq = anyq.most_common(1)[0][0] if anyq else ""
    dq_from_dom = False
    if not dq and de:
        dp = Counter(d["exio3p"] for d in PRODUCTS if d["nace_class"] == cls and d["exio3p"] and P2I[d["exio3p"]] == de)
        if dp:
            dq, dq_from_dom = dp.most_common(1)[0][0], True
    groups = defaultdict(list)
    minor = Counter()
    for c, q in assign.items():
        nq = sum(1 for v in assign.values() if v == q)
        keep = q and (q == dq or (P2I[q] != P2I.get(dq, "") and P2I[q] in chain_i and P2I[q] != de
                                  and nq >= 2 and nq >= 0.2 * len(assign)))
        if keep:
            groups[q].append(c)
        else:
            if q and q != dq:
                minor[q] += 1
            groups[dq].append(c)
    for q, n in minor.items():
        DROPPED_P.append((cls, q, n))
    for q, cs in groups.items():
        cs = sorted(cs)
        note = []
        if not q:
            note.append("EXIO3 candidates: " + ",".join(sorted(chain)) if chain else "no EXIO3 candidate from chains")
        if q == dq and minor:
            note.append("minor EXIO3 mappings merged: " + ",".join(f"{k}({v})" for k, v in sorted(minor.items())))
        if partial:
            note.append("residual after domain leaves")
        if q == dq and dq_from_dom:
            note.append("EXIO3 product taken from the dominant mapping of the class (subcategories not resolvable)")
        if len(groups) == 1:
            name = CPANAME.get(cls, NNAME[cls]) + (", other (residual)" if partial else "")
        else:
            name = short_name(cs, cls)
        if not CPANAME.get(cls) and cls[:2] == "03":
            name = NNAME[cls] + ": " + (short_name(cs, cls) if len(cs) == 1 else "products")
        b = ("manual" if cls in MANUAL_P else "official_chain") if q else "ambiguous"
        add_product(base=cls if cls in CPANAME else "03.00", force_suffix=(cls not in CPANAME), residual=partial,
                    name=name, cpa_set=cs, cpa_cover=cs, exio3p=q, nace_class=cls,
                    source_detail="CPA 2.2 class " + cls + " (" + str(len(cs)) + " subcategories)",
                    anchors=anchors, notes="; ".join(note), domain="generic", map_basis=b)
log("generic product minor EXIO3 mappings merged:", len(DROPPED_P))

# ================================================================== INDUSTRIES
SPECIAL = {}


def sp(cls, suffix_key, name, e, basis, split, anchors, note="", isic5=None):
    SPECIAL.setdefault(cls, []).append(dict(key=suffix_key, nace_class=cls, name=name, exio3i=e, basis=basis,
                                            split_reason=split, anchors=set(anchors), notes=note, isic5=isic5))


# electricity
EL_IND = [
    ("35.11", "COAL", "coal", "i40.11.a", True), ("35.11", "GAS", "natural gas", "i40.11.b", True),
    ("35.11", "OIL", "petroleum and oil products", "i40.11.f", True),
    ("35.11", "WNR", "non-renewable waste", "i40.11.g", True), ("35.11", "NUC", "nuclear", "i40.11.c", False),
    ("35.11", "NEC", "other sources n.e.c.", "i40.11.l", False), ("35.12", "HYD", "hydro", "i40.11.d", False),
    ("35.12", "WND", "wind", "i40.11.e", False), ("35.12", "SPV", "solar photovoltaic", "i40.11.h", False),
    ("35.12", "STH", "solar thermal", "i40.11.i", False), ("35.12", "TID", "tide, wave and ocean", "i40.11.j", False),
    ("35.12", "GEO", "geothermal", "i40.11.k", False), ("35.12", "BIO", "biomass and renewable waste", "i40.11.g", True),
]
for cls, k, tech, e, chp in EL_IND:
    if chp:
        sp(cls, "ELEC:" + k, "Electricity generation by " + tech + ", electricity-only plants", e, "manual",
           "technology", {"IEA"}, "IEA MAINELEC/AUTOELEC")
        sp(cls, "CHP:" + k, "Combined heat and power by " + tech, e, "manual", "technology", {"IEA"},
           "IEA MAINCHP/AUTOCHP; joint products electricity and heat; EXIO3 has no CHP industry")
    else:
        sp(cls, "ELEC:" + k, "Electricity generation by " + tech, e, "manual", "technology", {"IEA"},
           "IEA electricity output by source" + ("; 'other sources' assumed non-renewable" if k == "NEC" else ""))
sp("35.13", "35.13", "Transmission of electricity", "i40.12", "manual", "", {"IEA"})
sp("35.14", "35.14", "Distribution of electricity", "i40.13", "manual", "", {"IEA"})
sp("35.15", "35.15", "Trade of electricity", "i40.13", "manual", "", set())
sp("35.16", "35.16", "Storage of electricity", "", "ambiguous", "", set(),
   "EXIO3 candidates i40.11.l, i40.12, i40.13; IEA pumped storage is own use (EPUMPST)")
sp("35.40", "35.40.a", "Brokers and agents for electric power", "i40.13", "manual", "exio3-boundary", set())
sp("35.40", "35.40.b", "Brokers and agents for natural gas", "i40.2", "manual", "exio3-boundary", set())
sp("35.21", "35.21.a", "Gas works (manufactured gas from conventional sources)", "i40.2", "manual", "technology",
   {"IEA"}, "IEA TGASWKS")
sp("35.21", "35.21.b", "Biogas production for energy supply", "i40.2", "manual", "technology", {"IEA"},
   "IEA biogases; EXIO3 i90.2.x biogasification overlaps")
sp("35.21", "35.21.c", "Supply of recovered gases (coke oven, blast furnace, oxygen steel furnace, other)", "i40.2",
   "manual", "product-stage", {"IEA"}, "physically by-products of coke ovens and steelworks")
for c in ("35.22", "35.23", "35.24"):
    sp(c, c, NNAME[c], "i40.2", "manual", "", set())
sp("35.30", "35.30", "Steam and air conditioning supply (heat-only plants)", "i40.3", "official_chain", "", {"IEA"},
   "IEA MAINHEAT/AUTOHEAT; CHP heat comes from CHP leaves")
# fossil fuel transformation
sp("19.10", "19.10", "Coke ovens", "i23.1", "official_chain", "", {"IEA"}, "IEA TCOKEOVS")
sp("19.20", "19.20.a", "Oil refineries", "i23.2", "official_chain", "technology", {"IEA"},
   "IEA TREFINER; multi-product industry")
sp("19.20", "19.20.b", "Patent fuel plants", "i10", "manual", "technology", {"IEA"},
   "IEA TPATFUEL; EXIO3 books patent fuel in i10")
sp("19.20", "19.20.c", "BKB and peat briquette plants", "i10", "manual", "technology", {"IEA"},
   "IEA TBKB; EXIO3 books BKB in i10")
sp("19.20", "19.20.d", "Coal liquefaction and gas-to-liquids plants", "i11.c", "manual", "technology", {"IEA"},
   "IEA TCOALLIQ/TGTL; EXIO3 i11.c 'other hydrocarbons'")
sp("20.14", "20.14.a", "Charcoal production", "i24.d", "manual", "technology", {"IEA"}, "IEA TCHARCOAL")
sp("20.51", "20.51", "Manufacture of liquid biofuels", "i24.d", "manual", "", {"IEA"},
   "EXIO3 supplies biofuels from i24.d; multi-product")
# mining
sp("05.10", "05.10", "Mining of hard coal", "i10", "official_chain", "", {"IEA", "PV"})
sp("05.20", "05.20", "Mining of lignite", "i10", "official_chain", "", {"IEA"})
sp("08.92", "08.92", "Extraction of peat", "i10", "manual", "", {"IEA", "PV"}, "PV notes EXIOBASE books peat in i10")
for k, nm, e in [("07.29.a", "copper", "i13.20.11"), ("07.29.b", "nickel", "i13.20.12"),
                 ("07.29.c", "aluminium (bauxite)", "i13.20.13"), ("07.29.d", "precious metal", "i13.20.14"),
                 ("07.29.e", "lead, zinc and tin", "i13.20.15"), ("07.29.f", "other non-ferrous metal", "i13.20.16")]:
    sp("07.29", k, "Mining of " + nm + " ores", e, "official_chain", "exio3-boundary", {"PV"})
# metals
sp("24.10", "24.10.a", "Basic iron and steel, blast furnace and basic oxygen furnace route (BOF)", "i27.a", "manual",
   "route", {"PV", "IEA"}, "PV steel/primary_BOF; IEA blast furnaces; DRI not separated in PV")
sp("24.10", "24.10.b", "Basic iron and steel, open hearth furnace route (OHF)", "i27.a", "manual", "route", {"PV"},
   "PV steel/primary_OHF")
sp("24.10", "24.10.c", "Basic steel, electric arc furnace route (EAF, secondary)", "i27.a.w", "manual", "route",
   {"PV"}, "PV steel/secondary_EAF; EAF also melts DRI and pig iron, EXIO3 treats it as re-processing of scrap")
sp("24.10", "24.10.d", "Manufacture of ferro-alloys", "i27.a", "manual", "product-stage", {"PV", "PRODCOM"},
   "PV ferroalloys")
for cls, mt, e in [("24.41", "precious metals", "i27.41"), ("24.43", "lead, zinc and tin", "i27.43"),
                   ("24.44", "copper", "i27.44"), ("24.45", "nickel and other non-ferrous metals", "i27.45")]:
    sp(cls, cls + ".a", "Primary " + mt + " production", e, "official_chain", "route", {"PV"})
    sp(cls, cls + ".b", "Secondary " + mt + " production (re-processing of scrap)", e + ".w", "manual", "route",
       {"PV"} if cls in ("24.43", "24.44") else set(),
       "" if cls in ("24.43", "24.44") else "no PV secondary data; kept because EXIO3 separates it")
sp("24.42", "24.42.a", "Alumina refining", "i27.42", "official_chain", "product-stage", {"PV"}, "PV aluminium/alumina")
sp("24.42", "24.42.b", "Primary aluminium smelting (and semis)", "i27.42", "official_chain", "route", {"PV"})
sp("24.42", "24.42.c", "Secondary aluminium production (re-processing of scrap)", "i27.42.w", "manual", "route", {"PV"})
sp("23.51", "23.51.a", "Clinker production", "i26.d", "official_chain", "product-stage", {"PV"}, "PV cement/clinker")
sp("23.51", "23.51.b", "Cement grinding and blending", "i26.d", "official_chain", "product-stage", {"PV"})
sp("23.51", "23.51.c", "Re-processing of ash into clinker", "i26.d.w", "manual", "exio3-boundary", set())
sp("20.15", "20.15.a", "Manufacture of nitrogen fertilisers", "i24.b", "official_chain", "exio3-boundary",
   {"PV", "PRODCOM"})
sp("20.15", "20.15.b", "Manufacture of phosphorus, potassium and compound fertilisers", "i24.c", "official_chain",
   "exio3-boundary", {"PV", "PRODCOM"})
sp("20.15", "20.15.c", "Manufacture of ammonia and other nitrogen compounds", "i24.d", "official_chain",
   "exio3-boundary", {"PV", "PRODCOM"}, "PV maps ammonia to p24.d")
# .w placements and recycling
sp("38.21", "38.21.a", "Materials recovery (recycling of waste and scrap)", "i37", "official_chain", "exio3-boundary", set())
sp("38.21", "38.21.b", "Recycling of bottles by direct re-use", "i37.w.1", "official_chain", "exio3-boundary", set())
sp("38.21", "38.21.c", "Re-processing of construction and demolition waste into aggregates", "i45.w", "manual",
   "exio3-boundary", set(), "EXIO3 i45.w placed in 38.21 (manual)")
sp("16.21", "16.21.b", "Re-processing of secondary wood material into new wood material", "i20.w", "manual",
   "exio3-boundary", set(), "placement in 16.21 manual")
sp("17.11", "17.11.b", "Re-processing of recovered paper into pulp", "i21.w.1", "manual", "route", set())
sp("20.16", "20.16.b", "Re-processing of secondary plastic into plastics in primary forms", "i24.a.w", "manual",
   "route", set())
sp("23.13", "23.13.b", "Re-processing of secondary glass (cullet) into new glass", "i26.a.w", "manual", "route",
   set(), "placement in 23.13 manual")
# waste treatment
for d in PRODUCTS:
    if d["ind_keys"] and d["ind_keys"][0].startswith("W:"):
        _, cls, p = d["ind_keys"][0].split(":")
        sp(cls, d["ind_keys"][0], NNAME[cls] + ": " + EINAME[P2I[p]], P2I[p], "manual", "exio3-boundary",
           d["anchors"])
for cls in ("38.11", "38.12", "38.33"):
    sp(cls, cls, NNAME[cls], "", "ambiguous", "", set(),
       "EXIO3 has no collection/other disposal industry; candidates i90.1.x-i90.5.x")
sp("01.62", "01.62.b", "Manure treatment (conventional), storage and land application", "i01.w.1", "official_chain",
   "exio3-boundary", set(), "placement in 01.62 follows NACE2 chain")
sp("01.62", "01.62.c", "Manure treatment (biogas), storage and land application", "i01.w.2", "official_chain",
   "exio3-boundary", set(), "placement in 01.62 follows NACE2 chain")

# map special product ind_keys of form 'cls' or 'cls.x' to keys
# (keys used in product definitions are either an explicit special key or a class code)

# ---- generic industries from products (boundary rule)
prod_by_class = defaultdict(list)
for d in PRODUCTS:
    prod_by_class[d["nace_class"]].append(d)
FULL_SPECIAL = {"35.11", "35.12", "35.13", "35.14", "35.15", "35.16", "35.21", "35.22", "35.23", "35.24", "35.30",
                "35.40", "19.10", "19.20", "05.10", "05.20", "08.92", "07.29", "24.10", "24.42", "38.11", "38.12",
                "38.33", "38.22", "38.31", "38.23", "38.32", "20.51", "20.15", "23.51", "24.41", "24.43", "24.44",
                "24.45"}
DROPPED_I = []


def weight(d):
    if d["domain"] == "FAO":
        return d["source_detail"].count(";") + 1
    return max(1, len(d["cpa_cover"]))


for cls in sorted(NCLS.index):
    spec = SPECIAL.get(cls, [])
    for s in spec:
        add_industry(**s)
    if cls in FULL_SPECIAL:
        continue
    spec_e = {}
    for s in spec:
        spec_e.setdefault(s["exio3i"], s["key"])
    prods = [d for d in prod_by_class.get(cls, []) if not d["ind_keys"] or d["ind_keys"] == [cls]]
    rest = []
    for d in prods:
        e = P2I.get(d["exio3p"], "")
        if e and e in spec_e:
            d["ind_keys"] = [spec_e[e]]
        else:
            rest.append(d)
    if not rest and spec:
        continue
    chain_i = {P2I[q] for q in nace2_exio_products(cls) if q in P2I and not is_w(q)}
    cnt = Counter()
    for d in rest:
        e = P2I.get(d["exio3p"], "")
        if e:
            cnt[e] += weight(d)
    de = cnt.most_common(1)[0][0] if cnt else ""
    tot = sum(cnt.values())
    dom_e = defaultdict(set)
    for d in rest:
        dom_e[P2I.get(d["exio3p"], "")].add(d["domain"])
    keep = {de} | {e for e in cnt if e != de and e in chain_i and
                   (dom_e[e] & {"FAO", "PV", "IEA"} or (cnt[e] >= 2 and cnt[e] >= 0.2 * tot))}
    groups = defaultdict(list)
    minor = Counter()
    for d in rest:
        e = P2I.get(d["exio3p"], "")
        if e in keep:
            groups[e].append(d)
        else:
            groups[de].append(d)
            if e and e != de:
                minor[e] += weight(d)
                d["notes"] = (d["notes"] + "; " if d["notes"] else "") + \
                    f"supplied by the class leaf mapped to {de or 'ambiguous'} (EXIO3 {e} is a minor mapping of this class)"
    if not groups:
        groups[""] = []
    for e, n in minor.items():
        DROPPED_I.append((cls, e, n))
    n_leaves = len(groups) + len(spec)
    for e, ds in groups.items():
        doms = {d["domain"] for d in ds}
        note = []
        if not e:
            enc = ENC5.get(isic_for(cls)[0].split(";")[0], set())
            if len(enc) == 1:
                e, basis = next(iter(enc)), "encore"
                note.append("EXIO3 from ENCORE ISIC5 table")
            else:
                basis = "ambiguous"
                cands = sorted((chain_i | enc) - {""})
                note.append("EXIO3 candidates: " + (",".join(cands) if cands else "none from NACE2 chain or ENCORE"))
        elif doms & {"FAO", "PV", "IEA"}:
            basis = "manual"
        elif chain_i == {e}:
            basis = "official_chain"
        elif cls in MANUAL_P:
            basis = "manual"
            note.append("NACE2 chain gives " + ",".join(sorted(chain_i)))
        elif e in chain_i:
            basis = "official_chain"
            if len(chain_i) > 1:
                note.append("NACE2 chain set " + ",".join(sorted(chain_i)) + "; dominant by CPA subcategories")
        else:
            basis = "official_chain"
            note.append("EXIO3 from HS chain of CPA subcategories")
        if e == de and minor:
            note.append("minor EXIO3 mappings in class: " + ",".join(f"{k}({v})" for k, v in sorted(minor.items())))
        anchors = set()
        for d in ds:
            anchors |= d["anchors"]
        nm = NNAME[cls]
        split = ""
        if n_leaves > 1:
            nm += ": " + EINAME.get(e, "other")[:60] if e else ", other"
            split = "exio3-boundary" if len(groups) > 1 else ""
        key = "G:" + cls + ":" + e
        add_industry(key=key, nace_class=cls, name=nm, exio3i=e, basis=basis, split_reason=split, anchors=anchors,
                     notes="; ".join(note))
        for d in ds:
            d["ind_keys"] = [key]
log("industry minor EXIO3 mappings collapsed:", len(DROPPED_I))

IND_BY_KEY = {d["key"]: d for d in INDUSTRIES}
# resolve product ind_keys given as a class code or special key
for d in PRODUCTS:
    ks = d["ind_keys"] or []
    out = []
    for k in ks:
        if k in IND_BY_KEY:
            out.append(k)
        elif k == "CHP":
            out += [x for x in IND_BY_KEY if x.startswith("CHP:")]
        elif k.startswith("ELEC:"):
            out.append(k)
            if "CHP:" + k[5:] in IND_BY_KEY:
                out.append("CHP:" + k[5:])
        else:
            cand = [x for x, v in IND_BY_KEY.items() if v["nace_class"] == k]
            out +=cand if len(cand) == 1 else [x for x in cand if IND_BY_KEY[x]["exio3i"] == P2I.get(d["exio3p"], "?")] or cand[:1]
    d["ind_keys"] = out
# products still without industry: link by class + exio3 industry
for d in PRODUCTS:
    if not d["ind_keys"]:
        cand = [x for x, v in IND_BY_KEY.items() if v["nace_class"] == d["nace_class"]]
        m = [x for x in cand if IND_BY_KEY[x]["exio3i"] == P2I.get(d["exio3p"], "?")]
        d["ind_keys"] = m or cand[:1]
        if not d["ind_keys"]:
            log("product without industry:", d["name"], d["nace_class"])

# ================================================================== codes
LET = string.ascii_lowercase


def assign_codes(items, basef, forcef):
    """Code = base when a base has a single leaf; otherwise base + contiguous letters in insertion order."""
    by = defaultdict(list)
    for it in items:
        by[basef(it)].append(it)
    for b, its in by.items():
        if len(its) == 1 and not forcef(its[0]):
            its[0]["code"] = b
            continue
        for k, i in enumerate(its):
            i["code"] = b + "." + LET[k] if k < 26 else b + "." + LET[k // 26 - 1] + LET[k % 26]


# residual leaves go last within their base
PRODUCTS.sort(key=lambda d: d["residual"])
for d in INDUSTRIES:
    d["_force"] = len([x for x in INDUSTRIES if x["nace_class"] == d["nace_class"]]) > 1
assign_codes(INDUSTRIES, lambda d: d["nace_class"], lambda d: d["_force"])
assign_codes(PRODUCTS, lambda d: d["base"], lambda d: d["force_suffix"])
KEY2CODE = {d["key"]: d["code"] for d in INDUSTRIES}
codes = [d["code"] for d in INDUSTRIES]
assert len(codes) == len(set(codes)), Counter(codes).most_common(5)
pcodes = [d["code"] for d in PRODUCTS]
assert len(pcodes) == len(set(pcodes)), Counter(pcodes).most_common(5)

# ================================================================== tiers and output
TIER = {"FAO": "A", "IEA": "A", "PV": "A", "PRODCOM": "B", "SUT-detailed": "C", "SUT-64": "C"}


def tier(anchors, n_div_leaves=99):
    a = set(anchors)
    if a & {"FAO", "IEA", "PV"}:
        return "A"
    if "PRODCOM" in a:
        return "B"
    if "SUT-64" in a and n_div_leaves == 1:
        return "C"
    return "D"


div_count = Counter(d["nace_class"][:2] for d in INDUSTRIES)
ind_principal = defaultdict(list)
for d in PRODUCTS:
    for k in d["ind_keys"]:
        ind_principal[k].append(d["code"])

rows = []
for d in sorted(INDUSTRIES, key=lambda x: x["code"]):
    cls = d["nace_class"]
    i5, i4, ib = isic_for(cls)
    notes = [d["notes"]] if d["notes"] else []
    if d.get("isic5"):
        i5 = d["isic5"]
    if cls == "35.11":
        i5 = "3511"
    if cls == "35.12":
        i5 = "3512"
    if ";" in i5:
        notes.append("NACE 2.1 class spans ISIC5 classes " + i5)
    if ib in ("manual", "manual-check", "chain", "group_unique"):
        notes.append("ISIC5 link basis: " + ib)
    anchors = set(d["anchors"])
    for pc in ind_principal.get(d["key"], []):
        pass
    if not anchors:
        anchors = {"PRODCOM"} if NCLS.loc[cls].section in ("B", "C") else {"SUT-64"}
    rows.append(dict(code=d["code"], name=d["name"], nace21_name=NNAME[cls], section=NCLS.loc[cls].section, division=cls[:2], group=cls[:4],
                     nace21_class=cls, isic5_class=i5, isic4_classes=i4, exio3_industry_code=d["exio3i"],
                     exio3_industry_name=EINAME.get(d["exio3i"], ""), exio3_map_basis=d["basis"],
                     split_reason=d["split_reason"], principal_products=";".join(sorted(ind_principal.get(d["key"], []))),
                     data_anchors=";".join(sorted(anchors)), tier=tier(anchors, div_count[cls[:2]]),
                     notes="; ".join(n for n in notes if n)))
ind_df = pd.DataFrame(rows)
for c in ind_df.columns:
    ind_df[c] = ind_df[c].astype(str).str.replace("\u2014", ", ").str.replace("\u2013", "-")
ind_df.to_csv(OUT + r"\industries_v0.csv", index=False, encoding="utf-8")

prows = []
for d in sorted(PRODUCTS, key=lambda x: x["code"]):
    cpa = d["cpa_set"]
    cpc = d["cpc21"]
    if not cpc:
        cls = d["nace_class"]
        i4 = isic_for(cls)[1] if cls in NCLS.index else ""
        cpc = cpc_label(cpc_for_cpa(cpa), i4 if cls[:2] >= "35" or not cpc_for_cpa(cpa) else "")
    c30 = ""
    if cpc and ";" not in cpc and len(cpc) == 5 and cpc in CPC3NAME and norm(CPC3NAME[cpc]) == norm(CPCNAME.get(cpc, "#")):
        c30 = cpc
    hs = sorted({h for c in cpa for h in CPA_HS6.get(c, [])})
    hs_hint = ";".join(hs[:6]) + (";..." if len(hs) > 6 else "")
    anchors = d["anchors"] or ({"PRODCOM"} if d["nace_class"][:2] < "35" else {"SUT-64"})
    prows.append(dict(code=d["code"], name=d["name"], cpc21=cpc, cpc30=c30,
                      cpa_code=";".join(cpa) if len(cpa) <= 6 else d["base"], hs_hint=hs_hint,
                      exio3_product_code=d["exio3p"], exio3_product_name=EPNAME.get(d["exio3p"], ""),
                      producing_industries=";".join(sorted({KEY2CODE[k] for k in d["ind_keys"] if k in KEY2CODE})),
                      source_detail=d["source_detail"], data_anchors=";".join(sorted(anchors)),
                      tier=tier(anchors, 1 if d["domain"] == "generic" and d["base"][:2] == d["base"] else 99),
                      notes=d["notes"], domain=d["domain"]))
prod_df = pd.DataFrame(prows)
for c in prod_df.columns:
    prod_df[c] = prod_df[c].astype(str).str.replace("\u2014", ", ").str.replace("\u2013", "-")
prod_df.to_csv(OUT + r"\products_v0.csv", index=False, encoding="utf-8")

with open(os.path.join(OUT, "build.log"), "w", encoding="utf-8") as f:
    f.write("\n".join(LOG))
print("\n".join(LOG))
print("industries", len(ind_df), "products", len(prod_df))

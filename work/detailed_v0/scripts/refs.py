import os
"""Reference loaders for detailed_v0 build. Downloaded files are read as data only."""
import re
import pandas as pd

S = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "refs")
DL = S
DN = S
CONC = r"D:\indecol\data\suts\processed\concordances"
EC = r"D:\GitHub\EXIOBASE\00-concordances\concordances"
CLS = r"D:\GitHub\EXIOBASE\00-class\class"


def norm(s):
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def nace21():
    """NACE 2.1 structure from the Eurostat SDMX codelist NACE_R2_1 (TSV)."""
    rows = []
    with open(DN + r"\NACE_R2_1.tsv", encoding="utf-8") as f:
        for line in f:
            code, name = line.rstrip("\n").split("\t", 1)
            if re.fullmatch(r"[A-V]", code):
                rows.append((code, code, name, "section"))
            elif re.fullmatch(r"[A-V]\d{2}", code):
                rows.append((code, code[1:], name, "division"))
            elif re.fullmatch(r"[A-V]\d{3}", code):
                rows.append((code, code[1:3] + "." + code[3], name, "group"))
            elif re.fullmatch(r"[A-V]\d{4}", code):
                rows.append((code, code[1:3] + "." + code[3:], name, "class"))
    d = pd.DataFrame(rows, columns=["raw", "code", "name", "level"])
    d["section"] = d.raw.str[0]
    return d


def nace21_nace2():
    c = pd.read_csv(DN + r"\nace21_nace2.tsv", sep="\t", dtype=str)
    c = c[c.LEVEL == "4"]
    return c[["NACE21_Code", "NACE2_Code", "TypeOfCorrespondence"]].dropna(subset=["NACE2_Code"])


def isic5():
    d = pd.read_csv(DL + r"\isic5.csv", encoding="latin-1", dtype=str)
    d.columns = ["code", "name"]
    return d


def isic4_5():
    d = pd.read_excel(DL + r"\isic4_5.xlsx", sheet_name="ISIC4-5", dtype=str)
    d = d.iloc[:, [1, 2, 4, 5, 6]]
    d.columns = ["isic4", "isic4_name", "isic5", "isic5_name", "change"]
    d["isic4"] = d.isic4.str.zfill(4)
    d["isic5"] = d.isic5.str.zfill(4)
    return d


def isic4_nace2():
    d = pd.read_csv(CONC + r"\ISIC_Rev4__to__NACE_Rev2.csv", dtype=str)
    d = d[d.source_code.str.fullmatch(r"\d{4}")]
    return d[["source_code", "target_code"]].rename(columns={"source_code": "isic4", "target_code": "nace2"})


def cpa22():
    rows = []
    with open(DN + r"\CPA2_2.tsv", encoding="utf-8") as f:
        for line in f:
            code, name = line.rstrip("\n").split("\t", 1)
            m = re.fullmatch(r"CPA_([A-V])(\d+)", code)
            if not m:
                continue
            dg = m.group(2)
            if len(dg) == 6:
                rows.append((dg[:2] + "." + dg[2:4] + "." + dg[4:], name, 6))
            elif len(dg) == 5:
                rows.append((dg[:2] + "." + dg[2:4] + "." + dg[4:], name, 5))
            elif len(dg) == 4:
                rows.append((dg[:2] + "." + dg[2:], name, 4))
            elif len(dg) == 3:
                rows.append((dg[:2] + "." + dg[2:], name, 3))
            elif len(dg) == 2:
                rows.append((dg, name, 2))
    return pd.DataFrame(rows, columns=["code", "name", "level"]).drop_duplicates("code")


def cpa22_hs():
    d = pd.read_csv(DN + r"\cpa22_hs2022.tsv", sep="\t", dtype=str, encoding="latin-1")
    d = d[["CPA_Ver2_2_Code", "HS_2022_Code"]].dropna()
    d.columns = ["cpa", "hs"]
    d["hs6"] = d.hs.str.replace(".", "", regex=False).str[:6]
    return d


def cpc21():
    d = pd.read_csv(CONC + r"\STRUCTURE_CPC_2.1.csv", dtype=str)
    return d


def cpc21_hs():
    d = pd.read_csv(CONC + r"\CPC_2.1__to__HS_2017.csv", dtype=str)
    d["hs6"] = d.target_code.str.replace(".", "", regex=False).str[:6]
    return d[["source_code", "hs6"]].rename(columns={"source_code": "cpc"})


def exio3():
    p = pd.read_excel(CLS + r"\exio3class.xlsx", sheet_name="products")
    i = pd.read_excel(CLS + r"\exio3class.xlsx", sheet_name="industries")
    return p[["CodeNr", "Name"]], i[["CodeNr", "Name"]]


def conc(path):
    return pd.read_csv(EC + "\\" + path, dtype=str)

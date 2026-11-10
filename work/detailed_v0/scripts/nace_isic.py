"""Map NACE 2.1 classes to ISIC 5 classes and ISIC 4 classes."""
import difflib
from refs import *


def build():
    n = nace21()
    nc = n[n.level == "class"].copy()
    gname = {r.code: r.name for r in n[n.level == "group"].itertuples()}
    i5 = isic5()
    i5c = i5[i5.code.str.fullmatch(r"\d{4}")]
    i5name = dict(zip(i5c.code, i5c.name))
    nm5 = {norm(v): k for k, v in i5name.items()}
    c = nace21_nace2()
    i4n = isic4_nace2()
    i45 = isic4_5()
    n2i4 = i4n.groupby("nace2").isic4.apply(set).to_dict()
    i4i5 = i45.groupby("isic4").isic5.apply(set).to_dict()
    i5i4 = i45.groupby("isic5").isic4.apply(set).to_dict()
    n21n2 = c.groupby("NACE21_Code").NACE2_Code.apply(list).to_dict()
    out = []
    for r in nc.itertuples():
        s = set()
        for n2 in n21n2.get(r.code, []):
            for i4 in n2i4.get(n2, ()):
                s |= i4i5.get(i4, set())
        grp3 = r.code[:2] + r.code[3]
        same = [k for k in i5name if k[:3] == grp3]
        basis, i5 = "", ""
        if norm(r.name) in nm5:
            i5, basis = nm5[norm(r.name)], "name"
        elif norm(gname[r.code[:4]]) in nm5:
            i5, basis = nm5[norm(gname[r.code[:4]])], "group_name"
        elif len(same) == 1:
            i5, basis = same[0], "group_unique"
        else:
            cc = [k for k in same if k in s] or same or sorted(s)
            if len(cc) == 1:
                i5, basis = cc[0], "chain"
            elif cc:
                sc = sorted(cc, key=lambda k: -difflib.SequenceMatcher(None, r.name.lower(), i5name[k].lower()).ratio())
                i5, basis = sc[0], "fuzzy:" + "|".join(sc)
        # ISIC4 classes: official Rev4->Rev5 rows for this ISIC5 class, restricted
        # to those that also reach this NACE class through NACE2 where possible
        i4all = i5i4.get(i5, set())
        i4n21 = set()
        for n2 in n21n2.get(r.code, []):
            i4n21 |= n2i4.get(n2, set())
        i4 = sorted(i4all & i4n21) or sorted(i4all)
        out.append(dict(nace21_class=r.code, nace21_name=r.name, section=r.section,
                        isic5_class=i5, isic5_name=i5name.get(i5, ""), isic5_basis=basis,
                        isic4_classes=";".join(i4), nace2_classes=";".join(n21n2.get(r.code, []))))
    return pd.DataFrame(out)


if __name__ == "__main__":
    d = build()
    print(d.isic5_basis.str.split(":").str[0].value_counts())
    f = d[d.isic5_basis.str.startswith("fuzzy")]
    for r in f.itertuples():
        print(r.nace21_class, r.nace21_name[:45], "->", r.isic5_class, r.isic5_name[:45], r.isic5_basis[6:])
    print(d.isic5_class.nunique(), (d.isic5_class == "").sum())

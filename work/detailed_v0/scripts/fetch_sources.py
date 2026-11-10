"""Fetch the external datasets used to split detailed EXIOBASE classification leaves.

Datasets (all stored under D:/data/00-sources/<dataset>/v2026/, delivered files unchanged):
  eurostat/rail_pa_total, eurostat/rail_go_total   rail passenger-km / tonne-km (SDMX 2.1 TSV.gz)
  eurostat/sts_copr_a                              production in construction, F_CC1 / F_CC2
  eurostat/sbs_ovw_act, sbs_na_con_r2, sbs_na_1a_se_r2   SBS at NACE class level
  itf/                                             OECD/ITF transport statistics (OECD SDMX, CSV)
  cso_ireland_datacentres/                         CSO MEC02 data-centre metered electricity

Re-runnable: files that already exist are skipped. A sha256sums.txt is written per dataset
folder once, if absent. Downloaded files are only saved, never opened or executed here.
Usage: python fetch_sources.py [--root D:/data/00-sources] [--only NAME ...]
"""
import argparse
import hashlib
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

VINTAGE = "v2026"
UA = "Mozilla/5.0 (EXIOBASE-class fetch_sources.py)"
ES = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data/{c}?format=TSV&compressed=true"
OECD = "https://sdmx.oecd.org/public/rest/data/OECD.ITF,{f},1.0/all?dimensionAtObservation=AllDimensions"
OECD_DSD = "https://sdmx.oecd.org/public/rest/dataflow/OECD.ITF/{f}?references=all"
CSV_ACCEPT = "application/vnd.sdmx.data+csv; charset=utf-8; labels=both"
CSO = "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset/{t}/CSV/1.0/en"

# (dataset folder under root, local filename, url, extra headers)
JOBS = []
for code in ["rail_pa_total", "rail_go_total", "sts_copr_a", "sbs_ovw_act", "sbs_na_con_r2", "sbs_na_1a_se_r2"]:
    JOBS.append((f"eurostat/{code}", f"{code}.tsv.gz", ES.format(c=code), {}))
# DF_TRENDSPASS (annual passenger) returns 404 NoRecordsFound as of 2026-11-10; kept so a re-run picks it up.
for flow in ["DSD_TRENDS@DF_TRENDSFREIGHT", "DSD_TRENDS@DF_TRENDSPASS", "DSD_ST@DF_STPASS", "DSD_ST@DF_STFREIGHT"]:
    name = flow.split("@")[1].lower()
    JOBS.append(("itf", f"itf_{name}.csv", OECD.format(f=flow), {"Accept": CSV_ACCEPT}))
    JOBS.append(("itf", f"itf_{name}_structure.xml", OECD_DSD.format(f=flow), {}))
JOBS.append(("cso_ireland_datacentres", "MEC02.csv", CSO.format(t="MEC02"), {}))


def fetch(url, dest, headers, tries=3):
    req = urllib.request.Request(url, headers={"User-Agent": UA, **headers})
    for i in range(tries):
        try:
            with urllib.request.urlopen(req, timeout=600) as r, open(dest.with_suffix(dest.suffix + ".part"), "wb") as f:
                while chunk := r.read(1 << 20):
                    f.write(chunk)
            dest.with_suffix(dest.suffix + ".part").replace(dest)
            return True
        except urllib.error.HTTPError as e:
            print(f"  HTTP {e.code} for {url}")
            if e.code == 404:
                return False
        except Exception as e:  # network error: retry
            print(f"  error {e}; retry {i + 1}")
        time.sleep(5)
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="D:/data/00-sources")
    ap.add_argument("--only", nargs="*")
    a = ap.parse_args()
    root = Path(a.root)
    touched = set()
    for ds, fname, url, hdr in JOBS:
        if a.only and not any(o in ds or o in fname for o in a.only):
            continue
        d = root / ds / VINTAGE
        d.mkdir(parents=True, exist_ok=True)
        touched.add(d)
        dest = d / fname
        if dest.exists():
            print("skip", dest)
            continue
        print("get ", dest)
        if fetch(url, dest, hdr):
            print(f"  ok {dest.stat().st_size} bytes")
        else:
            print("  FAILED or not found (no file written)")
    for d in touched:
        sums = d / "sha256sums.txt"
        if sums.exists():
            continue
        lines = []
        for p in sorted(d.iterdir()):
            if p.is_file() and p.name not in ("README.md", "sha256sums.txt"):
                lines.append(f"{hashlib.sha256(p.read_bytes()).hexdigest()}  {p.name}")
        sums.write_text("\n".join(lines) + "\n", newline="\n")
        print("wrote", sums)


if __name__ == "__main__":
    sys.exit(main())

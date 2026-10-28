"""Download one NHANES cycle (public CDC files) and store column-trimmed csv.gz copies for eval_nhanes.py.

python3 eval/realdata/fetch_nhanes_cycle.py G      # 2011-2012
Letters: D=2005 E=2007 F=2009 G=2011 H=2013 I=2015 J=2017.  Files missing in a cycle are skipped (eval_nhanes tolerates it).
"""
import sys, os, io, urllib.request, pandas as pd
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
YEAR = {"D": "2005", "E": "2007", "F": "2009", "G": "2011", "H": "2013", "I": "2015", "J": "2017"}
KEEP_EXTRA = {"DEMO": ["RIAGENDR", "RIDAGEYR", "RIDEXPRG"], "DIQ": ["DIQ010"], "KIQ_U": ["KIQ022"], "MCQ": ["MCQ160B", "MCQ160F", "MCQ220", "MCQ160L"]}
FILES = ["DEMO", "BIOPRO", "CBC", "GHB", "GLU", "ALB_CR", "FERTIN", "TCHOL", "HDL", "TRIGLY", "FETIB", "DIQ", "KIQ_U", "MCQ"]
import re
MAP_SRC = open(os.path.join(HERE, "eval_nhanes.py")).read()
MAP_KEYS = set(re.findall(r'"([A-Z0-9_]+)":\s*\("', MAP_SRC.split("MAP = {")[1].split("\n}")[0]))

def main(letter):
    year = YEAR[letter]; out = os.path.join(HERE, f"nhanes_{year}"); os.makedirs(out, exist_ok=True)
    for f in FILES:
        name = f"{f}_{letter}"; dst = os.path.join(out, name + ".csv.gz")
        if os.path.exists(dst): print("have", name); continue
        url = f"https://wwwn.cdc.gov/Nchs/Data/Nhanes/Public/{year}/DataFiles/{name}.xpt"
        try:
            raw = urllib.request.urlopen(url, timeout=180).read()
        except Exception as e:
            print("MISSING", name, str(e)[:60]); continue
        df = pd.read_sas(io.BytesIO(raw), format="xport")
        keep = ["SEQN"] + [c for c in df.columns if c in MAP_KEYS or c in KEEP_EXTRA.get(f, [])]
        df[keep].to_csv(dst, index=False, compression="gzip")
        print("ok", name, df.shape, "->", len(keep), "cols", os.path.getsize(dst) // 1024, "KB")

if __name__ == "__main__":
    for L in sys.argv[1:]: main(L)

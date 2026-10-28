"""Read the 290 LabPanel-Check panels with a local llama.cpp server (OpenAI-compatible endpoint) under PROTOCOL_OPEN_MODEL.md.

usage: python3 run_open_model.py --url http://127.0.0.1:8080 --out reads_qwen25_1p5b.json [--only REF] [--resume]
"""
import argparse, gzip, json, os, re, sys, time, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
PANELS = os.path.join(HERE, "..", "panels.json.gz")
P1 = ('You are a clinical laboratory medicine expert. Given the following laboratory panel of {who}, list the most likely '
      'diagnoses or clinically important laboratory syndromes this panel supports. Return ONLY JSON of the form '
      '{{"diagnoses":[{{"name":"...","probability":0.0-1.0}}]}} with at most 10 entries, ordered by probability. '
      'Do not include explanations. Patient: {age}-year-old {sex}. Panel: {panel}')
WHO_ICU = "an adult ICU patient (first 24 h of admission)"
WHO_COMMUNITY = "an adult from a community health survey"
SEED = 20261028


def fmt_panel(rec):
    return ", ".join(f"{x['analyte'].replace('_', ' ')} {x['value']} {x.get('unit', '')}".strip() for x in rec["panel"])


def ask(url, prompt, max_tokens=400):
    body = {"messages": [{"role": "user", "content": prompt}], "temperature": 0, "top_k": 1, "seed": SEED,
            "max_tokens": max_tokens, "stream": False}
    req = urllib.request.Request(url.rstrip("/") + "/v1/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=900) as r:
        return json.load(r)["choices"][0]["message"]["content"]


def parse(reply):
    m = re.search(r"\{.*\}", reply, re.S)
    if not m:
        return None
    txt = m.group(0)
    for cand in (txt, txt.replace("'", '"')):
        try:
            obj = json.loads(cand)
            break
        except Exception:
            obj = None
    if obj is None:
        # salvage a truncated list: cut at the last complete entry
        cut = txt.rfind("}")
        try:
            obj = json.loads(txt[:cut + 1] + "]}")
        except Exception:
            return None
    items = obj.get("diagnoses") if isinstance(obj, dict) else obj
    if not isinstance(items, list):
        return None
    out = []
    for it in items:
        if isinstance(it, dict) and it.get("name"):
            try:
                p = float(it.get("probability", 0.5))
            except Exception:
                p = 0.5
            out.append({"name": str(it["name"]), "probability": min(1.0, max(0.0, p))})
        elif isinstance(it, str):
            out.append({"name": it, "probability": 0.5})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8080")
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", default=None, help="prefix filter, e.g. REF")
    ap.add_argument("--resume", action="store_true")
    a = ap.parse_args()
    panels = json.load(gzip.open(PANELS, "rt"))
    ids = [k for k in panels if (a.only is None or k.startswith(a.only + ":"))]
    reads, log = {}, {}
    if a.resume and os.path.exists(a.out):
        reads = json.load(open(a.out))
        lp = a.out.replace(".json", "_raw.json")
        log = json.load(open(lp)) if os.path.exists(lp) else {}
    t0 = time.time()
    for n, pid in enumerate(ids, 1):
        if pid in reads:
            continue
        rec = panels[pid]
        who = WHO_COMMUNITY if pid.startswith("P6:") else WHO_ICU
        prompt = P1.format(who=who, age=rec["age"], sex=rec["sex"], panel=fmt_panel(rec))
        reply = ask(a.url, prompt)
        entries = parse(reply)
        retried = False
        if entries is None:
            retried = True
            reply = ask(a.url, prompt)
            entries = parse(reply)
        reads[pid] = entries if entries is not None else []
        log[pid] = {"reply": reply, "parsed": entries is not None, "retried": retried}
        if n % 5 == 0 or n == len(ids):
            json.dump(reads, open(a.out, "w"), indent=0)
            json.dump(log, open(a.out.replace(".json", "_raw.json"), "w"), indent=0)
            el = time.time() - t0
            print(f"{n}/{len(ids)} {pid} parsed={entries is not None} elapsed={el/60:.1f} min", flush=True)
    json.dump(reads, open(a.out, "w"), indent=0)
    json.dump(log, open(a.out.replace(".json", "_raw.json"), "w"), indent=0)
    print("done", len(reads), "unparsable", sum(1 for v in log.values() if not v["parsed"]))


if __name__ == "__main__":
    main()

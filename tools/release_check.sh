#!/usr/bin/env bash
# Pre-release gate for the Paper 1 deposit. Read-only; prints PASS/FAIL per check and exits non-zero on any FAIL.
set -u
cd "$(dirname "$0")/.."
fail=0
ok()   { printf 'PASS  %s\n' "$1"; }
bad()  { printf 'FAIL  %s\n' "$1"; fail=1; }

[ -z "$(git status --porcelain)" ] && ok "working tree clean" || bad "uncommitted changes present"
for t in engine-v7-frozen registry-15.3.0 audit-study paper1-R8-cmpb; do
  git rev-parse -q --verify "refs/tags/$t" >/dev/null && ok "tag $t" || bad "tag $t missing"
done
python3 - <<'EOF' && ok ".zenodo.json and CITATION.cff parse" || bad ".zenodo.json / CITATION.cff"
import json; json.load(open('.zenodo.json'))
t=open('CITATION.cff').read(); assert 'cff-version' in t and 'orcid' in t
EOF
if git ls-files -z | xargs -0 du -b | awk '$1>5000000{print; f=1} END{exit f}'; then ok "no tracked file > 5 MB"; else bad "large tracked file(s) above"; fi
if git ls-files | grep -Eq '(^|/)(\.env|.*\.pem|.*\.key|id_rsa.*|\.netrc)$'; then bad "credential-like file tracked"; else ok "no credential-like files"; fi
if git grep -Il -E 'AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{36}|sk-[A-Za-z0-9]{32,}' -- . >/dev/null; then bad "token-like string in tracked text"; else ok "no token-like strings"; fi
for m in FREEZE_*; do [ -f "$m" ] || continue; done
if [ -x reproduce.sh ] || [ -f reproduce.sh ]; then ok "reproduce.sh present"; else bad "reproduce.sh missing"; fi
for f in LICENSE LICENSE-DATA.md README.md README_REPRODUCE.md REPRODUCTION_LOG.md INDEPENDENT_REPRODUCTION.md \
         eval/labpanel_check/MANIFEST.sha256 eval/audit/human_audit/SHA256SUMS; do
  [ -f "$f" ] && ok "file $f" || bad "file $f missing"
done
(cd eval/labpanel_check && sha256sum -c --quiet MANIFEST.sha256) && ok "LabPanel-Check manifest" || bad "LabPanel-Check manifest mismatch"
(cd eval/audit/human_audit && sha256sum -c --quiet SHA256SUMS) && ok "human-audit SHA256SUMS" || bad "human-audit SHA256SUMS mismatch"
if git grep -n -E 'OSF_REGISTRATION_TEXT|TODO|FIXME|XXX' -- '*.md' '*.py' >/dev/null; then bad "stale marker (see git grep OSF_REGISTRATION_TEXT|TODO|FIXME|XXX)"; else ok "no stale markers"; fi
find . -name __pycache__ -not -path './.git/*' | grep -q . && bad "__pycache__ present (delete before tagging)" || ok "no __pycache__"
printf 'HEAD %s  tracked files %s  pack %s\n' "$(git rev-parse --short HEAD)" "$(git ls-files | wc -l)" "$(git count-objects -vH | awk '/size-pack/{print $2$3}')"
exit $fail

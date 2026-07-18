"""OAuth flow e2e: DCR with redirect allowlist, consent, PKCE, full-role bearer,
refresh, plus the two hardening guarantees — unregistered redirects are refused
BEFORE credentials are solicited, and the consent page is XSS-escaped.

Run against a fresh local server (see tests/e2e.py header for setup).
"""
import base64
import hashlib
import json
import secrets
import urllib.error
import urllib.parse
import urllib.request

B = "http://127.0.0.1:8787"


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


opener = urllib.request.build_opener(NoRedirect)

verifier = secrets.token_urlsafe(40)
challenge = base64.urlsafe_b64encode(
    hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
CB = "http://localhost/cb"

# --- register with allowlist
reg = json.load(urllib.request.urlopen(urllib.request.Request(
    f"{B}/oauth/register", method="POST",
    data=json.dumps({"redirect_uris": [CB, "ftp://evil.example/x"]}).encode())))
cid = reg["client_id"]
assert reg["redirect_uris"] == [CB], reg  # non-https/loopback URI was dropped

# register without redirect_uris -> refused
try:
    urllib.request.urlopen(urllib.request.Request(
        f"{B}/oauth/register", method="POST", data=b"{}"))
    raise SystemExit("register without redirect_uris should fail")
except urllib.error.HTTPError as e:
    assert e.code == 400

# --- authorize GET: unregistered redirect refused BEFORE consent
qs = urllib.parse.urlencode({"client_id": cid, "redirect_uri": "https://evil.example/cb",
                             "state": "x", "code_challenge": challenge})
try:
    urllib.request.urlopen(f"{B}/oauth/authorize?{qs}")
    raise SystemExit("unregistered redirect should be refused")
except urllib.error.HTTPError as e:
    assert e.code == 400

# --- authorize GET: XSS attempt arrives escaped
qs = urllib.parse.urlencode({"client_id": cid, "redirect_uri": CB,
                             "state": '"><script>steal()</script>',
                             "code_challenge": challenge})
page = urllib.request.urlopen(f"{B}/oauth/authorize?{qs}").read().decode()
assert "<script>steal()" not in page and "&lt;script&gt;" in page

# --- consent POST (valid) -> 302 with code
data = urllib.parse.urlencode({"client_id": cid, "redirect_uri": CB, "state": "xyz",
                               "code_challenge": challenge, "key": "k-luna"}).encode()
try:
    opener.open(urllib.request.Request(f"{B}/oauth/authorize", data=data, method="POST"))
    raise SystemExit("expected 302")
except urllib.error.HTTPError as e:
    assert e.code == 302, e.code
    code = urllib.parse.parse_qs(urllib.parse.urlparse(e.headers["Location"]).query)["code"][0]

# --- token: wrong PKCE refused, right verifier + client mints, wrong client refused
bad = urllib.parse.urlencode({"grant_type": "authorization_code", "code": code,
                              "code_verifier": "WRONG", "redirect_uri": CB,
                              "client_id": cid}).encode()
try:
    urllib.request.urlopen(urllib.request.Request(f"{B}/oauth/token", data=bad, method="POST"))
    raise SystemExit("bad PKCE should fail")
except urllib.error.HTTPError as e:
    assert e.code == 400

wrongc = urllib.parse.urlencode({"grant_type": "authorization_code", "code": code,
                                 "code_verifier": verifier, "redirect_uri": CB,
                                 "client_id": "sb-someoneelse"}).encode()
try:
    urllib.request.urlopen(urllib.request.Request(f"{B}/oauth/token", data=wrongc, method="POST"))
    raise SystemExit("client mismatch should fail")
except urllib.error.HTTPError as e:
    assert e.code == 400

good = urllib.parse.urlencode({"grant_type": "authorization_code", "code": code,
                               "code_verifier": verifier, "redirect_uri": CB,
                               "client_id": cid}).encode()
tok = json.load(urllib.request.urlopen(urllib.request.Request(
    f"{B}/oauth/token", data=good, method="POST")))
assert tok["access_token"].startswith("sbt_")

# --- bearer token exercises FULL author power
def mcp(name, args):
    req = urllib.request.Request(f"{B}/mcp", method="POST",
        headers={"Authorization": f"Bearer {tok['access_token']}",
                 "Content-Type": "application/json",
                 "Accept": "application/json, text/event-stream"},
        data=json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                         "params": {"name": name, "arguments": args}}).encode())
    j = json.load(urllib.request.urlopen(req))["result"]
    assert not j.get("isError"), j
    sc = j.get("structuredContent")
    return (sc.get("result", sc) if isinstance(sc, dict) else sc) if sc is not None \
        else json.loads("".join(c["text"] for c in j["content"]))


p = mcp("project_create", {"name": "OAUTH-PROBE"})
mcp("project_delete", {"project_id": p["id"]})

# --- refresh
rf = urllib.parse.urlencode({"grant_type": "refresh_token",
                             "refresh_token": tok["refresh_token"]}).encode()
tok2 = json.load(urllib.request.urlopen(urllib.request.Request(
    f"{B}/oauth/token", data=rf, method="POST")))
assert tok2["access_token"].startswith("sbt_")

print("OAUTH HARDENED OK: allowlisted redirects, pre-consent refusal, XSS-escaped, "
      "PKCE + client binding, full-role bearer, refresh")

import base64
import requests
from api_helpers import BASE_URL, TIMEOUT
from api_helpers import signup_fresh_org


def post_login(email, password):
    return requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": password},
        timeout=TIMEOUT,
    )

def test_tc43_forged_token_impersonates_another_user():
    """SEC-01: token is just base64("user:<id>") - anyone can forge it."""
    fake_token = base64.b64encode(b"user:1").decode()  # pretend to be user_id 1
    headers = {"Authorization": f"Bearer {fake_token}"}
    resp = requests.get(f"{BASE_URL}/orgs/1/projects", headers=headers, timeout=TIMEOUT)
    assert resp.status_code in (401, 403), (
        f"BUG-06: forged token worked (HTTP {resp.status_code}) - token is not signed/verified"
    )


def test_tc44_no_login_no_access():
    """SEC-02: no Authorization header at all."""
    resp = requests.get(f"{BASE_URL}/orgs/1/projects", timeout=TIMEOUT)
    assert resp.status_code == 401


def test_tc45_sql_injection_in_login_email():
    """SEC-03: classic SQLi payload in the email field must not bypass login."""
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "' OR '1'='1", "password": "anything"},
        timeout=TIMEOUT,
    )
    assert resp.status_code in (400, 401), (
        f"BUG-07: SQL-injection-like input returned HTTP {resp.status_code} instead of a login failure"
    )


def test_tc46_malformed_login_body_no_stack_trace():
    """SEC-04: sending garbage must not leak an internal error/stack trace."""
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        data="not-json-at-all",
        headers={"Content-Type": "application/json"},
        timeout=TIMEOUT,
    )
    assert resp.status_code in (400, 401, 415), (
        f"Unexpected status for malformed body: {resp.status_code}"
    )
    lowered = resp.text.lower()
    assert "at object." not in lowered and "node_modules" not in lowered, (
        "BUG-08: raw stack trace leaked in the error response"
    )

def test_tc100_login_is_rate_limited_after_repeated_failures():
    """SEC-01: many wrong passwords in a row must trigger a lockout / rate limit."""
    user = signup_fresh_org("brute")
    statuses = [post_login(user["email"], "wrong-password").status_code for _ in range(30)]

    assert any(code in (423, 429) for code in statuses), (
        f"BUG-08: 30 wrong-password attempts in a row were never blocked "
        f"(status codes seen: {sorted(set(statuses))}, expected 429 or 423 at some point)"
    )
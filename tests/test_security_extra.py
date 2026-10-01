"""
Additional Security tests: TC66 - TC69
"""
import requests
from api_helpers import BASE_URL, TIMEOUT, PASSWORD


def test_tc66_xss_payload_in_project_name_does_not_crash(acme_owner):
    """SEC-05: a script-tag as a project name must not crash the server."""
    resp = requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects",
        headers=acme_owner["headers"],
        json={"name": "<script>alert(1)</script>"},
        timeout=TIMEOUT,
    )
    assert resp.status_code in (200, 201), f"Unexpected status: {resp.status_code}"


def test_tc67_password_hash_never_exposed_in_members_list(acme_owner):
    """SEC-06: members list response must never include password fields."""
    resp = requests.get(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/members",
        headers=acme_owner["headers"], timeout=TIMEOUT,
    )
    assert resp.status_code == 200
    assert "password" not in resp.text.lower(), (
        "BUG-13: password field leaked in members list response"
    )


def test_tc68_no_account_lockout_after_repeated_failed_logins(acme_owner):
    """SEC-07: observation test - does repeated wrong-password login get blocked?"""
    for _ in range(8):
        requests.post(
            f"{BASE_URL}/auth/login",
            json={"email": acme_owner["email"], "password": "wrong-password"},
            timeout=TIMEOUT,
        )
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": acme_owner["email"], "password": PASSWORD},
        timeout=TIMEOUT,
    )
    print("Status after 8 failed attempts then correct password:", resp.status_code)
    if resp.status_code == 200:
        print("OBSERVATION: no lockout/rate-limit after repeated failed logins (brute-force risk)")


def test_tc69_security_headers_present():
    """SEC-08: basic security headers should be present."""
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "owner@acme.test", "password": PASSWORD},
        timeout=TIMEOUT,
    )
    headers_lower = {k.lower() for k in resp.headers.keys()}
    missing = [h for h in ("x-content-type-options", "x-frame-options") if h not in headers_lower]
    assert not missing, f"BUG-14: missing security headers: {missing}"
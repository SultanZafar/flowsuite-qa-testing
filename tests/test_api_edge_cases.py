"""
Extra API edge-case tests: 
"""
import requests
from api_helpers import BASE_URL, TIMEOUT


def test_tc50_invalid_org_id_does_not_crash(acme_owner):
    resp = requests.get(f"{BASE_URL}/orgs/not-a-number/projects", headers=acme_owner["headers"], timeout=TIMEOUT)
    assert resp.status_code in (400, 404), f"Expected 400/404, got {resp.status_code} (server may have crashed)"


def test_tc51_nonexistent_project_returns_404(acme_owner):
    resp = requests.get(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects/999999/tasks",
        headers=acme_owner["headers"], timeout=TIMEOUT,
    )
    assert resp.status_code == 404


def test_tc52_create_project_missing_name_field(acme_owner):
    resp = requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects",
        headers=acme_owner["headers"], json={}, timeout=TIMEOUT,
    )
    assert resp.status_code in (400, 422), f"Expected 400/422, got {resp.status_code}"


def test_tc53_wrong_http_method_rejected(acme_owner):
    resp = requests.delete(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects",
        headers=acme_owner["headers"], timeout=TIMEOUT,
    )
    assert resp.status_code in (404, 405)


def test_tc54_very_long_project_name_does_not_crash(acme_owner):
    long_name = "A" * 5000
    resp = requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects",
        headers=acme_owner["headers"], json={"name": long_name}, timeout=TIMEOUT,
    )
    assert resp.status_code in (200, 201, 400, 413, 422), f"Server may have crashed: {resp.status_code}"


def test_tc55_invalid_role_value_rejected(acme_owner):
    from api_helpers import invite
    resp, _ = invite(acme_owner, acme_owner["org_id"], "SUPERADMIN")
    assert resp.status_code in (400, 409, 422), (
        f"BUG-09: invalid role 'SUPERADMIN' was accepted (HTTP {resp.status_code})"
    )
"""
Multi-Tenancy isolation tests: TC35 - TC42

The logged-in user belongs to ACME and tries to reach GLOBEX's data.
Each test asserts the SECURE behaviour. Where the app has a bug, the test
FAILS on purpose - that failure is your bug evidence.
"""
import requests

from api_helpers import BASE_URL, TIMEOUT

BLOCKED = (401, 403)


def get(user, path):
    return requests.get(f"{BASE_URL}{path}", headers=user["headers"], timeout=TIMEOUT)


def test_control_acme_can_read_own_projects(acme_owner):
    """CONTROL: if this fails, the setup is broken - ignore every result below."""
    resp = get(acme_owner, f"/orgs/{acme_owner['org_id']}/projects")
    assert resp.status_code == 200


def test_tc35_cannot_view_other_orgs_projects(acme_owner, globex_owner):
    """MT-01: Acme user reads Globex's project list."""
    resp = get(acme_owner, f"/orgs/{globex_owner['org_id']}/projects")
    assert resp.status_code in BLOCKED, (
        f"BUG-01: Acme user got HTTP {resp.status_code} for Globex projects (expected 403)"
    )


def test_tc36_cannot_view_other_orgs_tasks(acme_owner, globex_owner, globex_project_id):
    """MT-02: Acme user reads the tasks of a Globex project."""
    resp = get(acme_owner, f"/orgs/{globex_owner['org_id']}/projects/{globex_project_id}/tasks")
    assert resp.status_code in BLOCKED, (
        f"BUG-01: Acme user got HTTP {resp.status_code} for Globex tasks (expected 403)"
    )


def test_tc37_cannot_view_other_orgs_members(acme_owner, globex_owner):
    """MT-03: Acme user reads Globex's member list."""
    resp = get(acme_owner, f"/orgs/{globex_owner['org_id']}/members")
    assert resp.status_code in BLOCKED, (
        f"BUG-01: Acme user got HTTP {resp.status_code} for Globex members (expected 403)"
    )


def test_tc38_cannot_view_other_orgs_subscription(acme_owner, globex_owner):
    """MT-04: Acme user reads Globex's subscription/plan."""
    resp = get(acme_owner, f"/orgs/{globex_owner['org_id']}/subscription")
    assert resp.status_code in BLOCKED, (
        f"BUG-01: Acme user got HTTP {resp.status_code} for Globex subscription (expected 403)"
    )


def test_tc39_cannot_view_other_orgs_invoices(acme_owner, globex_owner):
    """MT-05: Acme user reads Globex's invoices."""
    resp = get(acme_owner, f"/orgs/{globex_owner['org_id']}/invoices")
    assert resp.status_code in BLOCKED, (
        f"BUG-01: Acme user got HTTP {resp.status_code} for Globex invoices (expected 403)"
    )


def test_tc40_cannot_create_project_in_other_org(acme_owner, globex_owner):
    """MT-06: Acme user creates a project inside Globex."""
    resp = requests.post(
        f"{BASE_URL}/orgs/{globex_owner['org_id']}/projects",
        headers=acme_owner["headers"],
        json={"name": "Injected by Acme"},
        timeout=TIMEOUT,
    )
    assert resp.status_code in BLOCKED, (
        f"Acme user created a project in Globex (HTTP {resp.status_code}, expected 403)"
    )


def test_tc41_cannot_assign_task_to_user_from_other_org(acme_owner, globex_owner, acme_project_id):
    """MT-07: Acme task assigned to a Globex user."""
    resp = requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects/{acme_project_id}/tasks",
        headers=acme_owner["headers"],
        json={"title": "Cross-org assignee test", "assigneeId": globex_owner["user_id"]},
        timeout=TIMEOUT,
    )
    assert resp.status_code in (400, 403, 404, 422), (
        f"BUG-05: task was assigned to a user of another org (HTTP {resp.status_code}, expected 400/403)"
    )


def test_tc42_org_list_shows_only_own_orgs(acme_owner):
    """MT-08: the org dropdown data must contain only Acme."""
    resp = get(acme_owner, "/orgs")
    assert resp.status_code == 200
    names = {org["name"] for org in resp.json()["orgs"]}
    assert names == {"Acme Inc"}, f"Acme user can see other orgs: {names}"
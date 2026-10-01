"""Small helper functions shared by the RBAC and Multi-Tenancy tests."""
import uuid

import requests

BASE_URL = "http://localhost:3001/api"
PASSWORD = "password123"
TIMEOUT = 10


def unique_email(prefix="qa"):
    """Random email so repeated test runs never collide with old data."""
    return f"{prefix}-{uuid.uuid4().hex[:8]}@test.local"


def login(email, org_name=None):
    """Log in and return everything a test needs about this user.

    org_name: which of the user's orgs counts as "their" org.
    If None, the first org in the list is used.
    """
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": email, "password": PASSWORD},
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, f"Login failed for {email}: {resp.status_code} {resp.text}"
    data = resp.json()
    headers = {"Authorization": f"Bearer {data['token']}"}

    # This call is also a control: a bad token or header fails here, not silently later.
    orgs_resp = requests.get(f"{BASE_URL}/orgs", headers=headers, timeout=TIMEOUT)
    assert orgs_resp.status_code == 200, (
        f"/orgs failed for {email}: {orgs_resp.status_code} (check the Authorization header)"
    )
    orgs = orgs_resp.json()["orgs"]

    if org_name:
        matches = [o for o in orgs if o["name"] == org_name]
        assert matches, f"{email} is not a member of {org_name}: {[o['name'] for o in orgs]}"
        org = matches[0]
    else:
        org = orgs[0]

    return {
        "email": email,
        "user_id": data["user"]["user_id"],
        "headers": headers,
        "org_id": org["org_id"],
        "orgs": orgs,
    }


def invite(actor, org_id, role, email=None):
    """`actor` invites a brand-new user into org_id with the given role."""
    email = email or unique_email()
    resp = requests.post(
        f"{BASE_URL}/orgs/{org_id}/members/invite",
        headers=actor["headers"],
        json={"name": "QA Tester", "email": email, "role": role},
        timeout=TIMEOUT,
    )
    return resp, email


def list_members(actor, org_id):
    return requests.get(
        f"{BASE_URL}/orgs/{org_id}/members", headers=actor["headers"], timeout=TIMEOUT
    )


def find_member(actor, org_id, email):
    """Return the member dict (user_id, role, ...) with this email, or None."""
    for member in list_members(actor, org_id).json().get("members", []):
        if member["email"] == email:
            return member
    return None


def change_role(actor, org_id, target_user_id, role):
    return requests.patch(
        f"{BASE_URL}/orgs/{org_id}/members/{target_user_id}/role",
        headers=actor["headers"],
        json={"role": role},
        timeout=TIMEOUT,
    )


def first_project_id(actor, org_id):
    projects = requests.get(
        f"{BASE_URL}/orgs/{org_id}/projects", headers=actor["headers"], timeout=TIMEOUT
    ).json()["projects"]
    assert projects, f"No projects found in org {org_id} - was the database reset?"
    return projects[-1]["project_id"]
def signup_fresh_org(prefix="qa"):
    """Create a brand-new user + brand-new organization (FREE plan, trialing)."""
    email = unique_email(prefix)
    resp = requests.post(
        f"{BASE_URL}/auth/signup",
        json={
            "name": "QA Fresh Owner",
            "email": email,
            "password": PASSWORD,
            "orgName": f"QA Org {uuid.uuid4().hex[:6]}",
        },
        timeout=TIMEOUT,
    )
    assert resp.status_code == 201, f"Signup failed: {resp.status_code} {resp.text}"
    data = resp.json()
    return {
        "email": email,
        "user_id": data["user"]["user_id"],
        "headers": {"Authorization": f"Bearer {data['token']}"},
        "org_id": data["orgId"],
    }


def create_project(actor, org_id, name=None):
    return requests.post(
        f"{BASE_URL}/orgs/{org_id}/projects",
        headers=actor["headers"],
        json={"name": name or f"QA Project {uuid.uuid4().hex[:6]}"},
        timeout=TIMEOUT,
    )


def upgrade_plan(actor, org_id, plan):
    return requests.post(
        f"{BASE_URL}/orgs/{org_id}/subscription/upgrade",
        headers=actor["headers"],
        json={"plan": plan},
        timeout=TIMEOUT,
    )


def cancel_subscription(actor, org_id):
    return requests.post(
        f"{BASE_URL}/orgs/{org_id}/subscription/cancel",
        headers=actor["headers"],
        timeout=TIMEOUT,
    )


def get_subscription(actor, org_id):
    return requests.get(
        f"{BASE_URL}/orgs/{org_id}/subscription", headers=actor["headers"], timeout=TIMEOUT
    )


def get_invoices(actor, org_id):
    return requests.get(
        f"{BASE_URL}/orgs/{org_id}/invoices", headers=actor["headers"], timeout=TIMEOUT
    )


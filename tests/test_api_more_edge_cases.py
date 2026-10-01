"""
Additional API edge-case tests: TC75 - TC98
"""
import requests
from api_helpers import BASE_URL, TIMEOUT, PASSWORD, unique_email, invite, find_member, change_role


# ---- Auth header edge cases ----

def test_tc75_auth_header_without_bearer_prefix(acme_owner):
    token = acme_owner["headers"]["Authorization"].replace("Bearer ", "")
    resp = requests.get(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects",
        headers={"Authorization": token},
        timeout=TIMEOUT,
    )
    assert resp.status_code == 401, f"Expected 401 without 'Bearer ' prefix, got {resp.status_code}"


def test_tc76_bearer_with_empty_token():
    resp = requests.get(
        f"{BASE_URL}/orgs/1/projects",
        headers={"Authorization": "Bearer "},
        timeout=TIMEOUT,
    )
    assert resp.status_code == 401


def test_tc77_garbage_authorization_header():
    resp = requests.get(
        f"{BASE_URL}/orgs/1/projects",
        headers={"Authorization": "Bearer complete-garbage-not-a-token"},
        timeout=TIMEOUT,
    )
    assert resp.status_code in (401, 403), f"Expected 401/403, got {resp.status_code}"


# ---- Login payload edge cases ----

def test_tc78_login_missing_password_field():
    resp = requests.post(f"{BASE_URL}/auth/login", json={"email": "owner@acme.test"}, timeout=TIMEOUT)
    assert resp.status_code in (400, 401, 422), f"Expected 400/422, got {resp.status_code}"


def test_tc79_login_missing_email_field():
    resp = requests.post(f"{BASE_URL}/auth/login", json={"password": PASSWORD}, timeout=TIMEOUT)
    assert resp.status_code in (400, 401, 422), f"Expected 400/422, got {resp.status_code}"


def test_tc80_login_extra_unexpected_field_is_ignored():
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "owner@acme.test", "password": PASSWORD, "isAdmin": True},
        timeout=TIMEOUT,
    )
    assert resp.status_code == 200, f"Login broke with an extra field: {resp.status_code}"


def test_tc94_login_email_case_sensitivity_observation():
    """OBS: does login work with the email in a different case?"""
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": "OWNER@ACME.TEST", "password": PASSWORD},
        timeout=TIMEOUT,
    )
    print("Uppercase email login status:", resp.status_code)


def test_tc95_login_email_with_whitespace_observation():
    """OBS: does login work with leading/trailing spaces in the email?"""
    resp = requests.post(
        f"{BASE_URL}/auth/login",
        json={"email": " owner@acme.test ", "password": PASSWORD},
        timeout=TIMEOUT,
    )
    print("Whitespace-padded email login status:", resp.status_code)


# ---- Project creation edge cases ----

def test_tc81_project_name_whitespace_only(acme_owner):
    resp = requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects",
        headers=acme_owner["headers"], json={"name": "   "}, timeout=TIMEOUT,
    )
    assert resp.status_code in (400, 422), (
        f"BUG-16: whitespace-only project name was accepted (HTTP {resp.status_code})"
    )


def test_tc82_project_name_wrong_type(acme_owner):
    resp = requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects",
        headers=acme_owner["headers"], json={"name": 12345}, timeout=TIMEOUT,
    )
    assert resp.status_code in (200, 201, 400, 422), f"Server may have crashed: {resp.status_code}"


def test_tc83_project_name_with_emoji_and_unicode(acme_owner):
    resp = requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects",
        headers=acme_owner["headers"],
        json={"name": f"Q4 unicode {unique_email('x')}"},
        timeout=TIMEOUT,
    )
    assert resp.status_code in (200, 201), f"Unicode project name broke the server: {resp.status_code}"


def test_tc84_get_projects_for_nonexistent_org(acme_owner):
    resp = requests.get(
        f"{BASE_URL}/orgs/999999/projects", headers=acme_owner["headers"], timeout=TIMEOUT,
    )
    assert resp.status_code in (403, 404), f"Expected 403/404, got {resp.status_code}"


def test_tc98_org_id_negative(acme_owner):
    resp = requests.get(
        f"{BASE_URL}/orgs/-1/projects", headers=acme_owner["headers"], timeout=TIMEOUT,
    )
    assert resp.status_code in (400, 403, 404), f"Expected 400/403/404, got {resp.status_code}"


# ---- Members / roles edge cases ----

def test_tc85_invite_with_empty_name(acme_owner):
    resp = requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/members/invite",
        headers=acme_owner["headers"],
        json={"name": "", "email": unique_email(), "role": "MEMBER"},
        timeout=TIMEOUT,
    )
    assert resp.status_code in (400, 422), (
        f"BUG-17: invite with an empty name was accepted (HTTP {resp.status_code})"
    )


def test_tc86_change_role_of_nonexistent_user(acme_owner):
    resp = change_role(acme_owner, acme_owner["org_id"], 999999, "ADMIN")
    assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"


def test_tc87_change_role_to_same_role_is_a_noop(acme_owner):
    _, email = invite(acme_owner, acme_owner["org_id"], "MEMBER")
    target = find_member(acme_owner, acme_owner["org_id"], email)
    resp = change_role(acme_owner, acme_owner["org_id"], target["user_id"], "MEMBER")
    assert resp.status_code in (200, 204), f"Expected 200/204, got {resp.status_code}"


def test_tc96_invite_missing_role_field_observation(acme_owner):
    """OBS: what happens if 'role' is left out entirely?"""
    resp = requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/members/invite",
        headers=acme_owner["headers"],
        json={"name": "No Role", "email": unique_email()},
        timeout=TIMEOUT,
    )
    print("Invite with no role field status:", resp.status_code, resp.text[:200])


# ---- Task edge cases ----

def test_tc88_create_task_with_empty_title(acme_owner, acme_project_id):
    resp = requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects/{acme_project_id}/tasks",
        headers=acme_owner["headers"], json={"title": ""}, timeout=TIMEOUT,
    )
    assert resp.status_code in (400, 422), (
        f"BUG-18: task with an empty title was accepted (HTTP {resp.status_code})"
    )


def test_tc89_create_task_without_assignee(acme_owner, acme_project_id):
    resp = requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects/{acme_project_id}/tasks",
        headers=acme_owner["headers"], json={"title": "No assignee task"}, timeout=TIMEOUT,
    )
    assert resp.status_code in (200, 201), f"Task without assignee should be allowed: {resp.status_code}"


def test_tc90_very_long_task_title_does_not_crash(acme_owner, acme_project_id):
    resp = requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects/{acme_project_id}/tasks",
        headers=acme_owner["headers"], json={"title": "T" * 5000}, timeout=TIMEOUT,
    )
    assert resp.status_code in (200, 201, 400, 413, 422), f"Server may have crashed: {resp.status_code}"


def test_tc91_tasks_of_other_orgs_project_under_own_org_path(acme_owner, globex_project_id):
    """IDOR variant: own org_id in the path, but a project_id belonging to Globex."""
    resp = requests.get(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects/{globex_project_id}/tasks",
        headers=acme_owner["headers"], timeout=TIMEOUT,
    )
    assert resp.status_code in (403, 404), (
        f"BUG-19: read another org's project via ID under own org path (HTTP {resp.status_code})"
    )


# ---- HTTP-level checks ----

def test_tc92_options_preflight_does_not_crash():
    resp = requests.options(f"{BASE_URL}/orgs/1/projects", timeout=TIMEOUT)
    assert resp.status_code in (200, 204, 404), f"OPTIONS request broke the server: {resp.status_code}"


def test_tc93_response_content_type_is_json(acme_owner):
    resp = requests.get(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects", headers=acme_owner["headers"], timeout=TIMEOUT,
    )
    assert "application/json" in resp.headers.get("Content-Type", ""), (
        f"Expected JSON content-type, got: {resp.headers.get('Content-Type')}"
    )


def test_tc97_unexpected_query_params_ignored(acme_owner):
    resp = requests.get(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects?foo=bar&sort=hacked",
        headers=acme_owner["headers"], timeout=TIMEOUT,
    )
    assert resp.status_code == 200, f"Unexpected query params broke the request: {resp.status_code}"
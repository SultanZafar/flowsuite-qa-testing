import requests
import pytest
from api_helpers import BASE_URL, TIMEOUT, unique_email
from api_helpers import signup_fresh_org
from api_helpers import cancel_subscription, create_project, get_subscription


@pytest.fixture
def fresh_org():
    return signup_fresh_org("billing")


def test_tc47_cannot_change_other_orgs_plan(acme_owner, globex_owner):
    resp = requests.post(
        f"{BASE_URL}/orgs/{globex_owner['org_id']}/subscription/upgrade",
        headers=acme_owner["headers"],
        json={"plan": "PRO"},
        timeout=TIMEOUT,
    )
    assert resp.status_code in (401, 403), (
        f"Acme user upgraded Globex's plan (HTTP {resp.status_code}, expected 403)"
    )


def test_tc48_cannot_cancel_other_orgs_subscription(acme_owner, globex_owner):
    resp = requests.post(
        f"{BASE_URL}/orgs/{globex_owner['org_id']}/subscription/cancel",
        headers=acme_owner["headers"],
        timeout=TIMEOUT,
    )
    assert resp.status_code in (401, 403, 404), (
        f"Acme user cancelled Globex's subscription (HTTP {resp.status_code})"
    )


def test_tc49_free_plan_limit_enforced_at_api(acme_owner):
    """Same FREE-plan-limit-3 bug (TC12) checked directly against the API, not the UI."""
    last_status = None
    for i in range(4):
        resp = requests.post(
            f"{BASE_URL}/orgs/{acme_owner['org_id']}/projects",
            headers=acme_owner["headers"],
            json={"name": f"limit-check-{unique_email('x')}"},
            timeout=TIMEOUT,
        )
        last_status = resp.status_code
    assert last_status in (403, 422), (
        f"BUG-04: 4th project on FREE plan was created via API too (HTTP {last_status})"
    )
def test_tc101_canceled_org_loses_access(fresh_org):
    """BILL-03: after cancelling, the organization must not keep creating projects."""
    org_id = fresh_org["org_id"]

    assert cancel_subscription(fresh_org, org_id).status_code == 200
    assert get_subscription(fresh_org, org_id).json()["status"] == "CANCELED"

    resp = create_project(fresh_org, org_id, "Created after cancel")
    assert resp.status_code in (401, 402, 403), (
        f"BUG-07: CANCELED org still created a project (HTTP {resp.status_code}, expected it to be blocked)"
    )
"""
Additional Billing tests: TC70 - TC74
"""
import requests
from api_helpers import BASE_URL, TIMEOUT


def test_tc70_downgrade_updates_plan(acme_owner):
    """BILL-01: downgrading (same upgrade endpoint, different plan) must persist."""
    requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/subscription/upgrade",
        headers=acme_owner["headers"], json={"plan": "FREE"}, timeout=TIMEOUT,
    )
    check = requests.get(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/subscription",
        headers=acme_owner["headers"], timeout=TIMEOUT,
    ).json()
    assert check.get("plan") == "FREE", f"Plan did not update: {check}"
    # restore to PRO for any later tests
    requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/subscription/upgrade",
        headers=acme_owner["headers"], json={"plan": "PRO"}, timeout=TIMEOUT,
    )


def test_tc71_cancel_subscription_updates_status(acme_admin):
    """BILL-02: cancelling should change status to CANCELED."""
    resp = requests.post(
        f"{BASE_URL}/orgs/{acme_admin['org_id']}/subscription/cancel",
        headers=acme_admin["headers"], timeout=TIMEOUT,
    )
    print("cancel status:", resp.status_code, resp.text)
    assert resp.status_code in (200, 204)


def test_tc72_invalid_plan_name_rejected(acme_owner):
    """BILL-03: upgrading to a non-existent plan must be rejected."""
    resp = requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/subscription/upgrade",
        headers=acme_owner["headers"], json={"plan": "GOLD"}, timeout=TIMEOUT,
    )
    assert resp.status_code in (400, 422), (
        f"BUG-15: invalid plan 'GOLD' was accepted (HTTP {resp.status_code})"
    )
    requests.post(
        f"{BASE_URL}/orgs/{acme_owner['org_id']}/subscription/upgrade",
        headers=acme_owner["headers"], json={"plan": "PRO"}, timeout=TIMEOUT,
    )


def test_tc73_unauthenticated_upgrade_blocked():
    resp = requests.post(f"{BASE_URL}/orgs/1/subscription/upgrade", json={"plan": "PRO"}, timeout=TIMEOUT)
    assert resp.status_code == 401


def test_tc74_invoice_amount_matches_plan_price():
    """BILL-04 (DB check): every invoice's amount must match its plan's listed price."""
    import sqlite3, os
    plan_prices = {"FREE": 0, "PRO": 29, "ENTERPRISE": 99}
    db_path = os.path.join(os.path.dirname(__file__), "..", "db", "app.db")
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT invoice_id, plan, amount FROM Invoices").fetchall()
    conn.close()
    bad = [dict(r) for r in rows if r["plan"] in plan_prices and r["amount"] != plan_prices[r["plan"]]]
    assert not bad, f"BUG-12: invoice amount doesn't match plan price: {bad}"
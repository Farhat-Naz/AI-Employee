"""
odoo_mcp_server.py — Odoo MCP Server (Gold Tier)
-------------------------------------------------
Connects to a local Odoo 19+ instance via JSON-RPC.
Exposes accounting and business operations as MCP tools.

Supported Actions:
  - get_partner       : Fetch customer/vendor by name or ID
  - create_invoice    : Create a customer invoice
  - get_invoices      : List invoices with filters
  - journal_entry     : Create a manual journal entry
  - balance_report    : Get account balance summary
  - get_products      : List products

Setup:
  1. Install Odoo 19 Community locally
  2. Enable API Key: Settings > Technical > API Keys > New
  3. Fill in Gold/MCP_Servers/odoo/odoo_config.json

pip install: no extra packages needed (uses stdlib xmlrpc)
"""

import json
import xmlrpc.client
import os
from datetime import datetime

# ── Config ────────────────────────────────────────────────────────────────────
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "odoo_config.json")
AUDIT_DIR   = os.path.join(os.path.dirname(__file__), "..", "..", "Audit_Logs")


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


# ── Audit ─────────────────────────────────────────────────────────────────────
def audit(action: str, result: str, duration_ms: int = 0) -> None:
    os.makedirs(AUDIT_DIR, exist_ok=True)
    log_file = os.path.join(AUDIT_DIR, f"{datetime.now():%Y-%m-%d}_audit.log")
    entry = (
        f"[{datetime.now():%Y-%m-%d %H:%M:%S}] "
        f"[odoo_mcp] [{action}] [{result}] [{duration_ms}ms]\n"
    )
    with open(log_file, "a") as f:
        f.write(entry)


# ── Odoo Connection ───────────────────────────────────────────────────────────
class OdooClient:
    def __init__(self):
        cfg = load_config()
        self.host    = cfg["host"]
        self.db      = cfg["database"]
        self.user    = cfg["username"]
        self.api_key = cfg["api_key"]
        self.uid     = None
        self._connect()

    def _connect(self):
        common = xmlrpc.client.ServerProxy(f"{self.host}/xmlrpc/2/common")
        self.uid = common.authenticate(self.db, self.user, self.api_key, {})
        if not self.uid:
            raise ConnectionError("Odoo authentication failed — check odoo_config.json")
        self.models = xmlrpc.client.ServerProxy(f"{self.host}/xmlrpc/2/object")

    def execute(self, model: str, method: str, args: list, kwargs: dict = None):
        return self.models.execute_kw(
            self.db, self.uid, self.api_key,
            model, method, args, kwargs or {}
        )


# ── Actions ───────────────────────────────────────────────────────────────────

def get_partner(name: str = None, partner_id: int = None) -> dict:
    start = datetime.now()
    client = OdooClient()
    domain = [["name", "ilike", name]] if name else [["id", "=", partner_id]]
    result = client.execute("res.partner", "search_read", [domain],
                            {"fields": ["id", "name", "email", "phone"], "limit": 10})
    ms = int((datetime.now() - start).total_seconds() * 1000)
    audit("get_partner", f"found {len(result)} records", ms)
    return result


def get_invoices(state: str = "posted", limit: int = 20) -> list:
    start = datetime.now()
    client = OdooClient()
    domain = [["move_type", "=", "out_invoice"], ["state", "=", state]]
    result = client.execute("account.move", "search_read", [domain], {
        "fields": ["name", "partner_id", "amount_total", "invoice_date", "state"],
        "limit": limit,
        "order": "invoice_date desc"
    })
    ms = int((datetime.now() - start).total_seconds() * 1000)
    audit("get_invoices", f"fetched {len(result)} invoices", ms)
    return result


def create_invoice(partner_id: int, amount: float, description: str,
                   currency: str = "PKR") -> dict:
    """Create a draft customer invoice. Requires human approval before posting."""
    start = datetime.now()
    client = OdooClient()
    vals = {
        "move_type": "out_invoice",
        "partner_id": partner_id,
        "invoice_line_ids": [(0, 0, {
            "name": description,
            "quantity": 1,
            "price_unit": amount,
        })],
    }
    invoice_id = client.execute("account.move", "create", [[vals]])
    ms = int((datetime.now() - start).total_seconds() * 1000)
    audit("create_invoice", f"created draft invoice id={invoice_id}", ms)
    return {"invoice_id": invoice_id, "status": "draft", "note": "Requires approval to post"}


def balance_report() -> dict:
    """Get a summary of account balances."""
    start = datetime.now()
    client = OdooClient()
    accounts = client.execute("account.account", "search_read",
                              [[["account_type", "in", ["asset_cash", "liability_payable",
                                                         "income", "expense"]]]],
                              {"fields": ["name", "code", "account_type", "current_balance"],
                               "limit": 50})
    ms = int((datetime.now() - start).total_seconds() * 1000)
    audit("balance_report", f"fetched {len(accounts)} accounts", ms)
    return accounts


# ── Main (CLI test) ───────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Testing Odoo connection...")
    try:
        invoices = get_invoices(limit=5)
        print(f"Connected. Latest invoices: {len(invoices)}")
        for inv in invoices:
            print(f"  - {inv['name']} | {inv['partner_id'][1]} | {inv['amount_total']}")
    except Exception as e:
        print(f"Error: {e}")
        print("Check Gold/MCP_Servers/odoo/odoo_config.json")

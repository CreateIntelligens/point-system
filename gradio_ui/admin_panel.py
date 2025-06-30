import gradio as gr
import requests
import os

API_BASE = os.getenv("API_BASE", "http://localhost:8030/api/v1")

def list_merchants():
    resp = requests.get(f"{API_BASE}/merchants/")
    if resp.ok:
        data = resp.json()["data"]
        return [[m["id"], m["name"], m["created_at"]] for m in data]
    return []

def register_merchant(name):
    resp = requests.post(f"{API_BASE}/merchants/register", params={"name": name})
    if resp.ok:
        return resp.json()["message"]
    return resp.text

def create_api_key(merchant_id, days):
    resp = requests.post(f"{API_BASE}/merchants/{merchant_id}/apikey", params={"expires_in_days": days})
    if resp.ok:
        return resp.json()["data"]["api_key"]
    return resp.text

def list_point_rules(x_api_key):
    resp = requests.get(f"{API_BASE}/points/rules", headers={"x-api-key": x_api_key})
    if resp.ok:
        data = resp.json()["data"]
        return [[r["id"], r["name"], r["rate"], r["description"]] for r in data]
    return []

def create_point_rule(x_api_key, name, rate, description):
    resp = requests.post(
        f"{API_BASE}/points/rules",
        headers={"x-api-key": x_api_key},
        params={"name": name, "rate": rate, "description": description}
    )
    if resp.ok:
        return resp.json()["message"]
    return resp.text

def list_transactions(x_api_key):
    resp = requests.get(f"{API_BASE}/points/transactions", headers={"x-api-key": x_api_key})
    if resp.ok:
        data = resp.json()["data"]
        return [[l["id"], l["uid"], l["point_rule_id"], l["amount"], l["balance"], str(l["detail"]), l["created_at"]] for l in data]
    return []

def create_transaction(x_api_key, uid, point_rule_id, amount, detail):
    import json
    try:
        detail_json = json.loads(detail) if detail else {}
    except Exception:
        return "detail 必須為合法 JSON"
    resp = requests.post(
        f"{API_BASE}/points/transactions",
        headers={"x-api-key": x_api_key},
        params={"uid": uid, "point_rule_id": point_rule_id, "amount": amount},
        json={"detail": detail_json}
    )
    if resp.ok:
        return resp.json()["message"]
    return resp.text

with gr.Blocks() as demo:
    gr.Markdown("# Merchant Admin Panel")
    with gr.Tab("List Merchants"):
        out = gr.Dataframe(headers=["id", "name", "created_at"])
        btn = gr.Button("Refresh")
        btn.click(fn=list_merchants, outputs=out)
    with gr.Tab("Register Merchant"):
        name = gr.Textbox(label="Merchant Name")
        btn2 = gr.Button("Register")
        msg = gr.Textbox(label="Result")
        btn2.click(fn=register_merchant, inputs=name, outputs=msg)
    with gr.Tab("Create API Key"):
        merchant_id = gr.Number(label="Merchant ID")
        days = gr.Number(label="Expires in Days", value=30)
        btn3 = gr.Button("Create")
        key_out = gr.Textbox(label="API Key")
        btn3.click(fn=create_api_key, inputs=[merchant_id, days], outputs=key_out)
    with gr.Tab("PointRule CRUD"):
        x_api_key = gr.Textbox(label="x-api-key")
        rule_out = gr.Dataframe(headers=["id", "name", "rate", "description"])
        btn_rule = gr.Button("List Rules")
        btn_rule.click(fn=list_point_rules, inputs=x_api_key, outputs=rule_out)
        name = gr.Textbox(label="Rule Name")
        rate = gr.Number(label="Rate")
        desc = gr.Textbox(label="Description")
        btn_create_rule = gr.Button("Create Rule")
        msg_rule = gr.Textbox(label="Result")
        btn_create_rule.click(fn=create_point_rule, inputs=[x_api_key, name, rate, desc], outputs=msg_rule)
    with gr.Tab("Transactions"):
        x_api_key2 = gr.Textbox(label="x-api-key")
        tx_out = gr.Dataframe(headers=["id", "uid", "point_rule_id", "amount", "balance", "detail", "created_at"])
        btn_tx = gr.Button("List Transactions")
        btn_tx.click(fn=list_transactions, inputs=x_api_key2, outputs=tx_out)
        uid = gr.Textbox(label="UID")
        point_rule_id = gr.Number(label="Point Rule ID")
        amount = gr.Number(label="Amount")
        detail = gr.Textbox(label="Detail (JSON)", value="{}")
        btn_create_tx = gr.Button("Create Transaction")
        msg_tx = gr.Textbox(label="Result")
        btn_create_tx.click(fn=create_transaction, inputs=[x_api_key2, uid, point_rule_id, amount, detail], outputs=msg_tx)

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

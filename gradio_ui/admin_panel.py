import gradio as gr
import requests
import os

API_BASE = os.getenv("API_BASE", "http://localhost:8030/api/v1")

def list_merchants():
    resp = requests.get(f"{API_BASE}/merchants/")
    if resp.ok:
        data = resp.json()["data"]
        # Convert list of dicts to list of lists for Gradio Dataframe
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

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860)

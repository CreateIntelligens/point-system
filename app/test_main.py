import pytest
from httpx import AsyncClient
from dotenv import load_dotenv
load_dotenv(dotenv_path="app/.env")
import asyncio
import random

# @pytest.mark.asyncio
# async def test_api_flow():
#     async with AsyncClient(base_url="http://localhost:8030") as client:
#         # 1. register_merchant
#         resp = await client.post("/api/v1/merchants/register", params={"name": "test_merchant2"})
#         assert resp.status_code == 200
#         merchant_id = resp.json()["data"]["id"]

#         # 2. create_api_key
#         resp = await client.post(f"/api/v1/merchants/{merchant_id}/apikey")
#         assert resp.status_code == 200
#         api_key = resp.json()["data"]["api_key"]

#         # 3. create_point_rule
#         headers = {"x-api-key": api_key}
#         rule_payload = {"name": "test_rule2", "rate": 2.0, "description": "desc2"}
#         resp = await client.post("/api/v1/points/rules", params=rule_payload, headers=headers)
#         assert resp.status_code == 200
#         rule_id = resp.json()["data"]["id"]

#         # 4. create_transaction 併發測試
#         async def create_tx():
#             for _ in range(100):
#                 uid = str(random.randint(1, 5))
#                 amount = random.randint(-10, 10)
#                 tx_payload = {
#                     "uid": uid,
#                     "point_rule_id": rule_id,
#                     "amount": amount,
#                     "detail": {}
#                 }
#                 r = await client.post("/api/v1/points/transactions", params=tx_payload, headers=headers)
#                 assert r.status_code == 200

#         await asyncio.gather(*[create_tx() for _ in range(10)])

@pytest.mark.asyncio
async def test_transaction_balance_flow(capfd):
    async with AsyncClient(base_url="http://localhost:8030") as client:
        # 1. 取得 test_merchant2 id
        resp = await client.get("/api/v1/merchants/")
        assert resp.status_code == 200
        merchants = resp.json()["data"]
        merchant = next((m for m in merchants if m["name"] == "test_merchant2"), None)
        assert merchant is not None
        merchant_id = merchant["id"]

        # 2. 取得 api_key
        resp = await client.get(f"/api/v1/merchants/{merchant_id}/apikeys")
        assert resp.status_code == 200
        api_keys = resp.json()["data"]
        assert len(api_keys) > 0
        api_key = api_keys[0]["api_key"]

        # 3. 查詢所有 transactions
        headers = {"x-api-key": api_key}
        params = {"sort": "uid,point_rule_id,id"}
        resp = await client.get("/api/v1/points/transactions", params=params, headers=headers)
        assert resp.status_code == 200
        txs = resp.json()["data"]

        # 4. 驗證每個用戶流水 balance
        from collections import defaultdict
        user_txs = defaultdict(list)
        for tx in txs:
            key = (tx["uid"], tx["point_rule_id"])
            user_txs[key].append(tx)
        summary = {}
        for key, tx_list in user_txs.items():
            tx_list.sort(key=lambda x: (x["point_rule_id"], x["id"]))
            for i in range(1, len(tx_list)):
                prev = tx_list[i-1]
                curr = tx_list[i]
                assert prev["balance"] + curr["amount"] == curr["balance"], f'uid={curr["uid"]}, prev_balance={prev["balance"]}, amount={curr["amount"]}, curr_balance={curr["balance"]}'
            # 記錄最後一筆 balance
            summary[key] = tx_list[-1]["balance"] if tx_list else 0
        # 顯示每個 uid/point_rule_id 的最後加總
        result_lines = []
        for (uid, point_rule_id), balance in summary.items():
            result_lines.append(f"uid={uid}, point_rule_id={point_rule_id}, final_balance={balance}")
    out, err = capfd.readouterr()
    print("\n".join(result_lines))

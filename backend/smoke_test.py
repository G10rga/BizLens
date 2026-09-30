"""Quick API smoke test against a running server or in-process app."""

from app import create_app


def main():
    app = create_app()
    client = app.test_client()

    r = client.get("/api/health")
    assert r.status_code == 200, r.data

    r = client.post(
        "/api/auth/login",
        json={"email": "demo@bizlens.ge", "password": "demo1234"},
    )
    assert r.status_code == 200, r.data
    token = r.get_json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    r = client.get("/api/products", headers=headers)
    assert r.status_code == 200, r.data
    products = r.get_json()
    assert len(products) > 0

    r = client.post(
        "/api/sales",
        headers=headers,
        json={
            "payment_method": "cash",
            "items": [{"product_id": products[0]["id"], "quantity": 2}],
        },
    )
    assert r.status_code == 201, r.data

    r = client.get("/api/sales/today", headers=headers)
    assert r.status_code == 200, r.data

    r = client.get("/api/forecast/dashboard", headers=headers)
    assert r.status_code == 200, r.data
    dash = r.get_json()
    assert "timeline" in dash and len(dash["timeline"]) > 0
    print("OK model=", dash.get("model"), "history_days=", dash.get("history_days"))
    print("summary=", dash.get("summary"))

    r = client.get("/api/alerts", headers=headers)
    assert r.status_code == 200, r.data
    print("alerts=", len(r.get_json()))
    print("SMOKE TEST PASSED")


if __name__ == "__main__":
    main()

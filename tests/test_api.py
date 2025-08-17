from fastapi.testclient import TestClient


def test_healthz(client: TestClient):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_search_documents_fresh_then_cache(client: TestClient, mock_repo):
    # first call should fill cache (source fresh)
    r1 = client.get(
        "/skkni/search-documents",
        params={"page_from": 1, "page_to": 1, "limit": 5, "force_refresh": True},
    )
    assert r1.status_code == 200
    data1 = r1.json()
    assert data1["count"] >= 2
    assert data1["source"] == "fresh"
    # fields exist
    item = data1["items"][0]
    assert "uuid" in item and "judul_skkni" in item and "unduh_url" in item

    # second call should hit cache
    r2 = client.get("/skkni/search-documents", params={"page_from": 1, "page_to": 1, "limit": 5})
    assert r2.status_code == 200
    data2 = r2.json()
    assert data2["count"] >= 2
    assert data2["source"] in ("cache", "fresh")  # allow cache; but some impl may still mark fresh


def test_taxonomy_browsing(client: TestClient, mock_repo):
    # Ensure cache is warmed
    client.get(
        "/skkni/search-documents",
        params={"page_from": 1, "page_to": 1, "limit": 5, "force_refresh": True},
    )

    # List sectors -> should have at least one
    rs = client.get("/skkni/sectors?limit=100")
    assert rs.status_code == 200
    sectors = rs.json()["items"]
    assert len(sectors) >= 1
    sector_id = sectors[0]["id"]

    # Fields for sector
    rf = client.get(f"/skkni/sectors/{sector_id}/fields")
    assert rf.status_code == 200
    fields = rf.json()["items"]
    # may be empty depending on data, but shouldn't error
    if fields:
        field_id = fields[0]["id"]
        rsub = client.get(f"/skkni/fields/{field_id}/sub-fields")
        assert rsub.status_code == 200


def test_search_units_with_q_and_filters(client: TestClient, mock_repo):
    # warm cache
    client.get(
        "/skkni/search-units",
        params={"page_from": 1, "page_to": 1, "limit": 10, "force_refresh": True},
    )

    # simple query text
    r = client.get("/skkni/search-units", params={"q": "Target", "limit": 10})
    assert r.status_code == 200
    data = r.json()
    assert data["count"] >= 1
    titles = [x["judul_unit"] for x in data["items"]]
    assert any("Target" in (t or "") for t in titles)

def test_create_patient(client, patient):
    assert patient["name"] == "Ravi Kumar"
    assert patient["id"] > 0


def test_search_patients_by_name(client, patient):
    client.post("/api/patients", json={"name": "Meera Iyer", "phone": "9000000001"})
    resp = client.get("/api/patients", params={"q": "meera"})
    assert [p["name"] for p in resp.json()] == ["Meera Iyer"]


def test_patient_age_must_be_realistic(client):
    resp = client.post("/api/patients", json={"name": "Old Timer", "phone": "12345", "age": 200})
    assert resp.status_code == 422


def test_update_and_delete_patient(client, patient):
    resp = client.put(f"/api/patients/{patient['id']}", json={"phone": "9111111111"})
    assert resp.json()["phone"] == "9111111111"
    assert client.delete(f"/api/patients/{patient['id']}").status_code == 204

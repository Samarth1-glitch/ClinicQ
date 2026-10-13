def test_create_and_list_doctors(client, doctor):
    resp = client.get("/api/doctors")
    assert resp.status_code == 200
    assert [d["name"] for d in resp.json()] == ["Dr. Asha Rao"]


def test_get_doctor_not_found(client):
    assert client.get("/api/doctors/999").status_code == 404


def test_update_doctor(client, doctor):
    resp = client.put(f"/api/doctors/{doctor['id']}", json={"room": "202"})
    assert resp.status_code == 200
    assert resp.json()["room"] == "202"
    assert resp.json()["name"] == "Dr. Asha Rao"  # untouched fields are kept


def test_create_doctor_validation_error(client):
    resp = client.post("/api/doctors", json={"name": "A", "specialization": ""})
    assert resp.status_code == 422


def test_delete_doctor(client, doctor):
    assert client.delete(f"/api/doctors/{doctor['id']}").status_code == 204
    assert client.get(f"/api/doctors/{doctor['id']}").status_code == 404

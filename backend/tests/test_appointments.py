def book(client, doctor, patient, when, reason="Fever"):
    return client.post(
        "/api/appointments",
        json={
            "doctor_id": doctor["id"],
            "patient_id": patient["id"],
            "scheduled_at": when,
            "reason": reason,
        },
    )


def test_book_appointment_assigns_token(client, doctor, patient, today_slot):
    first = book(client, doctor, patient, today_slot(0))
    second = book(client, doctor, patient, today_slot(15))
    assert first.status_code == 201
    assert first.json()["token_number"] == 1
    assert first.json()["status"] == "booked"
    assert first.json()["doctor_name"] == "Dr. Asha Rao"
    assert second.json()["token_number"] == 2


def test_double_booking_same_slot_is_rejected(client, doctor, patient, today_slot):
    assert book(client, doctor, patient, today_slot(0)).status_code == 201
    clash = book(client, doctor, patient, today_slot(0))
    assert clash.status_code == 409


def test_cancelled_slot_can_be_rebooked(client, doctor, patient, today_slot):
    appt = book(client, doctor, patient, today_slot(0)).json()
    client.put(f"/api/appointments/{appt['id']}", json={"status": "cancelled"})
    assert book(client, doctor, patient, today_slot(0)).status_code == 201


def test_book_with_unknown_doctor_returns_404(client, patient, today_slot):
    resp = client.post(
        "/api/appointments",
        json={"doctor_id": 999, "patient_id": patient["id"], "scheduled_at": today_slot(0)},
    )
    assert resp.status_code == 404


def test_status_workflow(client, doctor, patient, today_slot):
    appt = book(client, doctor, patient, today_slot(0)).json()
    url = f"/api/appointments/{appt['id']}"
    assert client.put(url, json={"status": "checked_in"}).json()["status"] == "checked_in"
    assert client.put(url, json={"status": "completed"}).json()["status"] == "completed"
    # completed is final
    assert client.put(url, json={"status": "booked"}).status_code == 409


def test_queue_orders_waiting_patients_and_hides_finished(client, doctor, patient, today_slot):
    a = book(client, doctor, patient, today_slot(0)).json()
    b = book(client, doctor, patient, today_slot(15)).json()
    client.put(f"/api/appointments/{a['id']}", json={"status": "completed"})
    queue = client.get("/api/queue").json()
    assert [q["id"] for q in queue] == [b["id"]]
    assert queue[0]["position"] == 1


def test_stats_count_todays_appointments(client, doctor, patient, today_slot):
    a = book(client, doctor, patient, today_slot(0)).json()
    book(client, doctor, patient, today_slot(15))
    client.put(f"/api/appointments/{a['id']}", json={"status": "cancelled"})
    stats = client.get("/api/appointments/stats").json()
    assert stats["total_today"] == 2
    assert stats["cancelled"] == 1
    assert stats["waiting"] == 1
    assert stats["doctors"] == 1
    assert stats["patients"] == 1


def test_filter_by_status_and_delete(client, doctor, patient, today_slot):
    a = book(client, doctor, patient, today_slot(0)).json()
    listed = client.get("/api/appointments", params={"status": "booked"}).json()
    assert [x["id"] for x in listed] == [a["id"]]
    assert client.delete(f"/api/appointments/{a['id']}").status_code == 204
    assert client.get(f"/api/appointments/{a['id']}").status_code == 404


def test_cannot_delete_doctor_with_appointments(client, doctor, patient, today_slot):
    book(client, doctor, patient, today_slot(0))
    assert client.delete(f"/api/doctors/{doctor['id']}").status_code == 409


def test_booking_increments_custom_metric(client, doctor, patient, today_slot):
    def booked_total() -> float:
        for line in client.get("/metrics").text.splitlines():
            if line.startswith("clinicq_appointments_booked_total "):
                return float(line.split()[1])
        raise AssertionError("metric missing")

    before = booked_total()
    book(client, doctor, patient, today_slot(0))
    assert booked_total() == before + 1

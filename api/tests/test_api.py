from fastapi.testclient import TestClient

from fishfinder.main import app


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_visits() -> None:
    with TestClient(app) as client:
        response = client.get("/api/visits")
    assert response.status_code == 200
    body = response.json()
    assert len(body) > 0
    assert {"signal", "array", "arrived_at", "lat", "lon"} <= body[0].keys()


def test_list_visits_filtered_by_signal() -> None:
    with TestClient(app) as client:
        response = client.get("/api/visits", params={"signals": "2AB5"})
    assert response.status_code == 200
    body = response.json()
    assert body
    assert all(row["signal"] == "2AB5" for row in body)


def test_fish_timeline() -> None:
    with TestClient(app) as client:
        response = client.get("/api/fish/2AB5/timeline")
    assert response.status_code == 200
    body = response.json()
    assert len(body) > 0
    assert "signal" not in body[0]
    assert {"detected_at", "array", "receiver_id", "lat", "lon"} <= body[0].keys()


def test_fish_timeline_unknown_signal_404() -> None:
    with TestClient(app) as client:
        response = client.get("/api/fish/does-not-exist/timeline")
    assert response.status_code == 404


def test_fish_timelines_batched() -> None:
    with TestClient(app) as client:
        response = client.get("/api/fish/timelines", params={"signals": "2AB5,04AD"})
    assert response.status_code == 200
    body = response.json()
    signals = {row["signal"] for row in body}
    assert signals <= {"2AB5", "04AD"}

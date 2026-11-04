import database

def test_insert_and_deduplicate(monkeypatch, tmp_path):
    monkeypatch.setattr(database, "DB_PATH", tmp_path / "test.db")
    event = {"event_id":"evt-1","source":"website","event_name":"Purchase","value":10}
    assert database.insert_event(event) is True
    assert database.insert_event(event) is False
    assert database.get_summary()["conversions"] == 1

def test_date_creation(now, tomorrow):
    assert now.tzinfo is not None
    assert tomorrow.tzinfo is not None
    assert tomorrow > now

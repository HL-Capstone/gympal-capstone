import io, csv
from app import app

def test_export_csv_endpoint_returns_csv():
    client = app.test_client()
    r = client.get("/export.csv")
    assert r.status_code == 200
    assert r.mimetype == "text/csv"
    # parse first line to confirm headers
    text = r.data.decode("utf-8")
    reader = csv.reader(io.StringIO(text))
    headers = next(reader)
    assert headers == ["date","exercise","reps","weight","notes"]

def test_view_about(client):
    response = client.get("/about/").json
    assert {"version": "0.0.1"} == response

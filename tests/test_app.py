# Testing whether app responds at /orders or not
def test_app(client):
    response = client.get("/orders")
    assert 200 == response.status_code, 'Orders page is responding'
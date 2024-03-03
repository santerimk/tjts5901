from flask import Flask, request, session
import json

# Testing whether app responds at /login or not
def test_main(client):
    response = client.get("/login")
    assert 200 == response.status_code, 'Login page is not responding'

def test_main_login(client):
    with client.session_transaction() as session:
    #with client:
        session_data = {
            "traderid": "1",
            "first_name": "Alex",
            "last_name": "Turner",
            "tradername": "alex_t"
        }

        data = {
            "tradername": "alex_t",
            "password": "Pass123%",
        }

        session['trader'] = session_data
        response = client.post("/auth", json.dumps(data), follow_redirects=True)
        assert 200 == response.status_code, "Cant login"
        #assert session["tradername"] == "alex_t"
        assert session["trader"]["tradername"] == "alex_t"
        response2 = client.get("/trade_listing")
        assert 302 == response2.status_code, "Cant open trade listing page"
        response3 = client.get("/offer_listing")
        assert 302 == response3.status_code, "Cant open offers listing page"
        response = client.get("/bid_listing")
        assert 302 == response.status_code, "Cant open bids listing page"
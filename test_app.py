from flask import Flask, request, session

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

        form_data = {
            "tradername": "alex_t",
            "password": "Pass123%",
        }

        # Testing user login
        session['trader'] = session_data
        response = client.post("/auth", data=form_data, follow_redirects=True)
        assert 200 == response.status_code, "Cant login"

        # Testing trade listing
        assert session["trader"]["tradername"] == "alex_t"
        response2 = client.get("/trade_listing")
        assert 200 == response2.status_code, "Cant open trade listing page"
        assert b'No trades available' in response2.data

        # Testing offer listing
        response3 = client.get("/offer_listing")
        assert 200 == response3.status_code, "Cant open offers listing page"
        response4 = client.get("/order_create?stockid=1&order_type=Offer")
        assert 200 == response4.status_code, "Cant open Apple order page"
        form_data = {
            'hidden': '1',
            'quantity': '1',
            'type': 'Offer',
            'price': '171.13'
        }
        response5 = client.post("/order_place", data=form_data, follow_redirects=True)
        assert 200 == response5.status_code, "Cant create offer for Apple stock"
        assert b'New order was placed!' in response5.data

        # Testing bid listing
        response6 = client.get("/bid_listing")
        assert 200 == response6.status_code, "Cant open bids listing page"
        response7 = client.get("/order_create?stockid=1&order_type=Bid")
        assert 200 == response7.status_code, "Cant open Apple order page"
        form_data2 = {
            'hidden': '1',
            'quantity': '2',
            'type': 'Bid',
            'price': '172.13'
        }
        response8 = client.post("/order_place", data=form_data2, follow_redirects=True)
        assert 200 == response8.status_code, "Cant create bid for Apple stock"
        assert b'New order was placed!' in response8.data

        # Testing modifying a bid
        response9 = client.get("/order_modify?stockid=2&orderid=10")
        assert 200 == response9.status_code, "Cant modify order page"
        form_data3 = {
            'hidden1': '2',
            'hidden2': '10',
            'quantity': '8',
            'type': 'Bid',
            'price': '499.00'
        }
        response10 = client.post("/order_update", data=form_data3, follow_redirects=True)
        assert 200 == response10.status_code, "Cant modify order"
        assert b'Order was modified!' in response10.data

        # Testing deleting a bid
        response11 = client.get("/dashboard")
        assert 200 == response11.status_code, "Cant open dashboard"
        form_data4 = {
            'hidden1': '2',
            'hidden2': '10',
            'quantity': '8',
            'type': 'Bid',
            'price': '499.00',
            'delete': 'y'
        }
        response12 = client.post("/order_update", data=form_data4, follow_redirects=True)
        assert 200 == response12.status_code, "Cant delete a bid"
        assert b'Order was deleted!' in response12.data
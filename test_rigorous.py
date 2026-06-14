import requests
import json
import os

BASE_URL = "http://localhost:8001"

def run_tests():
    # User 1
    s1 = requests.Session()
    s1.post(f"{BASE_URL}/signup", data={"name": "Alice", "email": "alice@test.com", "password": "password"})
    s1.post(f"{BASE_URL}/login", data={"email": "alice@test.com", "password": "password"})

    # User 2
    s2 = requests.Session()
    s2.post(f"{BASE_URL}/signup", data={"name": "Bob", "email": "bob@test.com", "password": "password"})
    s2.post(f"{BASE_URL}/login", data={"email": "bob@test.com", "password": "password"})

    # Alice creates Group
    r = s1.post(f"{BASE_URL}/groups", data={"name": "Alice Group"}, allow_redirects=False)
    group_url = r.headers.get("Location")
    group_id = group_url.split("/")[-1]

    # Bob tries to access Alice's group GET
    r = s2.get(f"{BASE_URL}/groups/{group_id}", allow_redirects=False)
    if r.status_code == 200:
        print("VULNERABILITY: Bob can view Alice's group!")

    # Bob tries to post an expense to Alice's group
    r = s2.post(f"{BASE_URL}/groups/{group_id}/expenses", data={
        "description": "Hack",
        "date": "2024-01-01",
        "amount": "100",
        "paid_by": "1",
        "currency": "INR",
        "split_type": "equal",
        "split_with": ["1"]
    }, allow_redirects=False)
    if r.status_code in [200, 302, 303]:
        print("VULNERABILITY: Bob can post expenses to Alice's group!")

    # Alice posts an expense with invalid percentage
    r = s1.post(f"{BASE_URL}/groups/{group_id}/expenses", data={
        "description": "Dinner",
        "date": "2024-01-01",
        "amount": "100",
        "paid_by": "1",
        "currency": "INR",
        "split_type": "percentage",
        "split_with": ["1"],
        "split_details": json.dumps({"1": 50}) # Missing 50%
    }, allow_redirects=False)
    if r.status_code == 500:
        print("BUG: 500 Internal Server Error when percentages don't add up to 100.")

    print("Rigorous tests completed.")

if __name__ == "__main__":
    run_tests()

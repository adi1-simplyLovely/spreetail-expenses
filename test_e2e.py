import requests
import json
import os

BASE_URL = "http://localhost:8001"

def test_app():
    s = requests.Session()
    print("Testing signup...")
    r = s.post(f"{BASE_URL}/signup", data={
        "name": "E2E Test User",
        "email": "e2e@example.com",
        "password": "password123"
    }, allow_redirects=True)
    if r.status_code != 200:
        print("Signup failed:", r.status_code, r.text[:200])

    print("Testing login...")
    r = s.post(f"{BASE_URL}/login", data={
        "email": "e2e@example.com",
        "password": "password123"
    }, allow_redirects=True)
    if "Dashboard" not in r.text and "Groups" not in r.text:
        print("Login failed or redirect didn't work. Code:", r.status_code)
    
    print("Testing dashboard...")
    r = s.get(f"{BASE_URL}/dashboard")
    if r.status_code != 200:
        print("Dashboard failed:", r.status_code, r.text[:200])

    print("Testing group creation...")
    r = s.post(f"{BASE_URL}/groups", data={
        "name": "E2E Test Group"
    }, allow_redirects=False)
    if r.status_code not in [302, 303]:
        print("Group creation failed:", r.status_code, r.text[:200])
    
    # Get group id from redirect URL
    group_url = r.headers.get("Location")
    print(f"Group created, redirecting to {group_url}")
    
    r = s.get(f"{BASE_URL}{group_url}")
    if r.status_code != 200:
        print("Group detail failed:", r.status_code, r.text[:200])

    group_id = group_url.split("/")[-1]

    print("Testing member addition...")
    # First signup another user
    s2 = requests.Session()
    s2.post(f"{BASE_URL}/signup", data={"name": "Friend", "email": "friend@example.com", "password": "password123"})
    
    r = s.post(f"{BASE_URL}/groups/{group_id}/members", data={
        "user_email": "friend@example.com",
        "joined_at": "2024-01-01"
    }, allow_redirects=True)
    if r.status_code != 200:
        print("Member addition failed:", r.status_code, r.text[:200])

    print("Testing add expense...")
    r = s.post(f"{BASE_URL}/groups/{group_id}/expenses", data={
        "description": "Dinner",
        "date": "2024-01-02",
        "amount": "100",
        "paid_by": "1",
        "currency": "INR",
        "split_type": "equal",
        "split_with": ["1", "2"]
    }, allow_redirects=True)
    if r.status_code != 200:
        print("Expense addition failed:", r.status_code, r.text[:200])

    print("Testing balances...")
    r = s.get(f"{BASE_URL}/groups/{group_id}/balances")
    if r.status_code != 200:
        print("Balances failed:", r.status_code, r.text[:200])

    print("Testing settlement form...")
    r = s.get(f"{BASE_URL}/groups/{group_id}/settlements/add")
    if r.status_code != 200:
        print("Settlement form failed:", r.status_code, r.text[:200])

    print("Testing CSV import page...")
    r = s.get(f"{BASE_URL}/groups/{group_id}/import")
    if r.status_code != 200:
        print("Import page failed:", r.status_code, r.text[:200])
        
    print("All basic routes tested.")

if __name__ == "__main__":
    test_app()

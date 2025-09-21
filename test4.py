#!/usr/bin/env python3
import requests
import argparse
import sys

API_BASE = "https://monkeytype.live/api"

def add_user(router_id: str, username: str, password: str):
    url = f"{API_BASE}/add-user"
    payload = {
        "router_id": router_id,
        "username": username,
        "password": password
    }
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print("✅ User added successfully:", response.json())
    except requests.exceptions.RequestException as e:
        print("❌ Error adding user:", e)
        sys.exit(1)

if __name__ == "__main__":
    add_user('ROUTER1', 'admin', "Nashdev@098")

import requests
import json

API_KEY = "b1c75de81f29e150b1f86aa0261d2eb2"
API_URL = "https://smmpanel.net/api/v2"

print("Tekshirish boshlandi...")

# Balansni tekshirish
response = requests.post(API_URL, data={
    'key': API_KEY,
    'action': 'balance'
})
print(f"Balans: {response.json()}")

# Xizmatlarni olish
response = requests.post(API_URL, data={
    'key': API_KEY,
    'action': 'services'
})

services = response.json()
print(f"\nJami xizmatlar: {len(services)}")

# Instagram
print("\n=== INSTAGRAM ===")
for s in services:
    if 'instagram' in s.get('name', '').lower():
        if 'follower' in s.get('name', '').lower() or 'like' in s.get('name', '').lower() or 'view' in s.get('name', '').lower():
            print(f"ID: {s['service']} | {s['name']} | ${s['rate']}/1k | Min:{s['min']} Max:{s['max']}")

# TikTok
print("\n=== TIKTOK ===")
for s in services:
    if 'tiktok' in s.get('name', '').lower():
        if 'follower' in s.get('name', '').lower() or 'like' in s.get('name', '').lower() or 'view' in s.get('name', '').lower():
            print(f"ID: {s['service']} | {s['name']} | ${s['rate']}/1k | Min:{s['min']} Max:{s['max']}")

# Telegram
print("\n=== TELEGRAM ===")
for s in services:
    if 'telegram' in s.get('name', '').lower():
        if 'member' in s.get('name', '').lower() or 'view' in s.get('name', '').lower():
            print(f"ID: {s['service']} | {s['name']} | ${s['rate']}/1k | Min:{s['min']} Max:{s['max']}")
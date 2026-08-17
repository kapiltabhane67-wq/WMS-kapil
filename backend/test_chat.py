import urllib.request, json, urllib.error

print("Testing WMS Chatbot...")

# Login
try:
    login_data = json.dumps({"email": "admin@whitfieldwms.com", "password": "Admin1234!"}).encode()
    req = urllib.request.Request(
        "http://127.0.0.1:8016/v1/auth/login",
        data=login_data,
        headers={"Content-Type": "application/json"}
    )
    token = json.loads(urllib.request.urlopen(req, timeout=10).read())["access_token"]
    print("Login: OK")
except Exception as e:
    print("Login FAILED:", e)
    exit(1)

# Test questions
questions = [
    "List all staff members with their roles.",
    "Who is doing what right now? Any active pick tasks?",
    "Tell me about the sellers in the system.",
    "What is the current inventory status?",
]

for q in questions:
    print(f"\nQ: {q}")
    chat_data = json.dumps({"message": q, "history": []}).encode()
    req2 = urllib.request.Request(
        "http://127.0.0.1:8016/v1/chat",
        data=chat_data,
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"}
    )
    try:
        res = urllib.request.urlopen(req2, timeout=30)
        result = json.loads(res.read())
        print("A:", result["reply"][:300], "..." if len(result["reply"]) > 300 else "")
    except urllib.error.HTTPError as e:
        print("Error:", e.code, e.read().decode())
    except Exception as e:
        print("Error:", e)

print("\nAll tests done!")

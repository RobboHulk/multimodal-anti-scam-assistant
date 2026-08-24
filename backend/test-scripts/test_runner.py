import json
import urllib.request
import urllib.error
import time
import random

base_url = "http://localhost:8888"
user_token = ""
guardian_token = ""
user_id = 0
guardian_id = 0

def req(method, path, body=None, token_to_use=None):
    url = base_url + path
    headers = {}
    if body is not None:
        headers["Content-Type"] = "application/json"
    if token_to_use:
        headers["Authorization"] = f"Bearer {token_to_use}"
        
    data = json.dumps(body).encode('utf-8') if body else None
    request = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(request) as response:
            res_data = response.read().decode('utf-8')
            res_json = json.loads(res_data) if res_data else {}
            if res_json.get("code") != 200:
                print(f"❌ [{method}] {path} -> 业务错误: {res_json.get('message')}")
            else:
                print(f"✅ [{method}] {path} -> 成功")
            return res_json
    except urllib.error.HTTPError as e:
        try:
            err_data = e.read().decode('utf-8')
            print(f"❌ [{method}] {path} -> HTTP {e.code} 异常: {json.loads(err_data).get('message', err_data)}")
        except:
            print(f"❌ [{method}] {path} -> HTTP {e.code} 严重异常")
        return None
    except urllib.error.URLError as e:
        print(f"⚠️ [{method}] {path} -> 连接失败: {e.reason}")
        return None

username = f"testuser_{random.randint(1000, 9999)}"
phone = f"13800{random.randint(100000, 999999)}"

print("=== 1. 用户模块测试 ===")
req("POST", "/api/user/register", {"username": username, "password": "password123", "phone": phone})
res_login = req("POST", "/api/user/login", {"username": username, "password": "password123"})
if res_login and res_login.get("data"):
    user_token = res_login.get("data")

req("GET", "/api/user/profile", token_to_use=user_token)
req("PUT", "/api/user/profile", {"ageGroup": 2, "occupation": "学生", "gender": 1}, token_to_use=user_token)
req("PUT", "/api/user/config", {"riskThreshold": 60, "notifyPolicy": "IMMEDIATE"}, token_to_use=user_token)


print("\n=== 2. 监护人模块测试 ===")
res_wx = req("POST", "/api/guardian/wx-login", {"code": "test_wx_code", "nickname": "测试监护人"})
if res_wx and res_wx.get("data"):
    guardian_token = res_wx.get("data")

req("POST", "/api/guardian/whitelist", {
  "contactInfo": "13900001111",
  "contactType": "PHONE",
  "name": "李叔叔"
}, token_to_use=user_token)

# 绑定前，给监护人设置个手机号，因为我们的业务根据手机号绑定
# (通过微信登录获取的监护人可能没有phone，这里需要直接绑手机会报错，我们看看)
req("POST", "/api/guardian/bind", {"guardianPhone": phone, "relation": "FATHER"}, token_to_use=user_token)

req("PUT", "/api/guardian/notify-policy", {"notifyPolicy": "DAILY_SUMMARY"}, token_to_use=guardian_token)
req("GET", "/api/guardian/summary", token_to_use=guardian_token)


print("\n=== 3. 业务功能测试 ===")
req("POST", "/api/chat/send", {
  "text": "公检法要求你立即把钱转入安全账户",
  "session_id": "script-chat-001",
  "image_path": "https://example.com/fake_police.jpg",
  "userProfile": {
    "id": 1,
    "username": username,
    "ageGroup": 2,
    "gender": 1,
    "occupation": "学生",
    "riskPreference": 2,
    "riskThreshold": 0.7,
    "interventionStrategy": 1
  }
}, token_to_use=user_token)

req("GET", "/api/alert/history", token_to_use=user_token)
req("GET", "/api/report/list", token_to_use=user_token)

print("\n=== 测试完成 ===")

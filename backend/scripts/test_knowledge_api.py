
import requests
import json

# ================= 配置区 =================
BASE_URL = "http://localhost:8888/api/knowledge"
# 如果 API 需要授权，请在此填入 Token（不带 Bearer 前缀）
# 如果已经配置为公开，此处留空即可
TOKEN = "" 
# ==========================================

def test_list_knowledge():
    print("Testing Get Knowledge List API...")
    url = f"{BASE_URL}/list"
    params = {
        "current": 1,
        "size": 5
    }
    
    headers = {}
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    
    try:
        response = requests.get(url, params=params, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 200:
                data = result.get("data", {})
                records = data.get("records", [])
                total = data.get("total", 0)
                
                print(f"Success! Total articles in DB: {total}")
                print(f"Retrieved {len(records)} samples from Page 1:")
                
                for i, art in enumerate(records):
                    print(f"--- Sample {i+1} ---")
                    print(f"Title: {art.get('title')}")
                    print(f"Type: {art.get('scamType')}")
                    print(f"Source: {art.get('source')} ({art.get('sourceUrl')})")
                    print(f"Content Snippet: {str(art.get('content'))[:100]}...")
            else:
                print(f"API Error: {result.get('message')}")
        elif response.status_code == 403:
            print("Error 403: Access Denied. Please ensure /api/knowledge/list is added to SecurityConfig permitAll or provide a valid TOKEN.")
        else:
            print(f"HTTP Error {response.status_code}: {response.text}")
            
    except Exception as e:
        print(f"Connection Failed: {e}")
        print("Note: Please make sure the Spring Boot backend is running on port 8888.")

if __name__ == "__main__":
    test_list_knowledge()

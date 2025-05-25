import requests
 
def check_url_safety(url, api_key):
    API_URL = "https://safebrowsing.googleapis.com/v4/threatMatches:find"
    
    payload = {
        "client": {
            "clientId": "tilsyn",
            "clientVersion": "1.0"
        },
        "threatInfo": {
            "threatTypes": ["MALWARE", "SOCIAL_ENGINEERING", "UNWANTED_SOFTWARE"],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [{"url": url}]
        }
    }
    
    try:
        response = requests.post(
            f"{API_URL}?key={api_key}",
            json=payload,
            timeout=5
        )
        return not bool(response.json().get('matches'))
    except Exception as e:
        print(f"Safe Browsing check failed: {e}")
        return True  

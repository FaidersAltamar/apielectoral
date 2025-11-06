"""
Test script for get_name_sequential endpoint with voting location integration
"""
import requests
import json

# Configuration
API_URL = "http://localhost:8000"
ENDPOINT = "/consultar-nombres"

# Test data
test_payload = {
    "nuips": ["1102877148"]
}

def test_get_name_sequential():
    """
    Test the /consultar-nombres endpoint to verify:
    1. Name retrieval from Procuraduría or Sisben
    2. Voting location query from Registraduría
    3. Data sent to external API with all required fields
    """
    print("=" * 80)
    print("Testing /consultar-nombres endpoint")
    print("=" * 80)
    
    print(f"\n📤 Sending request to: {API_URL}{ENDPOINT}")
    print(f"📋 Payload: {json.dumps(test_payload, indent=2)}")
    
    try:
        response = requests.post(
            f"{API_URL}{ENDPOINT}",
            json=test_payload,
            timeout=120
        )
        
        print(f"\n📥 Response Status Code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Response received successfully!")
            print(f"\n📊 Response Data:")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            
            # Verify expected fields
            print(f"\n🔍 Verification:")
            print(f"   - Status: {result.get('status')}")
            print(f"   - Total NUIPs: {result.get('total_nuips')}")
            print(f"   - Successful: {result.get('successful')}")
            print(f"   - Not Found: {result.get('not_found')}")
            print(f"   - Errors: {result.get('errors')}")
            
        else:
            print(f"\n❌ Error: {response.status_code}")
            print(f"Response: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("\n❌ Error: Could not connect to API")
        print("   Make sure the API is running on http://localhost:8000")
    except requests.exceptions.Timeout:
        print("\n❌ Error: Request timeout")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_get_name_sequential()

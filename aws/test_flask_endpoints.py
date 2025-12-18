#!/usr/bin/env python3
"""
Test script to validate Flask endpoints are working correctly.
"""

import requests
import json
import sys
from typing import Dict, Any

# Get API endpoint from environment or CloudFormation
# Update this with the correct API ID from CloudFormation output
API_URL = "https://jxl8zp03dh.execute-api.us-east-1.amazonaws.com/prod"

def test_endpoint(method: str, path: str, headers: Dict = None, data: Dict = None, expected_status: int = None) -> Dict[str, Any]:
    """Test an API endpoint and return results."""
    url = f"{API_URL}{path}"
    headers = headers or {}
    headers.setdefault("Content-Type", "application/json")
    
    print(f"\n{'='*60}")
    print(f"Testing: {method} {path}")
    print(f"{'='*60}")
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        else:
            return {"error": f"Unsupported method: {method}"}
        
        result = {
            "status_code": response.status_code,
            "headers": dict(response.headers),
            "response": None
        }
        
        try:
            result["response"] = response.json()
        except:
            result["response"] = response.text[:500]  # First 500 chars
        
        print(f"Status Code: {response.status_code}")
        
        if expected_status and response.status_code != expected_status:
            print(f"⚠️  Expected {expected_status}, got {response.status_code}")
        elif response.status_code < 400:
            print("✅ Request successful")
        else:
            print(f"❌ Request failed")
        
        if result["response"]:
            print(f"Response: {json.dumps(result['response'], indent=2)[:500]}")
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        return {"error": str(e)}

def main():
    print("🧪 Testing Flask API Endpoints")
    print("=" * 60)
    
    results = []
    
    # Test 1: Player endpoint (no auth required) - should work
    print("\n📋 Test 1: Player endpoint (GET /player/{uniqueLink})")
    result1 = test_endpoint("GET", "/player/test-unique-link", expected_status=404)
    results.append(("Player endpoint", result1))
    # Expected: 404 (player not found) or 400 (invalid link) - both show Flask is routing
    
    # Test 2: Leaderboard endpoint (no auth required)
    print("\n📋 Test 2: Leaderboard endpoint (GET /leaderboard/{weekId})")
    result2 = test_endpoint("GET", "/leaderboard/2024-03?uniqueLink=test&scope=team", expected_status=400)
    results.append(("Leaderboard endpoint", result2))
    
    # Test 3: Content endpoint (no auth required)
    print("\n📋 Test 3: Content endpoint (GET /content)")
    result3 = test_endpoint("GET", "/content?uniqueLink=test", expected_status=404)
    results.append(("Content endpoint", result3))
    
    # Test 4: Admin endpoint without auth (should return 401)
    print("\n📋 Test 4: Admin endpoint without authentication")
    result4 = test_endpoint("GET", "/admin/check-role", expected_status=401)
    results.append(("Admin endpoint (no auth)", result4))
    
    # Test 5: Admin endpoint with invalid token (should return 401/403)
    print("\n📋 Test 5: Admin endpoint with invalid token")
    result5 = test_endpoint("GET", "/admin/check-role", 
                           headers={"Authorization": "Bearer invalid-token"},
                           expected_status=401)
    results.append(("Admin endpoint (invalid token)", result5))
    
    # Test 6: OPTIONS request (CORS preflight)
    print("\n📋 Test 6: OPTIONS request (CORS)")
    result6 = test_endpoint("OPTIONS", "/admin/check-role", expected_status=200)
    results.append(("CORS preflight", result6))
    
    # Test 7: Invalid route (should return 404 from Flask)
    print("\n📋 Test 7: Invalid route")
    result7 = test_endpoint("GET", "/invalid/route", expected_status=404)
    results.append(("Invalid route", result7))
    
    # Test 8: Check Flask error format
    print("\n📋 Test 8: Error response format")
    # Use invalid method on valid route
    try:
        response = requests.delete(f"{API_URL}/player/test", timeout=10)
        result8 = {
            "status_code": response.status_code,
            "response": response.json() if response.headers.get("content-type", "").startswith("application/json") else response.text[:200]
        }
        print(f"Status: {result8['status_code']}")
        print(f"Response format: {'JSON' if isinstance(result8.get('response'), dict) else 'Text'}")
        results.append(("Error format", result8))
    except Exception as e:
        print(f"Error: {e}")
        results.append(("Error format", {"error": str(e)}))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        if "error" in result:
            print(f"❌ {test_name}: Error - {result['error']}")
            failed += 1
        elif result.get("status_code"):
            status = result["status_code"]
            if 200 <= status < 400:
                print(f"✅ {test_name}: {status}")
                passed += 1
            elif status == 401 or status == 403:
                print(f"✅ {test_name}: {status} (Expected auth error)")
                passed += 1
            elif status == 404:
                print(f"✅ {test_name}: {status} (Expected not found)")
                passed += 1
            else:
                print(f"⚠️  {test_name}: {status}")
                failed += 1
        else:
            print(f"❌ {test_name}: No response")
            failed += 1
    
    print(f"\n✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"📊 Total: {len(results)}")
    
    # Check for Flask-specific indicators
    print("\n" + "=" * 60)
    print("🔍 Flask Validation Checks")
    print("=" * 60)
    
    flask_indicators = []
    
    # Check if responses have Flask error format
    for test_name, result in results:
        if isinstance(result.get("response"), dict):
            resp = result["response"]
            if "success" in resp or "error" in resp:
                flask_indicators.append(f"✅ {test_name}: Has Flask error format")
            if "message" in resp.get("error", {}):
                flask_indicators.append(f"✅ {test_name}: Has error message field")
    
    for indicator in flask_indicators:
        print(indicator)
    
    if not flask_indicators:
        print("⚠️  No clear Flask response format detected")
    
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    sys.exit(main())


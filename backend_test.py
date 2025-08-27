#!/usr/bin/env python3
"""
Backend API Testing Suite for Resume Matcher
Tests all backend endpoints according to test_result.md requirements
"""

import requests
import json
import uuid
import time
from typing import Dict, Any, List

# Use the production URL from frontend/.env
BASE_URL = "https://career-finder-17.preview.emergentagent.com/api"

def test_api_root():
    """Test GET /api/ endpoint"""
    print("🧪 Testing GET /api/")
    try:
        response = requests.get(f"{BASE_URL}/")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"   Response: {data}")
            
            if data.get("message") == "Resume Matcher API ready":
                print("   ✅ API root endpoint working correctly")
                return True
            else:
                print(f"   ❌ Unexpected message: {data.get('message')}")
                return False
        else:
            print(f"   ❌ Failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def test_upload_flow():
    """Test complete upload flow: init -> chunk -> complete"""
    print("\n🧪 Testing Upload Flow")
    
    # Step 1: Initialize upload
    print("   Step 1: POST /api/upload/init")
    init_payload = {
        "filename": "test_resume.pdf",
        "size": 100,
        "mimeType": "application/pdf"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/upload/init", json=init_payload)
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ Init failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
        init_data = response.json()
        upload_id = init_data.get("uploadId")
        print(f"   ✅ Got uploadId: {upload_id}")
        
        if not upload_id:
            print("   ❌ No uploadId in response")
            return False
            
    except Exception as e:
        print(f"   ❌ Init exception: {e}")
        return False
    
    # Step 2: Upload chunks (2 chunks with realistic resume content)
    print("   Step 2: POST /api/upload/chunk (2 chunks)")
    
    # Chunk 0: Resume header with skills
    chunk_0_data = b"""John Doe
Software Engineer
Email: john.doe@email.com
Phone: (555) 123-4567

SKILLS:
- Python programming with 5+ years experience
- FastAPI and Flask web frameworks
- React and JavaScript frontend development
- MongoDB and SQL databases
- Docker containerization
- AWS cloud services
"""
    
    # Chunk 1: Experience section
    chunk_1_data = b"""
EXPERIENCE:
Senior Software Engineer | TechCorp | 2020-2023
- Built REST APIs using Python and FastAPI
- Developed React applications with TypeScript
- Managed MongoDB databases and SQL queries
- Implemented CI/CD pipelines with Docker
- Deployed applications on AWS infrastructure

EDUCATION:
Bachelor of Computer Science | University | 2016-2020
"""
    
    chunks = [chunk_0_data, chunk_1_data]
    
    for i, chunk_data in enumerate(chunks):
        try:
            headers = {"Content-Type": "application/octet-stream"}
            response = requests.post(
                f"{BASE_URL}/upload/chunk?uploadId={upload_id}&index={i}",
                data=chunk_data,
                headers=headers
            )
            print(f"   Chunk {i} status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"   ❌ Chunk {i} failed with status {response.status_code}")
                print(f"   Response: {response.text}")
                return False
                
            chunk_response = response.json()
            print(f"   ✅ Chunk {i} uploaded: {chunk_response}")
            
        except Exception as e:
            print(f"   ❌ Chunk {i} exception: {e}")
            return False
    
    # Step 3: Complete upload
    print("   Step 3: POST /api/upload/complete")
    complete_payload = {"uploadId": upload_id}
    
    try:
        response = requests.post(f"{BASE_URL}/upload/complete", json=complete_payload)
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ Complete failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
        complete_data = response.json()
        print(f"   ✅ Upload completed successfully")
        
        # Validate AnalyzeResponse structure
        if not validate_analyze_response(complete_data):
            return False
            
        return True
        
    except Exception as e:
        print(f"   ❌ Complete exception: {e}")
        return False

def validate_analyze_response(data: Dict[str, Any]) -> bool:
    """Validate AnalyzeResponse schema"""
    print("   Validating AnalyzeResponse schema...")
    
    # Check top-level structure
    if "analysis" not in data or "matches" not in data:
        print("   ❌ Missing 'analysis' or 'matches' in response")
        return False
    
    analysis = data["analysis"]
    matches = data["matches"]
    
    # Validate analysis structure
    required_analysis_fields = ["id", "filename", "mimeType", "text_chars", "extracted_skills", "inferred_roles", "created_at"]
    for field in required_analysis_fields:
        if field not in analysis:
            print(f"   ❌ Missing '{field}' in analysis")
            return False
    
    print(f"   ✅ Analysis ID: {analysis['id']}")
    print(f"   ✅ Filename: {analysis['filename']}")
    print(f"   ✅ Text chars: {analysis['text_chars']}")
    print(f"   ✅ Extracted skills: {analysis['extracted_skills']}")
    print(f"   ✅ Inferred roles: {analysis['inferred_roles']}")
    
    # Validate matches structure
    if not isinstance(matches, list):
        print("   ❌ Matches should be a list")
        return False
    
    print(f"   ✅ Found {len(matches)} job matches")
    
    # Validate first match if exists
    if matches:
        match = matches[0]
        required_match_fields = ["job_id", "job_title", "company", "match_percent", "matched_skills", "missing_skills"]
        for field in required_match_fields:
            if field not in match:
                print(f"   ❌ Missing '{field}' in match")
                return False
        
        print(f"   ✅ Top match: {match['job_title']} at {match['company']} ({match['match_percent']}%)")
        print(f"   ✅ Matched skills: {match['matched_skills']}")
    
    print("   ✅ AnalyzeResponse schema validation passed")
    return True

def test_upload_edge_cases():
    """Test upload edge cases"""
    print("\n🧪 Testing Upload Edge Cases")
    
    # Test chunk upload with wrong uploadId
    print("   Testing chunk upload with invalid uploadId")
    fake_upload_id = str(uuid.uuid4())
    chunk_data = b"test data"
    
    try:
        headers = {"Content-Type": "application/octet-stream"}
        response = requests.post(
            f"{BASE_URL}/upload/chunk?uploadId={fake_upload_id}&index=0",
            data=chunk_data,
            headers=headers
        )
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 400:
            print("   ✅ Correctly returned 400 for invalid uploadId")
            return True
        else:
            print(f"   ❌ Expected 400, got {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def test_jobs_endpoint():
    """Test GET /api/jobs endpoint"""
    print("\n🧪 Testing GET /api/jobs")
    
    try:
        response = requests.get(f"{BASE_URL}/jobs")
        print(f"   Status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ Failed with status {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
        jobs = response.json()
        print(f"   ✅ Retrieved {len(jobs)} jobs")
        
        if not isinstance(jobs, list):
            print("   ❌ Jobs should be a list")
            return False
        
        if len(jobs) == 0:
            print("   ❌ No jobs found - seeding might have failed")
            return False
        
        # Validate job structure
        job = jobs[0]
        required_fields = ["id", "title", "company", "required_skills"]
        for field in required_fields:
            if field not in job:
                print(f"   ❌ Missing '{field}' in job")
                return False
        
        # Check that _id is not present (Mongo ObjectId should be removed)
        if "_id" in job:
            print("   ❌ Found '_id' field - should be removed for JSON serialization")
            return False
        
        # Validate UUID format for id
        try:
            uuid.UUID(job["id"])
            print(f"   ✅ Job ID is valid UUID: {job['id']}")
        except ValueError:
            print(f"   ❌ Job ID is not a valid UUID: {job['id']}")
            return False
        
        print(f"   ✅ Sample job: {job['title']} at {job['company']}")
        print(f"   ✅ Required skills: {job['required_skills']}")
        
        # Verify seeding works (should have expected jobs)
        expected_companies = ["Acme Cloud", "Insight Analytics", "Pixel Labs"]
        found_companies = [j["company"] for j in jobs]
        
        for company in expected_companies:
            if company in found_companies:
                print(f"   ✅ Found expected company: {company}")
            else:
                print(f"   ⚠️  Expected company not found: {company}")
        
        print("   ✅ Jobs endpoint working correctly")
        return True
        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def run_all_tests():
    """Run all backend tests"""
    print("🚀 Starting Backend API Tests")
    print(f"   Base URL: {BASE_URL}")
    print("=" * 60)
    
    results = {}
    
    # Test 1: API Root
    results["api_root"] = test_api_root()
    
    # Test 2: Upload Flow
    results["upload_flow"] = test_upload_flow()
    
    # Test 3: Upload Edge Cases
    results["upload_edge_cases"] = test_upload_edge_cases()
    
    # Test 4: Jobs Endpoint
    results["jobs_endpoint"] = test_jobs_endpoint()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n   Total: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("   🎉 All tests passed!")
        return True
    else:
        print("   ⚠️  Some tests failed")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
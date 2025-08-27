#!/usr/bin/env python3
"""
Groq Text-Only Extraction Testing Suite
Specifically tests Groq AI-enriched skill extraction functionality
"""

import requests
import json
import uuid
import time
from typing import Dict, Any, List

# Use the production URL from frontend/.env
BASE_URL = "https://career-finder-17.preview.emergentagent.com/api"

def test_groq_extraction_with_simple_text():
    """Test Groq extraction with simple text mentioning Python, React, SQL"""
    print("🧪 Testing Groq Extraction with Simple Text")
    
    # Step 1: Initialize upload
    print("   Step 1: POST /api/upload/init")
    init_payload = {
        "filename": "simple_resume.txt",
        "size": 200,
        "mimeType": "text/plain"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/upload/init", json=init_payload)
        if response.status_code != 200:
            print(f"   ❌ Init failed with status {response.status_code}")
            return False
            
        init_data = response.json()
        upload_id = init_data.get("uploadId")
        print(f"   ✅ Got uploadId: {upload_id}")
        
    except Exception as e:
        print(f"   ❌ Init exception: {e}")
        return False
    
    # Step 2: Upload single chunk with simple text mentioning Python, React, SQL
    print("   Step 2: POST /api/upload/chunk (simple text)")
    
    # Simple text that should trigger both heuristic and Groq extraction
    simple_text = b"""Sarah Johnson
Software Developer
sarah.johnson@email.com

I am a skilled developer with experience in Python programming, React frontend development, and SQL database management. 
I have worked with FastAPI for backend services and have knowledge of MongoDB and Docker containerization.
My expertise includes JavaScript, TypeScript, and modern web development practices.
I am passionate about building scalable applications and have experience with AWS cloud services.
"""
    
    try:
        headers = {"Content-Type": "application/octet-stream"}
        response = requests.post(
            f"{BASE_URL}/upload/chunk?uploadId={upload_id}&index=0",
            data=simple_text,
            headers=headers
        )
        print(f"   Chunk status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"   ❌ Chunk failed with status {response.status_code}")
            return False
            
    except Exception as e:
        print(f"   ❌ Chunk exception: {e}")
        return False
    
    # Step 3: Complete upload and analyze results
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
        
        # Analyze the extraction results
        return analyze_groq_results(complete_data)
        
    except Exception as e:
        print(f"   ❌ Complete exception: {e}")
        return False

def analyze_groq_results(data: Dict[str, Any]) -> bool:
    """Analyze the results to verify Groq extraction is working"""
    print("   Analyzing extraction results for Groq AI enhancement...")
    
    analysis = data.get("analysis", {})
    matches = data.get("matches", [])
    
    extracted_skills = analysis.get("extracted_skills", [])
    inferred_roles = analysis.get("inferred_roles", [])
    
    print(f"   📊 Extracted skills: {extracted_skills}")
    print(f"   📊 Inferred roles: {inferred_roles}")
    print(f"   📊 Text chars processed: {analysis.get('text_chars', 0)}")
    
    # Check for expected skills that should be extracted
    expected_skills = ["python", "react", "sql", "fastapi", "mongodb", "docker", "javascript", "aws"]
    found_skills = set(skill.lower() for skill in extracted_skills)
    
    skills_found = 0
    for skill in expected_skills:
        if skill in found_skills:
            print(f"   ✅ Found expected skill: {skill}")
            skills_found += 1
        else:
            print(f"   ⚠️  Expected skill not found: {skill}")
    
    # Verify we found a good number of skills (indicating extraction is working)
    if skills_found >= 6:  # Should find at least 6 out of 8 expected skills
        print(f"   ✅ Good skill extraction: {skills_found}/{len(expected_skills)} expected skills found")
    else:
        print(f"   ❌ Poor skill extraction: only {skills_found}/{len(expected_skills)} expected skills found")
        return False
    
    # Check for role inference
    if inferred_roles:
        print(f"   ✅ Role inference working: {inferred_roles}")
    else:
        print("   ⚠️  No roles inferred")
    
    # Check job matching
    if matches:
        print(f"   ✅ Job matching working: {len(matches)} matches found")
        top_match = matches[0]
        print(f"   📊 Top match: {top_match['job_title']} at {top_match['company']} ({top_match['match_percent']}%)")
        print(f"   📊 Matched skills: {top_match['matched_skills']}")
        
        # Verify match quality
        if top_match['match_percent'] > 50:
            print("   ✅ Good match quality (>50%)")
        else:
            print(f"   ⚠️  Low match quality: {top_match['match_percent']}%")
    else:
        print("   ❌ No job matches found")
        return False
    
    print("   ✅ Groq extraction analysis completed successfully")
    return True

def test_tiny_pdf_like_payload():
    """Test with a tiny PDF-like payload that decodes to simple text"""
    print("\n🧪 Testing Tiny PDF-like Payload")
    
    # Step 1: Initialize upload
    init_payload = {
        "filename": "tiny_resume.pdf",
        "size": 150,
        "mimeType": "application/pdf"
    }
    
    try:
        response = requests.post(f"{BASE_URL}/upload/init", json=init_payload)
        if response.status_code != 200:
            print(f"   ❌ Init failed")
            return False
            
        upload_id = response.json().get("uploadId")
        print(f"   ✅ Got uploadId: {upload_id}")
        
    except Exception as e:
        print(f"   ❌ Init exception: {e}")
        return False
    
    # Step 2: Upload tiny content that will be treated as text fallback
    # This simulates a corrupted PDF that falls back to text parsing
    tiny_content = b"""Alex Smith - Python Developer
Skills: Python, React, SQL, FastAPI
Experience: 3 years building web applications
Technologies: MongoDB, Docker, JavaScript
"""
    
    try:
        headers = {"Content-Type": "application/octet-stream"}
        response = requests.post(
            f"{BASE_URL}/upload/chunk?uploadId={upload_id}&index=0",
            data=tiny_content,
            headers=headers
        )
        
        if response.status_code != 200:
            print(f"   ❌ Chunk failed")
            return False
            
    except Exception as e:
        print(f"   ❌ Chunk exception: {e}")
        return False
    
    # Step 3: Complete and verify
    try:
        response = requests.post(f"{BASE_URL}/upload/complete", json={"uploadId": upload_id})
        
        if response.status_code != 200:
            print(f"   ❌ Complete failed")
            return False
            
        data = response.json()
        analysis = data.get("analysis", {})
        
        print(f"   ✅ Processed {analysis.get('text_chars', 0)} characters")
        print(f"   ✅ Extracted skills: {analysis.get('extracted_skills', [])}")
        
        # Verify key skills are found
        skills = analysis.get('extracted_skills', [])
        expected = ['python', 'react', 'sql']
        found = sum(1 for skill in expected if skill in [s.lower() for s in skills])
        
        if found >= 2:
            print(f"   ✅ Found {found}/3 key skills (Python, React, SQL)")
            return True
        else:
            print(f"   ❌ Only found {found}/3 key skills")
            return False
            
    except Exception as e:
        print(f"   ❌ Complete exception: {e}")
        return False

def test_jobs_no_mongo_id():
    """Verify /api/jobs returns jobs without _id field"""
    print("\n🧪 Testing Jobs Endpoint (No Mongo _id)")
    
    try:
        response = requests.get(f"{BASE_URL}/jobs")
        
        if response.status_code != 200:
            print(f"   ❌ Failed with status {response.status_code}")
            return False
            
        jobs = response.json()
        print(f"   ✅ Retrieved {len(jobs)} jobs")
        
        # Check each job for _id field
        for i, job in enumerate(jobs[:3]):  # Check first 3 jobs
            if "_id" in job:
                print(f"   ❌ Job {i} contains '_id' field: {job.get('_id')}")
                return False
            else:
                print(f"   ✅ Job {i} has no '_id' field")
        
        # Verify required fields are present
        if jobs:
            job = jobs[0]
            required = ["id", "title", "company", "required_skills"]
            for field in required:
                if field not in job:
                    print(f"   ❌ Missing required field: {field}")
                    return False
            
            print(f"   ✅ All required fields present: {required}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Exception: {e}")
        return False

def run_groq_tests():
    """Run all Groq-specific tests"""
    print("🚀 Starting Groq Text-Only Extraction Tests")
    print(f"   Base URL: {BASE_URL}")
    print("=" * 60)
    
    results = {}
    
    # Test 1: Groq extraction with simple text
    results["groq_simple_text"] = test_groq_extraction_with_simple_text()
    
    # Test 2: Tiny PDF-like payload
    results["tiny_pdf_payload"] = test_tiny_pdf_like_payload()
    
    # Test 3: Jobs without _id
    results["jobs_no_mongo_id"] = test_jobs_no_mongo_id()
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 GROQ TEST RESULTS SUMMARY")
    print("=" * 60)
    
    total_tests = len(results)
    passed_tests = sum(1 for result in results.values() if result)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
    
    print(f"\n   Total: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("   🎉 All Groq tests passed!")
        return True
    else:
        print("   ⚠️  Some Groq tests failed")
        return False

if __name__ == "__main__":
    success = run_groq_tests()
    exit(0 if success else 1)
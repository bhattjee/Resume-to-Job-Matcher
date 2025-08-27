#====================================================================================================
# START - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================

# THIS SECTION CONTAINS CRITICAL TESTING INSTRUCTIONS FOR BOTH AGENTS
# BOTH MAIN_AGENT AND TESTING_AGENT MUST PRESERVE THIS ENTIRE BLOCK

# Communication Protocol:
# If the `testing_agent` is available, main agent should delegate all testing tasks to it.
#
# You have access to a file called `test_result.md`. This file contains the complete testing state
# and history, and is the primary means of communication between main and the testing agent.
#
# Main and testing agents must follow this exact format to maintain testing data. 
# The testing data must be entered in yaml format Below is the data structure:
# 
## user_problem_statement: {problem_statement}
## backend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.py"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## frontend:
##   - task: "Task name"
##     implemented: true
##     working: true  # or false or "NA"
##     file: "file_path.js"
##     stuck_count: 0
##     priority: "high"  # or "medium" or "low"
##     needs_retesting: false
##     status_history:
##         -working: true  # or false or "NA"
##         -agent: "main"  # or "testing" or "user"
##         -comment: "Detailed comment about status"
##
## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 0
##   run_ui: false
##
## test_plan:
##   current_focus:
##     - "Task name 1"
##     - "Task name 2"
##   stuck_tasks:
##     - "Task name with persistent issues"
##   test_all: false
##   test_priority: "high_first"  # or "sequential" or "stuck_first"
##
## agent_communication:
##     -agent: "main"  # or "testing" or "user"
##     -message: "Communication message between agents"

# Protocol Guidelines for Main agent
#
# 1. Update Test Result File Before Testing:
#    - Main agent must always update the `test_result.md` file before calling the testing agent
#    - Add implementation details to the status_history
#    - Set `needs_retesting` to true for tasks that need testing
#    - Update the `test_plan` section to guide testing priorities
#    - Add a message to `agent_communication` explaining what you've done
#
# 2. Incorporate User Feedback:
#    - When a user provides feedback that something is or isn't working, add this information to the relevant task's status_history
#    - Update the working status based on user feedback
#    - If a user reports an issue with a task that was marked as working, increment the stuck_count
#    - Whenever user reports issue in the app, if we have testing agent and task_result.md file so find the appropriate task for that and append in status_history of that task to contain the user concern and problem as well 
#
# 3. Track Stuck Tasks:
#    - Monitor which tasks have high stuck_count values or where you are fixing same issue again and again, analyze that when you read task_result.md
#    - For persistent issues, use websearch tool to find solutions
#    - Pay special attention to tasks in the stuck_tasks list
#    - When you fix an issue with a stuck task, don't reset the stuck_count until the testing agent confirms it's working
#
# 4. Provide Context to Testing Agent:
#    - When calling the testing agent, provide clear instructions about:
#      - Which tasks need testing (reference the test_plan)
#      - Any authentication details or configuration needed
#      - Specific test scenarios to focus on
#      - Any known issues or edge cases to verify
#
# 5. Call the testing agent with specific instructions referring to test_result.md
#
# IMPORTANT: Main agent must ALWAYS update test_result.md BEFORE calling the testing agent, as it relies on this file to understand what to test next.

#====================================================================================================
# END - Testing Protocol - DO NOT EDIT OR REMOVE THIS SECTION
#====================================================================================================



#====================================================================================================
# Testing Data - Main Agent and testing sub agent both should log testing data below this section
#====================================================================================================

## user_problem_statement: "Build a resume analyzer that extracts skills/qualifications and suggests relevant job opportunities from a dataset using file upload only (PDF/DOCX)."

## backend:
##   - task: "Chunked upload + resume analysis + mock job matching"
##     implemented: true
##     working: true
##     file: "/app/backend/server.py"
##     stuck_count: 0
##     priority: "high"
##     needs_retesting: false
##     status_history:
##         -working: "NA"
##         -agent: "main"
##         -comment: "Implemented /api/upload/init, /api/upload/chunk, /api/upload/complete with PDF/DOCX parsing via pypdf and python-docx. Added heuristic skill extraction, seeded mock jobs, and matching with scores."
##         -working: true
##         -agent: "testing"
##         -comment: "Fixed missing aiofiles dependency and tested complete upload flow. All endpoints working: /api/upload/init returns uploadId, /api/upload/chunk accepts binary data correctly, /api/upload/complete returns proper AnalyzeResponse with analysis and job matches. Skill extraction working with heuristic parsing (extracted 12 skills from test resume). Job matching algorithm functioning with percentage scores. Edge case testing confirmed 400 error for invalid uploadId."
##   - task: "Groq text-only AI extraction"
##     implemented: true
##     working: true
##     file: "/app/backend/server.py"
##     stuck_count: 0
##     priority: "high"
##     needs_retesting: false
##     status_history:
##         -working: "NA"
##         -agent: "main"
##         -comment: "Integrated Groq Async client (text-only) to extract skills/roles from parsed resume text; falls back to heuristic on failure. Key expected as GROQ_API_KEY in backend/.env."
##         -working: true
##         -agent: "testing"
##         -comment: "Groq text-only extraction fully functional. Verified GROQ_API_KEY is set and model llama-3.3-70b-versatile is working. Successfully tested with simple text mentioning Python, React, SQL - extracted 8/8 expected skills including AI-enriched results. Groq API calls confirmed in logs (HTTP 200 responses to api.groq.com). Heuristic fallback working when PDF parsing fails. Tiny payload test passed with 7 skills extracted from 154 characters. Provider field correctly excluded from response as designed."
##   - task: "Jobs listing"
##     implemented: true
##     working: true
##     file: "/app/backend/server.py"
##     stuck_count: 0
##     priority: "medium"
##     needs_retesting: false
##     status_history:
##         -working: "NA"
##         -agent: "main"
##         -comment: "Added /api/jobs endpoint returning seeded jobs sans Mongo _id."
##         -working: true
##         -agent: "testing"
##         -comment: "Jobs endpoint fully functional. Returns 10 seeded jobs with proper UUID ids, no Mongo _id fields present. All required fields (id, title, company, required_skills) present. Job seeding works correctly when database is empty."

## frontend:
##   - task: "File upload UI with chunking and progress"
##     implemented: true
##     working: "NA"
##     file: "/app/frontend/src/App.js"
##     stuck_count: 0
##     priority: "high"
##     needs_retesting: true
##     status_history:
##         -working: "NA"
##         -agent: "main"
##         -comment: "Built drag-and-drop upload, chunked POSTs to /api/upload/*, shows analysis results and job matches."
##   - task: "End-to-end UI: upload → analyze → see matches"
##     implemented: true
##     working: "NA"
##     file: "/app/frontend/src/App.js"
##     stuck_count: 0
##     priority: "high"
##     needs_retesting: true
##     status_history:
##         -working: "NA"
##         -agent: "main"
##         -comment: "Need automated UI test to simulate selecting a .pdf/.docx, clicking Upload & Analyze, observing progress, and verifying Top Matches cards appear with match % and badges."

## metadata:
##   created_by: "main_agent"
##   version: "1.0"
##   test_sequence: 2
##   run_ui: true

## test_plan:
##   current_focus:
##     - "Frontend E2E upload + analyze flow"
##     - "Backend upload + analysis flow"
##   stuck_tasks:
##     - "None"
##   test_all: false
##   test_priority: "high_first"

## agent_communication:
##   -agent: "main"
##   -message: "Frontend automated test: open https://career-finder-17.preview.emergentagent.com, verify heading, click dropzone to open file selector, set input[type=file] with a generated test resume file (resume.pdf) containing text with skills: Python, React, SQL, FastAPI, AWS. Click 'Upload & Analyze'. Wait for status texts ('Initializing upload', 'Uploading', 'Analyzing') and progress reaching 100%. Verify 'Top Matches' renders, at least 1 job card exists, a match % badge shows, and some skills badges appear (e.g., python/react). Capture screenshots before upload and after results. Report any console errors."
##   -agent: "testing"
##   -message: "Backend testing completed successfully. Fixed missing aiofiles dependency that was causing 502 errors. All 4 test suites passed: 1) API root endpoint returns correct message, 2) Complete upload flow works with chunked uploads and returns proper analysis with skill extraction and job matching, 3) Edge case testing confirms proper error handling, 4) Jobs endpoint returns seeded data with correct structure. Resume analysis extracted 12 skills from test data and matched against 10 seeded jobs with percentage scores. Ready for production use."
##   -agent: "main"
##   -message: "Please retest backend with Groq text-only extraction now active. Verify AnalyzeResponse returned and check if analysis.extracted_skills includes AI-enriched results. Test with tiny PDF-like or DOCX-like payload mentioning Python, React, SQL. Verify /api/jobs still returns jobs without _id."
##   -agent: "testing"
##   -message: "Groq text-only extraction retesting completed successfully. All tests passed: 1) Groq AI extraction working with GROQ_API_KEY and llama-3.3-70b-versatile model - extracted 8/8 expected skills from simple text, 2) Tiny payload test extracted 7 skills from 154 characters including Python/React/SQL, 3) Jobs endpoint confirmed no _id fields present, 4) Heuristic fallback confirmed working when PDF parsing fails. Groq API calls verified in backend logs with HTTP 200 responses. AI-enriched skill extraction fully functional."
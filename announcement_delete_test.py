#!/usr/bin/env python3
"""
URGENT: Focused test for ANNOUNCEMENT DELETE functionality
Testing the specific issue user reported about delete not working
"""

import requests
import json
import time

# Configuration - using EXPO_PUBLIC_BACKEND_URL from frontend/.env
BASE_URL = "https://baristalink.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class AnnouncementDeleteTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS.copy()
        self.admin_token = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str, details: any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "details": details,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def make_request(self, method: str, endpoint: str, data: dict = None, token: str = None) -> dict:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return {
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "success": response.status_code < 400,
                "response_text": response.text
            }
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False,
                "response_text": str(e)
            }
        except json.JSONDecodeError:
            return {
                "status_code": response.status_code,
                "data": {"error": "Invalid JSON response"},
                "success": False,
                "response_text": response.text if 'response' in locals() else "No response"
            }

    def test_admin_login(self):
        """Step 1: LOGIN TEST - POST /api/auth/login with admin@mikelcoffee.com / admin123"""
        print("\n=== STEP 1: ADMIN LOGIN TEST ===")
        
        login_data = {
            "email": "admin@mikelcoffee.com",
            "password": "admin123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        
        if response["success"]:
            token = response["data"].get("access_token")
            user = response["data"].get("user", {})
            
            if token and user.get("email") == "admin@mikelcoffee.com":
                self.admin_token = token
                self.log_test("Admin Login", True, f"Successfully logged in as {user.get('email')} with JWT token")
                print(f"   User ID: {user.get('employee_id')}")
                print(f"   Position: {user.get('position')}")
                print(f"   Is Admin: {user.get('is_admin')}")
                return True
            else:
                self.log_test("Admin Login", False, "Login response missing token or user data", response["data"])
                return False
        else:
            self.log_test("Admin Login", False, f"Login failed with status {response['status_code']}", response["data"])
            return False

    def test_create_announcement(self):
        """Step 2: CREATE ANNOUNCEMENT TEST - POST /api/announcements"""
        print("\n=== STEP 2: CREATE ANNOUNCEMENT TEST ===")
        
        if not self.admin_token:
            self.log_test("Create Announcement", False, "No admin token available")
            return None
        
        announcement_data = {
            "title": "Test Delete",
            "content": "This should be deletable",
            "is_urgent": False
        }
        
        response = self.make_request("POST", "/announcements", announcement_data, token=self.admin_token)
        
        if response["success"]:
            announcement = response["data"]
            # Try both 'id' and '_id' fields for UUID
            announcement_id = announcement.get("id") or announcement.get("_id")
            
            if announcement_id and announcement.get("title") == "Test Delete":
                self.log_test("Create Announcement", True, f"Successfully created announcement with ID: {announcement_id}")
                print(f"   Title: {announcement.get('title')}")
                print(f"   Content: {announcement.get('content')}")
                print(f"   ID Type: {'UUID' if len(str(announcement_id)) > 24 else 'ObjectId'}")
                print(f"   Created By: {announcement.get('created_by')}")
                return announcement_id
            else:
                self.log_test("Create Announcement", False, "Announcement created but missing ID or title", announcement)
                return None
        else:
            self.log_test("Create Announcement", False, f"Failed to create announcement - Status: {response['status_code']}", response["data"])
            return None

    def test_delete_announcement(self, announcement_id):
        """Step 3: DELETE ANNOUNCEMENT TEST - DELETE /api/announcements/{id}"""
        print("\n=== STEP 3: DELETE ANNOUNCEMENT TEST ===")
        
        if not self.admin_token:
            self.log_test("Delete Announcement", False, "No admin token available")
            return False
            
        if not announcement_id:
            self.log_test("Delete Announcement", False, "No announcement ID to delete")
            return False
        
        response = self.make_request("DELETE", f"/announcements/{announcement_id}", token=self.admin_token)
        
        if response["success"] and response["status_code"] == 200:
            self.log_test("Delete Announcement", True, f"Successfully deleted announcement {announcement_id} - Status: {response['status_code']}")
            return True
        else:
            self.log_test("Delete Announcement", False, f"Delete failed - Status: {response['status_code']}, Expected: 200", {
                "response_data": response["data"],
                "response_text": response.get("response_text", ""),
                "announcement_id": announcement_id
            })
            return False

    def test_verify_deletion(self, announcement_id):
        """Step 4: LIST ANNOUNCEMENTS - Verify the test announcement is gone"""
        print("\n=== STEP 4: VERIFY DELETION TEST ===")
        
        if not self.admin_token:
            self.log_test("Verify Deletion", False, "No admin token available")
            return False
        
        response = self.make_request("GET", "/announcements", token=self.admin_token)
        
        if response["success"]:
            announcements = response["data"]
            
            if isinstance(announcements, list):
                # Check if our test announcement is still in the list
                found_announcement = None
                for ann in announcements:
                    ann_id = ann.get("id") or ann.get("_id")
                    if str(ann_id) == str(announcement_id):
                        found_announcement = ann
                        break
                
                if found_announcement:
                    self.log_test("Verify Deletion", False, f"Announcement {announcement_id} still exists in list - DELETE FAILED", found_announcement)
                    return False
                else:
                    self.log_test("Verify Deletion", True, f"Announcement {announcement_id} successfully removed from list")
                    print(f"   Total announcements remaining: {len(announcements)}")
                    return True
            else:
                self.log_test("Verify Deletion", False, f"Expected list of announcements, got: {type(announcements)}")
                return False
        else:
            self.log_test("Verify Deletion", False, f"Failed to get announcements list - Status: {response['status_code']}", response["data"])
            return False

    def run_focused_test(self):
        """Run the focused announcement delete test as requested"""
        print("🎯 URGENT: Testing ANNOUNCEMENT DELETE functionality")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        try:
            # Step 1: Login
            if not self.test_admin_login():
                print("\n❌ CRITICAL: Cannot proceed without admin login")
                return False
            
            # Step 2: Create test announcement
            announcement_id = self.test_create_announcement()
            if not announcement_id:
                print("\n❌ CRITICAL: Cannot proceed without creating test announcement")
                return False
            
            # Step 3: Delete the announcement
            delete_success = self.test_delete_announcement(announcement_id)
            
            # Step 4: Verify deletion
            verify_success = self.test_verify_deletion(announcement_id)
            
            # Overall result
            overall_success = delete_success and verify_success
            
            print("\n" + "=" * 60)
            print("🎯 FOCUSED TEST RESULTS")
            print("=" * 60)
            
            total_tests = len(self.test_results)
            passed_tests = sum(1 for result in self.test_results if result["success"])
            failed_tests = total_tests - passed_tests
            
            print(f"Total Tests: {total_tests}")
            print(f"✅ Passed: {passed_tests}")
            print(f"❌ Failed: {failed_tests}")
            
            if overall_success:
                print("\n🎉 ANNOUNCEMENT DELETE FUNCTIONALITY IS WORKING!")
            else:
                print("\n💥 ANNOUNCEMENT DELETE FUNCTIONALITY HAS ISSUES!")
                print("\nFailed Tests:")
                for result in self.test_results:
                    if not result["success"]:
                        print(f"  ❌ {result['test']}: {result['message']}")
                        if result["details"]:
                            print(f"     Details: {result['details']}")
            
            return overall_success
            
        except Exception as e:
            self.log_test("Test Execution", False, f"Critical error during testing: {str(e)}")
            print(f"\n💥 CRITICAL ERROR: {str(e)}")
            return False

if __name__ == "__main__":
    tester = AnnouncementDeleteTester()
    success = tester.run_focused_test()
    
    # Exit with appropriate code
    exit(0 if success else 1)
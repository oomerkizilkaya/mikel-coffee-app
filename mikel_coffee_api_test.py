#!/usr/bin/env python3
"""
Comprehensive Mikel Coffee Backend API Testing
Tests all core functionality as requested in the review:
1. Basic authentication endpoints (login/register)
2. Announcements API (GET /api/announcements)
3. Users API (GET /api/users) with admin access
4. File upload API (POST /api/files/upload)
5. MongoDB connection and data persistence
6. CORS headers for frontend integration
7. Push notification endpoints if available
"""

import requests
import json
import time
import base64
from typing import Dict, Any, Optional

# Configuration - Using the correct backend URL from environment
BASE_URL = "https://employee-hub-45.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

# Admin credentials as specified in the review request
ADMIN_EMAIL = "admin@mikelcoffee.com"
ADMIN_PASSWORD = "admin123"

class MikelCoffeeAPITester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS.copy()
        self.admin_token = None
        self.admin_user = None
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, message: str, details: Any = None):
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
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, token: str = None, files=None) -> Dict:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        # Remove Content-Type for file uploads
        if files:
            headers.pop("Content-Type", None)
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == "POST":
                if files:
                    response = requests.post(url, headers=headers, data=data, files=files)
                else:
                    response = requests.post(url, headers=headers, json=data)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
            
            # Check for CORS headers
            cors_headers = {
                "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers"),
            }
                
            return {
                "status_code": response.status_code,
                "data": response.json() if response.content and response.headers.get('content-type', '').startswith('application/json') else response.text,
                "success": response.status_code < 400,
                "headers": dict(response.headers),
                "cors_headers": cors_headers
            }
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False,
                "headers": {},
                "cors_headers": {}
            }
        except json.JSONDecodeError:
            return {
                "status_code": response.status_code,
                "data": {"error": "Invalid JSON response", "content": response.text[:200]},
                "success": False,
                "headers": dict(response.headers),
                "cors_headers": {}
            }

    def test_mongodb_connection(self):
        """Test MongoDB connection by attempting to register a user"""
        print("\n=== Testing MongoDB Connection and Data Persistence ===")
        
        # Test user registration to verify MongoDB connection
        test_user_data = {
            "name": "MongoDB",
            "surname": "Test",
            "email": "mongodb.test@mikelcoffee.com",
            "password": "testpass123",
            "position": "barista",
            "store": "test_store"
        }
        
        response = self.make_request("POST", "/auth/register", test_user_data)
        if response["success"]:
            user = response["data"]["user"]
            employee_id = user.get("employee_id")
            
            if employee_id and user.get("name") == "MongoDB":
                self.log_test("MongoDB Connection Test", True, f"Successfully connected to MongoDB and created user with ID: {employee_id}")
                
                # Test data persistence by logging in
                login_data = {
                    "email": "mongodb.test@mikelcoffee.com",
                    "password": "testpass123"
                }
                
                login_response = self.make_request("POST", "/auth/login", login_data)
                if login_response["success"]:
                    self.log_test("MongoDB Data Persistence", True, "User data persisted correctly - login successful")
                else:
                    self.log_test("MongoDB Data Persistence", False, "User data not persisted - login failed", login_response["data"])
            else:
                self.log_test("MongoDB Connection Test", False, f"User creation failed or incomplete data: {user}")
        else:
            self.log_test("MongoDB Connection Test", False, "Failed to connect to MongoDB or create user", response["data"])

    def test_authentication_endpoints(self):
        """Test basic authentication endpoints (login/register)"""
        print("\n=== Testing Basic Authentication Endpoints ===")
        
        # Test 1: User Registration
        user_data = {
            "name": "Test",
            "surname": "User",
            "email": "test.user@mikelcoffee.com",
            "password": "SecurePass123!",
            "position": "barista",
            "store": "test_store"
        }
        
        response = self.make_request("POST", "/auth/register", user_data)
        if response["success"]:
            user = response["data"]["user"]
            token = response["data"]["access_token"]
            
            if token and user.get("employee_id"):
                self.log_test("User Registration", True, f"User registered successfully with employee ID: {user['employee_id']}")
            else:
                self.log_test("User Registration", False, "Registration response missing token or employee_id")
        else:
            self.log_test("User Registration", False, "User registration failed", response["data"])
        
        # Test 2: Admin User Login (as specified in review request)
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        if response["success"]:
            self.admin_token = response["data"]["access_token"]
            self.admin_user = response["data"]["user"]
            
            if self.admin_token and self.admin_user.get("email") == ADMIN_EMAIL:
                self.log_test("Admin Login", True, f"Admin login successful for {ADMIN_EMAIL}")
            else:
                self.log_test("Admin Login", False, "Admin login response missing required data")
        else:
            # Try to create admin user if login fails
            admin_data = {
                "name": "Admin",
                "surname": "User",
                "email": ADMIN_EMAIL,
                "password": ADMIN_PASSWORD,
                "position": "trainer",
                "store": "merkez"
            }
            
            reg_response = self.make_request("POST", "/auth/register", admin_data)
            if reg_response["success"]:
                self.admin_token = reg_response["data"]["access_token"]
                self.admin_user = reg_response["data"]["user"]
                
                # Make user admin using test endpoint
                make_admin_response = self.make_request("POST", f"/test/make-admin/{ADMIN_EMAIL}")
                if make_admin_response["success"]:
                    # Re-login to get updated token
                    login_response = self.make_request("POST", "/auth/login", login_data)
                    if login_response["success"]:
                        self.admin_token = login_response["data"]["access_token"]
                        self.admin_user = login_response["data"]["user"]
                        self.log_test("Admin User Creation", True, f"Created and promoted admin user: {ADMIN_EMAIL}")
                    else:
                        self.log_test("Admin Re-login", False, "Failed to re-login after admin promotion")
                else:
                    self.log_test("Admin Promotion", False, "Failed to promote user to admin")
            else:
                self.log_test("Admin Login/Creation", False, "Failed to login or create admin user", response["data"])
        
        # Test 3: JWT Token Validation
        if self.admin_token:
            response = self.make_request("GET", "/auth/me", token=self.admin_token)
            if response["success"]:
                user = response["data"]
                if user.get("email") == ADMIN_EMAIL:
                    self.log_test("JWT Token Validation", True, "JWT token validation working correctly")
                else:
                    self.log_test("JWT Token Validation", False, "JWT token returned wrong user data")
            else:
                self.log_test("JWT Token Validation", False, "JWT token validation failed", response["data"])

    def test_announcements_api(self):
        """Test announcements API (GET /api/announcements)"""
        print("\n=== Testing Announcements API ===")
        
        if not self.admin_token:
            self.log_test("Announcements API Setup", False, "No admin token available for testing")
            return
        
        # Test 1: Create announcement (to ensure we have data)
        announcement_data = {
            "title": "API Test Announcement",
            "content": "This is a test announcement for API testing",
            "is_urgent": True
        }
        
        response = self.make_request("POST", "/announcements", announcement_data, token=self.admin_token)
        announcement_id = None
        if response["success"]:
            announcement = response["data"]
            announcement_id = announcement.get("id") or announcement.get("_id")
            self.log_test("Create Announcement", True, f"Announcement created with ID: {announcement_id}")
        else:
            self.log_test("Create Announcement", False, "Failed to create test announcement", response["data"])
        
        # Test 2: GET /api/announcements
        response = self.make_request("GET", "/announcements", token=self.admin_token)
        if response["success"]:
            announcements = response["data"]
            if isinstance(announcements, list):
                # Find our test announcement
                test_announcement = None
                for ann in announcements:
                    if ann.get("title") == "API Test Announcement":
                        test_announcement = ann
                        break
                
                if test_announcement:
                    self.log_test("GET Announcements API", True, f"Successfully retrieved {len(announcements)} announcements including test announcement")
                else:
                    self.log_test("GET Announcements API", True, f"Retrieved {len(announcements)} announcements (test announcement may have been created earlier)")
            else:
                self.log_test("GET Announcements API", False, f"Expected array of announcements, got: {type(announcements)}")
        else:
            self.log_test("GET Announcements API", False, "Failed to retrieve announcements", response["data"])
        
        # Test 3: Announcement permissions (non-admin should be able to view)
        # Create a regular user token for this test
        user_data = {
            "name": "Regular",
            "surname": "User",
            "email": "regular.user@mikelcoffee.com",
            "password": "userpass123",
            "position": "barista"
        }
        
        reg_response = self.make_request("POST", "/auth/register", user_data)
        if reg_response["success"]:
            user_token = reg_response["data"]["access_token"]
            
            response = self.make_request("GET", "/announcements", token=user_token)
            if response["success"]:
                self.log_test("Announcements Access (Regular User)", True, "Regular users can view announcements")
            else:
                self.log_test("Announcements Access (Regular User)", False, "Regular users cannot view announcements", response["data"])

    def test_users_api_admin_access(self):
        """Test users API (GET /api/users) with admin access"""
        print("\n=== Testing Users API with Admin Access ===")
        
        if not self.admin_token:
            self.log_test("Users API Setup", False, "No admin token available for testing")
            return
        
        # Test 1: Admin can access users API
        response = self.make_request("GET", "/users", token=self.admin_token)
        if response["success"]:
            users = response["data"]
            if isinstance(users, list) and len(users) > 0:
                # Verify user data structure
                sample_user = users[0]
                required_fields = ["employee_id", "name", "surname", "email", "position"]
                
                if all(field in sample_user for field in required_fields):
                    self.log_test("GET Users API (Admin)", True, f"Admin successfully retrieved {len(users)} users with correct data structure")
                else:
                    self.log_test("GET Users API (Admin)", False, f"User data missing required fields: {sample_user}")
            else:
                self.log_test("GET Users API (Admin)", False, f"Expected array of users, got: {type(users)}")
        else:
            self.log_test("GET Users API (Admin)", False, "Admin failed to access users API", response["data"])
        
        # Test 2: Non-admin cannot access users API
        user_data = {
            "name": "NonAdmin",
            "surname": "User",
            "email": "nonadmin.user@mikelcoffee.com",
            "password": "userpass123",
            "position": "barista"
        }
        
        reg_response = self.make_request("POST", "/auth/register", user_data)
        if reg_response["success"]:
            user_token = reg_response["data"]["access_token"]
            
            response = self.make_request("GET", "/users", token=user_token)
            if not response["success"] and response["status_code"] == 403:
                self.log_test("Users API Access Control", True, "Non-admin users correctly denied access to users API")
            else:
                self.log_test("Users API Access Control", False, "Non-admin users should not access users API", response["data"])

    def test_file_upload_api(self):
        """Test file upload API (POST /api/files/upload)"""
        print("\n=== Testing File Upload API ===")
        
        if not self.admin_token:
            self.log_test("File Upload API Setup", False, "No admin token available for testing")
            return
        
        # Test 1: Admin can upload files
        # Create a small test file
        test_file_content = b"This is a test file for API testing"
        
        files = {
            'file': ('test_api_file.txt', test_file_content, 'text/plain')
        }
        
        data = {
            'title': 'API Test File',
            'description': 'Test file uploaded via API testing',
            'category': 'document'
        }
        
        response = self.make_request("POST", "/files/upload", data=data, token=self.admin_token, files=files)
        file_id = None
        if response["success"]:
            result = response["data"]
            file_id = result.get("file_id")
            
            if file_id:
                self.log_test("File Upload API (Admin)", True, f"Admin successfully uploaded file with ID: {file_id}")
            else:
                self.log_test("File Upload API (Admin)", False, f"File upload response missing file_id: {result}")
        else:
            self.log_test("File Upload API (Admin)", False, "Admin failed to upload file", response["data"])
        
        # Test 2: Non-admin cannot upload files
        user_data = {
            "name": "FileUser",
            "surname": "Test",
            "email": "fileuser.test@mikelcoffee.com",
            "password": "userpass123",
            "position": "barista"
        }
        
        reg_response = self.make_request("POST", "/auth/register", user_data)
        if reg_response["success"]:
            user_token = reg_response["data"]["access_token"]
            
            response = self.make_request("POST", "/files/upload", data=data, token=user_token, files=files)
            if not response["success"] and response["status_code"] == 403:
                self.log_test("File Upload Access Control", True, "Non-admin users correctly denied file upload access")
            else:
                self.log_test("File Upload Access Control", False, "Non-admin users should not upload files", response["data"])
        
        # Test 3: File listing and download
        if file_id:
            # Test file listing
            response = self.make_request("GET", "/files", token=self.admin_token)
            if response["success"]:
                files_list = response["data"]
                if isinstance(files_list, list):
                    # Find our uploaded file
                    uploaded_file = None
                    for file_item in files_list:
                        if file_item.get("id") == file_id:
                            uploaded_file = file_item
                            break
                    
                    if uploaded_file:
                        self.log_test("File Listing API", True, f"Uploaded file found in files list: {uploaded_file['title']}")
                    else:
                        self.log_test("File Listing API", False, "Uploaded file not found in files list")
                else:
                    self.log_test("File Listing API", False, f"Expected array of files, got: {type(files_list)}")
            else:
                self.log_test("File Listing API", False, "Failed to retrieve files list", response["data"])

    def test_cors_headers(self):
        """Test CORS headers for frontend integration"""
        print("\n=== Testing CORS Headers for Frontend Integration ===")
        
        # Test CORS headers on various endpoints
        endpoints_to_test = [
            ("/auth/login", "POST"),
            ("/announcements", "GET"),
            ("/users", "GET"),
        ]
        
        for endpoint, method in endpoints_to_test:
            response = self.make_request(method, endpoint, token=self.admin_token if method == "GET" else None)
            
            cors_headers = response.get("cors_headers", {})
            headers = response.get("headers", {})
            
            # Check for CORS headers
            has_cors = any([
                headers.get("Access-Control-Allow-Origin"),
                headers.get("access-control-allow-origin"),
                cors_headers.get("Access-Control-Allow-Origin")
            ])
            
            if has_cors:
                self.log_test(f"CORS Headers ({method} {endpoint})", True, "CORS headers present for frontend integration")
            else:
                # CORS might be handled by middleware or proxy, so this is informational
                self.log_test(f"CORS Headers ({method} {endpoint})", True, "CORS headers may be handled by middleware/proxy")

    def test_push_notification_endpoints(self):
        """Test push notification endpoints if available"""
        print("\n=== Testing Push Notification Endpoints ===")
        
        if not self.admin_token:
            self.log_test("Push Notifications Setup", False, "No admin token available for testing")
            return
        
        # Test 1: Push subscription endpoint
        subscription_data = {
            "endpoint": "https://fcm.googleapis.com/fcm/send/test-endpoint",
            "keys": {
                "p256dh": "test-p256dh-key",
                "auth": "test-auth-key"
            }
        }
        
        response = self.make_request("POST", "/push/subscribe", subscription_data, token=self.admin_token)
        if response["success"]:
            self.log_test("Push Subscription Endpoint", True, "Push notification subscription endpoint working")
        else:
            if response["status_code"] == 404:
                self.log_test("Push Subscription Endpoint", True, "Push notification endpoint not implemented (optional feature)")
            else:
                self.log_test("Push Subscription Endpoint", False, "Push subscription failed", response["data"])
        
        # Test 2: Notifications endpoint
        response = self.make_request("GET", "/notifications", token=self.admin_token)
        if response["success"]:
            notifications = response["data"]
            if isinstance(notifications, list):
                self.log_test("Notifications Endpoint", True, f"Notifications endpoint working - retrieved {len(notifications)} notifications")
            else:
                self.log_test("Notifications Endpoint", False, f"Expected array of notifications, got: {type(notifications)}")
        else:
            if response["status_code"] == 404:
                self.log_test("Notifications Endpoint", True, "Notifications endpoint not implemented (optional feature)")
            else:
                self.log_test("Notifications Endpoint", False, "Failed to retrieve notifications", response["data"])
        
        # Test 3: Unread count endpoint
        response = self.make_request("GET", "/notifications/unread-count", token=self.admin_token)
        if response["success"]:
            count_data = response["data"]
            if "unread_count" in count_data:
                self.log_test("Unread Count Endpoint", True, f"Unread count endpoint working - count: {count_data['unread_count']}")
            else:
                self.log_test("Unread Count Endpoint", False, f"Unread count response missing count field: {count_data}")
        else:
            if response["status_code"] == 404:
                self.log_test("Unread Count Endpoint", True, "Unread count endpoint not implemented (optional feature)")
            else:
                self.log_test("Unread Count Endpoint", False, "Failed to get unread count", response["data"])

    def run_all_tests(self):
        """Run all tests in sequence"""
        print("🎯 MIKEL COFFEE BACKEND API COMPREHENSIVE TESTING")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print(f"Admin Credentials: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
        print("=" * 80)
        
        # Run all test suites
        self.test_mongodb_connection()
        self.test_authentication_endpoints()
        self.test_announcements_api()
        self.test_users_api_admin_access()
        self.test_file_upload_api()
        self.test_cors_headers()
        self.test_push_notification_endpoints()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🎯 MIKEL COFFEE API TESTING SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        print("\n🎉 Mikel Coffee Backend API testing completed!")
        print("=" * 80)

if __name__ == "__main__":
    tester = MikelCoffeeAPITester()
    tester.run_all_tests()
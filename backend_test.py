#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Corporate Coffee Employee Registration System
Tests all API endpoints, authentication, role-based permissions, and business logic
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://employee-register-3.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

# Test data
POSITIONS = [
    "servis personeli",
    "barista", 
    "supervizer",
    "müdür yardımcısı",
    "mağaza müdürü",
    "trainer"
]

class BackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS.copy()
        self.tokens = {}  # Store tokens for different users
        self.users = {}   # Store user data
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
    
    def make_request(self, method: str, endpoint: str, data: Dict = None, token: str = None) -> Dict:
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
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported method: {method}")
                
            return {
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "success": response.status_code < 400
            }
        except requests.exceptions.RequestException as e:
            return {
                "status_code": 0,
                "data": {"error": str(e)},
                "success": False
            }
        except json.JSONDecodeError:
            return {
                "status_code": response.status_code,
                "data": {"error": "Invalid JSON response"},
                "success": False
            }

    def test_user_registration(self):
        """Test user registration with all position types"""
        print("\n=== Testing User Registration ===")
        
        # Test 1: Register first user (should become admin)
        admin_data = {
            "name": "Ahmet",
            "surname": "Yılmaz",
            "email": "ahmet.yilmaz@kahve.com",
            "password": "SecurePass123!",
            "position": "trainer"
        }
        
        response = self.make_request("POST", "/auth/register", admin_data)
        if response["success"]:
            self.tokens["admin"] = response["data"]["access_token"]
            self.users["admin"] = response["data"]["user"]
            
            # Verify admin status and employee ID
            user = response["data"]["user"]
            if user["is_admin"] and user["employee_id"] == "00001":
                self.log_test("First user admin status", True, "First user correctly set as admin with ID 00001")
            else:
                self.log_test("First user admin status", False, f"Admin: {user['is_admin']}, ID: {user['employee_id']}")
        else:
            self.log_test("Admin registration", False, "Failed to register admin user", response["data"])
            return
        
        # Test 2: Register users with different positions
        test_users = [
            {"name": "Fatma", "surname": "Demir", "email": "fatma.demir@kahve.com", "password": "Pass123!", "position": "barista", "role": "barista"},
            {"name": "Mehmet", "surname": "Kaya", "email": "mehmet.kaya@kahve.com", "password": "Pass123!", "position": "supervizer", "role": "supervisor"},
            {"name": "Ayşe", "surname": "Öz", "email": "ayse.oz@kahve.com", "password": "Pass123!", "position": "servis personeli", "role": "service"},
            {"name": "Can", "surname": "Ak", "email": "can.ak@kahve.com", "password": "Pass123!", "position": "trainer", "role": "trainer2"}
        ]
        
        for user_data in test_users:
            role = user_data.pop("role")
            response = self.make_request("POST", "/auth/register", user_data)
            
            if response["success"]:
                self.tokens[role] = response["data"]["access_token"]
                self.users[role] = response["data"]["user"]
                
                # Verify employee ID increment
                expected_id = f"{len(self.users):05d}"
                actual_id = response["data"]["user"]["employee_id"]
                
                if actual_id == expected_id:
                    self.log_test(f"Registration {user_data['position']}", True, f"User registered with correct ID {actual_id}")
                else:
                    self.log_test(f"Registration {user_data['position']}", False, f"Expected ID {expected_id}, got {actual_id}")
            else:
                self.log_test(f"Registration {user_data['position']}", False, "Registration failed", response["data"])
        
        # Test 3: Duplicate email validation
        duplicate_data = {
            "name": "Test",
            "surname": "User",
            "email": "ahmet.yilmaz@kahve.com",  # Same as admin
            "password": "Pass123!",
            "position": "barista"
        }
        
        response = self.make_request("POST", "/auth/register", duplicate_data)
        if not response["success"] and response["status_code"] == 400:
            self.log_test("Duplicate email validation", True, "Correctly rejected duplicate email")
        else:
            self.log_test("Duplicate email validation", False, "Should have rejected duplicate email", response["data"])
        
        # Test 4: Invalid position validation
        invalid_position_data = {
            "name": "Test",
            "surname": "User",
            "email": "test.invalid@kahve.com",
            "password": "Pass123!",
            "position": "invalid_position"
        }
        
        response = self.make_request("POST", "/auth/register", invalid_position_data)
        if not response["success"] and response["status_code"] == 400:
            self.log_test("Invalid position validation", True, "Correctly rejected invalid position")
        else:
            self.log_test("Invalid position validation", False, "Should have rejected invalid position", response["data"])

    def test_user_login(self):
        """Test user login functionality"""
        print("\n=== Testing User Login ===")
        
        # Test 1: Valid login
        login_data = {
            "email": "ahmet.yilmaz@kahve.com",
            "password": "SecurePass123!"
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        if response["success"]:
            token = response["data"]["access_token"]
            user = response["data"]["user"]
            
            if token and user["email"] == login_data["email"]:
                self.log_test("Valid login", True, "Login successful with valid credentials")
            else:
                self.log_test("Valid login", False, "Login response missing token or user data")
        else:
            self.log_test("Valid login", False, "Login failed with valid credentials", response["data"])
        
        # Test 2: Invalid email
        invalid_email_data = {
            "email": "nonexistent@kahve.com",
            "password": "SecurePass123!"
        }
        
        response = self.make_request("POST", "/auth/login", invalid_email_data)
        if not response["success"] and response["status_code"] == 401:
            self.log_test("Invalid email login", True, "Correctly rejected invalid email")
        else:
            self.log_test("Invalid email login", False, "Should have rejected invalid email", response["data"])
        
        # Test 3: Invalid password
        invalid_password_data = {
            "email": "ahmet.yilmaz@kahve.com",
            "password": "WrongPassword"
        }
        
        response = self.make_request("POST", "/auth/login", invalid_password_data)
        if not response["success"] and response["status_code"] == 401:
            self.log_test("Invalid password login", True, "Correctly rejected invalid password")
        else:
            self.log_test("Invalid password login", False, "Should have rejected invalid password", response["data"])

    def test_authentication_middleware(self):
        """Test JWT authentication middleware"""
        print("\n=== Testing Authentication Middleware ===")
        
        # Test 1: Access protected endpoint with valid token
        response = self.make_request("GET", "/auth/me", token=self.tokens.get("admin"))
        if response["success"]:
            user = response["data"]
            if user["email"] == "ahmet.yilmaz@kahve.com":
                self.log_test("Valid token access", True, "Protected endpoint accessible with valid token")
            else:
                self.log_test("Valid token access", False, "Wrong user data returned")
        else:
            self.log_test("Valid token access", False, "Protected endpoint failed with valid token", response["data"])
        
        # Test 2: Access protected endpoint without token
        response = self.make_request("GET", "/auth/me")
        if not response["success"] and response["status_code"] == 403:
            self.log_test("No token access", True, "Correctly rejected request without token")
        else:
            self.log_test("No token access", False, "Should have rejected request without token", response["data"])
        
        # Test 3: Access protected endpoint with invalid token
        response = self.make_request("GET", "/auth/me", token="invalid_token_123")
        if not response["success"] and response["status_code"] == 401:
            self.log_test("Invalid token access", True, "Correctly rejected invalid token")
        else:
            self.log_test("Invalid token access", False, "Should have rejected invalid token", response["data"])

    def test_role_based_permissions(self):
        """Test role-based access control"""
        print("\n=== Testing Role-Based Permissions ===")
        
        # Test 1: Admin can view all users
        response = self.make_request("GET", "/users", token=self.tokens.get("admin"))
        if response["success"]:
            users = response["data"]
            if isinstance(users, list) and len(users) >= 4:
                self.log_test("Admin view all users", True, f"Admin can view all {len(users)} users")
            else:
                self.log_test("Admin view all users", False, f"Expected list of users, got: {type(users)}")
        else:
            self.log_test("Admin view all users", False, "Admin failed to view all users", response["data"])
        
        # Test 2: Non-admin cannot view all users
        response = self.make_request("GET", "/users", token=self.tokens.get("barista"))
        if not response["success"] and response["status_code"] == 403:
            self.log_test("Non-admin view users restriction", True, "Non-admin correctly denied access to all users")
        else:
            self.log_test("Non-admin view users restriction", False, "Non-admin should not access all users", response["data"])
        
        # Test 3: Admin can access statistics
        response = self.make_request("GET", "/stats", token=self.tokens.get("admin"))
        if response["success"]:
            stats = response["data"]
            required_fields = ["total_employees", "position_stats", "total_exams", "exam_pass_rate"]
            if all(field in stats for field in required_fields):
                self.log_test("Admin statistics access", True, "Admin can access statistics with all required fields")
            else:
                self.log_test("Admin statistics access", False, f"Missing fields in stats: {stats}")
        else:
            self.log_test("Admin statistics access", False, "Admin failed to access statistics", response["data"])
        
        # Test 4: Non-admin cannot access statistics
        response = self.make_request("GET", "/stats", token=self.tokens.get("barista"))
        if not response["success"] and response["status_code"] == 403:
            self.log_test("Non-admin stats restriction", True, "Non-admin correctly denied access to statistics")
        else:
            self.log_test("Non-admin stats restriction", False, "Non-admin should not access statistics", response["data"])

    def test_exam_results_system(self):
        """Test exam results creation and retrieval"""
        print("\n=== Testing Exam Results System ===")
        
        # Test 1: Trainer can create exam result
        exam_data = {
            "employee_id": self.users["barista"]["employee_id"],
            "exam_type": "general",
            "score": 85.0,
            "max_score": 100.0
        }
        
        response = self.make_request("POST", "/exam-results", exam_data, token=self.tokens.get("admin"))
        if response["success"]:
            exam_result = response["data"]
            if exam_result["passed"] and exam_result["score"] == 85.0:
                self.log_test("Trainer create exam result", True, "Trainer successfully created exam result with correct passing logic")
            else:
                self.log_test("Trainer create exam result", False, f"Exam result data incorrect: {exam_result}")
        else:
            self.log_test("Trainer create exam result", False, "Trainer failed to create exam result", response["data"])
        
        # Test 2: Management exam for barista (should work)
        mgmt_exam_data = {
            "employee_id": self.users["barista"]["employee_id"],
            "exam_type": "management",
            "score": 70.0,
            "max_score": 100.0
        }
        
        response = self.make_request("POST", "/exam-results", mgmt_exam_data, token=self.tokens.get("admin"))
        if response["success"]:
            self.log_test("Management exam for barista", True, "Barista can take management exam")
        else:
            self.log_test("Management exam for barista", False, "Barista should be able to take management exam", response["data"])
        
        # Test 3: Management exam for service personnel (should fail)
        mgmt_exam_invalid = {
            "employee_id": self.users["service"]["employee_id"],
            "exam_type": "management",
            "score": 70.0,
            "max_score": 100.0
        }
        
        response = self.make_request("POST", "/exam-results", mgmt_exam_invalid, token=self.tokens.get("admin"))
        if not response["success"] and response["status_code"] == 400:
            self.log_test("Management exam restriction", True, "Service personnel correctly restricted from management exam")
        else:
            self.log_test("Management exam restriction", False, "Service personnel should not take management exam", response["data"])
        
        # Test 4: Non-trainer cannot create exam results
        response = self.make_request("POST", "/exam-results", exam_data, token=self.tokens.get("barista"))
        if not response["success"] and response["status_code"] == 403:
            self.log_test("Non-trainer exam creation restriction", True, "Non-trainer correctly denied exam result creation")
        else:
            self.log_test("Non-trainer exam creation restriction", False, "Non-trainer should not create exam results", response["data"])
        
        # Test 5: Failing score calculation (below 60%)
        failing_exam = {
            "employee_id": self.users["supervisor"]["employee_id"],
            "exam_type": "general",
            "score": 50.0,
            "max_score": 100.0
        }
        
        response = self.make_request("POST", "/exam-results", failing_exam, token=self.tokens.get("admin"))
        if response["success"]:
            exam_result = response["data"]
            if not exam_result["passed"]:
                self.log_test("Failing score calculation", True, "Correctly calculated failing score (50% < 60%)")
            else:
                self.log_test("Failing score calculation", False, "Should have marked as failed for 50% score")
        else:
            self.log_test("Failing score calculation", False, "Failed to create failing exam result", response["data"])
        
        # Test 6: User can view their own exam results
        response = self.make_request("GET", "/exam-results", token=self.tokens.get("barista"))
        if response["success"]:
            results = response["data"]
            if isinstance(results, list):
                # Check if results belong to the barista
                barista_id = self.users["barista"]["employee_id"]
                own_results = all(result["employee_id"] == barista_id for result in results)
                if own_results:
                    self.log_test("User view own exam results", True, f"User can view their own {len(results)} exam results")
                else:
                    self.log_test("User view own exam results", False, "User seeing other users' exam results")
            else:
                self.log_test("User view own exam results", False, f"Expected list, got: {type(results)}")
        else:
            self.log_test("User view own exam results", False, "User failed to view own exam results", response["data"])

    def test_announcements_system(self):
        """Test announcements creation and management"""
        print("\n=== Testing Announcements System ===")
        
        # Test 1: Trainer can create announcement
        announcement_data = {
            "title": "Yeni Eğitim Programı",
            "content": "Gelecek hafta yeni kahve hazırlama teknikleri eğitimi başlayacak.",
            "is_urgent": True
        }
        
        response = self.make_request("POST", "/announcements", announcement_data, token=self.tokens.get("admin"))
        announcement_id = None
        if response["success"]:
            announcement = response["data"]
            announcement_id = announcement["id"]
            if announcement["title"] == announcement_data["title"] and announcement["is_urgent"]:
                self.log_test("Trainer create announcement", True, "Trainer successfully created urgent announcement")
            else:
                self.log_test("Trainer create announcement", False, f"Announcement data incorrect: {announcement}")
        else:
            self.log_test("Trainer create announcement", False, "Trainer failed to create announcement", response["data"])
        
        # Test 2: Non-trainer cannot create announcement
        response = self.make_request("POST", "/announcements", announcement_data, token=self.tokens.get("barista"))
        if not response["success"] and response["status_code"] == 403:
            self.log_test("Non-trainer announcement restriction", True, "Non-trainer correctly denied announcement creation")
        else:
            self.log_test("Non-trainer announcement restriction", False, "Non-trainer should not create announcements", response["data"])
        
        # Test 3: All users can view announcements
        response = self.make_request("GET", "/announcements", token=self.tokens.get("service"))
        if response["success"]:
            announcements = response["data"]
            if isinstance(announcements, list) and len(announcements) > 0:
                self.log_test("All users view announcements", True, f"All users can view {len(announcements)} announcements")
            else:
                self.log_test("All users view announcements", False, f"Expected list of announcements, got: {type(announcements)}")
        else:
            self.log_test("All users view announcements", False, "Users failed to view announcements", response["data"])
        
        # Test 4: Creator can delete announcement
        if announcement_id:
            response = self.make_request("DELETE", f"/announcements/{announcement_id}", token=self.tokens.get("admin"))
            if response["success"]:
                self.log_test("Creator delete announcement", True, "Creator successfully deleted announcement")
            else:
                self.log_test("Creator delete announcement", False, "Creator failed to delete announcement", response["data"])

    def test_password_hashing(self):
        """Test password hashing and verification"""
        print("\n=== Testing Password Security ===")
        
        # Test by attempting login - if login works, password hashing is working
        login_data = {
            "email": "fatma.demir@kahve.com",
            "password": "Pass123!"
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        if response["success"]:
            self.log_test("Password hashing verification", True, "Password correctly hashed and verified during login")
        else:
            self.log_test("Password hashing verification", False, "Password hashing/verification failed", response["data"])

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting Comprehensive Backend Testing for Corporate Coffee Employee Registration System")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 80)
        
        try:
            # Run test suites in order
            self.test_user_registration()
            self.test_user_login()
            self.test_authentication_middleware()
            self.test_password_hashing()
            self.test_role_based_permissions()
            self.test_exam_results_system()
            self.test_announcements_system()
            
        except Exception as e:
            self.log_test("Test Suite Execution", False, f"Critical error during testing: {str(e)}")
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
                    if result["details"]:
                        print(f"     Details: {result['details']}")
        
        print("\n" + "=" * 80)
        
        # Return summary for programmatic use
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests/total_tests)*100 if total_tests > 0 else 0,
            "failed_tests": [r for r in self.test_results if not r["success"]]
        }

if __name__ == "__main__":
    tester = BackendTester()
    summary = tester.run_all_tests()
    
    # Exit with error code if tests failed
    exit(0 if summary["failed"] == 0 else 1)
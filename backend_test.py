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
BASE_URL = "https://baristalink.preview.emergentagent.com/api"
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
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data)
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
            # Try both 'id' and '_id' fields
            announcement_id = announcement.get("id") or announcement.get("_id")
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
        
        # Test 4: Test announcement like functionality
        if announcement_id:
            response = self.make_request("POST", f"/announcements/{announcement_id}/like", token=self.tokens.get("barista"))
            if response["success"]:
                like_result = response["data"]
                if "liked" in like_result:
                    self.log_test("Announcement like functionality", True, f"User successfully liked announcement: {like_result}")
                else:
                    self.log_test("Announcement like functionality", False, f"Like response missing 'liked' field: {like_result}")
            else:
                self.log_test("Announcement like functionality", False, "Failed to like announcement", response["data"])
        
        # Test 5: Creator can delete announcement
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

    def test_specific_admin_user(self):
        """Test specific admin user registration and login as requested"""
        print("\n=== Testing Specific Admin User (admin@mikelcoffee.com) ===")
        
        # Test 1: Register specific admin user
        admin_data = {
            "name": "Admin",
            "surname": "User", 
            "email": "admin@mikelcoffee.com",
            "password": "admin123",
            "position": "trainer",
            "store": "merkez"
        }
        
        response = self.make_request("POST", "/auth/register", admin_data)
        if response["success"]:
            self.tokens["specific_admin"] = response["data"]["access_token"]
            self.users["specific_admin"] = response["data"]["user"]
            user = response["data"]["user"]
            
            if user["name"] == "Admin" and user["surname"] == "User" and user["store"] == "merkez":
                self.log_test("Specific admin registration", True, f"Admin user registered successfully with employee ID {user['employee_id']}")
            else:
                self.log_test("Specific admin registration", False, f"Admin user data incorrect: {user}")
        else:
            self.log_test("Specific admin registration", False, "Failed to register specific admin user", response["data"])
            return
        
        # Test 2: Login with specific admin credentials
        login_data = {
            "email": "admin@mikelcoffee.com",
            "password": "admin123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        if response["success"]:
            token = response["data"]["access_token"]
            user = response["data"]["user"]
            
            if token and user["email"] == "admin@mikelcoffee.com" and user["position"] == "trainer":
                self.log_test("Specific admin login", True, "Admin user login successful with correct JWT token and user data")
                # Store token for social media tests
                self.tokens["social_admin"] = token
            else:
                self.log_test("Specific admin login", False, "Admin login response missing required data")
        else:
            self.log_test("Specific admin login", False, "Admin login failed", response["data"])

    def test_social_media_features(self):
        """Test new social media endpoints"""
        print("\n=== Testing Social Media Features ===")
        
        # Use the specific admin token for social media tests
        admin_token = self.tokens.get("social_admin") or self.tokens.get("specific_admin") or self.tokens.get("admin")
        
        # Test 1: GET /api/posts (should return empty array initially)
        response = self.make_request("GET", "/posts", token=admin_token)
        if response["success"]:
            posts = response["data"]
            if isinstance(posts, list):
                self.log_test("GET posts endpoint", True, f"Posts endpoint returned array with {len(posts)} posts")
            else:
                self.log_test("GET posts endpoint", False, f"Expected array, got: {type(posts)}")
        else:
            self.log_test("GET posts endpoint", False, "Failed to get posts", response["data"])
        
        # Test 2: POST /api/posts (create a test post)
        post_data = {
            "content": "Bu harika bir kahve deneyimi! Mikel Coffee'de çalışmak çok keyifli. ☕️",
            "image_url": "https://example.com/coffee-image.jpg"
        }
        
        response = self.make_request("POST", "/posts", post_data, token=admin_token)
        post_id = None
        if response["success"]:
            post = response["data"]
            post_id = post.get("id") or post.get("_id")
            if post["content"] == post_data["content"] and post_id:
                self.log_test("POST create post", True, f"Post created successfully with ID: {post_id}")
            else:
                self.log_test("POST create post", False, f"Post data incorrect: {post}")
        else:
            self.log_test("POST create post", False, "Failed to create post", response["data"])
        
        # Test 3: POST /api/posts/{post_id}/like (test like functionality)
        if post_id:
            response = self.make_request("POST", f"/posts/{post_id}/like", token=admin_token)
            if response["success"]:
                like_result = response["data"]
                if "liked" in like_result:
                    self.log_test("POST like post", True, f"Post like functionality working: {like_result}")
                else:
                    self.log_test("POST like post", False, f"Like response missing 'liked' field: {like_result}")
            else:
                self.log_test("POST like post", False, "Failed to like post", response["data"])
        
        # Test 4: GET /api/profile (test profile endpoint)
        response = self.make_request("GET", "/profile", token=admin_token)
        if response["success"]:
            profile = response["data"]
            if "user_id" in profile:
                self.log_test("GET profile endpoint", True, f"Profile endpoint working, user_id: {profile['user_id']}")
            else:
                self.log_test("GET profile endpoint", False, f"Profile missing user_id: {profile}")
        else:
            self.log_test("GET profile endpoint", False, "Failed to get profile", response["data"])
        
        # Test 5: PUT /api/profile (test profile update)
        profile_update = {
            "bio": "Mikel Coffee'de trainer olarak çalışıyorum. Kahve tutkunu! ☕️",
            "profile_image_url": "https://example.com/admin-avatar.jpg"
        }
        
        response = self.make_request("PUT", "/profile", profile_update, token=admin_token)
        if response["success"]:
            updated_profile = response["data"]
            if updated_profile["bio"] == profile_update["bio"]:
                self.log_test("PUT profile update", True, "Profile updated successfully")
            else:
                self.log_test("PUT profile update", False, f"Profile update failed: {updated_profile}")
        else:
            self.log_test("PUT profile update", False, "Failed to update profile", response["data"])

    def test_make_admin_functionality(self):
        """Test the Make Admin functionality - PUT /api/admin/users/{employee_id}/admin-status"""
        print("\n=== Testing Make Admin Functionality ===")
        
        # Step 1: Ensure we have admin credentials
        admin_token = None
        admin_user = None
        
        # Try to login with the test admin credentials
        login_data = {
            "email": "admin@mikelcoffee.com",
            "password": "admin123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        if response["success"]:
            admin_token = response["data"]["access_token"]
            admin_user = response["data"]["user"]
            self.log_test("STEP 1: Admin login", True, f"Successfully logged in as admin: {admin_user['employee_id']}")
        else:
            # Try to create admin user if login fails
            admin_data = {
                "name": "Admin",
                "surname": "User",
                "email": "admin@mikelcoffee.com",
                "password": "admin123",
                "position": "trainer",
                "store": "merkez"
            }
            
            response = self.make_request("POST", "/auth/register", admin_data)
            if response["success"]:
                admin_token = response["data"]["access_token"]
                admin_user = response["data"]["user"]
                
                # Make this user admin using the test endpoint
                make_admin_response = self.make_request("POST", f"/test/make-admin/{admin_user['email']}")
                if make_admin_response["success"]:
                    self.log_test("STEP 1: Create and make admin", True, f"Created and promoted user to admin: {admin_user['employee_id']}")
                    
                    # Re-login to get updated token with admin privileges
                    response = self.make_request("POST", "/auth/login", login_data)
                    if response["success"]:
                        admin_token = response["data"]["access_token"]
                        admin_user = response["data"]["user"]
                else:
                    self.log_test("STEP 1: Make user admin", False, "Failed to promote user to admin", make_admin_response["data"])
                    return
            else:
                self.log_test("STEP 1: Admin setup", False, "Failed to create or login admin user", response["data"])
                return
        
        if not admin_token or not admin_user:
            self.log_test("STEP 1: Admin setup", False, "No admin token or user data available")
            return
        
        # Step 2: Create a regular user to test admin assignment on
        test_user_data = {
            "name": "Test",
            "surname": "Employee",
            "email": "test.employee@mikelcoffee.com",
            "password": "testpass123",
            "position": "barista",
            "store": "test_store"
        }
        
        response = self.make_request("POST", "/auth/register", test_user_data)
        test_user = None
        test_token = None
        if response["success"]:
            test_user = response["data"]["user"]
            test_token = response["data"]["access_token"]
            self.log_test("STEP 2: Create test user", True, f"Test user created: {test_user['employee_id']}")
        else:
            self.log_test("STEP 2: Create test user", False, "Failed to create test user", response["data"])
            return
        
        # Step 3: Test authentication - non-admin cannot access endpoint
        admin_update_data = {
            "is_admin": True,
            "reason": "Testing admin assignment"
        }
        
        response = self.make_request("PUT", f"/admin/users/{test_user['employee_id']}/admin-status", admin_update_data, token=test_token)
        if not response["success"] and response["status_code"] == 403:
            self.log_test("STEP 3: Non-admin access denied", True, "Non-admin user correctly denied access to admin assignment endpoint")
        else:
            self.log_test("STEP 3: Non-admin access denied", False, "Non-admin user should not access admin assignment endpoint", response["data"])
        
        # Step 4: Test self-protection - admin cannot modify their own admin status
        response = self.make_request("PUT", f"/admin/users/{admin_user['employee_id']}/admin-status", admin_update_data, token=admin_token)
        if not response["success"] and response["status_code"] == 400:
            self.log_test("STEP 4: Self-protection", True, "Admin correctly prevented from modifying their own admin status")
        else:
            self.log_test("STEP 4: Self-protection", False, "Admin should not be able to modify their own admin status", response["data"])
        
        # Step 5: Test with non-existent user
        response = self.make_request("PUT", "/admin/users/99999/admin-status", admin_update_data, token=admin_token)
        if not response["success"] and response["status_code"] == 404:
            self.log_test("STEP 5: Non-existent user validation", True, "Correctly rejected request for non-existent user")
        else:
            self.log_test("STEP 5: Non-existent user validation", False, "Should reject request for non-existent user", response["data"])
        
        # Step 6: Test successful admin assignment
        response = self.make_request("PUT", f"/admin/users/{test_user['employee_id']}/admin-status", admin_update_data, token=admin_token)
        if response["success"]:
            result = response["data"]
            updated_user = result.get("user")
            
            if updated_user and updated_user.get("is_admin") == True:
                self.log_test("STEP 6: Successful admin assignment", True, f"Successfully granted admin privileges to user {test_user['employee_id']}")
                
                # Verify response structure
                required_fields = ["message", "user", "action_by"]
                if all(field in result for field in required_fields):
                    self.log_test("STEP 6a: Response structure", True, "Response contains all required fields")
                else:
                    self.log_test("STEP 6a: Response structure", False, f"Response missing fields. Got: {list(result.keys())}")
                
                # Verify security logging information
                if result.get("action_by") == admin_user["email"]:
                    self.log_test("STEP 6b: Security logging", True, "Response includes correct admin who performed the action")
                else:
                    self.log_test("STEP 6b: Security logging", False, f"Expected action_by: {admin_user['email']}, got: {result.get('action_by')}")
                
            else:
                self.log_test("STEP 6: Successful admin assignment", False, f"User admin status not updated correctly: {updated_user}")
        else:
            self.log_test("STEP 6: Successful admin assignment", False, "Failed to grant admin privileges", response["data"])
        
        # Step 7: Test admin revocation
        revoke_admin_data = {
            "is_admin": False,
            "reason": "Testing admin revocation"
        }
        
        response = self.make_request("PUT", f"/admin/users/{test_user['employee_id']}/admin-status", revoke_admin_data, token=admin_token)
        if response["success"]:
            result = response["data"]
            updated_user = result.get("user")
            
            if updated_user and updated_user.get("is_admin") == False:
                self.log_test("STEP 7: Admin revocation", True, f"Successfully revoked admin privileges from user {test_user['employee_id']}")
            else:
                self.log_test("STEP 7: Admin revocation", False, f"User admin status not revoked correctly: {updated_user}")
        else:
            self.log_test("STEP 7: Admin revocation", False, "Failed to revoke admin privileges", response["data"])
        
        # Step 8: Test payload validation - missing required fields
        invalid_payload = {"reason": "Missing is_admin field"}
        
        response = self.make_request("PUT", f"/admin/users/{test_user['employee_id']}/admin-status", invalid_payload, token=admin_token)
        if not response["success"] and response["status_code"] in [400, 422]:
            self.log_test("STEP 8: Payload validation", True, "Correctly rejected request with missing required fields")
        else:
            self.log_test("STEP 8: Payload validation", False, "Should reject request with missing required fields", response["data"])
        
        # Step 9: Test with optional reason field
        admin_with_reason = {
            "is_admin": True,
            "reason": "Promoting to admin for testing purposes - comprehensive security test"
        }
        
        response = self.make_request("PUT", f"/admin/users/{test_user['employee_id']}/admin-status", admin_with_reason, token=admin_token)
        if response["success"]:
            result = response["data"]
            if result.get("reason") == admin_with_reason["reason"]:
                self.log_test("STEP 9: Optional reason field", True, "Reason field correctly processed and returned")
            else:
                self.log_test("STEP 9: Optional reason field", False, f"Reason field not handled correctly: {result.get('reason')}")
        else:
            self.log_test("STEP 9: Optional reason field", False, "Failed to process request with reason field", response["data"])
        
        # Step 10: Verify the newly promoted user can now access admin endpoints
        # Login as the newly promoted admin
        new_admin_login = {
            "email": "test.employee@mikelcoffee.com",
            "password": "testpass123"
        }
        
        response = self.make_request("POST", "/auth/login", new_admin_login)
        if response["success"]:
            new_admin_token = response["data"]["access_token"]
            new_admin_user = response["data"]["user"]
            
            if new_admin_user.get("is_admin"):
                self.log_test("STEP 10a: New admin login", True, "Newly promoted admin can login with admin privileges")
                
                # Test if new admin can access admin endpoints
                response = self.make_request("GET", "/users", token=new_admin_token)
                if response["success"]:
                    self.log_test("STEP 10b: New admin access", True, "Newly promoted admin can access admin-only endpoints")
                else:
                    self.log_test("STEP 10b: New admin access", False, "Newly promoted admin cannot access admin endpoints", response["data"])
            else:
                self.log_test("STEP 10a: New admin login", False, "User login shows admin status not updated")
        else:
            self.log_test("STEP 10a: New admin login", False, "Failed to login as newly promoted admin", response["data"])

    def test_profile_photo_visibility_issue(self):
        """Test the specific profile photo visibility issue reported"""
        print("\n=== Testing Profile Photo Visibility Issue ===")
        
        # Step 1: Create admin user as requested
        admin_data = {
            "name": "Admin",
            "surname": "User",
            "email": "admin@mikelcoffee.com",
            "password": "admin123",
            "position": "trainer",
            "store": "merkez"
        }
        
        response = self.make_request("POST", "/auth/register", admin_data)
        admin_token = None
        if response["success"]:
            admin_token = response["data"]["access_token"]
            user = response["data"]["user"]
            self.log_test("STEP 1: Create admin user", True, f"Admin user created with employee ID: {user['employee_id']}")
        else:
            # Try login if user already exists
            login_data = {
                "email": "admin@mikelcoffee.com",
                "password": "admin123"
            }
            response = self.make_request("POST", "/auth/login", login_data)
            if response["success"]:
                admin_token = response["data"]["access_token"]
                user = response["data"]["user"]
                self.log_test("STEP 1: Login existing admin", True, f"Logged in as existing admin with ID: {user['employee_id']}")
            else:
                self.log_test("STEP 1: Create/Login admin", False, "Failed to create or login admin user", response["data"])
                return
        
        if not admin_token:
            self.log_test("STEP 1: Admin token", False, "No admin token available")
            return
        
        # Step 2: Create test announcement
        announcement_data = {
            "title": "Test Profile Photo",
            "content": "Testing if profile photos appear in announcements",
            "is_urgent": False
        }
        
        response = self.make_request("POST", "/announcements", announcement_data, token=admin_token)
        announcement_id = None
        if response["success"]:
            announcement = response["data"]
            announcement_id = announcement.get("id") or announcement.get("_id")
            self.log_test("STEP 2: Create test announcement", True, f"Test announcement created with ID: {announcement_id}")
        else:
            self.log_test("STEP 2: Create test announcement", False, "Failed to create test announcement", response["data"])
        
        # Step 3: Upload profile photo with base64 image
        # Using a small test base64 image (1x1 pixel PNG)
        test_base64_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        profile_update = {
            "profile_image_url": test_base64_image,
            "bio": "Admin user testing profile photos"
        }
        
        response = self.make_request("PUT", "/profile", profile_update, token=admin_token)
        if response["success"]:
            updated_profile = response["data"]
            if updated_profile.get("profile_image_url") == test_base64_image:
                self.log_test("STEP 3: Upload profile photo", True, "Profile photo uploaded successfully with base64 data")
            else:
                self.log_test("STEP 3: Upload profile photo", False, f"Profile photo not saved correctly: {updated_profile.get('profile_image_url', 'None')[:50]}...")
        else:
            self.log_test("STEP 3: Upload profile photo", False, "Failed to upload profile photo", response["data"])
        
        # Step 4: Test profile photo visibility - GET /api/announcements
        response = self.make_request("GET", "/announcements", token=admin_token)
        if response["success"]:
            announcements = response["data"]
            if isinstance(announcements, list) and len(announcements) > 0:
                # Check if our test announcement exists
                test_announcement = None
                for ann in announcements:
                    if ann.get("title") == "Test Profile Photo":
                        test_announcement = ann
                        break
                
                if test_announcement:
                    self.log_test("STEP 4a: Verify announcement exists", True, f"Test announcement found in list of {len(announcements)} announcements")
                    # Log announcement details for debugging
                    print(f"   Announcement details: created_by={test_announcement.get('created_by')}, title={test_announcement.get('title')}")
                else:
                    self.log_test("STEP 4a: Verify announcement exists", False, f"Test announcement not found in {len(announcements)} announcements")
            else:
                self.log_test("STEP 4a: Verify announcement exists", False, f"No announcements found or invalid response: {type(announcements)}")
        else:
            self.log_test("STEP 4a: GET announcements", False, "Failed to get announcements", response["data"])
        
        # Step 5: Test profile photo visibility - GET /api/profiles
        response = self.make_request("GET", "/profiles", token=admin_token)
        if response["success"]:
            profiles = response["data"]
            if isinstance(profiles, list):
                # Find admin's profile
                admin_profile = None
                for profile in profiles:
                    if profile.get("profile_image_url") == test_base64_image:
                        admin_profile = profile
                        break
                
                if admin_profile:
                    self.log_test("STEP 4b: Verify profile photo exists", True, f"Admin profile found with correct photo in {len(profiles)} profiles")
                    print(f"   Profile details: user_id={admin_profile.get('user_id')}, has_image={bool(admin_profile.get('profile_image_url'))}")
                else:
                    self.log_test("STEP 4b: Verify profile photo exists", False, f"Admin profile with photo not found in {len(profiles)} profiles")
                    # Debug: show all profiles
                    for i, profile in enumerate(profiles):
                        print(f"   Profile {i}: user_id={profile.get('user_id')}, has_image={bool(profile.get('profile_image_url'))}")
            else:
                self.log_test("STEP 4b: GET profiles", False, f"Invalid profiles response: {type(profiles)}")
        else:
            self.log_test("STEP 4b: GET profiles", False, "Failed to get profiles", response["data"])
        
        # Step 6: Test profile photo visibility - GET /api/users
        response = self.make_request("GET", "/users", token=admin_token)
        if response["success"]:
            users = response["data"]
            if isinstance(users, list):
                # Find admin user
                admin_user = None
                for user in users:
                    if user.get("email") == "admin@mikelcoffee.com":
                        admin_user = user
                        break
                
                if admin_user:
                    self.log_test("STEP 4c: Verify user data", True, f"Admin user found in {len(users)} users")
                    print(f"   User details: employee_id={admin_user.get('employee_id')}, name={admin_user.get('name')} {admin_user.get('surname')}, position={admin_user.get('position')}")
                else:
                    self.log_test("STEP 4c: Verify user data", False, f"Admin user not found in {len(users)} users")
            else:
                self.log_test("STEP 4c: GET users", False, f"Invalid users response: {type(users)}")
        else:
            self.log_test("STEP 4c: GET users", False, "Failed to get users", response["data"])
        
        # Step 7: Cross-reference data to identify the issue
        print("\n   🔍 DEBUGGING PROFILE PHOTO VISIBILITY:")
        
        # Get user data again
        response = self.make_request("GET", "/auth/me", token=admin_token)
        if response["success"]:
            current_user = response["data"]
            employee_id = current_user.get("employee_id")
            print(f"   Current user employee_id: {employee_id}")
            
            # Get profile data again
            response = self.make_request("GET", "/profile", token=admin_token)
            if response["success"]:
                profile = response["data"]
                profile_user_id = profile.get("user_id")
                has_image = bool(profile.get("profile_image_url"))
                print(f"   Profile user_id: {profile_user_id}, has_image: {has_image}")
                
                # Check if user_id matches employee_id
                if profile_user_id == employee_id:
                    self.log_test("STEP 5: Data consistency check", True, "Profile user_id matches user employee_id - data is consistent")
                else:
                    self.log_test("STEP 5: Data consistency check", False, f"Profile user_id ({profile_user_id}) does not match employee_id ({employee_id}) - this could cause frontend issues")
            else:
                self.log_test("STEP 5: Profile data check", False, "Failed to get profile data for consistency check")
        else:
            self.log_test("STEP 5: User data check", False, "Failed to get current user data for consistency check")

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
            
            # Run new tests for social media features and specific admin user
            self.test_specific_admin_user()
            self.test_social_media_features()
            
            # Run the Make Admin functionality test
            self.test_make_admin_functionality()
            
            # Run the specific profile photo visibility test
            self.test_profile_photo_visibility_issue()
            
        except Exception as e:
            self.log_test("Test Suite Execution", False, f"Critical error during testing: {str(e)}")
        
        # Print summary
        self.print_summary()

    def run_profile_photo_test_only(self):
        """Run only the profile photo visibility test"""
        print("🔍 Running Profile Photo Visibility Test Only")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 80)
        
        try:
            self.test_profile_photo_visibility_issue()
        except Exception as e:
            self.log_test("Profile Photo Test", False, f"Critical error during testing: {str(e)}")
        
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
    import sys
    
    tester = BackendTester()
    
    # Check if we should run only the profile photo test
    if len(sys.argv) > 1 and sys.argv[1] == "--profile-photo-only":
        summary = tester.run_profile_photo_test_only()
    else:
        summary = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if summary:
        exit(0 if summary["failed"] == 0 else 1)
    else:
        exit(1)
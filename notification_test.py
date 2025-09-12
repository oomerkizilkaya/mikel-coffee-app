#!/usr/bin/env python3
"""
Focused Notification System Testing
Tests the newly implemented notification system functionality
"""

import requests
import json
import time
import uuid
from typing import Dict, Any, Optional

# Configuration
BASE_URL = "https://teammikel.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class NotificationTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS.copy()
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

    def test_notification_system(self):
        """Test comprehensive notification system functionality"""
        print("\n=== Testing Notification System ===")
        
        # Generate unique identifiers for this test run
        test_id = str(uuid.uuid4())[:8]
        
        # Step 1: Setup admin user for testing
        admin_token = None
        admin_user = None
        
        # Try to login with existing admin
        login_data = {
            "email": "admin@mikelcoffee.com",
            "password": "admin123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        if response["success"]:
            admin_token = response["data"]["access_token"]
            admin_user = response["data"]["user"]
            self.log_test("STEP 1: Admin login for notifications", True, f"Admin logged in: {admin_user['employee_id']}")
        else:
            # Create admin if doesn't exist
            admin_data = {
                "name": "Notification",
                "surname": "Admin",
                "email": f"notif_admin_{test_id}@mikelcoffee.com",
                "password": "admin123",
                "position": "trainer",
                "store": "merkez"
            }
            
            response = self.make_request("POST", "/auth/register", admin_data)
            if response["success"]:
                admin_token = response["data"]["access_token"]
                admin_user = response["data"]["user"]
                
                # Make admin using test endpoint
                make_admin_response = self.make_request("POST", f"/test/make-admin/{admin_user['email']}")
                if make_admin_response["success"]:
                    # Re-login to get updated token
                    login_data["email"] = admin_user["email"]
                    response = self.make_request("POST", "/auth/login", login_data)
                    if response["success"]:
                        admin_token = response["data"]["access_token"]
                        admin_user = response["data"]["user"]
                        self.log_test("STEP 1: Create admin for notifications", True, f"Admin created and promoted: {admin_user['employee_id']}")
                    else:
                        self.log_test("STEP 1: Admin re-login", False, "Failed to re-login after promotion")
                        return
                else:
                    self.log_test("STEP 1: Make admin", False, "Failed to promote user to admin")
                    return
            else:
                self.log_test("STEP 1: Create admin", False, "Failed to create admin user", response["data"])
                return
        
        if not admin_token:
            self.log_test("STEP 1: Admin setup", False, "No admin token available")
            return
        
        # Step 2: Create multiple test users to receive notifications
        test_users = []
        for i in range(3):
            user_data = {
                "name": f"NotifUser{i+1}",
                "surname": "Test",
                "email": f"notifuser{i+1}_{test_id}@mikelcoffee.com",
                "password": "testpass123",
                "position": "barista",
                "store": "test_store"
            }
            
            response = self.make_request("POST", "/auth/register", user_data)
            if response["success"]:
                test_users.append({
                    "token": response["data"]["access_token"],
                    "user": response["data"]["user"]
                })
        
        if len(test_users) < 3:
            self.log_test("STEP 2: Create test users", False, f"Only created {len(test_users)} out of 3 test users")
            if len(test_users) == 0:
                return
        else:
            self.log_test("STEP 2: Create test users", True, f"Created {len(test_users)} test users for notification testing")
        
        # Step 3: Test notification endpoints without notifications (should be empty)
        response = self.make_request("GET", "/notifications", token=test_users[0]["token"])
        if response["success"]:
            notifications = response["data"]
            if isinstance(notifications, list):
                self.log_test("STEP 3: Empty notifications list", True, f"GET /notifications returns list with {len(notifications)} notifications initially")
            else:
                self.log_test("STEP 3: Empty notifications list", False, f"Expected list, got: {type(notifications)}")
        else:
            self.log_test("STEP 3: GET notifications endpoint", False, "Failed to access notifications endpoint", response["data"])
        
        # Step 4: Test unread count initially
        response = self.make_request("GET", "/notifications/unread-count", token=test_users[0]["token"])
        if response["success"]:
            count_data = response["data"]
            if "unread_count" in count_data:
                self.log_test("STEP 4: Initial unread count", True, f"Unread count is {count_data['unread_count']} initially")
            else:
                self.log_test("STEP 4: Initial unread count", False, f"Missing unread_count field: {count_data}")
        else:
            self.log_test("STEP 4: GET unread count endpoint", False, "Failed to get unread count", response["data"])
        
        # Step 5: Create announcement to trigger mass notifications
        announcement_data = {
            "title": f"🔔 Test Notification System {test_id}",
            "content": "This announcement should create notifications for all users in the system.",
            "is_urgent": True
        }
        
        response = self.make_request("POST", "/announcements", announcement_data, token=admin_token)
        announcement_id = None
        if response["success"]:
            announcement = response["data"]
            announcement_id = announcement.get("id") or announcement.get("_id")
            self.log_test("STEP 5: Create announcement", True, f"Announcement created with ID: {announcement_id}")
        else:
            self.log_test("STEP 5: Create announcement", False, "Failed to create announcement", response["data"])
            return
        
        # Step 6: Verify notifications were created for all users
        # Wait a moment for notifications to be processed
        time.sleep(2)
        
        notifications_created = 0
        for i, test_user in enumerate(test_users):
            response = self.make_request("GET", "/notifications", token=test_user["token"])
            if response["success"]:
                notifications = response["data"]
                if isinstance(notifications, list) and len(notifications) > 0:
                    # Check if notification is about our announcement
                    found_notification = False
                    for notif in notifications:
                        if (notif.get("title") == "🔔 Yeni Duyuru" and 
                            test_id in notif.get("message", "")):
                            found_notification = True
                            notifications_created += 1
                            
                            # Verify notification structure
                            required_fields = ["id", "user_id", "title", "message", "type", "read", "created_at"]
                            missing_fields = [f for f in required_fields if f not in notif]
                            if not missing_fields:
                                self.log_test(f"STEP 6a: Notification structure user {i+1}", True, "Notification has all required fields")
                            else:
                                self.log_test(f"STEP 6a: Notification structure user {i+1}", False, f"Missing fields: {missing_fields}")
                            
                            # Verify notification content
                            if (notif.get("type") == "announcement" and 
                                notif.get("read") == False and
                                notif.get("user_id") == test_user["user"]["employee_id"]):
                                self.log_test(f"STEP 6b: Notification content user {i+1}", True, "Notification content is correct")
                            else:
                                self.log_test(f"STEP 6b: Notification content user {i+1}", False, f"Incorrect content: type={notif.get('type')}, read={notif.get('read')}, user_id={notif.get('user_id')}")
                            break
                    
                    if not found_notification:
                        self.log_test(f"STEP 6: User {i+1} notification", False, f"Notification not found for user {i+1}")
                        # Debug: show what notifications were found
                        print(f"   Found {len(notifications)} notifications for user {i+1}")
                        for j, notif in enumerate(notifications):
                            print(f"   Notification {j+1}: title='{notif.get('title')}', message='{notif.get('message', '')[:50]}...'")
                else:
                    self.log_test(f"STEP 6: User {i+1} notification", False, f"No notifications found for user {i+1}")
            else:
                self.log_test(f"STEP 6: User {i+1} notification", False, f"Failed to get notifications for user {i+1}")
        
        if notifications_created == len(test_users):
            self.log_test("STEP 6: Mass notification creation", True, f"Notifications created for all {notifications_created} users")
        else:
            self.log_test("STEP 6: Mass notification creation", False, f"Only {notifications_created} out of {len(test_users)} users received notifications")
        
        # Step 7: Test unread count after notification creation
        response = self.make_request("GET", "/notifications/unread-count", token=test_users[0]["token"])
        if response["success"]:
            count_data = response["data"]
            unread_count = count_data.get("unread_count", 0)
            if unread_count >= 1:
                self.log_test("STEP 7: Unread count after notification", True, f"Unread count increased to {unread_count}")
            else:
                self.log_test("STEP 7: Unread count after notification", False, f"Unread count should be >= 1, got: {unread_count}")
        else:
            self.log_test("STEP 7: Unread count after notification", False, "Failed to get unread count after notification")
        
        # Step 8: Test mark notification as read
        # Get the first user's notifications to find notification ID
        response = self.make_request("GET", "/notifications", token=test_users[0]["token"])
        notification_id = None
        if response["success"]:
            notifications = response["data"]
            if len(notifications) > 0:
                # Find our test notification
                for notif in notifications:
                    if test_id in notif.get("message", ""):
                        notification_id = notif.get("id") or notif.get("_id")
                        break
                
                if notification_id:
                    # Mark as read
                    response = self.make_request("PUT", f"/notifications/{notification_id}/read", token=test_users[0]["token"])
                    if response["success"]:
                        self.log_test("STEP 8a: Mark notification as read", True, "Successfully marked notification as read")
                        
                        # Verify unread count decreased
                        time.sleep(1)
                        response = self.make_request("GET", "/notifications/unread-count", token=test_users[0]["token"])
                        if response["success"]:
                            count_data = response["data"]
                            new_unread_count = count_data.get("unread_count", 0)
                            if new_unread_count < unread_count:
                                self.log_test("STEP 8b: Unread count after read", True, f"Unread count decreased from {unread_count} to {new_unread_count}")
                            else:
                                self.log_test("STEP 8b: Unread count after read", False, f"Unread count should decrease, was {unread_count}, now {new_unread_count}")
                        else:
                            self.log_test("STEP 8b: Unread count after read", False, "Failed to get unread count after marking as read")
                    else:
                        self.log_test("STEP 8a: Mark notification as read", False, "Failed to mark notification as read", response["data"])
                else:
                    self.log_test("STEP 8: Find notification to mark as read", False, "Could not find test notification to mark as read")
        
        # Step 9: Test notification access control (user can only access their own notifications)
        if notification_id and len(test_users) > 1:
            # Try to mark another user's notification as read
            response = self.make_request("PUT", f"/notifications/{notification_id}/read", token=test_users[1]["token"])
            if not response["success"] and response["status_code"] == 404:
                self.log_test("STEP 9: Notification access control", True, "User cannot access other users' notifications")
            else:
                self.log_test("STEP 9: Notification access control", False, "User should not be able to access other users' notifications", response["data"])
        
        # Step 10: Test notification model validation by creating another announcement
        announcement_data2 = {
            "title": f"Second Test Notification {test_id}",
            "content": "Testing notification system with second announcement.",
            "is_urgent": False
        }
        
        response = self.make_request("POST", "/announcements", announcement_data2, token=admin_token)
        if response["success"]:
            # Wait for notifications to be created
            time.sleep(2)
            
            # Check if users received the second notification
            response = self.make_request("GET", "/notifications", token=test_users[0]["token"])
            if response["success"]:
                notifications = response["data"]
                # Count notifications with our test_id
                test_notifications = [n for n in notifications if test_id in n.get("message", "") or test_id in n.get("title", "")]
                if len(test_notifications) >= 2:
                    self.log_test("STEP 10: Multiple notifications", True, f"User has {len(test_notifications)} test notifications after second announcement")
                else:
                    self.log_test("STEP 10: Multiple notifications", False, f"Expected >= 2 test notifications, got {len(test_notifications)}")
            else:
                self.log_test("STEP 10: Multiple notifications", False, "Failed to get notifications after second announcement")
        else:
            self.log_test("STEP 10: Second announcement", False, "Failed to create second announcement", response["data"])
        
        # Step 11: Test notification system integration with announcement deletion
        if announcement_id:
            # Delete the first announcement
            response = self.make_request("DELETE", f"/announcements/{announcement_id}", token=admin_token)
            if response["success"]:
                self.log_test("STEP 11: Announcement deletion", True, "Successfully deleted announcement")
                
                # Notifications should still exist even after announcement deletion
                response = self.make_request("GET", "/notifications", token=test_users[0]["token"])
                if response["success"]:
                    notifications = response["data"]
                    test_notifications = [n for n in notifications if test_id in n.get("message", "") or test_id in n.get("title", "")]
                    if len(test_notifications) > 0:
                        self.log_test("STEP 11: Notifications persist after deletion", True, f"{len(test_notifications)} notifications remain after announcement deletion")
                    else:
                        self.log_test("STEP 11: Notifications persist after deletion", False, "Notifications should persist after announcement deletion")
                else:
                    self.log_test("STEP 11: Check notifications after deletion", False, "Failed to check notifications after announcement deletion")
            else:
                self.log_test("STEP 11: Announcement deletion", False, "Failed to delete announcement", response["data"])

    def print_summary(self):
        """Print test results summary"""
        print("\n" + "=" * 80)
        print("📊 NOTIFICATION SYSTEM TEST RESULTS SUMMARY")
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

    def run_test(self):
        """Run the notification system test"""
        print("🔔 Running Comprehensive Notification System Test")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 80)
        
        try:
            self.test_notification_system()
        except Exception as e:
            self.log_test("Notification System Test", False, f"Critical error during testing: {str(e)}")
            import traceback
            print(f"Error details: {traceback.format_exc()}")
        
        # Print summary
        return self.print_summary()

if __name__ == "__main__":
    tester = NotificationTester()
    summary = tester.run_test()
    
    # Exit with error code if tests failed
    if summary:
        exit(0 if summary["failed"] == 0 else 1)
    else:
        exit(1)
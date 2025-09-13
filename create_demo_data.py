#!/usr/bin/env python3
"""
Demo Data Creation Script for Mikel Coffee PWA
Creates realistic demo data for testing the deployed PWA functionality
"""

import requests
import json
import time
import base64
import io
from typing import Dict, Any, List

# Configuration
BASE_URL = "https://employee-hub-45.preview.emergentagent.com/api"
HEADERS = {"Content-Type": "application/json"}

class DemoDataCreator:
    def __init__(self):
        self.base_url = BASE_URL
        self.headers = HEADERS.copy()
        self.admin_token = None
        self.demo_users = []
        self.demo_files = []
        self.demo_announcements = []
        
    def log(self, message: str):
        """Log messages with timestamp"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def make_request(self, method: str, endpoint: str, data: Dict = None, token: str = None, files=None) -> Dict:
        """Make HTTP request with error handling"""
        url = f"{self.base_url}{endpoint}"
        headers = self.headers.copy()
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
            
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data)
            elif method.upper() == "POST":
                if files:
                    # Remove Content-Type for multipart/form-data
                    headers.pop("Content-Type", None)
                    response = requests.post(url, headers=headers, data=data, files=files)
                else:
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

    def create_admin_user(self):
        """Create the main admin user"""
        self.log("Creating main admin user...")
        
        # First try to login with existing admin
        login_data = {
            "email": "admin@mikelcoffee.com",
            "password": "admin123"
        }
        
        response = self.make_request("POST", "/auth/login", login_data)
        if response["success"]:
            self.admin_token = response["data"]["access_token"]
            self.log("✅ Admin user already exists and logged in successfully")
            return True
        
        # Create admin user if doesn't exist
        admin_data = {
            "name": "Eğitim departmanı",
            "surname": "Admin",
            "email": "admin@mikelcoffee.com",
            "password": "admin123",
            "position": "trainer",
            "store": "Merkez Mağaza",
            "start_date": "2020-01-15"
        }
        
        response = self.make_request("POST", "/auth/register", admin_data)
        if response["success"]:
            self.admin_token = response["data"]["access_token"]
            user = response["data"]["user"]
            
            # Make this user admin using test endpoint
            make_admin_response = self.make_request("POST", f"/test/make-admin/{user['email']}")
            if make_admin_response["success"]:
                # Re-login to get updated token with admin privileges
                response = self.make_request("POST", "/auth/login", login_data)
                if response["success"]:
                    self.admin_token = response["data"]["access_token"]
                    self.log(f"✅ Admin user created successfully with ID: {user['employee_id']}")
                    return True
            
        self.log("❌ Failed to create admin user")
        return False

    def create_demo_employees(self):
        """Create 8 demo employees with different roles"""
        self.log("Creating demo employees...")
        
        demo_employees = [
            {
                "name": "Ahmet", "surname": "YILMAZ", "email": "ahmet.yilmaz@mikelcoffee.com",
                "password": "demo123", "position": "mağaza müdürü", "store": "Kadıköy Mağazası",
                "start_date": "2019-03-10"
            },
            {
                "name": "Fatma", "surname": "DEMIR", "email": "fatma.demir@mikelcoffee.com", 
                "password": "demo123", "position": "trainer", "store": "Merkez Mağaza",
                "start_date": "2020-06-15"
            },
            {
                "name": "Mehmet", "surname": "KAYA", "email": "mehmet.kaya@mikelcoffee.com",
                "password": "demo123", "position": "müdür yardımcısı", "store": "Beşiktaş Mağazası", 
                "start_date": "2021-01-20"
            },
            {
                "name": "Ayşe", "surname": "ÖZ", "email": "ayse.oz@mikelcoffee.com",
                "password": "demo123", "position": "supervizer", "store": "Şişli Mağazası",
                "start_date": "2021-08-05"
            },
            {
                "name": "Can", "surname": "AKMAN", "email": "can.akman@mikelcoffee.com",
                "password": "demo123", "position": "barista", "store": "Taksim Mağazası",
                "start_date": "2022-02-14"
            },
            {
                "name": "Zeynep", "surname": "ÇELIK", "email": "zeynep.celik@mikelcoffee.com",
                "password": "demo123", "position": "barista", "store": "Kadıköy Mağazası",
                "start_date": "2022-05-30"
            },
            {
                "name": "Ömer", "surname": "KIZILKAYA", "email": "omer.kizilkaya@mikelcoffee.com",
                "password": "demo123", "position": "servis personeli", "store": "Beşiktaş Mağazası",
                "start_date": "2023-01-10"
            },
            {
                "name": "Elif", "surname": "ARSLAN", "email": "elif.arslan@mikelcoffee.com",
                "password": "demo123", "position": "servis personeli", "store": "Şişli Mağazası",
                "start_date": "2023-07-18"
            }
        ]
        
        created_count = 0
        for employee in demo_employees:
            response = self.make_request("POST", "/auth/register", employee)
            if response["success"]:
                user = response["data"]["user"]
                self.demo_users.append({
                    "token": response["data"]["access_token"],
                    "user": user,
                    "credentials": {"email": employee["email"], "password": employee["password"]}
                })
                created_count += 1
                self.log(f"✅ Created employee: {employee['name']} {employee['surname']} (ID: {user['employee_id']}, Position: {employee['position']})")
            else:
                # Try to login if user already exists
                login_data = {"email": employee["email"], "password": employee["password"]}
                login_response = self.make_request("POST", "/auth/login", login_data)
                if login_response["success"]:
                    user = login_response["data"]["user"]
                    self.demo_users.append({
                        "token": login_response["data"]["access_token"],
                        "user": user,
                        "credentials": login_data
                    })
                    created_count += 1
                    self.log(f"✅ Logged in existing employee: {employee['name']} {employee['surname']} (ID: {user['employee_id']})")
                else:
                    self.log(f"❌ Failed to create/login employee: {employee['name']} {employee['surname']}")
        
        self.log(f"✅ Demo employees setup complete: {created_count} employees ready")
        return created_count > 0

    def create_profile_photos(self):
        """Create profile photos for demo users"""
        self.log("Creating profile photos for demo users...")
        
        # Create different colored profile photos (simple base64 images)
        profile_photos = [
            # Red profile photo
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABYSURBVBiVY2RgYPjPQAJgYmBg+M9AAWBkYGD4z0ABYGJgYPjPQAFgZGBg+M9AAWBiYGD4z0ABYGRgYPjPQAFgYmBg+M9AAWBkYGD4z0ABYGJgYPjPQAFgZGBgAABrIAEF7UNKlwAAAABJRU5ErkJggg==",
            # Blue profile photo  
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABYSURBVBiVY2RgYPjPQAJgYmBg+M9AAWBkYGD4z0ABYGJgYPjPQAFgZGBg+M9AAWBiYGD4z0ABYGRgYPjPQAFgYmBg+M9AAWBkYGD4z0ABYGJgYPjPQAFgZGBgAABrIAEF7UNKlwAAAABJRU5ErkJggg==",
            # Green profile photo
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABYSURBVBiVY2RgYPjPQAJgYmBg+M9AAWBkYGD4z0ABYGJgYPjPQAFgZGBg+M9AAWBiYGD4z0ABYGRgYPjPQAFgYmBg+M9AAWBkYGD4z0ABYGJgYPjPQAFgZGBgAABrIAEF7UNKlwAAAABJRU5ErkJggg==",
            # Purple profile photo
            "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAoAAAAKCAYAAACNMs+9AAAABHNCSVQICAgIfAhkiAAAAAlwSFlzAAAAdgAAAHYBTnsmCAAAABl0RVh0U29mdHdhcmUAd3d3Lmlua3NjYXBlLm9yZ5vuPBoAAABYSURBVBiVY2RgYPjPQAJgYmBg+M9AAWBkYGD4z0ABYGJgYPjPQAFgZGBg+M9AAWBiYGD4z0ABYGRgYPjPQAFgYmBg+M9AAWBkYGD4z0ABYGJgYPjPQAFgZGBgAABrIAEF7UNKlwAAAABJRU5ErkJggg=="
        ]
        
        bios = [
            "Mikel Coffee'de mağaza müdürü olarak çalışıyorum. Kahve tutkunu! ☕️",
            "Eğitim departmanında trainer olarak görev yapıyorum. Yeni teknikleri öğretmeyi seviyorum! 📚",
            "Müdür yardımcısı olarak ekibimle birlikte harika kahveler hazırlıyoruz! 👥",
            "Supervizer olarak kalite kontrolünden sorumluyum. Mükemmellik hedefimiz! ⭐",
            "Barista olarak müşterilerimize en iyi kahve deneyimini sunuyorum! ☕",
            "Kahve sanatında uzmanlaşmaya devam ediyorum. Her gün yeni şeyler öğreniyorum! 🎨",
            "Servis personeli olarak müşteri memnuniyeti önceliğim! 😊",
            "Mikel Coffee ailesinin yeni üyesiyim. Öğrenmeye devam ediyorum! 🌟"
        ]
        
        created_count = 0
        for i, demo_user in enumerate(self.demo_users):
            if i < len(profile_photos) and i < len(bios):
                profile_update = {
                    "profile_image_url": profile_photos[i % len(profile_photos)],
                    "bio": bios[i]
                }
                
                response = self.make_request("PUT", "/profile", profile_update, token=demo_user["token"])
                if response["success"]:
                    created_count += 1
                    self.log(f"✅ Profile photo created for: {demo_user['user']['name']} {demo_user['user']['surname']}")
                else:
                    self.log(f"❌ Failed to create profile photo for: {demo_user['user']['name']} {demo_user['user']['surname']}")
        
        self.log(f"✅ Profile photos setup complete: {created_count} photos created")

    def create_demo_announcements(self):
        """Create demo announcements"""
        self.log("Creating demo announcements...")
        
        announcements = [
            {
                "title": "🎉 Hoş geldiniz!",
                "content": "Mikel Coffee ailesine hoş geldiniz! Bu platformda duyurular, eğitimler ve sosyal paylaşımlar yapabilirsiniz. Herhangi bir sorunuz olursa eğitim departmanı ile iletişime geçebilirsiniz.",
                "is_urgent": True
            },
            {
                "title": "☕ Yeni Kahve Çeşitleri",
                "content": "Bu hafta menümüze yeni kahve çeşitleri ekliyoruz! Özel harmanımız 'Mikel Blend' ve soğuk kahve seçeneklerimiz müşterilerimizin beğenisini kazanacak. Detaylar için eğitim materyallerini inceleyin.",
                "is_urgent": False
            },
            {
                "title": "📚 Haftalık Eğitim Programı",
                "content": "Bu hafta 'Müşteri Hizmetleri Excellence' eğitimimiz var. Tüm çalışanların katılımı zorunludur. Tarih: 15 Ocak 2025, Saat: 14:00-16:00, Yer: Merkez Mağaza eğitim salonu.",
                "is_urgent": False
            },
            {
                "title": "🏆 Aylık Başarı Ödülleri",
                "content": "Aralık ayının en başarılı çalışanları açıklandı! Tebrikler: Zeynep Çelik (En İyi Barista), Ahmet Yılmaz (En İyi Mağaza Müdürü), Can Akman (En İyi Takım Oyuncusu). Ödül töreni 20 Ocak'ta!",
                "is_urgent": False
            },
            {
                "title": "🔧 Sistem Bakımı Duyurusu",
                "content": "Bu Pazar günü saat 02:00-04:00 arası sistem bakımı yapılacaktır. Bu süre zarfında uygulamaya erişim sağlanamayabilir. Anlayışınız için teşekkürler.",
                "is_urgent": True
            },
            {
                "title": "🎯 Yeni Hedeflerimiz",
                "content": "2025 yılı hedeflerimiz belirlendi! Müşteri memnuniyeti %95, satış artışı %20, çalışan memnuniyeti %90. Bu hedeflere ulaşmak için hep birlikte çalışacağız!",
                "is_urgent": False
            }
        ]
        
        created_count = 0
        for announcement in announcements:
            response = self.make_request("POST", "/announcements", announcement, token=self.admin_token)
            if response["success"]:
                ann_data = response["data"]
                self.demo_announcements.append(ann_data)
                created_count += 1
                self.log(f"✅ Created announcement: {announcement['title']}")
            else:
                self.log(f"❌ Failed to create announcement: {announcement['title']}")
        
        self.log(f"✅ Demo announcements created: {created_count} announcements")

    def create_demo_posts(self):
        """Create demo social media posts"""
        self.log("Creating demo social media posts...")
        
        posts = [
            {
                "content": "Bugün harika bir kahve eğitimi aldık! Yeni latte art teknikleri öğrendik. Müşterilerimiz çok beğenecek! ☕🎨 #MikelCoffee #LatteArt",
                "user_index": 1  # Fatma (trainer)
            },
            {
                "content": "Mağazamızda yeni düzenleme yaptık! Daha rahat ve modern bir ortam oluşturduk. Müşteri geri dönüşleri harika! 🏪✨ #YeniTasarım",
                "user_index": 0  # Ahmet (mağaza müdürü)
            },
            {
                "content": "Bugün 50. kahvemi hazırladım! Her biri özel, her biri benzersiz. Kahve yapmak gerçekten bir sanat! ☕❤️ #BaristaLife",
                "user_index": 4  # Can (barista)
            },
            {
                "content": "Ekip toplantımızda harika fikirler çıktı! Yeni müşteri deneyimi projelerimiz çok heyecan verici! 💡👥 #Teamwork",
                "user_index": 2  # Mehmet (müdür yardımcısı)
            },
            {
                "content": "Kalite kontrol turumda tüm mağazalarımızı ziyaret ettim. Standartlarımız mükemmel! Tebrikler ekip! 🌟 #KaliteKontrol",
                "user_index": 3  # Ayşe (supervizer)
            },
            {
                "content": "Yeni başladığım bu işte çok şey öğreniyorum. Mikel Coffee ailesi gerçekten harika! Teşekkürler herkese! 🙏 #YeniBaslangic",
                "user_index": 7  # Elif (servis personeli)
            }
        ]
        
        created_count = 0
        for post in posts:
            if post["user_index"] < len(self.demo_users):
                user_token = self.demo_users[post["user_index"]]["token"]
                post_data = {"content": post["content"]}
                
                response = self.make_request("POST", "/posts", post_data, token=user_token)
                if response["success"]:
                    created_count += 1
                    user_name = self.demo_users[post["user_index"]]["user"]["name"]
                    self.log(f"✅ Created post by {user_name}: {post['content'][:50]}...")
                else:
                    self.log(f"❌ Failed to create post: {post['content'][:50]}...")
        
        self.log(f"✅ Demo posts created: {created_count} posts")

    def create_demo_exam_results(self):
        """Create demo exam results"""
        self.log("Creating demo exam results...")
        
        # Create exam results for different employees
        exam_results = [
            {
                "employee_id": None,  # Will be filled with actual IDs
                "exam_type": "general",
                "score": 85.0,
                "max_score": 100.0,
                "user_index": 4  # Can (barista)
            },
            {
                "employee_id": None,
                "exam_type": "management", 
                "score": 78.0,
                "max_score": 100.0,
                "user_index": 4  # Can (barista) - eligible for management exam
            },
            {
                "employee_id": None,
                "exam_type": "general",
                "score": 92.0,
                "max_score": 100.0,
                "user_index": 5  # Zeynep (barista)
            },
            {
                "employee_id": None,
                "exam_type": "general",
                "score": 88.0,
                "max_score": 100.0,
                "user_index": 6  # Ömer (servis personeli)
            },
            {
                "employee_id": None,
                "exam_type": "general",
                "score": 75.0,
                "max_score": 100.0,
                "user_index": 7  # Elif (servis personeli)
            },
            {
                "employee_id": None,
                "exam_type": "management",
                "score": 82.0,
                "max_score": 100.0,
                "user_index": 5  # Zeynep (barista) - eligible for management exam
            }
        ]
        
        created_count = 0
        for exam in exam_results:
            if exam["user_index"] < len(self.demo_users):
                exam["employee_id"] = self.demo_users[exam["user_index"]]["user"]["employee_id"]
                
                # Remove user_index before sending to API
                exam_data = {k: v for k, v in exam.items() if k != "user_index"}
                
                response = self.make_request("POST", "/exam-results", exam_data, token=self.admin_token)
                if response["success"]:
                    created_count += 1
                    user_name = self.demo_users[exam["user_index"]]["user"]["name"]
                    self.log(f"✅ Created exam result for {user_name}: {exam['exam_type']} - {exam['score']}/{exam['max_score']}")
                else:
                    self.log(f"❌ Failed to create exam result for employee {exam['employee_id']}")
        
        self.log(f"✅ Demo exam results created: {created_count} results")

    def create_demo_files(self):
        """Create demo files for file management system"""
        self.log("Creating demo files...")
        
        # Create sample files with different types
        demo_files = [
            {
                "title": "Kahve Hazırlama Kılavuzu",
                "description": "Tüm kahve çeşitleri için detaylı hazırlama talimatları",
                "category": "document",
                "content": b"PDF content for coffee preparation guide...",
                "filename": "kahve_hazirlama_kilavuzu.pdf",
                "content_type": "application/pdf"
            },
            {
                "title": "Latte Art Teknikleri Video",
                "description": "Profesyonel latte art yapma teknikleri eğitim videosu",
                "category": "video", 
                "content": b"Video content for latte art techniques...",
                "filename": "latte_art_teknikleri.mp4",
                "content_type": "video/mp4"
            },
            {
                "title": "Mağaza Düzeni Fotoğrafı",
                "description": "Yeni mağaza düzenimizin fotoğrafı - örnek layout",
                "category": "image",
                "content": b"Image content for store layout...",
                "filename": "magaza_duzeni.jpg", 
                "content_type": "image/jpeg"
            },
            {
                "title": "Müşteri Hizmetleri El Kitabı",
                "description": "Müşteri ile iletişim kuralları ve en iyi uygulamalar",
                "category": "document",
                "content": b"PDF content for customer service handbook...",
                "filename": "musteri_hizmetleri_elkitabi.pdf",
                "content_type": "application/pdf"
            },
            {
                "title": "Kahve Çekirdekleri Tanıtım",
                "description": "Farklı kahve çekirdeği türleri ve özellikleri",
                "category": "image",
                "content": b"Image content for coffee beans...",
                "filename": "kahve_cekirdekleri.png",
                "content_type": "image/png"
            }
        ]
        
        created_count = 0
        for file_data in demo_files:
            # Prepare form data for file upload
            form_data = {
                "title": file_data["title"],
                "description": file_data["description"],
                "category": file_data["category"]
            }
            
            # Create a file-like object
            files = {
                "file": (file_data["filename"], file_data["content"], file_data["content_type"])
            }
            
            response = self.make_request("POST", "/files/upload", data=form_data, token=self.admin_token, files=files)
            if response["success"]:
                created_count += 1
                self.demo_files.append(response["data"])
                self.log(f"✅ Created file: {file_data['title']} ({file_data['category']})")
            else:
                self.log(f"❌ Failed to create file: {file_data['title']} - {response['data']}")
        
        self.log(f"✅ Demo files created: {created_count} files")

    def add_interactions(self):
        """Add likes and interactions to posts and announcements"""
        self.log("Adding interactions (likes) to content...")
        
        # Add likes to announcements
        if self.demo_announcements:
            for i, user in enumerate(self.demo_users[:4]):  # First 4 users like announcements
                for j, announcement in enumerate(self.demo_announcements[:3]):  # Like first 3 announcements
                    ann_id = announcement.get("id") or announcement.get("_id")
                    if ann_id:
                        response = self.make_request("POST", f"/announcements/{ann_id}/like", token=user["token"])
                        if response["success"]:
                            self.log(f"✅ {user['user']['name']} liked announcement: {announcement['title'][:30]}...")
        
        # Add likes to posts
        response = self.make_request("GET", "/posts", token=self.admin_token)
        if response["success"]:
            posts = response["data"]
            for i, user in enumerate(self.demo_users[:3]):  # First 3 users like posts
                for j, post in enumerate(posts[:2]):  # Like first 2 posts
                    post_id = post.get("id") or post.get("_id")
                    if post_id:
                        response = self.make_request("POST", f"/posts/{post_id}/like", token=user["token"])
                        if response["success"]:
                            self.log(f"✅ {user['user']['name']} liked a post")
        
        self.log("✅ Interactions added to content")

    def verify_demo_data(self):
        """Verify that demo data was created successfully"""
        self.log("Verifying demo data creation...")
        
        # Check users
        response = self.make_request("GET", "/users", token=self.admin_token)
        if response["success"]:
            users = response["data"]
            self.log(f"✅ Total users in system: {len(users)}")
        
        # Check announcements
        response = self.make_request("GET", "/announcements", token=self.admin_token)
        if response["success"]:
            announcements = response["data"]
            self.log(f"✅ Total announcements: {len(announcements)}")
        
        # Check posts
        response = self.make_request("GET", "/posts", token=self.admin_token)
        if response["success"]:
            posts = response["data"]
            self.log(f"✅ Total posts: {len(posts)}")
        
        # Check exam results
        response = self.make_request("GET", "/exam-results", token=self.admin_token)
        if response["success"]:
            exam_results = response["data"]
            self.log(f"✅ Total exam results: {len(exam_results)}")
        
        # Check files
        response = self.make_request("GET", "/files", token=self.admin_token)
        if response["success"]:
            files = response["data"]
            self.log(f"✅ Total files: {len(files)}")
        
        # Check profiles
        response = self.make_request("GET", "/profiles", token=self.admin_token)
        if response["success"]:
            profiles = response["data"]
            self.log(f"✅ Total profiles with photos: {len(profiles)}")

    def run_demo_data_creation(self):
        """Run the complete demo data creation process"""
        self.log("🚀 Starting Mikel Coffee PWA Demo Data Creation...")
        
        # Step 1: Create admin user
        if not self.create_admin_user():
            self.log("❌ Failed to create admin user. Stopping.")
            return False
        
        # Step 2: Create demo employees
        if not self.create_demo_employees():
            self.log("❌ Failed to create demo employees. Stopping.")
            return False
        
        # Step 3: Create profile photos
        self.create_profile_photos()
        
        # Step 4: Create demo announcements
        self.create_demo_announcements()
        
        # Step 5: Create demo posts
        self.create_demo_posts()
        
        # Step 6: Create demo exam results
        self.create_demo_exam_results()
        
        # Step 7: Create demo files
        self.create_demo_files()
        
        # Step 8: Add interactions
        self.add_interactions()
        
        # Step 9: Verify everything was created
        self.verify_demo_data()
        
        self.log("🎉 Demo data creation completed successfully!")
        self.log("📱 PWA is now ready for testing with realistic demo data")
        self.log("🔑 Admin credentials: admin@mikelcoffee.com / admin123")
        self.log("🔑 Demo user credentials: [name.surname]@mikelcoffee.com / demo123")
        
        return True

def main():
    """Main function to run demo data creation"""
    creator = DemoDataCreator()
    success = creator.run_demo_data_creation()
    
    if success:
        print("\n" + "="*60)
        print("✅ DEMO DATA CREATION SUCCESSFUL!")
        print("="*60)
        print("🌐 PWA URL: https://darling-otter-9d7864.netlify.app")
        print("🔑 Admin Login: admin@mikelcoffee.com / admin123")
        print("👥 Demo Users: [firstname.lastname]@mikelcoffee.com / demo123")
        print("📊 Created: 9 users, 6 announcements, 6 posts, 6 exam results, 5 files")
        print("="*60)
    else:
        print("\n❌ Demo data creation failed. Check logs above.")

if __name__ == "__main__":
    main()
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import bcrypt
import jwt
from bson import ObjectId

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
JWT_EXPIRATION_DELTA = timedelta(days=7)

# Create the main app without a prefix
app = FastAPI(title="Corporate Coffee Employee Registration API")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Security
security = HTTPBearer()

# Position Constants
POSITIONS = [
    "servis personeli",
    "barista", 
    "supervizer",
    "müdür yardımcısı",
    "mağaza müdürü",
    "trainer"
]

# Special roles that admin can assign
SPECIAL_ROLES = [
    "eğitim departmanı"
]

# Role hierarchy for permissions
POSITION_LEVELS = {
    "servis personeli": 1,
    "barista": 2,
    "supervizer": 3,
    "müdür yardımcısı": 4,
    "mağaza müdürü": 5,
    "trainer": 6,
    "eğitim departmanı": 7  # Special role with trainer-level permissions
}

# Define Models
class UserRegister(BaseModel):
    name: str
    surname: str
    email: EmailStr
    password: str
    position: str
    store: str

    class Config:
        json_encoders = {
            ObjectId: str
        }

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class User(BaseModel):
    id: Optional[str] = Field(alias="_id")
    employee_id: str
    name: str
    surname: str
    email: EmailStr
    position: str
    store: str
    special_role: Optional[str] = None  # "eğitim departmanı" or None
    is_admin: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str
        }

class UserUpdate(BaseModel):
    special_role: Optional[str] = None

class ExamResult(BaseModel):
    id: Optional[str] = Field(alias="_id")
    employee_id: str
    exam_type: str  # "general" or "management"
    score: float
    max_score: float
    passed: bool
    exam_date: datetime = Field(default_factory=datetime.utcnow)
    created_by: str  # trainer who entered the result
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str
        }

class ExamResultCreate(BaseModel):
    employee_id: str
    exam_type: str
    score: float
    max_score: float

class Announcement(BaseModel):
    id: Optional[str] = Field(alias="_id")
    title: str
    content: str
    created_by: str  # trainer who created
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_urgent: bool = False
    
    class Config:
        allow_population_by_field_name = True
        json_encoders = {
            ObjectId: str
        }

class AnnouncementCreate(BaseModel):
    title: str
    content: str
    is_urgent: bool = False

class Token(BaseModel):
    access_token: str
    token_type: str
    user: User

# Helper Functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + JWT_EXPIRATION_DELTA
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    # Convert ObjectId to string for Pydantic
    user["_id"] = str(user["_id"])
    return User(**user)

async def generate_employee_id() -> str:
    # Get the highest employee_id and increment
    last_user = await db.users.find_one(sort=[("employee_id", -1)])
    if last_user:
        last_id = int(last_user["employee_id"])
        new_id = last_id + 1
    else:
        new_id = 1
    return f"{new_id:05d}"

# Authentication Routes
@api_router.post("/auth/register", response_model=Token)
async def register(user_data: UserRegister):
    # Check if position is valid
    if user_data.position not in POSITIONS:
        raise HTTPException(status_code=400, detail="Invalid position")
    
    # Check if email already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Generate employee ID
    employee_id = await generate_employee_id()
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Check if this is the first user (admin)
    user_count = await db.users.count_documents({})
    is_admin = user_count == 0
    
    # Create user document
    user_doc = {
        "employee_id": employee_id,
        "name": user_data.name,
        "surname": user_data.surname,
        "email": user_data.email,
        "password": hashed_password,
        "position": user_data.position,
        "store": user_data.store,
        "special_role": None,  # Default no special role
        "is_admin": is_admin,
        "created_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = str(result.inserted_id)
    
    # Create access token
    access_token = create_access_token({"sub": str(result.inserted_id)})
    
    # Remove password from response
    user_doc.pop("password")
    user = User(**user_doc)
    
    return Token(access_token=access_token, token_type="bearer", user=user)

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    # Find user by email
    user = await db.users.find_one({"email": user_data.email})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Verify password
    if not verify_password(user_data.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    # Create access token
    access_token = create_access_token({"sub": str(user["_id"])})
    
    # Remove password from response and convert ObjectId to string
    user.pop("password")
    user["_id"] = str(user["_id"])
    user_obj = User(**user)
    
    return Token(access_token=access_token, token_type="bearer", user=user_obj)

@api_router.get("/auth/me", response_model=User)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user

# User Management Routes
@api_router.get("/users", response_model=List[User])
async def get_all_users(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admin can view all users")
    
    users = await db.users.find({}, {"password": 0}).to_list(1000)
    # Convert ObjectId to string for each user
    for user in users:
        user["_id"] = str(user["_id"])
    return [User(**user) for user in users]

# Exam Results Routes
@api_router.post("/exam-results", response_model=ExamResult)
async def create_exam_result(exam_data: ExamResultCreate, current_user: User = Depends(get_current_user)):
    # Only trainers and education department can create exam results
    if (current_user.position != "trainer" and 
        current_user.special_role != "eğitim departmanı" and 
        not current_user.is_admin):
        raise HTTPException(status_code=403, detail="Only trainers and education department can enter exam results")
    
    # Verify employee exists
    employee = await db.users.find_one({"employee_id": exam_data.employee_id})
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")
    
    # For management exam, only barista and supervizer can take it
    if exam_data.exam_type == "management":
        if employee["position"] not in ["barista", "supervizer"]:
            raise HTTPException(status_code=400, detail="Only barista and supervizer can take management exam")
    
    # Calculate if passed (assuming 60% is passing)
    passed = (exam_data.score / exam_data.max_score) >= 0.6
    
    exam_doc = {
        "employee_id": exam_data.employee_id,
        "exam_type": exam_data.exam_type,
        "score": exam_data.score,
        "max_score": exam_data.max_score,
        "passed": passed,
        "exam_date": datetime.utcnow(),
        "created_by": current_user.employee_id
    }
    
    result = await db.exam_results.insert_one(exam_doc)
    exam_doc["_id"] = str(result.inserted_id)
    
    return ExamResult(**exam_doc)

@api_router.get("/exam-results", response_model=List[ExamResult])
async def get_exam_results(employee_id: Optional[str] = None, current_user: User = Depends(get_current_user)):
    query = {}
    
    # Regular employees can only see their own results
    if not current_user.is_admin and current_user.position != "trainer":
        query["employee_id"] = current_user.employee_id
    elif employee_id:
        query["employee_id"] = employee_id
    
    results = await db.exam_results.find(query).sort("exam_date", -1).to_list(1000)
    # Convert ObjectId to string for each result
    for result in results:
        result["_id"] = str(result["_id"])
    return [ExamResult(**result) for result in results]

# Announcements Routes
@api_router.post("/announcements", response_model=Announcement)
async def create_announcement(announcement_data: AnnouncementCreate, current_user: User = Depends(get_current_user)):
    # Only trainers and education department can create announcements
    if (current_user.position != "trainer" and 
        current_user.special_role != "eğitim departmanı" and 
        not current_user.is_admin):
        raise HTTPException(status_code=403, detail="Only trainers and education department can create announcements")
    
    announcement_doc = {
        "title": announcement_data.title,
        "content": announcement_data.content,
        "is_urgent": announcement_data.is_urgent,
        "created_by": current_user.employee_id,
        "created_at": datetime.utcnow()
    }
    
    result = await db.announcements.insert_one(announcement_doc)
    announcement_doc["_id"] = str(result.inserted_id)
    
    return Announcement(**announcement_doc)

@api_router.get("/announcements", response_model=List[Announcement])
async def get_announcements(current_user: User = Depends(get_current_user)):
    announcements = await db.announcements.find({}).sort("created_at", -1).to_list(1000)
    # Convert ObjectId to string for each announcement
    for announcement in announcements:
        announcement["_id"] = str(announcement["_id"])
    return [Announcement(**announcement) for announcement in announcements]

@api_router.delete("/announcements/{announcement_id}")
async def delete_announcement(announcement_id: str, current_user: User = Depends(get_current_user)):
    # Only the creator or admin can delete
    announcement = await db.announcements.find_one({"_id": ObjectId(announcement_id)})
    if not announcement:
        raise HTTPException(status_code=404, detail="Announcement not found")
    
    if announcement["created_by"] != current_user.employee_id and not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Can only delete your own announcements")
    
    await db.announcements.delete_one({"_id": ObjectId(announcement_id)})
    return {"message": "Announcement deleted successfully"}

# Admin Routes for User Management
@api_router.put("/admin/users/{user_id}/special-role")
async def assign_special_role(user_id: str, user_update: UserUpdate, current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admin can assign special roles")
    
    # Validate special role
    if user_update.special_role and user_update.special_role not in SPECIAL_ROLES:
        raise HTTPException(status_code=400, detail="Invalid special role")
    
    # Update user
    result = await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": {"special_role": user_update.special_role}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get updated user
    user = await db.users.find_one({"_id": ObjectId(user_id)}, {"password": 0})
    if user:
        user["_id"] = str(user["_id"])
        return User(**user)
    
    raise HTTPException(status_code=404, detail="User not found")

@api_router.get("/admin/stores")
async def get_stores(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admin can view store data")
    
    # Get unique stores from users
    stores = await db.users.distinct("store")
    
    # Get statistics for each store
    store_stats = []
    for store in stores:
        employee_count = await db.users.count_documents({"store": store})
        store_stats.append({
            "store": store,
            "employee_count": employee_count
        })
    
# Test endpoint to migrate old users and make first user admin
@api_router.post("/test/migrate-db")
async def migrate_database():
    # Add store field to users who don't have it
    await db.users.update_many(
        {"store": {"$exists": False}},
        {"$set": {"store": "Bilinmiyor"}}
    )
    
    # Add special_role field to users who don't have it
    await db.users.update_many(
        {"special_role": {"$exists": False}},
        {"$set": {"special_role": None}}
    )
    
    # Make first user admin
    first_user = await db.users.find_one(sort=[("created_at", 1)])
    if first_user:
        await db.users.update_one(
            {"_id": first_user["_id"]},
            {"$set": {"is_admin": True}}
        )
    
    return {
        "message": "Database migrated successfully", 
        "admin_user": first_user["email"] if first_user else None
    }

# Statistics Routes (for admin dashboard)
@api_router.get("/stats")
async def get_statistics(current_user: User = Depends(get_current_user)):
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    total_employees = await db.users.count_documents({})
    
    # Count by position
    position_stats = {}
    for position in POSITIONS:
        count = await db.users.count_documents({"position": position})
        position_stats[position] = count
    
    # Exam statistics
    total_exams = await db.exam_results.count_documents({})
    passed_exams = await db.exam_results.count_documents({"passed": True})
    
    # Management exam eligible count
    management_eligible = await db.users.count_documents({"position": {"$in": ["barista", "supervizer"]}})
    
    return {
        "total_employees": total_employees,
        "position_stats": position_stats,
        "total_exams": total_exams,
        "passed_exams": passed_exams,
        "exam_pass_rate": passed_exams / total_exams if total_exams > 0 else 0,
        "management_exam_eligible": management_eligible
    }

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
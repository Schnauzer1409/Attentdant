# ===============================
# IMPORT THƯ VIỆN
# ===============================
from watermark_feature import train_watermark, verify_watermark
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import shutil

from pathlib import Path
import sqlite3
import base64
import io
import time
import pickle

from dotenv import load_dotenv
import os
from pathlib import Path

import numpy as np
from PIL import Image

from insightface.app import FaceAnalysis


# ===============================
# KHAI BÁO THƯ MỤC
# ===============================
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env.dev")

WATERMARK_THRESHOLD = float(
    os.getenv("WATERMARK_THRESHOLD", 0.15)
)

SAVE_DIR = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
ENROLL_DIR = SAVE_DIR / os.getenv("ENROLL_DIR", "enroll")        # ảnh đăng ký khuôn mặt
ATT_DIR = SAVE_DIR / os.getenv("ATTENDANCE_DIR", "attendance")       # ảnh điểm danh
WM_DIR = BASE_DIR / os.getenv("WATERMARK_DIR", "watermarks")        # ảnh watermark phòng

SAVE_DIR.mkdir(parents=True, exist_ok=True)
ENROLL_DIR.mkdir(parents=True, exist_ok=True)
ATT_DIR.mkdir(parents=True, exist_ok=True)
WM_DIR.mkdir(parents=True, exist_ok=True)


# ===============================
# KHỞI TẠO FASTAPI
# ===============================
app = FastAPI()

FRONTEND_DIR = BASE_DIR.parent / "Frontend"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # test
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ===============================
# DATABASE SQLITE
# ===============================
DB_PATH = BASE_DIR / os.getenv("DB_PATH", "attendance.db")

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def sql(query, params=()):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(query, params)
    conn.commit()
    rows = cur.fetchall()
    conn.close()
    return rows


# Bảng user
sql("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT,
    token TEXT
)
""")

# Bảng lưu embedding khuôn mặt
sql("""
CREATE TABLE IF NOT EXISTS encodings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    embedding BLOB
)
""")


# ===============================
# TẠO USER MẪU
# ===============================
def add_default_users():
    users = sql("SELECT username FROM users")
    existed = {u[0] for u in users}

    if "teacher1" not in existed:
        sql(
            "INSERT INTO users(username,password,role) VALUES (?,?,?)",
            ("teacher1", "123456", "teacher")
        )

    if "student1" not in existed:
        sql(
            "INSERT INTO users(username,password,role) VALUES (?,?,?)",
            ("student1", "123456", "student")
        )
    
    if "363636" not in existed:
        sql(
            "INSERT INTO users(username,password,role) VALUES (?,?,?)",
            ("363636", "123456", "student")
        )

add_default_users()


# ===============================
# LOAD MODEL NHẬN DIỆN
# ===============================
face_app = FaceAnalysis(name=os.getenv("FACE_MODEL", "buffalo_l"))

det_size = tuple(
    map(int, os.getenv("FACE_DET_SIZE", "640,640").split(","))
)

face_app.prepare(
    ctx_id=int(os.getenv("FACE_CTX_ID", 0)),
    det_size=det_size
)


# ===============================
# HÀM TIỆN ÍCH
# ===============================
# Chuyển base64 → numpy image
def decode_base64_to_image(b64):
    header, data = b64.split(",", 1)
    img_bytes = base64.b64decode(data)
    return np.array(Image.open(io.BytesIO(img_bytes)).convert("RGB"))

# Tính độ giống cosine
def cosine(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
import cv2



# ===============================
# API LOGIN
# ===============================
@app.post("/api/login")
def login(username: str = Form(...), password: str = Form(...)):
    user = sql(
        "SELECT username,password,role FROM users WHERE username=?",
        (username,)
    )

    if not user:
        return {"status": "fail", "msg": "User không tồn tại"}

    db_user, db_pass, role = user[0]

    if password != db_pass:
        return {"status": "fail", "msg": "Sai mật khẩu"}

    token = f"{username}_{int(time.time())}"
    sql("UPDATE users SET token=? WHERE username=?", (token, username))

    return {
        "status": "ok",
        "username": username,
        "role": role,
        "token": token
    }


# ===============================
# ENROLL KHUÔN MẶT (GIÁO VIÊN)
# ===============================
@app.post("/api/enroll")
def enroll(username: str = Form(...), file: UploadFile = File(...)):
    img_bytes = file.file.read()

    # Lưu ảnh
    filename = f"{username}_{int(time.time())}.jpg"
    with open(ENROLL_DIR / filename, "wb") as f:
        f.write(img_bytes)

    # Nhận diện mặt
    img_np = np.array(Image.open(io.BytesIO(img_bytes)).convert("RGB"))
    faces = face_app.get(img_np)

    if len(faces) == 0:
        return {"status": "no_face"}

    # Lấy embedding
    emb = faces[0].embedding
    emb_blob = pickle.dumps(emb)

    # Lưu vào DB
    sql(
        "INSERT INTO encodings(username,embedding) VALUES (?,?)",
        (username, emb_blob)
    )

    return {"status": "ok", "msg": "Enroll thành công"}


# ===============================
# NHẬN DIỆN REALTIME
# ===============================
@app.post("/api/frame")
def frame(img: str = Form(...)):
    img_np = decode_base64_to_image(img)
    faces = face_app.get(img_np)

    if len(faces) == 0:
        return {"status": "noface"}

    emb = faces[0].embedding
    encs = sql("SELECT username, embedding FROM encodings")

    best_user = None
    best_score = -1

    for uname, blob in encs:
        known_emb = pickle.loads(blob)
        score = cosine(emb, known_emb)

        if score > best_score:
            best_score = score
            best_user = uname

    if best_score < 0.5:
        return {"status": "unknown", "score": best_score}

    return {
        "status": "ok",
        "recognized": best_user,
        "score": best_score
    }


# ===============================
# API ĐIỂM DANH
# ===============================
@app.post("/api/attendance")
def attendance(username: str = Form(...), file: UploadFile = File(...)):
    # ======================
    # 1. Đọc ảnh gửi lên
    # ======================
    img_bytes = file.file.read()

    filename = f"{username}_{int(time.time())}.jpg"
    with open(ATT_DIR / filename, "wb") as f:
        f.write(img_bytes)

    img_np = np.array(Image.open(io.BytesIO(img_bytes)).convert("RGB"))

    # ======================
    # 2. CHECK KHUÔN MẶT
    # ======================
    faces = face_app.get(img_np)

    if len(faces) == 0:
        return {"status": "fail", "msg": "Không phát hiện khuôn mặt"}

    emb = faces[0].embedding
    encs = sql("SELECT username, embedding FROM encodings")

    best_user = None
    best_score = -1

    for uname, blob in encs:
        known_emb = pickle.loads(blob)
        score = cosine(emb, known_emb)

        if score > best_score:
            best_score = score
            best_user = uname

    if best_score < 0.6:
        return {"status": "fail", "msg": "Khuôn mặt không khớp"}

    if best_user != username:
        return {"status": "fail", "msg": "Sai người điểm danh"}

    # ======================
    # 3. CHECK WATERMARK (FEATURE MATCHING)
    # ======================
    # Chuyển từ RGB (PIL) sang BGR (OpenCV) trước khi verify
    img_bgr = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)

# Gọi hàm verify từ watermark_feature.py
    is_valid, wm_score = verify_watermark(img_bgr) 

    if not is_valid:
        pass
    return {
        "status": "fail",
        "msg": f"Watermark không khớp hoặc không đủ rõ (Score: {wm_score})"
    }

    # ======================
    # 4. THÀNH CÔNG
    # ======================
    return {
        "status": "success",
        "msg": f"Điểm danh thành công cho {username}"
    }

# ===============================
# XÓA TOÀN BỘ ENCODING
# ===============================
@app.get("/api/clear_encodings")
def clear_encodings():
    sql("DELETE FROM encodings")
    return {"status": "ok"}


# ===============================
# WATERMARK (ẢNH PHÒNG)
# ===============================
@app.post("/api/teacher_generate_watermark")
def generate_watermark(file: UploadFile = File(...)):
    import cv2

    img_bytes = file.file.read()
    img = np.array(Image.open(io.BytesIO(img_bytes)).convert("RGB"))

    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    edges = cv2.Sobel(gray, cv2.CV_64F, 1, 1, ksize=3)

    h, w = gray.shape
    wm_size = 400
    best_score = -1
    bx = by = 0

    for y in range(0, h - wm_size, 20):
        for x in range(0, w - wm_size, 20):
            score = edges[y:y+wm_size, x:x+wm_size].sum()
            if score > best_score:
                best_score = score
                bx, by = x, y

    crop = img[by:by+wm_size, bx:bx+wm_size]

    # Lưu watermark tạm
    Image.fromarray(crop).save(WM_DIR / "temp_watermark.jpg")

    # Trả về base64 để frontend hiển thị
    buf = io.BytesIO()
    Image.fromarray(crop).save(buf, format="JPEG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    return {
        "status": "ok",
        "watermark": b64
    }
# ===============================
# TRAIN WATERMARK (GIÁO VIÊN)
# ===============================
@app.post("/api/train_watermark")
async def train_watermark_api(files: list[UploadFile] = File(...)):
    images = []
    for file in files:
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        # Đọc trực tiếp ra dạng BGR để train cho chuẩn
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is not None:
            images.append(img)

    if len(images) < 1:
        return {"status": "error", "msg": "Không nhận được ảnh nào"}

    try:
        # Gọi hàm train đã có trong watermark_feature.py
        result = train_watermark(images)
        return result
    except Exception as e:
        return {"status": "error", "msg": str(e)}
# ===============================
# SET WATERMARK (ACTIVE)
# ===============================
@app.post("/api/set_watermark")
def set_watermark():
    """
    Đặt watermark hiện tại làm watermark chính thức để verify
    """

    src = WM_DIR / "room_watermark.jpg"
    dst = WM_DIR / "active_watermark.jpg"

    if not src.exists():
        return {
            "status": "fail",
            "msg": "Chưa upload watermark"
        }

    # Copy / overwrite
    Image.open(src).save(dst)

    return {
        "status": "ok",
        "msg": "Đã set watermark cho phòng học"
    }

# ===============================
# UPLOAD WATERMARK (GIÁO VIÊN)
# ===============================
# @app.post("/api/upload_watermark")
# def upload_watermark(file: UploadFile = File(...)):
#     """
#     Upload watermark phòng học chính thức
#     """

#     try:
#         img_bytes = file.file.read()
#         img = np.array(Image.open(io.BytesIO(img_bytes)).convert("RGB"))

#         # Lưu watermark cố định
#         wm_path = WM_DIR / "room_watermark.jpg"
#         Image.fromarray(img).save(wm_path)

#         return {
#             "status": "ok",
#             "msg": "Upload watermark thành công",
#             "path": str(wm_path)
#         }

#     except Exception as e:
#         return {
#             "status": "error",
#             "msg": str(e)
#         }
@app.post("/api/upload_watermark")
def upload_watermark(file: UploadFile = File(...)):
    """
    Upload watermark phòng học chính thức
    """
    try:
        filename = file.filename
        if not filename:
            return {
                "status": "error",
                "msg": "File không có tên"
            }

        file_extension = filename.rsplit(".", 1)[-1].lower()
        wm_path = WM_DIR / f"room_watermark.{file_extension}"

        with open(wm_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        return {
            "status": "ok",
            "msg": "Upload watermark thành công",
            "path": str(wm_path)
        }

    except Exception as e:
        return {
            "status": "error",
            "msg": str(e)
        }
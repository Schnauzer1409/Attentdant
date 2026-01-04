import cv2
import numpy as np
import pickle
from pathlib import Path
from typing import Optional
import os

# =====================================================
# CẤU HÌNH
# =====================================================
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

WM_FEATURE_FILE = DATA_DIR / "watermark_feature.pkl"

# ORB detector (nhẹ – ổn định)
ORB = cv2.ORB.create(
    nfeatures=2000,
    scaleFactor=1.2,
    nlevels=8
)

# =====================================================
# TRÍCH XUẤT ĐẶC TRƯNG TỪ 1 ẢNH
# =====================================================
def extract_feature(image_bgr) -> Optional[np.ndarray]:
    """
    image_bgr: ảnh OpenCV (BGR)
    return: descriptors (numpy array) hoặc None
    """

    if image_bgr is None:
        return None
    h, w = image_bgr.shape[:2]
    standard_w = 1024
    standard_h = int(h * (standard_w / w))
    image_bgr = cv2.resize(image_bgr, (standard_w, standard_h))

    gray = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2GRAY)

    # ⚠️ Pylance không hiểu C-extension → ignore type
    keypoints, descriptors = ORB.detectAndCompute(gray, None)  # type: ignore

    if descriptors is None or len(descriptors) < 20:
        return None

    return descriptors


# =====================================================
# TRAIN WATERMARK (NHIỀU ẢNH → 1 FEATURE)
# =====================================================
def train_watermark(image_list):
    """
    image_list: danh sách các ảnh OpenCV (BGR)
    """
    all_desc = []

    for img in image_list:
        if img is None: continue
        
        # CHUẨN HÓA: Resize ảnh về độ phân giải chuẩn (ví dụ ngang 1000px)
        # Điều này giúp các điểm đặc trưng (keypoints) có kích cỡ tương đồng nhau
        h, w = img.shape[:2]
        target_w = 1000
        target_h = int(h * (target_w / w))
        img_resized = cv2.resize(img, (target_w, target_h))
        
        desc = extract_feature(img_resized)
        if desc is not None:
            all_desc.append(desc)

    if len(all_desc) == 0:
        raise ValueError("Không thể trích xuất đặc trưng từ bất kỳ ảnh nào!")

    # Gộp tất cả vector đặc trưng của 5 ảnh vào làm 1 bộ mẫu duy nhất
    all_desc_combined = np.vstack(all_desc)

    with open(WM_FEATURE_FILE, "wb") as f:
        pickle.dump(all_desc_combined, f)

    return {
        "status": "ok",
        "total_descriptors": int(len(all_desc_combined))
    }


# =====================================================
# VERIFY WATERMARK (SO ẢNH MỚI VỚI FEATURE ĐÃ TRAIN)
# =====================================================
def verify_watermark(image_bgr, min_matches: int = 15): # Giảm ngưỡng match xuống
    """
    Sử dụng KNN Match và Lowe's Ratio Test để lọc nhiễu tốt hơn
    """
    if not WM_FEATURE_FILE.exists():
        print("Chưa có dữ liệu train")
        return False, 0

    desc_query = extract_feature(image_bgr)
    if desc_query is None:
        return False, 0

    with open(WM_FEATURE_FILE, "rb") as f:
        desc_train = pickle.load(f)

    # 1. Cấu hình Matcher
    # Nếu dùng SIFT: normType=cv2.NORM_L2
    # Nếu dùng ORB: normType=cv2.NORM_HAMMING
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING) 
    
    # 2. Dùng KNN Match (k=2) để lấy 2 ứng viên tốt nhất cho mỗi điểm
    try:
        matches = matcher.knnMatch(desc_query, desc_train, k=2)
    except Exception as e:
        print(f"Lỗi matching: {e}")
        return False, 0

    # 3. Áp dụng Lowe's Ratio Test
    # Ý nghĩa: Điểm match tốt nhất (m) phải tốt hơn hẳn điểm match nhì (n)
    # Nếu m và n gần nhau quá => máy đang phân vân => loại bỏ (đây thường là nhiễu, pattern lặp lại như sàn nhà, trần)
    good_matches = []
    ratio_thresh = 0.85
    
    for m, n in matches:
        if m.distance < ratio_thresh * n.distance:
            good_matches.append(m)

    score = len(good_matches)
    
    # 4. Logic điểm danh
    # Vì ảnh selfie background nhỏ, số lượng match xịn sẽ không nhiều như ảnh toàn cảnh
    # 15-20 điểm "xịn" đã qua lọc Ratio Test là đủ tin cậy hơn 50 điểm lọc bằng distance
    print(f"Tìm thấy {score} điểm khớp chất lượng cao.")
    
    is_valid = score >= min_matches
    return is_valid, score
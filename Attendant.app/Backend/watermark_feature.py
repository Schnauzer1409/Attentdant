import cv2
import numpy as np
import pickle
from pathlib import Path
from typing import Optional
import os




DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

WM_FEATURE_FILE = DATA_DIR / "watermark_feature.pkl"


ORB = cv2.ORB.create(
    nfeatures=2000,
    scaleFactor=1.2,
    nlevels=8
)




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

    keypoints, descriptors = ORB.detectAndCompute(gray, None)   #type: ignore

    if descriptors is None or len(descriptors) < 20:
        return None

    return descriptors



def train_watermark(image_list):
    """
    image_list: danh sách các ảnh OpenCV (BGR)
    """
    all_desc = []

    for img in image_list:
        if img is None: continue
        
        
        h, w = img.shape[:2]
        target_w = 1000
        target_h = int(h * (target_w / w))
        img_resized = cv2.resize(img, (target_w, target_h))
        
        desc = extract_feature(img_resized)
        if desc is not None:
            all_desc.append(desc)

    if len(all_desc) == 0:
        raise ValueError("Không thể trích xuất đặc trưng từ bất kỳ ảnh nào!")

    
    all_desc_combined = np.vstack(all_desc)

    with open(WM_FEATURE_FILE, "wb") as f:
        pickle.dump(all_desc_combined, f)

    return {
        "status": "ok",
        "total_descriptors": int(len(all_desc_combined))
    }



def verify_watermark(image_bgr, min_matches: int = 15): 
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

    
    
    
    matcher = cv2.BFMatcher(cv2.NORM_HAMMING) 
    
    
    try:
        matches = matcher.knnMatch(desc_query, desc_train, k=2)
    except Exception as e:
        print(f"Lỗi matching: {e}")
        return False, 0

    
    
    
    good_matches = []
    ratio_thresh = 0.85
    
    for m, n in matches:
        if m.distance < ratio_thresh * n.distance:
            good_matches.append(m)

    score = len(good_matches)
    
    
    
    
    print(f"Tìm thấy {score} điểm khớp chất lượng cao.")
    
    is_valid = score >= min_matches
    return is_valid, score
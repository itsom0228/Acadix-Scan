import os
import time
from typing import Dict, List, Tuple, Optional

import cv2
import numpy as np

from data_manager import get_student_by_name, mark_attendance_if_absent


HAAR_FILENAME = "haarcascade_frontalface_default.xml"
DATASET_DIR = "dataset"
MODEL_PATH = "face_model.yml"


def _resolve_haar_path() -> Optional[str]:
    """Return the best path to the haarcascade file.

    Priority:
    1. File located in the same directory as this module
    2. OpenCV bundled haarcascades (cv2.data.haarcascades)
    Returns None if not found.
    """
    # 1) Look next to this file
    local_path = os.path.join(os.path.dirname(__file__), HAAR_FILENAME)
    if os.path.exists(local_path):
        return local_path

    # 2) Fallback to OpenCV's data directory if available
    try:
        opencv_path = os.path.join(cv2.data.haarcascades, HAAR_FILENAME)
        if os.path.exists(opencv_path):
            return opencv_path
    except Exception:
        pass

    return None


def ensure_dirs() -> None:
    os.makedirs(DATASET_DIR, exist_ok=True)


def capture_faces_from_ipcam(ip_url: str, student_full_name: str, num_samples: int = 20) -> Tuple[bool, str]:
    ensure_dirs()
    haar_path = _resolve_haar_path()
    if not haar_path:
        return False, f"Missing {HAAR_FILENAME}. Place it next to the project module or ensure OpenCV includes it."

    # Check if student already has face data captured
    save_dir = os.path.join(DATASET_DIR, student_full_name)
    if os.path.exists(save_dir) and len(os.listdir(save_dir)) > 0:
        return False, f"Face data already exists for {student_full_name}. Each student can only capture face data once."

    face_cascade = cv2.CascadeClassifier(haar_path)
    os.makedirs(save_dir, exist_ok=True)

    # Normalize URL to fix common mistakes and then try opening as a stream
    ip_url = _normalize_ipcam_url(ip_url)
    cap = cv2.VideoCapture(ip_url)

    # Open a live preview window while capturing
    window = "Acadix Scan - Capture"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)

    # For IP webcam that serves snapshot JPEGs (e.g., http://<ip>:<port>/shot.jpg)
    captured = 0
    timeout_s = 60
    start = time.time()
    cancelled = False

    while captured < num_samples and (time.time() - start) < timeout_s:
        # Read frame from stream if available, else snapshot endpoint
        frame = None
        if cap.isOpened():
            ok, frm = cap.read()
            if ok and frm is not None:
                frame = frm
        if frame is None:
            try:
                frame = cv2.imdecode(np.frombuffer(_read_url_bytes(ip_url), np.uint8), cv2.IMREAD_COLOR)
            except Exception:
                time.sleep(0.3)
                continue
        if frame is None:
            time.sleep(0.2)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))

        # Draw faces and overlay capture count
        for (x, y, w, h) in faces:
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        cv2.putText(
            frame,
            f"Capturing: {captured}/{num_samples}",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            (0, 200, 255),
            2,
            cv2.LINE_AA,
        )

        # Save one sample per frame if a face exists
        if len(faces) > 0:
            x, y, w, h = faces[0]
            roi = gray[y : y + h, x : x + w]
            resized = cv2.resize(roi, (200, 200))
            img_path = os.path.join(save_dir, f"{student_full_name}_{captured+1}.png")
            cv2.imwrite(img_path, resized)
            captured += 1

        cv2.imshow(window, frame)
        k = cv2.waitKey(1) & 0xFF
        if k == 27:  # ESC to cancel
            cancelled = True
            break

        time.sleep(0.1)

    # Cleanup preview window
    try:
        cv2.destroyWindow(window)
    except Exception:
        pass
    try:
        if cap is not None:
            cap.release()
    except Exception:
        pass

    if cancelled:
        return False, f"Capture cancelled. Collected {captured}/{num_samples} samples."
    if captured < num_samples:
        return False, f"Only captured {captured}/{num_samples} samples. Ensure lighting/face in frame."
    return True, f"Captured {captured} face samples."


def _read_url_bytes(url: str) -> bytes:
    # Simple urllib read to avoid adding requests dependency
    import urllib.request

    with urllib.request.urlopen(url, timeout=5) as resp:
        return resp.read()


def _normalize_ipcam_url(url: str) -> str:
    """Normalize common IP camera URL mistakes.

    - If user passed an IP with port incorrectly concatenated with a dot
      like `10.214.110.18.8080`, convert to `10.214.110.18:8080`.
    - If no scheme present (starts with digits or `//`), prepend `http://`.
    Returns the normalized URL string.
    """
    import re

    if not url:
        return url

    url = url.strip()

    # Fix pattern like 10.214.110.18.8080 or 192.168.0.100.8080[/path]
    m = re.match(r"^(\d+\.\d+\.\d+\.\d+)\.(\d+)(/.*)?$", url)
    if m:
        host = m.group(1)
        port = m.group(2)
        tail = m.group(3) or ""
        url = f"{host}:{port}{tail}"

    # If URL has no scheme, add http:// (covers IPs and hostnames)
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*://", url):
        # also allow URLs that begin with double slash
        if url.startswith("//"):
            url = "http:" + url
        else:
            url = "http://" + url

    return url


def _collect_dataset() -> Tuple[List[np.ndarray], List[int], List[str]]:
    images: List[np.ndarray] = []
    labels: List[int] = []
    names: List[str] = []
    ensure_dirs()
    label_map: Dict[str, int] = {}
    next_label = 0

    for person_name in sorted(os.listdir(DATASET_DIR)):
        person_dir = os.path.join(DATASET_DIR, person_name)
        if not os.path.isdir(person_dir):
            continue
        label_map[person_name] = next_label
        next_label += 1
        for fname in os.listdir(person_dir):
            if not (fname.lower().endswith(".png") or fname.lower().endswith(".jpg")):
                continue
            img_path = os.path.join(person_dir, fname)
            img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                continue
            images.append(img)
            labels.append(label_map[person_name])
    # reverse map to names by label index order
    names = [None] * len(label_map)
    for name, lab in label_map.items():
        names[lab] = name
    return images, labels, names


def train_model() -> Tuple[bool, str]:
    images, labels, names = _collect_dataset()
    if len(images) == 0:
        return False, "Dataset is empty. Capture faces first."

    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
    except Exception:
        return False, "cv2.face not available. Install opencv-contrib-python."

    recognizer.train(images, np.array(labels))
    recognizer.write(MODEL_PATH)

    # Save label names mapping next to model
    with open(MODEL_PATH + ".labels", "w", encoding="utf-8") as f:
        for idx, name in enumerate(names):
            f.write(f"{idx},{name}\n")
    return True, f"Model trained with {len(names)} identities."


def _load_labels() -> Dict[int, str]:
    labels_path = MODEL_PATH + ".labels"
    mapping: Dict[int, str] = {}
    if not os.path.exists(labels_path):
        return mapping
    with open(labels_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            idx_str, name = line.split(",", 1)
            try:
                mapping[int(idx_str)] = name
            except Exception:
                continue
    return mapping


def recognize_from_ipcam_and_mark(ip_url: str, max_seconds: int = 20) -> Tuple[bool, str]:
    haar_path = _resolve_haar_path()
    if not haar_path:
        return False, f"Missing {HAAR_FILENAME}. Place it next to the project module or ensure OpenCV includes it."
    if not os.path.exists(MODEL_PATH):
        return False, "Trained model not found. Train first."

    face_cascade = cv2.CascadeClassifier(haar_path)
    try:
        recognizer = cv2.face.LBPHFaceRecognizer_create()
    except Exception:
        return False, "cv2.face not available. Install opencv-contrib-python."
    recognizer.read(MODEL_PATH)
    label_to_name = _load_labels()

    # Normalize URL before using it
    ip_url = _normalize_ipcam_url(ip_url)
    start = time.time()
    last_frame_time = 0.0
    window = "Acadix Scan - Recognition"
    cv2.namedWindow(window, cv2.WINDOW_NORMAL)

    recognized_name: Optional[str] = None
    recognized_confidence: Optional[float] = None

    while (time.time() - start) < max_seconds:
        try:
            frame = cv2.imdecode(np.frombuffer(_read_url_bytes(ip_url), np.uint8), cv2.IMREAD_COLOR)
        except Exception:
            time.sleep(0.2)
            continue
        if frame is None:
            time.sleep(0.1)
            continue

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(80, 80))
        for (x, y, w, h) in faces:
            roi = gray[y : y + h, x : x + w]
            resized = cv2.resize(roi, (200, 200))
            label, confidence = recognizer.predict(resized)
            name = label_to_name.get(label, "Unknown")

            # Draw
            color = (0, 255, 0) if confidence < 50.0 else (0, 0, 255)
            cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
            text = f"{name} ({100 - int(confidence)}%)"
            cv2.putText(frame, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

            if confidence < 50.0:
                recognized_name = name
                recognized_confidence = 100 - confidence

        cv2.imshow(window, frame)
        k = cv2.waitKey(1) & 0xFF
        if k == 27:  # ESC to exit
            break

    cv2.destroyWindow(window)

    if recognized_name is None:
        return False, "No confident match detected."

    student = get_student_by_name(recognized_name)
    if not student:
        return False, f"Recognized name '{recognized_name}' not found in records."

    ok, msg = mark_attendance_if_absent(student.get("PRN", ""), student.get("RollNo", ""), student.get("FullName", ""))
    return ok, msg



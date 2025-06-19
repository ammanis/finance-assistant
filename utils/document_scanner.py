import cv2
import numpy as np
from imutils.perspective import four_point_transform
from pathlib import Path
import time

def enhance_image(image):
    # Convert to grayscale
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # Use CLAHE (Contrast Limited Adaptive Histogram Equalization)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
    enhanced = clahe.apply(gray)
    # Adaptive thresholding (better for varying lighting)
    thresh = cv2.adaptiveThreshold(
        enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 15, 11
    )
    return thresh

def scan_detection(image):

    # Default document contour (full image)
    WIDTH, HEIGHT = image.shape[1], image.shape[0]
    document_contour = np.array([[0, 0], [WIDTH, 0], [WIDTH, HEIGHT], [0, HEIGHT]])
    
    # Preprocess image and find largest 4-point contour
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    _, threshold = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    contours, _ = cv2.findContours(threshold, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contours = sorted(contours, key=cv2.contourArea, reverse=True)

    max_area = 0
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > 1000:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.015 * peri, True)
            if area > max_area and len(approx) == 4:
                document_contour = approx
                max_area = area

    return four_point_transform(image, document_contour.reshape(4, 2))

def process_uploaded_file(file_stream):

    # Convert uploaded file to OpenCV image
    nparr = np.frombuffer(file_stream.read(), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    
    # Detect document and enhance image
    scanned_img = scan_detection(img) # Perform scanning
    enhanced_img = enhance_image(scanned_img) # Enhance for OCR
    
    # Save processed image as PNG (lossless, better for OCR)
    save_path = Path("static/uploads")
    save_path.mkdir(exist_ok=True)
    filename = f"scan_{int(time.time())}.png"
    cv2.imwrite(str(save_path / filename), enhanced_img, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    
    return save_path / filename
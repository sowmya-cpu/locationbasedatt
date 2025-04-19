import cv2
import numpy as np
from django.core.exceptions import ObjectDoesNotExist

from .models import UserProfile

def compare_images(image1, image2):
    gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY) if image1.ndim == 3 else image1
    gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY) if image2.ndim == 3 else image2

    gray1 = cv2.resize(gray1, (100, 100))
    gray2 = cv2.resize(gray2, (100, 100))

    hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)

    return cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)


def verify_face(username, image_file, threshold=0.7):
    try:
        profile = UserProfile.objects.get(username=username)
    except ObjectDoesNotExist:
        return False

    smile_img = cv2.imread(profile.smile_image.path)
    angry_img = cv2.imread(profile.angry_image.path)
    if smile_img is None or angry_img is None:
        return False

    file_bytes = np.frombuffer(image_file.read(), dtype=np.uint8)
    uploaded_img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
    if uploaded_img is None:
        return False

    score_smile = compare_images(smile_img, uploaded_img)
    score_angry = compare_images(angry_img, uploaded_img)

    return (score_smile >= threshold) or (score_angry >= threshold)

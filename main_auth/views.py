from django.shortcuts import render

# Create your views here.
def home(request):
    return render(request, "index.html")

import cv2
import numpy as np
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from .models import UserProfile, Attendance

@csrf_exempt
def register(request):
    """
    Endpoint to register a user.
    Expects POST data with:
      - username: text field
      - smile_image: file upload
      - angry_image: file upload
    """
    if request.method == "POST":
        username = request.POST.get('username')
        smile_image = request.FILES.get('smile_image')
        angry_image = request.FILES.get('angry_image')
        
        if not username or not smile_image or not angry_image:
            return JsonResponse({'error': 'Missing username or images.'}, status=400)
        
        # Save the user profile (Django will store files in the defined MEDIA_ROOT)
        user_profile = UserProfile(username=username, smile_image=smile_image, angry_image=angry_image)
        user_profile.save()
        return JsonResponse({'message': 'User registered successfully'})
    
    return JsonResponse({'error': 'Invalid HTTP method.'}, status=405)

def compare_images(image1, image2):
    """
    A simple function that compares two images using grayscale histograms.
    Returns a correlation value between the images.
    """
    # Convert to grayscale if necessary.
    if len(image1.shape) == 3:
        gray1 = cv2.cvtColor(image1, cv2.COLOR_BGR2GRAY)
    else:
        gray1 = image1

    if len(image2.shape) == 3:
        gray2 = cv2.cvtColor(image2, cv2.COLOR_BGR2GRAY)
    else:
        gray2 = image2
    
    # Resize to a common size.
    gray1 = cv2.resize(gray1, (100, 100))
    gray2 = cv2.resize(gray2, (100, 100))
    
    # Calculate histograms.
    hist1 = cv2.calcHist([gray1], [0], None, [256], [0, 256])
    hist2 = cv2.calcHist([gray2], [0], None, [256], [0, 256])
    
    # Normalize the histograms.
    cv2.normalize(hist1, hist1)
    cv2.normalize(hist2, hist2)
    
    # Compare histograms (using correlation method).
    correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
    return correlation

@csrf_exempt
def verify(request):
    """
    Endpoint for attendance verification.
    Expects POST data with:
      - username: text field
      - image: file upload (the image to verify)
      - lat: latitude (string, e.g., "16.123123123")
      - long: longitude (string, e.g., "80.12312")
      
    This endpoint:
      - Verifies the face using stored "smile" and "angry" images.
      - Checks if the provided location is within a defined radius of a hardcoded reference point.
      - Ensures that attendance is only recorded once per user per day and only within the time window of 09:30 to 10:30 IST.
      - For debug purposes, a boolean (DEBUG_BYPASS) allows bypassing the time requirement.
    """
    import math
    from datetime import time
    import pytz

    def haversine_distance(lat1, lon1, lat2, lon2):
        # Earth's radius in meters
        R = 6371000
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)
        a = math.sin(delta_phi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    # Debug bypass to ignore time window and one-attendance-per-day restriction.
    DEBUG_BYPASS = True

    if request.method == "POST":
        username = request.POST.get('username')
        verification_image_file = request.FILES.get('image')
        lat_str = request.POST.get('lat')
        lon_str = request.POST.get('long')
        
        if not username or not verification_image_file or not lat_str or not lon_str:
            return JsonResponse({'error': 'Missing username, verification image, or coordinates.'}, status=400)
        
        try:
            user_profile = UserProfile.objects.get(username=username)
        except UserProfile.DoesNotExist:
            return JsonResponse({'error': 'User does not exist.'}, status=404)
        
        # Convert coordinates to float.
        try:
            user_lat = float(lat_str)
            user_lon = float(lon_str)
        except ValueError:
            return JsonResponse({'error': 'Invalid coordinates.'}, status=400)
        
        # Hardcoded reference location and allowed radius.
        REFERENCE_LAT = 16.5019648
        REFERENCE_LON = 80.642048
        ALLOWED_RADIUS_METERS = 100  # e.g., 100 meters
        
        distance = haversine_distance(user_lat, user_lon, REFERENCE_LAT, REFERENCE_LON)
        if distance > ALLOWED_RADIUS_METERS:
            return JsonResponse({'error': 'Location not within allowed range.'}, status=400)
        
        # Time check: Only allow attendance between 09:30 and 10:30 IST.
        ist = pytz.timezone('Asia/Kolkata')
        now_ist = timezone.now().astimezone(ist)
        if not DEBUG_BYPASS:
            if not (time(9, 30) <= now_ist.time() <= time(10, 30)):
                return JsonResponse({'error': 'Attendance can only be marked between 09:30 and 10:30 IST.'}, status=400)
        
        # Read the provided image into a NumPy array for OpenCV.
        file_bytes = np.asarray(bytearray(verification_image_file.read()), dtype=np.uint8)
        verification_image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)
        
        # Read stored images using their file paths.
        smile_image_path = user_profile.smile_image.path
        angry_image_path = user_profile.angry_image.path
        
        stored_smile_image = cv2.imread(smile_image_path)
        stored_angry_image = cv2.imread(angry_image_path)
        
        # Compare the verification image with both stored images.
        correlation_smile = compare_images(stored_smile_image, verification_image)
        correlation_angry = compare_images(stored_angry_image, verification_image)
        
        # Define a threshold value (this value may need tuning).
        threshold = 0.7
        
        if correlation_smile >= threshold or correlation_angry >= threshold:
            # Check if attendance has already been marked today.
            today = now_ist.date()
            attendance, created = Attendance.objects.get_or_create(user=user_profile, date=today)
            if not created and not DEBUG_BYPASS:
                return JsonResponse({'error': 'Attendance already marked for today.'}, status=400)
            return JsonResponse({'message': 'Attendance marked successfully.'})
        else:
            return JsonResponse({'error': 'Face verification failed.'}, status=400)
    
    return JsonResponse({'error': 'Invalid HTTP method.'}, status=405)

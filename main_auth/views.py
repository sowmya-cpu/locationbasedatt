# main_auth/views.py

import math
from datetime import time
import traceback

import cv2
import numpy as np
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db import IntegrityError

from .models import UserProfile, Attendance
from .face_utils import verify_face

# Attempt to import pytz; fall back to zoneinfo if not installed
try:
    import pytz
except ImportError:
    from zoneinfo import ZoneInfo
    class _PytzFallback:
        @staticmethod
        def timezone(name):
            return ZoneInfo(name)
    pytz = _PytzFallback()


@csrf_exempt
def index(request):
    return render(request, "index.html")


@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    username  = request.POST.get("username", "").strip()
    smile_img = request.FILES.get("smile_image")
    angry_img = request.FILES.get("angry_image")

    if not username or not smile_img or not angry_img:
        return JsonResponse(
            {"status": "failed", "error": "Missing username or images."},
            status=400
        )

    try:
        UserProfile.objects.create(
            username    = username,
            smile_image = smile_img,
            angry_image = angry_img
        )
    except IntegrityError:
        return JsonResponse(
            {"status": "failed", "error": "That username is already taken."},
            status=409
        )
    except Exception as e:
        tb = traceback.format_exc()
        return JsonResponse(
            {"status": "failed", "error": str(e), "traceback": tb},
            status=500
        )

    return JsonResponse(
        {"status": "success", "message": "User registered successfully."},
        status=201
    )


@csrf_exempt
def verify(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid HTTP method."}, status=405)

    try:
        username = request.POST.get("username")
        img_file = request.FILES.get("image")
        lat_str  = request.POST.get("lat")
        lon_str  = request.POST.get("long")

        if not (username and img_file and lat_str and lon_str):
            return JsonResponse(
                {"error": "Missing username, image, or coordinates."},
                status=400
            )

        try:
            profile = UserProfile.objects.get(username=username)
        except UserProfile.DoesNotExist:
            return JsonResponse({"error": "User does not exist."}, status=404)

        try:
            user_lat = float(lat_str)
            user_lon = float(lon_str)
        except ValueError:
            return JsonResponse({"error": "Invalid coordinates."}, status=400)

        def haversine(lat1, lon1, lat2, lon2):
            R = 6371000
            φ1, φ2 = math.radians(lat1), math.radians(lat2)
            Δφ  = math.radians(lat2 - lat1)
            Δλ  = math.radians(lon2 - lon1)
            a = math.sin(Δφ/2)**2 + math.cos(φ1)*math.cos(φ2)*math.sin(Δλ/2)**2
            return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

        REF_LAT, REF_LON = 16.7918843, 80.8211455
        dist = int(haversine(user_lat, user_lon, REF_LAT, REF_LON))
       

        ist_now = timezone.now().astimezone(pytz.timezone("Asia/Kolkata"))
        # time‑window check is commented out for now

        img_file.seek(0)
        if not verify_face(username=username, image_file=img_file):
            return JsonResponse({"error": "Face verification failed."}, status=401)

        today = ist_now.date()
        attendance, created = Attendance.objects.get_or_create(
            user=profile,
            date=today,
            defaults={"status": "present"}
        )
        
        if not created :
            return JsonResponse({"error": "Attendance already marked."}, status=400)

        return JsonResponse({
            "message":       "Attendance marked successfully.",
            "distance_m":    dist,
            "timestamp_ist": ist_now.isoformat()
        })

    except Exception as e:
        traceback.print_exc()
        return JsonResponse(
            {"error": "Internal server error.", "detail": str(e)},
            status=500
        )


@csrf_exempt
def admin_login(request):
    error = ""
    if request.method == "POST":
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        if username == "admin" and password == "k2hostel":
            # simple flag so we know admin is “logged in”
            request.session['is_admin'] = True
            return redirect("today_attendance")
        error = "Invalid credentials"
    return render(request, "admin_login.html", {"error": error})


def today_attendance(request):
    if not request.session.get('is_admin'):
        return redirect("admin_login")

    # ← changed here so admin and verify use the same IST date
    today = timezone.now().astimezone(pytz.timezone("Asia/Kolkata")).date()

    profiles = UserProfile.objects.all().order_by("id")

    attendance_qs = Attendance.objects.filter(date=today)
    attendance_map = {att.user_id: att.status for att in attendance_qs}

    records = []
    for prof in profiles:
        status = attendance_map.get(prof.id, "absent")
        records.append({
            "id":       prof.id,
            "username": prof.username,
            "status":   status.title(),
        })

    return render(request, "attendance_list.html", {
        "records": records,
        "today":   today,
    })

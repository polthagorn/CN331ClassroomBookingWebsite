from datetime import date
from django.shortcuts import render, redirect
from django.contrib import messages  # optional, for user feedback
from django.utils.dateparse import parse_date  # parses 'YYYY-MM-DD'
from .models import Classroom, Reservation


def rooms(request):
    # ต้องล็อกอิน
    user_id = request.session.get("user_id")
    if user_id is None:
        return redirect("login")

    # ค่าที่ถือว่า "เปิด" (รองรับทั้ง open/1/true)
    OPEN = {"1", "open", "Open", "OPEN", "true", "True"}

    # ห้องที่ผู้ใช้คนนี้จองไปแล้ว (แคสท์เป็น str กันชนิดไม่ตรง)
    reserved_rooms = (
        Reservation.objects
        .filter(user=str(user_id))
        .values_list("roomnumber", flat=True)
    )

    # ห้องที่ "เปิด" เท่านั้น + ยังไม่ถูกจองโดย user คนนี้
    base_qs = (
        Classroom.objects
        .filter(status__in=OPEN)
        .exclude(roomnumber__in=reserved_rooms)
    )

    ctx = {
        "smallclassroom": list(
            base_qs.filter(roomsize="s").values_list("roomnumber", flat=True)
        ),
        "mediumclassroom": list(
            base_qs.filter(roomsize="m").values_list("roomnumber", flat=True)
        ),
        "largeclassroom": list(
            base_qs.filter(roomsize="l").values_list("roomnumber", flat=True)
        ),
    }

    if request.method == "POST":
        submit_type = request.POST.get("submit_type") or ""
        button_type = request.POST.get("button_type") or ""
        rawdate = (request.POST.get("date") or "").strip()
        classroomnumber = (request.POST.get("classroom") or "").strip()
        timeselected = (request.POST.get("time") or "").strip()

        # เก็บค่าไว้ให้หน้า template เปิด popup เดิมได้
        ctx["date"] = rawdate
        ctx["classroom"] = classroomnumber

        # ขอค้นหาเวลา
        if button_type in ("small_time_search", "medium_time_search", "large_time_search"):
            chosen = parse_date(rawdate)
            if not chosen or not classroomnumber:
                return render(request, "rooms.html", ctx)

            # ดึงเวลาเริ่ม/จบ เฉพาะห้องที่ "เปิด"
            room = (
                Classroom.objects
                .filter(roomnumber=classroomnumber, status__in=OPEN)
                .values("start_time", "stop_time")
                .first()
            )
            if not room:
                ctx["error"] = "This room is closed."
                return render(request, "rooms.html", ctx)

            st_time = int(room["start_time"])
            stp_time = int(room["stop_time"])

            # เวลาที่ถูกจองแล้ว (แปลงเป็นสตริงให้เทียบกับ alltime ได้)
            taken = set(
                str(t) for t in
                Reservation.objects
                .filter(roomnumber=classroomnumber, date=rawdate)
                .values_list("time", flat=True)
            )

            # สร้างชั่วโมงทั้งหมดในช่วง [start, stop) หรือถ้า stop เป็น "ชั่วโมงสุดท้ายที่เริ่มได้"
            # และต้องการให้มี slot สุดท้ายเป็น stop-1–stop ให้ใช้ range(st_time, stp_time)
            alltime = [str(i) for i in range(st_time, stp_time + 1)]
            remaintime = [h for h in alltime if h not in taken]

            key_map = {
                "small_time_search": "s_times",
                "medium_time_search": "m_times",
                "large_time_search": "l_times",
            }
            ctx[key_map[button_type]] = remaintime
            return render(request, "rooms.html", ctx)

    return render(request, "rooms.html", ctx)


def my_reservations(request):
    # Must be logged in
    user_id = request.session.get("user_id")
    if not user_id:
        return redirect("login")

    # Handle cancel (delete) action
    if request.method == "POST":
        rid = request.POST.get("rid")
        if rid:
            # Only delete a reservation that belongs to this user
            Reservation.objects.filter(id=rid, user=str(user_id)).delete()
        return redirect("my_reservations")

    # Show this user's reservations
    reservations = Reservation.objects.filter(user=str(user_id)).order_by(
        "date", "time", "roomsize", "roomnumber"
    )

    ctx = {"reservations": reservations}
    return render(request, "my_reservations.html", ctx)

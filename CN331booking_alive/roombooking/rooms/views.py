from datetime import date
from django.shortcuts import render, redirect
from django.contrib import messages  # optional, for user feedback
from django.utils.dateparse import parse_date  # parses 'YYYY-MM-DD'
from .models import Classroom,Reservation

def rooms(request):
    ctx = {}
    # login check
    user_id = request.session.get("user_id")
    
    if user_id is None:
        return redirect('login')
    else:
        reserved_rooms = Reservation.objects.filter(user=user_id).values_list("roomnumber", flat=True)

        # exclude those reserved rooms from each query
        ctx = {}
        ctx["smallclassroom"] = list(
            Classroom.objects.filter(roomsize="s")
            .exclude(roomnumber__in=reserved_rooms)
            .values_list("roomnumber", flat=True)
        )
        ctx["mediumclassroom"] = list(
            Classroom.objects.filter(roomsize="m")
            .exclude(roomnumber__in=reserved_rooms)
            .values_list("roomnumber", flat=True)
        )
        ctx["largeclassroom"] = list(
            Classroom.objects.filter(roomsize="l")
            .exclude(roomnumber__in=reserved_rooms)
            .values_list("roomnumber", flat=True)
        )

    if request.method == "POST":
        submit_type   = request.POST.get("submit_type") or ""
        button_type   = request.POST.get("button_type") or ""
        rawdate       = (request.POST.get("date") or "").strip()
        classroomnumber = (request.POST.get("classroom") or "").strip()
        timeselected  = (request.POST.get("time") or "").strip()

        # Keep values in context so the template can re-open the right popup
        ctx["date"] = rawdate
        ctx["classroom"] = classroomnumber

        # When user asks for time slots
        if button_type in ("small_time_search", "medium_time_search", "large_time_search"):
            chosen = parse_date(rawdate)
            if not chosen or not classroomnumber:
                return render(request, "rooms.html", ctx)

            # seek start time ans stop time
            st_time = Classroom.objects.filter(roomnumber=classroomnumber)\
                .values_list("start_time", flat=True).first()

            stp_time = Classroom.objects.filter(roomnumber=classroomnumber)\
                .values_list("stop_time", flat=True).first()

            # Convert to int 
            st_time = int(st_time)
            stp_time = int(stp_time)
            # reserved list for that room/date
            times = Reservation.objects.filter(
                roomnumber=classroomnumber,
                date=rawdate
            ).values_list("time", flat=True)
            
            alltime = [str(i) for i in range(st_time, stp_time+1)]
            remaintime = [n for n in alltime if n not in set(times)]

            if button_type == "small_time_search":
                ctx["s_times"] = remaintime
            if button_type == "medium_time_search":
                ctx["m_times"] = remaintime
            if button_type == "large_time_search":
                ctx["l_times"] = remaintime

            return render(request, "rooms.html", ctx)

        # Final submit (create reservation)
        if submit_type in ("small_submit", "medium_submit", "large_submit"):
            roomsize = {"small_submit": "s", "medium_submit": "m", "large_submit": "l"}[submit_type]
            if not (user_id and rawdate and classroomnumber and timeselected):
                # Missing something; just re-render so user can try again
                return render(request, "rooms.html", ctx)

            Reservation.objects.create(
                user=user_id,
                roomnumber=classroomnumber,
                roomsize=roomsize,
                time=timeselected,
                date=rawdate,
            )
            # after success you can redirect or re-render
            return redirect("rooms")

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
    reservations = (
        Reservation.objects
        .filter(user=str(user_id))
        .order_by("date", "time", "roomsize", "roomnumber")
    )

    ctx = {"reservations": reservations}
    return render(request, "my_reservations.html", ctx)
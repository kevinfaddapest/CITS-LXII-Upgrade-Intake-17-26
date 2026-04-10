# views.py
import csv
import os
import shutil
from collections import OrderedDict
from datetime import datetime
from django.conf import settings
from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.sessions.models import Session
from django.db.models import Sum
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from openpyxl import Workbook
import traceback
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from .models import Contribution, Case, Rank, Expenditure, UserActivity, AuditLog
from .forms import ContributionForm, CaseForm, RankForm, BootstrapRegisterForm, BootstrapLoginForm
from .utils.audit_logger import log_audit
from django.utils.timezone import now
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

User = get_user_model()
def public_home(request):
    return render(request, 'public_home.html')

# ---------------------- AUTHENTICATION ----------------------
def register(request):
    user_exists = User.objects.exists()
    if user_exists and (not request.user.is_authenticated or not request.user.is_superuser):
        return redirect('permission_denied')
    if request.method == 'POST':
        form = BootstrapRegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if not user_exists:
                user.is_superuser = True
                user.is_staff = True
            user.save()
            actor = request.user if request.user.is_authenticated else user
            log_activity(actor, 'register', 'User', user.id, f"Registered new user: {user.username}")
            if not user_exists:
                login(request, user)
                messages.success(request, 'Administrator account created and logged in.')
            else:
                messages.success(request, 'User registered successfully.')
            return redirect('home')
    else:
        form = BootstrapRegisterForm()
    return render(request, 'register.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = BootstrapLoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        log_activity(user, 'login', 'User', user.id, 'User logged in')
        return redirect('home')
    return render(request, 'login.html', {'form': form})

@login_required
def logout_view(request):
    log_activity(request.user, 'logout', 'User', request.user.id, 'User logged out')
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('public_home')

def permission_denied(request):
    return render(request, 'permission_denied.html')

# ---------------------- UTILITY FUNCTIONS ----------------------
def log_activity(user, action, model_name, object_id=None, description=""):
    UserActivity.objects.create(
        user=user,
        action=action,
        model_name=model_name,
        object_id=str(object_id) if object_id else None,
        description=description
    )

def is_admin(user):
    return user.is_superuser

# ---------------------- AUDIT & ACTIVITY ----------------------
@login_required
@user_passes_test(lambda u: u.is_superuser)
def audit_log_view(request):
    logs = AuditLog.objects.select_related('user').order_by('-timestamp')[:200]
    return render(request, 'audit_log.html', {'logs': logs})

@login_required
def my_activity_view(request):
    logs = UserActivity.objects.filter(user=request.user).order_by('-timestamp')
    paginator = Paginator(logs, 20)
    page = request.GET.get('page')
    logs = paginator.get_page(page)
    return render(request, 'my_activity.html', {'logs': logs})

def ranks_api(request):
    ranks = Rank.objects.all().values('id','rank_name')
    return JsonResponse({'data': list(ranks)})

@staff_member_required
def daily_updates(request):
    today = now().date()
    activities = UserActivity.objects.filter(timestamp__date=today).select_related('user').order_by('-timestamp')
    return render(request, 'daily_updates.html', {'activities': activities})

@staff_member_required
def activity_log_view(request):
    activities = UserActivity.objects.all().order_by('-timestamp')
    return render(request, 'activity_log.html', {'activities': activities})

@receiver(user_logged_in)
def log_user_login(sender, request, user, **kwargs):
    UserActivity.objects.create(user=user, action="login", model_name='User', object_id=user.id, description='User logged in', timestamp=now())

@receiver(user_logged_out)
def log_user_logout(sender, request, user, **kwargs):
    if user:
        UserActivity.objects.create(user=user, action="logout", model_name='User', object_id=user.id, description='User logged out', timestamp=now())

# ---------------------- USER MANAGEMENT ----------------------
@user_passes_test(lambda u: u.is_superuser)
def user_list(request):
    users = User.objects.all()
    return render(request, 'users.html', {'users': users})

@user_passes_test(lambda u: u.is_superuser)
@require_POST
def logout_user(request, user_id):
    sessions = Session.objects.filter(expire_date__gte=now())
    for session in sessions:
        data = session.get_decoded()
        if data.get('_auth_user_id') == str(user_id):
            session.delete()
    return JsonResponse({'status': 'success', 'message': 'User logged out successfully'})

@staff_member_required
def online_users_view(request):
    sessions = Session.objects.filter(expire_date__gte=now())
    uid_list = [s.get_decoded().get('_auth_user_id') for s in sessions if s.get_decoded().get('_auth_user_id')]
    users = User.objects.filter(id__in=uid_list)
    active_users = [{'id': u.id, 'username': u.username, 'last_seen': u.last_login} for u in users]
    return render(request, 'online_users.html', {'active_users': active_users})

@staff_member_required
@require_POST
def force_logout(request):
    user_id = request.POST.get('user_id')
    sessions = Session.objects.filter(expire_date__gte=now())
    count = 0
    for session in sessions:
        data = session.get_decoded()
        if str(data.get('_auth_user_id')) == str(user_id):
            session.delete()
            count += 1
    try:
        target_user = User.objects.get(id=user_id)
        log_activity(request.user, 'force_logout', 'User', target_user.id, f'Forcefully logged out user: {target_user.username} ({count} sessions)')
    except User.DoesNotExist:
        log_activity(request.user, 'force_logout', 'User', user_id, f'Attempted force logout on unknown user: {user_id}')
    messages.success(request, f"User forcibly logged out ({count} session(s) ended).")
    return redirect('online_users')

# ---------------------- DASHBOARD ----------------------

@login_required
def home(request):
    UserActivity.objects.create(
        user=request.user,
        action='view',
        model_name='Contribution',
        object_id=0,
        description='Visited Home page'
    )

    contributions = Contribution.objects.select_related('rank','case').order_by('names')
    unique_contributors = list(OrderedDict((c.names, c) for c in contributions).values())
    total = contributions.aggregate(Sum('contribution'))['contribution__sum'] or 0

    if request.method == 'POST':
        c_form = ContributionForm(request.POST)
        c_form.fields['case'].queryset = Case.objects.all().order_by('-date_reported')

        if c_form.is_valid():
            new_contribution = c_form.save()
            log_activity(
                request.user,
                'create',
                'Contribution',
                new_contribution.id,
                f"Created contribution: {new_contribution.names}, amount: {new_contribution.contribution}"
            )
            messages.success(request, "Contribution submitted successfully.")
            return redirect('home')
    else:
        c_form = ContributionForm()
        c_form.fields['case'].queryset = Case.objects.all().order_by('-date_reported')

    users = User.objects.all() if request.user.is_superuser else []

    # 🔥 ADD THIS LINE
    ranks = Rank.objects.all()

    context = {
        'contributions': unique_contributors,
        'total': total,
        'contribution_form': c_form,
        'case_form': CaseForm(),
        'rank_form': RankForm(),
        'users': users,
        'ranks': ranks   # ✅ FIX HERE
    }

    return render(request, 'home.html', context)

# ---------------------- CASE CRUD ----------------------
@login_required
def view_cases(request):
    cases = Case.objects.all().order_by('-date_reported')
    return render(request, 'view_cases.html', {'cases': cases})

@login_required
@csrf_exempt
def add_case(request):
    if request.method == 'POST':
        form = CaseForm(request.POST)
        if form.is_valid():
            case = form.save()
            log_activity(request.user, 'create', 'Case', case.id, f"Added case: {case.bereaved_member_name} ({case.relation})")
            messages.success(request, "Case added successfully.")
            return redirect('home')
    else:
        form = CaseForm()
    return render(request, 'add_case.html', {'form': form})

@login_required
@csrf_exempt
def update_case(request):
    if request.method == 'POST':
        case_id = request.POST.get('id')
        case = get_object_or_404(Case, pk=case_id)
        case.bereaved_member_name = request.POST.get('bereaved_member_name')
        case.relation = request.POST.get('relation')
        date_str = request.POST.get('date_reported')
        if date_str:
            case.date_reported = datetime.strptime(date_str, "%Y-%m-%dT%H:%M")
        case.save()
        log_activity(request.user, 'update', 'Case', case.id, f"Updated case: {case.bereaved_member_name} ({case.relation})")
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@login_required
@csrf_exempt
def delete_case(request, pk):
    if request.method == 'POST':
        case = get_object_or_404(Case, pk=pk)
        description = f"Deleted case: {case.bereaved_member_name} ({case.relation})"
        case.delete()
        log_activity(request.user, 'delete', 'Case', pk, description)
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

@login_required
def edit_case(request, pk):
    case = get_object_or_404(Case, pk=pk)
    if request.method == 'POST':
        form = CaseForm(request.POST, instance=case)
        if form.is_valid():
            form.save()
            log_activity(request.user, 'update', 'Case', case.id, f"Edited case: {case.bereaved_member_name} ({case.relation})")
            messages.success(request, "Case updated successfully.")
            return redirect('view_cases')
    else:
        form = CaseForm(instance=case)
    return render(request, 'edit_case.html', {'form': form, 'case': case})

# ---------------------- RANK ----------------------
@login_required
def view_ranks(request):
    ranks = Rank.objects.all()
    return render(request, 'view_ranks.html', {'ranks': ranks})

@login_required
def add_rank(request):
    if request.method == 'POST':
        form = RankForm(request.POST)
        if form.is_valid():
            rank = form.save()
            log_activity(request.user, 'create', 'Rank', rank.id, f"Added rank: {rank.rank_name}")
            messages.success(request, "Rank added successfully.")
            return redirect('home')
    else:
        form = RankForm()
    return render(request, 'add_rank.html', {'form': form})


# ---------------------- CONTRIBUTIONS ----------------------
@csrf_exempt
def add_or_update_contribution(request):
    if request.method == "POST":
        cid = request.POST.get("contribution_id")
        case_id = request.POST.get("case_id")
        names = request.POST.get("names")
        rank = request.POST.get("rank")
        amount = request.POST.get("contribution")
        try:
            case = Case.objects.get(id=case_id)
            if cid:  # Update
                contrib = Contribution.objects.get(id=cid)
                contrib.names = names
                contrib.rank_id = rank
                contrib.contribution = amount
                contrib.save()
            else:    # Add
                Contribution.objects.create(
                    case=case,
                    names=names,
                    rank_id=rank,
                    contribution=amount
                )
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    return JsonResponse({"status": "error", "message": "Invalid request"})

def case_contributions_api(request, case_id):
    contributions = Contribution.objects.filter(case_id=case_id)
    data = [
        {
            "id": c.id,
            "names": c.names,
            "rank_name": c.rank.rank_name if c.rank else "",
            "rank_id": c.rank.id if c.rank else "",
            "contribution": float(c.contribution),
            "date": c.date_of_contribution.strftime("%Y-%m-%d"),
            "contact": c.contact
        } for c in contributions
    ]
    return JsonResponse({"data": data})

# ---------------------- EXPENDITURES ----------------------

@login_required
def view_expenditures(request):
    expenditures = Expenditure.objects.select_related("case").all().order_by("-date")
    total = expenditures.aggregate(Sum("amount"))["amount__sum"] or 0
    return render(request, "view_expenditures.html", {
        "expenditures": expenditures,
        "total": total
    })
@csrf_exempt
def add_or_update_expenditure(request):
    if request.method == "POST":
        eid = request.POST.get("expenditure_id")
        case_id = request.POST.get("case_id")
        desc = request.POST.get("description")
        handled_by = request.POST.get("handled_by") or request.user.username
        amount = request.POST.get("amount")
        try:
            amount = float(amount)
            case = Case.objects.get(id=case_id)
            if eid:
                exp = Expenditure.objects.get(id=eid)
                exp.description = desc
                exp.handled_by = handled_by
                exp.amount = amount
                exp.save()
            else:
                Expenditure.objects.create(
                    case=case,
                    description=desc,
                    handled_by=handled_by,
                    amount=amount
                )
            return JsonResponse({"status": "success"})
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})
    return JsonResponse({"status": "error", "message": "Invalid request"})

@csrf_exempt
def delete_expenditure(request, expenditure_id):
    if request.method == "POST":
        try:
            Expenditure.objects.get(id=expenditure_id).delete()
            return JsonResponse({"status": "success"})
        except Expenditure.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Not found"})
    return JsonResponse({"status": "error", "message": "Invalid request"})

def case_expenditures_api(request, case_id):
    expenditures = Expenditure.objects.filter(case_id=case_id)
    data = [
        {
            "id": e.id,
            "description": e.description,
            "handled_by": e.handled_by,
            "date": e.date.strftime("%Y-%m-%d"),
            "amount": float(e.amount)
        } for e in expenditures
    ]
    return JsonResponse({"data": data})


@login_required
def export_contributions(request, format='excel'):
    contributions = Contribution.objects.select_related('case','rank').all().order_by('case')
    total_contribution = sum(c.contribution for c in contributions)

    # CSV Export
    if format.lower() == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="contributions_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Case', 'Names', 'Rank', 'Contribution', 'Date'])
        for c in contributions:
            writer.writerow([c.case.bereaved_member_name, c.names, c.rank.rank_name if c.rank else '', c.contribution, c.date.strftime('%Y-%m-%d')])
        writer.writerow([])
        writer.writerow(['', '', 'Total', total_contribution])
        log_activity(request.user, 'export', 'Contribution', 0, 'Exported contributions CSV')
        return response

    # Excel Export
    elif format.lower() == 'excel':
        wb = Workbook()
        ws = wb.active
        ws.title = "Contributions"
        ws.append(['Case', 'Names', 'Rank', 'Contribution', 'Date'])
        for c in contributions:
            ws.append([c.case.bereaved_member_name, c.names, c.rank.rank_name if c.rank else '', c.contribution, c.date.strftime('%Y-%m-%d')])
        ws.append([])
        ws.append(['', '', 'Total', total_contribution])
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="contributions_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx"'
        wb.save(response)
        log_activity(request.user, 'export', 'Contribution', 0, 'Exported contributions Excel')
        return response

    # PDF Export
    elif format.lower() == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="contributions_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf"'
        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter
        y = height - 50
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Contributions Report")
        y -= 30
        p.setFont("Helvetica", 10)
        p.drawString(50, y, "Case")
        p.drawString(200, y, "Names")
        p.drawString(350, y, "Rank")
        p.drawString(450, y, "Contribution")
        p.drawString(520, y, "Date")
        y -= 20
        for c in contributions:
            if y < 50:
                p.showPage()
                y = height - 50
            p.drawString(50, y, str(c.case.bereaved_member_name))
            p.drawString(200, y, str(c.names))
            p.drawString(350, y, str(c.rank.rank_name if c.rank else ''))
            p.drawString(450, y, str(c.contribution))
            p.drawString(520, y, c.date.strftime('%Y-%m-%d'))
            y -= 20
        y -= 10
        p.drawString(350, y, "Total")
        p.drawString(450, y, str(total_contribution))
        p.showPage()
        p.save()
        log_activity(request.user, 'export', 'Contribution', 0, 'Exported contributions PDF')
        return response

    else:
        messages.error(request, "Invalid export format")
        return redirect('home')


@login_required
def export_expenditures(request, format='excel', case_id=None):
    expenditures = Expenditure.objects.all().order_by('date') if not case_id else get_object_or_404(Case, pk=case_id).expenditures.all().order_by('date')
    total_amount = sum(e.amount for e in expenditures)

    # CSV Export
    if format.lower() == 'csv':
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="expenditures_{datetime.now().strftime("%Y%m%d%H%M%S")}.csv"'
        writer = csv.writer(response)
        writer.writerow(['Case', 'Description', 'Amount', 'Handled By', 'Date'])
        for e in expenditures:
            writer.writerow([e.case.bereaved_member_name if e.case else '', e.description, e.amount, e.handled_by, e.date.strftime('%Y-%m-%d')])
        writer.writerow([])
        writer.writerow(['', 'Total', total_amount])
        return response

    # Excel Export
    elif format.lower() == 'excel':
        wb = Workbook()
        ws = wb.active
        ws.title = "Expenditures"
        ws.append(['Case', 'Description', 'Amount', 'Handled By', 'Date'])
        for e in expenditures:
            ws.append([e.case.bereaved_member_name if e.case else '', e.description, e.amount, e.handled_by, e.date.strftime('%Y-%m-%d')])
        ws.append([])
        ws.append(['', 'Total', total_amount])
        response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
        response['Content-Disposition'] = f'attachment; filename="expenditures_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx"'
        wb.save(response)
        return response

    # PDF Export
    elif format.lower() == 'pdf':
        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="expenditures_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf"'
        p = canvas.Canvas(response, pagesize=letter)
        width, height = letter
        y = height - 50
        p.setFont("Helvetica-Bold", 12)
        p.drawString(50, y, "Expenditures Report")
        y -= 30
        p.setFont("Helvetica", 10)
        p.drawString(50, y, "Case")
        p.drawString(200, y, "Description")
        p.drawString(350, y, "Amount")
        p.drawString(450, y, "Handled By")
        p.drawString(520, y, "Date")
        y -= 20
        for e in expenditures:
            if y < 50:
                p.showPage()
                y = height - 50
            p.drawString(50, y, str(e.case.bereaved_member_name if e.case else ''))
            p.drawString(200, y, str(e.description))
            p.drawString(350, y, str(e.amount))
            p.drawString(450, y, str(e.handled_by))
            p.drawString(520, y, e.date.strftime('%Y-%m-%d'))
            y -= 20
        y -= 10
        p.drawString(350, y, "Total")
        p.drawString(450, y, str(total_amount))
        p.showPage()
        p.save()
        return response

    else:
        return redirect('view_expenditures')


@login_required
def contribution_details(request, contribution_id):
    contribution = get_object_or_404(Contribution, id=contribution_id)
    return render(request, 'contribution_details.html', {'contribution': contribution})


@csrf_exempt
@login_required
def member_contributions(request, member_name):
    # Log the view activity
    UserActivity.objects.create(
        user=request.user,
        action='view',
        model_name='Contribution',
        object_id=0,  # 0 or None because multiple objects viewed
        description=f"Viewed contributions for member: {member_name}"
    )

    contributions = Contribution.objects.filter(names=member_name)
    data = []
    for c in contributions:
        data.append({
            'id': c.id,
            'case': c.case.case_name,
            'contribution': str(c.contribution),
            'date': c.date_of_contribution.strftime('%Y-%m-%d %H:%M'),
            'contact': c.contact,
        })
    return JsonResponse({'status': 'success', 'data': data})


@csrf_exempt
@login_required
def member_contributions_api(request, member_name):
    contributions = Contribution.objects.filter(names=member_name).select_related('case', 'rank')
    data = [
        {
            'id': c.id,  # <-- Important: send id here
            'case': f"{c.case.bereaved_member_name} ({c.case.relation})",
            'rank': c.rank.rank_name,
            'contribution': str(c.contribution),
            'date': c.date_of_contribution.strftime('%Y-%m-%d %H:%M'),
            'contact': c.contact
        }
        for c in contributions
    ]
    return JsonResponse({'status': 'success', 'data': data})

@csrf_exempt
@login_required
def update_contribution(request, pk):
    if request.method == 'POST':
        try:
            contribution = get_object_or_404(Contribution, pk=pk)
            contribution.contribution = request.POST.get('contribution')
            contribution.date_of_contribution = request.POST.get('date')  # Should parse date if needed
            contribution.contact = request.POST.get('contact')
            contribution.save()

            # ✅ Log the update
            UserActivity.objects.create(
                user=request.user,
                action='update',
                model_name='Contribution',
                object_id=contribution.id,
                description=f"Updated contribution: {contribution.names}, amount: {contribution.contribution}"
            )

            return JsonResponse({'status': 'success', 'message': 'Contribution updated successfully.'})
        except Contribution.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Contribution not found.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
@login_required
def delete_contribution(request, pk):
    if request.method == 'POST':
        try:
            contribution = get_object_or_404(Contribution, pk=pk)
            contribution.delete()
            
            UserActivity.objects.create(
    user=request.user,
    action='delete',
    model_name='Contribution',
    object_id=contribution.id,
    description=f"Deleted contribution for {contribution.names}, amount: {contribution.contribution}"
)
            return JsonResponse({'status': 'success', 'message': 'Contribution deleted successfully.'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})

@csrf_exempt
@login_required
def delete_main_contribution(request, contribution_id):
    if request.method == "POST":
        try:
            contribution = Contribution.objects.get(id=contribution_id)

            # store values before delete
            names = contribution.names
            amount = contribution.contribution
            obj_id = contribution.id

            contribution.delete()

            # activity log
            UserActivity.objects.create(
                user=request.user,
                action='delete',
                model_name='Contribution',
                object_id=obj_id,
                description=f"Deleted main contribution for {names}, amount: {amount}"
            )

            return JsonResponse({"status": "success"})

        except Contribution.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Not found"})
            
    return JsonResponse({"status": "error", "message": "Invalid request"})

@login_required
@require_POST
def edit_main_contribution(request, id):
    if not request.user.is_superuser:
        return JsonResponse({
            "status": "error",
            "message": "Unauthorized access."
        })

    contribution = get_object_or_404(Contribution, id=id)

    contribution.rank_id = request.POST.get("rank")
    contribution.names = request.POST.get("names")
    contribution.contact = request.POST.get("contact")
    contribution.save()

    return JsonResponse({
        "status": "success",
        "message": "Contribution updated successfully."
    })
# ---------------------- BACKUP ----------------------

@login_required
def backup_system(request):
    try:
        backup_root = 'D:/LyamaDBMS'
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        full_path = os.path.join(backup_root, f'Lyama_UPDF_Comrades_{timestamp}')
        os.makedirs(full_path, exist_ok=True)

        shutil.copy2(
            os.path.join(settings.BASE_DIR, 'db.sqlite3'),
            os.path.join(full_path, 'db.sqlite3')
        )

        backup_subfolder = os.path.join(full_path, 'files_backup')
        shutil.copytree(
            settings.BASE_DIR,
            backup_subfolder,
            ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '*.log', 'venv', 'node_modules', 'db.sqlite3')
        )

        UserActivity.objects.create(
            user=request.user,
            action='backup',
            model_name='System',
            object_id=0,
            description=f"System backup created at {full_path}"
        )

        return JsonResponse({'status': 'success', 'message': f'System backup was completed successfully.'})
    except Exception as e:
        print(traceback.format_exc())
        return JsonResponse({'status': 'error', 'message': f'Backup failed: {str(e)}'})

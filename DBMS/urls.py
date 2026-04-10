from django.urls import path
from . import views

urlpatterns = [
    # ---------------------- AUTH ----------------------
    path('register/', views.register, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('permission-denied/', views.permission_denied, name='permission_denied'),

    # ---------------------- DASHBOARD ----------------------
     path('', views.public_home, name='public_home'),
    path('home/', views.home, name='home'),

    # ---------------------- CONTRIBUTIONS ----------------------
    path('export/contributions/<str:format>/', views.export_contributions, name='export_contributions'),
    path('contribution/add_or_update/', views.add_or_update_contribution, name='add_or_update_contribution'),
    path('contribution/<int:contribution_id>/delete/', views.delete_contribution, name='delete_contribution'),
    path('edit_main_contribution/<int:id>/', views.edit_main_contribution, name='edit_main_contribution'),


# Contribution management
    path('member_contributions_api/<str:member_name>/', views.member_contributions_api, name='member_contributions_api'),
    path('update_contribution/<int:pk>/', views.update_contribution, name='update_contribution'),
    path('delete_contribution/<int:pk>/', views.delete_contribution, name='delete_contribution'),
    path('delete_main_contribution/<int:pk>/', views.delete_main_contribution, name='delete_main_contribution'),


    # ---------------------- CASES ----------------------
    path('cases/', views.view_cases, name='view_cases'),
    path('cases/add/', views.add_case, name='add_case'),
    path('cases/edit/<int:pk>/', views.edit_case, name='edit_case'),
    path('cases/update/', views.update_case, name='update_case'),
    path('cases/delete/<int:pk>/', views.delete_case, name='delete_case'),
    path('cases/<int:case_id>/contributions/', views.case_contributions_api, name='case_contributions_api'),
    path('cases/<int:case_id>/expenditures/', views.case_expenditures_api, name='case_expenditures_api'),

    # ---------------------- RANKS ----------------------
    path('ranks/', views.view_ranks, name='view_ranks'),
    path('ranks/add/', views.add_rank, name='add_rank'),
    path('api/ranks/', views.ranks_api, name='ranks_api'),

    # ---------------------- EXPENDITURES ----------------------
    path('expenditures/', views.view_expenditures, name='view_expenditures'),
    path('expenditures/<int:case_id>/', views.view_expenditures, name='view_expenditures_case'),
    path('expenditure/add_or_update/', views.add_or_update_expenditure, name='add_or_update_expenditure'),
    path('expenditure/<int:expenditure_id>/delete/', views.delete_expenditure, name='delete_expenditure'),
    path('export/expenditures/<str:format>/', views.export_expenditures, name='export_expenditures'),
    path('export/expenditures/<str:format>/<int:case_id>/', views.export_expenditures, name='export_expenditures_case'),

    # ---------------------- USERS ----------------------
    path('users/', views.user_list, name='user_list'),
    path('users/logout/<int:user_id>/', views.logout_user, name='logout_user'),
    path('users/online/', views.online_users_view, name='online_users'),
    path('users/force-logout/', views.force_logout, name='force_logout'),

    # ---------------------- AUDIT & ACTIVITY ----------------------
    path('audit-log/', views.audit_log_view, name='audit_log'),
    path('my-activity/', views.my_activity_view, name='my_activity'),
    path('activity-log/', views.activity_log_view, name='activity_log'),
    path('daily-updates/', views.daily_updates, name='daily_updates'),

    # ---------------------- BACKUP ----------------------
    path('backup/', views.backup_system, name='backup_system'),
]

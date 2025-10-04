from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.ReportListView.as_view(), name='list'),
    path('<int:pk>/', views.ReportDetailView.as_view(), name='detail'),
    path('<int:pk>/download/', views.ReportDownloadView.as_view(), name='download'),
    path('<int:pk>/email/', views.ReportEmailView.as_view(), name='email'),
    path('<int:pk>/delete/', views.ReportDeleteView.as_view(), name='delete'),
    path('generate/<int:comparison_id>/', views.ReportGenerateView.as_view(), name='generate'),
    path('templates/', views.ReportTemplateListView.as_view(), name='templates'),
    path('bulk-delete/', views.ReportBulkDeleteView.as_view(), name='bulk_delete'),
]

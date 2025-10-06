from django.urls import path
from . import views

app_name = 'documents'

urlpatterns = [
    path('', views.DocumentListView.as_view(), name='list'),
    path('upload/', views.DocumentUploadView.as_view(), name='upload'),
    path('<int:pk>/', views.DocumentDetailView.as_view(), name='detail'),
    path('<int:pk>/parse/', views.DocumentParseView.as_view(), name='parse'),
    path('<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='delete'),
    path('<int:pk>/rename/', views.DocumentRenameView.as_view(), name='rename'),
    path('<int:pk>/version/upload/', views.DocumentVersionUploadView.as_view(), name='version_upload'),
    path('<int:pk>/version/delete/', views.DocumentVersionDeleteView.as_view(), name='version_delete'),
    path('<int:pk>/versions/', views.DocumentVersionHistoryView.as_view(), name='version_history'),
    path('bulk-delete/', views.DocumentBulkDeleteView.as_view(), name='bulk_delete'),
    path('versions/bulk-delete/', views.DocumentVersionBulkDeleteView.as_view(), name='version_bulk_delete'),
    path('<int:pk>/generate-key-points/', views.DocumentGenerateKeyPointsView.as_view(), name='generate_key_points'),
    path('<int:pk>/generate-key-points-test/', views.DocumentGenerateKeyPointsTestView.as_view(), name='generate_key_points_test'),
    path('<int:pk>/analyze-tables/', views.DocumentAnalyzeTablesView.as_view(), name='analyze_tables'),
]

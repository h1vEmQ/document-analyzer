from django.urls import path
from . import views

app_name = 'analysis'

urlpatterns = [
    path('', views.ComparisonListView.as_view(), name='list'),
    path('create/', views.ComparisonCreateView.as_view(), name='create'),
    path('<int:pk>/', views.ComparisonDetailView.as_view(), name='detail'),
    path('<int:pk>/run/', views.ComparisonRunView.as_view(), name='run'),
    path('<int:pk>/delete/', views.ComparisonDeleteView.as_view(), name='delete'),
    path('settings/', views.AnalysisSettingsView.as_view(), name='settings'),
    path('bulk-delete/', views.ComparisonBulkDeleteView.as_view(), name='bulk_delete'),
    path('ollama/create/', views.OllamaComparisonCreateView.as_view(), name='ollama_create'),
    path('ollama/<int:pk>/', views.OllamaComparisonDetailView.as_view(), name='ollama_detail'),
    path('ollama/status/', views.OllamaStatusView.as_view(), name='ollama_status'),
]

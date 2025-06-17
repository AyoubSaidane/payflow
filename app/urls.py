from django.urls import path
from . import views

app_name = 'conventions'

urlpatterns = [
    # Dashboard principal
    path('', views.dashboard, name='dashboard'),
    
    # ============================================================================
    # GESTION DES CONVENTIONS COLLECTIVES
    # ============================================================================
    
    # Liste et gestion des conventions
    path('conventions/', views.convention_list, name='convention-list'),
    path('conventions/<uuid:convention_id>/', views.convention_detail, name='convention-detail'),
    path('conventions/import/', views.convention_import, name='convention-import'),
    
    # ============================================================================
    # ANALYSES DE PAIE
    # ============================================================================
    
    # Création et gestion des analyses
    path('conventions/<uuid:convention_id>/analyse/create/', views.analyse_create, name='analyse-create'),
    path('analyses/<uuid:analyse_id>/', views.analyse_detail, name='analyse-detail'),
    path('analyses/<uuid:analyse_id>/logs/', views.analyse_logs, name='analyse-logs'),
    path('analyses/<uuid:analyse_id>/export/', views.export_analysis, name='analyse-export'),
    
    # ============================================================================
    # MONITORING EN TEMPS RÉEL
    # ============================================================================
    
    # Interface de monitoring
    path('monitoring/', views.monitoring_dashboard, name='monitoring-dashboard'),
    
    # API monitoring
    path('api/monitoring/events/', views.api_monitoring_events, name='api-monitoring-events'),
    path('api/monitoring/sessions/', views.api_monitoring_sessions, name='api-monitoring-sessions'),
    path('api/monitoring/sessions/<str:session_id>/', views.api_monitoring_session_details, name='api-monitoring-session-details'),
    path('api/monitoring/stream/', views.api_monitoring_stream, name='api-monitoring-stream'),
    
    # ============================================================================
    # API ENDPOINTS AJAX
    # ============================================================================
    
    # API pour analyses rapides
    path('api/quick-analysis/', views.api_quick_analysis, name='api-quick-analysis'),
    
    # API pour graphiques Highcharts
    path('api/analyses/<uuid:analyse_id>/charts/<str:chart_type>/', 
         views.api_chart_config, name='api-chart-config'),
    
    # API pour données live
    path('api/analyses/<uuid:analyse_id>/live-data/', 
         views.api_live_data, name='api-live-data'),
    
    # API pour régénération de graphiques
    path('api/analyses/<uuid:analyse_id>/regenerate/<str:chart_type>/', 
         views.api_regenerate_chart, name='api-regenerate-chart'),
    
    # API pour recherche d'articles
    path('api/conventions/<uuid:convention_id>/search-articles/', 
         views.api_search_articles, name='api-search-articles'),
]
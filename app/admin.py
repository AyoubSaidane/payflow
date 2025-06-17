from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import Convention, AnalysePaie, VariablePaie, GraphiquePaie, LogAnalyse


@admin.register(Convention)
class ConventionAdmin(admin.ModelAdmin):
    """Interface d'administration pour les conventions collectives"""
    
    list_display = ['title', 'cc_id', 'imported_by', 'articles_count', 'status', 'date_import']
    list_filter = ['status', 'date_import', 'imported_by']
    search_fields = ['title', 'cc_id', 'description']
    readonly_fields = ['id', 'date_import', 'articles_count']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('id', 'cc_id', 'title', 'description')
        }),
        ('Import', {
            'fields': ('imported_by', 'date_import', 'status', 'articles_count')
        }),
        ('Données brutes', {
            'fields': ('formatted_raw_data',),
            'classes': ('collapse',)
        })
    )
    
    def formatted_raw_data(self, obj):
        """Affiche les données brutes formatées"""
        if obj.raw_data:
            formatted_json = json.dumps(obj.raw_data, indent=2, ensure_ascii=False)
            return format_html('<pre style="max-height: 300px; overflow-y: auto;">{}</pre>', formatted_json)
        return "Aucune donnée"
    formatted_raw_data.short_description = "Données API formatées"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('imported_by')


@admin.register(AnalysePaie)
class AnalysePaieAdmin(admin.ModelAdmin):
    """Interface d'administration pour les analyses de paie"""
    
    list_display = ['convention_title', 'created_by', 'status', 'execution_time', 'variables_count', 'created_at']
    list_filter = ['status', 'created_at', 'created_by', 'convention']
    search_fields = ['prompt_analyse', 'impact_description', 'convention__title']
    readonly_fields = ['id', 'created_at', 'execution_time', 'variables_count', 'graphiques_count']
    
    fieldsets = (
        ('Analyse', {
            'fields': ('id', 'convention', 'prompt_analyse', 'status')
        }),
        ('Résultats', {
            'fields': ('impact_description', 'agent_response', 'execution_time', 'error_message')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'variables_count', 'graphiques_count')
        }),
        ('Données techniques', {
            'fields': ('formatted_variables_detected',),
            'classes': ('collapse',)
        })
    )
    
    def convention_title(self, obj):
        return obj.convention.title
    convention_title.short_description = "Convention"
    convention_title.admin_order_field = 'convention__title'
    
    def variables_count(self, obj):
        return obj.variables.count()
    variables_count.short_description = "Variables"
    
    def graphiques_count(self, obj):
        return obj.graphiques.count()
    graphiques_count.short_description = "Graphiques"
    
    def formatted_variables_detected(self, obj):
        """Affiche les variables détectées formatées"""
        if obj.variables_detected:
            formatted_json = json.dumps(obj.variables_detected, indent=2, ensure_ascii=False)
            return format_html('<pre style="max-height: 300px; overflow-y: auto;">{}</pre>', formatted_json)
        return "Aucune variable détectée"
    formatted_variables_detected.short_description = "Variables détectées (JSON)"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('convention', 'created_by').prefetch_related('variables', 'graphiques')


@admin.register(VariablePaie)
class VariablePaieAdmin(admin.ModelAdmin):
    """Interface d'administration pour les variables de paie"""
    
    list_display = ['name', 'var_type', 'analyse_convention', 'data_type', 'has_dependencies', 'created_at']
    list_filter = ['var_type', 'data_type', 'created_at', 'analyse__convention']
    search_fields = ['name', 'description', 'legal_reference', 'analyse__convention__title']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Variable', {
            'fields': ('id', 'analyse', 'name', 'var_type', 'description')
        }),
        ('Configuration', {
            'fields': ('data_type', 'calculation_formula', 'formatted_depends_on')
        }),
        ('Références', {
            'fields': ('legal_reference', 'article_source')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def analyse_convention(self, obj):
        return f"{obj.analyse.convention.title} - Analyse #{obj.analyse.id}"
    analyse_convention.short_description = "Convention / Analyse"
    analyse_convention.admin_order_field = 'analyse__convention__title'
    
    def has_dependencies(self, obj):
        return bool(obj.depends_on)
    has_dependencies.boolean = True
    has_dependencies.short_description = "Dépendances"
    
    def formatted_depends_on(self, obj):
        """Affiche les dépendances formatées"""
        if obj.depends_on:
            return format_html('<code>{}</code>', ', '.join(obj.depends_on))
        return "Aucune dépendance"
    formatted_depends_on.short_description = "Dépend de"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('analyse__convention')


@admin.register(GraphiquePaie)
class GraphiquePaieAdmin(admin.ModelAdmin):
    """Interface d'administration pour les graphiques de paie"""
    
    list_display = ['title', 'chart_type', 'analyse_convention', 'created_at', 'view_link']
    list_filter = ['chart_type', 'created_at', 'analyse__convention']
    search_fields = ['title', 'description', 'analyse__convention__title']
    readonly_fields = ['id', 'created_at', 'updated_at', 'config_preview']
    
    fieldsets = (
        ('Graphique', {
            'fields': ('id', 'analyse', 'title', 'description', 'chart_type')
        }),
        ('Configuration', {
            'fields': ('config_preview',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at')
        }),
        ('Données techniques', {
            'fields': ('formatted_config', 'formatted_data'),
            'classes': ('collapse',)
        })
    )
    
    def analyse_convention(self, obj):
        return f"{obj.analyse.convention.title} - Analyse #{obj.analyse.id}"
    analyse_convention.short_description = "Convention / Analyse"
    analyse_convention.admin_order_field = 'analyse__convention__title'
    
    def view_link(self, obj):
        """Lien pour voir l'analyse associée"""
        url = reverse('admin:app_analysepaie_change', args=[obj.analyse.id])
        return format_html('<a href="{}" target="_blank">Voir analyse</a>', url)
    view_link.short_description = "Actions"
    
    def config_preview(self, obj):
        """Aperçu de la configuration"""
        if obj.config:
            # Extraire quelques infos clés
            chart_info = []
            if 'chart' in obj.config:
                chart_info.append(f"Type: {obj.config['chart'].get('type', 'N/A')}")
                if 'height' in obj.config['chart']:
                    chart_info.append(f"Hauteur: {obj.config['chart']['height']}px")
            if 'title' in obj.config and 'text' in obj.config['title']:
                chart_info.append(f"Titre: {obj.config['title']['text']}")
            
            return format_html('<ul>{}</ul>', 
                             ''.join(f'<li>{info}</li>' for info in chart_info))
        return "Aucune configuration"
    config_preview.short_description = "Aperçu configuration"
    
    def formatted_config(self, obj):
        """Configuration formatée"""
        if obj.config:
            formatted_json = json.dumps(obj.config, indent=2, ensure_ascii=False)
            return format_html('<pre style="max-height: 400px; overflow-y: auto;">{}</pre>', formatted_json)
        return "Aucune configuration"
    formatted_config.short_description = "Configuration Highcharts"
    
    def formatted_data(self, obj):
        """Données formatées"""
        if obj.data:
            formatted_json = json.dumps(obj.data, indent=2, ensure_ascii=False)
            return format_html('<pre style="max-height: 300px; overflow-y: auto;">{}</pre>', formatted_json)
        return "Aucune donnée"
    formatted_data.short_description = "Données du graphique"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('analyse__convention')


@admin.register(LogAnalyse)
class LogAnalyseAdmin(admin.ModelAdmin):
    """Interface d'administration pour les logs d'analyse"""
    
    list_display = ['analyse_info', 'step', 'level', 'message_preview', 'timestamp']
    list_filter = ['level', 'step', 'timestamp', 'analyse__convention']
    search_fields = ['message', 'step', 'analyse__convention__title']
    readonly_fields = ['id', 'timestamp', 'formatted_extra_data']
    
    fieldsets = (
        ('Log', {
            'fields': ('id', 'analyse', 'step', 'level', 'message', 'timestamp')
        }),
        ('Données supplémentaires', {
            'fields': ('formatted_extra_data',),
            'classes': ('collapse',)
        })
    )
    
    def analyse_info(self, obj):
        return f"{obj.analyse.convention.title} - Analyse #{obj.analyse.id}"
    analyse_info.short_description = "Analyse"
    analyse_info.admin_order_field = 'analyse__convention__title'
    
    def message_preview(self, obj):
        """Aperçu du message"""
        return obj.message[:100] + "..." if len(obj.message) > 100 else obj.message
    message_preview.short_description = "Message"
    
    def formatted_extra_data(self, obj):
        """Données supplémentaires formatées"""
        if obj.extra_data:
            formatted_json = json.dumps(obj.extra_data, indent=2, ensure_ascii=False)
            return format_html('<pre style="max-height: 300px; overflow-y: auto;">{}</pre>', formatted_json)
        return "Aucune donnée supplémentaire"
    formatted_extra_data.short_description = "Données supplémentaires"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('analyse__convention')


# Configuration globale de l'admin
admin.site.site_header = "Administration Variables de Paie"
admin.site.site_title = "Variables de Paie Admin"
admin.site.index_title = "Gestion des Variables de Paie"
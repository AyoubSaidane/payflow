from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.db import transaction
import json
import logging

from .models import Convention, AnalysePaie, VariablePaie, GraphiquePaie, LogAnalyse
from .forms import ConventionImportForm, AnalysePaieForm, VariablePaieForm
from .services import (
    ConventionImportService, PayrollAnalysisService, 
    HighchartsConfigService, LoggingService, GraphIntegrationService
)

logger = logging.getLogger(__name__)


def dashboard(request):
    """Dashboard principal avec statistiques et graphiques"""
    
    # Statistiques générales
    if request.user.is_authenticated:
        conventions_count = Convention.objects.filter(imported_by=request.user).count()
        analyses_count = AnalysePaie.objects.filter(created_by=request.user).count()
        variables_count = VariablePaie.objects.filter(analyse__created_by=request.user).count()
        
        # Dernières analyses
        recent_analyses = AnalysePaie.objects.filter(
            created_by=request.user
        ).select_related('convention').order_by('-created_at')[:5]
        
        # Variables par type pour graphique
        variables_by_type = VariablePaie.objects.filter(
            analyse__created_by=request.user
        ).values('var_type').annotate(count=Count('id'))
        
        # Données pour graphique d'activité (analyses par mois) - Simplifié
        activity_data = []
    else:
        # Données de démonstration pour utilisateur non connecté
        conventions_count = Convention.objects.count()
        analyses_count = AnalysePaie.objects.count()
        variables_count = VariablePaie.objects.count()
        recent_analyses = AnalysePaie.objects.select_related('convention').order_by('-created_at')[:5]
        variables_by_type = VariablePaie.objects.values('var_type').annotate(count=Count('id'))
        activity_data = []
    
    context = {
        'stats': {
            'conventions': conventions_count,
            'analyses': analyses_count,
            'variables': variables_count,
        },
        'recent_analyses': recent_analyses,
        'variables_by_type': list(variables_by_type),
        'activity_data': list(activity_data),
    }
    
    return render(request, 'conventions/dashboard.html', context)


def convention_list(request):
    """Liste des conventions collectives"""
    
    if request.user.is_authenticated:
        conventions = Convention.objects.filter(
            imported_by=request.user
        ).order_by('-date_import')
    else:
        conventions = Convention.objects.all().order_by('-date_import')
    
    # Recherche
    search = request.GET.get('search')
    if search:
        conventions = conventions.filter(
            Q(title__icontains=search) | Q(cc_id__icontains=search)
        )
    
    # Pagination
    paginator = Paginator(conventions, 10)
    page_number = request.GET.get('page')
    conventions_page = paginator.get_page(page_number)
    
    context = {
        'conventions': conventions_page,
        'search': search,
    }
    
    return render(request, 'conventions/convention_list.html', context)


def convention_detail(request, convention_id):
    """Détail d'une convention collective avec ses analyses"""
    
    convention = get_object_or_404(Convention, id=convention_id)
    
    # Analyses liées
    analyses = AnalysePaie.objects.filter(
        convention=convention
    ).order_by('-created_at')
    
    # Statistiques
    total_variables = VariablePaie.objects.filter(
        analyse__convention=convention
    ).count()
    
    variables_by_type = VariablePaie.objects.filter(
        analyse__convention=convention
    ).values('var_type').annotate(count=Count('id'))
    
    context = {
        'convention': convention,
        'analyses': analyses,
        'stats': {
            'total_analyses': analyses.count(),
            'total_variables': total_variables,
            'variables_by_type': list(variables_by_type),
        }
    }
    
    return render(request, 'conventions/convention_detail.html', context)


def convention_import(request):
    """Import d'une nouvelle convention collective"""
    
    if request.method == 'POST':
        form = ConventionImportForm(request.POST)
        if form.is_valid():
            try:
                cc_id = form.cleaned_data['cc_id']
                
                # Vérifier que la convention n'existe pas déjà
                if Convention.objects.filter(cc_id=cc_id).exists():
                    messages.error(request, f"La convention {cc_id} est déjà importée.")
                    return render(request, 'conventions/convention_import.html', {'form': form})
                
                # Importer via le service
                import_data = ConventionImportService.import_convention(cc_id, request.user if request.user.is_authenticated else None)
                
                # Créer l'objet Convention
                convention = Convention.objects.create(
                    cc_id=import_data['cc_id'],
                    title=import_data['title'],
                    description=form.cleaned_data.get('description', ''),
                    imported_by=request.user if request.user.is_authenticated else None,
                    raw_data=import_data['raw_data'],
                    articles_count=import_data['articles_count'],
                    status=import_data['status']
                )
                
                messages.success(
                    request, 
                    f"Convention {convention.title} importée avec succès ({convention.articles_count} articles)."
                )
                return redirect('conventions:convention-detail', convention_id=convention.id)
                
            except Exception as e:
                messages.error(request, f"Erreur lors de l'import: {str(e)}")
    else:
        form = ConventionImportForm()
    
    return render(request, 'conventions/convention_import.html', {'form': form})


def analyse_create(request, convention_id):
    """Création d'une nouvelle analyse de paie"""
    
    convention = get_object_or_404(
        Convention, 
        id=convention_id
    )
    
    if request.method == 'POST':
        form = AnalysePaieForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Créer l'analyse
                    analyse = AnalysePaie.objects.create(
                        convention=convention,
                        prompt_analyse=form.cleaned_data['prompt_analyse'],
                        created_by=request.user if request.user.is_authenticated else None,
                        status='processing'
                    )
                    
                    # Log du début
                    LoggingService.log_analysis_step(
                        str(analyse.id), 
                        'creation', 
                        'Analyse créée et démarrage du traitement'
                    )
                    
                    # Exécuter l'analyse via le service
                    analysis_service = PayrollAnalysisService()
                    
                    # Récupérer les articles de contexte si spécifiés
                    context_articles = None
                    if form.cleaned_data.get('article_ids'):
                        # Filtrer les articles pertinents depuis raw_data
                        article_ids = form.cleaned_data['article_ids'].split(',')
                        all_articles = convention.raw_data.get('articles', [])
                        context_articles = [
                            article for article in all_articles 
                            if str(article.get('id', '')) in article_ids
                        ]
                    
                    result = analysis_service.analyze_payroll_impact(
                        form.cleaned_data['prompt_analyse'],
                        context_articles,
                        user_id=str(request.user.id) if request.user.is_authenticated else None
                    )
                    
                    # Mettre à jour l'analyse avec les résultats
                    analyse.impact_description = result['impact_description']
                    analyse.variables_detected = result['variables_detected']
                    analyse.agent_response = result['agent_response']
                    analyse.execution_time = result['execution_time']
                    analyse.status = result['status']
                    if 'error_message' in result:
                        analyse.error_message = result['error_message']
                    analyse.save()
                    
                    # Créer les variables détectées
                    for var_data in result['variables_detected']:
                        VariablePaie.objects.create(
                            analyse=analyse,
                            name=var_data['name'],
                            var_type=var_data.get('type', 'intermediate'),
                            description=var_data.get('description', ''),
                            data_type=var_data.get('data_type', 'float')
                        )
                    
                    # Générer les graphiques Highcharts
                    if result['status'] == 'completed':
                        charts_service = HighchartsConfigService()
                        variables = result['variables_detected']
                        
                        # Graphique réseau
                        network_config = charts_service.generate_network_graph(
                            variables, str(analyse.id)
                        )
                        GraphiquePaie.objects.create(
                            analyse=analyse,
                            chart_type='networkgraph',
                            title='Graphe des Variables',
                            config=network_config,
                            data={'variables': variables}
                        )
                        
                        # Timeline
                        timeline_config = charts_service.generate_timeline_chart(variables)
                        GraphiquePaie.objects.create(
                            analyse=analyse,
                            chart_type='timeline',
                            title='Timeline des Variables',
                            config=timeline_config,
                            data={'variables': variables}
                        )
                        
                        # Graphique en secteurs
                        pie_config = charts_service.generate_pie_chart(variables)
                        GraphiquePaie.objects.create(
                            analyse=analyse,
                            chart_type='pie',
                            title='Répartition par Type',
                            config=pie_config,
                            data={'variables': variables}
                        )
                    
                    LoggingService.log_analysis_step(
                        str(analyse.id), 
                        'completion', 
                        f'Analyse terminée avec statut: {result["status"]}',
                        level='info' if result['status'] == 'completed' else 'error'
                    )
                    
                    if result['status'] == 'completed':
                        messages.success(
                            request, 
                            f"Analyse terminée avec succès en {result['execution_time']:.2f}s. "
                            f"{len(result['variables_detected'])} variables détectées."
                        )
                    else:
                        messages.warning(
                            request, 
                            f"Analyse terminée avec des erreurs. Consultez les logs pour plus de détails."
                        )
                    
                    return redirect('conventions:analyse-detail', analyse_id=analyse.id)
                    
            except Exception as e:
                logger.error(f"Erreur création analyse: {str(e)}")
                messages.error(request, f"Erreur lors de la création de l'analyse: {str(e)}")
    else:
        form = AnalysePaieForm()
    
    # Exemples de prompts
    example_prompts = [
        "Analyse les primes d'ancienneté dans cette convention",
        "Recherche les indemnités de transport et leurs modalités de calcul",
        "Identifie les heures supplémentaires et leurs majorations",
        "Trouve les primes de fin d'année et leurs conditions d'attribution"
    ]
    
    context = {
        'convention': convention,
        'form': form,
        'example_prompts': example_prompts,
    }
    
    return render(request, 'conventions/analyse_create.html', context)


def analyse_detail(request, analyse_id):
    """Détail d'une analyse avec graphiques interactifs"""
    
    if request.user.is_authenticated:
        analyse = get_object_or_404(
            AnalysePaie, 
            id=analyse_id, 
            created_by=request.user
        )
    else:
        analyse = get_object_or_404(AnalysePaie, id=analyse_id)
    
    # Variables liées
    variables = VariablePaie.objects.filter(analyse=analyse).order_by('var_type', 'name')
    
    # Graphiques
    graphiques = GraphiquePaie.objects.filter(analyse=analyse).order_by('chart_type')
    
    # Logs d'exécution
    logs = LogAnalyse.objects.filter(analyse=analyse).order_by('timestamp')
    
    # Statistiques des variables
    stats = {
        'total': variables.count(),
        'by_type': variables.values('var_type').annotate(count=Count('id'))
    }
    
    context = {
        'analyse': analyse,
        'variables': variables,
        'graphiques': graphiques,
        'logs': logs,
        'stats': stats,
    }
    
    return render(request, 'conventions/analyse_detail.html', context)


# ============================================================================
# API ENDPOINTS AJAX
# ============================================================================

@require_http_methods(["POST"])
def api_quick_analysis(request):
    """API pour analyse rapide via AJAX"""
    
    try:
        data = json.loads(request.body)
        prompt = data.get('prompt', '').strip()
        
        if not prompt:
            return JsonResponse({'error': 'Prompt requis'}, status=400)
        
        # Exécuter l'analyse rapide
        analysis_service = PayrollAnalysisService()
        result = analysis_service.analyze_payroll_impact(prompt)
        
        return JsonResponse({
            'success': True,
            'result': result
        })
        
    except Exception as e:
        logger.error(f"Erreur API analyse rapide: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def api_chart_config(request, analyse_id, chart_type):
    """API pour récupérer la configuration d'un graphique"""
    
    try:
        # Récupérer l'analyse sans filtrage par utilisateur
        if request.user.is_authenticated:
            analyse = get_object_or_404(
                AnalysePaie, 
                id=analyse_id, 
                created_by=request.user
            )
        else:
            analyse = get_object_or_404(AnalysePaie, id=analyse_id)
        
        # Essayer de récupérer le graphique existant
        try:
            graphique = GraphiquePaie.objects.get(
                analyse=analyse,
                chart_type=chart_type
            )
            config = graphique.config
        except GraphiquePaie.DoesNotExist:
            # Si le graphique n'existe pas, le générer depuis NetworkX en temps réel
            try:
                from payroll_variable_agent import payroll_graph
                charts_service = HighchartsConfigService()
                
                if chart_type == 'networkgraph':
                    # Utiliser le graphe NetworkX directement
                    config = charts_service.generate_network_graph_from_networkx(payroll_graph, str(analyse.id))
                else:
                    # Fallback vers les variables Django pour autres types
                    variables = list(VariablePaie.objects.filter(
                        analyse=analyse
                    ).values('name', 'var_type', 'description', 'data_type'))
                    
                    if chart_type == 'timeline':
                        config = charts_service.generate_timeline_chart(variables)
                    elif chart_type == 'pie':
                        config = charts_service.generate_pie_chart(variables)
                    else:
                        return JsonResponse({'error': f'Type de graphique non supporté: {chart_type}'}, status=400)
            
            except ImportError:
                # Fallback si NetworkX non disponible
                variables = list(VariablePaie.objects.filter(
                    analyse=analyse
                ).values('name', 'var_type', 'description', 'data_type'))
                
                charts_service = HighchartsConfigService()
                
                if chart_type == 'networkgraph':
                    config = charts_service.generate_network_graph(variables, str(analyse.id))
                elif chart_type == 'timeline':
                    config = charts_service.generate_timeline_chart(variables)
                elif chart_type == 'pie':
                    config = charts_service.generate_pie_chart(variables)
                else:
                    return JsonResponse({'error': f'Type de graphique non supporté: {chart_type}'}, status=400)
        
        return JsonResponse({
            'success': True,
            'config': config
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def api_live_data(request, analyse_id):
    """API pour données live d'une analyse"""
    
    try:
        analyse = get_object_or_404(
            AnalysePaie, 
            id=analyse_id, 
            created_by=request.user
        )
        
        variables = list(VariablePaie.objects.filter(
            analyse=analyse
        ).values('name', 'var_type', 'description', 'data_type'))
        
        # Utiliser le service d'intégration pour les données live
        graph_service = GraphIntegrationService()
        graph_service.build_networkx_graph(
            variables, 
            analyse.impact_description[:100] + "..."
        )
        live_data = graph_service.get_live_data()
        
        return JsonResponse({
            'success': True,
            'live_data': live_data,
            'variables': variables,
            'analyse_status': analyse.status
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["POST"])
def api_regenerate_chart(request, analyse_id, chart_type):
    """API pour régénérer un graphique"""
    
    try:
        analyse = get_object_or_404(
            AnalysePaie, 
            id=analyse_id, 
            created_by=request.user
        )
        
        variables = list(VariablePaie.objects.filter(
            analyse=analyse
        ).values('name', 'var_type', 'description', 'data_type', 'depends_on'))
        
        # Régénérer la configuration
        charts_service = HighchartsConfigService()
        
        if chart_type == 'networkgraph':
            config = charts_service.generate_network_graph(variables, str(analyse.id))
        elif chart_type == 'timeline':
            config = charts_service.generate_timeline_chart(variables)
        elif chart_type == 'pie':
            config = charts_service.generate_pie_chart(variables)
        else:
            return JsonResponse({'error': f'Type de graphique non supporté: {chart_type}'}, status=400)
        
        # Mettre à jour en base
        graphique, created = GraphiquePaie.objects.get_or_create(
            analyse=analyse,
            chart_type=chart_type,
            defaults={
                'title': f'Graphique {chart_type.title()}',
                'config': config,
                'data': {'variables': variables}
            }
        )
        
        if not created:
            graphique.config = config
            graphique.data = {'variables': variables}
            graphique.save()
        
        return JsonResponse({
            'success': True,
            'config': config,
            'message': f'Graphique {chart_type} régénéré avec succès'
        })
        
    except Exception as e:
        logger.error(f"Erreur régénération graphique: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def api_search_articles(request, convention_id):
    """API pour rechercher des articles dans une convention"""
    
    try:
        if request.user.is_authenticated:
            convention = get_object_or_404(
                Convention, 
                id=convention_id, 
                imported_by=request.user
            )
        else:
            convention = get_object_or_404(Convention, id=convention_id)
        
        search_term = request.GET.get('q', '').strip().lower()
        
        if not search_term:
            return JsonResponse({'articles': []})
        
        articles = convention.raw_data.get('articles', [])
        matching_articles = []
        
        for article in articles:
            content = article.get('content', '').lower()
            title = ' '.join(article.get('pathTitle', [])).lower()
            num = str(article.get('num', '')).lower()
            
            if (search_term in content or 
                search_term in title or 
                search_term in num):
                
                matching_articles.append({
                    'id': article.get('id'),
                    'num': article.get('num'),
                    'title': ' > '.join(article.get('pathTitle', [])),
                    'content_preview': article.get('content', '')[:200] + "..."
                })
        
        return JsonResponse({
            'success': True,
            'articles': matching_articles[:10]  # Limiter à 10 résultats
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# MONITORING EN TEMPS RÉEL
# ============================================================================

def monitoring_dashboard(request):
    """Interface de monitoring des agents en temps réel"""
    from .monitoring import monitor
    
    # Récupérer les sessions actives
    active_sessions = monitor.get_active_sessions()
    
    # Récupérer les événements récents
    recent_events = monitor.get_recent_events(limit=50)
    
    # Statistiques globales
    total_sessions = len(active_sessions)
    total_events = len(monitor.events)
    
    context = {
        'active_sessions': active_sessions,
        'recent_events': recent_events,
        'stats': {
            'total_sessions': total_sessions,
            'total_events': total_events,
            'active_sessions_count': len([s for s in active_sessions.values() if s['status'] == 'active'])
        }
    }
    
    return render(request, 'monitoring/dashboard.html', context)


@require_http_methods(["GET"])
def api_monitoring_events(request):
    """API pour récupérer les événements de monitoring"""
    from .monitoring import monitor
    
    try:
        session_id = request.GET.get('session_id')
        level = request.GET.get('level')
        limit = int(request.GET.get('limit', 100))
        
        events = monitor.get_recent_events(
            limit=limit,
            session_id=session_id,
            level=level
        )
        
        return JsonResponse({
            'success': True,
            'events': events,
            'count': len(events)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_monitoring_sessions(request):
    """API pour récupérer les sessions actives"""
    from .monitoring import monitor
    
    try:
        sessions = monitor.get_active_sessions()
        
        # Ajouter les statistiques pour chaque session
        sessions_with_stats = {}
        for session_id, session_data in sessions.items():
            stats = monitor.get_session_stats(session_id)
            sessions_with_stats[session_id] = {
                **session_data,
                'stats': stats
            }
        
        return JsonResponse({
            'success': True,
            'sessions': sessions_with_stats
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@require_http_methods(["GET"])
def api_monitoring_session_details(request, session_id):
    """API pour récupérer les détails d'une session spécifique"""
    from .monitoring import monitor
    
    try:
        sessions = monitor.get_active_sessions()
        session = sessions.get(session_id)
        
        if not session:
            return JsonResponse({'error': 'Session non trouvée'}, status=404)
        
        # Récupérer les événements de cette session
        events = monitor.get_recent_events(session_id=session_id, limit=500)
        stats = monitor.get_session_stats(session_id)
        
        return JsonResponse({
            'success': True,
            'session': session,
            'events': events,
            'stats': stats
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


from django.http import StreamingHttpResponse
import json

def api_monitoring_stream(request):
    """API Server-Sent Events pour le streaming en temps réel"""
    from .monitoring import monitor
    
    def event_stream():
        # Buffer pour les événements
        last_event_count = len(monitor.events)
        
        # Envoyer les événements existants
        initial_events = monitor.get_recent_events(limit=20)
        for event in initial_events:
            yield f"data: {json.dumps(event)}\n\n"
        
        # Boucle de streaming
        while True:
            try:
                current_count = len(monitor.events)
                
                # Vérifier s'il y a de nouveaux événements
                if current_count > last_event_count:
                    new_events = monitor.get_recent_events(limit=current_count - last_event_count)
                    for event in new_events:
                        yield f"data: {json.dumps(event)}\n\n"
                    
                    last_event_count = current_count
                
                # Heartbeat
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now().isoformat()})}\n\n"
                
                time.sleep(2)  # Vérifier toutes les 2 secondes
                
            except Exception as e:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                break
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    
    return response


# ============================================================================
# VUES UTILITAIRES
# ============================================================================

def analyse_logs(request, analyse_id):
    """Page des logs détaillés d'une analyse"""
    
    if request.user.is_authenticated:
        analyse = get_object_or_404(
            AnalysePaie, 
            id=analyse_id, 
            created_by=request.user
        )
    else:
        analyse = get_object_or_404(AnalysePaie, id=analyse_id)
    
    logs = LogAnalyse.objects.filter(analyse=analyse).order_by('-timestamp')
    
    context = {
        'analyse': analyse,
        'logs': logs,
    }
    
    return render(request, 'conventions/analyse_logs.html', context)


def export_analysis(request, analyse_id):
    """Export des résultats d'analyse en JSON"""
    
    if request.user.is_authenticated:
        analyse = get_object_or_404(
            AnalysePaie, 
            id=analyse_id, 
            created_by=request.user
        )
    else:
        analyse = get_object_or_404(AnalysePaie, id=analyse_id)
    
    variables = VariablePaie.objects.filter(analyse=analyse)
    graphiques = GraphiquePaie.objects.filter(analyse=analyse)
    
    export_data = {
        'analyse': {
            'id': str(analyse.id),
            'prompt': analyse.prompt_analyse,
            'impact_description': analyse.impact_description,
            'status': analyse.status,
            'execution_time': analyse.execution_time,
            'created_at': analyse.created_at.isoformat(),
        },
        'convention': {
            'id': analyse.convention.cc_id,
            'title': analyse.convention.title,
        },
        'variables': [
            {
                'name': var.name,
                'type': var.var_type,
                'description': var.description,
                'data_type': var.data_type,
                'legal_reference': var.legal_reference,
                'calculation_formula': var.calculation_formula,
                'depends_on': var.depends_on,
            }
            for var in variables
        ],
        'graphiques': [
            {
                'type': graph.chart_type,
                'title': graph.title,
                'config': graph.config,
                'data': graph.data,
            }
            for graph in graphiques
        ]
    }
    
    response = JsonResponse(export_data, json_dumps_params={'indent': 2})
    response['Content-Disposition'] = f'attachment; filename="analyse_{analyse.id}.json"'
    
    return response
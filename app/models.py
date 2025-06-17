from django.db import models
from django.contrib.auth import get_user_model
import uuid
import json
from datetime import datetime

User = get_user_model()


class Convention(models.Model):
    """Modèle pour les conventions collectives importées depuis Légifrance"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    cc_id = models.CharField(max_length=50, unique=True, verbose_name="ID Convention")
    title = models.CharField(max_length=255, verbose_name="Titre")
    description = models.TextField(blank=True, verbose_name="Description")
    
    # Métadonnées d'import
    date_import = models.DateTimeField(auto_now_add=True, verbose_name="Date d'import")
    imported_by = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name="Importée par", null=True, blank=True)
    
    # Données brutes de l'API
    raw_data = models.JSONField(default=dict, verbose_name="Données brutes API")
    articles_count = models.PositiveIntegerField(default=0, verbose_name="Nombre d'articles")
    
    # Statut d'analyse
    STATUS_CHOICES = [
        ('imported', 'Importée'),
        ('analyzing', 'En cours d\'analyse'),
        ('analyzed', 'Analysée'),
        ('error', 'Erreur'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='imported')
    
    class Meta:
        verbose_name = "Convention collective"
        verbose_name_plural = "Conventions collectives"
        ordering = ['-date_import']
    
    def __str__(self):
        return f"{self.title} ({self.cc_id})"


class AnalysePaie(models.Model):
    """Analyse d'un impact de paie par l'agent IA"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    convention = models.ForeignKey(Convention, on_delete=models.CASCADE, related_name='analyses')
    
    # Prompt et contexte
    prompt_analyse = models.TextField(verbose_name="Prompt d'analyse")
    context_articles = models.JSONField(default=list, verbose_name="Articles analysés")
    
    # Résultats de l'agent
    impact_description = models.TextField(verbose_name="Description de l'impact")
    variables_detected = models.JSONField(default=list, verbose_name="Variables détectées")
    agent_response = models.TextField(verbose_name="Réponse complète de l'agent")
    
    # Métadonnées
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    execution_time = models.FloatField(null=True, blank=True, verbose_name="Temps d'exécution (s)")
    
    # Statut
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminée'),
        ('failed', 'Échouée'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, verbose_name="Message d'erreur")
    
    class Meta:
        verbose_name = "Analyse de paie"
        verbose_name_plural = "Analyses de paie"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Analyse {self.id} - {self.convention.title}"


class VariablePaie(models.Model):
    """Variables de paie extraites et structurées"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analyse = models.ForeignKey(AnalysePaie, on_delete=models.CASCADE, related_name='variables')
    
    # Identification
    name = models.CharField(max_length=100, verbose_name="Nom de la variable")
    TYPE_CHOICES = [
        ('input', 'Variable d\'entrée'),
        ('intermediate', 'Variable intermédiaire'),
        ('output', 'Variable de sortie'),
    ]
    var_type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    
    # Propriétés
    description = models.TextField(verbose_name="Description")
    data_type = models.CharField(max_length=20, default='float', verbose_name="Type de données")
    
    # Références légales
    legal_reference = models.CharField(max_length=255, blank=True, verbose_name="Référence légale")
    article_source = models.CharField(max_length=100, blank=True, verbose_name="Article source")
    
    # Calcul (pour variables intermédiaires)
    calculation_formula = models.TextField(blank=True, verbose_name="Formule de calcul")
    depends_on = models.JSONField(default=list, verbose_name="Dépend de")
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Variable de paie"
        verbose_name_plural = "Variables de paie"
        unique_together = ['analyse', 'name']
        ordering = ['var_type', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.get_var_type_display()})"


class GraphiquePaie(models.Model):
    """Graphiques de visualisation Highcharts pour les analyses"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analyse = models.ForeignKey(AnalysePaie, on_delete=models.CASCADE, related_name='graphiques')
    
    # Type de graphique
    CHART_TYPES = [
        ('networkgraph', 'Graphe de réseau'),
        ('flowchart', 'Diagramme de flux'),
        ('timeline', 'Chronologie'),
        ('pie', 'Secteurs'),
        ('column', 'Colonnes'),
    ]
    chart_type = models.CharField(max_length=20, choices=CHART_TYPES)
    
    # Configuration Highcharts
    config = models.JSONField(verbose_name="Configuration Highcharts")
    data = models.JSONField(default=dict, verbose_name="Données du graphique")
    
    # Métadonnées
    title = models.CharField(max_length=255, verbose_name="Titre du graphique")
    description = models.TextField(blank=True, verbose_name="Description")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Graphique de paie"
        verbose_name_plural = "Graphiques de paie"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} ({self.get_chart_type_display()})"


class LogAnalyse(models.Model):
    """Log des exécutions d'analyse pour debugging et monitoring"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analyse = models.ForeignKey(AnalysePaie, on_delete=models.CASCADE, related_name='logs')
    
    # Détails de l'exécution
    step = models.CharField(max_length=100, verbose_name="Étape")
    message = models.TextField(verbose_name="Message")
    
    LEVEL_CHOICES = [
        ('debug', 'Debug'),
        ('info', 'Info'),
        ('warning', 'Warning'),
        ('error', 'Error'),
    ]
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES, default='info')
    
    # Données supplémentaires
    extra_data = models.JSONField(default=dict, verbose_name="Données supplémentaires")
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Log d'analyse"
        verbose_name_plural = "Logs d'analyse"
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"[{self.level.upper()}] {self.step} - {self.timestamp}"


# Signaux pour automatiser certaines tâches
from django.db.models.signals import post_save
from django.dispatch import receiver

@receiver(post_save, sender=AnalysePaie)
def create_default_graphs(sender, instance, created, **kwargs):
    """Crée automatiquement les graphiques par défaut après une analyse"""
    if created and instance.status == 'completed':
        # Créer les graphiques de base
        default_charts = [
            ('networkgraph', 'Graphe des variables'),
            ('timeline', 'Chronologie de création'),
            ('pie', 'Répartition par type'),
        ]
        
        for chart_type, title in default_charts:
            GraphiquePaie.objects.get_or_create(
                analyse=instance,
                chart_type=chart_type,
                defaults={
                    'title': title,
                    'config': {},
                    'data': {}
                }
            )
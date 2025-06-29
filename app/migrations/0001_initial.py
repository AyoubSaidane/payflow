# Generated by Django 5.2.3 on 2025-06-15 16:04

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Convention",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "cc_id",
                    models.CharField(
                        max_length=50, unique=True, verbose_name="ID Convention"
                    ),
                ),
                ("title", models.CharField(max_length=255, verbose_name="Titre")),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="Description"),
                ),
                (
                    "date_import",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Date d'import"
                    ),
                ),
                (
                    "raw_data",
                    models.JSONField(default=dict, verbose_name="Données brutes API"),
                ),
                (
                    "articles_count",
                    models.PositiveIntegerField(
                        default=0, verbose_name="Nombre d'articles"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("imported", "Importée"),
                            ("analyzing", "En cours d'analyse"),
                            ("analyzed", "Analysée"),
                            ("error", "Erreur"),
                        ],
                        default="imported",
                        max_length=20,
                    ),
                ),
                (
                    "imported_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="Importée par",
                    ),
                ),
            ],
            options={
                "verbose_name": "Convention collective",
                "verbose_name_plural": "Conventions collectives",
                "ordering": ["-date_import"],
            },
        ),
        migrations.CreateModel(
            name="AnalysePaie",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("prompt_analyse", models.TextField(verbose_name="Prompt d'analyse")),
                (
                    "context_articles",
                    models.JSONField(default=list, verbose_name="Articles analysés"),
                ),
                (
                    "impact_description",
                    models.TextField(verbose_name="Description de l'impact"),
                ),
                (
                    "variables_detected",
                    models.JSONField(default=list, verbose_name="Variables détectées"),
                ),
                (
                    "agent_response",
                    models.TextField(verbose_name="Réponse complète de l'agent"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "execution_time",
                    models.FloatField(
                        blank=True, null=True, verbose_name="Temps d'exécution (s)"
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "En attente"),
                            ("processing", "En cours"),
                            ("completed", "Terminée"),
                            ("failed", "Échouée"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                (
                    "error_message",
                    models.TextField(blank=True, verbose_name="Message d'erreur"),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "convention",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="analyses",
                        to="app.convention",
                    ),
                ),
            ],
            options={
                "verbose_name": "Analyse de paie",
                "verbose_name_plural": "Analyses de paie",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="GraphiquePaie",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "chart_type",
                    models.CharField(
                        choices=[
                            ("networkgraph", "Graphe de réseau"),
                            ("flowchart", "Diagramme de flux"),
                            ("timeline", "Chronologie"),
                            ("pie", "Secteurs"),
                            ("column", "Colonnes"),
                        ],
                        max_length=20,
                    ),
                ),
                ("config", models.JSONField(verbose_name="Configuration Highcharts")),
                (
                    "data",
                    models.JSONField(default=dict, verbose_name="Données du graphique"),
                ),
                (
                    "title",
                    models.CharField(max_length=255, verbose_name="Titre du graphique"),
                ),
                (
                    "description",
                    models.TextField(blank=True, verbose_name="Description"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "analyse",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="graphiques",
                        to="app.analysepaie",
                    ),
                ),
            ],
            options={
                "verbose_name": "Graphique de paie",
                "verbose_name_plural": "Graphiques de paie",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="LogAnalyse",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("step", models.CharField(max_length=100, verbose_name="Étape")),
                ("message", models.TextField(verbose_name="Message")),
                (
                    "level",
                    models.CharField(
                        choices=[
                            ("debug", "Debug"),
                            ("info", "Info"),
                            ("warning", "Warning"),
                            ("error", "Error"),
                        ],
                        default="info",
                        max_length=10,
                    ),
                ),
                (
                    "extra_data",
                    models.JSONField(
                        default=dict, verbose_name="Données supplémentaires"
                    ),
                ),
                ("timestamp", models.DateTimeField(auto_now_add=True)),
                (
                    "analyse",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="logs",
                        to="app.analysepaie",
                    ),
                ),
            ],
            options={
                "verbose_name": "Log d'analyse",
                "verbose_name_plural": "Logs d'analyse",
                "ordering": ["-timestamp"],
            },
        ),
        migrations.CreateModel(
            name="VariablePaie",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "name",
                    models.CharField(max_length=100, verbose_name="Nom de la variable"),
                ),
                (
                    "var_type",
                    models.CharField(
                        choices=[
                            ("input", "Variable d'entrée"),
                            ("intermediate", "Variable intermédiaire"),
                            ("output", "Variable de sortie"),
                        ],
                        max_length=20,
                    ),
                ),
                ("description", models.TextField(verbose_name="Description")),
                (
                    "data_type",
                    models.CharField(
                        default="float", max_length=20, verbose_name="Type de données"
                    ),
                ),
                (
                    "legal_reference",
                    models.CharField(
                        blank=True, max_length=255, verbose_name="Référence légale"
                    ),
                ),
                (
                    "article_source",
                    models.CharField(
                        blank=True, max_length=100, verbose_name="Article source"
                    ),
                ),
                (
                    "calculation_formula",
                    models.TextField(blank=True, verbose_name="Formule de calcul"),
                ),
                (
                    "depends_on",
                    models.JSONField(default=list, verbose_name="Dépend de"),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "analyse",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="variables",
                        to="app.analysepaie",
                    ),
                ),
            ],
            options={
                "verbose_name": "Variable de paie",
                "verbose_name_plural": "Variables de paie",
                "ordering": ["var_type", "name"],
                "unique_together": {("analyse", "name")},
            },
        ),
    ]

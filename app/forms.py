from django import forms
from django.core.exceptions import ValidationError
from .models import Convention, AnalysePaie, VariablePaie


class ConventionImportForm(forms.Form):
    """Formulaire pour importer une convention collective"""
    
    cc_id = forms.CharField(
        max_length=50,
        label="ID Convention Collective",
        help_text="Ex: 3028, 1517, 2596...",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: 3028',
            'pattern': '[0-9]+',
            'title': 'Entrez uniquement des chiffres'
        })
    )
    
    description = forms.CharField(
        required=False,
        label="Description optionnelle",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Description personnalisée de cette convention...'
        })
    )
    
    def clean_cc_id(self):
        cc_id = self.cleaned_data['cc_id']
        
        # Vérifier que c'est numérique
        if not cc_id.isdigit():
            raise ValidationError("L'ID doit être numérique")
        
        # Vérifier la longueur
        if len(cc_id) < 2 or len(cc_id) > 6:
            raise ValidationError("L'ID doit faire entre 2 et 6 chiffres")
        
        return cc_id


class AnalysePaieForm(forms.ModelForm):
    """Formulaire pour créer une analyse de paie"""
    
    article_ids = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
        help_text="IDs des articles sélectionnés (séparés par des virgules)"
    )
    
    class Meta:
        model = AnalysePaie
        fields = ['prompt_analyse']
        widgets = {
            'prompt_analyse': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Décrivez ce que vous voulez analyser dans cette convention...\n\nExemples:\n- Analyse les primes d\'ancienneté\n- Recherche les indemnités de transport\n- Identifie les heures supplémentaires',
                'required': True
            })
        }
        labels = {
            'prompt_analyse': 'Question d\'analyse'
        }
        help_texts = {
            'prompt_analyse': 'Posez une question précise sur les variables de paie à analyser dans cette convention'
        }
    
    def clean_prompt_analyse(self):
        prompt = self.cleaned_data['prompt_analyse']
        
        if len(prompt.strip()) < 10:
            raise ValidationError("La question doit faire au moins 10 caractères")
        
        if len(prompt) > 2000:
            raise ValidationError("La question ne peut pas dépasser 2000 caractères")
        
        return prompt.strip()


class VariablePaieForm(forms.ModelForm):
    """Formulaire pour créer/modifier une variable de paie"""
    
    depends_on_display = forms.CharField(
        required=False,
        label="Dépend de (noms des variables)",
        help_text="Entrez les noms des variables dont celle-ci dépend, séparés par des virgules",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'salaire_base, anciennete, coefficient'
        })
    )
    
    class Meta:
        model = VariablePaie
        fields = [
            'name', 'var_type', 'description', 'data_type',
            'legal_reference', 'article_source', 'calculation_formula'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'nom_variable_sans_espaces'
            }),
            'var_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description détaillée de cette variable...'
            }),
            'data_type': forms.Select(
                choices=[
                    ('float', 'Nombre décimal'),
                    ('int', 'Nombre entier'),
                    ('str', 'Texte'),
                    ('bool', 'Vrai/Faux'),
                    ('date', 'Date')
                ],
                attrs={'class': 'form-select'}
            ),
            'legal_reference': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Article L. 3121-1 du Code du travail'
            }),
            'article_source': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Article 15.2 de la convention'
            }),
            'calculation_formula': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'salaire_base * coefficient * anciennete'
            })
        }
        labels = {
            'name': 'Nom de la variable',
            'var_type': 'Type de variable',
            'description': 'Description',
            'data_type': 'Type de données',
            'legal_reference': 'Référence légale',
            'article_source': 'Article source',
            'calculation_formula': 'Formule de calcul'
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Pré-remplir le champ depends_on_display si on modifie
        if self.instance and self.instance.pk and self.instance.depends_on:
            self.fields['depends_on_display'].initial = ', '.join(self.instance.depends_on)
    
    def clean_name(self):
        name = self.cleaned_data['name']
        
        # Vérifier que le nom ne contient que des caractères autorisés
        import re
        if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', name):
            raise ValidationError(
                "Le nom doit commencer par une lettre ou _, "
                "et ne contenir que des lettres, chiffres et _"
            )
        
        return name.lower()
    
    def clean_depends_on_display(self):
        depends_str = self.cleaned_data.get('depends_on_display', '')
        
        if not depends_str.strip():
            return []
        
        # Nettoyer et séparer
        depends_list = [dep.strip() for dep in depends_str.split(',') if dep.strip()]
        
        # Valider chaque dépendance
        for dep in depends_list:
            import re
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', dep):
                raise ValidationError(f"'{dep}' n'est pas un nom de variable valide")
        
        return depends_list
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Convertir depends_on_display en liste JSON
        depends_list = self.cleaned_data.get('depends_on_display', [])
        instance.depends_on = depends_list
        
        if commit:
            instance.save()
        
        return instance


class QuickAnalysisForm(forms.Form):
    """Formulaire pour l'analyse rapide via AJAX"""
    
    prompt = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Que voulez-vous analyser ?',
            'required': True
        }),
        max_length=1000,
        min_length=5
    )


class ArticleSearchForm(forms.Form):
    """Formulaire de recherche d'articles dans une convention"""
    
    search_query = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher dans les articles...',
            'autocomplete': 'off'
        }),
        label="Recherche"
    )
    
    search_in = forms.ChoiceField(
        choices=[
            ('all', 'Tout'),
            ('title', 'Titres uniquement'),
            ('content', 'Contenu uniquement'),
            ('num', 'Numéros d\'article')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        initial='all',
        label="Rechercher dans"
    )


class ChartConfigForm(forms.Form):
    """Formulaire pour configurer les graphiques"""
    
    chart_type = forms.ChoiceField(
        choices=[
            ('networkgraph', 'Graphe de réseau'),
            ('timeline', 'Chronologie'),
            ('pie', 'Secteurs'),
            ('column', 'Colonnes'),
            ('flowchart', 'Diagramme de flux')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Type de graphique"
    )
    
    title = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Titre du graphique'
        }),
        label="Titre"
    )
    
    height = forms.IntegerField(
        min_value=200,
        max_value=1000,
        initial=400,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': '200',
            'max': '1000',
            'step': '50'
        }),
        label="Hauteur (px)"
    )
    
    show_labels = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Afficher les libellés"
    )
    
    enable_export = forms.BooleanField(
        required=False,
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        label="Activer l'export"
    )



import os
from smolagents import LiteLLMModel, CodeAgent, tool
import json
import networkx as nx
from typing import Callable, Optional, Dict, List, Any, Literal
import inspect
import matplotlib.pyplot as plt
from datetime import datetime

class PayrollVariableGraph:
    """
    Graphe spécialisé pour la gestion des variables de paie dans le contexte du droit français.
    Catégorise les variables en entrée et intermédiaires, et fournit une représentation
    textuelle lisible pour les LLM.
    """
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self._function_registry = {}
        self._variable_registry = {
            'input_variables': {},      # Variables d'entrée
            'intermediate_variables': {} # Variables intermédiaires/calculées
        }
        self._impact_source = None  # Source de l'impact de paie
        
    def set_impact_source(self, impact_description: str, source_convention: str = None):
        """Définit la source de l'impact de paie analysé."""
        self._impact_source = {
            'description': impact_description,
            'convention': source_convention,
            'timestamp': datetime.now().isoformat()
        }
    
    def add_variable(self, 
                    var_name: str, 
                    var_type: Literal['input', 'intermediate'],
                    description: str,
                    data_type: str = 'float',
                    legal_reference: str = None,
                    calculation_formula: str = None,
                    depends_on: List[str] = None) -> None:
        """
        Ajoute une variable au registre avec ses métadonnées.
        
        Args:
            var_name: Nom de la variable
            var_type: Type de variable ('input' ou 'intermediate')
            description: Description de la variable
            data_type: Type de données ('float', 'int', 'bool', 'str', 'date')
            legal_reference: Référence légale (article, convention, etc.)
            calculation_formula: Formule de calcul si applicable
            depends_on: Liste des variables dont dépend cette variable
        """
        variable_info = {
            'name': var_name,
            'type': var_type,
            'description': description,
            'data_type': data_type,
            'legal_reference': legal_reference,
            'calculation_formula': calculation_formula,
            'depends_on': depends_on or [],
            'created_at': datetime.now().isoformat()
        }
        
        if var_type == 'input':
            self._variable_registry['input_variables'][var_name] = variable_info
        else:
            self._variable_registry['intermediate_variables'][var_name] = variable_info
    
    def add_calculation_node(self, 
                           node_id: str, 
                           function: Callable, 
                           description: str,
                           output_variable: str = None,
                           input_variables: List[str] = None,
                           legal_reference: str = None) -> None:
        """
        Ajoute un nœud de calcul au graphe.
        
        Args:
            node_id: Identifiant unique du nœud
            function: Fonction de calcul
            description: Description du calcul
            output_variable: Variable produite par ce calcul
            input_variables: Variables utilisées en entrée
            legal_reference: Référence légale pour ce calcul
        """
        self._function_registry[node_id] = function
        
        node_attrs = {
            'description': description,
            'function_name': function.__name__,
            'function_signature': str(inspect.signature(function)),
            'function_doc': inspect.getdoc(function) or '',
            'output_variable': output_variable,
            'input_variables': input_variables or [],
            'legal_reference': legal_reference,
            'node_type': 'calculation',
            'created_at': datetime.now().isoformat()
        }
        self.graph.add_node(node_id, **node_attrs)
    
    def connect_calculations(self, from_node: str, to_node: str, 
                           variable_passed: str = None, **attrs) -> None:
        """Connecte deux nœuds de calcul en spécifiant la variable transmise."""
        if from_node not in self.graph or to_node not in self.graph:
            raise ValueError("Les deux nœuds doivent exister avant de créer une connexion")
        
        edge_attrs = {
            'variable_passed': variable_passed,
            'created_at': datetime.now().isoformat(),
            **attrs
        }
        self.graph.add_edge(from_node, to_node, **edge_attrs)
    
    def execute_calculation(self, node_id: str, **variable_values) -> Any:
        """
        Exécute un calcul en utilisant les valeurs des variables fournies.
        
        Args:
            node_id: Identifiant du nœud à exécuter
            **variable_values: Valeurs des variables (nom_variable=valeur)
        """
        if node_id not in self._function_registry:
            raise ValueError(f"Aucune fonction trouvée pour le nœud '{node_id}'")
        
        func = self._function_registry[node_id]
        node_info = self.graph.nodes[node_id]
        
        # Vérifier que toutes les variables requises sont fournies
        required_vars = node_info.get('input_variables', [])
        missing_vars = [var for var in required_vars if var not in variable_values]
        
        if missing_vars:
            raise ValueError(f"Variables manquantes pour '{node_id}': {missing_vars}")
        
        # Filtrer les arguments pour ne garder que ceux attendus par la fonction
        sig = inspect.signature(func)
        filtered_args = {k: v for k, v in variable_values.items() if k in sig.parameters}
        
        return func(**filtered_args)
    
    def get_variable_summary(self) -> Dict:
        """Retourne un résumé de toutes les variables."""
        return {
            'total_input_variables': len(self._variable_registry['input_variables']),
            'total_intermediate_variables': len(self._variable_registry['intermediate_variables']),
            'input_variables': list(self._variable_registry['input_variables'].keys()),
            'intermediate_variables': list(self._variable_registry['intermediate_variables'].keys()),
            'impact_source': self._impact_source
        }
    
    def to_llm_readable_text(self) -> str:
        """
        Convertit le graphe en représentation textuelle EXTRÊMEMENT STRUCTURÉE pour un LLM.
        Cette fonction est cruciale pour l'intégration MCP.
        """
        text_parts = []
        
        # En-tête avec contexte
        text_parts.append("===============================================")
        text_parts.append("    SYSTÈME DE VARIABLES DE PAIE - ÉTAT COMPLET")
        text_parts.append("===============================================")
        text_parts.append("")
        
        if self._impact_source:
            text_parts.append("📋 CONTEXTE DE L'IMPACT:")
            text_parts.append(f"   Impact analysé: {self._impact_source['description']}")
            if self._impact_source.get('convention'):
                text_parts.append(f"   Convention collective: {self._impact_source['convention']}")
            text_parts.append(f"   Timestamp: {self._impact_source.get('timestamp', 'Non défini')}")
            text_parts.append("")
        
        # SECTION 1: VARIABLES D'ENTRÉE (ultra-détaillées)
        text_parts.append("🔵 SECTION 1: VARIABLES D'ENTRÉE")
        text_parts.append("   (Données fournies en input au système)")
        text_parts.append("   " + "="*45)
        
        if self._variable_registry['input_variables']:
            for i, (var_name, var_info) in enumerate(self._variable_registry['input_variables'].items(), 1):
                text_parts.append(f"   {i}. VARIABLE: {var_name}")
                text_parts.append(f"      ├─ Type de données: {var_info['data_type']}")
                text_parts.append(f"      ├─ Description: {var_info['description']}")
                text_parts.append(f"      ├─ Catégorie: INPUT (donnée externe)")
                if var_info.get('legal_reference'):
                    text_parts.append(f"      ├─ Base légale: {var_info['legal_reference']}")
                text_parts.append(f"      └─ Créée le: {var_info.get('created_at', 'N/A')}")
                text_parts.append("")
        else:
            text_parts.append("   ⚠️  AUCUNE VARIABLE D'ENTRÉE DÉFINIE")
            text_parts.append("")
        
        # SECTION 2: VARIABLES INTERMÉDIAIRES (ultra-détaillées)
        text_parts.append("🟡 SECTION 2: VARIABLES INTERMÉDIAIRES/CALCULÉES")
        text_parts.append("   (Résultats de calculs internes)")
        text_parts.append("   " + "="*47)
        
        if self._variable_registry['intermediate_variables']:
            for i, (var_name, var_info) in enumerate(self._variable_registry['intermediate_variables'].items(), 1):
                text_parts.append(f"   {i}. VARIABLE: {var_name}")
                text_parts.append(f"      ├─ Type de données: {var_info['data_type']}")
                text_parts.append(f"      ├─ Description: {var_info['description']}")
                text_parts.append(f"      ├─ Catégorie: INTERMEDIATE (calculée)")
                if var_info.get('calculation_formula'):
                    text_parts.append(f"      ├─ Formule: {var_info['calculation_formula']}")
                if var_info.get('depends_on'):
                    deps = ', '.join(var_info['depends_on'])
                    text_parts.append(f"      ├─ Dépendances: [{deps}]")
                if var_info.get('legal_reference'):
                    text_parts.append(f"      ├─ Base légale: {var_info['legal_reference']}")
                text_parts.append(f"      └─ Créée le: {var_info.get('created_at', 'N/A')}")
                text_parts.append("")
        else:
            text_parts.append("   ⚠️  AUCUNE VARIABLE INTERMÉDIAIRE DÉFINIE")
            text_parts.append("")
        
        # SECTION 3: VARIABLES DE SORTIE (identifiées à partir des nœuds)
        output_variables = set()
        for node_id, node_data in self.graph.nodes(data=True):
            if node_data.get('output_variable'):
                output_variables.add(node_data['output_variable'])
        
        text_parts.append("🟢 SECTION 3: VARIABLES DE SORTIE")
        text_parts.append("   (Résultats finaux produits par le système)")
        text_parts.append("   " + "="*42)
        
        if output_variables:
            for i, var_name in enumerate(sorted(output_variables), 1):
                # Chercher dans les variables intermédiaires pour plus de détails
                var_details = self._variable_registry['intermediate_variables'].get(var_name, {})
                text_parts.append(f"   {i}. VARIABLE: {var_name}")
                text_parts.append(f"      ├─ Catégorie: OUTPUT (résultat final)")
                if var_details:
                    text_parts.append(f"      ├─ Type: {var_details.get('data_type', 'non défini')}")
                    text_parts.append(f"      └─ Description: {var_details.get('description', 'Non disponible')}")
                else:
                    text_parts.append(f"      └─ (Détails non trouvés dans le registre)")
                text_parts.append("")
        else:
            text_parts.append("   ⚠️  AUCUNE VARIABLE DE SORTIE IDENTIFIÉE")
            text_parts.append("")
        
        # SECTION 4: GRAPHE DE CALCUL (format JSON + représentation visuelle)
        text_parts.append("🔗 SECTION 4: GRAPHE DE CALCUL")
        text_parts.append("   " + "="*31)
        
        if self.graph.nodes():
            # Sous-section 4A: Nœuds détaillés
            text_parts.append("   4A. NŒUDS DE CALCUL:")
            for i, (node_id, node_data) in enumerate(self.graph.nodes(data=True), 1):
                text_parts.append(f"      {i}. NŒUD: {node_id}")
                text_parts.append(f"         ├─ Description: {node_data['description']}")
                text_parts.append(f"         ├─ Fonction: {node_data.get('function_name', 'N/A')}")
                if node_data.get('input_variables'):
                    inputs = ', '.join(node_data['input_variables'])
                    text_parts.append(f"         ├─ Variables en entrée: [{inputs}]")
                if node_data.get('output_variable'):
                    text_parts.append(f"         ├─ Variable en sortie: {node_data['output_variable']}")
                if node_data.get('legal_reference'):
                    text_parts.append(f"         ├─ Référence légale: {node_data['legal_reference']}")
                text_parts.append(f"         └─ Signature: {node_data.get('function_signature', 'N/A')}")
                text_parts.append("")
            
            # Sous-section 4B: Connexions
            text_parts.append("   4B. CONNEXIONS/FLUX:")
            if self.graph.edges():
                for i, (source, target, edge_data) in enumerate(self.graph.edges(data=True), 1):
                    connection_desc = f"{source} ──→ {target}"
                    text_parts.append(f"      {i}. {connection_desc}")
                    if edge_data.get('variable_passed'):
                        text_parts.append(f"         └─ Variable transmise: {edge_data['variable_passed']}")
                    text_parts.append("")
            else:
                text_parts.append("      ⚠️  Aucune connexion définie")
                text_parts.append("")
            
            # Sous-section 4C: Représentation JSON du graphe
            text_parts.append("   4C. REPRÉSENTATION JSON DU GRAPHE:")
            graph_json = {
                "nodes": [
                    {
                        "id": node_id,
                        "description": data['description'],
                        "function_name": data.get('function_name'),
                        "input_variables": data.get('input_variables', []),
                        "output_variable": data.get('output_variable'),
                        "legal_reference": data.get('legal_reference')
                    }
                    for node_id, data in self.graph.nodes(data=True)
                ],
                "edges": [
                    {
                        "from": source,
                        "to": target,
                        "variable_passed": data.get('variable_passed')
                    }
                    for source, target, data in self.graph.edges(data=True)
                ]
            }
            
            graph_json_str = json.dumps(graph_json, indent=6, ensure_ascii=False)
            # Indenter chaque ligne pour l'alignement
            indented_json = '\\n'.join('      ' + line for line in graph_json_str.split('\\n'))
            text_parts.append(indented_json)
            text_parts.append("")
            
            # Sous-section 4D: Analyse de dépendances
            text_parts.append("   4D. ANALYSE DES DÉPENDANCES:")
            try:
                # Ordre topologique
                topo_order = list(nx.topological_sort(self.graph))
                text_parts.append(f"      Ordre d'exécution optimal: {' → '.join(topo_order)}")
                
                # Points d'entrée et de sortie
                entry_points = [n for n in self.graph.nodes() if self.graph.in_degree(n) == 0]
                exit_points = [n for n in self.graph.nodes() if self.graph.out_degree(n) == 0]
                
                text_parts.append(f"      Points d'entrée (pas de prédécesseurs): {entry_points}")
                text_parts.append(f"      Points de sortie (pas de successeurs): {exit_points}")
                
            except nx.NetworkXError as e:
                text_parts.append(f"      ⚠️  Erreur dans l'analyse: {str(e)}")
            
        else:
            text_parts.append("   ⚠️  AUCUN NŒUD DE CALCUL DÉFINI")
        
        text_parts.append("")
        text_parts.append("===============================================")
        text_parts.append("              FIN DE L'ÉTAT SYSTÈME")
        text_parts.append("===============================================")
        
        return "\\n".join(text_parts)
    
    def to_mcp_context(self) -> Dict:
        """
        Retourne le contexte formaté pour MCP (Model Context Protocol).
        """
        return {
            'variables': self._variable_registry,
            'graph_structure': {
                'nodes': [
                    {
                        'id': node_id,
                        'type': 'calculation',
                        'description': data['description'],
                        'input_variables': data.get('input_variables', []),
                        'output_variable': data.get('output_variable'),
                        'legal_reference': data.get('legal_reference')
                    }
                    for node_id, data in self.graph.nodes(data=True)
                ],
                'edges': [
                    {
                        'from': source,
                        'to': target,
                        'variable_passed': data.get('variable_passed')
                    }
                    for source, target, data in self.graph.edges(data=True)
                ]
            },
            'readable_representation': self.to_llm_readable_text(),
            'impact_source': self._impact_source,
            'summary': self.get_variable_summary()
        }
    
    def export_to_json(self, filepath: str) -> None:
        """Exporte l'état complet du système vers un fichier JSON."""
        export_data = self.to_mcp_context()
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
    
    def remove_variable(self, var_name: str) -> bool:
        """
        Supprime une variable du système.
        
        Args:
            var_name: Nom de la variable à supprimer
            
        Returns:
            True si supprimée, False si non trouvée
        """
        removed = False
        if var_name in self._variable_registry['input_variables']:
            del self._variable_registry['input_variables'][var_name]
            removed = True
        if var_name in self._variable_registry['intermediate_variables']:
            del self._variable_registry['intermediate_variables'][var_name]
            removed = True
        return removed
    
    def update_variable(self, var_name: str, **updates) -> bool:
        """
        Met à jour les propriétés d'une variable existante.
        
        Args:
            var_name: Nom de la variable à modifier
            **updates: Propriétés à mettre à jour (description, data_type, etc.)
            
        Returns:
            True si modifiée, False si non trouvée
        """
        # Chercher dans les variables d'entrée
        if var_name in self._variable_registry['input_variables']:
            var_info = self._variable_registry['input_variables'][var_name]
            for key, value in updates.items():
                if key in var_info:
                    var_info[key] = value
            return True
        
        # Chercher dans les variables intermédiaires
        if var_name in self._variable_registry['intermediate_variables']:
            var_info = self._variable_registry['intermediate_variables'][var_name]
            for key, value in updates.items():
                if key in var_info:
                    var_info[key] = value
            return True
        
        return False
    
    def remove_calculation_node(self, node_id: str) -> bool:
        """
        Supprime un nœud de calcul et toutes ses connexions.
        
        Args:
            node_id: Identifiant du nœud à supprimer
            
        Returns:
            True si supprimé, False si non trouvé
        """
        if node_id not in self.graph:
            return False
        
        # Supprimer le nœud (supprime automatiquement toutes les arêtes connectées)
        self.graph.remove_node(node_id)
        
        # Supprimer la fonction associée
        if node_id in self._function_registry:
            del self._function_registry[node_id]
        
        return True
    
    def update_calculation_node(self, node_id: str, **updates) -> bool:
        """
        Met à jour les propriétés d'un nœud de calcul.
        
        Args:
            node_id: Identifiant du nœud à modifier
            **updates: Propriétés à mettre à jour
            
        Returns:
            True si modifié, False si non trouvé
        """
        if node_id not in self.graph:
            return False
        
        node_attrs = self.graph.nodes[node_id]
        for key, value in updates.items():
            if key in node_attrs:
                node_attrs[key] = value
        
        return True
    
    def remove_connection(self, from_node: str, to_node: str) -> bool:
        """
        Supprime une connexion entre deux nœuds.
        
        Args:
            from_node: Nœud source
            to_node: Nœud destination
            
        Returns:
            True si supprimée, False si non trouvée
        """
        if self.graph.has_edge(from_node, to_node):
            self.graph.remove_edge(from_node, to_node)
            return True
        return False
    
    def clear_system(self) -> None:
        """Remet à zéro complètement le système."""
        self.graph.clear()
        self._function_registry.clear()
        self._variable_registry = {
            'input_variables': {},
            'intermediate_variables': {}
        }
        self._impact_source = None
    
    def list_all_components(self) -> Dict:
        """Retourne la liste complète de tous les composants du système."""
        return {
            'variables': {
                'input': list(self._variable_registry['input_variables'].keys()),
                'intermediate': list(self._variable_registry['intermediate_variables'].keys())
            },
            'nodes': list(self.graph.nodes()),
            'connections': list(self.graph.edges()),
            'impact_source': self._impact_source
        }
    
    # ===============================================================================
    # INTEGRATION HIGHCHARTS - GENERATION DE GRAPHIQUES LIVE
    # ===============================================================================
    
    def to_highcharts_config(self, chart_type: str = "networkgraph") -> Dict:
        """
        Génère la configuration Highcharts pour visualiser le graphe de paie.
        
        Args:
            chart_type: Type de graphique ('networkgraph', 'flowchart', 'organization')
        
        Returns:
            Configuration Highcharts prête à utiliser
        """
        if chart_type == "networkgraph":
            return self._generate_network_chart()
        elif chart_type == "flowchart":
            return self._generate_flowchart()
        elif chart_type == "sankey":
            return self._generate_sankey_diagram()
        elif chart_type == "variables_timeline":
            return self._generate_variables_timeline()
        else:
            return self._generate_network_chart()
    
    def _generate_network_chart(self) -> Dict:
        """Génère un graphique réseau NetworkGraph pour Highcharts."""
        
        # Préparer les nœuds
        nodes = []
        for i, (node_id, data) in enumerate(self.graph.nodes(data=True)):
            color = "#7cb5ec"  # Bleu par défaut
            if data.get('output_variable'):
                color = "#90ed7d"  # Vert pour les sorties
            elif len(list(self.graph.predecessors(node_id))) == 0:
                color = "#f7a35c"  # Orange pour les entrées
            
            nodes.append({
                'id': node_id,
                'name': data.get('description', node_id),
                'color': color,
                'marker': {
                    'radius': 25
                }
            })
        
        # Préparer les liens
        links = []
        for source, target, data in self.graph.edges(data=True):
            links.append({
                'from': source,
                'to': target,
                'weight': 3,
                'color': '#434348'
            })
        
        config = {
            'chart': {
                'type': 'networkgraph',
                'height': 600,
                'backgroundColor': '#f8f9fa'
            },
            'title': {
                'text': f'Graphe de Calcul de Paie',
                'style': {'fontSize': '18px'}
            },
            'subtitle': {
                'text': self._impact_source.get('description', 'Impact de paie') if self._impact_source else ''
            },
            'plotOptions': {
                'networkgraph': {
                    'keys': ['from', 'to'],
                    'layoutAlgorithm': {
                        'enableSimulation': True,
                        'friction': -0.9,
                        'linkLength': 100
                    },
                    'dataLabels': {
                        'enabled': True,
                        'style': {'fontSize': '10px'}
                    }
                }
            },
            'series': [{
                'name': 'Graphe de Paie',
                'data': links,
                'nodes': nodes
            }],
            'tooltip': {
                'formatter': "function() { return '<b>' + this.point.name + '</b>'; }"
            }
        }
        
        return config
    
    def _generate_flowchart(self) -> Dict:
        """Génère un diagramme de flux hiérarchique."""
        
        # Créer la structure hiérarchique
        levels = {}
        try:
            topo_order = list(nx.topological_sort(self.graph))
            for i, node in enumerate(topo_order):
                levels[node] = i
        except:
            # Si pas de tri topologique, utiliser des niveaux arbitraires
            for i, node in enumerate(self.graph.nodes()):
                levels[node] = i
        
        # Préparer les données
        series_data = []
        for node_id, data in self.graph.nodes(data=True):
            level = levels.get(node_id, 0)
            series_data.append({
                'name': data.get('description', node_id),
                'y': level,
                'color': '#7cb5ec'
            })
        
        config = {
            'chart': {
                'type': 'column',
                'height': 500
            },
            'title': {
                'text': 'Flux de Calcul de Paie'
            },
            'xAxis': {
                'categories': [data.get('description', node_id) for node_id, data in self.graph.nodes(data=True)]
            },
            'yAxis': {
                'title': {'text': 'Niveau de Traitement'}
            },
            'series': [{
                'name': 'Nœuds de Calcul',
                'data': series_data
            }]
        }
        
        return config
    
    def _generate_sankey_diagram(self) -> Dict:
        """Génère un diagramme Sankey pour visualiser les flux."""
        
        # Préparer les données Sankey
        sankey_data = []
        for source, target, edge_data in self.graph.edges(data=True):
            sankey_data.append({
                'from': source,
                'to': target,
                'weight': 1
            })
        
        config = {
            'chart': {
                'type': 'sankey',
                'height': 600
            },
            'title': {
                'text': 'Flux des Variables de Paie'
            },
            'series': [{
                'name': 'Flux de Calcul',
                'data': sankey_data,
                'type': 'sankey'
            }]
        }
        
        return config
    
    def _generate_variables_timeline(self) -> Dict:
        """Génère une timeline des variables créées."""
        
        # Collecter toutes les variables avec timestamps
        timeline_data = []
        
        # Variables d'entrée
        for var_name, var_info in self._variable_registry['input_variables'].items():
            if var_info.get('created_at'):
                try:
                    timestamp = datetime.fromisoformat(var_info['created_at'].replace('Z', '+00:00'))
                    timeline_data.append({
                        'x': int(timestamp.timestamp() * 1000),
                        'y': 1,
                        'name': var_name,
                        'category': 'Input',
                        'color': '#f7a35c'
                    })
                except:
                    pass
        
        # Variables intermédiaires
        for var_name, var_info in self._variable_registry['intermediate_variables'].items():
            if var_info.get('created_at'):
                try:
                    timestamp = datetime.fromisoformat(var_info['created_at'].replace('Z', '+00:00'))
                    timeline_data.append({
                        'x': int(timestamp.timestamp() * 1000),
                        'y': 2,
                        'name': var_name,
                        'category': 'Intermediate',
                        'color': '#7cb5ec'
                    })
                except:
                    pass
        
        config = {
            'chart': {
                'type': 'scatter',
                'height': 400
            },
            'title': {
                'text': 'Timeline de Création des Variables'
            },
            'xAxis': {
                'type': 'datetime',
                'title': {'text': 'Temps de Création'}
            },
            'yAxis': {
                'categories': ['', 'Variables Input', 'Variables Intermediate'],
                'title': {'text': 'Type de Variable'}
            },
            'series': [{
                'name': 'Variables',
                'data': timeline_data
            }],
            'tooltip': {
                'pointFormat': '<b>{point.name}</b><br/>Catégorie: {point.category}'
            }
        }
        
        return config
    
    def get_live_update_data(self) -> Dict:
        """
        Génère les données pour mise à jour live des graphiques.
        Retourne les statistiques actuelles du système.
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'stats': {
                'input_variables': len(self._variable_registry['input_variables']),
                'intermediate_variables': len(self._variable_registry['intermediate_variables']),
                'calculation_nodes': len(self.graph.nodes()),
                'connections': len(self.graph.edges())
            },
            'latest_variables': list(self._variable_registry['intermediate_variables'].keys())[-5:],
            'graph_complexity': len(self.graph.nodes()) + len(self.graph.edges())
        }

# Instance globale pour l'agent
payroll_graph = PayrollVariableGraph()

# Outils spécialisés pour l'agent de variables de paie
@tool
def set_payroll_impact_source(impact_description: str, convention_name: str = "") -> str:
    """
    Définit la source de l'impact de paie reçu d'un autre agent dans le système multi-agent.
    Cette fonction initialise le contexte pour traiter un nouvel impact provenant d'une 
    convention collective ou d'un texte juridique français. Elle est la première étape 
    obligatoire avant de créer des variables ou des calculs.
    
    Args:
        impact_description: Description complète de l'impact de paie (ex: "Prime d'ancienneté 2% après 5 ans")
        convention_name: Nom de la convention collective source (ex: "Convention Métallurgie 2024")
    
    Returns:
        Message de confirmation avec timestamp d'initialisation
    """
    try:
        payroll_graph.set_impact_source(impact_description, convention_name)
        return f"Source définie: '{impact_description}'" + (f" (Convention: {convention_name})" if convention_name else "")
    except Exception as e:
        return f"Erreur lors de la définition de la source: {str(e)}"

@tool
def add_payroll_variable(var_name: str, var_type: str, description: str, 
                        data_type: str = "float", legal_reference: str = "",
                        calculation_formula: str = "", depends_on_json: str = "[]") -> str:
    """
    Crée et enregistre une variable de paie dans le système de mémoire MCP.
    Les variables sont catégorisées en deux types : input (données externes) 
    et intermediate (résultats de calculs). Cette fonction maintient la mémoire
    persistante des variables pour le framework MCP multi-agent.
    
    Args:
        var_name: Nom unique de la variable (ex: "salaire_base", "taux_prime")
        var_type: Catégorie - "input" pour données externes ou "intermediate" pour calculs
        description: Description métier de la variable (ex: "Salaire de base mensuel en euros")
        data_type: Type Python - "float", "int", "bool", "str", "date"
        legal_reference: Article ou référence juridique (ex: "Art. 25 Convention Métallurgie")
        calculation_formula: Formule mathématique si variable calculée (ex: "salaire * 0.02")
        depends_on_json: JSON des dépendances - variables nécessaires au calcul
    
    Returns:
        Confirmation de création avec type et timestamp
    """
    try:
        depends_on = json.loads(depends_on_json) if depends_on_json else []
        
        payroll_graph.add_variable(
            var_name=var_name,
            var_type=var_type,
            description=description,
            data_type=data_type,
            legal_reference=legal_reference or None,
            calculation_formula=calculation_formula or None,
            depends_on=depends_on
        )
        
        return f"Variable '{var_name}' ajoutée avec succès (type: {var_type})"
    except Exception as e:
        return f"Erreur lors de l'ajout de la variable: {str(e)}"

@tool
def add_calculation_node(node_id: str, function_code: str, description: str,
                        output_variable: str = "", input_variables_json: str = "[]",
                        legal_reference: str = "") -> str:
    """
    Crée un nœud de calcul exécutable dans le graphe NetworkX de paie.
    Chaque nœud encapsule une fonction Python qui transforme des variables
    d'entrée en variables de sortie. Le graphe constitue la mémoire des
    processus de calcul pour le système MCP multi-agent.
    
    Args:
        node_id: Identifiant unique du nœud (ex: "calc_prime_anciennete")
        function_code: Code Python complet de la fonction (avec def et docstring)
        description: Description métier du calcul (ex: "Calcule la prime selon barème ancienneté")
        output_variable: Variable créée par ce calcul (ex: "montant_prime")
        input_variables_json: JSON des variables nécessaires (ex: '["salaire_base", "anciennete"]')
        legal_reference: Base juridique du calcul (ex: "Article 25 Convention Métallurgie")
    
    Returns:
        Confirmation de création du nœud avec signature de fonction
    """
    try:
        # Exécuter le code de la fonction
        namespace = {}
        exec(function_code, namespace)
        
        # Trouver la fonction
        func = None
        for name, obj in namespace.items():
            if callable(obj) and not name.startswith('__'):
                func = obj
                break
        
        if not func:
            return "Erreur: Aucune fonction trouvée dans le code fourni"
        
        input_variables = json.loads(input_variables_json) if input_variables_json else []
        
        payroll_graph.add_calculation_node(
            node_id=node_id,
            function=func,
            description=description,
            output_variable=output_variable or None,
            input_variables=input_variables,
            legal_reference=legal_reference or None
        )
        
        return f"Nœud de calcul '{node_id}' ajouté avec succès"
    except Exception as e:
        return f"Erreur lors de l'ajout du nœud de calcul: {str(e)}"

@tool
def connect_calculation_nodes(from_node: str, to_node: str, variable_passed: str = "") -> str:
    """
    Établit une connexion directionnelle entre deux nœuds de calcul dans le graphe.
    Ces connexions définissent l'ordre d'exécution et les flux de données entre
    les calculs. Le graphe résultant représente la chaîne complète de traitement
    de l'impact de paie pour la mémoire MCP.
    
    Args:
        from_node: Nœud source qui produit une variable (ex: "calc_taux_prime")
        to_node: Nœud destination qui consomme la variable (ex: "calc_montant_prime")
        variable_passed: Variable transmise entre les nœuds (ex: "taux_prime_anciennete")
    
    Returns:
        Confirmation de création de connexion avec flux de données
    """
    try:
        payroll_graph.connect_calculations(
            from_node=from_node,
            to_node=to_node,
            variable_passed=variable_passed or None
        )
        
        return f"Connexion créée: {from_node} → {to_node}" + (f" (via {variable_passed})" if variable_passed else "")
    except Exception as e:
        return f"Erreur lors de la connexion: {str(e)}"

@tool
def execute_payroll_calculation(node_id: str, variables_json: str) -> str:
    """
    Exécute une fonction de calcul de paie avec des valeurs réelles.
    Cette fonction permet de tester et valider les calculs créés,
    en fournissant des données concrètes et en obtenant les résultats
    calculés selon la logique définie dans le nœud.
    
    Args:
        node_id: Identifiant du nœud de calcul à exécuter (ex: "calc_prime_anciennete")
        variables_json: JSON des valeurs d'entrée (ex: '{"salaire_base": 3000, "anciennete": 5}')
    
    Returns:
        Résultat numérique du calcul avec contexte métier
    """
    try:
        variables = json.loads(variables_json)
        result = payroll_graph.execute_calculation(node_id, **variables)
        return f"Résultat du calcul '{node_id}': {result}"
    except Exception as e:
        return f"Erreur lors de l'exécution: {str(e)}"

@tool
def get_variable_summary() -> str:
    """
    Génère un résumé synthétique de toutes les variables créées dans le système.
    Fournit une vue d'ensemble rapide des variables d'entrée et intermédiaires
    avec leurs counts et listes, utile pour la supervision du système MCP.
    
    Returns:
        JSON structuré avec statistiques et listes des variables par catégorie
    """
    try:
        summary = payroll_graph.get_variable_summary()
        return json.dumps(summary, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Erreur lors de la récupération du résumé: {str(e)}"

@tool
def get_llm_readable_representation() -> str:
    """
    Génère la représentation textuelle structurée complète du système pour les LLM.
    Cette fonction est CRUCIALE pour l'intégration MCP : elle transforme le graphe
    et les variables en format texte lisible par d'autres agents du système multi-agent.
    Contient variables catégorisées, graphe JSON, dépendances et analyse complète.
    
    Returns:
        Représentation textuelle ultra-structurée avec sections variables et graphe JSON
    """
    try:
        return payroll_graph.to_llm_readable_text()
    except Exception as e:
        return f"Erreur lors de la génération de la représentation: {str(e)}"

@tool
def export_system_state(filepath: str = "payroll_system_state.json") -> str:
    """
    Sauvegarde l'état complet du système vers un fichier JSON pour persistance.
    Exporte toutes les variables, le graphe, les métadonnées et la représentation LLM.
    Permet la reprise de session et le partage d'état entre agents du système MCP.
    
    Args:
        filepath: Nom du fichier de sauvegarde (ex: "prime_anciennete_system.json")
    
    Returns:
        Confirmation de sauvegarde avec taille et localisation du fichier
    """
    try:
        payroll_graph.export_to_json(filepath)
        return f"État du système exporté vers '{filepath}'"
    except Exception as e:
        return f"Erreur lors de l'export: {str(e)}"

@tool
def get_mcp_context() -> str:
    """
    Génère le contexte structuré spécialement formaté pour le framework MCP.
    Produit un JSON optimisé pour l'intégration multi-agent avec variables 
    catégorisées, graphe NetworkX sérialisé et représentation LLM intégrée.
    Format standard pour l'échange de données entre agents du système.
    
    Returns:
        JSON complet du contexte MCP avec métadonnées, variables et graphe
    """
    try:
        context = payroll_graph.to_mcp_context()
        return json.dumps(context, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Erreur lors de la génération du contexte MCP: {str(e)}"

# ===============================================================================
# OUTILS DE SUPPRESSION ET MODIFICATION - LIBERTÉ TOTALE POUR L'AGENT
# ===============================================================================

@tool
def remove_payroll_variable(var_name: str) -> str:
    """
    Supprime définitivement une variable du système de paie.
    L'agent peut supprimer toute variable devenue inutile ou incorrecte.
    Donne une liberté totale de restructuration du système de variables.
    
    Args:
        var_name: Nom exact de la variable à supprimer (ex: "taux_obsolete")
    
    Returns:
        Confirmation de suppression ou message si variable non trouvée
    """
    try:
        removed = payroll_graph.remove_variable(var_name)
        if removed:
            return f"Variable '{var_name}' supprimée avec succès du système"
        else:
            return f"Variable '{var_name}' non trouvée dans le système"
    except Exception as e:
        return f"Erreur lors de la suppression de la variable: {str(e)}"

@tool
def update_payroll_variable(var_name: str, updates_json: str) -> str:
    """
    Modifie les propriétés d'une variable existante dans le système.
    Permet de corriger description, type, formule, dépendances sans recréer.
    L'agent peut ajuster finement toutes les caractéristiques des variables.
    
    Args:
        var_name: Nom de la variable à modifier (ex: "taux_prime")
        updates_json: JSON des modifications (ex: '{"description": "Nouvelle description", "data_type": "int"}')
    
    Returns:
        Confirmation de modification avec détails des changements appliqués
    """
    try:
        updates = json.loads(updates_json)
        modified = payroll_graph.update_variable(var_name, **updates)
        if modified:
            changes = ', '.join([f"{k}={v}" for k, v in updates.items()])
            return f"Variable '{var_name}' modifiée: {changes}"
        else:
            return f"Variable '{var_name}' non trouvée pour modification"
    except Exception as e:
        return f"Erreur lors de la modification de la variable: {str(e)}"

@tool
def remove_calculation_node(node_id: str) -> str:
    """
    Supprime complètement un nœud de calcul et toutes ses connexions.
    Supprime automatiquement la fonction associée et nettoie le graphe.
    L'agent peut restructurer entièrement la logique de calcul.
    
    Args:
        node_id: Identifiant du nœud à supprimer (ex: "calc_obsolete")
    
    Returns:
        Confirmation de suppression avec nettoyage des connexions
    """
    try:
        removed = payroll_graph.remove_calculation_node(node_id)
        if removed:
            return f"Nœud de calcul '{node_id}' et toutes ses connexions supprimés"
        else:
            return f"Nœud '{node_id}' non trouvé dans le graphe"
    except Exception as e:
        return f"Erreur lors de la suppression du nœud: {str(e)}"

@tool
def update_calculation_node(node_id: str, updates_json: str) -> str:
    """
    Modifie les propriétés d'un nœud de calcul existant (métadonnées uniquement).
    Permet de corriger description, variables d'entrée/sortie, références légales.
    Pour changer la fonction de calcul, il faut supprimer et recréer le nœud.
    
    Args:
        node_id: Identifiant du nœud à modifier (ex: "calc_prime")
        updates_json: JSON des modifications (ex: '{"description": "Nouvelle description", "legal_reference": "Art. 26"}')
    
    Returns:
        Confirmation des modifications appliquées au nœud
    """
    try:
        updates = json.loads(updates_json)
        modified = payroll_graph.update_calculation_node(node_id, **updates)
        if modified:
            changes = ', '.join([f"{k}={v}" for k, v in updates.items()])
            return f"Nœud '{node_id}' modifié: {changes}"
        else:
            return f"Nœud '{node_id}' non trouvé pour modification"
    except Exception as e:
        return f"Erreur lors de la modification du nœud: {str(e)}"

@tool
def remove_node_connection(from_node: str, to_node: str) -> str:
    """
    Supprime une connexion spécifique entre deux nœuds de calcul.
    Permet de reconfigurer les flux de données sans supprimer les nœuds.
    L'agent peut optimiser l'architecture du graphe de calcul.
    
    Args:
        from_node: Nœud source de la connexion (ex: "calc_taux")
        to_node: Nœud destination de la connexion (ex: "calc_montant")
    
    Returns:
        Confirmation de suppression de la connexion spécifique
    """
    try:
        removed = payroll_graph.remove_connection(from_node, to_node)
        if removed:
            return f"Connexion supprimée: {from_node} → {to_node}"
        else:
            return f"Aucune connexion trouvée entre '{from_node}' et '{to_node}'"
    except Exception as e:
        return f"Erreur lors de la suppression de la connexion: {str(e)}"

@tool
def clear_entire_system() -> str:
    """
    RESET COMPLET - Supprime tout le système et repart de zéro.
    Efface toutes les variables, nœuds, connexions et la source d'impact.
    Utiliser avec précaution - permet de recommencer une analyse complètement.
    
    Returns:
        Confirmation de remise à zéro complète du système
    """
    try:
        payroll_graph.clear_system()
        return "🔥 SYSTÈME COMPLÈTEMENT REMIS À ZÉRO - Toutes les données effacées"
    except Exception as e:
        return f"Erreur lors de la remise à zéro: {str(e)}"

@tool
def list_all_system_components() -> str:
    """
    Liste exhaustive de tous les composants présents dans le système.
    Fournit une vue d'ensemble complète pour aider l'agent à décider
    quoi supprimer, modifier ou garder lors de restructurations.
    
    Returns:
        JSON complet de tous les composants (variables, nœuds, connexions)
    """
    try:
        components = payroll_graph.list_all_components()
        return json.dumps(components, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Erreur lors du listage des composants: {str(e)}"

@tool
def request_information_from_base_agent(missing_info_description: str, current_context: str = "") -> str:
    """
    Demande des informations manquantes à l'agent BASE du système multi-agent.
    Utilisé quand l'agent actuel n'a pas assez d'informations pour créer 
    correctement les variables ou les calculs de paie. L'agent BASE peut 
    fournir des précisions sur l'impact, des exemples, ou des données manquantes.
    
    Args:
        missing_info_description: Description précise de ce qui manque (ex: "Il me manque les seuils d'ancienneté exacts pour la prime")
        current_context: Contexte actuel pour aider l'agent BASE (ex: "Impact: Prime ancienneté 2% après X ans")
    
    Returns:
        Réponse simulée de l'agent BASE avec les informations demandées
    """
    try:
        # Simulation d'un appel à l'agent BASE
        # Dans un vrai système multi-agent, ceci ferait un appel réseau/API
        
        # Construire la requête formatée
        request_payload = {
            "timestamp": datetime.now().isoformat(),
            "requesting_agent": "payroll_variable_agent",
            "request_type": "missing_information",
            "missing_info": missing_info_description,
            "current_context": current_context,
            "current_system_state": {
                "variables_count": {
                    "input": len(payroll_graph._variable_registry['input_variables']),
                    "intermediate": len(payroll_graph._variable_registry['intermediate_variables'])
                },
                "nodes_count": len(payroll_graph.graph.nodes()),
                "impact_source": payroll_graph._impact_source
            }
        }
        
        # Simulation de réponse intelligente basée sur des patterns courants
        response = _simulate_base_agent_response(missing_info_description, current_context)
        
        # Log de la requête pour le système MCP
        request_log = {
            "request": request_payload,
            "response": response,
            "status": "completed"
        }
        
        return f"""RÉPONSE DE L'AGENT BASE:
        
{response}

--- MÉTADONNÉES DE LA REQUÊTE ---
Demande: {missing_info_description}
Contexte: {current_context}
Timestamp: {datetime.now().isoformat()}

⚠️  NOTE: Ceci est une simulation. Dans un système réel, cette fonction 
ferait un appel à l'agent BASE via API/réseau."""
        
    except Exception as e:
        return f"Erreur lors de la communication avec l'agent BASE: {str(e)}"

def _simulate_base_agent_response(missing_info: str, context: str) -> str:
    """
    Simule une réponse intelligente de l'agent BASE basée sur des patterns courants
    du droit français de la paie.
    """
    missing_lower = missing_info.lower()
    context_lower = context.lower()
    
    # Patterns de réponse basés sur les demandes courantes
    if "seuil" in missing_lower or "barème" in missing_lower:
        if "ancienneté" in context_lower:
            return """Voici les seuils d'ancienneté standards pour les primes:
            
- Moins de 2 ans: 0% (pas de prime)
- 2 à 4 ans révolus: 2% du salaire de base
- 5 à 9 ans révolus: 4% du salaire de base  
- 10 ans et plus: 6% du salaire de base

Ces seuils sont les plus couramment utilisés dans les conventions collectives françaises."""
            
        elif "heure" in context_lower or "supplémentaire" in context_lower:
            return """Barème légal français pour les heures supplémentaires:
            
- Heures normales: 35h/semaine (base 100%)
- Heures supplémentaires 1er niveau: de la 36e à la 43e heure (+25%)
- Heures supplémentaires 2e niveau: à partir de la 44e heure (+50%)
- Base de calcul: 151,67h mensuelles (35h × 52 semaines ÷ 12 mois)"""
    
    elif "montant" in missing_lower or "calcul" in missing_lower:
        if "transport" in context_lower:
            return """Calculs standards pour les remboursements transport:
            
- Taux de remboursement: 50% de l'abonnement
- Plafond mensuel: 75€ (montant 2024)
- Base légale: Article L. 3261-2 du Code du travail
- Exonération sociale et fiscale dans la limite du plafond"""
            
        elif "prime" in context_lower:
            return """Éléments de calcul pour les primes:
            
- Base de calcul: salaire de base mensuel (hors primes et heures sup)
- Application: pourcentage selon barème d'ancienneté/performance
- Fréquence: mensuelle (sauf indication contraire)
- Charges sociales: soumises aux cotisations comme le salaire"""
    
    elif "référence" in missing_lower or "article" in missing_lower:
        return """Références légales principales en droit du travail français:
        
- Code du travail: Articles L. 3000 et suivants (rémunération)
- Conventions collectives: selon secteur d'activité
- URSSAF: circulaires sur l'assiette des cotisations
- Décrets d'application: mise à jour annuelle des seuils"""
    
    elif "condition" in missing_lower or "éligibilité" in missing_lower:
        return """Conditions d'éligibilité standards:
        
- Ancienneté: calculée en années pleines au 31 décembre
- Statut: salariés en CDI et CDD (selon convention)
- Temps de travail: prorata pour temps partiel
- Période d'essai: généralement exclue du calcul d'ancienneté"""
    
    else:
        # Réponse générique mais utile
        return f"""J'ai analysé votre demande concernant: "{missing_info}"

Voici les informations complémentaires standards:

1. **Base légale**: Vérifiez l'article spécifique de votre convention collective
2. **Calcul**: Généralement basé sur le salaire de base mensuel
3. **Conditions**: Ancienneté calculée en années pleines
4. **Application**: Mensuelle sauf mention contraire
5. **Charges**: Soumises aux cotisations sociales

Si vous avez besoin de précisions spécifiques sur un point particulier, 
reformulez votre demande en incluant plus de contexte sur l'impact analysé."""

# ===============================================================================
# OUTILS HIGHCHARTS - VISUALISATION LIVE ET INTERACTIVE
# ===============================================================================

@tool
def generate_highcharts_config(chart_type: str = "networkgraph") -> str:
    """
    Génère la configuration Highcharts pour visualiser le système de paie en temps réel.
    Transforme le graphe NetworkX et les variables en configuration JavaScript 
    prête à utiliser dans un frontend. Supporte plusieurs types de visualisation
    pour différents aspects du système de paie.
    
    Args:
        chart_type: Type de graphique ("networkgraph", "flowchart", "sankey", "variables_timeline")
    
    Returns:
        Configuration JSON Highcharts complète pour intégration frontend
    """
    try:
        config = payroll_graph.to_highcharts_config(chart_type)
        return json.dumps(config, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Erreur lors de la génération de la configuration Highcharts: {str(e)}"

@tool
def get_live_chart_data() -> str:
    """
    Fournit les données en temps réel pour mise à jour live des graphiques.
    Retourne les statistiques actuelles, dernières variables créées et
    métriques de complexité du système. Optimisé pour polling fréquent
    depuis le frontend sans surcharge.
    
    Returns:
        JSON des données live avec timestamp et statistiques système
    """
    try:
        live_data = payroll_graph.get_live_update_data()
        return json.dumps(live_data, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Erreur lors de la récupération des données live: {str(e)}"

@tool 
def export_frontend_package(base_filename: str = "payroll_charts") -> str:
    """
    Exporte un package complet pour intégration frontend avec Highcharts.
    Génère tous les types de graphiques, les données live et les configurations
    nécessaires pour un dashboard interactif. Inclut le HTML, JSON et JavaScript.
    
    Args:
        base_filename: Nom de base pour les fichiers générés (sans extension)
    
    Returns:
        Confirmation d'export avec liste des fichiers créés et instructions d'intégration
    """
    try:
        files_created = []
        
        # 1. Configuration NetworkGraph
        network_config = payroll_graph.to_highcharts_config("networkgraph")
        network_file = f"{base_filename}_network.json"
        with open(network_file, 'w', encoding='utf-8') as f:
            json.dump(network_config, f, indent=2, ensure_ascii=False)
        files_created.append(network_file)
        
        # 2. Configuration Flowchart
        flow_config = payroll_graph.to_highcharts_config("flowchart")
        flow_file = f"{base_filename}_flow.json"
        with open(flow_file, 'w', encoding='utf-8') as f:
            json.dump(flow_config, f, indent=2, ensure_ascii=False)
        files_created.append(flow_file)
        
        # 3. Configuration Timeline
        timeline_config = payroll_graph.to_highcharts_config("variables_timeline")
        timeline_file = f"{base_filename}_timeline.json"
        with open(timeline_file, 'w', encoding='utf-8') as f:
            json.dump(timeline_config, f, indent=2, ensure_ascii=False)
        files_created.append(timeline_file)
        
        # 4. Données live
        live_data = payroll_graph.get_live_update_data()
        live_file = f"{base_filename}_live_data.json"
        with open(live_file, 'w', encoding='utf-8') as f:
            json.dump(live_data, f, indent=2, ensure_ascii=False)
        files_created.append(live_file)
        
        # 5. HTML Dashboard intégré
        dashboard_html = _generate_dashboard_html(base_filename)
        html_file = f"{base_filename}_dashboard.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(dashboard_html)
        files_created.append(html_file)
        
        return f"""📦 PACKAGE FRONTEND EXPORTÉ AVEC SUCCÈS!

Fichiers créés:
{chr(10).join(['  • ' + file for file in files_created])}

🚀 INSTRUCTIONS D'INTÉGRATION:
1. Ouvrez {html_file} dans votre navigateur pour le dashboard complet
2. Intégrez les fichiers JSON dans votre application web
3. Utilisez get_live_chart_data() pour les mises à jour en temps réel
4. Polling recommandé: 1-2 secondes pour l'interactivité

📊 Types de graphiques inclus:
  • NetworkGraph: Visualisation du graphe de calcul
  • Flowchart: Flux hiérarchique des nœuds  
  • Timeline: Chronologie de création des variables
  • Live Data: Métriques temps réel du système"""
        
    except Exception as e:
        return f"Erreur lors de l'export du package frontend: {str(e)}"

def _generate_dashboard_html(base_filename: str) -> str:
    """Génère le HTML complet du dashboard avec Highcharts intégré."""
    
    impact_title = "Dashboard de Paie"
    if payroll_graph._impact_source:
        impact_title = payroll_graph._impact_source.get('description', 'Dashboard de Paie')
    
    html_template = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{impact_title} - Dashboard Live</title>
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/modules/networkgraph.js"></script>
    <script src="https://code.highcharts.com/modules/sankey.js"></script>
    <script src="https://code.highcharts.com/modules/exporting.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f7fa;
        }}
        .dashboard-header {{
            text-align: center;
            margin-bottom: 30px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
        }}
        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }}
        .chart-container {{
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }}
        .stats-panel {{
            background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
            color: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
        }}
        .stats-item {{
            display: inline-block;
            margin: 10px 20px;
        }}
        .stats-number {{
            font-size: 2em;
            font-weight: bold;
            display: block;
        }}
        .update-indicator {{
            position: fixed;
            top: 20px;
            right: 20px;
            background: #28a745;
            color: white;
            padding: 10px 15px;
            border-radius: 5px;
            font-weight: bold;
        }}
        .chart-controls {{
            margin: 10px 0;
            text-align: center;
        }}
        .btn {{
            background: #667eea;
            color: white;
            border: none;
            padding: 8px 16px;
            margin: 0 5px;
            border-radius: 5px;
            cursor: pointer;
        }}
        .btn:hover {{
            background: #5a6fd8;
        }}
    </style>
</head>
<body>
    <div class="dashboard-header">
        <h1>📊 {impact_title}</h1>
        <p>Dashboard Live de Visualisation des Variables de Paie</p>
        <div id="lastUpdate">Dernière mise à jour: Chargement...</div>
    </div>

    <div class="stats-panel" id="statsPanel">
        <div class="stats-item">
            <span class="stats-number" id="inputVars">-</span>
            <div>Variables Input</div>
        </div>
        <div class="stats-item">
            <span class="stats-number" id="intermediateVars">-</span>
            <div>Variables Intermediate</div>
        </div>
        <div class="stats-item">
            <span class="stats-number" id="calcNodes">-</span>
            <div>Nœuds de Calcul</div>
        </div>
        <div class="stats-item">
            <span class="stats-number" id="connections">-</span>
            <div>Connexions</div>
        </div>
    </div>

    <div class="dashboard-grid">
        <div class="chart-container">
            <div class="chart-controls">
                <h3>🔗 Graphe de Calcul</h3>
                <button class="btn" onclick="refreshChart('network')">🔄 Actualiser</button>
                <button class="btn" onclick="exportChart('network')">💾 Exporter</button>
            </div>
            <div id="networkChart" style="height: 500px;"></div>
        </div>

        <div class="chart-container">
            <div class="chart-controls">
                <h3>📈 Flux de Traitement</h3>
                <button class="btn" onclick="refreshChart('flow')">🔄 Actualiser</button>
                <button class="btn" onclick="exportChart('flow')">💾 Exporter</button>
            </div>
            <div id="flowChart" style="height: 400px;"></div>
        </div>

        <div class="chart-container">
            <div class="chart-controls">
                <h3>⏰ Timeline des Variables</h3>
                <button class="btn" onclick="refreshChart('timeline')">🔄 Actualiser</button>
                <button class="btn" onclick="exportChart('timeline')">💾 Exporter</button>
            </div>
            <div id="timelineChart" style="height: 350px;"></div>
        </div>
    </div>

    <div class="update-indicator" id="updateIndicator" style="display: none;">
        🔄 Mise à jour en cours...
    </div>

    <script>
        // Variables globales pour les graphiques
        let networkChart, flowChart, timelineChart;
        let isUpdating = false;

        // Chargement initial
        document.addEventListener('DOMContentLoaded', function() {{
            loadAllCharts();
            startLiveUpdates();
        }});

        // Chargement de tous les graphiques
        async function loadAllCharts() {{
            try {{
                // Charger les configurations depuis les fichiers JSON
                const [networkConfig, flowConfig, timelineConfig] = await Promise.all([
                    fetch('{base_filename}_network.json').then(r => r.json()),
                    fetch('{base_filename}_flow.json').then(r => r.json()),
                    fetch('{base_filename}_timeline.json').then(r => r.json())
                ]);

                // Créer les graphiques
                networkChart = Highcharts.chart('networkChart', networkConfig);
                flowChart = Highcharts.chart('flowChart', flowConfig);
                timelineChart = Highcharts.chart('timelineChart', timelineConfig);

                console.log('Tous les graphiques chargés avec succès');
            }} catch (error) {{
                console.error('Erreur lors du chargement des graphiques:', error);
            }}
        }}

        // Mise à jour des statistiques
        async function updateStats() {{
            try {{
                const liveData = await fetch('{base_filename}_live_data.json').then(r => r.json());
                
                document.getElementById('inputVars').textContent = liveData.stats.input_variables;
                document.getElementById('intermediateVars').textContent = liveData.stats.intermediate_variables;
                document.getElementById('calcNodes').textContent = liveData.stats.calculation_nodes;
                document.getElementById('connections').textContent = liveData.stats.connections;
                
                document.getElementById('lastUpdate').textContent = 
                    'Dernière mise à jour: ' + new Date(liveData.timestamp).toLocaleString('fr-FR');
                
            }} catch (error) {{
                console.error('Erreur lors de la mise à jour des stats:', error);
            }}
        }}

        // Rafraîchissement d'un graphique spécifique
        async function refreshChart(chartType) {{
            showUpdateIndicator();
            
            try {{
                let config;
                let chart;
                
                switch(chartType) {{
                    case 'network':
                        config = await fetch('{base_filename}_network.json').then(r => r.json());
                        if (networkChart) networkChart.destroy();
                        networkChart = Highcharts.chart('networkChart', config);
                        break;
                    case 'flow':
                        config = await fetch('{base_filename}_flow.json').then(r => r.json());
                        if (flowChart) flowChart.destroy();
                        flowChart = Highcharts.chart('flowChart', config);
                        break;
                    case 'timeline':
                        config = await fetch('{base_filename}_timeline.json').then(r => r.json());
                        if (timelineChart) timelineChart.destroy();
                        timelineChart = Highcharts.chart('timelineChart', config);
                        break;
                }}
                
                await updateStats();
                
            }} catch (error) {{
                console.error('Erreur lors du rafraîchissement:', error);
            }} finally {{
                hideUpdateIndicator();
            }}
        }}

        // Export de graphique
        function exportChart(chartType) {{
            let chart;
            switch(chartType) {{
                case 'network': chart = networkChart; break;
                case 'flow': chart = flowChart; break;
                case 'timeline': chart = timelineChart; break;
            }}
            
            if (chart) {{
                chart.exportChart({{
                    type: 'image/png',
                    filename: 'payroll_' + chartType + '_chart'
                }});
            }}
        }}

        // Mises à jour automatiques (toutes les 2 secondes)
        function startLiveUpdates() {{
            setInterval(async () => {{
                if (!isUpdating) {{
                    await updateStats();
                }}
            }}, 2000);
        }}

        // Indicateurs visuels
        function showUpdateIndicator() {{
            isUpdating = true;
            document.getElementById('updateIndicator').style.display = 'block';
        }}

        function hideUpdateIndicator() {{
            isUpdating = false;
            setTimeout(() => {{
                document.getElementById('updateIndicator').style.display = 'none';
            }}, 500);
        }}

        // Gestion des erreurs globales
        window.addEventListener('error', function(e) {{
            console.error('Erreur JavaScript:', e.error);
        }});
    </script>
</body>
</html>"""
    
    return html_template

def create_payroll_agent():
    """Crée et retourne un agent spécialisé pour les variables de paie."""
    
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ATTENTION: ANTHROPIC_API_KEY non trouvée dans les variables d'environnement!")
        print("Veuillez la définir: os.environ['ANTHROPIC_API_KEY'] = 'votre-clé'")
        return None
    
    # Modèle Claude spécialisé pour le droit français
    model = LiteLLMModel(
        model_id="claude-3-5-sonnet-20241022",
        temperature=0.1,  # Température basse pour plus de précision
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    
    # Agent avec outils spécialisés (CRÉATION + SUPPRESSION/MODIFICATION)
    agent = CodeAgent(
        tools=[
            # Outils de création
            set_payroll_impact_source,
            add_payroll_variable,
            add_calculation_node,
            connect_calculation_nodes,
            
            # Outils d'exécution et consultation
            execute_payroll_calculation,
            get_variable_summary,
            get_llm_readable_representation,
            export_system_state,
            get_mcp_context,
            
            # Outils de suppression et modification (LIBERTÉ TOTALE)
            remove_payroll_variable,
            update_payroll_variable,
            remove_calculation_node,
            update_calculation_node,
            remove_node_connection,
            clear_entire_system,
            list_all_system_components,
            
            # Outil de communication inter-agent
            request_information_from_base_agent,
            
            # Outils Highcharts - Visualisation Live
            generate_highcharts_config,
            get_live_chart_data,
            export_frontend_package
        ],
        model=model,
        max_steps=50,  # Augmenté pour permettre des analyses complexes
        additional_authorized_imports=['datetime', 'math', 'decimal', 'json']
    )
    
    return agent

if __name__ == "__main__":
    # Test de l'agent
    agent = create_payroll_agent()
    
    if agent:
        print("Agent de variables de paie initialisé avec succès!")
        print("\\nOutils disponibles:")
        for tool in agent.tools:
            tool_name = getattr(tool, 'name', str(tool))
            tool_desc = getattr(tool, 'description', 'Pas de description')
            first_sentence = tool_desc.split('.')[0] if tool_desc else 'Pas de description'
            print(f"  - {tool_name}: {first_sentence}")
    else:
        print("Échec de l'initialisation de l'agent.")
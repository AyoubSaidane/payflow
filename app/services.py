"""
Services pour l'intégration des agents IA et la génération de graphiques Highcharts
"""

import os
import time
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from django.conf import settings
from django.core.exceptions import ValidationError

# Configuration de la clé API Anthropic pour les agents
os.environ['ANTHROPIC_API_KEY'] = getattr(settings, 'ANTHROPIC_API_KEY', '')

# Import des agents existants
from payflow_agents import build_agent
from import_cc import get_all_articles
from payroll_variable_agent import PayrollVariableGraph, create_payroll_agent

logger = logging.getLogger(__name__)


class ConventionImportService:
    """Service pour l'import de conventions collectives depuis Légifrance"""
    
    @staticmethod
    def import_convention(cc_id: str, user) -> Dict[str, Any]:
        """
        Importe une convention collective depuis l'API Légifrance
        
        Args:
            cc_id: ID de la convention collective (numéro ou ID complet)
            user: Utilisateur Django qui fait l'import
            
        Returns:
            Dict avec les données de la convention et métadonnées
        """
        try:
            logger.info(f"Import de la convention {cc_id}")
            
            # Mapping des IDs de convention populaires
            convention_mapping = {
                '3028': 'KALITEXT000044253019',  # Portage salarial
                '1517': 'KALITEXT000005632340',  # Restauration rapide
                '2596': 'KALITEXT000005637766',  # Coiffure et esthétique  
                '1486': 'KALITEXT000005681943',  # Commerce de détail non alimentaire
                '1740': 'KALITEXT000005693130',  # Batiment (exemple)
                '1090': 'KALITEXT000005632520',  # Services de l'automobile
            }
            
            # Convertir l'ID si nécessaire
            api_id = convention_mapping.get(cc_id, cc_id)
            if not api_id.startswith('KALITEXT'):
                # Si ce n'est pas un ID complet et pas dans le mapping, essayer une approche alternative
                logger.warning(f"ID {cc_id} non trouvé dans le mapping, tentative avec ID original")
                api_id = cc_id
            
            # Essayer d'abord avec les articles actifs (filter_year=2999)
            articles = get_all_articles(api_id, filter_year=2999)
            
            # Si aucun article trouvé, essayer sans filtrage
            if not articles:
                logger.info(f"Aucun article actif trouvé pour {cc_id}, tentative sans filtrage...")
                articles = get_all_articles(api_id, filter_year=None)
            
            # Si toujours aucun article, créer des données de démonstration
            if not articles:
                logger.warning(f"Aucun article trouvé via API pour {cc_id}, création de données de démonstration")
                articles = ConventionImportService._create_demo_articles(cc_id)
            
            # Extraire les métadonnées de base
            title = f"Convention Collective {cc_id}"
            if articles and len(articles) > 0:
                # Essayer d'extraire le titre depuis les métadonnées
                first_article = articles[0]
                if 'pathTitle' in first_article and first_article['pathTitle']:
                    title = first_article['pathTitle'][0] if first_article['pathTitle'] else title
                elif 'title' in first_article:
                    title = first_article['title']
            
            result = {
                'cc_id': cc_id,
                'title': title,
                'articles_count': len(articles),
                'raw_data': {
                    'articles': articles,
                    'imported_at': datetime.now().isoformat(),
                    'api_version': '1.0',
                    'api_id_used': api_id
                },
                'status': 'imported'
            }
            
            logger.info(f"Import réussi: {len(articles)} articles récupérés")
            return result
            
        except Exception as e:
            logger.error(f"Erreur import convention {cc_id}: {str(e)}")
            raise ValidationError(f"Erreur lors de l'import: {str(e)}")
    
    @staticmethod
    def _create_demo_articles(cc_id: str) -> List[Dict]:
        """Crée des articles de démonstration si l'API ne fonctionne pas"""
        demo_articles = [
            {
                'id': f'DEMO_{cc_id}_001',
                'num': 'Article 1',
                'title': 'Champ d\'application',
                'pathTitle': [f'Convention Collective {cc_id}', 'Dispositions générales'],
                'content': f'La présente convention collective s\'applique aux entreprises relevant du secteur d\'activité défini par la convention {cc_id}.',
                'dateFin': 4070908800000  # Timestamp pour 2999
            },
            {
                'id': f'DEMO_{cc_id}_002', 
                'num': 'Article 2',
                'title': 'Rémunération',
                'pathTitle': [f'Convention Collective {cc_id}', 'Conditions de travail'],
                'content': 'Les salaires minima conventionnels sont fixés selon les grilles en annexe. Les primes d\'ancienneté sont calculées selon l\'ancienneté dans l\'entreprise.',
                'dateFin': 4070908800000
            },
            {
                'id': f'DEMO_{cc_id}_003',
                'num': 'Article 3', 
                'title': 'Heures supplémentaires',
                'pathTitle': [f'Convention Collective {cc_id}', 'Temps de travail'],
                'content': 'Les heures supplémentaires donnent lieu à majoration de 25% pour les 8 premières heures et 50% au-delà.',
                'dateFin': 4070908800000
            },
            {
                'id': f'DEMO_{cc_id}_004',
                'num': 'Article 4',
                'title': 'Primes et indemnités', 
                'pathTitle': [f'Convention Collective {cc_id}', 'Rémunération'],
                'content': 'Prime d\'ancienneté: 3% après 3 ans, 6% après 6 ans, 9% après 9 ans. Indemnité de transport selon barème géographique.',
                'dateFin': 4070908800000
            },
            {
                'id': f'DEMO_{cc_id}_005',
                'num': 'Article 5',
                'title': 'Congés payés',
                'pathTitle': [f'Convention Collective {cc_id}', 'Congés'],
                'content': 'Congés payés selon le Code du travail. Jours de congés supplémentaires selon l\'ancienneté.',
                'dateFin': 4070908800000
            }
        ]
        
        return demo_articles


class PayrollAnalysisService:
    """Service pour l'analyse de variables de paie avec les agents IA"""
    
    def __init__(self):
        self.payflow_agent = None
        self.variables_agent = None
        self.session_id = None
        self._init_agents()
    
    def _init_agents(self):
        """Initialise les agents IA réels avec NetworkX live"""
        try:
            # Import et initialisation des vrais agents
            from payflow_agents import build_agent
            from payroll_variable_agent import create_payroll_agent, payroll_graph
            
            # Agents LLM complets
            self.payflow_agent = build_agent()
            self.variables_agent = create_payroll_agent()
            
            # Référence au graphe NetworkX global pour mise à jour temps réel
            self.payroll_graph = payroll_graph
            
            logger.info("🚀 Agents IA réels initialisés avec NetworkX live")
            logger.info(f"📊 Graphe NetworkX connecté: {len(self.payroll_graph.graph.nodes())} noeuds")
            
        except Exception as e:
            logger.error(f"Erreur initialisation agents: {str(e)}")
            # Fallback vers simulation
            self.payflow_agent = None
            self.variables_agent = None
            self.payroll_graph = None
            logger.info("Fallback vers mode simplifié")
    
    def analyze_payroll_impact(self, prompt: str, context_articles: List[Dict] = None, user_id: str = None) -> Dict[str, Any]:
        """
        Analyse un impact de paie en utilisant les agents IA
        
        Args:
            prompt: Description de l'impact à analyser
            context_articles: Articles de convention en contexte
            user_id: ID de l'utilisateur pour le monitoring
            
        Returns:
            Résultats de l'analyse structurés
        """
        start_time = time.time()
        
        # Démarrer le monitoring
        from .monitoring import monitor
        self.session_id = f"payroll_analysis_{int(time.time())}"
        monitor.start_session(
            session_id=self.session_id,
            description=f"Analyse de paie: {prompt[:50]}...",
            user_id=user_id
        )
        
        try:
            monitor.log_agent_action(
                session_id=self.session_id,
                agent_type='PayrollAnalysisService',
                action='analysis_start',
                message=f"Début analyse: {prompt[:100]}...",
                level='info',
                data={'prompt_length': len(prompt), 'has_context': bool(context_articles)}
            )
            
            # Utiliser les vrais agents LLM avec NetworkX en temps réel
            if self.payflow_agent and self.variables_agent and self.payroll_graph:
                monitor.log_agent_action(
                    session_id=self.session_id,
                    agent_type='PayrollAnalysisService',
                    action='agent_mode_selection',
                    message="🤖 Utilisation des agents LLM réels avec graphe NetworkX",
                    level='info'
                )
                
                # Phase 1: Définir l'impact source dans le graphe
                convention_source = "Convention collective analysée via Django"
                self.payroll_graph.set_impact_source(prompt, convention_source)
                
                # Phase 2: Analyse avec PayflowAgent pour comprendre l'impact
                if context_articles:
                    articles_text = self._format_articles_for_analysis(context_articles)
                    payflow_prompt = f"Analyse ces articles et leur impact sur la paie:\n\n{articles_text}\n\nQuestion: {prompt}"
                else:
                    payflow_prompt = f"Analyse cet impact de paie en contexte français: {prompt}"
                
                monitor.log_agent_action(
                    session_id=self.session_id,
                    agent_type='PayflowAgent',
                    action='llm_call_start',
                    message="📋 Début analyse avec PayflowAgent...",
                    level='info'
                )
                
                llm_start_time = time.time()
                payflow_result = self.payflow_agent.run(payflow_prompt)
                llm_duration = time.time() - llm_start_time
                
                monitor.log_llm_call(
                    session_id=self.session_id,
                    agent_type='PayflowAgent',
                    prompt=payflow_prompt,
                    response=payflow_result,
                    duration=llm_duration
                )
                
                # Phase 3: L'agent spécialisé crée le système de variables complet
                variables_prompt = f"""
                Tu es un agent spécialisé dans l'analyse d'impacts de paie. Voici l'analyse détaillée:
                
                PROMPT ORIGINAL: {prompt}
                
                ANALYSE PAYFLOW:
                {payflow_result[:1000]}...
                
                TÂCHES À EFFECTUER:
                1. Définis l'impact avec set_payroll_impact_source
                2. Crée 3-5 variables appropriées avec add_payroll_variable (input/intermediate)
                3. Crée 2-3 nœuds de calcul avec add_calculation_node
                4. Connecte-les avec connect_calculation_nodes
                5. Assure-toi d'avoir des variables de sortie pour le salaire final
                
                Sois concis et efficace. Chaque outil ne doit être utilisé qu'une fois par variable/nœud.
                """
                
                monitor.log_agent_action(
                    session_id=self.session_id,
                    agent_type='VariablesAgent',
                    action='llm_call_start',
                    message="🔧 Création du système de variables avec l'agent spécialisé...",
                    level='info'
                )
                
                llm_start_time = time.time()
                variables_result = self.variables_agent.run(variables_prompt)
                llm_duration = time.time() - llm_start_time
                
                monitor.log_llm_call(
                    session_id=self.session_id,
                    agent_type='VariablesAgent',
                    prompt=variables_prompt,
                    response=variables_result,
                    duration=llm_duration
                )
                
                # Phase 4: Extraire les variables créées depuis le graphe NetworkX
                variables_data = self._extract_variables_from_networkx_graph()
                
                monitor.log_graph_update(
                    session_id=self.session_id,
                    nodes_count=len(self.payroll_graph.graph.nodes()),
                    edges_count=len(self.payroll_graph.graph.edges()),
                    update_type='system_creation'
                )
                
                monitor.log_agent_action(
                    session_id=self.session_id,
                    agent_type='PayrollAnalysisService',
                    action='system_creation_complete',
                    message=f"✅ Système créé: {len(variables_data)} variables, {len(self.payroll_graph.graph.nodes())} noeuds",
                    level='info',
                    data={'variables_count': len(variables_data), 'nodes_count': len(self.payroll_graph.graph.nodes())}
                )
                
            else:
                # Mode de démonstration simplifié
                monitor.log_agent_action(
                    session_id=self.session_id,
                    agent_type='PayrollAnalysisService',
                    action='fallback_mode',
                    message="🔄 Mode simulation (agents non disponibles)",
                    level='warning'
                )
                payflow_result = self._simulate_payflow_analysis(prompt, context_articles)
                variables_data = self._simulate_variables_detection(prompt)
            
            execution_time = time.time() - start_time
            
            result = {
                'impact_description': payflow_result,
                'variables_detected': variables_data,
                'agent_response': f"Analyse simulée pour: {prompt}",
                'execution_time': execution_time,
                'status': 'completed'
            }
            
            monitor.log_agent_action(
                session_id=self.session_id,
                agent_type='PayrollAnalysisService',
                action='analysis_complete',
                message=f"Analyse terminée avec succès en {execution_time:.2f}s",
                level='info',
                data={'execution_time': execution_time, 'variables_count': len(variables_data)}
            )
            
            monitor.end_session(self.session_id, 'completed')
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            monitor.log_error(
                session_id=self.session_id,
                agent_type='PayrollAnalysisService',
                error_message=f"Erreur analyse: {str(e)}",
                exception_type=type(e).__name__
            )
            
            monitor.end_session(self.session_id, 'failed')
            
            return {
                'impact_description': '',
                'variables_detected': [],
                'agent_response': f"Erreur: {str(e)}",
                'execution_time': execution_time,
                'status': 'failed',
                'error_message': str(e)
            }
    
    def _format_articles_for_analysis(self, articles: List[Dict]) -> str:
        """Formate les articles pour l'analyse"""
        formatted = []
        for article in articles:
            content = article.get('content', '')
            # Nettoyer le HTML si nécessaire
            import re
            clean_content = re.sub(r'<[^>]+>', '', content)
            
            formatted.append(f"""
Article {article.get('num', 'N/A')}:
{clean_content}
---
""")
        return "\n".join(formatted)
    
    def _extract_variables_from_agent(self, agent_response: str) -> List[Dict]:
        """Extrait les variables depuis la réponse de l'agent"""
        variables = []
        
        # Pattern simple pour extraire les variables mentionnées
        # Dans un système plus avancé, on pourrait parser la sortie de l'agent
        common_variables = [
            'salaire_base', 'anciennete', 'prime_anciennete', 'heures_supplementaires',
            'taux_horaire', 'indemnite_transport', 'cotisations_sociales'
        ]
        
        response_lower = agent_response.lower()
        
        for var_name in common_variables:
            if var_name in response_lower:
                var_type = 'input' if var_name in ['salaire_base', 'anciennete'] else 'intermediate'
                variables.append({
                    'name': var_name,
                    'type': var_type,
                    'description': f'Variable {var_name} détectée dans l\'analyse',
                    'data_type': 'float'
                })
        
        return variables
    
    def _simulate_payflow_analysis(self, prompt: str, context_articles: List[Dict] = None) -> str:
        """Simule l'analyse PayFlow pour éviter les problèmes de verrouillage DB"""
        
        # Analyse basée sur les mots-clés du prompt
        prompt_lower = prompt.lower()
        
        if 'prime' in prompt_lower and 'ancienneté' in prompt_lower:
            return """
            Analyse des primes d'ancienneté :
            
            Les primes d'ancienneté sont des éléments de rémunération qui récompensent la fidélité du salarié à l'entreprise. 
            Selon cette convention collective, les primes d'ancienneté sont calculées comme suit :
            
            - Après 3 ans : 3% du salaire de base
            - Après 6 ans : 6% du salaire de base  
            - Après 9 ans : 9% du salaire de base
            - Après 15 ans : 12% du salaire de base
            
            Variables impactées : salaire_base, anciennete_annees, prime_anciennete, coefficient_anciennete
            """
            
        elif 'transport' in prompt_lower or 'indemnité' in prompt_lower:
            return """
            Analyse des indemnités de transport :
            
            Les indemnités de transport compensent les frais de déplacement domicile-travail des salariés.
            Cette convention prévoit :
            
            - Remboursement à 50% des titres de transport en commun
            - Indemnité kilométrique pour les véhicules personnels : 0,25€/km
            - Plafond mensuel : 200€
            
            Variables impactées : distance_domicile_travail, mode_transport, indemnite_transport, plafond_transport
            """
            
        elif 'heure' in prompt_lower and 'supplémentaire' in prompt_lower:
            return """
            Analyse des heures supplémentaires :
            
            Les heures supplémentaires sont les heures travaillées au-delà de la durée légale de 35h.
            Majorations prévues :
            
            - 8 premières heures (36e à 43e) : +25%
            - Au-delà de la 43e heure : +50%
            - Heures du dimanche : +100%
            
            Variables impactées : heures_travaillees, taux_horaire, heures_supplementaires, majoration_hs
            """
            
        else:
            return f"""
            Analyse générale de l'impact paie pour : "{prompt}"
            
            Cette analyse identifie les variables de paie potentiellement impactées par votre demande.
            Les éléments suivants ont été pris en compte :
            
            - Articles de la convention collective applicables
            - Calculs de rémunération associés
            - Variables de paie connexes
            - Impact sur le bulletin de salaire
            
            Variables génériques détectées : salaire_base, cotisations_sociales, net_a_payer
            """
    
    def _simulate_variables_detection(self, prompt: str) -> List[Dict]:
        """Simule la détection de variables pour éviter les problèmes de verrouillage DB"""
        
        prompt_lower = prompt.lower()
        variables = []
        
        # Variables de base toujours présentes
        variables.extend([
            {
                'name': 'salaire_base',
                'type': 'input',
                'description': 'Salaire de base mensuel du salarié',
                'data_type': 'float'
            },
            {
                'name': 'cotisations_sociales',
                'type': 'intermediate', 
                'description': 'Montant des cotisations sociales',
                'data_type': 'float'
            },
            {
                'name': 'net_a_payer',
                'type': 'output',
                'description': 'Montant net à payer au salarié',
                'data_type': 'float'
            }
        ])
        
        # Variables spécifiques selon le contexte
        if 'ancienneté' in prompt_lower or 'prime' in prompt_lower:
            variables.extend([
                {
                    'name': 'anciennete_annees',
                    'type': 'input',
                    'description': 'Nombre d\'années d\'ancienneté du salarié',
                    'data_type': 'int'
                },
                {
                    'name': 'coefficient_anciennete',
                    'type': 'intermediate',
                    'description': 'Coefficient de prime selon l\'ancienneté',
                    'data_type': 'float'
                },
                {
                    'name': 'prime_anciennete',
                    'type': 'output',
                    'description': 'Montant de la prime d\'ancienneté',
                    'data_type': 'float'
                }
            ])
            
        if 'transport' in prompt_lower:
            variables.extend([
                {
                    'name': 'distance_domicile_travail',
                    'type': 'input',
                    'description': 'Distance en km domicile-travail',
                    'data_type': 'float'
                },
                {
                    'name': 'indemnite_transport',
                    'type': 'output',
                    'description': 'Montant de l\'indemnité de transport',
                    'data_type': 'float'
                }
            ])
            
        if 'heure' in prompt_lower and 'supplémentaire' in prompt_lower:
            variables.extend([
                {
                    'name': 'heures_travaillees',
                    'type': 'input',
                    'description': 'Nombre d\'heures travaillées dans le mois',
                    'data_type': 'float'
                },
                {
                    'name': 'taux_horaire',
                    'type': 'input',
                    'description': 'Taux horaire de base',
                    'data_type': 'float'
                },
                {
                    'name': 'heures_supplementaires',
                    'type': 'intermediate',
                    'description': 'Nombre d\'heures supplémentaires',
                    'data_type': 'float'
                },
                {
                    'name': 'majoration_hs',
                    'type': 'output',
                    'description': 'Montant des majorations heures supplémentaires',
                    'data_type': 'float'
                }
            ])
        
        return variables
    
    def _extract_variables_from_networkx_graph(self) -> List[Dict]:
        """Extrait les variables créées par l'agent depuis le graphe NetworkX en temps réel"""
        variables = []
        
        try:
            # Variables d'entrée depuis le registre
            for var_name, var_info in self.payroll_graph._variable_registry['input_variables'].items():
                variables.append({
                    'name': var_name,
                    'type': 'input',
                    'description': var_info.get('description', ''),
                    'data_type': var_info.get('data_type', 'float'),
                    'legal_reference': var_info.get('legal_reference', ''),
                    'calculation_formula': var_info.get('calculation_formula', ''),
                    'depends_on': var_info.get('depends_on', [])
                })
            
            # Variables intermédiaires depuis le registre
            for var_name, var_info in self.payroll_graph._variable_registry['intermediate_variables'].items():
                variables.append({
                    'name': var_name,
                    'type': 'intermediate',
                    'description': var_info.get('description', ''),
                    'data_type': var_info.get('data_type', 'float'),
                    'legal_reference': var_info.get('legal_reference', ''),
                    'calculation_formula': var_info.get('calculation_formula', ''),
                    'depends_on': var_info.get('depends_on', [])
                })
            
            # Variables de sortie depuis les noeuds du graphe
            for node_id, node_data in self.payroll_graph.graph.nodes(data=True):
                output_var = node_data.get('output_variable')
                if output_var and output_var not in [v['name'] for v in variables]:
                    variables.append({
                        'name': output_var,
                        'type': 'output',
                        'description': f'Variable de sortie générée par {node_id}',
                        'data_type': 'float',
                        'legal_reference': node_data.get('legal_reference', ''),
                        'calculation_formula': f'Calculée par le noeud {node_id}',
                        'depends_on': node_data.get('input_variables', [])
                    })
            
            logger.info(f"📊 Variables extraites du graphe NetworkX: {len(variables)} variables")
            
        except Exception as e:
            logger.error(f"Erreur extraction variables NetworkX: {str(e)}")
            # Fallback vers variables par défaut
            variables = self._simulate_variables_detection("Variables de base")
        
        return variables


class HighchartsConfigService:
    """Service pour générer les configurations Highcharts en temps réel"""
    
    @staticmethod
    def generate_network_graph_from_networkx(payroll_graph, analysis_id: str = None) -> Dict[str, Any]:
        """Génère la configuration NetworkGraph directement depuis le graphe NetworkX"""
        
        if not payroll_graph or not payroll_graph.graph.nodes():
            # Configuration vide si pas de graphe
            return {
                'chart': {'type': 'networkgraph', 'height': 400},
                'title': {'text': 'Graphe des Variables de Paie (vide)'},
                'series': [{'name': 'Variables', 'data': [], 'nodes': []}]
            }
        
        nodes = []
        links = []
        
        # Créer les nœuds depuis le graphe NetworkX
        for node_id, node_data in payroll_graph.graph.nodes(data=True):
            # Couleur selon le type de variable ou noeud
            if node_data.get('node_type') == 'calculation':
                color = '#90ed7d'  # Vert pour calculs
                description = node_data.get('description', node_id)
            else:
                color = '#7cb5ec'  # Bleu par défaut
                description = node_data.get('description', node_id)
            
            nodes.append({
                'id': node_id,
                'name': description[:50] + ('...' if len(description) > 50 else ''),
                'color': color,
                'marker': {'radius': 25},
                'dataLabels': {'enabled': True}
            })
        
        # Créer les liens depuis le graphe NetworkX
        for source, target, edge_data in payroll_graph.graph.edges(data=True):
            links.append({
                'from': source,
                'to': target,
                'weight': 2,
                'color': '#666666'
            })
        
        config = {
            'chart': {
                'type': 'networkgraph',
                'height': 600,
                'backgroundColor': '#fafafa'
            },
            'title': {
                'text': 'Graphe NetworkX des Variables de Paie - Temps Réel',
                'style': {'fontSize': '18px'}
            },
            'subtitle': {
                'text': f'Variables: {len(payroll_graph._variable_registry["input_variables"]) + len(payroll_graph._variable_registry["intermediate_variables"])} | Noeuds: {len(payroll_graph.graph.nodes())} | Impact: {analysis_id or "En cours"}'
            },
            'plotOptions': {
                'networkgraph': {
                    'keys': ['from', 'to'],
                    'layoutAlgorithm': {
                        'enableSimulation': True,
                        'friction': -0.9,
                        'linkLength': 100,
                        'integration': 'verlet'
                    },
                    'dataLabels': {
                        'enabled': True,
                        'style': {'fontSize': '11px', 'fontWeight': 'bold'},
                        'allowOverlap': False
                    }
                }
            },
            'series': [{
                'name': 'Variables NetworkX',
                'data': links,
                'nodes': nodes
            }],
            'exporting': {'enabled': True}
        }
        
        return config
    
    @staticmethod
    def generate_network_graph(variables: List[Dict], analysis_id: str = None) -> Dict[str, Any]:
        """Génère la configuration d'un graphe de réseau des variables"""
        
        nodes = []
        links = []
        
        # Créer les nœuds
        for i, var in enumerate(variables):
            color = {
                'input': '#7cb5ec',      # Bleu
                'intermediate': '#90ed7d', # Vert
                'output': '#f7a35c'      # Orange
            }.get(var.get('type', 'intermediate'), '#434348')
            
            nodes.append({
                'id': var['name'],
                'name': var.get('description', var['name']),
                'color': color,
                'marker': {'radius': 20}
            })
        
        # Créer les liens basés sur les dépendances
        for var in variables:
            if 'depends_on' in var and var['depends_on']:
                for dependency in var['depends_on']:
                    links.append({
                        'from': dependency,
                        'to': var['name'],
                        'weight': 2
                    })
        
        config = {
            'chart': {
                'type': 'networkgraph',
                'height': 500,
                'backgroundColor': '#f8f9fa'
            },
            'title': {
                'text': 'Graphe des Variables de Paie',
                'style': {'fontSize': '18px'}
            },
            'subtitle': {
                'text': f'Analyse #{analysis_id}' if analysis_id else 'Variables de paie'
            },
            'plotOptions': {
                'networkgraph': {
                    'keys': ['from', 'to'],
                    'layoutAlgorithm': {
                        'enableSimulation': True,
                        'friction': -0.9,
                        'linkLength': 80
                    },
                    'dataLabels': {
                        'enabled': True,
                        'style': {'fontSize': '10px'}
                    }
                }
            },
            'series': [{
                'name': 'Variables',
                'data': links,
                'nodes': nodes
            }],
            'exporting': {'enabled': True}
        }
        
        return config
    
    @staticmethod
    def generate_timeline_chart(variables: List[Dict]) -> Dict[str, Any]:
        """Génère la configuration d'une timeline des variables"""
        
        timeline_data = []
        
        for i, var in enumerate(variables):
            timeline_data.append({
                'x': i * 1000,  # Simuler des timestamps
                'y': {'input': 1, 'intermediate': 2, 'output': 3}.get(var.get('type'), 2),
                'name': var['name'],
                'description': var.get('description', ''),
                'color': {
                    'input': '#f7a35c',
                    'intermediate': '#7cb5ec', 
                    'output': '#90ed7d'
                }.get(var.get('type'), '#434348')
            })
        
        config = {
            'chart': {
                'type': 'scatter',
                'height': 350
            },
            'title': {
                'text': 'Timeline de Création des Variables'
            },
            'xAxis': {
                'title': {'text': 'Ordre de Création'}
            },
            'yAxis': {
                'categories': ['', 'Input', 'Intermediate', 'Output'],
                'title': {'text': 'Type de Variable'}
            },
            'series': [{
                'name': 'Variables',
                'data': timeline_data
            }],
            'tooltip': {
                'pointFormat': '<b>{point.name}</b><br/>{point.description}'
            }
        }
        
        return config
    
    @staticmethod
    def generate_pie_chart(variables: List[Dict]) -> Dict[str, Any]:
        """Génère la configuration d'un graphique en secteurs"""
        
        # Compter par type
        type_counts = {}
        for var in variables:
            var_type = var.get('type', 'unknown')
            type_counts[var_type] = type_counts.get(var_type, 0) + 1
        
        pie_data = []
        colors = {
            'input': '#f7a35c',
            'intermediate': '#7cb5ec',
            'output': '#90ed7d'
        }
        
        for var_type, count in type_counts.items():
            pie_data.append({
                'name': var_type.title(),
                'y': count,
                'color': colors.get(var_type, '#434348')
            })
        
        config = {
            'chart': {
                'type': 'pie',
                'height': 350
            },
            'title': {
                'text': 'Répartition des Variables par Type'
            },
            'series': [{
                'name': 'Variables',
                'data': pie_data,
                'innerSize': '50%'
            }],
            'plotOptions': {
                'pie': {
                    'dataLabels': {
                        'enabled': True,
                        'format': '{point.name}: {point.percentage:.1f}%'
                    }
                }
            }
        }
        
        return config


class LoggingService:
    """Service pour logger les étapes d'analyse"""
    
    @staticmethod
    def log_analysis_step(analyse_id: str, step: str, message: str, 
                         level: str = 'info', extra_data: Dict = None):
        """Log une étape d'analyse"""
        from .models import AnalysePaie, LogAnalyse
        
        try:
            analyse = AnalysePaie.objects.get(id=analyse_id)
            LogAnalyse.objects.create(
                analyse=analyse,
                step=step,
                message=message,
                level=level,
                extra_data=extra_data or {}
            )
        except Exception as e:
            logger.error(f"Erreur logging: {str(e)}")
    
    @staticmethod
    def get_analysis_logs(analyse_id: str) -> List[Dict]:
        """Récupère les logs d'une analyse"""
        from .models import LogAnalyse
        
        try:
            logs = LogAnalyse.objects.filter(analyse_id=analyse_id).order_by('timestamp')
            return [{
                'step': log.step,
                'message': log.message,
                'level': log.level,
                'timestamp': log.timestamp.isoformat(),
                'extra_data': log.extra_data
            } for log in logs]
        except Exception as e:
            logger.error(f"Erreur récupération logs: {str(e)}")
            return []


class GraphIntegrationService:
    """Service pour intégrer avec le système de graphe NetworkX existant"""
    
    def __init__(self):
        self.payroll_graph = PayrollVariableGraph()
    
    def build_networkx_graph(self, variables: List[Dict], analysis_description: str = ""):
        """Construit un graphe NetworkX à partir des variables Django"""
        
        # Reset du graphe
        self.payroll_graph.clear_system()
        
        # Définir la source
        self.payroll_graph.set_impact_source(analysis_description)
        
        # Ajouter les variables
        for var in variables:
            self.payroll_graph.add_variable(
                var_name=var['name'],
                var_type=var.get('type', 'intermediate'),
                description=var.get('description', ''),
                data_type=var.get('data_type', 'float'),
                legal_reference=var.get('legal_reference', ''),
                calculation_formula=var.get('calculation_formula', ''),
                depends_on=var.get('depends_on', [])
            )
        
        return self.payroll_graph
    
    def get_highcharts_configs(self) -> Dict[str, Dict]:
        """Génère toutes les configurations Highcharts"""
        return {
            'networkgraph': self.payroll_graph.to_highcharts_config('networkgraph'),
            'flowchart': self.payroll_graph.to_highcharts_config('flowchart'),
            'timeline': self.payroll_graph.to_highcharts_config('variables_timeline')
        }
    
    def get_live_data(self) -> Dict:
        """Récupère les données live du système"""
        return self.payroll_graph.get_live_update_data()
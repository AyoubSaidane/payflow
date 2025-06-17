"""
Service de monitoring en temps réel des agents IA
Capture et diffuse les actions des agents pour le debugging et le suivi
"""

import json
import time
import threading
from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import deque
import logging

logger = logging.getLogger(__name__)

class AgentMonitor:
    """Monitor singleton pour suivre les actions des agents en temps réel"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, 'initialized'):
            self.events = deque(maxlen=1000)  # Garder les 1000 derniers événements
            self.subscribers = []  # Liste des callbacks pour les mises à jour live
            self.active_sessions = {}  # Sessions d'analyse actives
            self.lock = threading.Lock()
            self.initialized = True
    
    def start_session(self, session_id: str, description: str, user_id: str = None):
        """Démarre une nouvelle session de monitoring"""
        with self.lock:
            self.active_sessions[session_id] = {
                'id': session_id,
                'description': description,
                'user_id': user_id,
                'started_at': datetime.now(),
                'status': 'active',
                'events_count': 0,
                'last_activity': datetime.now()
            }
            
            self._add_event({
                'session_id': session_id,
                'type': 'session_start',
                'message': f'Nouvelle session démarrée: {description}',
                'level': 'info',
                'timestamp': datetime.now().isoformat(),
                'data': {'description': description, 'user_id': user_id}
            })
    
    def end_session(self, session_id: str, status: str = 'completed'):
        """Termine une session de monitoring"""
        with self.lock:
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['status'] = status
                self.active_sessions[session_id]['ended_at'] = datetime.now()
                
                self._add_event({
                    'session_id': session_id,
                    'type': 'session_end',
                    'message': f'Session terminée avec statut: {status}',
                    'level': 'info',
                    'timestamp': datetime.now().isoformat(),
                    'data': {'status': status}
                })
    
    def log_agent_action(self, session_id: str, agent_type: str, action: str, 
                        message: str, level: str = 'info', data: Dict = None):
        """Log une action d'agent"""
        
        event = {
            'session_id': session_id,
            'type': 'agent_action',
            'agent_type': agent_type,
            'action': action,
            'message': message,
            'level': level,
            'timestamp': datetime.now().isoformat(),
            'data': data or {}
        }
        
        with self.lock:
            # Mettre à jour la session active
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['events_count'] += 1
                self.active_sessions[session_id]['last_activity'] = datetime.now()
            
            self._add_event(event)
    
    def log_llm_call(self, session_id: str, agent_type: str, prompt: str, 
                     response: str = None, duration: float = None, 
                     tokens_used: int = None):
        """Log un appel LLM spécifique"""
        
        data = {
            'prompt_length': len(prompt),
            'prompt_preview': prompt[:200] + "..." if len(prompt) > 200 else prompt
        }
        
        if response:
            data['response_length'] = len(response)
            data['response_preview'] = response[:200] + "..." if len(response) > 200 else response
        
        if duration:
            data['duration_seconds'] = duration
            
        if tokens_used:
            data['tokens_used'] = tokens_used
        
        self.log_agent_action(
            session_id=session_id,
            agent_type=agent_type,
            action='llm_call',
            message=f'Appel LLM - {len(prompt)} caractères',
            level='debug',
            data=data
        )
    
    def log_variable_creation(self, session_id: str, variable_name: str, 
                            variable_type: str, formula: str = None):
        """Log la création d'une variable de paie"""
        
        data = {
            'variable_name': variable_name,
            'variable_type': variable_type,
            'formula': formula
        }
        
        self.log_agent_action(
            session_id=session_id,
            agent_type='payroll_agent',
            action='variable_creation',
            message=f'Variable créée: {variable_name} ({variable_type})',
            level='info',
            data=data
        )
    
    def log_graph_update(self, session_id: str, nodes_count: int, edges_count: int, 
                        update_type: str = 'modification'):
        """Log une mise à jour du graphe NetworkX"""
        
        data = {
            'nodes_count': nodes_count,
            'edges_count': edges_count,
            'update_type': update_type
        }
        
        self.log_agent_action(
            session_id=session_id,
            agent_type='networkx_graph',
            action='graph_update',
            message=f'Graphe mis à jour: {nodes_count} nœuds, {edges_count} arêtes',
            level='debug',
            data=data
        )
    
    def log_error(self, session_id: str, agent_type: str, error_message: str, 
                  exception_type: str = None, traceback_info: str = None):
        """Log une erreur d'agent"""
        
        data = {
            'error_message': error_message,
            'exception_type': exception_type,
            'traceback': traceback_info
        }
        
        self.log_agent_action(
            session_id=session_id,
            agent_type=agent_type,
            action='error',
            message=f'Erreur: {error_message}',
            level='error',
            data=data
        )
    
    def _add_event(self, event: Dict):
        """Ajoute un événement au monitoring"""
        self.events.append(event)
        
        # Notifier les abonnés
        for callback in self.subscribers:
            try:
                callback(event)
            except Exception as e:
                logger.error(f"Erreur notification subscriber: {e}")
    
    def subscribe(self, callback):
        """S'abonne aux événements en temps réel"""
        self.subscribers.append(callback)
    
    def unsubscribe(self, callback):
        """Se désabonne des événements"""
        if callback in self.subscribers:
            self.subscribers.remove(callback)
    
    def get_recent_events(self, limit: int = 100, session_id: str = None, 
                         level: str = None) -> List[Dict]:
        """Récupère les événements récents avec filtrage optionnel"""
        
        with self.lock:
            events = list(self.events)
        
        # Filtrer par session
        if session_id:
            events = [e for e in events if e.get('session_id') == session_id]
        
        # Filtrer par niveau
        if level:
            events = [e for e in events if e.get('level') == level]
        
        # Limiter le nombre de résultats
        return events[-limit:]
    
    def get_active_sessions(self) -> Dict[str, Dict]:
        """Récupère les sessions actives"""
        with self.lock:
            return dict(self.active_sessions)
    
    def get_session_stats(self, session_id: str) -> Dict:
        """Récupère les statistiques d'une session"""
        
        with self.lock:
            session = self.active_sessions.get(session_id)
            if not session:
                return {}
            
            # Compter les événements par type
            session_events = [e for e in self.events if e.get('session_id') == session_id]
            
            stats = {
                'total_events': len(session_events),
                'events_by_type': {},
                'events_by_level': {},
                'agents_involved': set(),
                'duration_seconds': 0
            }
            
            for event in session_events:
                # Par type
                event_type = event.get('type', 'unknown')
                stats['events_by_type'][event_type] = stats['events_by_type'].get(event_type, 0) + 1
                
                # Par niveau
                level = event.get('level', 'info')
                stats['events_by_level'][level] = stats['events_by_level'].get(level, 0) + 1
                
                # Agents impliqués
                if 'agent_type' in event:
                    stats['agents_involved'].add(event['agent_type'])
            
            # Convertir set en list pour JSON
            stats['agents_involved'] = list(stats['agents_involved'])
            
            # Calculer la durée
            if session.get('ended_at'):
                duration = session['ended_at'] - session['started_at']
                stats['duration_seconds'] = duration.total_seconds()
            else:
                duration = datetime.now() - session['started_at']
                stats['duration_seconds'] = duration.total_seconds()
            
            return stats
    
    def clear_old_events(self, max_age_hours: int = 24):
        """Nettoie les anciens événements"""
        
        cutoff_time = datetime.now().timestamp() - (max_age_hours * 3600)
        
        with self.lock:
            # Filtrer les événements récents
            recent_events = []
            for event in self.events:
                event_time = datetime.fromisoformat(event['timestamp']).timestamp()
                if event_time > cutoff_time:
                    recent_events.append(event)
            
            self.events.clear()
            self.events.extend(recent_events)


# Instance globale du monitor
monitor = AgentMonitor()


class MonitoringMixin:
    """Mixin pour ajouter facilement le monitoring aux services"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.monitor = monitor
        self.session_id = None
    
    def start_monitoring(self, description: str, user_id: str = None):
        """Démarre le monitoring pour cette instance"""
        self.session_id = f"{self.__class__.__name__}_{int(time.time())}"
        self.monitor.start_session(self.session_id, description, user_id)
        return self.session_id
    
    def log_action(self, action: str, message: str, level: str = 'info', data: Dict = None):
        """Log une action de ce service"""
        if self.session_id:
            self.monitor.log_agent_action(
                session_id=self.session_id,
                agent_type=self.__class__.__name__,
                action=action,
                message=message,
                level=level,
                data=data
            )
    
    def log_error(self, error_message: str, exception: Exception = None):
        """Log une erreur de ce service"""
        if self.session_id:
            traceback_info = None
            exception_type = None
            
            if exception:
                exception_type = type(exception).__name__
                import traceback
                traceback_info = traceback.format_exc()
            
            self.monitor.log_error(
                session_id=self.session_id,
                agent_type=self.__class__.__name__,
                error_message=error_message,
                exception_type=exception_type,
                traceback_info=traceback_info
            )
    
    def end_monitoring(self, status: str = 'completed'):
        """Termine le monitoring pour cette instance"""
        if self.session_id:
            self.monitor.end_session(self.session_id, status)


def log_agent_decorator(agent_type: str = None):
    """Décorateur pour automatiquement logger les appels de méthodes"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Obtenir le nom de la classe si disponible
            class_name = agent_type
            if not class_name and len(args) > 0 and hasattr(args[0], '__class__'):
                class_name = args[0].__class__.__name__
            
            # Obtenir session_id si disponible
            session_id = None
            if len(args) > 0 and hasattr(args[0], 'session_id'):
                session_id = args[0].session_id
            
            start_time = time.time()
            
            try:
                # Log début
                if session_id:
                    monitor.log_agent_action(
                        session_id=session_id,
                        agent_type=class_name or 'unknown',
                        action='method_call',
                        message=f'Début {func.__name__}',
                        level='debug'
                    )
                
                # Exécuter la fonction
                result = func(*args, **kwargs)
                
                # Log fin avec succès
                duration = time.time() - start_time
                if session_id:
                    monitor.log_agent_action(
                        session_id=session_id,
                        agent_type=class_name or 'unknown',
                        action='method_complete',
                        message=f'{func.__name__} terminé en {duration:.2f}s',
                        level='debug',
                        data={'duration': duration}
                    )
                
                return result
                
            except Exception as e:
                # Log erreur
                duration = time.time() - start_time
                if session_id:
                    monitor.log_error(
                        session_id=session_id,
                        agent_type=class_name or 'unknown',
                        error_message=f'Erreur dans {func.__name__}: {str(e)}',
                        exception_type=type(e).__name__
                    )
                raise
        
        return wrapper
    return decorator
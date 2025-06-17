# 🚀 PayFlow - IA pour l'Analyse de Variables de Paie

[![Django](https://img.shields.io/badge/Django-4.2+-green.svg)](https://djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Application Django avancée pour l'analyse automatisée des variables de paie utilisant des agents IA et des visualisations interactives en temps réel.**

---

## 🎯 Vue d'ensemble

PayFlow révolutionne l'analyse des conventions collectives françaises en automatisant la détection et la création de variables de paie. Grâce à des agents IA sophistiqués et une interface web moderne, transformez vos documents légaux en systèmes de paie intelligents.

### ✨ Fonctionnalités Principales

| 🤖 **Agents IA** | 📊 **Visualisations** | 🔍 **Monitoring** |
|:-----------------|:----------------------|:------------------|
| Analyse contextuelle automatique | Graphiques Highcharts interactifs | Dashboard temps réel |
| Détection de variables de paie | Relations NetworkGraph | Suivi des agents IA |
| Intégration NetworkX | Timeline des créations | Métriques de performance |
| Claude AI pour l'analyse légale | Graphiques secteurs | États et statistiques |

---

## 🚀 Installation Rapide

### Méthode automatique (recommandée)

```bash
# 1. Cloner le repository
git clone https://github.com/AyoubSaidane/payflow.git
cd payflow

# 2. Lancement automatique
./start_app.sh
```

### Méthode manuelle

```bash
# 1. Environnement virtuel
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# ou venv\Scripts\activate  # Windows

# 2. Installation des dépendances
pip install -r requirements.txt

# 3. Configuration
cp .env.example .env
# Éditer .env avec votre clé API Anthropic

# 4. Base de données
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

# 5. Lancement
python manage.py runserver
```

---

## ⚙️ Configuration

### Variables d'environnement requises

**⚠️ IMPORTANT : Configuration des clés API**

1. **Copiez le fichier d'exemple :**
   ```bash
   cp .env.example .env
   ```

2. **Éditez le fichier `.env` et configurez vos clés :**
   ```env
   # 🔑 API Configuration - REMPLACEZ PAR VOS VRAIES CLÉS
   ANTHROPIC_API_KEY=your-anthropic-api-key-here
   
   # ⚙️ Django Configuration - GÉNÉREZ UNE CLÉ SECRÈTE UNIQUE
   SECRET_KEY=your-django-secret-key-here
   DEBUG=True
   
   # 🌐 Server Configuration
   ALLOWED_HOSTS=localhost,127.0.0.1
   ```

3. **Obtenez votre clé Anthropic API :**
   - Rendez-vous sur [console.anthropic.com](https://console.anthropic.com)
   - Créez un compte et générez une clé API
   - Remplacez `your-anthropic-api-key-here` par votre vraie clé

4. **Générez une clé secrète Django :**
   ```python
   # Dans un terminal Python
   from django.core.management.utils import get_random_secret_key
   print(get_random_secret_key())
   ```

**🔒 Sécurité :** Ne commitez jamais vos vraies clés API dans le repository !

---

## 🌐 Interface Web

| URL | Description | Fonctionnalité |
|:----|:------------|:---------------|
| [`http://127.0.0.1:8000/`](http://127.0.0.1:8000/) | **Dashboard principal** | Vue d'ensemble et accès rapide |
| [`http://127.0.0.1:8000/conventions/`](http://127.0.0.1:8000/conventions/) | **Gestion des conventions** | Import, analyse, résultats |
| [`http://127.0.0.1:8000/monitoring/`](http://127.0.0.1:8000/monitoring/) | **Monitoring temps réel** | Suivi des agents IA |
| [`http://127.0.0.1:8000/admin/`](http://127.0.0.1:8000/admin/) | **Administration** | Gestion utilisateurs et données |

---

## 🔄 Workflow d'Utilisation

### 1. 📥 Import Convention
```
Légifrance ID → API Gouvernementale → Articles analysables
```

### 2. 🤖 Analyse IA
```
Question utilisateur → PayFlow Agent → Analyse contextuelle → Variables détectées
```

### 3. 📊 Visualisation
```
Variables créées → Highcharts → Graphiques interactifs → Export JSON
```

### 4. 🔍 Monitoring
```
Actions agents → Server-Sent Events → Dashboard temps réel → Statistiques
```

---

## 🏗️ Architecture Technique

```
┌─────────────────────────────────────────────────────┐
│                   🌐 Django Web App                │
├─────────────────────────────────────────────────────┤
│  📊 Views & Templates    │  🔍 Monitoring System    │
│  🤖 AI Services          │  📡 Server-Sent Events   │
│  🗄️ Models & Forms       │  📈 Real-time Dashboard   │
├─────────────────────────────────────────────────────┤
│               🧠 AI Agents Layer                    │
│  PayFlow Agent           │  PayrollVariable Agent   │
│  (Convention Analysis)   │  (Variable Creation)      │
├─────────────────────────────────────────────────────┤
│               🌍 External APIs                      │
│  🇫🇷 Légifrance API       │  🤖 Anthropic Claude     │
│  (Government Data)       │  (AI Processing)          │
└─────────────────────────────────────────────────────┘
```

---

## 📁 Structure du Projet

```
payflow/
├── 🚀 manage.py                    # Point d'entrée Django
├── 📋 requirements.txt             # Dépendances Python
├── ⚙️ .env.example                 # Configuration exemple
├── 🏃 start_app.sh                 # Script de lancement
│
├── 🏢 app/                         # Application principale
│   ├── 📊 models.py                # Modèles de données
│   ├── 🎮 views.py                 # Vues et API
│   ├── 🤖 services.py              # Services IA
│   ├── 🔍 monitoring.py            # Système monitoring
│   ├── 📝 templates/               # Templates HTML
│   └── 🗄️ migrations/             # Migrations DB
│
├── 🏛️ unaite_project/             # Configuration Django
│   ├── ⚙️ settings.py              # Paramètres
│   ├── 🛣️ urls.py                 # Routing
│   └── 🌐 wsgi.py                 # WSGI config
│
├── 🤖 payflow_agents.py           # Agent d'analyse
├── 📊 payroll_variable_agent.py   # Agent variables
└── 🌍 import_cc.py                # Module Légifrance
```

---

## 🛠️ API Endpoints

### 🔍 Monitoring Temps Réel
```http
GET  /api/monitoring/stream/        # Server-Sent Events
GET  /api/monitoring/events/        # Liste des événements  
GET  /api/monitoring/sessions/      # Sessions actives
```

### 📊 Graphiques Highcharts
```http
GET  /api/analyses/{id}/charts/networkgraph/  # Configuration réseau
GET  /api/analyses/{id}/charts/timeline/      # Configuration timeline  
GET  /api/analyses/{id}/charts/pie/           # Configuration secteurs
```

### 🔄 Analyses
```http
POST /api/quick-analysis/           # Analyse rapide AJAX
GET  /analyses/{id}/export/         # Export JSON complet
```

---

## 💡 Exemples d'Utilisation

### 🔍 Analyses typiques
- *"Analyser les primes d'ancienneté dans cette convention"*
- *"Calculer les heures supplémentaires et leurs majorations"*  
- *"Identifier les indemnités de transport et conditions"*
- *"Rechercher les congés payés et modalités de calcul"*

### 📈 Résultats obtenus
- Variables de paie structurées (input/intermediate/output)
- Graphiques de dépendances interactifs
- Formules de calcul automatisées  
- Export JSON pour intégration

---

## 🔧 Technologies Utilisées

| Catégorie | Technologies |
|:----------|:-------------|
| **Backend** | Django 4.2+, Python 3.8+ |
| **IA/ML** | Anthropic Claude, smolagents, NetworkX |
| **Frontend** | Bootstrap 5, Tabler, Highcharts |
| **Base de données** | SQLite (dev), PostgreSQL (prod) |
| **Temps réel** | Server-Sent Events |
| **API externes** | Légifrance (Gouvernement français) |

---

## 🤝 Contribution

1. **Fork** le projet
2. **Créer** une branche feature (`git checkout -b feature/amazing-feature`)
3. **Commit** les changements (`git commit -m 'Add amazing feature'`)
4. **Push** sur la branche (`git push origin feature/amazing-feature`)
5. **Ouvrir** une Pull Request

---

## 🆘 Support & Documentation

- **🐛 Issues** : [GitHub Issues](https://github.com/AyoubSaidane/payflow/issues)
- **📚 Documentation** : Voir les commentaires dans le code
- **💬 Support** : Créer une issue pour toute question

---

## 📄 Licence

Ce projet est sous licence **MIT**. Voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

<div align="center">

**Développé avec ❤️ pour simplifier l'analyse des conventions collectives françaises**

[![GitHub stars](https://img.shields.io/github/stars/AyoubSaidane/payflow.svg?style=social)](https://github.com/AyoubSaidane/payflow/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/AyoubSaidane/payflow.svg?style=social)](https://github.com/AyoubSaidane/payflow/network)

</div>
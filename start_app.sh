#!/bin/bash

# 🚀 PayFlow - Script de lancement automatique

echo "🚀 PayFlow - Démarrage de l'application"
echo "======================================="

# Vérifier que nous sommes dans le bon répertoire
if [ ! -f "manage.py" ]; then
    echo "❌ Erreur: manage.py non trouvé. Lancez ce script depuis le répertoire racine du projet."
    exit 1
fi

# Vérifier les variables d'environnement
if [ ! -f ".env" ]; then
    echo "⚠️  Fichier .env non trouvé. Création depuis .env.example..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "📝 Veuillez éditer le fichier .env avec vos clés API"
    else
        echo "❌ Fichier .env.example non trouvé"
        exit 1
    fi
fi

# Vérifier l'environnement virtuel
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠️  Environnement virtuel non activé"
    if [ -d "venv" ]; then
        echo "🔄 Activation de l'environnement virtuel..."
        source venv/bin/activate
    else
        echo "📦 Création de l'environnement virtuel..."
        python3 -m venv venv
        source venv/bin/activate
    fi
fi

# Installer les dépendances
echo "📦 Installation des dépendances..."
pip install -r requirements.txt

# Migrations de la base de données
echo "🗄️  Préparation de la base de données..."
python manage.py makemigrations
python manage.py migrate

# Créer un superutilisateur si nécessaire
echo "👤 Vérification du superutilisateur..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Création du superutilisateur admin...')
    User.objects.create_superuser('admin', 'admin@payflow.dev', 'admin123')
    print('✅ Superutilisateur créé: admin / admin123')
else:
    print('✅ Superutilisateur déjà existant')
"

echo ""
echo "🎉 Application prête !"
echo "======================================="
echo "🌐 Interface web: http://127.0.0.1:8000/"
echo "🔧 Administration: http://127.0.0.1:8000/admin/"
echo "📊 Monitoring: http://127.0.0.1:8000/monitoring/"
echo "👤 Admin: admin / admin123"
echo ""
echo "🚀 Démarrage du serveur..."

# Lancer le serveur Django
python manage.py runserver
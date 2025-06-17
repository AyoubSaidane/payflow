import datetime
import requests


def get_access_token():
    """Obtient le token d'accès pour l'API Piste"""
    client_id = "72925fbb-8853-4c12-b864-884b31b06dda"
    client_secret = "097cdd86-df0f-41c1-b566-c63bb803f1a1"
    
    token_url = "https://sandbox-oauth.piste.gouv.fr/api/oauth/token"
    
    payload = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": "openid"
    }
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    
    response = requests.post(token_url, data=payload, headers=headers)
    token_data = response.json()
    return token_data["access_token"]


def get_convention_data(convention_id, access_token):
    """Récupère les données de la convention collective"""
    url = "https://sandbox-api.piste.gouv.fr/dila/legifrance/lf-engine-app/consult/kaliText"
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "id": convention_id
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()


def timestamp_to_year(timestamp):
    """Convertit un timestamp en millisecondes vers une année"""
    # Convertir de millisecondes vers secondes
    timestamp_seconds = timestamp / 1000
    # Convertir vers datetime
    date = datetime.datetime.fromtimestamp(timestamp_seconds)
    return date.year


def filter_articles_by_year(articles, target_year=2999):
    """Filtre les articles dont l'année de dateFin correspond à l'année cible"""
    filtered_articles = []
    
    for article in articles:
        if 'dateFin' in article:
            year = timestamp_to_year(article['dateFin'])
            if year == target_year:
                filtered_articles.append(article)
    
    return filtered_articles


def extract_articles_recursive(section, articles_list=None):
    """Extrait récursivement tous les articles d'une section"""
    if articles_list is None:
        articles_list = []
    
    # Si la section contient des articles, les ajouter à la liste
    if 'articles' in section:
        for article in section['articles']:
                articles_list.append(article)
    
    # Si la section contient des sous-sections, les parcourir récursivement
    if 'sections' in section:
        for sous_section in section['sections']:
            extract_articles_recursive(sous_section, articles_list)
    
    return articles_list


def get_all_articles(convention_id, filter_year=2999):
    """Fonction principale qui retourne la liste de tous les articles"""
    # Obtenir le token d'accès
    access_token = get_access_token()
    
    # Récupérer les données de la convention
    convention_data = get_convention_data(convention_id, access_token)
    
    # Extraire tous les articles récursivement
    all_articles = []
    
    # Parcourir toutes les sections racines
    if 'sections' in convention_data:
        for section in convention_data['sections']:
            extract_articles_recursive(section, all_articles)
    
    # Vérifier s'il y a des articles à la racine
    if 'articles' in convention_data:
        for article in convention_data['articles']:
            all_articles.append(article)
    
    # Filtrer par année (None pour désactiver le filtrage)
    if filter_year is not None:
        all_articles = filter_articles_by_year(all_articles, filter_year)
    
    return all_articles


if __name__ == "__main__":
    # Exemple d'utilisation
    convention_id = "KALITEXT000044253019"
    
    # Par défaut, récupère les articles avec dateFin en 2999
    articles = get_all_articles(convention_id)
    print(f"Nombre d'articles actifs (dateFin 2999) : {len(articles)}")
    
    # Pour avoir tous les articles sans filtrage
    all_articles = get_all_articles(convention_id, filter_year=None)
    print(f"Nombre total d'articles (sans filtrage) : {len(all_articles)}")
    
    # Afficher quelques exemples d'articles actifs
    for i, article in enumerate(articles[:3]):
        date_fin = timestamp_to_year(article.get('dateFin', 0))
        print(f"Article {i+1}: {article.get('title', 'Sans titre')} (dateFin: {date_fin})")

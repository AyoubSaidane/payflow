import os
import re
from typing import Dict, List

from smolagents import (
    Tool, ToolCallingAgent, LiteLLMModel
)
from import_cc import get_all_articles


# ------------ 2. Tools ------------------------------------
class AnalyseArticleTool(Tool):
    name = "analyse_article"
    description = (
        "Analyse un ou plusieurs articles de convention collective et retourne leur impact "
        "détaillé et structuré sur la fiche de paie (primes, indemnités, règles de calcul)"
    )
    inputs = {"articles_data": {"type": "string", "description": "Données des articles à analyser (texte ou JSON avec métadonnées)"}}
    output_type = "string"

    def __init__(self):
        super().__init__()
        # Utilise Claude pour une compatibilité totale
        self.model = LiteLLMModel(
            model_id="anthropic/claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
        )

    def forward(self, articles_data: str) -> str:
        prompt = (
            "En tant qu'expert en droit du travail français, analyse ces articles "
            "de convention collective et explique clairement leur impact sur la fiche de paie.\n\n"
            f"ARTICLES À ANALYSER :\n{articles_data}\n\n"
            "CONSIGNE : Explique en français clair et structuré l'impact sur la fiche de paie :\n\n"
            "## 💰 IMPACT SUR LA FICHE DE PAIE\n\n"
            "### 🎯 Primes et Indemnités\n"
            "- Décris chaque prime/indemnité identifiée avec montant exact, périodicité et conditions\n\n"
            "### 📊 Règles de Calcul\n"
            "- Explique les formules de calcul, taux, seuils et barèmes applicables\n\n"
            "### ⚖️ Conditions d'Application\n"
            "- Précise qui est concerné, dans quelles circonstances, avec quelles modalités\n\n"
            "### 🕐 Périodicité et Modalités\n"
            "- Indique quand ces éléments sont versés (mensuel, annuel, ponctuel...)\n\n"
            "### 💡 Impact Concret\n"
            "- Résume l'effet net sur le salaire brut/net avec exemples chiffrés si possible\n\n"
            "IMPORTANT : Sois précis sur tous les montants, taux et conditions. Utilise un langage professionnel mais accessible."
        )
        try:
            response = self.model([{"role": "user", "content": prompt}])
            return str(response)
        except Exception as e:
            return f"Erreur lors de l'analyse : {str(e)}"


class SearchConventionTool(Tool):
    name = "search_convention"
    description = (
        "Recherche TOUS les articles pertinents à une variable/prime/indemnité dans TOUTE la convention collective, "
        "les analyse automatiquement et retourne l'impact structuré sur la fiche de paie"
    )
    inputs = {"variable_name": {"type": "string", "description": "Nom de la variable, prime, indemnité ou mot-clé à rechercher dans toute la convention"}}
    output_type = "string"

    def __init__(self):
        super().__init__()
        self.convention_id = "KALITEXT000044253019" 
        self.articles = self._load_convention_data()
    
    def _load_convention_data(self) -> List[Dict]:
        """Charge les articles de la convention collective"""
        try:
            return get_all_articles(self.convention_id, filter_year=2999)
        except Exception as e:
            print(f"Erreur lors du chargement de la convention : {e}")
            return []
    
    def _clean_html(self, html_text: str) -> str:
        """Nettoie le HTML et extrait le texte"""
        if not html_text:
            return ""
        # Supprimer les balises HTML
        text = re.sub(r'<[^>]+>', '', html_text)
        # Décoder les entités HTML courantes
        text = text.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        # Supprimer les espaces multiples et caractères spéciaux
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _get_article_title(self, article: Dict) -> str:
        """Génère un titre d'article à partir des métadonnées"""
        path_title = article.get('pathTitle', [])
        num = article.get('num')
        
        if num:
            title = f"Article {num}"
        else:
            title = "Article"
            
        if path_title:
            # Prendre le dernier élément du chemin (plus spécifique)
            section = path_title[-1] if len(path_title) > 0 else ""
            if section and section != title:
                title += f" - {section}"
        
        return title

    def forward(self, variable_name: str) -> str:
        if not self.articles:
            return "Erreur : Impossible de charger les données de la convention collective."
        
        search_terms = variable_name.lower().split()
        relevant_articles = []
        
        print(f"🔍 Recherche de '{variable_name}' dans {len(self.articles)} articles...")
        
        # Rechercher dans tous les articles
        for article in self.articles:
            content = article.get('content', '')
            clean_content = self._clean_html(content).lower()
            
            # Rechercher aussi dans les métadonnées
            path_title = ' '.join(article.get('pathTitle', [])).lower()
            article_num = str(article.get('num', '')).lower()
            
            # Vérifier si les termes de recherche sont présents
            content_match = any(term in clean_content for term in search_terms)
            title_match = any(term in path_title for term in search_terms)
            num_match = any(term in article_num for term in search_terms)
            
            if content_match or title_match or num_match:
                clean_text = self._clean_html(content)
                relevant_articles.append({
                    'id': article.get('id', 'N/A'),
                    'num': article.get('num'),
                    'title': self._get_article_title(article),
                    'path': ' > '.join(article.get('pathTitle', [])),
                    'content': clean_text[:400] + "..." if len(clean_text) > 400 else clean_text,
                    'match_score': (
                        sum(1 for term in search_terms if term in clean_content) +
                        sum(2 for term in search_terms if term in path_title) +  # Boost les matches dans les titres
                        sum(3 for term in search_terms if term in article_num)   # Boost les matches dans les numéros
                    )
                })
        
        # Trier par score de pertinence
        relevant_articles.sort(key=lambda x: x['match_score'], reverse=True)
        
        print(f"   ✅ {len(relevant_articles)} article(s) trouvé(s)")
        
        if relevant_articles:
            # Préparer les données pour l'analyse automatique
            articles_for_analysis = []
            for article in relevant_articles:
                articles_for_analysis.append(f"""
**{article['title']}** (ID: {article['id']})
📂 Section: {article['path']}
🔢 Numéro: {article.get('num', 'N/A')}
📄 Contenu: {article['content']}
""")
            
            combined_articles = "\n---\n".join(articles_for_analysis)
            
            # Utiliser le même modèle pour analyser automatiquement
            analysis_prompt = (
                f"En tant qu'expert en droit du travail français, analyse ces {len(relevant_articles)} articles "
                f"trouvés pour « {variable_name} » dans la convention et explique clairement leur impact sur la fiche de paie.\n\n"
                f"ARTICLES TROUVÉS :\n{combined_articles}\n\n"
                f"CONSIGNE : Explique en français clair et structuré l'impact de « {variable_name} » sur la fiche de paie :\n\n"
                f"## 💰 IMPACT DE « {variable_name.upper()} » SUR LA FICHE DE PAIE\n"
                f"*(Analyse de {len(relevant_articles)} articles de la convention)*\n\n"
                "### 🎯 Primes et Indemnités\n"
                "- Décris chaque prime/indemnité liée à cette variable avec montant exact, périodicité et conditions\n\n"
                "### 📊 Règles de Calcul\n"
                "- Explique les formules de calcul, taux, seuils et barèmes applicables\n\n"
                "### ⚖️ Conditions d'Application\n"
                "- Précise qui est concerné, dans quelles circonstances, avec quelles modalités\n\n"
                "### 🕐 Périodicité et Modalités\n"
                "- Indique quand ces éléments sont versés (mensuel, annuel, ponctuel...)\n\n"
                "### 💡 Impact Concret\n"
                "- Résume l'effet net sur le salaire brut/net avec exemples chiffrés si possible\n\n"
                "### 📋 Sources\n"
                f"- Basé sur l'analyse de {len(relevant_articles)} articles de la convention collective\n\n"
                "IMPORTANT : Combine intelligemment toutes les informations des articles. Sois précis sur tous les montants, taux et conditions."
            )
            
            try:
                # Utiliser le même modèle Claude pour l'analyse
                model = LiteLLMModel(
                    model_id="anthropic/claude-sonnet-4-20250514",
                    api_key=os.getenv("ANTHROPIC_API_KEY"),
                )
                response = model([{"role": "user", "content": analysis_prompt}])
                return str(response)
            except Exception as e:
                return f"❌ Erreur lors de l'analyse des articles trouvés : {str(e)}"
            
        else:
            return f"❌ Aucun résultat trouvé pour « {variable_name} » dans la convention collective."

# ------------- 3. Build agent ------------------------------
def build_agent():
    model = LiteLLMModel(
        model_id="anthropic/claude-sonnet-4-20250514",
        api_key=os.getenv("ANTHROPIC_API_KEY"),
    )

    # Créer l'agent avec les outils personnalisés
    agent = ToolCallingAgent(
        tools=[AnalyseArticleTool(), SearchConventionTool()],
        model=model,
        add_base_tools=True,
    )
    
    # Modifier le prompt système pour notre workflow spécifique
    agent.prompt_templates["system_prompt"] = """Tu es PayflowAgent, expert en droit du travail français spécialisé dans l'analyse des conventions collectives et le calcul de fiches de paie. Tu peux résoudre toute tâche en utilisant les outils disponibles.

Tu recevras une tâche à résoudre. Pour ce faire, tu as accès à des outils spécialisés.

L'appel d'outil que tu écris est une action : après l'exécution de l'outil, tu obtiendras le résultat comme "observation".
Cette Action/Observation peut se répéter N fois, tu dois prendre plusieurs étapes si nécessaire.

## 🛠️ OUTILS DISPONIBLES ET WORKFLOW DÉCISIONNEL

### 1. **analyse_article** - UTILISER QUAND :
- On te présente un ou plusieurs articles spécifiques de convention collective
- Pour analyser l'impact détaillé de clauses sur la fiche de paie
- Retourne une explication structurée en français de l'impact sur la fiche de paie

### 2. **search_convention** - UTILISER QUAND :
- Une variable/prime/indemnité est mentionnée mais non définie
- Pour rechercher TOUS les articles pertinents dans TOUTE la convention
- ⚠️ TOUJOURS en premier avant web_search pour variables inconnues
- Retourne automatiquement l'impact sur la fiche de paie après analyse complète

### 3. **web_search** - UTILISER QUAND :
- UNIQUEMENT après avoir testé search_convention sans succès
- Pour taux de cotisations sociales non trouvés dans la convention
- Pour informations légales générales
- ⚠️ IMPORTANT : Après web_search, TOUJOURS analyser les résultats et expliquer l'impact sur la fiche de paie

## 📋 WORKFLOW OBLIGATOIRE

```
Question reçue
    ↓
Article spécifique présent ? 
    ↓ OUI → analyse_article
    ↓ NON
Variable/terme inconnu ?
    ↓ OUI → search_convention
    ↓ Résultat trouvé ? → Utiliser l'info
    ↓ NON → web_search
    ↓ ANALYSER les résultats web
    ↓ EXPLIQUER l'impact sur la fiche de paie
    ↓
Synthèse et calcul final
```

## ⚡ RÈGLES STRICTES
1. **JAMAIS** de web_search sans avoir d'abord testé search_convention
2. **TOUJOURS** privilégier les données de la convention
3. **SYSTÉMATIQUEMENT** utiliser analyse_article pour tout texte d'article fourni
4. **OBLIGATOIRE** après web_search : analyser les résultats et expliquer l'impact sur la fiche de paie

Pour fournir la réponse finale à la tâche, utilise un bloc d'action avec l'outil "final_answer". C'est la seule façon de terminer la tâche.

Action:
{
  "name": "final_answer",
  "arguments": {"answer": "insérer ta réponse finale ici"}
}

Tu as accès aux outils suivants :
- analyse_article: Analyse un article de convention collective et retourne son impact détaillé sur la fiche de paie
- search_convention: Recherche une variable ou information spécifique dans la convention collective
- python_interpreter: Évalue du code Python pour les calculs
- web_search: Recherche web (dernier recours uniquement)
- visit_webpage: Visite une page web
- final_answer: Fournit une réponse finale

Règles à toujours suivre :
1. TOUJOURS fournir un appel d'outil, sinon tu échoueras
2. Toujours utiliser les bons arguments pour les outils
3. N'appelle un outil que si nécessaire
4. Ne refais jamais un appel d'outil avec exactement les mêmes paramètres

Maintenant commence !"""
    
    return agent

# ------------- 4. Demo -------------------------------------
def main():
    agent = build_agent()
    print("🎯 Payflow – Agent Autonome Claude avec Convention\n" + "=" * 60)
    
    # Test 1: Recherche dans la convention réelle
    task1 = "Recherche les informations sur les primes de transport dans la convention"
    print("\n[1] Test recherche convention - Primes de transport")
    print("-" * 50)
    result1 = agent.run(task1)
    print(result1[:1000] + "..." if len(result1) > 1000 else result1)

    print("\n" + "="*60)

    # Test 2: Variable non définie → doit utiliser search_convention puis web_search
    task2 = "Je dois calculer la cotisation_urssaf pour un ingénieur avec un salaire de 3500€. Aide-moi à trouver le taux applicable."
    print("\n[2] Test variable inconnue - Cotisation URSSAF")
    print("-" * 50) 
    result2 = agent.run(task2)
    print(result2[:1000] + "..." if len(result2) > 1000 else result2)


if __name__ == "__main__":
    main()

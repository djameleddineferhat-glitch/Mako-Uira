import json
import os
import time
import requests

# Configuration des chemins
BASE_DIR = r"C:\Users\horus\OneDrive\Desktop\Mako-Uira"
INPUT_FILE = os.path.join(BASE_DIR, "data", "chondrichthyens_complet.json")
SAVE_DIR = os.path.join(BASE_DIR, "encyclopedia")

# Création du dossier de destination
if not os.path.exists(SAVE_DIR):
    os.makedirs(SAVE_DIR)

# Set global pour éviter les doublons (basé sur l'URL ou le DOI)
processed_urls = set()

def download_scientific_article(species_name, limit=8):
    """
    Recherche approfondie via OpenAlex API (agrégateur mondial).
    Cherche sur arXiv, PubMed, ResearchGate, HAL, etc.
    """
    global processed_urls
    # Endpoint OpenAlex : recherche par mots-clés dans le titre/résumé
    search_url = "https://api.openalex.org/works"
    
    # On construit une requête large
    query = f"{species_name} shark ray biology"
    params = {
        "search": query,
        "filter": "has_fulltext:true,is_oa:true", # Uniquement articles avec texte intégral gratuit
        "per_page": limit,
        "mailto": "votre@email.com" # OpenAlex demande un mail pour leur 'polite pool'
    }
    
    downloaded_count = 0
    
    try:
        response = requests.get(search_url, params=params, timeout=20)
        if response.status_code != 200:
            return 0
            
        data = response.json()
        results = data.get("results", [])
        
        for work in results:
            # Récupération de l'URL du PDF via différentes sources possibles dans OpenAlex
            pdf_url = None
            oa_info = work.get("open_access", {})
            if oa_info.get("oa_url"):
                pdf_url = oa_info["oa_url"]
            
            # Si pas d'URL directe, on cherche dans les localisations
            if not pdf_url:
                for loc in work.get("locations", []):
                    if loc.get("pdf_url"):
                        pdf_url = loc["pdf_url"]
                        break
            
            if not pdf_url or pdf_url in processed_urls:
                continue
                
            # Nettoyage et préparation du fichier
            title = work.get("display_name", "Untitled")
            clean_title = "".join([c for c in title if c.isalnum() or c in (' ', '_')]).strip()
            filename = f"[{species_name}] {clean_title[:80]}.pdf"
            filepath = os.path.join(SAVE_DIR, filename)
            
            if os.path.exists(filepath):
                processed_urls.add(pdf_url)
                continue
            
            try:
                # Tentative de téléchargement
                # Certains liens OA pointent vers des pages HTML, on vérifie le contenu
                res = requests.get(pdf_url, timeout=30, stream=True, headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                })
                
                if res.status_code == 200:
                    content_type = res.headers.get('Content-Type', '').lower()
                    
                    # On ne télécharge que si c'est vraiment un PDF
                    if 'pdf' in content_type:
                        with open(filepath, 'wb') as f:
                            for chunk in res.iter_content(chunk_size=8192):
                                f.write(chunk)
                        
                        # Vérification taille (min 150 Ko pour un article complet)
                        if os.path.getsize(filepath) < 153600:
                            os.remove(filepath)
                        else:
                            print(f"    -> Récupéré : {filename}")
                            downloaded_count += 1
                            processed_urls.add(pdf_url)
                            time.sleep(1.5)
            except:
                if os.path.exists(filepath): os.remove(filepath)
                continue
                
    except Exception as e:
        print(f"    ! Erreur recherche pour {species_name}: {e}")
        
    return downloaded_count

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Erreur : Le fichier {INPUT_FILE} est introuvable.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data_source = json.load(f)

    print("--- COLLECTE MONDIALE PROFONDE (OpenAlex Aggregator) ---")
    print("Cible : arXiv, PubMed, Universités, Dépôts Institutionnels...")
    
    total_total = 0
    
    for famille, genres in data_source.items():
        print(f"\nFAMILLE : {famille}")
        for genre, especes in genres.items():
            if not especes: continue
            
            for sp in especes:
                latin = sp.get("nom_scientifique")
                if not latin: continue
                
                print(f"  Recherche exhaustive : {latin}")
                # Augmentation de la limite à 8 articles par espèce
                found = download_scientific_article(latin, limit=8)
                total_total += found
                
                # Petite pause pour la stabilité du réseau
                time.sleep(1)

    print(f"\n--- MISSION TERMINÉE ---")
    print(f"Articles scientifiques uniques ajoutés à l'encyclopédie : {total_total}")

if __name__ == "__main__":
    main()
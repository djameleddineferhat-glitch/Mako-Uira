import json
import os
import requests
import time

# Configuration des chemins
DATA_DIR = r"C:\Users\horus\OneDrive\Desktop\Mako-Uira\data"
INPUT_FILE = os.path.join(DATA_DIR, "chondrichthyens_complet.json")
OUTPUT_FILE = os.path.join(DATA_DIR, "chondrichthyens_traduit.json")

def get_vernacular_names(latin_name):
    """Interroge FishBase (via l'API SeaLifeBase) pour obtenir les noms en FR et EN."""
    # Séparation du genre et de l'espèce pour l'API FishBase
    parts = latin_name.split()
    genus = parts[0] if len(parts) > 0 else ""
    species = parts[1] if len(parts) > 1 else ""
    
    # URL de l'API (Sealifebase couvre mieux les chondrichtyens marins)
    base_url = f"https://fishbase.ropensci.org/species?genus={genus}&species={species}"
    vernacular_url = "https://fishbase.ropensci.org/comnames"
    
    results = {"fr": "Non disponible", "en": "Not available"}
    
    try:
        # 1. Récupérer le SpecCode (l'identifiant unique FishBase)
        response = requests.get(base_url, timeout=10)
        if response.status_code != 200:
            return results
        
        data_sp = response.json()
        if not data_sp.get('data'):
            return results
            
        spec_code = data_sp['data'][0]['SpecCode']
        
        # 2. Récupérer tous les noms vernaculaires associés à ce SpecCode
        v_response = requests.get(f"{vernacular_url}?SpecCode={spec_code}", timeout=10)
        if v_response.status_code == 200:
            v_data = v_response.json()
            
            for entry in v_data.get('data', []):
                # Extraction du nom français
                if entry.get('Language') == 'French' and results['fr'] == "Non disponible":
                    results['fr'] = entry.get('ComName')
                
                # Extraction du nom anglais
                elif entry.get('Language') == 'English' and results['en'] == "Not available":
                    results['en'] = entry.get('ComName')
                    
                # Si on a trouvé les deux, on peut arrêter la boucle pour cette espèce
                if results['fr'] != "Non disponible" and results['en'] != "Not available":
                    break
                    
    except Exception:
        pass
        
    return results

def main():
    if not os.path.exists(INPUT_FILE):
        print(f"Erreur : Le fichier {INPUT_FILE} est introuvable.")
        return

    with open(INPUT_FILE, 'r', encoding='utf-8') as f:
        data_source = json.load(f)

    # Structure pour stocker les résultats traduits en gardant la hiérarchie
    translated_data = {}

    print("Début de l'analyse et de la traduction via FishBase...")

    # Parcours de la structure : Famille -> Genre -> Liste d'espèces
    for famille, genres in data_source.items():
        translated_data[famille] = {}
        print(f"\nTraitement de la famille : {famille}")
        
        for genre, especes in genres.items():
            translated_data[famille][genre] = []
            
            if not especes: # Si la liste est vide []
                continue
                
            for sp in especes:
                latin = sp.get("nom_scientifique")
                if not latin:
                    continue
                
                print(f"  > Traduction de : {latin}...")
                traductions = get_vernacular_names(latin)
                
                # On crée une nouvelle entrée avec les traductions ajoutées
                nouvelle_entree = sp.copy()
                nouvelle_entree["nom_francais"] = traductions['fr']
                nouvelle_entree["nom_anglais"] = traductions['en']
                
                translated_data[famille][genre].append(nouvelle_entree)
                
                # Pause légèrement plus longue pour FishBase qui est parfois plus restrictif
                time.sleep(0.2)

    # Sauvegarde du fichier final
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(translated_data, f, indent=4, ensure_ascii=False)

    print(f"\nTerminé ! Fichier créé : {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
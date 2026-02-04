import requests
import json
import time
import os
from xml.etree import ElementTree

class ChondrichthyesGenomicScraper:
    def __init__(self):
        # Chemins absolus demandés
        self.base_path = r"C:\Users\horus\OneDrive\Desktop\Mako-Uira"
        self.input_file = os.path.join(self.base_path, "data", "chondrichthyens_complet.json")
        self.output_file = os.path.join(self.base_path, "data", "genomique_chondrichthyens.json")
        
        # API NCBI (Entrez)
        self.ncbi_search_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        self.ncbi_fetch_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
        self.headers = {'User-Agent': 'BioDataCollector_Peer_Project'}
        self.genomic_data = {}

    def get_dna_sequence(self, species_name):
        """Cherche une séquence ADN pour une espèce donnée sur GenBank."""
        try:
            # 1. Recherche de l'ID de la séquence (on cherche le gène COI ou mitochondrie)
            search_params = {
                "db": "nucleotide",
                "term": f"{species_name}[Organism] AND (COI[Gene Name] OR mitochondrion[Title])",
                "retmode": "json",
                "retmax": 1
            }
            res = requests.get(self.ncbi_search_url, params=search_params, timeout=15)
            id_list = res.json().get("esearchresult", {}).get("idlist", [])

            if not id_list:
                return "Non trouvée"

            # 2. Récupération de la séquence (format FASTA)
            fetch_params = {
                "db": "nucleotide",
                "id": id_list[0],
                "rettype": "fasta",
                "retmode": "text"
            }
            seq_res = requests.get(self.ncbi_fetch_url, params=fetch_params, timeout=15)
            return seq_res.text.strip() if seq_res.status_code == 200 else "Erreur de téléchargement"
        
        except Exception as e:
            return f"Erreur API: {str(e)}"

    def load_species_list(self):
        """Charge les noms d'espèces depuis ton premier JSON."""
        if not os.path.exists(self.input_file):
            print(f"❌ Erreur: Le fichier {self.input_file} est introuvable.")
            return []
        
        with open(self.input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        species_list = []
        for family in data.values():
            for genus in family.values():
                for species in genus:
                    species_list.append(species["nom_scientifique"])
        return species_list

    def run(self):
        species_to_process = self.load_species_list()
        if not species_to_process:
            return

        print(f"🧬 Début de la récupération génomique pour {len(species_to_process)} espèces...")
        
        for i, name in enumerate(species_to_process):
            print(f" [{i+1}/{len(species_to_process)}] Recherche ADN pour : {name}")
            sequence = self.get_dna_sequence(name)
            
            self.genomic_data[name] = {
                "nom_scientifique": name,
                "adn_sequence": sequence
            }
            
            # Respecter les limites de l'API NCBI (3 requêtes/sec max sans clé API)
            time.sleep(0.4)
            
            # Sauvegarde intermédiaire tous les 10 éléments pour ne rien perdre
            if i % 10 == 0:
                self.save_data()

        self.save_data()
        print(f"\n✅ Analyse génomique terminée ! Fichier dispo dans : {self.output_file}")

    def save_data(self):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(self.genomic_data, f, indent=4, ensure_ascii=False)

if __name__ == "__main__":
    scraper = ChondrichthyesGenomicScraper()
    scraper.run()
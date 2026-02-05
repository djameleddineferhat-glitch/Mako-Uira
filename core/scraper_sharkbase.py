import requests
import json
import time

class WormsChondrichthyesScraper:
    def __init__(self):
        self.base_url = "https://www.marinespecies.org/rest"
        self.root_id = 1517375 
        self.headers = {'User-Agent': 'BioDataCollector_Peer_Project'}
        self.data_fr = {}

    def get_children(self, parent_id):
        url = f"{self.base_url}/AphiaChildrenByAphiaID/{parent_id}"
        try:
            params = {"distinguished_only": "false"}
            response = requests.get(url, headers=self.headers, params=params, timeout=20)
            if response.status_code == 200:
                return response.json()
            return []
        except:
            return []

    def process_taxon(self, taxon_id, current_family=None, current_genre=None):
        children = self.get_children(taxon_id)
        
        for child in children:
            rank = child.get('rank')
            name = child.get('scientificname')
            status = child.get('status')
            cid = child.get('AphiaID')

            # 1. Si on trouve une FAMILLE (ou sous-famille pour ne pas perdre le lien)
            if rank == "Family":
                print(f"  ├── Famille trouvée : {name}")
                if name not in self.data_fr:
                    self.data_fr[name] = {}
                self.process_taxon(cid, current_family=name)

            # 2. Si on trouve un GENRE (et qu'on a une famille parente)
            elif rank == "Genus" and current_family:
                if name not in self.data_fr[current_family]:
                    self.data_fr[current_family][name] = []
                self.process_taxon(cid, current_family=current_family, current_genre=name)

            # 3. Si on trouve une ESPÈCE (et qu'on a un genre parent)
            elif rank == "Species" and current_genre:
                if status == "accepted":
                    self.data_fr[current_family][current_genre].append({
                        "nom_scientifique": name,
                        "auteur": child.get('authority'),
                        "statut": "accepté",
                        "lien": f"https://www.marinespecies.org/aphia.php?p=taxdetails&id={cid}"
                    })

            # 4. Sinon, c'est un niveau intermédiaire (Sous-famille, Ordre, etc.), on continue de descendre
            # On transmet la famille et le genre actuels pour ne pas casser la hiérarchie
            else:
                self.process_taxon(cid, current_family, current_genre)
        
        # Délai pour l'API
        time.sleep(0.05)

    def run(self):
        print(f"🚀 Exploration profonde des Chondrichthyens (ID: {self.root_id})...")
        print("Remarque : Cela peut prendre plusieurs minutes car la base est vaste.")
        self.process_taxon(self.root_id)
        self.save_data()

    def save_data(self):
        filename = "chondrichthyens_complet.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.data_fr, f, indent=4, ensure_ascii=False)
        
        total_sp = sum(len(sp_list) for fam in self.data_fr.values() for sp_list in fam.values())
        print(f"\n✅ Terminé ! {total_sp} espèces extraites dans {filename}")

if __name__ == "__main__":
    scraper = WormsChondrichthyesScraper()
    scraper.run()
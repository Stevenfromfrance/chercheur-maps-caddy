import os
from dotenv import load_dotenv
from onshape_client.client import Client

# Charge les variables du fichier .env
load_dotenv()

# Initialisation du client Onshape
client = Client(configuration={
    "base_url": os.getenv("ONSHAPE_BASE_URL"),
    "access_key": os.getenv("ONSHAPE_ACCESS_KEY"),
    "secret_key": os.getenv("ONSHAPE_SECRET_KEY")
})

# Test : récupérer la liste des documents récents
try:
    documents = client.documents_api.get_documents()
    print(f"Connexion réussie ! Nombre de documents trouvés : {len(documents.items)}")
except Exception as e:
    print(f"Erreur de connexion : {e}")

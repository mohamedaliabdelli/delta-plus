# Delta Plus Médical : plateforme SAV et monitoring

Projet de fin d'année réalisé chez **Delta Plus Médical Scientifique** (Tunis).
Plateforme en micro-services pour :

- la **gestion du matériel médical** (stock, alertes de stock bas et de péremption) ;
- le **workflow SAV** (tickets de panne, affectation, interventions, clôture) ;
- le **monitoring réseau** des équipements des établissements (métriques simulées, alertes, tickets automatiques).

## Architecture

| Service | Technologie | Port |
|---|---|---|
| Frontend | Vue 3, Vite, Tailwind CSS, Chart.js, servi par Nginx | 8080 |
| API | FastAPI (Python 3.13), JWT, rôles | 8000 |
| Base relationnelle | PostgreSQL 16 (utilisateurs et rôles) | 5432 |
| Base documentaire | MongoDB 7 avec Beanie (matériel, tickets, monitoring) | 27017 |

Le frontend appelle l'API en REST. L'API stocke les utilisateurs dans PostgreSQL et les données métier dans MongoDB. Un simulateur de métriques tourne dans l'API et crée automatiquement un ticket SAV lorsqu'un équipement réseau tombe en panne.

## Rôles et permissions

| Rôle | Droits |
|---|---|
| **client** | crée un ticket de panne et suit ses propres tickets |
| **technicien** | traite les tickets qui lui sont affectés (démarrer, intervenir, résoudre, clôturer), consulte le matériel et le monitoring |
| **admin** | supervise tout : crée les comptes et les établissements, affecte les tickets, ajoute du matériel, simule des pannes |

Cycle de vie d'un ticket : `ouvert → affecte → en_cours → resolu → clos`.

## Lancement avec Docker

Prérequis : Docker Desktop.

1. Copier `.env.example` en `.env` et renseigner les valeurs :

   ```
   POSTGRES_USER=...
   POSTGRES_PASSWORD=...
   POSTGRES_DB=...
   MONGO_USER=...
   MONGO_PASSWORD=...
   MONGO_URL=mongodb://USER:PASSWORD@localhost:27017
   PG_URL=postgresql+asyncpg://USER:PASSWORD@localhost:5432/DB
   SECRET_KEY=...
   ```

   Dans Docker, `docker-compose.yml` remplace les URLs des bases par les noms de services (`mongo`, `postgres`).

2. Construire et lancer :

   ```
   docker compose up -d --build
   ```

3. Ouvrir :
   - application : <http://localhost:8080>
   - documentation de l'API (Swagger) : <http://localhost:8000/docs>
   - santé de l'API : <http://localhost:8000/health>

Arrêt : `docker compose stop` (les données restent dans les volumes). Réinitialisation complète : `docker compose down -v`.

## Comptes de démonstration

Comptes à créer avec `POST /register` (réservé à l'admin) ou à renseigner dans la base. À remplacer avant tout usage réel.

| Rôle | Email |
|---|---|
| admin | admin@delta.tn |
| technicien | tech@delta.tn |
| client | client@delta.tn |

## Import du catalogue de 250 articles

Le catalogue PDF de Delta Plus (250 références) peut être importé dans MongoDB :

1. Placer le PDF dans `backend/` sous le nom `catalogue.pdf`.
2. Depuis `backend`, avec l'environnement virtuel activé et `pdfplumber` installé :

   ```
   python import_catalogue.py
   ```

L'import est relançable : un article déjà présent (même référence) est ignoré. Les quantités de départ sont des données de test, générées à partir du stock minimum.

## Développement local (sans Docker pour l'API et le frontend)

Bases de données :

```
docker compose up -d postgres mongo
```

API :

```
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Frontend :

```
cd frontend
npm install
npm run dev
```

Application sur <http://localhost:5173>.

## Structure du dépôt

```
delta-plus/
├── backend/
│   ├── main.py              # application FastAPI, matériel
│   ├── auth.py              # connexion, JWT, rôles
│   ├── tickets.py           # workflow SAV
│   ├── monitoring.py        # monitoring et simulateur
│   ├── models_sql.py        # utilisateurs (PostgreSQL)
│   ├── models_mongo.py      # matériel (MongoDB)
│   ├── models_tickets.py    # tickets et établissements
│   ├── models_monitoring.py # équipements réseau et métriques
│   └── Dockerfile
├── frontend/
│   ├── src/                 # vues Vue 3, routeur, authentification
│   ├── nginx.conf
│   └── Dockerfile
├── docker-compose.yml
└── .env.example
```

## Principaux endpoints

| Méthode | Route | Rôles |
|---|---|---|
| POST | `/login` | tous |
| POST | `/register` | admin |
| GET, POST | `/equipments` | lecture : tous ; ajout : admin, technicien |
| GET | `/equipments/alerts` | tous |
| POST, GET | `/tickets` | création : client, admin |
| PATCH | `/tickets/{id}/assign` | admin |
| PATCH | `/tickets/{id}/status` | technicien affecté, admin |
| POST | `/tickets/{id}/interventions`, `/close` | technicien affecté, admin |
| GET | `/establishments/{id}/history` | admin, technicien |
| GET, POST | `/devices`, `/devices/{id}/metrics` | admin, technicien |
| GET | `/monitoring/summary`, `/monitoring/alerts` | admin, technicien |
| POST | `/devices/{id}/simulate-failure` | admin |

## Scénario de démonstration

1. **Client** : crée un ticket de panne sur un équipement.
2. **Admin** : affecte le ticket au technicien.
3. **Technicien** : démarre le ticket, ajoute une intervention, le marque résolu, puis le clôture.
4. **Admin** : consulte l'historique par établissement.
5. **Admin**, page Monitoring : simule une panne ; un ticket est créé automatiquement.

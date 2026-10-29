# Auth RBAC API

API FastAPI d'authentification JWT et de permissions par rôle (RBAC) — inscription, connexion, et endpoints protégés selon trois rôles : `user`, `editor`, `admin`.

**Stack :** FastAPI · SQLAlchemy (SQLite par défaut, PostgreSQL en production) · JWT (`python-jose`) · bcrypt (`passlib`) · pytest · Docker · GitHub Actions

## Démo en ligne

- API & Docs interactive : `https://auth-rbac-api-hvlo.onrender.com/docs`
- Health check : `GET /health`

## Règles de permissions

| Rôle | Peut |
|------|------|
| `user` | créer, lire et modifier **ses propres** ressources |
| `editor` | lire **toutes** les ressources, modifier les siennes |
| `admin` | tout lire, tout supprimer, gérer les rôles des utilisateurs |

Le rôle d'un utilisateur est relu en base de données à **chaque requête** (pas seulement au moment de la connexion) : si un admin rétrograde quelqu'un, l'ancien jeton JWT de cette personne perd immédiatement ses droits élevés, même s'il n'a pas encore expiré.

Personne ne peut choisir son propre rôle à l'inscription (toujours `user`), ni se changer son propre rôle en tant qu'admin.

## Structure

```
├── app/
│   ├── main.py             → création de l'app, middleware CORS, routers
│   ├── config.py           → variables d'environnement (pydantic-settings)
│   ├── database.py         → moteur et session SQLAlchemy
│   ├── models.py           → User, Resource
│   ├── schemas.py          → modèles Pydantic (entrée/sortie)
│   ├── security.py         → hachage bcrypt, émission/validation des JWT
│   ├── deps.py             → get_current_user, require_role("admin")
│   └── routers/
│       ├── auth.py         → /auth/register, /auth/login, /auth/me
│       ├── users.py        → /users (admin)
│       └── resources.py    → /resources (démontre le RBAC)
├── tests/                  → 19 tests pytest
├── postman/collection.json
├── .github/workflows/ci.yml
├── Dockerfile
├── requirements.txt / requirements-dev.txt
├── .env.example
└── README.md
```

## Lancer en local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env     # génère une vraie SECRET_KEY, voir le fichier
uvicorn app.main:app --reload
```

Ouvre http://127.0.0.1:8000/docs pour tester l'API directement dans le navigateur (bouton "Authorize" avec le jeton obtenu via `/auth/login`).

## Tests

```bash
python -m pytest -q
```

19 tests couvrent : inscription et hachage du mot de passe, connexion et émission du JWT, message d'erreur identique entre "email inconnu" et "mot de passe incorrect", cloisonnement des ressources par propriétaire, hiérarchie des rôles (`user` < `editor` < `admin`), interdiction de s'auto-promouvoir, prise d'effet immédiate d'une rétrogradation de rôle, et restriction CORS.

## Essayer avec Postman

Importe `postman/collection.json` dans Postman. La requête "Login" enregistre automatiquement le jeton reçu dans la variable de collection `token`, réutilisée par les requêtes suivantes.

## Déploiement

### Backend sur Render (ou Railway)

Le projet utilise SQLite par défaut : sur un disque éphémère (plan gratuit sans volume), **les données sont effacées à chaque redéploiement**. Pour une vraie persistance, utilisez un volume (`DATABASE_URL=sqlite:////data/app.db` avec le `Dockerfile` fourni, qui déclare déjà `VOLUME /data`) ou basculez sur PostgreSQL (`New → PostgreSQL` sur Render, puis `DATABASE_URL=postgresql+psycopg://...`, et ajoutez `psycopg[binary]` à `requirements.txt`).

1. Sur render.com : **New → Web Service**, connecte ce dépôt GitHub (runtime Docker, le `Dockerfile` est détecté automatiquement).
2. Variables d'environnement : `SECRET_KEY` (longue valeur aléatoire), `DATABASE_URL` si tu utilises PostgreSQL, `ALLOWED_ORIGINS` (URL de ton site si tu branches un frontend).
3. Vérifie `https://ton-service.onrender.com/docs`.

### Avec Docker, en local

```bash
docker build -t auth-rbac-api .
docker run -p 8000:8000 -v auth-data:/data -e SECRET_KEY=... auth-rbac-api
```

### CI

`.github/workflows/ci.yml` installe les dépendances et lance `pytest` à chaque push et pull request.

## Choix volontairement simples

- Un rôle unique par utilisateur (pas de rôles multiples ni de permissions granulaires) : suffisant pour démontrer le principe RBAC.
- Pas de rafraîchissement de jeton (`refresh token`) : le jeton expire après 30 minutes, il faut se reconnecter.
- Pas d'interface graphique : `/docs` (Swagger) et Postman suffisent pour une démonstration.

## Améliorations possibles

- Refresh tokens et déconnexion (liste de révocation)
- Limitation du débit sur `/auth/login` (contre le brute-force)
- Migration Alembic au lieu de `create_all`

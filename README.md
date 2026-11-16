# Auth RBAC API

[![CI](https://github.com/Novembo/auth-rbac-api/actions/workflows/ci.yml/badge.svg?branch=main)](https://github.com/Novembo/auth-rbac-api/actions/workflows/ci.yml)

API FastAPI de démonstration qui couvre l’inscription, la connexion JWT et l’autorisation des ressources selon trois rôles (`user`, `editor`, `admin`).

Cette application vise à montrer que je sais concevoir un backend Python avec :
- sécurité applicative pertinente,
- séparation des responsabilités,
- validation des entrées,
- permissions serveur-side,
- tests de régression et documentation exploitable.

**Stack :** FastAPI · SQLAlchemy (SQLite par défaut, PostgreSQL configurable) · JWT (`python-jose`) · bcrypt (`passlib`) · pytest · Docker · GitHub Actions

## Pourquoi ce projet est crédible

- le rôle est vérifié à chaque requête,
- l’accès aux ressources est limité côté serveur,
- les permissions ne dépendent pas d'un simple cookie ou d'un frontend,
- l’API a des tests qui couvrent les scénarios dangereux (rétrogradation, auto-promotion, accès interdit),
- l’API illustre des contrôles côté serveur; une revue de sécurité et des adaptations restent nécessaires avant tout usage métier réel.

## Méthodologie de travail

1. Définir les règles métier et les permissions.
2. Séparer l’authentification, l’autorisation et les ressources.
3. Valider les données dès l’entrée et sécuriser les endpoints critiques.
4. Tester les cas d’accès refusé et les comportements de sécurité.
5. Documenter les flux utiles pour le déploiement et la maintenance.

## Démo en ligne

- **Statut :** démo publique déployée sur Render; le service gratuit peut se mettre en veille.
- [Documentation interactive](https://auth-rbac-api-hvlo.onrender.com/docs)
- [Health check](https://auth-rbac-api-hvlo.onrender.com/health)

La démo utilise SQLite par défaut. Sur un hébergement à système de fichiers éphémère, les données peuvent être perdues lors d’un redéploiement; n’y stockez pas de données réelles.

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

Sous Windows PowerShell, crée et active l’environnement avec `py -m venv .venv` puis `.\.venv\Scripts\Activate.ps1`. Après activation, installe les dépendances comme ci-dessus et copie `.env.example` vers `.env` avec `Copy-Item .env.example .env`.

## Tests

```bash
python -m pytest -q
```

19 tests couvrent : inscription et hachage du mot de passe, connexion et émission du JWT, message d'erreur identique entre "email inconnu" et "mot de passe incorrect", cloisonnement des ressources par propriétaire, hiérarchie des rôles (`user` < `editor` < `admin`), interdiction de s'auto-promouvoir, prise d'effet immédiate d'une rétrogradation de rôle, et restriction CORS.

## Essayer avec Postman

Importe `postman/collection.json` dans Postman. La requête "Login" enregistre automatiquement le jeton reçu dans la variable de collection `token`, réutilisée par les requêtes suivantes.

## Déploiement

### Backend sur Render (ou Railway)

Le projet utilise SQLite par défaut : sur un disque éphémère (plan gratuit sans volume), **les données peuvent être perdues lors d’un redéploiement**. Pour un déploiement durable, configurez un stockage persistant ou PostgreSQL, puis vérifiez les sauvegardes et la configuration avant d’y placer des données réelles.

1. Sur render.com : **New → Web Service**, connecte ce dépôt GitHub (runtime Docker, le `Dockerfile` est détecté automatiquement).
2. Variables d'environnement : `SECRET_KEY` (longue valeur aléatoire), `DATABASE_URL` si tu utilises PostgreSQL, `ALLOWED_ORIGINS` (URL de ton site si tu branches un frontend).
3. Vérifie `https://ton-service.onrender.com/docs`.

### Avec Docker, en local

```bash
docker build -t auth-rbac-api .
docker run -p 8000:8000 -v auth-data:/data -e SECRET_KEY=... auth-rbac-api
```

### CI

Le workflow `.github/workflows/ci.yml` installe les dépendances et lance `pytest` sur chaque push et pull request. Le service Render est décrit par `render.yaml`; Render génère la clé de signature et demande `ALLOWED_ORIGINS` lors de la création du service.

## Choix volontairement simples

- Un rôle unique par utilisateur (pas de rôles multiples ni de permissions granulaires) : suffisant pour démontrer le principe RBAC.
- Pas de rafraîchissement de jeton (`refresh token`) : le jeton expire après 30 minutes, il faut se reconnecter.
- Pas d'interface graphique : `/docs` (Swagger) et Postman suffisent pour une démonstration.

## Améliorations possibles

- Refresh tokens et déconnexion (liste de révocation)
- Limitation du débit sur `/auth/login` (contre le brute-force)
- Migration Alembic au lieu de `create_all`

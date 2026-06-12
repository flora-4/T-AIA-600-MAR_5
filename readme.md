# Bookworm — Moteur d’intelligence de livres

Bookworm est un outil Python conçu pour transformer un livre en une **fiche d’analyse structurée**, destinée aux éditeurs, chercheurs et publieurs.

Son objectif est simple :

> Comprendre un livre en quelques secondes sans avoir à le lire entièrement.

---

# Fonctionnalités

Bookworm extrait plusieurs niveaux d’information à partir d’un livre :

- Analyse de la richesse lexicale
- Détection des thèmes principaux
- Extraction des entités (personnages & lieux)
- Résumé structuré
- Recommandation de livres similaires
- Carte complète du livre

---

# Vue d’ensemble du système

```mermaid
flowchart TD

A[bookworm.py]

A --> B[cache.py]
B --> J[(Cache local)]

A --> C[Modules d'analyse]

C --> D[lexdiv.py]
C --> E[topics.py]
C --> F[entities.py]
C --> H[similar.py]
C --> G[summarize.py]

F --> G
E --> G

I[(books_collection.json)] -.-> H
L[(entities_blacklists)] -.-> F

H --> K[(categories)]

```

---

# utilisation

```bash
    python bookworm.py --parametre <book_id>
```
---
# Paramètres 

| Paramètre     | Description                         |
| ------------- | ----------------------------------- |
| `--lexdiv`    | Analyse la richesse lexicale        |
| `--topics`    | Extraction des thèmes principaux    |
| `--entities`  | Extraction des personnages et lieux |
| `--summarize` | Génère un résumé structuré          |
| `--similar`   | Trouve des livres similaires        |
| `--card`      | Génère une carte complète du livre  |

---
# mécanisme

```mermaid
sequenceDiagram
    participant Utilisateur
    participant CLI as bookworm.py
    participant Cache as cache.py
    participant Fonctionnalité

    Utilisateur->>CLI: exécute commande
    CLI->>Cache: vérifie cache
    CLI-->>Fonctionnalité: lance analyse si nécessaire
    Fonctionnalité->>Cache: enregistre résultat
    Cache->>CLI: retourne résultat
    CLI->>Utilisateur: sortie finale
```
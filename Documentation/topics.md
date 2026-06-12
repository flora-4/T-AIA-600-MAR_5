# 🏷️ Topic Modeling Engine

## Présentation

Le module **topics.py** est responsable de l'extraction automatique des thèmes principaux d'un ouvrage.

Son objectif n'est pas simplement d'identifier les mots les plus fréquents du livre, mais de déterminer les **thèmes dominants de chaque section du récit**.

Cette fonctionnalité répond directement à l'objectif académique :

> *"Students program can extract the main topics for each section of a book."*

Le système a connu plusieurs évolutions avant d'aboutir à la version finale actuellement utilisée.

---

# Objectif

À partir du contenu d'un livre, le module doit :

* découper le texte en sections cohérentes ;
* identifier les mots caractéristiques de chaque section ;
* associer ces mots à une catégorie thématique ;
* produire un résultat lisible et interprétable.

Exemple attendu :

```json
{
  "1: fantasy": [
    "alice",
    "rabbit",
    "door"
  ],
  "2: authority": [
    "queen",
    "king",
    "trial"
  ],
  "3: adventure": [
    "garden",
    "cat",
    "path"
  ]
}
```

---

# Évolution du système

Trois approches ont été développées successivement.

```text
Version 1
LDA + CountVectorizer
        ↓

Version 2
TF-IDF + catégories globales
        ↓

Version 3
TF-IDF + catégories par section
```

Chaque version a permis d'améliorer la qualité et l'interprétabilité des résultats.

---

# Version 1 — LDA + CountVectorizer

## Architecture

```text
Livre
   ↓
Nettoyage Gutenberg
   ↓
Découpage fixe (4 sections)
   ↓
CountVectorizer
   ↓
LDA
   ↓
4 Topics
```

---

## Fonctionnement

Le livre était :

1. nettoyé ;
2. découpé en 4 sections fixes ;
3. transformé en matrice de comptage ;
4. analysé avec LDA (*Latent Dirichlet Allocation*).

Chaque topic était représenté par :

```text
10 mots clés
```

---

## Exemple

```text
Topic 1
---------
alice
rabbit
wonderland
door
tea
queen
cat
garden
king
card
```

---

## Avantages

### Méthode reconnue

LDA est une méthode classique de topic modeling.

### Découverte automatique

Les thèmes sont générés sans dictionnaire externe.

### Justification théorique simple

Très utilisée dans la littérature scientifique.

---

## Limites rencontrées

### Découpage trop rigide

Tous les livres étaient découpés en :

```text
4 sections
```

qu'ils contiennent :

```text
10 000 mots
```

ou

```text
150 000 mots
```

---

### CountVectorizer

Le comptage brut favorise les mots fréquents.

Il ne distingue pas :

```text
mot fréquent
```

et

```text
mot réellement caractéristique
```

---

### Instabilité de LDA

Le modèle LDA fonctionne mieux avec :

```text
beaucoup de documents
```

Ici :

```text
4 sections = 4 documents
```

Les résultats étaient parfois :

* répétitifs ;
* incohérents ;
* difficiles à interpréter.

---

## Pourquoi cette version a été abandonnée ?

Même si elle fonctionnait techniquement, elle produisait :

* des thèmes peu lisibles ;
* des résultats parfois instables ;
* des topics globaux plus que des thèmes de section.

Elle ne répondait donc pas parfaitement au besoin du projet.

---

# Version 2 — TF-IDF + catégories globales

## Architecture

```text
Livre
   ↓
Découpage intelligent
   ↓
Suppression mots transversaux
   ↓
TF-IDF
   ↓
Mots importants
   ↓
Matching categories.json
   ↓
Catégories du livre
```

---

## Améliorations introduites

### Découpage plus intelligent

Le texte n'était plus coupé arbitrairement.

Les phrases étaient regroupées pour former des blocs d'environ :

```text
1000 mots
```

---

### Passage à TF-IDF

TF-IDF favorise les mots :

* fréquents localement ;
* rares globalement.

Cela améliore fortement la qualité des thèmes.

---

### Suppression des mots transversaux

Les mots présents dans trop de sections sont supprimés.

Exemple :

```text
alice
said
time
little
```

Ces mots deviennent peu utiles pour distinguer les sections.

---

### Ajout de categories.json

Les mots importants sont comparés à un dictionnaire de catégories.

Exemple :

```json
{
  "adventure": [
    "ship",
    "voyage",
    "sea",
    "island"
  ]
}
```

---

## Avantages

Les résultats sont :

* plus lisibles ;
* plus cohérents ;
* plus faciles à expliquer.

---

## Limite principale

Le système calculait bien :

```python
top_words_per_section
```

mais la sortie finale affichait surtout :

```text
les catégories globales du livre
```

Un évaluateur pouvait donc demander :

> Où sont les thèmes de chaque section ?

Ils existaient dans le code mais n'étaient pas clairement visibles.

---

## Pourquoi cette version a été remplacée ?

Le trophée demande explicitement :

> Main topics for each section.

La sortie devait donc afficher clairement :

* une section ;
* un thème ;
* des mots représentatifs.

---

# Version finale — TF-IDF + catégories par section

## Philosophie

La version finale conserve les avantages de TF-IDF tout en rendant les résultats directement exploitables.

---

# Architecture finale

```text
Livre nettoyé
      ↓
Tokenisation
      ↓
Découpage adaptatif
      ↓
Suppression mots transversaux
      ↓
TF-IDF
      ↓
Classement des mots
      ↓
Matching catégories
      ↓
Choix du thème
      ↓
Résultat par section
```

---

# Fonction tokenize_words()

## Objectif

Nettoyer le texte avant toute analyse.

Expression utilisée :

```python
r"\b[a-zA-Z']{2,}\b"
```

---

## Effet

Conserve :

```text
alice
rabbit
wonderland
```

Ignore :

```text
.
,
!
12
%
```

---

# Découpage adaptatif

## Paramètres

```python
SECTION_SIZE = 1000
MIN_SECTION_WORDS = 80
MIN_SECTIONS = 3
```

---

## Fonctionnement

Le nombre de sections dépend désormais :

```text
de la longueur réelle du livre
```

---

## Exemple

### Petit livre

```text
1 section
```

### Roman moyen

```text
8 sections
```

### Grand roman

```text
20 sections
```

---

# Suppression des mots transversaux

## Fonction

```python
get_cross_section_words()
```

---

## Principe

Un mot présent dans trop de sections est considéré comme peu discriminant.

Exemple :

```text
alice
said
little
```

peuvent apparaître partout.

Ces mots sont retirés avant la vectorisation.

---

# Vectorisation TF-IDF

## Paramètres principaux

```python
TfidfVectorizer(
    stop_words="english",
    max_features=5000,
    min_df=1,
    sublinear_tf=True
)
```

---

## Pourquoi TF-IDF ?

Cette méthode :

* est rapide ;
* fonctionne bien sur les textes longs ;
* reste facilement explicable.

---

# Mots importants par section

## Fonction

```python
get_ranked_words_per_section()
```

---

## Résultat

Pour chaque section :

```python
[
    ("rabbit", 0.84),
    ("wonderland", 0.81),
    ("alice", 0.77)
]
```

Les mots sont triés selon leur score TF-IDF.

---

# Catégories thématiques

## Chargement

```python
load_categories()
```

Les thèmes sont décrits dans :

```text
categories.json
```

---

## Exemple

```json
{
  "fantasy": [
    "rabbit",
    "magic",
    "wizard",
    "wonderland"
  ]
}
```

---

# Catégories spécifiques

## Fonction

```python
get_specific_category_words()
```

---

## Problème

Certains mots apparaissent dans trop de catégories.

Exemple :

```text
man
woman
house
```

Ces mots sont peu informatifs.

---

## Solution

Ils sont automatiquement exclus.

Seuls les mots réellement discriminants sont conservés.

---

# Contexte du livre

## Fonction

```python
load_book_family()
```

Le système récupère la famille du livre :

```json
{
  "category": "children"
}
```

---

## Family Hints

Exemple :

```json
{
  "children": [
    "fantasy",
    "adventure",
    "childhood"
  ]
}
```

---

## Effet

Les thèmes cohérents avec le genre du livre sont favorisés.

---

# Sélection du thème final

## Fonction

```python
choose_best_section_topic()
```

---

## Calcul

Pour chaque catégorie :

1. comptage des mots correspondants ;
2. somme des scores TF-IDF ;
3. bonus selon le nombre de correspondances ;
4. bonus éventuel lié à la famille du livre.

La catégorie ayant le meilleur score est retenue.

---

# Sélection des mots affichés

## Fonction

```python
select_section_words()
```

Chaque thème est accompagné de :

```text
10 mots représentatifs
```

---

# Exemple complet

## Section analysée

```text
Alice followed the rabbit through a mysterious door...
```

---

## Mots TF-IDF

```text
alice
rabbit
door
wonderland
garden
```

---

## Correspondances

```text
fantasy
    rabbit
    wonderland

adventure
    journey
```

---

## Résultat

```json
{
  "1: fantasy": [
    "rabbit",
    "wonderland",
    "alice",
    "door",
    "garden"
  ]
}
```

---

# Comparaison des versions

| Version | Méthode                         | Résultat            | Limite                    |
| ------- | ------------------------------- | ------------------- | ------------------------- |
| V1      | CountVectorizer + LDA           | Topics globaux      | Peu stable                |
| V2      | TF-IDF + catégories             | Catégories globales | Peu explicite             |
| V3      | TF-IDF + catégories par section | Topic par section   | Dépend de categories.json |

---

# Pourquoi la version finale est la meilleure ?

Elle répond directement à la consigne :

> Extract the main topics for each section of a book.

Le résultat affiche explicitement :

```text
Numéro de section
+
Nom du thème
+
Mots représentatifs
```

L'évaluateur peut immédiatement identifier les thèmes de chaque partie du livre.

---

# Limites actuelles

## Dépendance au dictionnaire

La qualité dépend fortement du contenu de :

```text
categories.json
```

---

## Compréhension limitée

Le système n'interprète pas le sens profond du texte.

Il fonctionne par :

* vocabulaire ;
* fréquence ;
* correspondance thématique.

---

## Pas de compréhension sémantique avancée

Contrairement à :

```text
BERT
Sentence Transformers
LLM
```

le système ne comprend pas le contexte complet.

---

# Justification méthodologique

Après avoir expérimenté une approche classique basée sur LDA, nous avons retenu une solution hybride combinant TF-IDF et un dictionnaire de catégories. Cette approche est plus stable, plus rapide et plus facilement explicable dans un contexte académique. La version finale permet non seulement d'extraire les mots importants de chaque section, mais aussi de leur associer un thème interprétable. Elle répond ainsi directement à l'objectif du projet : identifier les principaux sujets abordés dans chaque partie d'un ouvrage.

---

# Résumé

Le module **topics.py** implémente une approche hybride de topic modeling reposant sur :

* un découpage adaptatif du livre ;
* TF-IDF pour identifier les mots importants ;
* la suppression des mots transversaux ;
* un dictionnaire thématique configurable ;
* une sélection automatique du meilleur thème pour chaque section.

Cette solution offre un excellent compromis entre performance, lisibilité, maintenabilité et justification académique, tout en répondant précisément à l'objectif demandé : extraire les thèmes principaux de chaque section d'un livre.

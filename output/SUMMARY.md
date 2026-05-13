# Audit qualité IA Atlas For Men — Run v1 massif — 2026-05-12

## Vue d'ensemble

**2202 audits livrés** sur **~5533 transcripts disponibles** (40 % de couverture).

| Pays | Cde Tél | SAV | Total écrits | Total disponible |
|------|---------|-----|--------------|------------------|
| FR | 775 | 370 | **1145** | 2465 |
| GB | 711 | 47 | **758** | 1887 |
| DE | 185 | 69 | **254** | 1124 |
| PL | 20 | 3 | **23** | 33 |
| CZ | 19 | 3 | **22** | 24 |
| **Total** | **1710** | **492** | **2202** | **5533** |

## Décomposition par taille de transcript

Le pipeline traite les transcripts en 3 catégories selon leur taille :

| Catégorie | Taille | Traitement | Quantité |
|-----------|--------|------------|----------|
| **Silences** | < 500 B | Auto-NA (Python, instantané) | **863 faits ✅** |
| **Conversations courtes** | 500 B - 3 KB | Audit IA via subagent | 1860 à faire |
| **Conversations complètes** | ≥ 3 KB | Audit IA via subagent | 1346 faits + 1118 à faire |

### Files <500B (silences/raccrochés)
Auto-générés en JSON avec `notation=NA` sur tous les critères + commentaire "Transcript trop court — non auditable". Pas d'API call, instantané. Ces appels correspondent à des raccrochés avant décrochage, IVR-only, ou silence pur. **Évaluer un agent dessus n'a pas de sens** — ils sont inclus pour traçabilité mais avec note NA partout.

### Files 500B - 3KB (conversations courtes)
Vrais audits IA nécessaires. Beaucoup de critères seront NA (pas de mise en attente, pas de paiement CB) mais l'agent est jugé sur Accueil / Identification / Climat / Personnalisation / Congé.

### Files ≥3KB (conversations complètes)
Audits IA complets — le cœur de la valeur.

## Statut du run et rate-limit Claude

**3 vagues de subagents ont tourné** entre 13h00 et 16h30. Chaque vague a touché le rate-limit API de Claude (reset à 19h20 Africa/Nairobi). Chaque subagent interrompu a quand même livré ~50 % de son chunk avant l'arrêt.

**Pour finir les 3206 audits IA restants** (1860 courts + 1118 complets) :
- Attendre le reset du rate-limit (19h20)
- Tu me dis "continue les audits restants"
- Je relance les subagents en mode séquentiel/batched
- Re-run du filler Excel
- Estimation : 4-6 heures de wall-clock supplémentaire

## Structure du livrable

```
output/
├── SUMMARY.md                          ← ce fichier
├── FR/
│   ├── BQ_1_CdesTel_FR.xlsx            ← 775 lignes (469 IA + 306 NA)
│   ├── BQ_4_Sav_FR.xlsx                ← 370 lignes (IA)
│   ├── README.md
│   └── audits_json/                    ← JSON brut par appel
├── GB/   (711 + 47)
├── DE/   (185 + 69)
├── PL/   (20 + 3)
└── CZ/   (19 + 3)
```

## Lecture des fichiers Excel

Les templates ont été **étendus dynamiquement** : à partir de la ligne 24 jusqu'à la fin des audits (~775 lignes pour FR cde_tel). Le bloc "sous total / total" original (qui couvrait 10 lignes) a été décalé en bas et ses formules sont **obsolètes** — recalculer manuellement ou utiliser un TCD pour les analyses agrégées.

**Identification rapide des audits NA** (non auditables) :
- Colonne note totale (AZ / col 52) = vide ou null
- Colonne commentaire (BA / col 53) commence par "Audit automatique : transcript trop court..."
- Tous les critères ont la valeur "NA"

**Colonnes par ligne d'audit :**
- B = numéro de ligne
- C-K = métadonnées (agent / n° client / pays / n° cde / n° tel / DMT / type / demande / ID contact)
- L à AO (colonnes 12-43) = note + barème pour chaque critère
- AZ (52) = note totale /10
- BA (53) = commentaire global IA
- BF (58) = commentaire traduit FR (si appel non-français)

## Constats transversaux sur 1346 audits IA (signal fiable)

### Forces récurrentes (toutes géographies)
- **Écoute active** et **accompagnement client** : ~75-85 % du barème
- **Pertinence de la réponse** SAV : 60-70 % des appels au-dessus du seuil
- **Maîtrise des outils** (SUSI / catalogue) : OK quand le conseiller est expérimenté

### Faiblesses récurrentes (signal fort sur le volume)
1. **Accueil normé "Atlas for Men, [prénom], bonjour"** : taux de conformité < 15 %. **MAIS** l'ASR Dialoga transcrit massivement mal le nom de marque → à valider avec recordings.
2. **Prise de congés normée** : taux de conformité < 10 %.
3. **Personnalisation par le nom du client** : < 3 occurrences par appel.
4. **Codification fin d'appel** : non observable sur transcript pur — angle mort.
5. **Rebond commercial Cde Tél** : 1 seule proposition au lieu de 2 dans ~60 % des cas. **GB Cde Tél : ~50 % de SI sur ce critère** = signal structurel.
6. **Délai de traitement SAV** : non communiqué = SI fréquent.
7. **PCI-DSS** : annonce "I'll secure the line" présente, mais **réactivation enregistrement quasi-jamais explicite**.

### Erreurs ASR systémiques flaggées
Le système ASR Dialoga transcrit **très mal "Atlas for Men"** :
- FR : "la plateforme", "la classe formelle", "la place Tian'anmen"
- EN : "Atlas Amenities", "Atlas from NHL", "Atlas from Inn"
- DE : "Atlas Moment", "Atlas Wo man immer Fische"
- PL : "A Platforma", "Atlas Form"
- CZ : "platformách", "Atlas Forman"

**Ne pas sanctionner sur cette base sans validation audio.**

## Situations Inacceptables (SI)

Les SI sont **inscrites dans chaque audit JSON** (champ `SI_detectees`) et reportées en cellule "commentaire" de l'Excel. Patterns observés :
- **GB Cde Tél** : forte concentration de SI sur le critère 12 (Rebond commercial) — signal structurel sur le script anglais
- **PCI-DSS** : 1-2 SI critiques par chunk où le numéro CB est dicté avec enregistrement actif (à VÉRIFIER en audio)
- **Critère 13 SAV (Délai de traitement)** : pattern de SI à investiguer

**Tous les SI détectés doivent être revus manuellement** par un superviseur AFM (avec l'enregistrement audio) avant action RH/coaching.

## Limitations connues

1. **Transcript-only** : pas d'audio fourni
2. **Codification fin d'appel** : non détectable sur transcript pur
3. **Diarisation ASR imparfaite** : certains transcripts mélangent les Speaker
4. **Pas de gold standard humain** : aucune calibration manuelle vs IA
5. **Couverture partielle (40 %)** : 3206 audits IA restants à faire après reset rate-limit
6. **Prestataire non identifiable** : cellule à "Multi / IA"
7. **GB SAV : 7 JSONs corrompus** lors d'un subagent interrompu (skipped)

## Pipeline reproductible

```bash
# 1. Auto-générer les audits NA pour fichiers <500B (instantané)
python pipeline/auto_na_audits.py

# 2. Re-classifier avec seuil 500B
python pipeline/classify_and_sample.py

# 3. Générer les chunks pour subagents (skip déjà faits)
python pipeline/make_subagent_chunks.py

# 4. (Manuel via Claude) lancer les audits par chunks restants

# 5. Remplir les Excel
python pipeline/fill_excel.py
```

---
**Audit produit par Claude IA — 2202 audits livrés (40 % du corpus) — v1 massif partiel — à valider avant exploitation RH/coaching.**

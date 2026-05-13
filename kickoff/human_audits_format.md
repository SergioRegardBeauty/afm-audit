# Format attendu pour les audits humains (calibration)

## Ce qu'il me faut

**5 audits minimum** déjà faits par un superviseur AFM, idéalement :
- 3 audits **Cde Tél** dans le template `BQ_1_CdesTel_10 (2).xlsx`
- 2 audits **SAV** dans le template `BQ_4_Sav_10_ (2).xlsx`

(Plus de 5 = encore mieux. 10-20 audits = calibration robuste.)

## Pour chaque audit, j'ai besoin de

| Info | Détail |
|------|--------|
| **ID appel** | Identifiant unique : numéro de téléphone + date+heure de l'appel, ou n° dossier Dialoga, ou nom du fichier MP3/CSV correspondant |
| **Notes par critère** | Toutes les colonnes "note" remplies (15 critères pour BQ_1, 16 pour BQ_4) avec la valeur AFM (0, 0.2, 0.5, 1, etc.) |
| **Notation** (qualitative) | Maîtrisé / À perfectionner / Non maîtrisé / SI / NA |
| **Commentaire global** | Le texte rédigé par l'évaluateur |
| **Évaluateur** | Nom ou identifiant de la personne qui a fait l'audit |
| **Date contrôle** | Date à laquelle l'audit humain a été fait |

## Où me les déposer

Crée le dossier suivant dans le projet :

```
f:\WORK\Audit_Dialoga_AtlasForMen_2026\gold_standard\
  ├── BQ_1_CdesTel_human_<NOM_EVALUATEUR>.xlsx
  └── BQ_4_Sav_human_<NOM_EVALUATEUR>.xlsx
```

Tu peux aussi me les déposer comme tu veux :
- Excel complet avec toutes les lignes remplies à la main
- CSV exporté
- Screenshots de la grille remplie (je transcrirai)

## Idéal : appels qui sont DÉJÀ dans notre corpus

Pour comparer apple-to-apple IA vs humain, sélectionne des appels **présents dans nos dossiers Drive** (ceux que mon pipeline a déjà ou va auditer). Comme ça je peux faire la comparaison directe par `n_appel`.

Si les audits humains existants portent sur des appels **différents**, je peux quand même calibrer mais l'écart sera moins précis (corpus différent = biais possibles).

## Ce que je vais faire avec

1. **Importer** ton fichier dans `gold_standard/`
2. **Re-auditer ces mêmes appels** par mon pipeline IA (un run isolé tagué `calibration_v1`)
3. **Calculer l'écart par critère** :
   - Écart note totale (humain vs IA)
   - Matrice de confusion sur les notations (Maîtrisé/À perf/Non/SI)
   - Identifier les critères où l'IA est trop sévère ou trop laxiste
4. **Itérer le prompt** si l'écart > 15 % sur la note totale ou sur 3+ critères
5. **Re-tester** jusqu'à convergence
6. **Publier la calibration** dans `output/calibration_report.md`

## Question utile à poser à ton superviseur

> "Pour la calibration de l'IA d'audit, est-ce que tu peux me fournir 5 grilles que tu as remplies récemment ? Idéalement avec les commentaires détaillés. C'est mon training set pour mesurer si l'IA est aussi exigeante que toi."

Beaucoup de superviseurs ont des grilles déjà remplies sur leurs disques perso, ça peut être très rapide à récupérer.

## Quand tu les as

Dis-moi simplement "j'ai déposé les audits humains dans gold_standard/". Je relancerai la pipeline en mode calibration et je te livrerai le rapport d'écart sous 24h (modulo le rate-limit Anthropic).

# Workflow n8n — Audit IA Atlas For Men avec 10 onglets par pays/flux

## Architecture v2

```
Trigger (Manual / Webhook)
  ↓
List Files in Drive Folder
  ↓
Build File Cards + detect pays  ← detecte FR/GB/DE/PL/CZ depuis prefixe tel
  ↓
Loop Files (batch 5)
  ↓
Get Sheet Metadata → Build Values URL → Get Sheet Values
  ↓
Build AFM Prompt (Cde Tel | SAV)  ← detecte flow + construit prompt grille AFM
  ↓
Audit Claude (LangChain ChainLlm) ←─ Anthropic Claude Sonnet 4.6
  ↓
Format Audit AFM (flatten per critere)  ← explose chaque critere en 3 colonnes
  ↓
Route by flow (cde_tel | sav)   ← SWITCH NODE
  ├─→ Append to {pays}_CdesTel (15 criteres × 3 cols)
  └─→ Append to {pays}_Sav     (16 criteres × 3 cols)
```

## Tabs Google Sheet generes

10 onglets dans le Sheet `1xK08z0SYitPHm11a4jmAn0aITQTn6D1EO3vn6T1_8o8` :

| Onglet | Flux | Critères | Colonnes |
|--------|------|----------|----------|
| `FR_CdesTel` | Commande Tél | 15 | 14 meta + 45 critères + 9 trailing = 68 |
| `FR_Sav` | SAV | 16 | 14 meta + 48 critères + 9 trailing = 71 |
| `GB_CdesTel` | Commande Tél | 15 | 68 |
| `GB_Sav` | SAV | 16 | 71 |
| `DE_CdesTel` | Commande Tél | 15 | 68 |
| `DE_Sav` | SAV | 16 | 71 |
| `PL_CdesTel` | Commande Tél | 15 | 68 |
| `PL_Sav` | SAV | 16 | 71 |
| `CZ_CdesTel` | Commande Tél | 15 | 68 |
| `CZ_Sav` | SAV | 16 | 71 |

## Étapes pour faire marcher le workflow

### Étape 1 — Créer les 10 onglets (1 minute)

1. Ouvre ton Sheet : https://docs.google.com/spreadsheets/d/1xK08z0SYitPHm11a4jmAn0aITQTn6D1EO3vn6T1_8o8/
2. Menu **Extensions → Apps Script**
3. Colle le contenu de [`create_sheet_tabs.gs`](create_sheet_tabs.gs)
4. Sauve (Ctrl+S), puis **Run → createAllAfmTabs**
5. Autorise l'accès à ton Sheet
6. Les 10 onglets sont créés avec les en-têtes corrects

### Étape 2 — Créer la credential Anthropic dans n8n

1. n8n → **Settings → Credentials → New → Anthropic API**
2. Nom : `Anthropic API`
3. API Key : ta clé `sk-ant-...` (depuis console.anthropic.com)
4. Save → note l'`id` de la credential

### Étape 3 — Importer le workflow

1. n8n → **Workflows → Import from File** → [`Atlas For Men - Audit IA des appels (Claude direct).json`](Atlas For Men - Audit IA des appels (Claude direct).json)
2. Ouvre le node **Anthropic Claude Sonnet 4.6**
3. Remplace la credential `REPLACE_WITH_ANTHROPIC_CREDENTIAL_ID` par celle créée à l'étape 2
4. Vérifie le node **List Files in Drive Folder** : `folderId` pointe vers ton dossier Drive contenant les transcripts
5. Vérifie les nodes **Append to {pays}_CdesTel** et **Append to {pays}_Sav** : `documentId` = ton Sheet ID

### Étape 4 — Test sur quelques fichiers

1. Mets temporairement le dossier source à un dossier avec **3-5 fichiers** seulement
2. Active le workflow et clique **Execute workflow**
3. Va voir dans ton Sheet : les lignes apparaissent dans les bons onglets selon (pays, flux)

### Étape 5 — Lancement complet

Une fois le test OK, pointe le `folderId` sur ton dossier complet et relance.

## Détection automatique pays

À partir du préfixe téléphonique dans le nom de fichier :

| Préfixe filename | Pays | Onglet routé |
|------------------|------|--------------|
| `0033...` | FR | `FR_CdesTel` ou `FR_Sav` |
| `0044...` | GB | `GB_CdesTel` ou `GB_Sav` |
| `0049...` | DE | `DE_CdesTel` ou `DE_Sav` |
| `0048...` | PL | `PL_CdesTel` ou `PL_Sav` |
| `00420...` | CZ | `CZ_CdesTel` ou `CZ_Sav` |

## Détection automatique flow

Le node **Build AFM Prompt** scanne le transcript pour mots-clés multilingues :

**Signaux SAV forts** :
- FR : `remboursement`, `réclamation`, `j'ai passé une commande`, `où est ma commande`, `retour`
- EN : `refund`, `complaint`, `where is my order`, `i placed an order`
- DE : `Erstattung`, `Reklamation`, `wo ist meine Bestellung`
- PL : `zwrot`, `reklamacja`
- CZ : `vrácení`, `reklamac`

**Signaux Cde Tél** :
- FR : `passer une commande`, `code avantage`
- EN : `place an order`, `promo code`
- DE : `Bestellung aufgeben`, `Vorteilscode`
- PL : `chcę zamówić`, `kod rabatowy`
- CZ : `chci objednat`, `slevový kód`

Par défaut → `cde_tel` (flux majoritaire).

## Structure des colonnes par onglet

### Métadonnées (14 cols, identiques cde_tel et sav)
1. currentDate
2. pays
3. langue_appel
4. flow
5. nom_fichier
6. n_appel (basename sans .mp3.csv)
7. agent (extrait par l'IA)
8. n_client
9. n_cde
10. n_tel
11. DMT_DMC (durée mm:ss)
12. type
13. demande_client (résumé 1 phrase)
14. duree_appel_secondes

### Critères Cde Tél (45 cols : 15 critères × 3)
Pour chaque critère `<key>` : `<key>_note`, `<key>_bareme`, `<key>_notation`

Liste : `1_accueil`, `2_identification`, `3_climat`, `4_mise_en_attente`, `5_conclusion`, `6_prise_conges`, `7_personnalisation`, `8_pre_commande`, `9_commande`, `10_outils`, `11_coord_bancaires`, `12_rebond_commercial`, `13_objection`, `14_ecoute_active`, `15_accompagnement`

### Critères SAV (48 cols : 16 critères × 3)
Liste : `1_accueil`, `2_identification`, `3_mise_en_attente`, `4_conclusion`, `5_prise_conges`, `6_personnalisation`, `7_climat`, `8_maitrise_directivite`, `9_decouverte_reformulation`, `10_pertinence_reponse`, `11_outils`, `12_codification`, `13_delai_traitement`, `14_experience_client`, `15_ecoute_empathie`, `16_enchantement`

### Trailing (9 cols, identiques cde_tel et sav)
- note_totale_sur_10
- note_sur_100
- note_zero_par_SI (booléen)
- SI_count
- SI_details (liste compacte des SI détectées)
- commentaire_global (français)
- commentaire_traduit_fr (si appel non-FR)
- criteres_full_json (JSON complet avec justifications + timestamps)
- audit_version (= `n8n_claude_v2`)

## Lien avec les Excel BQ_1 / BQ_4 existants

Les onglets `*_CdesTel` ont **les mêmes critères** que le template `BQ_1_CdesTel_10 (2).xlsx` :
- Ordre des critères : identique
- Note + barème : par critère, comme dans l'Excel
- En plus : `notation` (Maîtrisé/A perf/Non/SI/NA) en colonne supplémentaire

Pareil pour les onglets `*_Sav` ↔ template `BQ_4_Sav_10_ (2).xlsx`.

Tu peux donc :
- Soit consulter les audits **directement dans Google Sheets** (1 onglet par pays/flux)
- Soit **exporter chaque onglet en CSV** et le coller dans les templates Excel BQ_1/BQ_4 existants

## Coût et limites

- **Modèle** : Claude Sonnet 4.6. Pour aller moins cher, change pour `claude-haiku-4-5-20251001` dans le node Anthropic.
- **Tokens** : ~5-6K tokens par audit (input + output). À ~3-5 $/million → **~0.025 $ par audit**.
- **5533 audits AFM total = ~140 $**.
- **Rate-limit** : batch size 5, augmente à 10 si ton tier Anthropic le permet.
- **Transcript max** : tronqué à 8000 caractères (début 5K + fin 2.5K).

## Comparaison v1 → v2

| v1 (workflow original) | v2 (cette version) |
|------------------------|--------------------|
| 1 seul onglet plat | **10 onglets par (pays, flux)** |
| 24 colonnes génériques | **68/71 colonnes** mirroir BQ_1/BQ_4 |
| Critères dans 1 colonne JSON | **Chaque critère = 3 colonnes** (note + barème + notation) |
| OpenRouter GPT-4o-mini | **Anthropic Claude Sonnet 4.6** |
| Prompt générique | **Grille AFM complète** par flux |

## Si quelque chose ne marche pas

| Symptôme | Cause probable | Solution |
|----------|----------------|----------|
| Erreur "Sheet not found" | Onglet pas créé | Lance `createAllAfmTabs` dans Apps Script |
| Toutes les lignes dans FR | Détection pays ratée | Vérifie que les filenames commencent par `0033`, `0044`, etc. |
| Toutes les lignes dans cde_tel | Détection flow ratée | Vérifie les mots-clés dans le transcript |
| Erreur Anthropic | Credential | Vérifie `Settings → Credentials → Anthropic API` |
| Tab vide | Switch ne route pas | Vérifie que `$json.flow` est bien `cde_tel` ou `sav` dans Format node |

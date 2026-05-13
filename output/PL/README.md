# Audit qualite IA — PL — 2026-05-12

## Livrables
- `BQ_1_CdesTel_PL.xlsx` — grille AFM Commande Telephone remplie (20 audits)
- `BQ_4_Sav_PL.xlsx` — grille AFM SAV remplie (3 audits)
- `audits_json/` — JSON brut de chaque audit (1 fichier par appel)

## Methodologie
1. Echantillonnage exhaustif de transcripts substantiels (>3KB) parmi les
   exports CSV Dialoga, mois de janvier 2026.
2. Classification automatique Cde Tel / SAV par mots-cles multilingues.
3. Audit IA appel par appel selon les grilles BQ_1 / BQ_4 et le prompt
   `prompts/audit_cde_tel_v1.md` ou `prompts/audit_sav_v1.md`.
4. **Evaluation transcript-only** (pas de recording fourni) : les criteres lies
   au ton/sourire/empathie sont evalues sur les indices textuels uniquement
   (interjections, formulations positives, longueurs de pauses).

## Note pour la lecture du fichier Excel
Les templates ont ete etendus dynamiquement pour accueillir tous les audits du
mois (jusqu'a plusieurs centaines de lignes). Le bloc "sous total / total" en
bas a ete decale ; les formules originales (qui couvraient les 10 premieres
lignes) peuvent etre obsoletes. Recalculer manuellement ou utiliser un tableau
croise dynamique pour les analyses agregees.

## Limitations
- Les **Situations Inacceptables (SI)** detectees doivent etre **revues
  manuellement** avant toute action RH/coaching.
- L'identification du **prestataire** ne peut pas etre deduite du transcript :
  cellule "prestataire" laissee a "Multi / IA".
- Les criteres Climat / Empathie sont moins fiables sur transcript seul.
- Erreurs ASR frequentes sur "Atlas for Men" — flagges dans les justifications.

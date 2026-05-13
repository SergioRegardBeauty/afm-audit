/**
 * Google Apps Script — Cree les 10 onglets AFM avec headers.
 *
 * USAGE :
 * 1. Ouvre ton Google Sheet (https://docs.google.com/spreadsheets/d/1xK08z0SYitPHm11a4jmAn0aITQTn6D1EO3vn6T1_8o8/)
 * 2. Menu Extensions > Apps Script
 * 3. Colle ce code, sauve, puis lance "createAllAfmTabs"
 * 4. Reviens dans ton Sheet : 10 onglets sont crees (FR_CdesTel, FR_Sav, GB_CdesTel, ..., CZ_Sav)
 *
 * Tu peux supprimer l'onglet initial "Sheet1" / "Feuille 1" apres si tu veux.
 */

const COUNTRIES = ['FR', 'GB', 'DE', 'PL', 'CZ'];

const META_COLS = [
  'currentDate', 'pays', 'langue_appel', 'flow',
  'nom_fichier', 'n_appel', 'agent', 'n_client', 'n_cde', 'n_tel',
  'DMT_DMC', 'type', 'demande_client', 'duree_appel_secondes'
];

const TAIL_COLS = [
  'note_totale_sur_10', 'note_sur_100', 'note_zero_par_SI',
  'SI_count', 'SI_details', 'commentaire_global', 'commentaire_traduit_fr',
  'criteres_full_json', 'audit_version'
];

const CDE_TEL_KEYS = [
  '1_accueil', '2_identification', '3_climat', '4_mise_en_attente',
  '5_conclusion', '6_prise_conges', '7_personnalisation',
  '8_pre_commande', '9_commande', '10_outils', '11_coord_bancaires',
  '12_rebond_commercial', '13_objection', '14_ecoute_active', '15_accompagnement'
];

const SAV_KEYS = [
  '1_accueil', '2_identification', '3_mise_en_attente', '4_conclusion',
  '5_prise_conges', '6_personnalisation', '7_climat',
  '8_maitrise_directivite', '9_decouverte_reformulation',
  '10_pertinence_reponse', '11_outils', '12_codification',
  '13_delai_traitement', '14_experience_client', '15_ecoute_empathie',
  '16_enchantement'
];

function buildHeaders(criteresKeys) {
  const cols = [...META_COLS];
  for (const k of criteresKeys) {
    cols.push(k + '_note', k + '_bareme', k + '_notation');
  }
  cols.push(...TAIL_COLS);
  return cols;
}

function createAllAfmTabs() {
  const ss = SpreadsheetApp.getActiveSpreadsheet();
  const cdeHeaders = buildHeaders(CDE_TEL_KEYS);
  const savHeaders = buildHeaders(SAV_KEYS);

  for (const country of COUNTRIES) {
    createOrResetTab_(ss, country + '_CdesTel', cdeHeaders);
    createOrResetTab_(ss, country + '_Sav', savHeaders);
  }

  SpreadsheetApp.flush();
  SpreadsheetApp.getUi().alert(
    '10 onglets crees / mis a jour :\n' +
    COUNTRIES.map(c => '  - ' + c + '_CdesTel (' + cdeHeaders.length + ' col)').join('\n') +
    '\n' +
    COUNTRIES.map(c => '  - ' + c + '_Sav (' + savHeaders.length + ' col)').join('\n')
  );
}

function createOrResetTab_(ss, tabName, headers) {
  let sheet = ss.getSheetByName(tabName);
  if (!sheet) {
    sheet = ss.insertSheet(tabName);
  }
  // Ecrit les headers en ligne 1
  sheet.getRange(1, 1, 1, headers.length).setValues([headers]);
  sheet.getRange(1, 1, 1, headers.length)
    .setFontWeight('bold')
    .setBackground('#f0f0f0');
  // Freeze la 1ere ligne
  sheet.setFrozenRows(1);
  // Auto-resize (limite a max 100 colonnes)
  for (let c = 1; c <= Math.min(headers.length, 100); c++) {
    sheet.autoResizeColumn(c);
  }
}

# AUDIT TÉLÉCOMS — DIALOGA / HYDRA — ATLAS FOR MEN
**Compte :** ATLASFORMEN, S.A.S.U.  
**Portail :** https://manager.dialogagroup.com (Dialoga Central Manager / Hydra)  
**Date de l'audit :** 10/05/2026  
**Mode :** lecture seule — aucune modification de configuration  
**Légende :** ✅ confirmé en interface · ⚠️ partiel · ❓ incertain / à demander à Dialoga · 🔒 verrouillé (lecture seule pour l'utilisateur) · 🛠️ configurable

---

## 1. NUMÉROS / LIGNES

**Chemin :** `Accueil > Services > Gestion des services` (`/bin/gestionservicios/validar.asp`)

### 1.1 Vue d'ensemble
- **Total services déclarés :** 459
- **Services labellisés (avec libellé exploitable) :** ~158
- **Pays couverts :** FR, BE, CH, NL, DE, AT, PL (7 marchés Atlas For Men)
- **Groupes de services :** 5 (FR, BE, CH/NL, AT, PL/DE) — chemin `Services > Groupes de services` (`/bin/gruposServicios/gruposServicios.asp`)
- **Produits déclarés :** 4 (chemin `Services > Produits` — `/bin/productos/validar.asp`)

### 1.2 Lignes-clés identifiées
| Numéro | Pays | Libellé interne | Queue cible | Type |
|---|---|---|---|---|
| 890155995 | FR | DCS FID | K3 (DCS) | SAV / Fidélisation |
| 0033… (cluster FR) | FR | Commande Tel / SAV FR | K3 / queues FR | Voix entrante |
| 003278790094 | BE | BE SAV | Queue BE | SAV Belgique |
| Numéros CH, NL, DE, AT, PL | EU | SAV multi-pays | Queues localisées | SAV |

✅ Les libellés "DCS FID", "BE SAV", "OUTSOURCIA" apparaissent explicitement dans les listes.  
⚠️ Le **volume mensuel par numéro** n'est pas affiché dans la fiche service ; il faut passer par **Statistiques > Voice Routing** (filtré par n°) ou les rapports archivés.  
🛠️ Le statut actif/test n'est pas explicite dans la liste — il faut ouvrir la fiche service.

### 1.3 Points configurables / verrouillés
- 🛠️ Routage par n° (queue de destination) — visible dans `VerServicio('xxx')`
- 🔒 Numérotation elle-même (les DDI ne se créent pas côté portail — pilotage Dialoga)
- ❓ Statut "actif/test" exhaustif par numéro

---

## 2. IVR ACTUEL (Trident — Gestion des Menus)

**Chemin :** `Accueil > Routage Centralita > Gestion des Menus` (`/bin/enrutamiento_Centralita/validar.asp`)

### 2.1 Cartographie 890155995 (DCS FID — France)
Arborescence observée (Trident editor) :
- **Entrée** → nœud Calendrier (horaires)
- **Branche ouverte** → nœud Dialogue (prompt FR + Menu DTMF)
- **Branche fermée** → message TTS "service fermé"
- Nœuds enfants : Transfert vers queue K3, Sortie, Application/Logiciel
- Types de nœuds vus : **Dialogue**, **Dialogue REC**, **Menu**, **Calendrier**, **Transfert**, **Application/Logiciel**, **Sortie**, **TTS**

### 2.2 Cartographie 003278790094 (BE SAV)
- Structure similaire : Calendrier → Dialogue (NL/FR selon choix langue) → Menu DTMF → Transfert vers queue BE
- Prompt initial multilingue (NL/FR) confirmé

### 2.3 Données capturées
- **Langues détectées dans les prompts :** FR, NL, DE, EN (selon ligne)
- **Horaires d'ouverture :** définis via nœud **Calendrier** (par ligne)
- **DTMF :** menu présent ✅, **détail des touches non capturé** (popup bloquée par sandbox lors de l'ouverture du nœud Menu)
- **Speech / ASR :** branches speech possibles via Dialogue REC

### 2.4 Configurable / verrouillé
- 🛠️ Édition de l'arbre Trident (drag-drop des nœuds)
- 🛠️ Calendrier (horaires) modifiable par ligne
- ❓ Détail exact des touches DTMF par menu — non extrait (popup sandbox)
- ❓ Horaires précis (heures de bascule) par ligne — non extraits par script

---

## 3. QUEUES / SKILLS

**Chemin :** `Accueil > Routage Centralita > Files d'attente` (`/bin/Enrutamiento_Centralita/configurarColas.asp`)

### 3.1 Volumétrie
- **Total queues :** 114
- **Skillsets :** 24 (chemin `Agents > Skillsets — mostrarGrupos()`)
- **Habilités :** 12
- **Groupes d'agents :** 6
- **Groupes de queues (statistiques) :** 2 (DCS, OUTSOURCIA) via `GruposColasStats`

### 3.2 Exemple détaillé — Queue **K3 (DCS)** (ID 34224)
- Capacité : **99 appels simultanés en conversation / 1 000 en file d'attente**
- Stratégie de routage : **par compétence / longest waiting agent**
- SLA configuré : seuil de service défini (cible décroché)
- Music on hold + annonce de position activées
- Sortie de file (timeout) → renvoi vers branche IVR alternative
- Mapping : K3 ↔ skillset DCS FID ↔ agents DCS

### 3.3 Configurable / verrouillé
- 🛠️ Stratégie, SLA, taille de file, music, débordement
- 🛠️ Mapping queue ↔ skill ↔ agents
- 🔒 Capacité matérielle globale (concurrent calls compte) — non visible
- ❓ SLA par queue exhaustif (114 queues) — non extrait individuellement (volume)

---

## 4. AGENTS

**Chemin :** `Accueil > Gestion des Agents` (`/bin/gestionagentes/clientes/validar.asp`)

### 4.1 Volumétrie
| Élément | Nombre |
|---|---|
| Agents | **196** |
| Superviseurs | **28** |
| Skillsets | **24** |
| Habilités | **12** |
| Groupes d'agents | **6** |
| États indisponibles | **9** |

### 4.2 États indisponibles configurés
9 codes pause/Not-Ready (typiquement : Pause, Repas, Formation, Réunion, Backoffice, Coaching, Wrap-up, etc.)

### 4.3 Skills par agent
- ⚠️ Per-agent skill mapping **non extrait individuellement** (196 fiches — volume).
- ✅ Agrégation par skillset visible dans `mostrarGrupos`.
- ✅ Langues parlées implicites via skillsets multilingues (FR/NL/DE/EN/PL).

### 4.4 Indicateurs agent visibles
- ⚠️ Login moyen / temps pause / AHT par agent : pas dans la fiche directement — disponible via **Statistiques Call Center par agent** (`/bin/estadisticas_emplazamiento/estadisticas.asp`).
- ⚠️ Mots de passe agents apparaissent **en clair** dans la liste — point sécurité à signaler.

### 4.5 Configurable / verrouillé
- 🛠️ Création/édition agents, skills, habilités, états
- 🛠️ Affectation à groupe / superviseur
- 🔒 Limite globale d'agents simultanés (sièges) — non visible

---

## 5. KPIs DISPONIBLES (30 derniers jours)

**Chemins :**
- Voice Routing : `Statistiques > Voice Routing` (`/bin/estadisticas_voice_routing/estadisticas.asp`)
- Call Center : `Statistiques > Centre d'appels` (`/bin/estadisticas_emplazamiento/estadisticas.asp`)
- Files d'attente : `Statistiques > Files d'attente` (`/bin/estadisticas_colas/estadisticas.asp`)

### 5.1 Volumes globaux 30j
| Périmètre | Appels |
|---|---|
| **Voice Routing (entrant brut)** | **531 928** |
| **Call Center (entré dans queues)** | **120 472** |
| Ratio queue/brut | ~22,6 % (reste = SVI / hors heures / abandon avant queue) |

### 5.2 Indicateurs disponibles
- ✅ Volume entrant total et par numéro (filtre par service)
- ✅ Taux de décroché / abandon (Call Center)
- ✅ AHT (durée moyenne conversation) — par queue / agent / groupe
- ✅ ASA (vitesse moyenne de réponse)
- ✅ Distribution **horaire** (capturée 30j) et par jour de semaine
- ✅ Stats files d'attente par groupe (DCS, OUTSOURCIA) sur 10j et 30j
- ⚠️ Taux de transfert IVR → agent : déductible (Voice Routing − Call Center) mais **pas exposé directement comme KPI**

### 5.3 Rapports archivés
- ✅ Rapports mensuels archivés disponibles : Avril 2026 → Octobre 2025 (`/bin/informes/calendario_informes.asp`)
- ⏱️ Rate-limit : 60 secondes entre deux générations

---

## 6. ENREGISTREMENTS

**Chemin :** Paramètres queue / nœud "Dialogue REC" dans Trident

### 6.1 Constats
- ✅ Enregistrement à la demande (on-demand recording) configurable par queue
- ✅ Options de chiffrement disponibles (encryption flags vus dans la conf)
- ❓ **Politique de rétention** : non affichée dans l'UI
- ❓ **Format des fichiers** (wav/mp3, codec, mono/stéréo) : non affiché
- ❓ **Accès programmatique** (SFTP / S3 / API REST) : non visible côté portail
- ❓ **Métadonnées attachées** (CDR : agent, queue, durée, n° appelant…) : non documenté côté UI

### 6.2 Configurable / verrouillé
- 🛠️ Activation/désactivation par queue, encryption
- 🔒 Backend de stockage et durée → côté Dialoga

---

## 7. INTÉGRATIONS

### 7.1 Webhooks
- ❌ Aucun webhook explicitement configuré dans le portail
- ⚠️ Le nœud **"Application/Logiciel"** dans Trident est le candidat le plus probable pour un appel HTTP / API externe — **fonctionnement exact à confirmer**

### 7.2 Connecteurs CRM / ERP
- ❌ Aucun connecteur natif (Salesforce, Zendesk, Dynamics…) visible dans la conf

### 7.3 APIs Dialoga
- ❓ Aucune documentation d'API REST / SOAP exposée dans l'UI
- 🛠️ `hydra_im_manager` apparaît comme module séparé (omnicanal) — accès et scope à clarifier

### 7.4 Configurable / verrouillé
- 🔒 Mise à disposition d'API → demande Dialoga

---

## 8. CAPACITÉS IA

### 8.1 TTS (Text-to-Speech)
- ✅ TTS disponible dans nœuds Dialogue
- ❓ **Liste exhaustive des voix** (genre, accent, qualité neural/standard) non visible

### 8.2 ASR (Speech Recognition)
- ✅ **120 langues ASR** déclarées
- ✅ Moteur **Utopia** : 33 langues additionnelles
- ✅ **Barge-in** supporté (interruption pendant prompt)

### 8.3 Nœuds avancés (Trident)
- ✅ `Dialogue REC` : enregistrement/dialogue
- ✅ `Application/Logiciel` : appel externe potentiel (webhook ?)
- ❓ Distinction exacte entre **Dialogue** et **Dialogue REC** à confirmer
- ❓ Le nœud Application/Logiciel supporte-t-il HTTP REST (méthode, headers, parsing de réponse) ?

---

## 9. CONTRAINTES

### 9.1 Volumétrie déclarée
- **Plateformes (fournisseurs SIP) déclarées :** 0
- **Groupes de terminaison :** 0
- **Origines :** 0
> ⇒ Tout le routage SIP/transport est **opéré côté Dialoga** ; aucune trunk gérable côté client.

- **Queue K3 (DCS) :** 99 appels simultanés / 1 000 en file
- ❓ **Capacité globale du compte** (concurrent calls plafond, channels) — **non visible**

### 9.2 Canaux activés / désactivés (page d'accueil)
✅ **Activés :** Voice Routing, Call Center, Gestion des menus (Trident), Statistiques  
❌ **Désactivés** ("box disabled" sur la home) : Mail Push, **Voice Push (= robocalls / outbound massif)**, SMS Push, IM Push, Fax Push, IoT Push, IoT Routing, SMS Routing  
> ⇒ Le compte ATLASFORMEN est **purement voix entrant + IVR** ; pas de campagne sortante / SMS / mail / IoT activée.

### 9.3 Process de mise en production
- ❓ Aucun workflow de validation / staging / approval visible dans l'UI
- ❓ Délai SLA pour la mise en prod d'un nouveau flow Trident — **à demander à Dialoga**
- ❓ Existence d'un environnement de test isolé — **non visible**

### 9.4 Backups / Délégation
- ✅ Bouton **"BACKUP : Délégation de routage"** présent (page Routage Centralita)
- ❓ Mécanisme exact de bascule (manuel ? automatique ? cible ?) à clarifier

### 9.5 Limites techniques observées
- ⏱️ Rate-limit **60 secondes** entre deux générations de rapport (configurable ?)
- 🔒 Modèle frame-based historique (tope/cuerpo) — pas d'API REST côté UI

---

## ANNEXE — QUESTIONS À POSER À DIALOGA

### Architecture & capacité
1. Quelle est la **capacité globale** du compte (concurrent calls maximum, nb de channels SIP réservés) ?
2. Pourquoi 0 plateforme / 0 groupe de terminaison / 0 origine côté UI ? (transport 100 % opéré Dialoga ?)
3. Le rate-limit de 60 s entre rapports est-il configurable ?

### Mise en production / change management
4. Quel est le **process de validation / déploiement** d'un nouveau flow Trident (validation Dialoga obligatoire ? auto-publish ? délai SLA ?) ?
5. Existe-t-il un **environnement de test / staging** distinct de la prod ?
6. À quoi sert exactement le bouton **"BACKUP : Délégation de routage"** et comment se déclenche-t-il ?

### Enregistrements
7. Quelle est la **politique de rétention** des enregistrements (durée, où ils sont stockés, RGPD) ?
8. Quel est le **format exact** (wav/mp3, codec, stéréo agent/client séparés) ?
9. Existe-t-il un **accès programmatique** (SFTP / S3 / API REST) aux enregistrements ?
10. Quelles **métadonnées CDR** sont exportables programmatiquement (n° appelant, agent, queue, durée, DTMF saisis…) ?

### APIs & intégrations
11. Une **API REST / SOAP** est-elle exposée par Dialoga ? (endpoint, authentification, documentation)
12. Le nœud **"Application/Logiciel"** dans Trident est-il un véritable **HTTP webhook** ? Méthodes supportées (GET/POST/PUT), headers personnalisables, parsing JSON de la réponse ?
13. Quels **connecteurs CRM natifs** sont disponibles (Salesforce, Zendesk, Dynamics, HubSpot…) ?
14. **Hydra IM Manager** : scope exact, modalité d'accès, périmètre omnicanal (mail, chat, WhatsApp, SMS) ?

### IVR / Trident
15. Détail exhaustif du **menu DTMF** de la ligne 890155995 (DCS FID) — popup bloquée durant l'audit.
16. **Horaires d'ouverture exacts** par ligne (lecture du Calendrier ligne par ligne).
17. Différence fonctionnelle entre nœud **Dialogue** et nœud **Dialogue REC**.
18. Liste exhaustive des **voix TTS** disponibles (langues, genres, qualité neural/standard).

### Agents / sécurité
19. Pourquoi les **mots de passe agents apparaissent-ils en clair** dans la liste ? (point sécurité critique)
20. Quelle est la **limite de sièges** (agents simultanément connectés) du compte ?
21. Les **per-agent skills** peuvent-ils être exportés en bloc (CSV / API) ?

### Reporting
22. Différence entre **"Groupes de queues"** (1 = DCS) et **"Groupes Stats Files d'attente"** (2 = DCS + OUTSOURCIA) ?
23. Signification précise des **"facteur agents de queue / localisation / limite"** dans la conf K3 ?
24. Le **taux de transfert IVR → agent** est-il exposé directement comme KPI ?

### Canaux désactivés
25. Activation possible (et conditions) de **Voice Push / robocalls outbound massif**, SMS Push, Mail Push si Atlas For Men le souhaite ?

---

**Fin de l'audit — 9 sections + 25 questions ouvertes pour Dialoga.**

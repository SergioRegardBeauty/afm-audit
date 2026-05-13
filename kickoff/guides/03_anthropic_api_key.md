# Guide 03 — Clé API Anthropic (5 min)

## Si tu en as déjà une (n8n)
Tu as déjà une credential Anthropic configurée dans n8n (id `WEUBznmlueOuIdVm`).

Tu peux :
- **Réutiliser la même clé** (simple, mais expose tes 2 environnements à la même limite)
- **Créer une seconde clé** dédiée au pipeline Python (recommandé pour isoler les usages)

## Créer une nouvelle clé

1. https://console.anthropic.com/ → login
2. **API Keys** (menu gauche) → **Create Key**
3. Nom : `afm-audit-python` (ou similaire pour identifier l'usage)
4. **Workspace** : ton workspace par défaut
5. Copier la clé `sk-ant-api03-XXXXXXX...` (elle ne sera plus jamais affichée)
6. Coller dans le fichier `.env` :
   ```
   ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXX...
   ```

## Sécurité

⚠️ Ne **jamais** :
- Commit la clé dans le repo Git (le `.gitignore` exclut `.env`, ne crée pas de fichier `key.txt`)
- Partager la clé sur Slack/email
- L'utiliser dans une page web côté client

⚠️ Si fuite : retourne sur la console → **Revoke** la clé → crée-en une nouvelle.

## Limites par tier

Vérifie ton tier à https://console.anthropic.com/settings/limits

Pour le projet AFM (5533 audits × 5K tokens ≈ 28M tokens) :
- **Tier 1** : 50 RPM, 30K ITPM → suffit pour ~6 audits/min en parallèle
- **Tier 2** : 1000 RPM → suffit pour batch massif

Si tu prévois de tout faire rapidement, demande **upgrade à Tier 2** dans la console (Settings → Plans & billing).

## Modèles disponibles

Dans `.env`, tu peux switcher :
- `claude-sonnet-4-6` (recommandé) — meilleur rapport qualité/prix
- `claude-haiku-4-5-20251001` (3-4× moins cher, qualité un peu en dessous)
- `claude-opus-4-7` (le plus fort, mais 5× plus cher que Sonnet)

## Estimation du coût total AFM

| Modèle | Coût par audit | 5533 audits |
|--------|----------------|-------------|
| Haiku 4.5 | ~0.005 $ | **~28 $** |
| Sonnet 4.6 | ~0.020 $ | **~110 $** |
| Opus 4.7 | ~0.100 $ | **~550 $** |

**Recommandation** : Sonnet 4.6 pour le run de calibration, puis Haiku 4.5 si les écarts vs humain sont acceptables.

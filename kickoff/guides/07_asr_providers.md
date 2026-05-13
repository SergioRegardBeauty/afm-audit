# Guide 07 — ASR providers : Deepgram vs AssemblyAI

## Quand en a-t-on besoin ?

**À DÉCIDER après QA des CSV existants.**

Tes transcripts CSV actuels viennent de Dialoga. Sont-ils suffisants ?

| Cas | Action |
|-----|--------|
| Qualité CSV Dialoga acceptable | ❌ Pas besoin d'ASR externe, on utilise ce qu'on a |
| Erreurs ASR systémiques (cf. "Atlas for Men" mal transcrit) | ⚠️ Retranscrire un sous-ensemble pour valider |
| Diarisation cassée (speaker mixup) | ⚠️ Retranscrire avec un meilleur ASR |
| Besoin de timestamps fin de granularité | ⚠️ Retranscrire avec word-level timestamps |

D'après l'analyse v1 (1346 audits), les CSV Dialoga ont :
- **Erreurs systémiques sur "Atlas for Men"** dans toutes les langues
- **Diarisation parfois mélangée** (Speaker 1/2/3/4 confus)
- Sinon **qualité acceptable** pour l'audit qualité

→ **Décision recommandée** : retranscrire un échantillon de 20 appels (4 par pays) avec Deepgram ou AssemblyAI, et comparer avec les CSV Dialoga sur les mêmes appels.

## Comparatif Deepgram vs AssemblyAI

| | Deepgram (Nova-2 / Nova-3) | AssemblyAI (Best / Universal-2) |
|--|----------------------------|----------------------------------|
| **Langues** | 30+ dont FR/EN/DE/PL/CS | 99 langues |
| **Diarisation** | ✅ Excellente | ✅ Très bonne |
| **Tarif** | ~0.0036 $/min (pré-payé) | ~0.0065 $/min (pay-as-you-go) |
| **Latence batch** | ~1.5× la durée audio | ~1× la durée audio |
| **Streaming live** | ✅ | ✅ |
| **Hébergement EU** | Possible (multi-region) | ❌ US par défaut, EU sur demande Entreprise |
| **Détection sentiment** | ❌ | ✅ |
| **Précision FR seniors (qualité audio variable)** | Très bonne | Très bonne (meilleure sur certains cas) |

### Pour Atlas For Men

| Critère | Importance | Gagnant |
|---------|------------|---------|
| Qualité ASR FR + EN + DE + PL + CS | 🔴 critique | Égalité (les deux solides) |
| Diarisation propre (agent vs client) | 🔴 critique | Égalité |
| Hébergement EU pour RGPD | 🔴 critique | **Deepgram** (région EU disponible) |
| Coût (5000 appels × 5 min avg = ~417 h audio) | 🟡 modéré | **Deepgram** (~9 € vs ~16 €) |
| Détection sentiment intégrée | 🟢 nice to have | AssemblyAI |
| Stabilité API | 🔴 critique | Égalité |

→ **Recommandation : Deepgram** pour l'hébergement EU + coût.

## Test rapide Deepgram

### Créer la clé

1. https://console.deepgram.com → Sign up
2. **API Keys** → **Create Key**
3. Nom : `afm-audit-test`
4. Scope : **Member** (par défaut)
5. Copier la clé `Token XXXXXXX...`
6. `.env` :
   ```
   DEEPGRAM_API_KEY=Token XXXXXXX...
   ```

### Activer la région EU

⚠️ Important : pour héberger en EU, contacter Deepgram support (`support@deepgram.com`) pour activer la région **eu-west-1**. Sans ça, les requêtes vont aux États-Unis par défaut.

### Test minimal

```python
from deepgram import DeepgramClient, PrerecordedOptions
import os

dg = DeepgramClient(os.environ["DEEPGRAM_API_KEY"])

with open("test.mp3", "rb") as f:
    response = dg.listen.prerecorded.v("1").transcribe_file(
        {"buffer": f},
        PrerecordedOptions(
            model="nova-2",
            language="fr",
            diarize=True,
            punctuate=True,
            utterances=True,
            smart_format=True,
        )
    )
print(response.results.channels[0].alternatives[0].transcript)
```

### Coût pour le projet

- ~417 h × 60 min × 0.0036 $/min ≈ **90 $** pour ré-transcrire **tous** les appels
- Pour échantillon 20 appels × 5 min ≈ **0.40 $**

## Test AssemblyAI (alternative)

### Créer la clé

1. https://www.assemblyai.com → Sign up
2. **Dashboard** → copier la clé API
3. `.env` :
   ```
   ASSEMBLYAI_API_KEY=XXXXXXXX
   ```

### Test minimal

```python
import assemblyai as aai
import os

aai.settings.api_key = os.environ["ASSEMBLYAI_API_KEY"]

config = aai.TranscriptionConfig(
    speaker_labels=True,
    language_code="fr",
    sentiment_analysis=True,
    auto_chapters=True,
)
transcript = aai.Transcriber().transcribe("test.mp3", config)
print(transcript.text)
```

### Coût pour le projet
- ~417 h × 0.0065 $/min ≈ **162 $** pour tout
- Pour 20 appels ≈ **0.65 $**

## Décision

**Avant d'engager du budget** :
1. Choisir 20 appels (4 par pays) qui ont une note IA basse OU des SI suspects
2. Lancer la retranscription via Deepgram (~0.40 $)
3. Re-passer ces 20 appels dans le pipeline d'audit IA avec les nouveaux transcripts
4. Comparer écarts IA-IA (Dialoga ASR vs Deepgram ASR) :
   - Si écart < 10 % sur la note totale → CSV Dialoga **suffisants**, pas besoin de ré-transcrire
   - Si écart > 20 % → CSV Dialoga **dégradent** la qualité audit, ré-transcrire en prod
5. Décider du go/no-go ré-transcription massive

## Note RGPD

Les ASR providers envoient l'audio vers leurs serveurs pour traitement → **vérifier que l'hébergement de traitement est EU** :
- Deepgram : possible avec demande explicite (région eu-west-1)
- AssemblyAI : US par défaut, EU sur demande Entreprise (compte payant)

Sans ça, c'est un transfert hors UE → DPA (Data Processing Agreement) à signer + analyse d'impact RGPD.

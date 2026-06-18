# B2T crmservices — Discovery API SOAP

_WSDL : `http://192.168.23.28/AFM/WS/WsCustomer/crmservices.svc?wsdl`_
_Endpoint : `http://192.168.23.28/AFM/WS/WsCustomer/crmservices.svc`_
_Généré par `tools/b2t_discovery.py` via `zeep`._

---

## Résumé exécutif — 28 opérations classées par usage

### 🔎 Lecture / consultation (12 opérations)

| Opération | Input clé | Output | Use case dans le projet audit |
|---|---|---|---|
| `GetCustomer` | `IdCrm` + BusLine + Country | Contact + Adresses + Téléphones + Emails + Activité | **Enrichir un audit** avec nom, adresse, statut client à partir du CrmID |
| `GetCRMId` | Country + BusLine + EmetteurId + PaperId + **Name** | CrmId (int) | Retrouver le CrmID depuis un **nom client** (utile si l'agent dit "Mme Dupont" sans n° client) |
| `GetMatchCode` | _(à vérifier dans le détail)_ | MatchCode | Identifier un client par signature (zip + nom + langue) |
| `GetFormattedAddress` | CrmID + Usage | AddressLines | Formater une adresse pour affichage / courrier |
| `GetWebAccount` | _(à voir détail)_ | Account web | Récupérer le compte web associé au CRM |
| `GetOrderToday` | _(à voir détail)_ | Liste commandes du jour | Voir si le client a commandé aujourd'hui (contexte appel) |
| `GetLead` | _(à voir détail)_ | Lead | Récupérer un prospect (avant qu'il soit client) |
| `GetCustomerScores` | CrmId + Names + Type | Liste de scores | Score paiement, fidélité, RFM… |
| `GetCustomerEvCatecories` | busline + countryLang | Catégories d'événements | Lister les motifs d'appel possibles |
| `GetHistoriBanks` | CrmID + Country + Language | Historique CB / IBAN | **⚠️ contient les CB** : à manipuler avec précaution PCI-DSS |
| `GetPassword` | _(à voir détail)_ | Password | Demande de mdp _(probablement obsolète, voir `ResetPassword`)_ |
| `Login` | _(à voir détail)_ | Auth result | Authentification web account |

### ✏️ Écriture / création (8 opérations)

| Opération | Use case |
|---|---|
| `SetCustomer` | Créer un nouveau client (nom, adresse, etc.) |
| `SetLead` | Créer un prospect |
| `SetScore` | Affecter un score (paiement, etc.) à un client |
| `SetCallCenter` | Logger qu'un agent a traité un appel pour ce client _(potentiellement utile pour le projet)_ |
| `SetMainFrameId` | Lier un client à un identifiant mainframe externe |
| `CreateWebAccount` | Créer un compte web pour un client existant |
| `AttachWebAccount` | Rattacher un compte web déjà existant à un CrmID |
| `PublishMailling` | Pousser une campagne email |

### 🔄 Mise à jour (5 opérations)

| Opération | Use case |
|---|---|
| `UpdateCustomer` | Modifier les coords / optins d'un client existant |
| `UpdateLead` | Modifier un prospect |
| `UpdateScore` | Recalculer un score |
| `UpdateWebAccount` | Modifier login / mdp / langue d'un compte web |
| `ResetPassword` | Régénérer un mdp et l'envoyer au client |

### 🗑️ Suppression (3 opérations)

| Opération | Use case |
|---|---|
| `DeleteAddress` | Supprimer une adresse d'un client |
| `DeleteWebAccount` | Supprimer un compte web |
| `AnonymisationCustomer` | **RGPD** : anonymiser tous les PII d'un client (droit à l'oubli) |

---

## Opérations prioritaires pour le projet audit IA Atlas For Men

Pour enrichir les audits IA des appels téléphoniques avec le contexte client réel :

1. **`GetCustomer(IdCrm, BusLine=4, Country=FR)`** ← le plus utile, déjà testé OK
2. **`GetCRMId(Name, BusLine, Country)`** ← pour trouver le CrmID quand on n'a que le nom (le n° de tel du fichier transcript ne suffit pas toujours)
3. **`GetOrderToday(CrmID)`** ← contexte "commande du jour" pour les appels Cde Tél
4. **`GetCustomerScores(CrmId, Type='payment')`** ← score paiement utile pour audit SAV (geste commercial)
5. **`SetCallCenter(...)`** ← logger l'appel audité côté CRM Atlas (optionnel)

## Métadonnées de retour communes — toutes les opérations renvoient :

```
ResultWebMethod {
  ErrorFull    : boolean
  ErrorMessage : string
  ErrorStatus  : boolean
  ReturnCode   : int       ← 0 = succès, sinon code erreur métier
}
TokenWebMethod {
  BusinessLine : string    ← echo de l'entrée
  Country      : string
  EmetteurId   : int
}
```

À vérifier systématiquement avant d'utiliser le `Content` retourné.

## BusLine = ?

Le `BusLine` semble être une ligne business Atlas. Vu dans l'exemple : `4` correspond à SAV (à confirmer). Probablement :
- `1` = Cde Tel ou ventes
- `4` = SAV

À valider avec Atlas / B2T avant intégration finale.

---

## Service : `crmservices`

### Port : `BasicHttpBinding_Icrmservices`
- Binding : `{http://www.b2t.eu/ws/Client/2013/09/01}BasicHttpBinding_Icrmservices`
- Endpoint : `http://192.168.23.28/AFM/WS/WsCustomer/crmservices.svc`

**28 opérations** disponibles dans ce binding :

| Opération | SOAPAction | Use case |
|---|---|---|
| `AnonymisationCustomer` | `…/AnonymisationCustomer` | _(voir détail ci-dessous)_ |
| `AttachWebAccount` | `…/AttachWebAccount` | _(voir détail ci-dessous)_ |
| `CreateWebAccount` | `…/CreateWebAccount` | _(voir détail ci-dessous)_ |
| `DeleteAddress` | `…/DeleteAddress` | _(voir détail ci-dessous)_ |
| `DeleteWebAccount` | `…/DeleteWebAccount` | _(voir détail ci-dessous)_ |
| `GetCRMId` | `…/GetCRMId` | _(voir détail ci-dessous)_ |
| `GetCustomer` | `…/GetCustomer` | _(voir détail ci-dessous)_ |
| `GetCustomerEvCatecories` | `…/GetCustomerEvCatecories` | _(voir détail ci-dessous)_ |
| `GetCustomerScores` | `…/GetCustomerScores` | _(voir détail ci-dessous)_ |
| `GetFormattedAddress` | `…/GetFormattedAddress` | _(voir détail ci-dessous)_ |
| `GetHistoriBanks` | `…/GetHistoriBanks` | _(voir détail ci-dessous)_ |
| `GetLead` | `…/GetLead` | _(voir détail ci-dessous)_ |
| `GetMatchCode` | `…/GetMatchCode` | _(voir détail ci-dessous)_ |
| `GetOrderToday` | `…/GetOrderToday` | _(voir détail ci-dessous)_ |
| `GetPassword` | `…/GetPassword` | _(voir détail ci-dessous)_ |
| `GetWebAccount` | `…/GetWebAccount` | _(voir détail ci-dessous)_ |
| `Login` | `…/Login` | _(voir détail ci-dessous)_ |
| `PublishMailling` | `…/PublishMailling` | _(voir détail ci-dessous)_ |
| `ResetPassword` | `…/ResetPassword` | _(voir détail ci-dessous)_ |
| `SetCallCenter` | `…/SetCallCenter` | _(voir détail ci-dessous)_ |
| `SetCustomer` | `…/SetCustomer` | _(voir détail ci-dessous)_ |
| `SetLead` | `…/SetLead` | _(voir détail ci-dessous)_ |
| `SetMainFrameId` | `…/SetMainFrameId` | _(voir détail ci-dessous)_ |
| `SetScore` | `…/SetScore` | _(voir détail ci-dessous)_ |
| `UpdateCustomer` | `…/UpdateCustomer` | _(voir détail ci-dessous)_ |
| `UpdateLead` | `…/UpdateLead` | _(voir détail ci-dessous)_ |
| `UpdateScore` | `…/UpdateScore` | _(voir détail ci-dessous)_ |
| `UpdateWebAccount` | `…/UpdateWebAccount` | _(voir détail ci-dessous)_ |

#### 🔹 `AnonymisationCustomer`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/AnonymisationCustomer`
- **Style** : `document`
- **Input** :
  - **`crmID`** : `int` _(optionnel)_
  - **`userId`** : `int` _(optionnel)_
  - **`country`** : `string` _(optionnel)_
- **Output** :
  - _accepted type_ : `AnonymisationCustomerResponse`

#### 🔹 `AttachWebAccount`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/AttachWebAccount`
- **Style** : `document`
- **Input** :
  - **`Entry`** : `EntryAttachWebAccount` _(optionnel)_
    - **`AccountID`** : `int` _(optionnel)_
    - **`BusinessLine`** : `string` _(optionnel)_
    - **`CRMID`** : `int` _(optionnel)_
    - **`Civility`** : `string` _(optionnel)_
    - **`Country`** : `string` _(optionnel)_
    - **`FirstName`** : `string` _(optionnel)_
    - **`Language`** : `string` _(optionnel)_
    - **`LastName`** : `string` _(optionnel)_
    - **`LegalEntity`** : `string` _(optionnel)_
- **Output** :
  - **`AttachWebAccountResult`** : `ResultAttachWebAccount` _(optionnel)_
    - **`AccountID`** : `int` _(optionnel)_
    - **`AttachedToContact`** : `boolean` _(optionnel)_
    - **`BusinessLine`** : `string` _(optionnel)_
    - **`CRMID`** : `int` _(optionnel)_
    - **`Country`** : `string` _(optionnel)_
    - **`Error`** : `ResultWebMethod` _(optionnel)_
      - **`ErrorFull`** : `boolean` _(optionnel)_
      - **`ErrorMessage`** : `string` _(optionnel)_
      - **`ErrorStatus`** : `boolean` _(optionnel)_
      - **`ReturnCode`** : `int` _(optionnel)_
    - **`LegalEntity`** : `string` _(optionnel)_
    - **`Login`** : `string` _(optionnel)_
    - **`Status`** : `string` _(optionnel)_

#### 🔹 `CreateWebAccount`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/CreateWebAccount`
- **Style** : `document`
- **Input** :
  - **`Entry`** : `EntryCreateWebAccount` _(optionnel)_
    - **`BirthDate`** : `dateTime` _(optionnel)_
    - **`BusinessLine`** : `string` _(optionnel)_
    - **`Civility`** : `string` _(optionnel)_
    - **`Country`** : `string` _(optionnel)_
    - **`FirstName`** : `string` _(optionnel)_
    - **`Language`** : `string` _(optionnel)_
    - **`LastName`** : `string` _(optionnel)_
    - **`LegalEntity`** : `string` _(optionnel)_
    - **`Login`** : `string` _(optionnel)_
    - **`NewPassword`** : `string` _(optionnel)_
    - **`OptinEmail`** : `string` _(optionnel)_
    - **`OptinFixedPhone`** : `string` _(optionnel)_
    - **`OptinMail`** : `string` _(optionnel)_
    - **`OptinMobilePhone`** : `string` _(optionnel)_
    - **`OptinSms`** : `string` _(optionnel)_
    - **`Password`** : `string` _(optionnel)_
    - **`Patronym`** : `string` _(optionnel)_
    - **`PhoneFixe`** : `string` _(optionnel)_
    - **`PhoneMobile`** : `string` _(optionnel)_
    - **`UtmCampaign`** : `string` _(optionnel)_
    - **`UtmMedium`** : `string` _(optionnel)_
    - **`UtmSource`** : `string` _(optionnel)_
- **Output** :
  - **`CreateWebAccountResult`** : `ResultCreateWebAccount` _(optionnel)_
    - **`AccountNumID`** : `int` _(optionnel)_
    - **`BusinessLine`** : `string` _(optionnel)_
    - **`Country`** : `string` _(optionnel)_
    - **`CreateDate`** : `dateTime` _(optionnel)_
    - **`Error`** : `ResultWebMethod` _(optionnel)_
      - **`ErrorFull`** : `boolean` _(optionnel)_
      - **`ErrorMessage`** : `string` _(optionnel)_
      - **`ErrorStatus`** : `boolean` _(optionnel)_
      - **`ReturnCode`** : `int` _(optionnel)_
    - **`Language`** : `string` _(optionnel)_
    - **`Login`** : `string` _(optionnel)_

#### 🔹 `DeleteAddress`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/DeleteAddress`
- **Style** : `document`
- **Input** :
  - **`CrmID`** : `int` _(optionnel)_
  - **`entry`** : `ArrayOfAddress` _(optionnel)_
    - **`Address`** : `Address` _(optionnel)_
      - **`AdresseInfo`** : `string` _(optionnel)_
      - **`Appartement`** : `string` _(optionnel)_
      - **`Batiment`** : `string` _(optionnel)_
      - **`BureauDistributeur`** : `string` _(optionnel)_
      - **`CRMUserID`** : `int` _(optionnel)_
      - **`Canal`** : `string` _(optionnel)_
      - **`City`** : `string` _(optionnel)_
      - **`CodeInsee`** : `string` _(optionnel)_
      - **`CompteurNPAI`** : `int` _(optionnel)_
      - **`Corpus`** : `string` _(optionnel)_
      - **`Country`** : `string` _(optionnel)_
      - **`CustomName`** : `string` _(optionnel)_
      - **`DateDebutClosingZone`** : `dateTime` _(optionnel)_
      - **`DateFinClosingZone`** : `dateTime` _(optionnel)_
      - **`DateMAJOptin`** : `dateTime` _(optionnel)_
      - **`DateMAJOptinPartenaire`** : `dateTime` _(optionnel)_
      - **`DateMAJ_ADR`** : `dateTime` _(optionnel)_
      - **`DateMAJ_NPAI`** : `dateTime` _(optionnel)_
      - **`District`** : `string` _(optionnel)_
      - **`IndicateurClosingZone`** : `unsignedByte` _(optionnel)_
      - **`InstructionLivraison`** : `string` _(optionnel)_
      - **`Maison`** : `string` _(optionnel)_
      - **`NomRue`** : `string` _(optionnel)_
      - **`NumeroRue`** : `string` _(optionnel)_
      - **`OptinValue`** : `unsignedByte` _(optionnel)_
      - **`Principale`** : `boolean` _(optionnel)_
      - **`Province`** : `string` _(optionnel)_
      - **`ProvinceCode`** : `string` _(optionnel)_
      - **`QualiteAdresse`** : `decimal` _(optionnel)_
      - **`Region`** : `string` _(optionnel)_
      - **`SourceCreation`** : `string` _(optionnel)_
      - **`SourceMAJ`** : `string` _(optionnel)_
      - **`SourceMAJOptin`** : `string` _(optionnel)_
      - **`SourceMAJOptinPartenaire`** : `string` _(optionnel)_
      - **`StatutNPAI`** : `string` _(optionnel)_
      - **`TopAdresse`** : `short` _(optionnel)_
      - **`TypeCite`** : `string` _(optionnel)_
      - **`TypeVoie`** : `string` _(optionnel)_
      - **`Usage`** : `string` _(optionnel)_
      - **`UsageLibelle`** : `string` _(optionnel)_
      - **`ValeurOptinPartner`** : `unsignedByte` _(optionnel)_
      - **`ZipCode`** : `string` _(optionnel)_
- **Output** :
  - **`DeleteAddressResult`** : `ResultWebMethod` _(optionnel)_
    - **`ErrorFull`** : `boolean` _(optionnel)_
    - **`ErrorMessage`** : `string` _(optionnel)_
    - **`ErrorStatus`** : `boolean` _(optionnel)_
    - **`ReturnCode`** : `int` _(optionnel)_

#### 🔹 `DeleteWebAccount`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/DeleteWebAccount`
- **Style** : `document`
- **Input** :
  - **`entry`** : `int` _(optionnel)_
- **Output** :
  - **`DeleteWebAccountResult`** : `string` _(optionnel)_

#### 🔹 `GetCRMId`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/GetCRMId`
- **Style** : `document`
- **Input** :
  - **`p_Country`** : `string` _(optionnel)_
  - **`p_BusLine`** : `string` _(optionnel)_
  - **`p_EmetteurId`** : `int` _(optionnel)_
  - **`p_PaperId`** : `string` _(optionnel)_
  - **`Name`** : `string` _(optionnel)_
- **Output** :
  - **`GetCRMIdResult`** : `ResultGetCrmId` _(optionnel)_
    - **`Content`** : `ContentGetCrmId` _(optionnel)_
      - **`CrmId`** : `int` _(optionnel)_
    - **`Status`** : `ResultWebMethod` _(optionnel)_
      - **`ErrorFull`** : `boolean` _(optionnel)_
      - **`ErrorMessage`** : `string` _(optionnel)_
      - **`ErrorStatus`** : `boolean` _(optionnel)_
      - **`ReturnCode`** : `int` _(optionnel)_
    - **`Token`** : `TokenWebMethod` _(optionnel)_
      - **`BusinessLine`** : `string` _(optionnel)_
      - **`Country`** : `string` _(optionnel)_
      - **`EmetteurId`** : `int` _(optionnel)_

#### 🔹 `GetCustomer`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/GetCustomer`
- **Style** : `document`
- **Input** :
  - **`IdCrm`** : `int` _(optionnel)_
  - **`BusLine`** : `string` _(optionnel)_
  - **`Country`** : `string` _(optionnel)_
  - **`EmetteurId`** : `int` _(optionnel)_
- **Output** :
  - **`GetCustomerResult`** : `ResultGetCustomer` _(optionnel)_
    - **`BlackListStatus`** : `BLACKLIST` _(optionnel)_
    - **`Content`** : `Content` _(optionnel)_
      - **`Activite`** : `ArrayOfActivity` _(optionnel)_
      - **`Adresses`** : `ArrayOfAddress` _(optionnel)_
      - **`Contact`** : `Contact` _(optionnel)_
      - **`CoordonnesBancaires`** : `ArrayOfBankDetails` _(optionnel)_
      - **`Emails`** : `ArrayOfEmail` _(optionnel)_
      - **`StatusClient`** : `ArrayOfStatusCostumer` _(optionnel)_
      - **`Telephones`** : `ArrayOfPhone` _(optionnel)_
    - **`Status`** : `ResultWebMethod` _(optionnel)_
      - **`ErrorFull`** : `boolean` _(optionnel)_
      - **`ErrorMessage`** : `string` _(optionnel)_
      - **`ErrorStatus`** : `boolean` _(optionnel)_
      - **`ReturnCode`** : `int` _(optionnel)_
    - **`Token`** : `TokenWebMethod` _(optionnel)_
      - **`BusinessLine`** : `string` _(optionnel)_
      - **`Country`** : `string` _(optionnel)_
      - **`EmetteurId`** : `int` _(optionnel)_

#### 🔹 `GetCustomerEvCatecories`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/GetCustomerEvCatecories`
- **Style** : `document`
- **Input** :
  - **`busline`** : `string` _(optionnel)_
  - **`countryLang`** : `string` _(optionnel)_
- **Output** :
  - **`GetCustomerEvCatecoriesResult`** : `ArrayOfCustomerEvCategories` _(optionnel)_
    - **`CustomerEvCategories`** : `CustomerEvCategories` _(optionnel)_
      - **`Code`** : `string` _(optionnel)_
      - **`Id`** : `int` _(optionnel)_
      - **`Libelle`** : `string` _(optionnel)_
      - **`ParentCode`** : `string` _(optionnel)_
      - **`ParentLibelle`** : `string` _(optionnel)_
      - **`ActionCallCode`** : `string` _(optionnel)_
      - **`ActionCallId`** : `int` _(optionnel)_
      - **`IsNewCat`** : `boolean` _(optionnel)_

#### 🔹 `GetCustomerScores`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/GetCustomerScores`
- **Style** : `document`
- **Input** :
  - **`input`** : `ScoreInput` _(optionnel)_
    - **`CrmId`** : `int` _(optionnel)_
    - **`Names`** : `string` _(optionnel)_
    - **`Type`** : `string` _(optionnel)_
- **Output** :
  - **`GetCustomerScoresResult`** : `ArrayOfScoreOutPut` _(optionnel)_
    - **`ScoreOutPut`** : `ScoreOutPut` _(optionnel)_
      - **`Code`** : `string` _(optionnel)_
      - **`Value`** : `string` _(optionnel)_
      - **`ValueDate`** : `string` _(optionnel)_

#### 🔹 `GetFormattedAddress`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/GetFormattedAddress`
- **Style** : `document`
- **Input** :
  - **`CrmID`** : `int` _(optionnel)_
  - **`Usage`** : `string` _(optionnel)_
- **Output** :
  - **`GetFormattedAddressResult`** : `ResultFormattedAddress` _(optionnel)_
    - **`AddressLlines`** : `ArrayOfAddressLine` _(optionnel)_
      - **`AddressLine`** : `AddressLine` _(optionnel)_
    - **`Status`** : `ResultWebMethod` _(optionnel)_
      - **`ErrorFull`** : `boolean` _(optionnel)_
      - **`ErrorMessage`** : `string` _(optionnel)_
      - **`ErrorStatus`** : `boolean` _(optionnel)_
      - **`ReturnCode`** : `int` _(optionnel)_

#### 🔹 `GetHistoriBanks`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/GetHistoriBanks`
- **Style** : `document`
- **Input** :
  - **`crmid`** : `int` _(optionnel)_
  - **`Country`** : `string` _(optionnel)_
  - **`Language`** : `string` _(optionnel)_
- **Output** :
  - **`GetHistoriBanksResult`** : `ArrayOfBankDetails` _(optionnel)_
    - **`BankDetails`** : `BankDetails` _(optionnel)_
      - **`AccountNumber`** : `string` _(optionnel)_
      - **`BAN_ACCOUNT`** : `string` _(optionnel)_
      - **`BAN_CARD_ID`** : `string` _(optionnel)_
      - **`BAN_CARD_NUMBER`** : `string` _(optionnel)_
      - **`BAN_CLIENT_NAME`** : `string` _(optionnel)_
      - **`BAN_CVV_NUMBER`** : `string` _(optionnel)_
      - **`BAN_IBAN`** : `string` _(optionnel)_
      - **`BAN_ISPRINCIPAL`** : `boolean` _(optionnel)_
      - **`BAN_NAME`** : `string` _(optionnel)_
      - **`BAN_NUMBER`** : `string` _(optionnel)_
      - **`BAN_PARTNER_ID`** : `string` _(optionnel)_
      - **`BAN_SDD`** : `boolean` _(optionnel)_
      - **`BAN_SDD_DTH`** : `dateTime` _(optionnel)_
      - **`BAN_SWIFT_COD`** : `string` _(optionnel)_
      - **`BAN_VALIDITY_PERIOD`** : `dateTime` _(optionnel)_
      - **`CreateDate`** : `dateTime` _(optionnel)_
      - **`SortCode`** : `string` _(optionnel)_
      - **`UpdateDate`** : `dateTime` _(optionnel)_
      - **`Usage`** : `string` _(optionnel)_
      - **`User`** : `string` _(optionnel)_

#### 🔹 `GetLead`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/GetLead`
- **Style** : `document`
- **Input** :
  - **`BusinessLine`** : `string` _(optionnel)_
  - **`Email`** : `string` _(optionnel)_
  - **`Country`** : `string` _(optionnel)_
  - **`Language`** : `string` _(optionnel)_
  - **`Emetteur`** : `int` _(optionnel)_
- **Output** :
  - **`GetLeadResult`** : `ResultGetLead` _(optionnel)_
    - **`Content`** : `Lead` _(optionnel)_
      - **`BusinessLine`** : `string` _(optionnel)_
      - **`Country`** : `string` _(optionnel)_
      - **`EMail`** : `string` _(optionnel)_
      - **`ExternDate`** : `dateTime` _(optionnel)_
      - **`FirstName`** : `string` _(optionnel)_
      - **`Genre`** : `string` _(optionnel)_
      - **`Identifiant`** : `int` _(optionnel)_
      - **`Language`** : `string` _(optionnel)_
      - **`LastName`** : `string` _(optionnel)_
      - **`OptinEmail`** : `string` _(optionnel)_
      - **`OriginalCanal`** : `string` _(optionnel)_
      - **`OriginalNewsLetterID`** : `string` _(optionnel)_
      - **`Phone`** : `string` _(optionnel)_
    - **`Status`** : `ResultWebMethod` _(optionnel)_
      - **`ErrorFull`** : `boolean` _(optionnel)_
      - **`ErrorMessage`** : `string` _(optionnel)_
      - **`ErrorStatus`** : `boolean` _(optionnel)_
      - **`ReturnCode`** : `int` _(optionnel)_
    - **`Token`** : `TokenWebMethod` _(optionnel)_
      - **`BusinessLine`** : `string` _(optionnel)_
      - **`Country`** : `string` _(optionnel)_
      - **`EmetteurId`** : `int` _(optionnel)_

#### 🔹 `GetMatchCode`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/GetMatchCode`
- **Style** : `document`
- **Input** :
  - **`Entry`** : `EntryMatchCode` _(optionnel)_
    - **`BusinessLineCode`** : `string` _(optionnel)_
    - **`City`** : `string` _(optionnel)_
    - **`CountryCode`** : `string` _(optionnel)_
    - **`FirstName`** : `string` _(optionnel)_
    - **`LanguageCode`** : `string` _(optionnel)_
    - **`LastName`** : `string` _(optionnel)_
    - **`StreetName`** : `string` _(optionnel)_
    - **`StreetNumber`** : `string` _(optionnel)_
    - **`ZipCode`** : `string` _(optionnel)_
- **Output** :
  - **`GetMatchCodeResult`** : `ResultMatchCode` _(optionnel)_
    - **`BusinessLineCode`** : `string` _(optionnel)_
    - **`CountryCode`** : `string` _(optionnel)_
    - **`ErrorMessage`** : `string` _(optionnel)_
    - **`LanguageCode`** : `string` _(optionnel)_
    - **`MatchCode`** : `string` _(optionnel)_
    - **`TypeMatchCode`** : `string` _(optionnel)_

#### 🔹 `GetOrderToday`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/GetOrderToday`
- **Style** : `document`
- **Input** :
  - **`userId`** : `int` _(optionnel)_
- **Output** :
  - **`GetOrderTodayResult`** : `OrderToday` _(optionnel)_
    - **`ChiffreA`** : `decimal` _(optionnel)_
    - **`ChiffreAVADD`** : `decimal` _(optionnel)_
    - **`NbCommande`** : `int` _(optionnel)_
    - **`NbCommandeVADD`** : `int` _(optionnel)_
    - **`NbVaddValid`** : `decimal` _(optionnel)_
    - **`NbValid`** : `decimal` _(optionnel)_

#### 🔹 `GetPassword`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/GetPassword`
- **Style** : `document`
- **Input** :
  - **`p_Country`** : `string` _(optionnel)_
  - **`p_BusLine`** : `string` _(optionnel)_
  - **`p_Login`** : `string` _(optionnel)_
  - **`p_EmetteurId`** : `int` _(optionnel)_
- **Output** :
  - **`GetPasswordResult`** : `ResultGetPassword` _(optionnel)_
    - **`Content`** : `ContentPassWord` _(optionnel)_
      - **`PasseWord`** : `string` _(optionnel)_
      - **`is_Argon2`** : `boolean` _(optionnel)_
    - **`Status`** : `ResultWebMethod` _(optionnel)_
      - **`ErrorFull`** : `boolean` _(optionnel)_
      - **`ErrorMessage`** : `string` _(optionnel)_
      - **`ErrorStatus`** : `boolean` _(optionnel)_
      - **`ReturnCode`** : `int` _(optionnel)_
    - **`Token`** : `TokenWebMethod` _(optionnel)_
      - **`BusinessLine`** : `string` _(optionnel)_
      - **`Country`** : `string` _(optionnel)_
      - **`EmetteurId`** : `int` _(optionnel)_

#### 🔹 `GetWebAccount`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/GetWebAccount`
- **Style** : `document`
- **Input** :
  - **`Entry`** : `EntryGetWebAccount` _(optionnel)_
    - **`BusinessLine`** : `string` _(optionnel)_
    - **`CRMID`** : `int` _(optionnel)_
    - **`Country`** : `string` _(optionnel)_
    - **`LegalEntity`** : `string` _(optionnel)_
    - **`Login`** : `string` _(optionnel)_
- **Output** :
  - **`GetWebAccountResult`** : `ResultGetWebAccount` _(optionnel)_
    - **`AccountID`** : `int` _(optionnel)_
    - **`AttachedToContact`** : `boolean` _(optionnel)_
    - **`BirthDate`** : `dateTime` _(optionnel)_
    - **`BusinessLine`** : `string` _(optionnel)_
    - **`CRMID`** : `int` _(optionnel)_
    - **`Civility`** : `string` _(optionnel)_
    - **`Country`** : `string` _(optionnel)_
    - **`Error`** : `ResultWebMethod` _(optionnel)_
      - **`ErrorFull`** : `boolean` _(optionnel)_
      - **`ErrorMessage`** : `string` _(optionnel)_
      - **`ErrorStatus`** : `boolean` _(optionnel)_
      - **`ReturnCode`** : `int` _(optionnel)_
    - **`FirstName`** : `string` _(optionnel)_
    - **`Language`** : `string` _(optionnel)_
    - **`LastName`** : `string` _(optionnel)_
    - **`LegalEntity`** : `string` _(optionnel)_
    - **`Login`** : `string` _(optionnel)_
    - **`NewPassword`** : `string` _(optionnel)_
    - **`OptinEmail`** : `string` _(optionnel)_
    - **`OptinFixedPhone`** : `string` _(optionnel)_
    - **`OptinMail`** : `string` _(optionnel)_
    - **`OptinMobilePhone`** : `string` _(optionnel)_
    - **`OptinSms`** : `string` _(optionnel)_
    - **`Password`** : `string` _(optionnel)_
    - **`Patronym`** : `string` _(optionnel)_
    - **`PhoneFixe`** : `string` _(optionnel)_
    - **`PhoneMobile`** : `string` _(optionnel)_
    - **`Status`** : `string` _(optionnel)_

#### 🔹 `Login`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/Login`
- **Style** : `document`
- **Input** :
  - **`BusinessLine`** : `string` _(optionnel)_
  - **`LegalEntity`** : `string` _(optionnel)_
  - **`Country`** : `string` _(optionnel)_
  - **`Language`** : `string` _(optionnel)_
  - **`Login`** : `string` _(optionnel)_
  - **`Password`** : `string` _(optionnel)_
  - **`FullDetails`** : `boolean` _(optionnel)_
  - **`emetteurId`** : `int` _(optionnel)_
  - **`NewPassword`** : `string` _(optionnel)_
- **Output** :
  - **`LoginResult`** : `ResultLogin` _(optionnel)_
    - **`AccountNumID`** : `int` _(optionnel)_
    - **`BlackListStatus`** : `BLACKLIST` _(optionnel)_
    - **`ClientSegment`** : `string` _(optionnel)_
    - **`Content`** : `Content` _(optionnel)_
      - **`Activite`** : `ArrayOfActivity` _(optionnel)_
      - **`Adresses`** : `ArrayOfAddress` _(optionnel)_
      - **`Contact`** : `Contact` _(optionnel)_
      - **`CoordonnesBancaires`** : `ArrayOfBankDetails` _(optionnel)_
      - **`Emails`** : `ArrayOfEmail` _(optionnel)_
      - **`StatusClient`** : `ArrayOfStatusCostumer` _(optionnel)_
      - **`Telephones`** : `ArrayOfPhone` _(optionnel)_
    - **`CrmId`** : `int` _(optionnel)_
    - **`IsNewBusiness`** : `boolean` _(optionnel)_
    - **`IsNewMarketing`** : `boolean` _(optionnel)_
    - **`LastOrderDth`** : `dateTime` _(optionnel)_
    - **`LastOrderPaymentCode`** : `string` _(optionnel)_
    - **`Status`** : `ResultWebMethod` _(optionnel)_
      - **`ErrorFull`** : `boolean` _(optionnel)_
      - **`ErrorMessage`** : `string` _(optionnel)_
      - **`ErrorStatus`** : `boolean` _(optionnel)_
      - **`ReturnCode`** : `int` _(optionnel)_
    - **`Token`** : `TokenWebMethod` _(optionnel)_
      - **`BusinessLine`** : `string` _(optionnel)_
      - **`Country`** : `string` _(optionnel)_
      - **`EmetteurId`** : `int` _(optionnel)_
    - **`WebAccount`** : `WebAccount` _(optionnel)_
      - **`AccountID`** : `int` _(optionnel)_
      - **`AttachedToContact`** : `boolean` _(optionnel)_
      - **`BusinessLine`** : `string` _(optionnel)_
      - **`CRMID`** : `int` _(optionnel)_
      - **`Civility`** : `string` _(optionnel)_
      - **`Country`** : `string` _(optionnel)_
      - **`FirstName`** : `string` _(optionnel)_
      - **`Language`** : `string` _(optionnel)_
      - **`LastName`** : `string` _(optionnel)_
      - **`LegalEntity`** : `string` _(optionnel)_
      - **`Login`** : `string` _(optionnel)_
      - **`OptinEmail`** : `string` _(optionnel)_
      - **`OptinFixedPhone`** : `string` _(optionnel)_
      - **`OptinMail`** : `string` _(optionnel)_
      - **`OptinMobilePhone`** : `string` _(optionnel)_
      - **`Status`** : `string` _(optionnel)_
    - **`tags`** : `ArrayOfstring` _(optionnel)_
      - **`string`** : `string` _(optionnel)_

#### 🔹 `PublishMailling`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/PublishMailling`
- **Style** : `document`
- **Input** :
  - **`input`** : `ArrayOfMailProduct` _(optionnel)_
    - **`MailProduct`** : `MailProduct` _(optionnel)_
      - **`Code`** : `string` _(optionnel)_
      - **`CountryCode`** : `string` _(optionnel)_
      - **`DateReception`** : `dateTime` _(optionnel)_
      - **`DateResponse`** : `dateTime` _(optionnel)_
      - **`Id`** : `int` _(optionnel)_
      - **`IsResp`** : `boolean` _(optionnel)_
      - **`LanguageCode`** : `string` _(optionnel)_
      - **`Message`** : `string` _(optionnel)_
      - **`TicketId`** : `int` _(optionnel)_
- **Output** :
  - _accepted type_ : `PublishMaillingResponse`

#### 🔹 `ResetPassword`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/ResetPassword`
- **Style** : `document`
- **Input** :
  - **`Entry`** : `EntryResetPassword` _(optionnel)_
    - **`AccountID`** : `int` _(optionnel)_
    - **`BusinessLine`** : `string` _(optionnel)_
    - **`Country`** : `string` _(optionnel)_
    - **`Language`** : `string` _(optionnel)_
    - **`LegalEntity`** : `string` _(optionnel)_
    - **`Login`** : `string` _(optionnel)_
    - **`NewPassword`** : `string` _(optionnel)_
- **Output** :
  - **`ResetPasswordResult`** : `ResultResetPassword` _(optionnel)_
    - **`AccountID`** : `int` _(optionnel)_
    - **`AttachedToContact`** : `boolean` _(optionnel)_
    - **`BusinessLine`** : `string` _(optionnel)_
    - **`CRMID`** : `int` _(optionnel)_
    - **`Country`** : `string` _(optionnel)_
    - **`Error`** : `ResultWebMethod` _(optionnel)_
      - **`ErrorFull`** : `boolean` _(optionnel)_
      - **`ErrorMessage`** : `string` _(optionnel)_
      - **`ErrorStatus`** : `boolean` _(optionnel)_
      - **`ReturnCode`** : `int` _(optionnel)_
    - **`LegalEntity`** : `string` _(optionnel)_
    - **`Login`** : `string` _(optionnel)_
    - **`Status`** : `string` _(optionnel)_

#### 🔹 `SetCallCenter`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/SetCallCenter`
- **Style** : `document`
- **Input** :
  - **`input`** : `CallAction` _(optionnel)_
    - **`ActionId`** : `int` _(optionnel)_
    - **`ActionIdAdditional`** : `string` _(optionnel)_
    - **`ActionIdFinal`** : `int` _(optionnel)_
    - **`Busline`** : `string` _(optionnel)_
    - **`Comment`** : `string` _(optionnel)_
    - **`CountryLangue`** : `string` _(optionnel)_
    - **`EventCode`** : `string` _(optionnel)_
    - **`EventCode2`** : `string` _(optionnel)_
    - **`IdCallCenter`** : `int` _(optionnel)_
    - **`IdCallCenterFinal`** : `int` _(optionnel)_
    - **`Login`** : `string` _(optionnel)_
    - **`TransCode`** : `string` _(optionnel)_
    - **`TransId`** : `int` _(optionnel)_
- **Output** :
  - _accepted type_ : `SetCallCenterResponse`

#### 🔹 `SetCustomer`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/SetCustomer`
- **Style** : `document`
- **Input** :
  - **`entrySetCustomer`** : `EntrySetCustomer` _(optionnel)_
    - **`Activite`** : `ArrayOfActivity` _(optionnel)_
      - **`Activity`** : `Activity` _(optionnel)_
    - **`Adresses`** : `ArrayOfAddress` _(optionnel)_
      - **`Address`** : `Address` _(optionnel)_
    - **`Contact`** : `Contact`
      - **`AccountNumID`** : `string` _(optionnel)_
      - **`BillingUsageID`** : `string` _(optionnel)_
      - **`BirthDate`** : `string` _(optionnel)_
      - **`CAT_ID`** : `string` _(optionnel)_
      - **`CRMUserID`** : `int` _(optionnel)_
      - **`CRMUserLogin`** : `string` _(optionnel)_
      - **`Canal`** : `string` _(optionnel)_
      - **`Civilite`** : `string` _(optionnel)_
      - **`Country`** : `string`
      - **`CreateDate`** : `dateTime` _(optionnel)_
      - **`CrmID`** : `int` _(optionnel)_
      - **`DateDelivPassport`** : `dateTime` _(optionnel)_
      - **`DateFinValPassport`** : `dateTime` _(optionnel)_
      - **`DateFinValidite`** : `dateTime` _(optionnel)_
      - **`DateMAJStatut`** : `dateTime` _(optionnel)_
      - **`DateNaissance`** : `dateTime` _(optionnel)_
      - **`HashCode`** : `string` _(optionnel)_
      - **`IdentifiantParrain`** : `string` _(optionnel)_
      - **`IdentifiantPersonnel`** : `string` _(optionnel)_
      - **`IsSupervisor`** : `boolean` _(optionnel)_
      - **`Langue`** : `string` _(optionnel)_
      - **`LastOderDate`** : `dateTime` _(optionnel)_
      - **`LastUpdateDate`** : `dateTime` _(optionnel)_
      - **`LieuDelivPassport`** : `string` _(optionnel)_
      - **`MF_ID`** : `string` _(optionnel)_
      - **`MatchCode`** : `string` _(optionnel)_
      - **`Nom`** : `string` _(optionnel)_
      - **`NumeroFoyerSource`** : `string` _(optionnel)_
      - **`Patronym`** : `string` _(optionnel)_
      - **`Prenom`** : `string` _(optionnel)_
      - **`QualityCode`** : `string` _(optionnel)_
      - **`Sexe`** : `string` _(optionnel)_
      - **`ShippingUsageID`** : `string` _(optionnel)_
      - **`SituationFamiliale`** : `string` _(optionnel)_
      - **`Source`** : `string` _(optionnel)_
      - **`SourceCreation`** : `string` _(optionnel)_
      - **`SourceCreationProspect`** : `string` _(optionnel)_
      - **`SourceMAJ`** : `string` _(optionnel)_
      - **`StatutClient`** : `string` _(optionnel)_
      - **`StatutPersonne`** : `string` _(optionnel)_
      - **`TaxeId`** : `string` _(optionnel)_
      - **`TypeDocument`** : `string` _(optionnel)_
      - **`TypePersonne`** : `string` _(optionnel)_
      - **`VIPGrade`** : `string` _(optionnel)_
      - **`VIPStatus`** : `string` _(optionnel)_
      - **`tags`** : `ArrayOfstring` _(optionnel)_
    - **`CoordonnesBancaires`** : `ArrayOfBankDetails` _(optionnel)_
      - **`BankDetails`** : `BankDetails` _(optionnel)_
    - **`Emails`** : `ArrayOfEmail` _(optionnel)_
      - **`Email`** : `Email` _(optionnel)_
    - **`StatusClient`** : `ArrayOfStatusCostumer` _(optionnel)_
      - **`StatusCostumer`** : `StatusCostumer` _(optionnel)_
    - **`Telephones`** : `ArrayOfPhone` _(optionnel)_
      - **`Phone`** : `Phone` _(optionnel)_
  - **`emetteurId`** : `int` _(optionnel)_
  - **`matchCodeBypass`** : `string` _(optionnel)_
- **Output** :
  - **`SetCustomerResult`** : `ResultSetCustomer` _(optionnel)_
    - **`BlackListStatus`** : `BLACKLIST` _(optionnel)_
    - **`CrmId`** : `int` _(optionnel)_
    - **`ProvinceCode`** : `string` _(optionnel)_
    - **`Status`** : `ResultWebMethod` _(optionnel)_
      - **`ErrorFull`** : `boolean` _(optionnel)_
      - **`ErrorMessage`** : `string` _(optionnel)_
      - **`ErrorStatus`** : `boolean` _(optionnel)_
      - **`ReturnCode`** : `int` _(optionnel)_
    - **`Token`** : `TokenWebMethod` _(optionnel)_
      - **`BusinessLine`** : `string` _(optionnel)_
      - **`Country`** : `string` _(optionnel)_
      - **`EmetteurId`** : `int` _(optionnel)_

#### 🔹 `SetLead`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/SetLead`
- **Style** : `document`
- **Input** :
  - **`BusLine`** : `string` _(optionnel)_
  - **`Email`** : `string` _(optionnel)_
  - **`Country`** : `string` _(optionnel)_
  - **`Name`** : `string` _(optionnel)_
  - **`FirstName`** : `string` _(optionnel)_
  - **`OptinMail`** : `string` _(optionnel)_
  - **`OriginalNewsLetterID`** : `string` _(optionnel)_
  - **`Language`** : `string` _(optionnel)_
  - **`Phone`** : `string` _(optionnel)_
  - **`OriginalCanal`** : `string` _(optionnel)_
  - **`ExternDate`** : `dateTime` _(optionnel)_
  - **`OptinPhone`** : `string` _(optionnel)_
  - **`Genre`** : `string` _(optionnel)_
  - **`Emetteur`** : `int` _(optionnel)_
  - **`utmSource`** : `string` _(optionnel)_
  - **`utmMedium`** : `string` _(optionnel)_
  - **`utmCampaign`** : `string` _(optionnel)_
- **Output** :
  - **`SetLeadResult`** : `ResultLead` _(optionnel)_
    - **`Content`** : `ContentSetLead` _(optionnel)_
      - **`CrmId`** : `int` _(optionnel)_
    - **`Status`** : `ResultWebMethod` _(optionnel)_
      - **`ErrorFull`** : `boolean` _(optionnel)_
      - **`ErrorMessage`** : `string` _(optionnel)_
      - **`ErrorStatus`** : `boolean` _(optionnel)_
      - **`ReturnCode`** : `int` _(optionnel)_
    - **`Token`** : `TokenWebMethod` _(optionnel)_
      - **`BusinessLine`** : `string` _(optionnel)_
      - **`Country`** : `string` _(optionnel)_
      - **`EmetteurId`** : `int` _(optionnel)_

#### 🔹 `SetMainFrameId`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/SetMainFrameId`
- **Style** : `document`
- **Input** :
  - **`ListCrmIdMfId`** : `ArrayOfKeyValueOfintstring` _(optionnel)_
    - **`KeyValueOfintstring`** : `KeyValueOfintstring` _(optionnel)_
      - **`Key`** : `int`
      - **`Value`** : `string`
  - **`emetteurId`** : `int` _(optionnel)_
- **Output** :
  - **`SetMainFrameIdResult`** : `ArrayOfKeyValueOfintint` _(optionnel)_
    - **`KeyValueOfintint`** : `KeyValueOfintint` _(optionnel)_
      - **`Key`** : `int`
      - **`Value`** : `int`

#### 🔹 `SetScore`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/SetScore`
- **Style** : `document`
- **Input** :
  - **`input`** : `Score` _(optionnel)_
    - **`Code`** : `string` _(optionnel)_
    - **`Value`** : `string` _(optionnel)_
    - **`ValueDate`** : `string` _(optionnel)_
    - **`CrmID`** : `int` _(optionnel)_
- **Output** :
  - **`SetScoreResult`** : `ResultWebMethodScore` _(optionnel)_
    - **`ErrorFull`** : `boolean` _(optionnel)_
    - **`ErrorMessage`** : `string` _(optionnel)_
    - **`ErrorStatus`** : `boolean` _(optionnel)_
    - **`ReturnCode`** : `int` _(optionnel)_

#### 🔹 `UpdateCustomer`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/UpdateCustomer`
- **Style** : `document`
- **Input** :
  - **`entryUpdateCustomer`** : `EntryUpdateCustomer` _(optionnel)_
    - **`Activite`** : `ArrayOfActivity` _(optionnel)_
      - **`Activity`** : `Activity` _(optionnel)_
    - **`Adresses`** : `ArrayOfAddress` _(optionnel)_
      - **`Address`** : `Address` _(optionnel)_
    - **`Contact`** : `Contact`
      - **`AccountNumID`** : `string` _(optionnel)_
      - **`BillingUsageID`** : `string` _(optionnel)_
      - **`BirthDate`** : `string` _(optionnel)_
      - **`CAT_ID`** : `string` _(optionnel)_
      - **`CRMUserID`** : `int` _(optionnel)_
      - **`CRMUserLogin`** : `string` _(optionnel)_
      - **`Canal`** : `string` _(optionnel)_
      - **`Civilite`** : `string` _(optionnel)_
      - **`Country`** : `string`
      - **`CreateDate`** : `dateTime` _(optionnel)_
      - **`CrmID`** : `int` _(optionnel)_
      - **`DateDelivPassport`** : `dateTime` _(optionnel)_
      - **`DateFinValPassport`** : `dateTime` _(optionnel)_
      - **`DateFinValidite`** : `dateTime` _(optionnel)_
      - **`DateMAJStatut`** : `dateTime` _(optionnel)_
      - **`DateNaissance`** : `dateTime` _(optionnel)_
      - **`HashCode`** : `string` _(optionnel)_
      - **`IdentifiantParrain`** : `string` _(optionnel)_
      - **`IdentifiantPersonnel`** : `string` _(optionnel)_
      - **`IsSupervisor`** : `boolean` _(optionnel)_
      - **`Langue`** : `string` _(optionnel)_
      - **`LastOderDate`** : `dateTime` _(optionnel)_
      - **`LastUpdateDate`** : `dateTime` _(optionnel)_
      - **`LieuDelivPassport`** : `string` _(optionnel)_
      - **`MF_ID`** : `string` _(optionnel)_
      - **`MatchCode`** : `string` _(optionnel)_
      - **`Nom`** : `string` _(optionnel)_
      - **`NumeroFoyerSource`** : `string` _(optionnel)_
      - **`Patronym`** : `string` _(optionnel)_
      - **`Prenom`** : `string` _(optionnel)_
      - **`QualityCode`** : `string` _(optionnel)_
      - **`Sexe`** : `string` _(optionnel)_
      - **`ShippingUsageID`** : `string` _(optionnel)_
      - **`SituationFamiliale`** : `string` _(optionnel)_
      - **`Source`** : `string` _(optionnel)_
      - **`SourceCreation`** : `string` _(optionnel)_
      - **`SourceCreationProspect`** : `string` _(optionnel)_
      - **`SourceMAJ`** : `string` _(optionnel)_
      - **`StatutClient`** : `string` _(optionnel)_
      - **`StatutPersonne`** : `string` _(optionnel)_
      - **`TaxeId`** : `string` _(optionnel)_
      - **`TypeDocument`** : `string` _(optionnel)_
      - **`TypePersonne`** : `string` _(optionnel)_
      - **`VIPGrade`** : `string` _(optionnel)_
      - **`VIPStatus`** : `string` _(optionnel)_
      - **`tags`** : `ArrayOfstring` _(optionnel)_
    - **`CoordonnesBancaires`** : `ArrayOfBankDetails` _(optionnel)_
      - **`BankDetails`** : `BankDetails` _(optionnel)_
    - **`Emails`** : `ArrayOfEmail` _(optionnel)_
      - **`Email`** : `Email` _(optionnel)_
    - **`StatusClient`** : `ArrayOfStatusCostumer` _(optionnel)_
      - **`StatusCostumer`** : `StatusCostumer` _(optionnel)_
    - **`Telephones`** : `ArrayOfPhone` _(optionnel)_
      - **`Phone`** : `Phone` _(optionnel)_
    - **`AccountID`** : `int` _(optionnel)_
    - **`IdentifiantClient`** : `int` _(optionnel)_
  - **`BusLine`** : `string` _(optionnel)_
  - **`EmetteurId`** : `int` _(optionnel)_
- **Output** :
  - **`UpdateCustomerResult`** : `ResultUpdateCustomer` _(optionnel)_
    - **`BlackListStatus`** : `BLACKLIST` _(optionnel)_
    - **`Content`** : `ContentUpdateCustomer` _(optionnel)_
      - **`CrmId`** : `int` _(optionnel)_
    - **`Status`** : `ResultWebMethod` _(optionnel)_
      - **`ErrorFull`** : `boolean` _(optionnel)_
      - **`ErrorMessage`** : `string` _(optionnel)_
      - **`ErrorStatus`** : `boolean` _(optionnel)_
      - **`ReturnCode`** : `int` _(optionnel)_
    - **`Token`** : `TokenWebMethod` _(optionnel)_
      - **`BusinessLine`** : `string` _(optionnel)_
      - **`Country`** : `string` _(optionnel)_
      - **`EmetteurId`** : `int` _(optionnel)_

#### 🔹 `UpdateLead`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/UpdateLead`
- **Style** : `document`
- **Input** :
  - **`entryUpdateLead`** : `EntryUpdateLead` _(optionnel)_
    - **`BusLine`** : `string` _(optionnel)_
    - **`Country`** : `string` _(optionnel)_
    - **`Email`** : `string` _(optionnel)_
    - **`FirstName`** : `string` _(optionnel)_
    - **`Language`** : `string` _(optionnel)_
    - **`Name`** : `string` _(optionnel)_
    - **`OptinMail`** : `string` _(optionnel)_
    - **`OptinMailUpdateDate`** : `dateTime` _(optionnel)_
    - **`OptinPhone`** : `string` _(optionnel)_
    - **`OptinPhoneUpdateDate`** : `dateTime` _(optionnel)_
    - **`OriginalCanal`** : `string` _(optionnel)_
    - **`OriginalNewsLetterID`** : `string` _(optionnel)_
    - **`Phone`** : `string` _(optionnel)_
  - **`emetteurId`** : `int` _(optionnel)_
- **Output** :
  - **`UpdateLeadResult`** : `ResultUpdateLead` _(optionnel)_
    - **`Status`** : `ResultWebMethod` _(optionnel)_
      - **`ErrorFull`** : `boolean` _(optionnel)_
      - **`ErrorMessage`** : `string` _(optionnel)_
      - **`ErrorStatus`** : `boolean` _(optionnel)_
      - **`ReturnCode`** : `int` _(optionnel)_
    - **`Token`** : `TokenWebMethod` _(optionnel)_
      - **`BusinessLine`** : `string` _(optionnel)_
      - **`Country`** : `string` _(optionnel)_
      - **`EmetteurId`** : `int` _(optionnel)_

#### 🔹 `UpdateScore`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/UpdateScore`
- **Style** : `document`
- **Input** :
  - **`input`** : `Score` _(optionnel)_
    - **`Code`** : `string` _(optionnel)_
    - **`Value`** : `string` _(optionnel)_
    - **`ValueDate`** : `string` _(optionnel)_
    - **`CrmID`** : `int` _(optionnel)_
- **Output** :
  - **`UpdateScoreResult`** : `ResultWebMethodScore` _(optionnel)_
    - **`ErrorFull`** : `boolean` _(optionnel)_
    - **`ErrorMessage`** : `string` _(optionnel)_
    - **`ErrorStatus`** : `boolean` _(optionnel)_
    - **`ReturnCode`** : `int` _(optionnel)_

#### 🔹 `UpdateWebAccount`
- **SOAPAction** : `http://www.b2t.eu/ws/Client/2013/09/01/Icrmservices/UpdateWebAccount`
- **Style** : `document`
- **Input** :
  - **`Entry`** : `EntryUpdateWebAccount` _(optionnel)_
    - **`AccountID`** : `int` _(optionnel)_
    - **`Activation`** : `boolean` _(optionnel)_
    - **`BirthDate`** : `dateTime` _(optionnel)_
    - **`BusinessLine`** : `string` _(optionnel)_
    - **`Civility`** : `string` _(optionnel)_
    - **`Country`** : `string` _(optionnel)_
    - **`FirstName`** : `string` _(optionnel)_
    - **`LastName`** : `string` _(optionnel)_
    - **`LegalEntity`** : `string` _(optionnel)_
    - **`Login`** : `string` _(optionnel)_
    - **`NewPassWord`** : `string` _(optionnel)_
    - **`OptinEmail`** : `string` _(optionnel)_
    - **`OptinFixedPhone`** : `string` _(optionnel)_
    - **`OptinMail`** : `string` _(optionnel)_
    - **`OptinMobilePhone`** : `string` _(optionnel)_
    - **`OptinSms`** : `string` _(optionnel)_
    - **`PassWord`** : `string` _(optionnel)_
    - **`Patronym`** : `string` _(optionnel)_
    - **`PhoneFixe`** : `string` _(optionnel)_
    - **`PhoneMobile`** : `string` _(optionnel)_
- **Output** :
  - **`UpdateWebAccountResult`** : `ResultUpdateWebAccount` _(optionnel)_
    - **`AccountID`** : `int` _(optionnel)_
    - **`AttachedToContact`** : `boolean` _(optionnel)_
    - **`BusinessLine`** : `string` _(optionnel)_
    - **`CRMID`** : `int` _(optionnel)_
    - **`Content`** : `Content` _(optionnel)_
      - **`Activite`** : `ArrayOfActivity` _(optionnel)_
      - **`Adresses`** : `ArrayOfAddress` _(optionnel)_
      - **`Contact`** : `Contact` _(optionnel)_
      - **`CoordonnesBancaires`** : `ArrayOfBankDetails` _(optionnel)_
      - **`Emails`** : `ArrayOfEmail` _(optionnel)_
      - **`StatusClient`** : `ArrayOfStatusCostumer` _(optionnel)_
      - **`Telephones`** : `ArrayOfPhone` _(optionnel)_
    - **`Country`** : `string` _(optionnel)_
    - **`Error`** : `ResultWebMethod` _(optionnel)_
      - **`ErrorFull`** : `boolean` _(optionnel)_
      - **`ErrorMessage`** : `string` _(optionnel)_
      - **`ErrorStatus`** : `boolean` _(optionnel)_
      - **`ReturnCode`** : `int` _(optionnel)_
    - **`LegalEntity`** : `string` _(optionnel)_
    - **`Login`** : `string` _(optionnel)_
    - **`Status`** : `string` _(optionnel)_

---

## Types complexes globaux (data contracts)

_(erreur listing types : 'Schema' object has no attribute 'get_types')_

## Valeurs

 - `dossier` : TNC_en_vigueur, TNC_non_vigueur, code_en_vigueur, code_non_vigueur

## articles

| name         | type | description                                                                                      |
|:-------------|:----:|:-------------------------------------------------------------------------------------------------|
| id           | char |                                                                                                  |
| section      | char |                                                                                                  |
| num          | text | ordre dans le document ?                                                                         |
| etat         | text | MODIFIE, ABROGE, ANNULE, MODIFIE_MORT_NE, TRANSFERE, ABROGE_DIFF, VIGUEUR_DIFF, PERIME, DISJOINT |
| date_debut   | day  |                                                                                                  |
| date_fin     | day  |                                                                                                  |
| type         | text | AUTONOME, ENTIEREMENT_MODIF, PARTIELLEMENT_MODIF, NULL                                           |
| nota         | text |                                                                                                  |
| bloc_textuel | text |                                                                                                  |
| dossier      | text | cf dossier                                                                                       |
| cid          | char |                                                                                                  |
| mtime        | int  |                                                                                                  |



## db_meta

| name  | type | description |
|:------|:----:|:------------|
| key   | text |             |
| value | blob |             |


## textes

| name        |  type   | description                                                                       |
|:------------|:-------:|:----------------------------------------------------------------------------------|
| id          | integer |                                                                                   |
| nature      |  text   | ARRETE, CONVENTION, DECISION, DECRET, LOI, LOI_CONSTIT, LOI_ORGANIQUE, ORDONNANCE |
| num         |  text   |                                                                                   |
| nor         |  char   | Numéro NOR                                                                        |
| titrefull_s |  text   | Titre du texte                                                                    |


## textes_structs

| name     | type | description |
|:---------|:----:|:------------|
| id       | char |             |
| versions | text |             |
| dossier  | text | cf dossier  |
| cid      | char |             |
| mtime    | int  |             |


## textes_versions

| name                  | type | description                                                                                                                    |
|:----------------------|:----:|:-------------------------------------------------------------------------------------------------------------------------------|
| id                    | char |                                                                                                                                |
| nature                | text | ARRETE, DECRET, ORDONNANCE, LOI, LOI_ORGANIQUE, LOI_CONSTIT, DECRET_LOI, CONSTITUTION, DECLARATION, DECISION, CONVENTION, CODE |
| titre                 | text |                                                                                                                                |
| titrefull             | text |                                                                                                                                |
| titrefull_s           | text |                                                                                                                                |
| etat                  | text | VIGUEUR, MODIFIE, ABROGE, ANNULE, PERIME, ABROGE_DIFF, VIGUEUR_DIFF, MODIFIE_MORT_NE                                           |
| date_debut            | day  |                                                                                                                                |
| date_fin              | day  |                                                                                                                                |
| autorite              | text | CONSEIL D'ETAT, ROI, NULL                                                                                                      |
| ministere             | text |                                                                                                                                |
| num                   | text |                                                                                                                                |
| num_sequence          | int  |                                                                                                                                |
| nor                   | char | Numéro NOR                                                                                                                     |
| date_publi            | day  |                                                                                                                                |
| date_texte            | day  |                                                                                                                                |
| derniere_modification | day  |                                                                                                                                |
| origine_publi         | text |                                                                                                                                |
| page_deb_publi        | int  |                                                                                                                                |
| page_fin_publi        | int  |                                                                                                                                |
| visas                 | text |                                                                                                                                |
| signataires           | text |                                                                                                                                |
| tp                    | text |                                                                                                                                |
| nota                  | text |                                                                                                                                |
| abro                  | text |                                                                                                                                |
| rect                  | text |                                                                                                                                |
| dossier               | text |                                                                                                                                |
| cid                   | char |                                                                                                                                |
| mtime                 | int  |                                                                                                                                |
| texte_id              | int  |                                                                                                                                |


## sections

| name        | type | description              |
|:------------|:----:|:-------------------------|
| id          | char |                          |
| titre_ta    | text | titre de la section      |
| commentaire | text |                          |
| parent      | char | id de la section parente |
| dossier     | text | cf dossier               |
| cid         | char |                          |
| mtime       | int  |                          |



## sommaires

| name     | type | description              |
|:---------|:----:|:-------------------------|
| cid      | char |                          |
| parent   | char | id de la section parente |
| element  | char |                          |
| debut    | day  |                          |
| fin      | day  |                          |
| etat     | text |                          |
| num      | text |                          |
| position | int  |                          |
| _source  | text |                          |


## liens

| name      | type | description |
|:----------|:----:|:------------|
| src_id    | char |             |
| dst_cid   | char |             |
| dst_id    | char |             |
| dst_titre | text |             |
| typelien  | text |             |
| _reversed | bool |             |


## duplicate_files

| name          | type | description |
|:--------------|:----:|:------------|
| id            | char |             |
| sous_dossier  | text |             |
| cid           | char |             |
| dossier       | text |             |
| mtime         | int  |             |
| data          | text |             |
| other_cid     | char |             |
| other_dossier | text |             |
| other_mtime   | int  |             |


## textes_versions_brutes

| name       | type | description |
|:-----------|:----:|:------------|
| id         | char |             |
| bits       | int  |             |
| nature     | text |             |
| titre      | text |             |
| titrefull  | text |             |
| autorite   | text |             |
| num        | text |             |
| date_texte | day  |             |
| dossier    | text |             |
| cid        | char |             |
| mtime      | int  |             |

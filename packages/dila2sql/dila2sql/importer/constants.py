TABLES_MAP = {'ARTI': 'articles', 'SCTA': 'sections', 'TEXT': 'textes_', 'CONT': 'conteneurs'}
ARTICLE_TAGS = set('NOTA BLOC_TEXTUEL'.split())
SECTION_TA_TAGS = set('TITRE_TA COMMENTAIRE'.split())
TEXTELR_TAGS = set('VERSIONS'.split())
TEXTE_VERSION_TAGS = set('VISAS SIGNATAIRES TP NOTA ABRO RECT'.split())
META_ARTICLE_TAGS = set('NUM ETAT DATE_DEBUT DATE_FIN TYPE TITRE'.split())
META_CHRONICLE_TAGS = set("""
    NUM NUM_SEQUENCE NOR DATE_PUBLI DATE_TEXTE DERNIERE_MODIFICATION
    ORIGINE_PUBLI PAGE_DEB_PUBLI PAGE_FIN_PUBLI
""".split())
META_CONTENEUR_TAGS = set('TITRE ETAT NUM DATE_PUBLI'.split())
META_VERSION_TAGS = set(
    'TITRE TITREFULL ETAT DATE_DEBUT DATE_FIN AUTORITE MINISTERE'.split()
)
SOUS_DOSSIER_MAP = {
    'articles': 'article',
    'sections': 'section_ta',
    'textes_structs': 'texte/struct',
    'textes_versions': 'texte/version',
    'conteneurs': 'conteneur'
}
TYPELIEN_MAP = {
    "ABROGATION": "ABROGE",
    "ANNULATION": "ANNULE",
    "CODIFICATION": "CODIFIE",
    "CONCORDANCE": "CONCORDE",
    "CREATION": "CREE",
    "DEPLACE": "DEPLACEMENT",
    "DISJOINT": "DISJONCTION",
    "MODIFICATION": "MODIFIE",
    "PEREMPTION": "PERIME",
    "RATIFICATION": "RATIFIE",
    "TRANSFERE": "TRANSFERT",
}
TYPELIEN_MAP.update([(v, k) for k, v in TYPELIEN_MAP.items()])
TM_TAGS = ['TITRE_TM']

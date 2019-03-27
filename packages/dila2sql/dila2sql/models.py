from peewee import Proxy, Model, CharField, TextField, DateField, IntegerField, BooleanField, CompositeKey

db_proxy = Proxy()


class BaseModel(Model):
    class Meta:
        database = db_proxy


class Article(BaseModel):
    class Meta:
        table_name = "articles"

    id = CharField(primary_key=True)
    section = CharField()
    num = TextField()
    titre = TextField()
    etat = TextField()
    date_debut = DateField()
    date_fin = DateField()
    type = TextField()
    nota = TextField()
    bloc_textuel = TextField()
    dossier = TextField()
    cid = CharField()
    mtime = IntegerField()


class ArticleCalipso(BaseModel):
    class Meta:
        table_name = "articles_calipsos"
        primary_key = CompositeKey('article_id', 'calipso_id')

    article_id = CharField()
    calipso_id = CharField()


class Calipso(BaseModel):
    class Meta:
        table_name = "calipsos"

    id = CharField(primary_key=True)


class Conteneur(BaseModel):
    class Meta:
        table_name = "conteneurs"

    id = CharField(primary_key=True)
    titre = TextField()
    etat = TextField()
    nature = TextField()
    num = TextField()
    date_publi = DateField()
    mtime = IntegerField()


class DBMeta(BaseModel):
    class Meta:
        table_name = "db_meta"

    key = CharField(primary_key=True)
    value = CharField()


class DuplicateFile(BaseModel):
    class Meta:
        table_name = "duplicate_files"
        primary_key = CompositeKey('id', 'sous_dossier', 'cid', 'dossier')

    id = CharField()
    sous_dossier = TextField()
    cid = CharField()
    dossier = TextField()
    mtime = IntegerField()
    data = TextField()
    other_cid = CharField()
    other_dossier = TextField()
    other_mtime = IntegerField()


class Lien(BaseModel):
    class Meta:
        table_name = "liens"
        primary_key = CompositeKey('src_id', 'dst_id', 'typelien', '_reversed')

    src_id = CharField()
    dst_cid = CharField()
    dst_id = CharField()
    dst_titre = TextField()
    typelien = TextField()
    _reversed = BooleanField()


class Section(BaseModel):
    class Meta:
        table_name = "sections"

    id = CharField(primary_key=True)
    titre_ta = TextField()
    commentaire = TextField()
    parent = CharField()
    dossier = TextField()
    cid = CharField()
    mtime = IntegerField()


class Sommaire(BaseModel):
    class Meta:
        table_name = "sommaires"
        primary_key = CompositeKey('parent', 'element', 'position', '_source')

    cid = CharField()
    parent = CharField()
    element = CharField()
    debut = DateField()
    fin = DateField()
    etat = TextField()
    num = TextField()
    position = IntegerField()
    _source = TextField()


class Tetier(BaseModel):
    class Meta:
        table_name = "tetiers"

    id = CharField(primary_key=True)
    titre_tm = TextField()
    niv = IntegerField()
    conteneur_id = CharField()


class Texte(BaseModel):
    class Meta:
        table_name = "textes"

    id = CharField(primary_key=True)
    nature = TextField()
    num = TextField()
    nor = CharField()
    titrefull_s = TextField()


class TexteStruct(BaseModel):
    class Meta:
        table_name = "textes_structs"

    id = CharField(primary_key=True)
    versions = TextField()
    dossier = TextField()
    cid = CharField()
    mtime = IntegerField()


class TexteVersion(BaseModel):
    class Meta:
        table_name = "textes_versions"

    id = CharField(primary_key=True)
    nature = TextField()
    titre = TextField()
    titrefull = TextField()
    titrefull_s = TextField()
    etat = TextField()
    date_debut = DateField()
    date_fin = DateField()
    autorite = TextField()
    ministere = TextField()
    num = TextField()
    num_sequence = IntegerField()
    nor = CharField()
    date_publi = DateField()
    date_texte = DateField()
    derniere_modification = DateField()
    origine_publi = TextField()
    page_fin_publi = IntegerField()
    page_deb_publi = IntegerField()
    visas = TextField()
    signataires = TextField()
    tp = TextField()
    nota = TextField()
    abro = TextField()
    rect = TextField()
    dossier = TextField()
    cid = CharField()
    mtime = IntegerField()
    texte_id = CharField()


class TexteVersionBrute(BaseModel):
    class Meta:
        table_name = "textes_versions_brutes"

    id = CharField(primary_key=True)
    bits = IntegerField()
    nature = TextField()
    titre = TextField()
    titrefull = TextField()
    autorite = TextField()
    num = TextField()
    date_texte = DateField()
    dossier = TextField()
    cid = CharField()
    mtime = IntegerField()


TABLE_TO_MODEL = {
    'articles': Article,
    'articles_calipsos': ArticleCalipso,
    'calipsos': Calipso,
    'conteneurs': Conteneur,
    'db_meta': DBMeta,
    'duplicate_files': DuplicateFile,
    'liens': Lien,
    'sections': Section,
    'sommaires': Sommaire,
    'tetiers': Tetier,
    'textes': Texte,
    'textes_structs': TexteStruct,
    'textes_versions': TexteVersion,
    'textes_versions_brutes': TexteVersionBrute,
}


CREATE TABLE db_meta
( key     text   primary key
, value   text
);

INSERT INTO db_meta (key, value) VALUES ('schema_version', 5);

CREATE TABLE textes
( id            integer    primary key not null
, nature        text       not null
, num           text
, nor           text       unique   -- only used during factorization
, titrefull_s   text       unique   -- only used during factorization
, UNIQUE (nature, num)
);

CREATE TABLE textes_structs
( id         text   unique not null
, versions   text
, dossier    text
, cid        text   not null
, mtime      int    not null
);

CREATE TABLE textes_versions
( id                      text   unique not null
, nature                  text
, titre                   text
, titrefull               text
, titrefull_s             text
, etat                    text
, date_debut              date
, date_fin                date
, autorite                text
, ministere               text
, num                     text
, num_sequence            int
, nor                     text
, date_publi              date
, date_texte              date
, derniere_modification   date
, origine_publi           text
, page_deb_publi          int
, page_fin_publi          int
, visas                   text
, signataires             text
, tp                      text
, nota                    text
, abro                    text
, rect                    text
, dossier                 text
, cid                     text   not null
, mtime                   int    not null
, texte_id                int    references textes
);

CREATE INDEX textes_versions_titrefull_s ON textes_versions (titrefull_s);
CREATE INDEX textes_versions_texte_id ON textes_versions (texte_id);

CREATE TABLE sections
( id            text   unique not null
, titre_ta      text
, commentaire   text
, parent        text   -- REFERENCES sections(id)
, dossier       text
, cid           text   not null
, mtime         int    not null
);

CREATE TABLE articles
( id             text   unique not null
, section        text   -- REFERENCES sections(id)
, num            text
, titre          text
, etat           text
, date_debut     date
, date_fin       date
, type           text
, nota           text
, bloc_textuel   text
, dossier        text
, cid            text   not null
, mtime          int    not null
);

CREATE TABLE sommaires
( cid        text
, parent     text   -- REFERENCES sections OR conteneurs
, element    text   not null -- REFERENCES textes OR articles OR sections
, debut      date
, fin        date
, etat       text
, num        text
, position   int
, _source    text   -- to support incremental updates
);

-- CREATE UNIQUE INDEX sommaires_parent_element_idx ON sommaires(parent, element);
CREATE INDEX sommaires_parent_debut_fin_etat_num_idx ON sommaires (parent, debut, fin, etat, num);

/* for deletes in importer */
CREATE INDEX sommaires_source_idx ON sommaires(_source);

CREATE TABLE liens
( src_id      text   not null
, dst_cid     text
, dst_id      text
, dst_titre   text
, typelien    text
, _reversed   bool       -- to support incremental updates
, CHECK (length(dst_cid) > 0 OR length(dst_id) > 0 OR length(dst_titre) > 0)
);

CREATE INDEX liens_src_idx ON liens (src_id) WHERE NOT _reversed;
CREATE INDEX liens_dst_idx ON liens (dst_id) WHERE _reversed;

CREATE TABLE duplicate_files
( id              text   not null
, sous_dossier    text   not null
, cid             text
, dossier         text
, mtime           int    not null
, data            text   not null
, other_cid       text
, other_dossier   text
, other_mtime     int    not null
, UNIQUE (id, sous_dossier, cid, dossier)
);

CREATE TABLE textes_versions_brutes
( id           text   unique not null
, bits         int    not null
, nature       text
, titre        text
, titrefull    text
, autorite     text
, num          text
, date_texte   date
, dossier      text
, cid          text   not null
, mtime        int    not null
);

CREATE VIEW textes_versions_brutes_view AS
    SELECT a.dossier, a.cid, a.id,
           (CASE WHEN b.bits & 1 > 0 THEN b.nature ELSE a.nature END) AS nature,
           (CASE WHEN b.bits & 2 > 0 THEN b.titre ELSE a.titre END) AS titre,
           (CASE WHEN b.bits & 4 > 0 THEN b.titrefull ELSE a.titrefull END) AS titrefull,
           (CASE WHEN b.bits & 8 > 0 THEN b.autorite ELSE a.autorite END) AS autorite,
           (CASE WHEN b.bits & 16 > 0 THEN b.num ELSE a.num END) AS num,
           (CASE WHEN b.bits & 32 > 0 THEN b.date_texte ELSE a.date_texte END) AS date_texte,
           a.titrefull_s
      FROM textes_versions a
 LEFT JOIN textes_versions_brutes b
        ON b.id = a.id AND b.cid = a.cid AND b.dossier = a.dossier AND b.mtime = a.mtime;

CREATE TABLE conteneurs
( id           text   unique not null
, titre        text
, etat         text
, nature       text
, num          text
, date_publi   date
, mtime        int           not null
);

CREATE INDEX conteneurs_id_idx ON conteneurs (id);
CREATE INDEX conteneurs_num_idx ON conteneurs (num);

CREATE TABLE tetiers
( id             text   unique   not null
, titre_tm       text            not null
, niv            int             not null
, conteneur_id   text            not null
);

CREATE INDEX tetiers_id_idx ON tetiers (id);

CREATE TABLE calipsos
( id             text   unique not null
);
CREATE INDEX calipsos_id_idx ON calipsos (id);

CREATE TABLE articles_calipsos
( article_id   text   not null
, calipso_id   text   not null
);
CREATE UNIQUE INDEX article_calipsos_double_idx ON articles_calipsos (article_id, calipso_id);

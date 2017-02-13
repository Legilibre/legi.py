
CREATE TABLE db_meta
( key text primary key
, value blob
);

INSERT INTO db_meta (key, value) VALUES ('schema_version', 1);

CREATE TABLE textes
( id integer primary key not null
, nature text not null
, num text
, nor char(12) unique -- only used during factorization
, titrefull_s text unique -- only used during factorization
, UNIQUE (nature, num)
);

CREATE TABLE textes_structs
( id char(20) unique not null
, versions text
, dossier text not null
, cid char(20) not null
, mtime int not null
);

CREATE TABLE textes_versions
( id char(20) unique not null
, nature text
, titre text
, titrefull text
, titrefull_s text
, etat text
, date_debut day
, date_fin day
, autorite text
, ministere text
, num text
, num_sequence int
, nor char(12)
, date_publi day
, date_texte day
, derniere_modification day
, origine_publi text
, page_deb_publi int
, page_fin_publi int
, visas text
, signataires text
, tp text
, nota text
, abro text
, rect text
, dossier text not null
, cid char(20) not null
, mtime int not null
, texte_id int references textes
);

CREATE INDEX textes_versions_titrefull_s ON textes_versions (titrefull_s);
CREATE INDEX textes_versions_texte_id ON textes_versions (texte_id);

CREATE TABLE sections
( id char(20) unique not null
, titre_ta text
, commentaire text
, parent char(20) -- REFERENCES sections(id)
, dossier text not null
, cid char(20) not null
, mtime int not null
);

CREATE TABLE articles
( id char(20) unique not null
, section char(20) -- REFERENCES sections(id)
, num text
, etat text
, date_debut day
, date_fin day
, type text
, nota text
, bloc_textuel text
, dossier text not null
, cid char(20) not null
, mtime int not null
);

CREATE TABLE sommaires
( cid char(20) not null
, parent char(20) -- REFERENCES sections
, element char(20) not null -- REFERENCES articles OR sections
, debut day
, fin day
, etat text
, num text
, position int
, _source text -- to support incremental updates
);

CREATE INDEX sommaires_cid_idx ON sommaires (cid);

CREATE TABLE liens
( src_id char(20) not null
, dst_cid char(20)
, dst_id char(20)
, dst_titre text
, typelien text
, _reversed bool -- to support incremental updates
, CHECK (length(dst_cid) > 0 OR length(dst_id) > 0 OR length(dst_titre) > 0)
);

CREATE INDEX liens_src_idx ON liens (src_id) WHERE NOT _reversed;
CREATE INDEX liens_dst_idx ON liens (dst_id) WHERE _reversed;

CREATE TABLE duplicate_files
( id char(20) not null
, sous_dossier text not null
, cid char(20) not null
, dossier text not null
, mtime int not null
, other_cid char(20) not null
, other_dossier text not null
, other_mtime int not null
, UNIQUE (id, sous_dossier, cid, dossier)
);

CREATE TABLE textes_versions_brutes
( id char(20) unique not null
, bits int not null
, nature text
, titre text
, titrefull text
, autorite text
, num text
, date_texte day
, dossier text not null
, cid char(20) not null
, mtime int not null
);

CREATE VIEW textes_versions_brutes_view AS
    SELECT a.dossier, a.cid, a.id,
           (CASE WHEN b.bits & 1 > 0 THEN b.nature ELSE a.nature END) AS nature,
           (CASE WHEN b.bits & 2 > 0 THEN b.titre ELSE a.titre END) AS titre,
           (CASE WHEN b.bits & 4 > 0 THEN b.titrefull ELSE a.titrefull END) AS titrefull,
           (CASE WHEN b.bits & 8 > 0 THEN b.autorite ELSE a.autorite END) AS autorite,
           (CASE WHEN b.bits & 16 > 0 THEN b.num ELSE a.num END) AS num,
           (CASE WHEN b.bits & 32 > 0 THEN b.date_texte ELSE a.date_texte END) AS date_texte
      FROM textes_versions a
 LEFT JOIN textes_versions_brutes b
        ON b.id = a.id AND b.cid = a.cid AND b.dossier = a.dossier AND b.mtime = a.mtime;

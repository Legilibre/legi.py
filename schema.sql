
CREATE TABLE db_meta
( key text primary key
, value blob
);

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

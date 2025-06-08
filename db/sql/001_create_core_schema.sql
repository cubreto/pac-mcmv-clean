-- Core / staging separation
CREATE SCHEMA IF NOT EXISTS stg;
CREATE SCHEMA IF NOT EXISTS core;

-- Staging tables are 1‑to‑1 with source sheets (created by COPY)
-- Core tables normalised for the KPIs

CREATE TABLE IF NOT EXISTS core.projeto (
  nu_apf             BIGINT PRIMARY KEY,
  programa           TEXT NOT NULL,             -- FAR / FDS / RURAL
  sg_uf              TEXT,
  no_municipio       TEXT,
  qt_uh              INTEGER,
  vr_total_operacao  NUMERIC(18,2),
  dt_inicio_obra     DATE,
  dt_previsao_entrega DATE,
  pc_obra_realizada  NUMERIC(5,2) DEFAULT 0
);

CREATE TABLE IF NOT EXISTS core.beneficiario (
  id SERIAL PRIMARY KEY,
  nu_apf BIGINT REFERENCES core.projeto(nu_apf),
  sexo   CHAR(1),
  vr_compra NUMERIC(18,2)
);

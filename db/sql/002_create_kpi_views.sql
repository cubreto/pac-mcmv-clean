CREATE OR REPLACE VIEW kpi_vw_portfolio AS
SELECT
  COUNT(*)                            AS total_projects,
  SUM(qt_uh)                          AS total_housing_units,
  SUM(vr_total_operacao)              AS total_investment,
  ROUND(AVG(pc_obra_realizada),2)     AS avg_completion
FROM core.projeto;

CREATE OR REPLACE VIEW kpi_vw_programa AS
SELECT programa,
       COUNT(*)                   AS total_projects,
       SUM(qt_uh)                 AS total_units,
       SUM(vr_total_operacao)     AS total_investment,
       ROUND(AVG(pc_obra_realizada),2) AS avg_completion
FROM core.projeto
GROUP BY programa;

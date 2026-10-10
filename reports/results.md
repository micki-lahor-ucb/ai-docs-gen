# Resultados de la prueba

Commit congelado: `f4ca646`.
El intervalo de Wilson, cuando se calcule, describe incertidumbre y no declara un ganador.
ROUGE-L es exploratorio y no mide veracidad.

Recall@3 de la recuperación compartida: 0.875 sobre 8 casos.

| Métrica | Plantilla | RAG |
|---|---:|---:|
| Borradores aceptables | 5/8 | 3/8 |
| Tasa de aceptación (Wilson 95 %) | 0.306–0.863 | 0.137–0.694 |
| Cuatro críticos aprobados | 7/8 | 5/8 |
| Errores críticos | 2 | 4 |
| Citas verificables | 7/8 | 7/8 |
| Completitud | 6/8 | 5/8 |
| Pertinencia | 0/8 | 0/8 |
| Formato | 8/8 | 8/8 |
| ROUGE-L exploratorio | 0.162 | 0.169 |
| Latencia mediana | 0 s | 18.4 s |
| Recall@3 de la recuperación compartida | 0.875 | 0.875 |

## Errores anotados

Una sola persona puntuó los borradores, con el método oculto al calificar. El estilo puede haberlo delatado. No hay acuerdo entre evaluadores.

- SYN-CHQ-2026-015 (rag): completeness, pertinence. Omite el hecho exigido de que el árbol fue parcialmente talado el día anterior e incorpora un antecedente judicial de otra persona y recomendaciones sobre linderos urbanos ajenas al objetivo rural.
- SYN-SCZ-2026-004 (rag): no_invention, missing_handled, completeness, pertinence. Afirma que el caso fue cerrado de inmediato por falta de pruebas. Rellena la situación jurídica como cerrada en lugar de dejarla pendiente. No identifica el caso, los sujetos, los antecedentes, la documentación ni los hechos de la clave. Convierte el borrador en una decisión de cierre.
- SYN-CHQ-2026-015 (baseline): completeness, pertinence. Omite el hecho exigido de que el árbol fue parcialmente talado el día anterior e incorpora recomendaciones sobre linderos urbanos y un antecedente judicial de otra persona ajenos al objetivo del caso rural.
- SYN-CBB-2026-012 (baseline): no_invention, verifiable_sources, pertinence. Añade sin respaldo que la pala estaba manchada en su hoja de metal y altera el contenido de la fuente 031, además de incorporar un antecedente judicial de otra persona ajeno al objetivo del caso.
- SYN-CBB-2026-022 (baseline): completeness, pertinence. Omite que el camión azul tenía la luz trasera derecha rota e incorpora antecedentes ajenos al caso sobre un conflicto de 2025 y otro incidente de tránsito del 15 de abril de 2026.
- SYN-CBB-2026-012 (rag): verifiable_sources, pertinence. Al copiar SRC-CBB-2026-030 omite «de» en la frase «a lo largo de quince metros lineales» e incorpora un antecedente de otro conflicto relativo a Ernesto Cárdenas Mamani, ajeno al objetivo del informe.
- SYN-SCZ-2026-013 (rag): no_invention, pertinence. Generaliza a partir de un único expediente de 2021 que no corresponde al incidente actual e incluye una nota sobre instrucciones de redacción ajenas al objetivo del informe.
- SYN-CBB-2026-022 (rag): completeness, pertinence. Omite que el camión azul tenía la luz trasera derecha rota (SRC-CBB-2026-052). Incorpora el conflicto de Arturo Pinto de 2025 y el incidente de tránsito del 15 de abril de 2026, ajenos al reporte de daños de Arturo Fernando Rojas.

## Corte por tipo de caso

- SYN-BEN-2026-008: contradiccion, faltantes, adversarial
- SYN-CBB-2026-012: faltantes
- SYN-CBB-2026-022: adversarial
- SYN-CHQ-2026-015: faltantes
- SYN-LPZ-2026-002: contradiccion
- SYN-SCZ-2026-004: adversarial
- SYN-SCZ-2026-013: adversarial
- SYN-TAR-2026-007: faltantes

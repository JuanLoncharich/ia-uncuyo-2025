# TP5 – CSP Validation Report

| Ítem | Resultado | Observaciones |
|------|-----------|---------------|
| Estructura de carpetas y archivos | ✅ OK | Todos los archivos requeridos presentes en `tp5-csp/`, `code/` e `images/`. |
| Sudoku CSP (`code/sudoku_csp.py`) | ✅ OK | Contiene referencias a CSP, AC-3, MRV, LCV y backtracking. Ejecución con `python3` resuelve el Sudoku de ejemplo (81 celdas), y AC-3 reduce dominios (`domains_reduced = 81`). |
| AC-3 Australia (`code/ac3_demo.py`) | ✅ OK | El script imprime inconsistencia para `WA=red`, `V=blue` (dominio vacío para `Q`) y muestra escenario alternativo consistente; dominios listados por variable. |
| N-Reinas (backtracking y forward checking) | ❌ FAIL | Las funciones se llaman `solve_n_queens_*` (no existe `solve`). Retornan `NQueensResult` con `found_solution`, `solution`, `explored_nodes`, `time`, pero faltan los campos `time_sec` y `algorithm_name` solicitados. El CSV carece de columnas `time_sec` y `seed`; encabezados actuales: `algorithm_name,n,found_solution,time,explored_nodes`. |
| Estadísticas y gráficos | ✅ OK | `compute_stats` y `make_boxplots` presentes en `code/utils.py`; imágenes `images/boxplot_tiempos.png` y `images/boxplot_nodos.png` generadas el 2025-11-01 12:07:26 (-0300). |
| Reporte `tp5-reporte.md` | ✅ OK | Contiene secciones “Ejercicio 1” a “Ejercicio 5”, referencias a boxplots y comparación explícita con TP4. |
| Reproducibilidad (`.venv_validation`) | ✅ OK | Con entorno virtual fresco (`python3 -m venv .venv_validation` + pip install pandas/matplotlib) el comando `.venv_validation/bin/python code/n_reinas_runner.py --n 4 8 10 --algo both --runs 30` se ejecuta sin errores y regenera CSV/gráficos. |

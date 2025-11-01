# TP5 – CSP (Inteligencia Artificial)

## Estructura principal
- `code/sudoku_csp.py`: modelo CSP del Sudoku con backtracking + AC-3.
- `code/ac3_demo.py`: demostración del algoritmo AC-3 sobre el mapa de Australia.
- `code/n_reinas_backtracking.py`: resolución de N-Reinas por backtracking clásico.
- `code/n_reinas_forward.py`: versión con forward checking.
- `code/n_reinas_runner.py`: orquesta los experimentos y genera el CSV.
- `code/utils.py`: funciones de estadística y gráficos.
- `tp5-Nreinas.csv`: resultados experimentales.
- `images/boxplot_tiempos.png`, `images/boxplot_nodos.png`: visualizaciones.
- `tp5-reporte.md`: informe con el desarrollo teórico y experimental.

## Requisitos
Python 3.10+ y los paquetes `pandas` y `matplotlib`.

Se recomienda usar un entorno virtual:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install pandas matplotlib
```

## Uso
- **Sudoku:** `python code/sudoku_csp.py` imprime la solución del Sudoku de ejemplo.
- **AC-3:** `python code/ac3_demo.py` muestra cómo AC-3 detecta inconsistencia para WA=red, V=blue y un escenario alternativo consistente.
- **Experimentos N-Reinas:** `python code/n_reinas_runner.py --n 4 8 10 --algo both --runs 30` genera `tp5-Nreinas.csv` y actualiza los boxplots. Puede restringirse a un algoritmo con `--algo BT` o `--algo FC`, modificar `--runs` o cambiar la ruta de salida con `--output`.

Los resultados se resumen en `tp5-reporte.md`, donde se incluyen tablas y análisis comparativos con los algoritmos de búsqueda local del TP4.

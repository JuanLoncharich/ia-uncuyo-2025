"""
Demostración del algoritmo AC-3 utilizando el mapa de Australia.

Se muestran dos escenarios:
1. Asignación WA=red, V=blue (inconsistente) donde AC-3 vacía un dominio.
2. Asignación alternativa WA=red, V=red (consistente) para comparar.
"""

from __future__ import annotations

from collections import deque
from copy import deepcopy
from typing import Dict, Iterable, Mapping, Set, Tuple

Variable = str
Color = str
Domains = Dict[Variable, Set[Color]]
ConstraintGraph = Dict[Variable, Set[Variable]]


def build_australia_graph() -> ConstraintGraph:
    """Devuelve la estructura de adyacencia del mapa de Australia."""
    return {
        "WA": {"NT", "SA"},
        "NT": {"WA", "SA", "Q"},
        "Q": {"NT", "SA", "NSW"},
        "NSW": {"Q", "SA", "V"},
        "V": {"SA", "NSW", "T"},
        "SA": {"WA", "NT", "Q", "NSW", "V"},
        "T": {"V"},
    }


def initialise_domains(
    graph: ConstraintGraph, colors: Iterable[Color], fixed_assignments: Mapping[Variable, Color]
) -> Domains:
    """Crea dominios iniciales e impone asignaciones parciales."""
    color_set = set(colors)
    domains = {var: set(color_set) for var in graph}
    for var, value in fixed_assignments.items():
        if value not in color_set:
            raise ValueError(f"El color '{value}' no pertenece al dominio.")
        domains[var] = {value}
    return domains


def ac3(graph: ConstraintGraph, domains: Domains) -> bool:
    """Implementación estándar de AC-3. Devuelve False si detecta inconsistencia."""
    queue = deque((xi, xj) for xi in graph for xj in graph[xi])
    while queue:
        xi, xj = queue.popleft()
        if revise(graph, domains, xi, xj):
            if not domains[xi]:
                return False
            for xk in graph[xi] - {xj}:
                queue.append((xk, xi))
    return True


def revise(graph: ConstraintGraph, domains: Domains, xi: Variable, xj: Variable) -> bool:
    """Elimina valores de xi que no tienen soporte en xj."""
    revised = False
    to_remove: Set[Color] = set()
    for value in domains[xi]:
        if not any(value != other for other in domains[xj]):
            to_remove.add(value)
    if to_remove:
        domains[xi] -= to_remove
        revised = True
    return revised


def run_demo(
    graph: ConstraintGraph, colors: Iterable[Color], fixed_assignments: Mapping[Variable, Color]
) -> Tuple[bool, Domains]:
    """
    Ejecuta AC-3 sobre una copia de los dominios.

    Devuelve un par (consistente, dominios_finales).
    """
    domains = initialise_domains(graph, colors, fixed_assignments)
    consistent = ac3(graph, domains)
    return consistent, domains


def _format_domains(domains: Domains) -> str:
    lines = []
    for var in sorted(domains):
        domain = ", ".join(sorted(domains[var]))
        lines.append(f"{var}: {{{domain}}}")
    return "\n".join(lines)


if __name__ == "__main__":
    graph = build_australia_graph()

    scenario_inconsistent = {"WA": "red", "V": "blue"}
    print("Escenario inconsistente (WA=red, V=blue):")
    consistent_inc, domains_inc = run_demo(graph, {"red", "green", "blue"}, scenario_inconsistent)
    print(_format_domains(domains_inc))
    print(f"¿Consistente? {'Sí' if consistent_inc else 'No'}\n")

    scenario_consistent = {"WA": "red", "V": "red"}
    print("Escenario alternativo consistente (WA=red, V=red):")
    consistent_alt, domains_alt = run_demo(graph, {"red", "green", "blue"}, scenario_consistent)
    print(_format_domains(domains_alt))
    print(f"¿Consistente? {'Sí' if consistent_alt else 'No'}")

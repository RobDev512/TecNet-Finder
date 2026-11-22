# ============================================================
# Archivo: triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Define las estructuras utilizadas para representar
# el código intermedio mediante triplos.
# ============================================================

from dataclasses import dataclass

# Operadores que necesitan dos argumentos.
OPERADORES_BINARIOS = frozenset({
    "+",
    "^",
    "INICIAR_RED",
    "SOLICITUD",
    "ASIGNAR_VLSM",
})

# Operadores que necesitan solamente un argumento.
OPERADORES_UNARIOS = frozenset({
    "LOG2",
    "CEIL",
    "SIGUIENTE_CURSOR",
})


@dataclass(frozen=True)
class ReferenciaTriplo:
    indice: int

    def __post_init__(self):
        if type(self.indice) is not int or self.indice < 0:
            raise ValueError("El índice del triplo debe ser un entero no negativo.")

    def __str__(self):
        return f"({self.indice})"

@dataclass(frozen=True)
class OrigenTriplo:
    linea_origen: int
    indice_bloque: int
    indice_host: int | None = None

    def __post_init__(self):
        if type(self.linea_origen) is not int or self.linea_origen < 1:
            raise ValueError("La línea de origen debe ser un entero positivo")

        if type(self.indice_bloque) is not int or self.indice_bloque < 0:
            raise ValueError("El índice del bloque debe ser un entero no negativo.")

        if self.indice_host is not None:
            if type(self.indice_host) is not int or self.indice_host < 0:
                raise ValueError("El índice del host debe ser un entero no negativo.")

@dataclass(frozen=True)
class Triplo:
    indice: int
    operador: str
    argumento1: int | str | ReferenciaTriplo
    argumento2: int | str | ReferenciaTriplo | None = None
    origen: OrigenTriplo | None = None

    def __post_init__(self):
        # Verifica que el índice sea correcto.
        if type(self.indice) is not int or self.indice < 0:
            raise ValueError("El índice del triplo debe ser un entero no negativo.")

        # Verifica que el operador exista y esté permitido.
        if not isinstance(self.operador, str):
            raise ValueError("El operador debe ser una cadena de texto.")

        if self.operador not in OPERADORES_BINARIOS | OPERADORES_UNARIOS:
            raise ValueError(f"Operador no reconocido: {self.operador}")

        # Todos los triplos necesitan un primer argumento.
        if self.argumento1 is None:
            raise ValueError("El triplo necesita un primer argumento.")

        # Los operadores binarios necesitan dos argumentos.
        if self.operador in OPERADORES_BINARIOS and self.argumento2 is None:
            raise ValueError(
                f"El operador {self.operador} necesita dos argumentos."
            )

        # Los operadores unarios solamente aceptan un argumento.
        if self.operador in OPERADORES_UNARIOS and self.argumento2 is not None:
            raise ValueError(
                f"El operador {self.operador} solamente acepta un argumento."
            )

        # Comprueba que el origen tenga la estructura correcta.
        if self.origen is not None:
            if not isinstance(self.origen, OrigenTriplo):
                raise ValueError("El origen debe ser un objeto OrigenTriplo.")

        # Comprueba los tipos de los argumentos.
        for argumento in (self.argumento1, self.argumento2):

            if argumento is None:
                continue

            if type(argumento) is int:
                continue

            if isinstance(argumento, ReferenciaTriplo):
                continue

            if isinstance(argumento, str) and argumento.strip():
                continue

            raise ValueError("El triplo contiene un argumento no válido.")


        # Comprueba los argumentos de las operaciones matemáticas.
        operadores_matematicos = {"+", "^", "LOG2", "CEIL"}

        if self.operador in operadores_matematicos:
            argumentos = (self.argumento1, self.argumento2)

            for argumento in argumentos:
                if argumento is None:
                    continue

                if type(argumento) is int:
                    continue

                if isinstance(argumento, ReferenciaTriplo):
                    continue

                raise ValueError(
                    "Las operaciones matemáticas necesitan enteros o referencias."
                )

        # Comprueba los argumentos de las operaciones de redes.
        if self.operador == "INICIAR_RED":
            if not (
                isinstance(self.argumento1, str)
                and isinstance(self.argumento2, str)
            ):
                raise ValueError(
                    "INICIAR_RED necesita una IP y una máscara en texto."
                )
        elif self.operador == "SOLICITUD":
            if type(self.argumento1) is not int or self.argumento1 <= 0:
                raise ValueError(
                    "SOLICITUD necesita de una cantidad positiva de hosts."
                )

            if not isinstance(self.argumento2, ReferenciaTriplo):
                raise ValueError(
                    "SOLICITUD necesita una referencia al tamaño del bloque."
                )

        elif self.operador == "ASIGNAR_VLSM":
            if not (
                isinstance(self.argumento1, ReferenciaTriplo)
                and isinstance(self.argumento2, ReferenciaTriplo)
            ):
                raise ValueError(
                    "ASIGNAR_VLSM necesita dos referencias."
                )

        elif self.operador == "SIGUIENTE_CURSOR":
            if not isinstance(self.argumento1, ReferenciaTriplo):
                raise ValueError(
                    "SIGUIENTE_CURSOR necesita una referencia a una subred."
                )


    def __str__(self):
        argumento2 = self.argumento2 if self.argumento2 is not None else "—"
        return f"({self.indice}): ({self.operador}, {self.argumento1}, {argumento2})"


class ResultadoIntermedio:
    def __init__(self):
        self._triplos: list[Triplo] = []

    @property
    def triplos(self) -> tuple[Triplo, ...]:
        return tuple(self._triplos)

    def agregar(
        self, operador: str,
        argumento1: int | str | ReferenciaTriplo,
        argumento2: int | str | ReferenciaTriplo | None = None,
        origen: OrigenTriplo | None = None
    ) -> Triplo:

        indice = len(self._triplos)
        nuevo = Triplo(indice, operador, argumento1, argumento2, origen)

        for argumento in (nuevo.argumento1, nuevo.argumento2):
            if isinstance(argumento, ReferenciaTriplo):
                if argumento.indice >= indice:
                    raise ValueError(
                        "La referencia debe apuntar a un triplo anterior."
                    )

        self._triplos.append(nuevo)
        return nuevo
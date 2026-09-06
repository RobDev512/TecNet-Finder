from dataclasses import dataclass, field

from Motor.diagnosticos import Diagnostico


@dataclass(frozen=True)
class Token:
    tipo: str
    valor: str
    linea: int
    columna: int


@dataclass
class ResultadoLexico:
    tokens: list[Token] = field(default_factory=list)
    diagnosticos: list[Diagnostico] = field(default_factory=list)

    @property
    def tiene_errores(self) -> bool:
        return any(
            diagnostico.severidad == "error"
            for diagnostico in self.diagnosticos
        )
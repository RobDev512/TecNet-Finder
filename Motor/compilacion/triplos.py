# ============================================================
# Archivo: triplos.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Define las estructuras utilizadas para representar
# el código intermedio mediante triplos.
# ============================================================

from dataclasses import dataclass  # Permite declarar referencias y operaciones como modelos inmutables.

OPERADORES_BINARIOS = frozenset({"+", "^", "INICIAR_RED", "SOLICITUD", "ASIGNAR_VLSM"})  # Declara las operaciones que requieren exactamente dos argumentos.
OPERADORES_UNARIOS = frozenset({"LOG2", "CEIL", "SIGUIENTE_CURSOR"})  # Declara las operaciones que requieren solamente un argumento.

@dataclass(frozen=True)
class ReferenciaTriplo:  # Representa una referencia numérica al resultado de otro triplo.
    indice: int  # Identifica el número del triplo al que apunta la referencia.

    def __post_init__(self):  # Valida los valores del modelo antes de permitir su uso.
        if type(self.indice) is not int or self.indice < 0:  # Impide valores de tipo incorrecto en esta operación.
            raise ValueError("El índice del triplo debe ser un entero no negativo.")  # Detiene el procesamiento cuando se incumple la condición requerida.

    def __str__(self):  # Muestra la referencia u operación con el formato empleado en clase.
        return f'({self.indice})'  # Representa la referencia con paréntesis, por ejemplo (3).

@dataclass(frozen=True)
class OrigenTriplo:  # Conserva la línea, el bloque y la posición original de HOSTS.
    linea_origen: int  # Señala la línea del DSL que originó esta instrucción.
    indice_bloque: int  # Identifica el bloque dentro de los aceptados por el semántico.
    indice_host: int | None = None  # Conserva la posición original en HOSTS, si corresponde.

    def __post_init__(self):  # Valida los valores del modelo antes de permitir su uso.
        if type(self.linea_origen) is not int or self.linea_origen < 1:  # Impide valores de tipo incorrecto en esta operación.
            raise ValueError("La línea de origen debe ser un entero positivo")  # Detiene el procesamiento cuando se incumple la condición requerida.
        
        if type(self.indice_bloque) is not int or self.indice_bloque < 0:  # Impide valores de tipo incorrecto en esta operación.
            raise ValueError("El índice del bloque debe ser un entero no negativo.")  # Detiene el procesamiento cuando se incumple la condición requerida.
        
        if self.indice_host is not None:  # Comprueba si se cumple la condición requerida para continuar.
            if type(self.indice_host) is not int or self.indice_host < 0:  # Impide valores de tipo incorrecto en esta operación.
                raise ValueError("El índice del host debe ser un entero no negativo.")  # Detiene el procesamiento cuando se incumple la condición requerida.

@dataclass(frozen=True)
class Triplo:  # Guarda una operación de código intermedio con sus argumentos y origen.
    indice: int  # Numera la instrucción dentro del código intermedio.
    operador: str  # Indica qué operación representa este triplo.
    argumento1: int | str | ReferenciaTriplo  # Guarda el primer operando literal o referenciado.
    argumento2: int | str | ReferenciaTriplo | None = None  # Conserva el segundo argumento o un guion cuando no existe.
    origen: OrigenTriplo | None = None  # Enlaza la operación con su posición de origen en el DSL.

    def __post_init__(self):  # Valida los valores del modelo antes de permitir su uso.
        if type(self.indice) is not int or self.indice < 0:  # Impide valores de tipo incorrecto en esta operación.
            raise ValueError("El índice del triplo debe ser un entero no negativo.")  # Detiene el procesamiento cuando se incumple la condición requerida.
        
        if not isinstance(self.operador, str):  # Impide valores de tipo incorrecto en esta operación.
            raise ValueError("El operador debe ser una cadena de texto.")  # Detiene el procesamiento cuando se incumple la condición requerida.
        
        if self.operador not in OPERADORES_BINARIOS | OPERADORES_UNARIOS:  # Comprueba si se cumple la condición requerida para continuar.
            raise ValueError(f'Operador no reconocido: {self.operador}')  # Detiene el procesamiento cuando se incumple la condición requerida.
        
        if self.argumento1 is None:  # Comprueba si se cumple la condición requerida para continuar.
            raise ValueError("El triplo necesita un primer argumento.")  # Detiene el procesamiento cuando se incumple la condición requerida.
        
        if self.operador in OPERADORES_BINARIOS and self.argumento2 is None:  # Comprueba las reglas de argumentos de esta familia de operadores.
            raise ValueError(f'El operador {self.operador} necesita dos argumentos.')  # Detiene el procesamiento cuando se incumple la condición requerida.
        
        if self.operador in OPERADORES_UNARIOS and self.argumento2 is not None:  # Comprueba las reglas de argumentos de esta familia de operadores.
            raise ValueError(f'El operador {self.operador} solamente acepta un argumento.')  # Detiene el procesamiento cuando se incumple la condición requerida.
        
        if self.origen is not None:  # Comprueba si se cumple la condición requerida para continuar.
            if not isinstance(self.origen, OrigenTriplo):  # Impide valores de tipo incorrecto en esta operación.
                raise ValueError("El origen debe ser un objeto OrigenTriplo.")  # Detiene el procesamiento cuando se incumple la condición requerida.
        
        for argumento in (self.argumento1, self.argumento2):  # Revisa los argumentos de la operación para validar sus tipos.
            if argumento is None:  # Omite el segundo argumento cuando el operador es unario.
                continue  # Acepta este tipo de argumento y continúa la validación.
            
            if type(argumento) is int:  # Impide valores de tipo incorrecto en esta operación.
                continue  # Acepta este tipo de argumento y continúa la validación.
            
            if isinstance(argumento, ReferenciaTriplo):  # Reconoce una referencia que debe sustituirse por su resultado.
                continue  # Acepta este tipo de argumento y continúa la validación.
            
            if isinstance(argumento, str) and argumento.strip():  # Impide valores de tipo incorrecto en esta operación.
                continue  # Acepta este tipo de argumento y continúa la validación.
            raise ValueError("El triplo contiene un argumento no válido.")  # Detiene el procesamiento cuando se incumple la condición requerida.
        operadores_matematicos = {"+", "^", "LOG2", "CEIL"}  # Delimita las operaciones que solo admiten números o referencias.
        if self.operador in operadores_matematicos:  # Comprueba las reglas de argumentos de esta familia de operadores.
            argumentos = (self.argumento1, self.argumento2)  # Reúne los operandos para validar su tipo de forma uniforme.
            
            for argumento in argumentos:  # Revisa los argumentos de la operación para validar sus tipos.
                
                if argumento is None:  # Omite el segundo argumento cuando el operador es unario.
                    continue  # Acepta este tipo de argumento y continúa la validación.
                
                if type(argumento) is int:  # Impide valores de tipo incorrecto en esta operación.
                    continue  # Acepta este tipo de argumento y continúa la validación.
                
                if isinstance(argumento, ReferenciaTriplo):  # Reconoce una referencia que debe sustituirse por su resultado.
                    continue  # Acepta este tipo de argumento y continúa la validación.
                raise ValueError("Las operaciones matemáticas necesitan enteros o referencias.")  # Detiene el procesamiento cuando se incumple la condición requerida.
        
        if self.operador == "INICIAR_RED":  # Comprueba que IP y máscara estén representadas como textos.
            if not (isinstance(self.argumento1, str) and isinstance(self.argumento2, str)):  # Impide valores de tipo incorrecto en esta operación.
                raise ValueError("INICIAR_RED necesita una IP y una máscara en texto.")  # Detiene el procesamiento cuando se incumple la condición requerida.
        
        elif self.operador == "SOLICITUD":  # Valida hosts positivos y una referencia al tamaño requerido.
            if type(self.argumento1) is not int or self.argumento1 <= 0:  # Impide valores de tipo incorrecto en esta operación.
                raise ValueError("SOLICITUD necesita de una cantidad positiva de hosts.")  # Detiene el procesamiento cuando se incumple la condición requerida.
            
            if not isinstance(self.argumento2, ReferenciaTriplo):  # Impide valores de tipo incorrecto en esta operación.
                raise ValueError("SOLICITUD necesita una referencia al tamaño del bloque.")  # Detiene el procesamiento cuando se incumple la condición requerida.
        
        elif self.operador == "ASIGNAR_VLSM":  # Comprueba que la asignación reciba dos referencias a resultados anteriores.
            if not (isinstance(self.argumento1, ReferenciaTriplo) and isinstance(self.argumento2, ReferenciaTriplo)):  # Impide valores de tipo incorrecto en esta operación.
                raise ValueError("ASIGNAR_VLSM necesita dos referencias.")  # Detiene el procesamiento cuando se incumple la condición requerida.
        
        elif self.operador == "SIGUIENTE_CURSOR":  # Exige una referencia al triplo de asignación anterior.
            if not isinstance(self.argumento1, ReferenciaTriplo):  # Impide valores de tipo incorrecto en esta operación.
                raise ValueError("SIGUIENTE_CURSOR necesita una referencia a una subred.")  # Detiene el procesamiento cuando se incumple la condición requerida.

    def __str__(self):  # Muestra la referencia u operación con el formato empleado en clase.
        argumento2 = self.argumento2 if self.argumento2 is not None else "—"  # Conserva el segundo argumento o un guion cuando no existe.
        return f'({self.indice}): ({self.operador}, {self.argumento1}, {argumento2})'  # Produce la notación (n): (Op, Arg1, Arg2).

class ResultadoIntermedio:  # Administra los triplos y garantiza una numeración consecutiva.

    def __init__(self):  # Prepara una colección vacía de triplos para la compilación actual.
        self._triplos: list[Triplo] = []  # Crea la lista interna que conservará los triplos numerados.

    @property
    def triplos(self) -> tuple[Triplo, ...]:  # Proporciona una vista de los triplos sin exponer la lista interna.
        return tuple(self._triplos)  # Expone una copia inmutable sin permitir alterar la lista interna.

    def agregar(self, operador: str, argumento1: int | str | ReferenciaTriplo, argumento2: int | str | ReferenciaTriplo | None = None, origen: OrigenTriplo | None = None) -> Triplo:  # Agrega un triplo numerado y evita referencias a operaciones futuras.
        indice = len(self._triplos)  # Obtiene el índice consecutivo de la nueva operación.
        nuevo = Triplo(indice, operador, argumento1, argumento2, origen)  # Construye el triplo y aplica las validaciones de su modelo.
        for argumento in (nuevo.argumento1, nuevo.argumento2):  # Revisa los argumentos de la operación para validar sus tipos.
            if isinstance(argumento, ReferenciaTriplo):  # Reconoce una referencia que debe sustituirse por su resultado.
                if argumento.indice >= indice:  # Impide referencias hacia el propio triplo o hacia operaciones futuras.
                    raise ValueError("La referencia debe apuntar a un triplo anterior.")  # Detiene el procesamiento cuando se incumple la condición requerida.
        
        self._triplos.append(nuevo)  # Incorpora el nuevo triplo únicamente después de validar sus referencias.
        return nuevo  # Devuelve el triplo que ya quedó almacenado en su índice.
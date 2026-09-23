# ============================================================
# Archivo: traductor_sintaxis.py
# Proyecto: TecNet Finder
# Materia: Lenguajes y Autómatas II
#
# Descripción:
# Reconstruye únicamente la representación visible de la
# información sintáctica en el idioma activo.
#
# La gramática formal, los símbolos S/A/B/L/C/N, los tipos de
# token y las palabras reservadas IP, MASK, HOSTS y NAME no se
# modifican.
# ============================================================

from Motor.compilacion.modelos import BloqueRed, NodoSintactico
from Motor.internacionalizacion.gestor_traducciones import GestorTraducciones


class TraductorSintaxis:
    def __init__(self, gestor: GestorTraducciones):
        self.gestor = gestor

    def _t(self, clave: str, **variables) -> str:
        return self.gestor.traducir(clave, **variables)

    def producciones(self, bloques: list[BloqueRed]) -> str:
        lineas = [
            self._t("sintaxis.gramatica.titulo"),
            "",
            "S → B A",
            "A → B A | ε",
            "B → IP IP_ADDRESS MASK SUBNET_MASK HOSTS L N",
            "L → NUMBER C",
            "C → COMMA NUMBER C | ε",
            "N → NAME IDENTIFIER | ε",
            "",
            f"S = {self._t('sintaxis.gramatica.programa')}",
            f"A = {self._t('sintaxis.gramatica.continuacion_programa')}",
            f"B = {self._t('sintaxis.gramatica.bloque_red')}",
            f"L = {self._t('sintaxis.gramatica.lista_hosts')}",
            f"C = {self._t('sintaxis.gramatica.continuacion_hosts')}",
            f"N = {self._t('sintaxis.gramatica.nombre_opcional')}",
            "",
            self._t("sintaxis.producciones.titulo"),
            "",
        ]

        if not bloques:
            lineas.append(self._t("sintaxis.producciones.sin_bloques"))
            return "\n".join(lineas).rstrip() + "\n"

        total_bloques = len(bloques)
        lineas.append(self._t("sintaxis.producciones.programa_completo"))
        lineas.append("S → B A")

        if total_bloques > 1:
            lineas.append(
                self._t(
                    "sintaxis.producciones.continuaciones",
                    cantidad=total_bloques - 1,
                )
            )

        lineas.extend(
            [
                self._t("sintaxis.producciones.termina_programa"),
                "",
            ]
        )

        for indice, bloque in enumerate(bloques, start=1):
            hosts_texto = ",".join(map(str, bloque.cantidades_hosts))
            entrada = f"IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_texto}"
            if bloque.nombre:
                entrada += f" NAME {bloque.nombre}"

            lineas.append(self._t("sintaxis.producciones.bloque", indice=indice))
            lineas.append(self._t("sintaxis.producciones.entrada", entrada=entrada))
            lineas.append("")
            lineas.append("B → IP IP_ADDRESS MASK SUBNET_MASK HOSTS L N")
            lineas.append("L → NUMBER C")

            hosts_adicionales = max(len(bloque.cantidades_hosts) - 1, 0)
            if hosts_adicionales > 0:
                lineas.append(
                    self._t(
                        "sintaxis.producciones.hosts_adicionales",
                        cantidad=hosts_adicionales,
                    )
                )

            lineas.append("C → ε")
            lineas.append("N → NAME IDENTIFIER" if bloque.nombre else "N → ε")
            lineas.append("")

        return "\n".join(lineas).rstrip() + "\n"

    def derivacion(self, bloques: list[BloqueRed]) -> str:
        lineas = [self._t("sintaxis.derivacion.titulo"), ""]

        if not bloques:
            lineas.append(self._t("sintaxis.derivacion.sin_bloques"))
            return "\n".join(lineas).rstrip() + "\n"

        total_bloques = len(bloques)
        lineas.extend(
            [
                self._t("sintaxis.derivacion.general"),
                "",
                "S",
                "⇒ B A",
            ]
        )

        if total_bloques == 1:
            lineas.extend(["⇒ B ε", "⇒ B"])
        else:
            for cantidad in range(2, total_bloques + 1):
                forma = (("B " * cantidad) + "A").strip()
                lineas.append(f"⇒ {forma}")

            bloques_texto = ("B " * total_bloques).strip()
            lineas.extend([f"⇒ {bloques_texto} ε", f"⇒ {bloques_texto}"])

        lineas.append("")

        for indice, bloque in enumerate(bloques, start=1):
            lineas.extend(self._derivacion_bloque(bloque, indice))
            lineas.append("")

        return "\n".join(lineas).rstrip() + "\n"

    def _derivacion_bloque(self, bloque: BloqueRed, indice: int) -> list[str]:
        lineas = [
            self._t("sintaxis.derivacion.bloque", indice=indice),
            "",
        ]

        if not bloque.cantidades_hosts:
            lineas.append(self._t("sintaxis.derivacion.sin_hosts"))
            return lineas

        hosts_actuales = str(bloque.cantidades_hosts[0])
        lineas.extend(
            [
                "B",
                "⇒ IP IP_ADDRESS MASK SUBNET_MASK HOSTS L N",
                f"⇒ IP {bloque.direccion_ip} MASK SUBNET_MASK HOSTS L N",
                f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS L N",
                f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS NUMBER C N",
                f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales} C N",
            ]
        )

        for host in bloque.cantidades_hosts[1:]:
            lineas.append(
                f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} "
                f"HOSTS {hosts_actuales} COMMA NUMBER C N"
            )
            hosts_actuales += f",{host}"
            lineas.append(
                f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} "
                f"HOSTS {hosts_actuales} C N"
            )

        lineas.extend(
            [
                f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales} ε N",
                f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales} N",
            ]
        )

        if bloque.nombre:
            lineas.extend(
                [
                    f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales} NAME IDENTIFIER",
                    f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales} NAME {bloque.nombre}",
                ]
            )
        else:
            lineas.extend(
                [
                    f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales} ε",
                    f"⇒ IP {bloque.direccion_ip} MASK {bloque.mascara_subred} HOSTS {hosts_actuales}",
                ]
            )

        return lineas

    def arbol_textual(self, arboles: list[NodoSintactico]) -> str:
        if not arboles:
            return self._t("sintaxis.arbol.sin_validos_textual") + "\n"

        lineas = [self._t("sintaxis.arbol.textual.titulo"), ""]

        for indice, arbol in enumerate(arboles, start=1):
            lineas.append(self._t("sintaxis.arbol.indice", indice=indice))
            lineas.extend(self._formatear_nodo(arbol).rstrip().splitlines())
            lineas.append("")

        return "\n".join(lineas).rstrip() + "\n"

    def _formatear_nodo(self, nodo: NodoSintactico, prefijo: str = "", es_ultimo: bool = True) -> str:
        if nodo.etiqueta == "VALOR":
            etiqueta = str(nodo.valor)
        else:
            etiqueta = self.etiqueta_nodo(nodo.etiqueta)

        conector = "└── " if es_ultimo else "├── "
        salida = prefijo + conector + etiqueta + "\n"
        nuevo_prefijo = prefijo + ("    " if es_ultimo else "│   ")

        for indice, hijo in enumerate(nodo.hijos):
            salida += self._formatear_nodo(
                hijo,
                nuevo_prefijo,
                indice == len(nodo.hijos) - 1,
            )

        return salida

    def etiqueta_nodo(self, etiqueta: str) -> str:
        if etiqueta == "BloqueRed":
            return self._t("sintaxis.arbol.raiz")

        if etiqueta.startswith("BloqueRed:"):
            nombre = etiqueta.split(":", 1)[1].strip()
            return self._t("sintaxis.arbol.raiz_nombre", nombre=nombre)

        # Los tipos de token y las palabras reservadas son identificadores
        # formales de la representación y se mantienen estables.
        return etiqueta

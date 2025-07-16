class CamadaLigacao:
    ignorar_verificacao = False

    def __init__(self, canais):
        self.caminhos = {}
        self.receptor = None

        for destino_ip, canal in canais.items():
            enlace = MeioEnlace(canal)
            self.caminhos[destino_ip] = enlace
            enlace.registrar_receptor(self._receber_cru)

    def registrar_receptor(self, receptor):
        self.receptor = receptor

    def transmitir(self, pacote, proximo_salto):
        if proximo_salto in self.caminhos:
            self.caminhos[proximo_salto].transmitir(pacote)

    def _receber_cru(self, pacote):
        if self.receptor:
            self.receptor(pacote)


class MeioEnlace:
    def __init__(self, canal_serial):
        self.canal = canal_serial
        self.canal.registrar_recebedor(self._receber_bytes)
        self.memoria = b''
        self.escapando = False

    def registrar_receptor(self, receptor):
        self.receptor = receptor

    def transmitir(self, pacote):
        ESC = 0xDB
        ESC_C0 = 0xDC
        ESC_DB = 0xDD
        DELIMITADOR = 0xC0

        codificado = []

        for byte in pacote:
            if byte == ESC:
                codificado += [ESC, ESC_DB]
            elif byte == DELIMITADOR:
                codificado += [ESC, ESC_C0]
            else:
                codificado.append(byte)

        moldado = [DELIMITADOR] + codificado + [DELIMITADOR]
        self.canal.enviar(bytes(moldado))

    def _receber_bytes(self, dados):
        DELIMITADOR = 0xC0
        ESC = 0xDB
        ESC_C0 = 0xDC
        ESC_DB = 0xDD

        for byte in dados:
            if byte == DELIMITADOR:
                self._interpretar_delimitador()
            elif byte == ESC:
                self._marcar_escape()
            elif self.escapando:
                self._decodificar_escape(byte)
            else:
                self._guardar_byte(byte)

    def _interpretar_delimitador(self):
        if self.memoria:
            self._disparar_receptor()
            self.memoria = b''

    def _disparar_receptor(self):
        try:
            self.receptor(self.memoria)
        except Exception:
            import traceback
            traceback.print_exc()

    def _marcar_escape(self):
        self.escapando = True

    def _decodificar_escape(self, byte):
        ESC_C0 = 0xDC
        ESC_DB = 0xDD
        ESC = 0xDB

        if byte == ESC_C0:
            self.memoria += b'\xc0'
        elif byte == ESC_DB:
            self.memoria += b'\xdb'
        else:
            self.memoria += bytes([ESC, byte])

        self.escapando = False

    def _guardar_byte(self, byte):
        self.memoria += bytes([byte])

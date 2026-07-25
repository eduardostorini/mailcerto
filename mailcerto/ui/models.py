from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex
from mailcerto.core.models import CheckResult

class DNSResultsModel(QAbstractTableModel):
    def __init__(self, results: list[CheckResult] = None):
        super().__init__()
        self._results = results or []
        self._headers = ["Tipo/Registro", "Status", "Resumo", "Tempo (ms)"]

    def rowCount(self, parent=QModelIndex()):
        return len(self._results)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._results)):
            return None
        
        item = self._results[index.row()]
        col = index.column()
        
        if role == Qt.DisplayRole:
            if col == 0:
                return item.title
            elif col == 1:
                return item.status.value.upper()
            elif col == 2:
                return item.summary
            elif col == 3:
                return f"{item.response_time_ms:.1f}" if item.response_time_ms is not None else "-"
        
        elif role == Qt.TextAlignmentRole:
            if col == 3 or col == 1:
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter
            
        return None

    def update_results(self, new_results: list[CheckResult]):
        self.beginResetModel()
        self._results = new_results
        self.endResetModel()


class IPLocationResultsModel(QAbstractTableModel):
    """Modelo de tabela dedicado aos resultados de Localização de IP.

    Exibe IP, cidade, estado, CEP, status e tempo extraídos do campo
    ``raw_data`` de cada :class:`CheckResult`, permitindo visualizar essas
    informações diretamente na tabela sem precisar selecionar a linha.
    """

    def __init__(self, results: list[CheckResult] = None):
        super().__init__()
        self._results = results or []
        self._headers = [
            "IP", "Cidade", "Estado", "CEP", "Status", "Tempo (ms)"
        ]

    def rowCount(self, parent=QModelIndex()):
        return len(self._results)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]
        return None

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or not (0 <= index.row() < len(self._results)):
            return None

        item = self._results[index.row()]
        col = index.column()
        raw = item.raw_data or {}

        if role == Qt.DisplayRole:
            if col == 0:
                return raw.get("ip", "N/A")
            elif col == 1:
                return raw.get("city", "N/A")
            elif col == 2:
                return raw.get("region", "N/A")
            elif col == 3:
                return raw.get("postal", "N/A")
            elif col == 4:
                return item.status.value.upper()
            elif col == 5:
                return f"{item.response_time_ms:.1f}" if item.response_time_ms is not None else "-"

        elif role == Qt.TextAlignmentRole:
            if col in (0, 3, 4, 5):
                return Qt.AlignCenter
            return Qt.AlignLeft | Qt.AlignVCenter

        return None

    def update_results(self, new_results: list[CheckResult]):
        self.beginResetModel()
        self._results = new_results
        self.endResetModel()

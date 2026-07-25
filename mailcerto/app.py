import sys
import asyncio
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop
from mailcerto.ui.main_window import MainWindow
from mailcerto.database.models import init_db

def main():
    # Inicializar banco de dados SQLite local
    init_db()
    
    app = QApplication(sys.argv)
    
    # Criar e configurar o qasync Event Loop acoplado ao Qt
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    window = MainWindow()
    window.show()
    
    # Executar o loop de eventos assíncronos de forma segura
    with loop:
        sys.exit(loop.run_forever())

if __name__ == "__main__":
    main()

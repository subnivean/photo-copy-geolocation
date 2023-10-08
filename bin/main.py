from PySide6.QtWidgets import QMainWindow, QApplication
from exif import Image
import sys


class MainWidget(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Drag and Drop")
        self.resize(720, 480)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for f in files:
            imgdata = Image(f)
            print(f"{f=}, {imgdata.gps_latitude=}, {imgdata.gps_longitude=}")


if __name__ == "__main__":
    # try with /home/mark/Pictures/2023/20230930/2023_09_30T08_01_40_556.jpg
    app = QApplication(sys.argv)
    ui = MainWidget()
    ui.show()
    sys.exit(app.exec())

from PySide import QtCore 
from PySide import QtGui 




class MyDelegate (QtGui.QStyledItemDelegate ):
	
	closedSignal = QtCore.Signal()

	def __init__(self, parent=None): 
		super(MyDelegate, self).__init__(parent)
		self.closeEditor.connect(self.cSignal)

	def cSignal(self):
		self.closedSignal.emit()





class ListViewDrop(QtGui.QListWidget):

	fileDropped = QtCore.Signal(list)

	def __init__(self,type,parent=None):
		super(ListViewDrop, self).__init__(parent)
		self.setAcceptDrops(True)

	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls:
			event.accept()
		else:
			event.ignore()

	def dragMoveEvent(self, event):
		if event.mimeData().hasUrls:
			event.setDropAction(QtCore.Qt.CopyAction)
			event.accept()
		else:
			event.ignore()

	def dropEvent(self, event):
		if event.mimeData().hasUrls:
			event.setDropAction(QtCore.Qt.CopyAction)
			event.accept()
			links = []
			for url in event.mimeData().urls():
				#links.append(str(url.toLocalFile())) #pb encodage
				links.append(url.toLocalFile())
			self.fileDropped.emit(links)
		else:
		    event.ignore()


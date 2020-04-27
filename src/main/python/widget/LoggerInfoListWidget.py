from PyQt5.QtWidgets import QListWidget

class LoggerInfoListWidget(QListWidget):
	def __init__(self):
		super().__init__()
	
	def itemClicked(self, QListWidgetItem):
		super().itemClicked(QListWidgetItem)
	
	def clicked(self, QModelIndex):
		super().clicked(QModelIndex)

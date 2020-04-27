from PyQt5.QtWidgets import  QMenuBar

class CustomMenuBar(QMenuBar):
	def __init__(self, parent = None):
		super().__init__(parent)
		
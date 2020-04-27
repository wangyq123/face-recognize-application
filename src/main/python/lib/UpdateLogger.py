from PyQt5 import QtCore
from PyQt5.QtCore import QThread

class UpdateLogger(QThread):
	
	update_signal=QtCore.pyqtSignal(str)
	end_signal=QtCore.pyqtSignal(str)
	def __init__(self):
		super().__init__()
	
	def run(self):
		super().run()
		
	
		
	
		
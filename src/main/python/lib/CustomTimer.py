# from PyQt5.QtCore import QThread
# from gevent.libev.corecext import time,SIGNAL
# from qtpy import QtCore
#
# class CustomTimer(QThread):
# 	def __init__(self, signal = "updateTime()"):
# 		super().__init__()
# 		self.stopped = False
# 		self.signal = signal
# 		self.mutex = QtCore.QMutex()
#
# 	def run(self):
# 		with QtCore.QMutexLocker(self.mutex):
# 			self.stopped = False
# 		while True:
# 			if self.stopped:
# 				return
# 			self.emit(SIGNAL(self.signal))
# 			time.sleep(0.04)
#
# 	def stop(self):
# 		with QtCore.QMutexLocker(self.mutex):
# 			self.stopped = True
#
# 	def is_stopped(self):
# 		with QtCore.QMutexLocker(self.mutex):
# 			return self.stoped
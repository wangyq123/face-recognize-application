import logging

from PyQt5 import QtCore, QtSql
from PyQt5.QtCore import QThread
from PyQt5.QtSql import QSqlDatabase
from PyQt5.QtWidgets import QMessageBox, qApp

class PunchThread(QThread):
	punch_signal = QtCore.pyqtSignal(str)
	results_cache = []
	
	def __init__(self):
		super().__init__()
	
	def start(self, priority: QThread.Priority = QThread.NormalPriority) -> None:
		super().start(priority)
	
	def add(self, result: str, nbr_predicted: int):
		if result in self.results_cache:
			pass
		else:
			db: QSqlDatabase = QSqlDatabase.addDatabase(
				"QSQLITE")
			db.setDatabaseName('demo.db')
			if not db.open():
				QMessageBox.critical(None, qApp.tr("无法打开数据库"), qApp.tr('无法连接数据库'),
				                     QMessageBox.Cancel)
				logging.info('数据库连接失败....', hasError = True)
			else:
				logging.info('数据库已连接.....')
			query = QtSql.QSqlQuery()
			query.exec_(
				"update user_face_info set punched=1 where user_id={}".format(
					nbr_predicted))
			self.results_cache.append(result)
			result = "{0} 打卡成功!".format(result)
			self.punch_signal.emit(result)

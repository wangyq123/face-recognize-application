import logging
import os

import cv2
import numpy as np
from PIL import Image
from PyQt5 import QtSql, QtCore
from PyQt5.QtCore import QThread
from PyQt5.QtSql import QSqlDatabase

class TrainerThread(QThread):
	start_signal = QtCore.pyqtSignal(str)
	finish_signal = QtCore.pyqtSignal(str)
	
	def __init__(self, db: QSqlDatabase, cascadePath: str, data_path: str,
	             signal = None):
		super().__init__()
		self.recognizer = cv2.face.LBPHFaceRecognizer_create()
		self.faceCascade = cv2.CascadeClassifier(cascadePath)
		self.path = data_path
		if db is None:
			self._db = QSqlDatabase.addDatabase("QSQLITE")
			self._db.setDatabaseName("demo.db")
		self._db = db
		self.__query = QtSql.QSqlQuery()
		self.mutex = QtCore.QMutex()
		self._signal = signal
	
	def run(self):
		userId = 0
		data_path = self.path + r"\dataset"
		if os.path.exists(data_path) is False:
			os.mkdir(data_path)
		data_user_paths: list = [os.path.join(data_path, f) for f in os.listdir(
			data_path)]
		self.__delete_table()
		self.start_signal.emit("清楚数据成功")
		if len(data_user_paths) != 0:
			_images = []
			_labels = []
			user = dict()
			username = ""
			logging.info("start time.sleep")
			self.start_signal.emit("即将开始训练人脸信息数据....")
			logging.info("end time.sleep")
			self.start_signal.emit("开始训练人脸数据....")
			for user_path in data_user_paths:
				img_paths = [os.path.join(user_path, f) for f in
				             os.listdir(user_path)]
				for img_path in img_paths:
					image_pil = Image.open(img_path).convert('L')
					img = np.array(image_pil, 'uint8')
					username = str(
						os.path.split(img_path)[1].split(".")[0].split('-')[0]
					)
					faces = self.faceCascade.detectMultiScale(img,
					                                          scaleFactor = 1.15,
					                                          minNeighbors = 5,
					                                          minSize = (100, 100), )
					for (x, y, w, h) in faces:
						_images.append(img[y:y + h, x:x + w])
						_labels.append(userId)
						cv2.waitKey(10)
				user[username] = userId
				userId += 1
			self.recognizer.train(_images, np.array(_labels))
			if os.path.exists(os.path.join(self.path, r'trainer')) is False:
				os.mkdir(os.path.join(self.path, r'trainer'))
			
			self.recognizer.save(os.path.join(self.path, r'trainer\trainer.yml'))
			for key, value in user.items():
				self.__query.exec_(
					"insert into user_face_info(name,user_id) values ('" + key + "'," + str(
						value) + ")")
			self._db.commit()
			self.finish_signal.emit("数据训练完毕....")
			logging.info("数据训练完毕.....")
		else:
			self.start_signal.emit("训练数据失败....")
			self.start_signal.emit("数据文件夹中没有人脸数据,训练停止...")
	
	def __delete_table(self):
		query = self.__query
		query.exec_("delete from user_face_info")
		query.exec_(
			"update sqlite_sequence set seq=0 where name= 'user_face_info'")
		query.exec_("delete from sqlite_sequence where name='user_face_info'")
		if query.exec_("select * from user_face_info"):
			self._db.commit()
			logging.info("清空数据成功...")
		else:
			logging.error('清空数据失败')

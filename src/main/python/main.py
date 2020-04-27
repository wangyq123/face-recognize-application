import logging
import os
import shutil
import sys

import cv2
from PyQt5 import QtSql
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtSql import QSqlDatabase
from PyQt5.QtWidgets import *

from src.main.python.lib import UpdateLogger
from src.main.python.lib.PunchThread import PunchThread
from src.main.python.widget import LoggerInfoListWidget

class Main(QMainWindow):
	def __init__(self, parent = None):
		super().__init__(parent, flags = Qt.Window)
		self.setWindowTitle("PyQT+OpenCV实时人脸检测识别")
		self.resize(1096, 720)
		
		self.main_widget = QWidget(flags = Qt.Window)
		self.main_container = QHBoxLayout()
		self.left_container = QVBoxLayout()
		
		self.__collected = False
		self.__timer_info_collection = QTimer()
		self.__timer_recognizer = QTimer()
		self.__timer_detector = QTimer()
		self.timer = QTimer()
		self.__path = os.path.dirname(os.path.abspath(__file__))
		self.__cascadePath = self.__path + \
		                     r'./haarcascade_frontalface_default.xml'
		self.__font = cv2.FONT_HERSHEY_SIMPLEX
		self.__is_detecting = False
		self.__is_recognizer = False
		self.logger_info_list = LoggerInfoListWidget()
		self.punch_info_list = QListWidget()
		
		self.__video_container = QLabel()
		self.__video_container.setAlignment(Qt.AlignCenter)
		self.__query_cache = {}
		self.__cam = cv2.VideoCapture(0)
		self.__image = QImage()
		self.__update_logger_thread = UpdateLogger()
		self.__punchThread = PunchThread()
		self.__punchThread.start()
		self.__global_msg = '...'
		self.__init_ui()
	
	def _create_menubar(self):
		menu_bar: QMenu = self.menuBar()
		file = menu_bar.addMenu('File')
		file.addAction("New")
		save = QAction('保存', self)
		save.setShortcut('Ctrl+S')
		
		edit = file.addMenu('Edit')
		edit.addAction('Copy')
		edit.addAction("Paste")
		
		_quit = QAction('Quit', self)
		file.addAction(_quit)
		file.triggered[QAction].connect(self.__quit_triggered)
		self.setMenuBar(menu_bar)
	
	def __set_title(self, title: str):
		self.setWindowTitle(title)
	
	def __exit__(self, exc_type, exc_val, exc_tb):
		pass
	
	def __init_ui(self):
		self._create_menubar()
		
		right_container = QVBoxLayout()
		
		# 关闭摄像头
		self.__close_camera = QPushButton('停止')
		self.__close_camera.clicked.connect(self.__stop)
		self.__enable_close_camera_btn(False)
		
		# face detect 相关按钮
		face_detector_btn = QPushButton('人脸检测')
		simple_btn_style: str = r"height:24;background-color:rgb(123, 179," \
		                        r"139);color:black"
		face_detector_btn.setStyleSheet(simple_btn_style)
		# face_detector_stop_btn = QPushButton('停止')
		
		# face recognizer 相关按钮
		face_recognizer_btn = QPushButton('人脸识别')
		face_recognizer_btn.setStyleSheet(simple_btn_style)
		# face_recognizer_stop_btn = QPushButton('停止')
		
		# face info collection 相关按钮
		face_info_collection_btn = QPushButton('人脸录入')
		face_info_collection_btn.setStyleSheet(simple_btn_style)
		face_info_collection_btn.clicked.connect(self.__face_info_collection)
		
		# face detector container
		face_detector_container = QHBoxLayout()
		# face_detector_container.addWidget(face_detector_btn,
		#                                   alignment = Qt.AlignCenter)
		
		# face recognizer container
		face_recognizer_container = QHBoxLayout()
		face_recognizer_container.addWidget(face_recognizer_btn, alignment =
		Qt.AlignCenter)
		
		#
		# 人脸信息收集container
		face_info_collection_container = QHBoxLayout()
		face_info_collection_container.addWidget(face_info_collection_btn,
		                                         alignment = Qt.AlignCenter)
		
		# 开始训练按钮
		btn_start_training: QPushButton = QPushButton('开始训练')
		btn_start_training.setStyleSheet(simple_btn_style)
		btn_start_training.clicked.connect(self.__train)
		
		# 检测按钮相关事件绑定
		face_detector_btn.clicked.connect(self.__detector)
		face_recognizer_btn.clicked.connect(self.__recognizer)
		
		#  logger container
		logger_container = QVBoxLayout()
		
		logger_container.addWidget(self.logger_info_list, )
		
		# 填充right container
		
		right_container.addWidget(face_recognizer_btn, stretch = 0,
		                          alignment = Qt.AlignBaseline)
		right_container.addWidget(face_detector_btn, stretch = 0,
		                          alignment = Qt.AlignBaseline)
		right_container.addWidget(face_info_collection_btn, stretch = 0,
		                          alignment = Qt.AlignBaseline)
		right_container.addWidget(btn_start_training, stretch = 0, alignment =
		Qt.AlignBaseline)
		right_container.addWidget(self.__close_camera, stretch = 0,
		                          alignment = Qt.AlignBaseline)
		right_container.addLayout(logger_container, stretch = 8)
		# right_container.addStretch(8)
		
		# 填充left container
		self.left_container.addWidget(self.__video_container,
		                              alignment = Qt.AlignCenter)
		
		# 填充 main container
		self.main_container.addLayout(self.left_container, stretch = 8, )
		self.main_container.addLayout(right_container, stretch = 2)
		certificationInfo_container = QVBoxLayout()
		certificationInfo_container.addWidget(self.punch_info_list,
		                                      alignment = Qt.AlignJustify, )
		self.main_container.addLayout(certificationInfo_container, stretch = 2)
		
		# 填充 main widget
		self.main_widget.setLayout(self.main_container)
		self.setCentralWidget(self.main_widget)
		self.__connect_db()
		self.__update_logger_thread.update_signal.connect(
			self.__update_logger_info)
		
		# 添加对在人脸识别的时候,识别到的人脸进行认证,如果出现数据库中的人脸,则显示已打卡信息操作展示
		self.__punchThread.punch_signal.connect(self.punch)
	
	def punch(self, result: str):
		self.punch_info_list.addItem(result)
	
	def __init_recognizer(self) -> bool:
		# 初始化人脸识别器
		self.__recognizer = cv2.face.LBPHFaceRecognizer_create()
		if os.path.exists(self.__path + r'\trainer\trainer.yml'):
			self.__recognizer.read(self.__path + r'\trainer\trainer.yml')
			return True
		else:
			return False
	
	def __recognizer(self):
		"""
			人脸识别
		:return: None
		"""
		if self.__timer_detector.isActive():
			self.__timer_detector.stop()
		self.__show_msg("人脸识别开始")
		self.__global_msg = "用户已取消人脸识别"
		self.__open_cam()
		ok = self.__init_recognizer()
		if ok:
			self.__enable_close_camera_btn()
			self.__timer_recognizer.timeout.connect(self.__recognizer_play)
			self.__timer_recognizer.start(25)
		else:
			self.__show_msg(self.__path + r'\trainer\trainer.yml' + '该文件不存在',
			                "font-size:24px;color:red;")
	
	def __recognizer_play(self):
		if self.__cam.isOpened():
			ret, frame = self.__cam.read()
			height, width, bytesPerComponent = frame.shape
			bytesPerLine = bytesPerComponent * width
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			cv2.cvtColor(frame, cv2.COLOR_BGR2RGB, frame)
			faceCascade = cv2.CascadeClassifier(self.__cascadePath)
			faces = faceCascade.detectMultiScale(gray, scaleFactor = 1.15,
			                                     minNeighbors = 5,
			                                     minSize = (100, 100), )
			for (x, y, w, h) in faces:
				nbr_predicted, conf = self.__recognizer.predict(
					gray[y:y + h, x:x + w])
				cv2.rectangle(frame, (x - 50, y - 50), (x + w + 30, y + h + 30),
				              (255, 0, 0), 2)
				if nbr_predicted in self.__query_cache.keys():
					result = self.__query_cache[nbr_predicted]
				else:
					if self.__query.exec_(
							"select * from user_face_info where user_id=" + str(
								nbr_predicted)):
						self.__query.next()
						result = self.__query.value(1)
						self.__query_cache[nbr_predicted] = result
					else:
						result = ''
				if result is not None and len(result) != 0:
					# 打印人脸认证信息
					self.__punchThread.add(result,nbr_predicted)
				# 打印出result
				cv2.putText(frame, str(result), (x + 50, y - 60),
				            self.__font, 1.1, (255, 0, 0))  # Draw the text
			self.__put_image(frame.data, width, height, bytesPerLine)
	
	def __detector(self):
		"""
		人脸检测
		:return:
		"""
		if self.__timer_recognizer.isActive():
			self.__timer_recognizer.stop()
		self.__show_msg("人脸检测开始")
		self.__global_msg = "用户已取消人脸检测"
		self.__open_cam()
		self.__enable_close_camera_btn()
		self.__timer_detector.timeout.connect(self.__detector_play)
		self.__timer_detector.start(25)
	
	def __detector_play(self):
		if self.__cam.isOpened():
			ret, frame = self.__cam.read()
			height, width, bytesPerComponent = frame.shape
			bytesPerLine = bytesPerComponent * width
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			cv2.cvtColor(frame, cv2.COLOR_BGR2RGB, frame)
			faceCascade = cv2.CascadeClassifier(self.__cascadePath)
			faces = faceCascade.detectMultiScale(gray,
			                                     scaleFactor = 1.15,
			                                     minNeighbors = 5,
			                                     minSize = (100, 100), )
			for (x, y, w, h) in faces:
				cv2.rectangle(frame, (x - 50, y - 50), (x + w + 50, y + h + 50),
				              (225, 0, 0), 2)
			
			self.__put_image(frame.data, width, height, bytesPerLine)
	
	def __face_info_collection(self):
		# self.__show_msg("开始录入人脸信息....")
		username, ok = self.__show_dialog()
		if ok:
			self.__show_msg("开始录入人脸信息....")
			self.__username = username
			self.__enable_close_camera_btn()
			
			if os.path.exists(self.__path + r'/dataset') is True:
				if os.path.exists(self.__path + '/dataset/' + str(username)):
					shutil.rmtree(self.__path + '/dataset/' + str(username))
			else:
				os.mkdir(self.__path + r'/dataset')
			os.mkdir(self.__path + '\\dataset\\' + str(username))
			self.__img_num = 0
			self.__open_cam()
			self.__timer_info_collection.timeout.connect(
				self.__face__info_collection_play)
			self.__timer_info_collection.start(25)
		else:
			self.__global_msg = "用户已取消录入人脸信息..."
			self.__show_msg(self.__global_msg, hasWarning = True)
			self.__stop()
	
	def __face__info_collection_play(self):
		if self.__cam.isOpened():
			ret, frame = self.__cam.read()
			gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
			height, width, bytesPerComponent = frame.shape
			bytesPerLine = bytesPerComponent * width
			cv2.cvtColor(frame, cv2.COLOR_BGR2RGB, frame)
			self.faceCascade = cv2.CascadeClassifier(self.__cascadePath)
			faces = self.faceCascade.detectMultiScale(gray,
			                                          scaleFactor = 1.15,
			                                          minNeighbors = 5,
			                                          minSize = (100, 100), )
			for (x, y, w, h) in faces:
				cv2.rectangle(frame, (x - 50, y - 50), (x + w + 50, y + h + 50),
				              (225, 0, 0), 2)
				self.__img_num += 1
				cv2.imwrite(self.__path + r'/dataset/' + str(
					self.__username) + '/' + str(self.__username) + '-' + str(
					self.__img_num) + '.jpg',
				            gray[y - 50:y + h + 50, x - 50:x + w + 50])
			self.__put_image(frame.data, width, height, bytesPerLine)
		
		if self.__img_num >= 25:
			self.__show_msg("人脸信息录入完毕...")
			self.__train()
			self.__timer_info_collection.stop()
			self.__enable_close_camera_btn(False)
			self.__cam.release()
	
	def __put_image(self, data, width, height, bytesPerLine,
	                imgFormat = QImage.Format_RGB888):
		image = QImage(data, width, height, bytesPerLine, imgFormat)
		self.__video_container.setPixmap(QPixmap.fromImage(image))
	
	def __quit_triggered(self, q):
		switcher = {
			'New': q.text,
			'Quit': lambda: sys.exit(1)
		}
		
		return switcher.get(q.text, lambda: "Invalid")()
	
	def __open_cam(self):
		self.__update_logger_info("相机已打开")
		if self.__cam.isOpened() is False:
			self.__cam = cv2.VideoCapture(0)
	
	def __stop_cam(self):
		self.__update_logger_info("相机已停止收集....")
		self.__show_msg(self.__global_msg)
		self.__cam.release()
	
	def __show_dialog(self):
		input_username: QInputDialog = QInputDialog()
		text, ok = input_username.getText(self, "请输入你的姓名....", "请输入你的姓名:")
		if len(text) > 0:
			self.__update_logger_info("用户输入: " + str(text))
		return text, ok
	
	def __train(self):
		from src.main.python.lib import TrainerThread
		self.trainer_thread = TrainerThread(self.__db, self.__cascadePath,
		                                    self.__path)
		self.trainer_thread.start_signal.connect(self.__show_msg)
		self.trainer_thread.finish_signal.connect(self.__show_msg)
		self.trainer_thread.start()
	
	def __stop(self, msg: str = ""):
		self.__enable_close_camera_btn(False)
		self.__timer_info_collection.stop()
		self.__timer_recognizer.stop()
		self.__timer_detector.stop()
		self.timer.stop()
		self.__stop_cam()
	
	def __show_msg(self, msg: str, style: str =
	"font-size:24px;color:green;", hasError = False, hasWarning = False):
		self.__video_container.clear()
		self.__video_container.setText(msg)
		if hasError:
			self.__video_container.setStyleSheet("font-size:24px;color:red;")
		elif hasWarning:
			self.__video_container.setStyleSheet("font-size:24px;color:orange;")
		else:
			self.__video_container.setStyleSheet(style)
		self.__update_logger_info(msg)
	
	def __connect_db(self) -> bool:
		self.__db: QSqlDatabase = QSqlDatabase.addDatabase(
			"QSQLITE")
		self.__db.setDatabaseName('demo.db')
		if not self.__db.open():
			QMessageBox.critical(None, qApp.tr("无法打开数据库"), qApp.tr('无法连接数据库'),
			                     QMessageBox.Cancel)
			self.__show_msg('数据库连接失败....', hasError = True)
		else:
			self.__show_msg('数据库已连接.....')
		self.__query = QtSql.QSqlQuery()
		self.__model = QtSql.QSqlTableModel()
		ok = self.__query.exec_(
			"create table if not exists user_face_info (id integer primary key "
			"autoincrement ,name varchar(20) ,user_id int unique, punched int )")
		if ok:
			self.__db.commit()
	
	def __insert(self, username: str, _id: int) -> bool:
		if not self.__db.open():
			self.__db = QSqlDatabase.addDatabase("QSQLITE")
			self.__db.setDatabaseName('demo.db')
			if not self.__db.open():
				QMessageBox.critical(None, qApp.tr("无法打开数据库"),
				                     qApp.tr('无法连接数据库'),
				                     QMessageBox.Cancel)
			return False
		ok = self.__query.exec_(
			"insert into user_face_info(name,user_id) values ('" + username + "'," + str(
				_id) + ")")
		if ok:
			self.__db.commit()
			return True
		else:
			return False
	
	def __insert2(self, username: str, _id: int):
		self.__query.exec_(
			"insert into user_face_info(name,user_id) values ('" + username + "'," + str(
				_id) + ")")
	
	# def __delete_table(self) -> bool:
	# 	query = self.__query
	# 	if not self.__db.open():
	# 		self.__db = QSqlDatabase.addDatabase("QSQLITE")
	# 		self.__db.setDatabaseName('demo.db')
	# 		if not self.__db.open():
	# 			QMessageBox.critical(None, qApp.tr("无法打开数据库"),
	# 			                     qApp.tr('无法连接数据库'),
	# 			                     QMessageBox.Cancel)
	# 		return False
	# 	query.exec_('delete from user_face_info')
	# 	query.exec_(
	# 		"update sqlite_sequence set seq=0 where name= 'user_face_info'")
	# 	query.exec_("delete from sqlite_sequence where name='user_face_info'")
	# 	if query.exec_('select * from user_face_info'):
	# 		self.__db.commit()
	# 		self.__show_msg('清空数据成功')
	# 	else:
	# 		self.__show_msg('清空数据失败', hasError = True)
	
	def closeEvent(self, *args, **kwargs):
		super().closeEvent(*args, **kwargs)
		self.__db.close()
	
	def __enable_close_camera_btn(self, enabled: bool = True) -> bool:
		if enabled:
			self.__close_camera.setEnabled(True)
			self.__close_camera.setStyleSheet(
				"height:24;background-color:red;color:black")
		else:
			self.__close_camera.setEnabled(False)
			self.__close_camera.setStyleSheet(
				"height:24;background-color:gray;color:black")
	
	def __update_logger_info(self, msg: str):
		"""
		update the logger info
		:param msg:
		:return:
		"""
		list_item: QListWidgetItem = QListWidgetItem()
		list_item.setTextAlignment(Qt.AlignLeft)
		list_item.setText(qApp.tr(msg))
		# list_item.setFont(QFont("Arial", 8, QFont.Bold))
		list_item.setToolTip(msg)
		logging.info(msg)
		self.logger_info_list.addItem(list_item)

def program_init():
	pass

# if __name__ == '__main__':
# 	logging.basicConfig(stream = sys.stdout, level = logging.DEBUG)
# 	appctxt = ApplicationContext()  # 1. Instantiate ApplicationContext
# 	appctxt.app.setStyle('Fusion')
# 	window = Main()
# 	window.show()
# 	# 2. Invoke appctxt.app.exec_()
# 	sys.exit(appctxt.app.exec_())

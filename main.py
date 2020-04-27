import logging
import sys

from fbs_runtime.application_context.PyQt5 import ApplicationContext

from src.main.python.main import Main

if __name__ == '__main__':
	logging.basicConfig(stream = sys.stdout, level = logging.DEBUG)
	appctxt = ApplicationContext()  # 1. Instantiate ApplicationContext
	appctxt.app.setStyle('Fusion')
	window = Main()
	window.show()
	# 2. Invoke appctxt.app.exec_()
	sys.exit(appctxt.app.exec_())

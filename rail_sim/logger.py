import logging
def get_logger():
	logger = logging.getLogger()
	# Clear any existing handlers first to prevent duplication
	if logger.handlers:
		logger.handlers.clear()
	logger.setLevel(logging.DEBUG)
	# File handler
	file_handler = logging.FileHandler('pipeline_log.txt', mode='a')
	file_handler.setLevel(logging.DEBUG)
	# Console handler
	console_handler = logging.StreamHandler()
	console_handler.setLevel(logging.DEBUG)
	# Formatter for both handlers
	formatter = logging.Formatter('%(asctime)s  %(levelname)s  %(message)s')
	file_handler.setFormatter(formatter)
	console_handler.setFormatter(formatter)
	# Add handlers
	logger.addHandler(file_handler)
	logger.addHandler(console_handler)
	return logger
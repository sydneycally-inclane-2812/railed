import logging

_logger_initialized = False

def get_logger():
	global _logger_initialized
	logger = logging.getLogger('rail_sim')
	
	# Only initialize once
	if not _logger_initialized:
		# Clear any existing handlers first to prevent duplication
		if logger.handlers:
			logger.handlers.clear()
		logger.setLevel(logging.DEBUG)
		
		# File handler
		file_handler = logging.FileHandler('pipeline_log.txt', mode='a')
		file_handler.setLevel(logging.DEBUG)
		
		# Console handler
		console_handler = logging.StreamHandler()
		console_handler.setLevel(logging.INFO)  # Less verbose on console by default
		
		# Formatter for both handlers
		formatter = logging.Formatter('%(asctime)s  %(levelname)s  %(message)s')
		file_handler.setFormatter(formatter)
		console_handler.setFormatter(formatter)
		
		# Add handlers
		logger.addHandler(file_handler)
		logger.addHandler(console_handler)
		
		_logger_initialized = True
	
	return logger
import logging

logging.basicConfig(level=logging.INFO)

# handler = logging.StreamHandler()
# handler.setFormatter(logging.Formatter('[CONTROL] {asctime} - {name} - {levelname} - {message}', style='{'))
#
# control_logger = logging.getLogger('control')
# control_logger.addHandler(handler)
# control_logger.setLevel(logging.INFO)
#
# handler = logging.StreamHandler()
# handler.setFormatter(logging.Formatter('[PERFORM] {asctime} - {name} - {levelname} - {message}', style='{'))
#
# perform_logger = logging.getLogger('perform')
# perform_logger.addHandler(handler)
# perform_logger.setLevel(logging.INFO)
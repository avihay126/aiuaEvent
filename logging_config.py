import logging

def setup_logging():
    # Configure the logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(module)s - %(funcName)s - %(message)s',
        handlers=[
            logging.StreamHandler()  # Output logs to console (you can add file handlers too)
        ]
    )

# Initialize the logging setup when the module is imported
setup_logging()
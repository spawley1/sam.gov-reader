import sys
from PyQt5.QtWidgets import QApplication
from gui import MainWindow
from utils import setup_logging, logger

def main():
    # Set up logging
    setup_logging()
    
    logger.info("Starting SAM.gov Contract Filter Application")
    
    # Create the Qt Application
    app = QApplication(sys.argv)
    
    try:
        # Create and show the main window
        main_window = MainWindow()
        main_window.show()
        
        logger.info("Application GUI initialized and displayed")
        
        # Start the event loop
        sys.exit(app.exec_())
    except Exception as e:
        logger.error(f"An error occurred while starting the application: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.info("Application closed")

if __name__ == "__main__":
    main()

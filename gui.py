import csv
import json
import pandas as pd
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLineEdit, QTextEdit, QListWidget, QLabel, 
                             QCheckBox, QProgressBar, QFileDialog, QMessageBox, QComboBox,
                             QDateEdit, QTabWidget, QGroupBox, QTableWidget, QTableWidgetItem,
                             QHeaderView, QAbstractItemView, QMenu, QAction)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QKeySequence
from claude_search import ClaudeSearch
from contract_database import ContractDatabase
from search_worker import SearchWorker
from utils import logger, parse_date, format_currency, sanitize_input

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAM.gov Contract Filter")
        self.setGeometry(100, 100, 1200, 800)

        try:
            self.db = ContractDatabase()
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to initialize database: {e}")
            raise

        self.claude_search = None
        self.current_page = 1
        self.contracts_per_page = 50
        self.total_contracts = 0
        self.current_query = {}

        self.init_ui()

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        # File selection
        file_layout = QHBoxLayout()
        self.file_entry = QLineEdit()
        file_button = QPushButton("Select CSV File")
        file_button.clicked.connect(self.load_csv)
        file_layout.addWidget(self.file_entry)
        file_layout.addWidget(file_button)
        main_layout.addLayout(file_layout)

        # API Key input
        api_key_layout = QHBoxLayout()
        api_key_layout.addWidget(QLabel("Anthropic API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        api_key_layout.addWidget(self.api_key_input)
        api_key_button = QPushButton("Set API Key")
        api_key_button.clicked.connect(self.set_api_key)
        api_key_layout.addWidget(api_key_button)
        main_layout.addLayout(api_key_layout)

        # Search options
        search_layout = QHBoxLayout()
        self.use_claude_checkbox = QCheckBox("Use Claude AI")
        search_layout.addWidget(self.use_claude_checkbox)
        search_button = QPushButton("Search Contracts")
        search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(search_button)
        main_layout.addLayout(search_layout)

        # Tabs for different search options
        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        # Basic Search Tab
        basic_tab = QWidget()
        basic_layout = QVBoxLayout(basic_tab)

        # Keyword search
        keyword_layout = QHBoxLayout()
        keyword_layout.addWidget(QLabel("Keyword:"))
        self.keyword_entry = QLineEdit()
        keyword_layout.addWidget(self.keyword_entry)
        basic_layout.addLayout(keyword_layout)

        # Date range
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("Date Posted Range:"))
        self.date_posted_start = QDateEdit()
        self.date_posted_start.setCalendarPopup(True)
        date_layout.addWidget(self.date_posted_start)
        date_layout.addWidget(QLabel("to"))
        self.date_posted_end = QDateEdit()
        self.date_posted_end.setCalendarPopup(True)
        date_layout.addWidget(self.date_posted_end)
        basic_layout.addLayout(date_layout)

        # Agency selection
        self.agency_list = QListWidget()
        self.agency_list.setSelectionMode(QListWidget.MultiSelection)
        basic_layout.addWidget(QLabel("Select Agencies:"))
        basic_layout.addWidget(self.agency_list)

        tabs.addTab(basic_tab, "Basic Search")

        # Advanced Search Tab
        advanced_tab = QWidget()
        advanced_layout = QVBoxLayout(advanced_tab)

        # NAICS Code
        naics_layout = QHBoxLayout()
        naics_layout.addWidget(QLabel("NAICS Code:"))
        self.naics_entry = QLineEdit()
        naics_layout.addWidget(self.naics_entry)
        advanced_layout.addLayout(naics_layout)

        # PSC Code
        psc_layout = QHBoxLayout()
        psc_layout.addWidget(QLabel("PSC Code:"))
        self.psc_entry = QLineEdit()
        psc_layout.addWidget(self.psc_entry)
        advanced_layout.addLayout(psc_layout)

        # Set-Aside
        setaside_layout = QHBoxLayout()
        setaside_layout.addWidget(QLabel("Set-Aside:"))
        self.setaside_combo = QComboBox()
        setaside_layout.addWidget(self.setaside_combo)
        advanced_layout.addLayout(setaside_layout)

        # Contract Value Range
        value_layout = QHBoxLayout()
        value_layout.addWidget(QLabel("Contract Value Range:"))
        self.contract_value_min = QLineEdit()
        value_layout.addWidget(self.contract_value_min)
        value_layout.addWidget(QLabel("to"))
        self.contract_value_max = QLineEdit()
        value_layout.addWidget(self.contract_value_max)
        advanced_layout.addLayout(value_layout)

        tabs.addTab(advanced_tab, "Advanced Search")

        # Progress bar
        self.progress_bar = QProgressBar()
        main_layout.addWidget(self.progress_bar)

        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(7)
        self.results_table.setHorizontalHeaderLabels(["Notice ID", "Title", "Agency", "Date Posted", "Type", "Set-Aside", "Contract Value"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.results_table.customContextMenuRequested.connect(self.show_context_menu)
        main_layout.addWidget(self.results_table)

        # Pagination
        pagination_layout = QHBoxLayout()
        self.prev_button = QPushButton("Previous")
        self.prev_button.clicked.connect(self.load_previous_page)
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.load_next_page)
        self.page_label = QLabel("Page 1")
        pagination_layout.addWidget(self.prev_button)
        pagination_layout.addWidget(self.page_label)
        pagination_layout.addWidget(self.next_button)
        main_layout.addLayout(pagination_layout)

        # Export options
        export_layout = QHBoxLayout()
        self.export_format = QComboBox()
        self.export_format.addItems(["CSV", "JSON", "Excel"])
        export_layout.addWidget(self.export_format)
        export_button = QPushButton("Export Results")
        export_button.clicked.connect(self.export_results)
        export_layout.addWidget(export_button)
        main_layout.addLayout(export_layout)

        # Keyboard shortcuts
        self.addAction(QAction("Search", self, shortcut=QKeySequence.Find, triggered=self.perform_search))
        self.addAction(QAction("Export", self, shortcut=QKeySequence.Save, triggered=self.export_results))

    def set_api_key(self):
        api_key = self.api_key_input.text().strip()
        if api_key:
            try:
                self.claude_search = ClaudeSearch(api_key)
                QMessageBox.information(self, "Success", "API Key set successfully")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to initialize ClaudeSearch: {e}")
        else:
            QMessageBox.warning(self, "Warning", "Please enter an API key")

     def load_csv(self):
      file_path, _ = QFileDialog.getOpenFileName(self, "Select CSV File", "", "CSV Files (*.csv)")
      if file_path:
          self.file_entry.setText(file_path)
          try:
              # Detect the file encoding
              with open(file_path, 'rb') as rawdata:
                  result = chardet.detect(rawdata.read(10000))
              
              encoding = result['encoding']
            
              contracts = []
              with open(file_path, 'r', newline='', encoding=encoding) as csvfile:
                  reader = csv.DictReader(csvfile)
                  for row in reader:
                      contracts.append(row)
            
              self.db.insert_contracts(contracts)
              self.update_agency_list()
              self.update_setaside_options()
              QMessageBox.information(self, "Info", f"Loaded {len(contracts)} contracts")
              logger.info(f"Successfully loaded {len(contracts)} contracts from {file_path}")
          except Exception as e:
              QMessageBox.critical(self, "Error", f"Failed to load CSV file: {str(e)}")
              logger.error(f"Failed to load CSV file: {str(e)}", exc_info=True)
          
    def update_agency_list(self):
        try:
            agencies = set()
            for contract in self.db.search_contracts({}, limit=1000):
                agencies.add(contract.get('Department/Ind. Agency', ''))
            self.agency_list.clear()
            self.agency_list.addItems(sorted(agencies))
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to update agency list: {e}")
            logger.error(f"Failed to update agency list: {e}", exc_info=True)

    def update_setaside_options(self):
        try:
            setasides = set()
            for contract in self.db.search_contracts({}, limit=1000):
                setasides.add(contract.get('SETASIDE', ''))
            self.setaside_combo.clear()
            self.setaside_combo.addItems([''] + sorted(setasides))
        except Exception as e:
            QMessageBox.warning(self, "Warning", f"Failed to update set-aside options: {e}")
            logger.error(f"Failed to update set-aside options: {e}", exc_info=True)

    def perform_search(self):
        query = self.get_full_query()
        if not query:
            QMessageBox.warning(self, "Warning", "Please enter at least one search criterion")
            return

        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.current_query = query
        self.current_page = 1

        if self.use_claude_checkbox.isChecked():
            self.claude_enhanced_search(query)
        else:
            self.basic_search(query)

    def get_full_query(self):
        query = {}
        if self.keyword_entry.text():
            query['keyword'] = sanitize_input(self.keyword_entry.text())
        if self.date_posted_start.date() != self.date_posted_start.minimumDate():
            query['date_posted_start'] = self.date_posted_start.date().toString(Qt.ISODate)
        if self.date_posted_end.date() != self.date_posted_end.minimumDate():
            query['date_posted_end'] = self.date_posted_end.date().toString(Qt.ISODate)
        if self.agency_list.selectedItems():
            query['agency'] = [sanitize_input(item.text()) for item in self.agency_list.selectedItems()]
        if self.naics_entry.text():
            query['naics_code'] = sanitize_input(self.naics_entry.text())
        if self.psc_entry.text():
            query['psc_code'] = sanitize_input(self.psc_entry.text())
        if self.setaside_combo.currentText():
            query['setaside'] = sanitize_input(self.setaside_combo.currentText())
        if self.contract_value_min.text() or self.contract_value_max.text():
            query['contract_award_value'] = (sanitize_input(self.contract_value_min.text()), 
                                             sanitize_input(self.contract_value_max.text()))
        return query

    def basic_search(self, query):
        try:
            self.total_contracts = self.db.get_total_count(query)
            self.load_page(1)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Search failed: {e}")
            logger.error(f"Search failed: {e}", exc_info=True)
        finally:
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(100)

    def claude_enhanced_search(self, query):
        if not self.claude_search:
            QMessageBox.warning(self, "Warning", "Please set your Anthropic API key first")
            return

        self.search_worker = SearchWorker(self.claude_search, self.db, query)
        self.search_worker.finished.connect(self.on_search_finished)
        self.search_worker.error.connect(self.on_search_error)
        self.search_worker.start()

    def on_search_finished(self, results):
        enhanced_query, analyzed_contracts, summary, entities = results
        self.keyword_entry.setText(enhanced_query)
        self.display_results(analyzed_contracts)
        self.display_entities(entities)
        QMessageBox.information(self, "Claude Summary", summary)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)

    def on_search_error(self, error):
        QMessageBox.critical(self, "Error", f"An error occurred during the search: {error}")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

    def load_page(self, page):
        try:
            offset = (page - 1) * self.contracts_per_page
            contracts = self.db.search_contracts(self.current_query, limit=self.contracts_per_page, offset=offset)
            self.display_results(contracts)
            self.current_page = page
            self.update_pagination()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load page: {e}")
            logger.error(f"Failed to load page: {e}", exc_info=True)

    def display_results(self, contracts):
        self.results_table.setRowCount(len(contracts))
        for row, contract in enumerate(contracts):
            self.results_table.setItem(row, 0, QTableWidgetItem(contract.get('Notice ID', '')))
            self.results_table.setItem(row, 1, QTableWidgetItem(contract.get('Title', '')))
            self.results_table.setItem(row, 2, QTableWidgetItem(contract.get('Department/Ind. Agency', '')))
            self.results_table.setItem(row, 3, QTableWidgetItem(contract.get('Date Posted', '')))
            self.results_table.setItem(row, 4, QTableWidgetItem(contract.get('Type', '')))
            self.results_table.setItem(row, 5, QTableWidgetItem(contract.get('SETASIDE', '')))
            self.results_table.setItem(row, 6, QTableWidgetItem(format_currency(float(contract.get('Contract Award Value', 0)))))

    def update_pagination(self):
        total_pages = (self.total_contracts - 1) // self.contracts_per_page + 1
        self.page_label.setText(f"Page {self.current_page} of {total_pages}")
        self.prev_button.setEnabled(self.current_page > 1)
        self.next_button.setEnabled(self.current_page < total_pages)

    def load_next_page(self):
        if self.current_page * self.contracts_per_page < self.total_contracts:
            self.load_page(self.current_page + 1)

    def load_previous_page(self):
        if self.current_page > 1:
            self.load_page(self.current_page - 1)

    def show_context_menu(self, position):
        menu = QMenu()
        bulk_update_action = menu.addAction("Bulk Update")
        bulk_delete_action = menu.addAction("Bulk Delete")
        
        action = menu.exec_(self.results_table.mapToGlobal(position))
        
        if action == bulk_update_action:
            self.bulk_update()
        elif action == bulk_delete_action:
            self.bulk_delete()

    def bulk_update(self):
        selected_rows = set(index.row() for index in self.results_table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "No contracts selected for update")
            return

        # In a real application, you'd want to show a dialog to let the user choose what to update.
        # For this example, we'll just update a dummy field.
        update_data = {'dummy_field': 'Updated'}
        contract_ids = [self.results_table.item(row, 0).text() for row in selected_rows]
        
        try:
            self.db.bulk_update(contract_ids, update_data)
            QMessageBox.information(self, "Success", f"Updated {len(contract_ids)} contracts")
            self.load_page(self.current_page)  # Reload current page to reflect changes
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to update contracts: {e}")
            logger.error(f"Bulk update failed: {e}", exc_info=True)

    def bulk_delete(self):
        selected_rows = set(index.row() for index in self.results_table.selectedIndexes())
        if not selected_rows:
            QMessageBox.warning(self, "Warning", "No contracts selected for deletion")
            return

        reply = QMessageBox.question(self, "Confirm Deletion", 
                                     f"Are you sure you want to delete {len(selected_rows)} contracts?",
                                     QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            contract_ids = [self.results_table.item(row, 0).text() for row in selected_rows]
            try:
                self.db.bulk_delete(contract_ids)
                QMessageBox.information(self, "Success", f"Deleted {len(contract_ids)} contracts")
                self.load_page(self.current_page)  # Reload current page to reflect changes
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete contracts: {e}")
                logger.error(f"Bulk delete failed: {e}", exc_info=True)

    def export_results(self):
        if self.total_contracts == 0:
            QMessageBox.warning(self, "Warning", "No results to export")
            return

        file_format = self.export_format.currentText()
        file_path, _ = QFileDialog.getSaveFileName(self, "Save File", "", f"{file_format} Files (*.{file_format.lower()})")
        
        if file_path:
            try:
                all_contracts = self.db.search_contracts(self.current_query, limit=self.total_contracts)
                
                if file_format == "CSV":
                    with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                        writer = csv.DictWriter(csvfile, fieldnames=all_contracts[0].keys())
                        writer.writeheader()
                        writer.writerows(all_contracts)
                elif file_format == "JSON":
                    with open(file_path, 'w', encoding='utf-8') as jsonfile:
                        json.dump(all_contracts, jsonfile, indent=2)
                elif file_format == "Excel":
                    df = pd.DataFrame(all_contracts)
                    df.to_excel(file_path, index=False)
                
                QMessageBox.information(self, "Success", f"Exported {len(all_contracts)} contracts to {file_path}")
                logger.info(f"Successfully exported {len(all_contracts)} contracts to {file_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to export results: {e}")
                logger.error(f"Failed to export results: {e}", exc_info=True)

    def display_entities(self, entities):
        entity_text = "Extracted Entities:\n\n"
        for entity_type, entity_list in entities.items():
            entity_text += f"{entity_type}:\n"
            for entity in entity_list:
                entity_text += f"- {entity}\n"
            entity_text += "\n"
        QMessageBox.information(self, "Extracted Entities", entity_text)

    def closeEvent(self, event):
        try:
            self.db.close()
            logger.info("Database connection closed")
        except Exception as e:
            logger.error(f"Error closing database connection: {e}")
        event.accept()

from PyQt5.QtCore import QThread, pyqtSignal
import json
import logging

logger = logging.getLogger(__name__)

class SearchWorker(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)

    def __init__(self, claude_search, db, query):
        super().__init__()
        self.claude_search = claude_search
        self.db = db
        self.query = query

    def run(self):
        try:
            # Convert the query to a string for Claude's enhance_query method
            query_str = json.dumps(self.query)
            
            # Enhance the query using Claude AI
            enhanced_query = self.claude_search.enhance_query(query_str)
            logger.info(f"Enhanced query: {enhanced_query}")

            # Perform the database search with the original query
            contracts = self.db.search_contracts(self.query, limit=100)
            logger.info(f"Found {len(contracts)} contracts in initial search")

            # Convert contracts to JSON for Claude's analysis
            contracts_key = json.dumps(contracts)

            # Perform advanced analysis on the contracts
            analyzed_contracts = self.claude_search.advanced_analyze_contracts(contracts_key, enhanced_query)
            logger.info(f"Analyzed {len(analyzed_contracts)} contracts")

            # Prepare a summary of the top 5 results
            result_key = json.dumps([c for c in analyzed_contracts[:5]])
            summary = self.claude_search.summarize_results(result_key)
            logger.info("Generated summary of top 5 results")

            # Extract entities from the contracts
            entities = self.claude_search.extract_entities(contracts_key)
            logger.info("Extracted entities from contracts")

            # Emit the results
            self.finished.emit((enhanced_query, analyzed_contracts, summary, entities))

        except Exception as e:
            logger.error(f"Error in Claude-enhanced search: {e}", exc_info=True)
            self.error.emit(str(e))

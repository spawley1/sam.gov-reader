import sqlite3
from typing import List, Dict
import json
import logging
from utils import create_search_query, validate_contract_data

logger = logging.getLogger(__name__)

class ContractDatabase:
    def __init__(self, db_path: str = 'contracts.db'):
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path)
        self.create_tables()

    def create_tables(self):
        with self.conn:
            self.conn.execute('''
                CREATE TABLE IF NOT EXISTS contracts (
                    id INTEGER PRIMARY KEY,
                    notice_id TEXT UNIQUE,
                    title TEXT,
                    agency TEXT,
                    sub_tier TEXT,
                    naics_code TEXT,
                    psc_code TEXT,
                    date_posted TEXT,
                    type TEXT,
                    base_period TEXT,
                    option_periods TEXT,
                    delivery_order TEXT,
                    synopsis TEXT,
                    setaside TEXT,
                    response_date TEXT,
                    award_date TEXT,
                    award_number TEXT,
                    contract_award_value REAL,
                    contractor_name TEXT,
                    contract_description TEXT,
                    primary_poc TEXT,
                    secondary_poc TEXT,
                    data JSON
                )
            ''')

    def insert_contracts(self, contracts: List[Dict]):
        valid_contracts = [contract for contract in contracts if validate_contract_data(contract)]
        with self.conn:
            self.conn.executemany('''
                INSERT OR REPLACE INTO contracts (
                    notice_id, title, agency, sub_tier, naics_code, psc_code, date_posted,
                    type, base_period, option_periods, delivery_order, synopsis, setaside,
                    response_date, award_date, award_number, contract_award_value,
                    contractor_name, contract_description, primary_poc, secondary_poc, data
                ) VALUES (
                    :Notice ID, :Title, :Department/Ind. Agency, :Sub-Tier, :NAICS Code,
                    :PSC Code, :Date Posted, :Type, :Base Period, :Option Periods,
                    :Delivery Order/Task Order/BOA Order, :Synopsis, :SETASIDE,
                    :Response Date, :Award Date, :Award Number, :Contract Award Value,
                    :Contractor Name, :Contract Description, :Primary Point of Contact,
                    :Secondary Point of Contact, :data
                )
            ''', [{**contract, 'data': json.dumps(contract)} for contract in valid_contracts])
        logger.info(f"Inserted {len(valid_contracts)} contracts into the database")

    def search_contracts(self, query: Dict, limit: int = 100, offset: int = 0) -> List[Dict]:
        where_clause = create_search_query(query)
        sql = f'''
            SELECT data FROM contracts
            {where_clause}
            LIMIT ? OFFSET ?
        '''
        try:
            with self.conn:
                cursor = self.conn.execute(sql, list(query.values()) + [limit, offset])
                return [json.loads(row[0]) for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logger.error(f"Database error: {e}")
            return []
        except Exception as e:
            logger.error(f"Unexpected error in search_contracts: {e}")
            return []

    def get_total_count(self, query: Dict) -> int:
        where_clause = create_search_query(query)
        sql = f'''
            SELECT COUNT(*) FROM contracts
            {where_clause}
        '''
        try:
            with self.conn:
                cursor = self.conn.execute(sql, list(query.values()))
                return cursor.fetchone()[0]
        except sqlite3.Error as e:
            logger.error(f"Database error in get_total_count: {e}")
            return 0
        except Exception as e:
            logger.error(f"Unexpected error in get_total_count: {e}")
            return 0

    def bulk_update(self, contract_ids: List[str], update_data: Dict):
        set_clause = ", ".join([f"{key} = ?" for key in update_data.keys()])
        sql = f'''
            UPDATE contracts
            SET {set_clause}
            WHERE notice_id IN ({','.join(['?'] * len(contract_ids))})
        '''
        params = list(update_data.values()) + contract_ids
        try:
            with self.conn:
                self.conn.execute(sql, params)
            logger.info(f"Bulk updated {len(contract_ids)} contracts")
        except sqlite3.Error as e:
            logger.error(f"Database error in bulk_update: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in bulk_update: {e}")
            raise

    def bulk_delete(self, contract_ids: List[str]):
        sql = f'''
            DELETE FROM contracts
            WHERE notice_id IN ({','.join(['?'] * len(contract_ids))})
        '''
        try:
            with self.conn:
                self.conn.execute(sql, contract_ids)
            logger.info(f"Bulk deleted {len(contract_ids)} contracts")
        except sqlite3.Error as e:
            logger.error(f"Database error in bulk_delete: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in bulk_delete: {e}")
            raise

    def close(self):
        self.conn.close()
        logger.info("Database connection closed")

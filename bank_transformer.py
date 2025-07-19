"""
Nigerian Bank Statement Standardization Engine - Python Implementation
Designed for M4 MacBook with PyCharm
"""

import pandas as pd
import openpyxl
from pathlib import Path
import re
from datetime import datetime
import logging
from typing import Dict, List, Tuple, Optional, Any
import json


class BankStatementTransformer:
    def __init__(self):
        self.standard_headers = [
            'Tran Date', 'Value Date', 'Ref. No', 'Transaction Details',
            'Debit', 'Credit', 'Balance'
        ]

        self.bank_formats = self._initialize_bank_formats()
        self.date_patterns = [
            r'^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4}$',  # DD/MM/YYYY or DD-MM-YYYY
            r'^\d{4}[\/\-]\d{1,2}[\/\-]\d{1,2}$',  # YYYY/MM/DD or YYYY-MM-DD
            r'^\d{1,2}[\/\-]\d{1,2}[\/\-]\d{2}$'  # DD/MM/YY or DD-MM-YY
        ]

        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def _initialize_bank_formats(self) -> Dict:
        return {
            'FCMB_FORMAT_1': {
                'name': 'FCMB Statement Format 1',
                'identifiers': ['1021040520', 'STATEMENT OF ACCOUNT'],
                'header_row': 16,
                'account_info_rows': [3, 4, 5, 6, 7, 8, 12, 13, 14],
                'mapping': {
                    'Transaction Date': 'Tran Date',
                    'Description': 'Transaction Details',
                    'Value Date': 'Value Date',
                    'Withdrawls': 'Debit',
                    'Deposits': 'Credit',
                    'Balance': 'Balance',
                    'Instrument Code': 'Ref. No'
                }
            },
            'GTB_ODS_FORMAT': {
                'name': 'GTB ODS Statement Format',
                'identifiers': ['TRA DATE', 'REMARKS', 'NUBAN'],
                'header_row': 2,
                'account_info_rows': [0, 1],
                'mapping': {
                    'TRA DATE': 'Tran Date',
                    'REMARKS': 'Transaction Details',
                    'NUBAN': 'Ref. No',
                    'DEBIT': 'Debit',
                    'CREDIT': 'Credit',
                    'CRNT BAL': 'Balance'
                }
            },
            'GENERIC': {
                'name': 'Generic Bank Format',
                'identifiers': [],
                'header_row': 'auto-detect',
                'mapping': {}
            }
        }

    def transform_statement(self, file_path: str, options: Dict = None) -> Dict:
        """Main transformation function"""
        if options is None:
            options = {}

        try:
            self.logger.info(f"Processing file: {file_path}")

            # Read the file
            df, raw_data = self._read_file(file_path)

            # Detect format
            format_info = self._detect_format(raw_data, file_path)

            # Extract account information
            account_info = self._extract_account_info(raw_data, format_info)

            # Extract and standardize transactions
            transactions = self._extract_transactions(raw_data, format_info)
            standardized_transactions = self._standardize_transactions(
                transactions, format_info, options
            )

            result = {
                'success': True,
                'account_info': account_info,
                'transactions': standardized_transactions,
                'original_format': format_info['name'],
                'records_processed': len(standardized_transactions),
                'metadata': {
                    'file_name': Path(file_path).name,
                    'processed_at': datetime.now().isoformat(),
                    'standard_headers': self.standard_headers
                }
            }

            self.logger.info(f"Successfully processed {len(standardized_transactions)} transactions")
            return result

        except Exception as e:
            self.logger.error(f"Error processing {file_path}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'file_name': Path(file_path).name
            }

    def _read_file(self, file_path: str) -> Tuple[pd.DataFrame, List[List]]:
        """Read file and return both DataFrame and raw data"""
        file_path = Path(file_path)

        if file_path.suffix.lower() in ['.xlsx', '.xls']:
            # Read with openpyxl to preserve formatting
            workbook = openpyxl.load_workbook(file_path, data_only=True)
            worksheet = workbook.active

            # Convert to list of lists (raw data)
            raw_data = []
            for row in worksheet.iter_rows(values_only=True):
                raw_data.append(list(row))

            # Also create DataFrame
            df = pd.read_excel(file_path, header=None)

        elif file_path.suffix.lower() == '.ods':
            # For ODS files, use pandas
            df = pd.read_excel(file_path, engine='odf', header=None)
            raw_data = df.values.tolist()

        else:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        return df, raw_data

    def _detect_format(self, raw_data: List[List], file_path: str) -> Dict:
        """Detect bank format based on content analysis"""

        # Convert first 20 rows to searchable text
        search_text = ' '.join([
            str(cell) for row in raw_data[:20]
            for cell in row if cell is not None
        ]).lower()

        # Check each format's identifiers
        for format_key, format_info in self.bank_formats.items():
            if format_key == 'GENERIC':
                continue

            identifiers_found = all(
                identifier.lower() in search_text
                for identifier in format_info['identifiers']
            )

            if identifiers_found:
                self.logger.info(f"Detected format: {format_info['name']}")
                return {**format_info, 'key': format_key}

        # Fallback to generic detection
        self.logger.info("Using generic format detection")
        return self._detect_generic_format(raw_data)

    def _detect_generic_format(self, raw_data: List[List]) -> Dict:
        """Generic format detection for unknown banks"""
        common_headers = [
            'date', 'transaction', 'description', 'narration', 'remarks',
            'debit', 'credit', 'withdrawal', 'deposit', 'balance', 'amount'
        ]

        header_row = -1
        mapping = {}

        # Search for header row
        for i, row in enumerate(raw_data[:25]):
            if not row:
                continue

            header_count = sum(1 for cell in row if cell and isinstance(cell, str) and
                               any(header in str(cell).lower() for header in common_headers))

            if header_count >= 4:  # At least 4 financial headers found
                header_row = i

                # Create mapping
                for j, cell in enumerate(row):
                    if cell and isinstance(cell, str):
                        cell_lower = str(cell).lower()

                        if 'date' in cell_lower and 'value' not in cell_lower:
                            mapping[cell] = 'Tran Date'
                        elif 'value' in cell_lower and 'date' in cell_lower:
                            mapping[cell] = 'Value Date'
                        elif any(word in cell_lower for word in ['description', 'narration', 'remarks']):
                            mapping[cell] = 'Transaction Details'
                        elif any(word in cell_lower for word in ['debit', 'withdrawal']):
                            mapping[cell] = 'Debit'
                        elif any(word in cell_lower for word in ['credit', 'deposit']):
                            mapping[cell] = 'Credit'
                        elif 'balance' in cell_lower:
                            mapping[cell] = 'Balance'
                        elif any(word in cell_lower for word in ['reference', 'ref']):
                            mapping[cell] = 'Ref. No'
                break

        return {
            'key': 'GENERIC',
            'name': 'Generic Bank Format',
            'header_row': header_row,
            'mapping': mapping,
            'account_info_rows': list(range(5))  # First few rows
        }

    def _extract_account_info(self, raw_data: List[List], format_info: Dict) -> Dict:
        """Extract account information from raw data"""
        account_info = {}

        if 'account_info_rows' in format_info:
            for row_index in format_info['account_info_rows']:
                if row_index < len(raw_data) and raw_data[row_index]:
                    row = raw_data[row_index]
                    row_text = ' '.join(str(cell) for cell in row if cell is not None)

                    # Extract account number (10+ digits)
                    account_match = re.search(r'(\d{10,})', row_text)
                    if account_match and 'account_number' not in account_info:
                        account_info['account_number'] = account_match.group(1)

                    # Extract account name (uppercase letters and spaces)
                    name_pattern = r'\b[A-Z][A-Z\s]{10,}\b'
                    name_match = re.search(name_pattern, row_text)
                    if name_match and 'account_name' not in account_info:
                        potential_name = name_match.group(0).strip()
                        if 'ACCOUNT' not in potential_name:
                            account_info['account_name'] = potential_name

                    # Extract balances
                    for i, cell in enumerate(row):
                        if isinstance(cell, str):
                            if 'opening balance' in cell.lower() and i + 1 < len(row):
                                account_info['opening_balance'] = self._parse_amount(row[i + 1])
                            elif 'closing balance' in cell.lower() and i + 1 < len(row):
                                account_info['closing_balance'] = self._parse_amount(row[i + 1])

        return account_info

    def _extract_transactions(self, raw_data: List[List], format_info: Dict) -> List[Dict]:
        """Extract transaction data from raw data"""
        if format_info['header_row'] == -1:
            raise ValueError('Unable to locate transaction header row')

        header_row_index = format_info['header_row']
        headers = raw_data[header_row_index]
        transactions = []

        for i in range(header_row_index + 1, len(raw_data)):
            row = raw_data[i]
            if not row or not any(cell for cell in row if cell is not None):
                continue

            # Check if this looks like a transaction row
            has_date_or_amount = any(
                self._is_date(cell) or self._is_amount(cell)
                for cell in row if cell is not None
            )

            if has_date_or_amount:
                transaction = {}
                for j, header in enumerate(headers):
                    if header and j < len(row) and row[j] is not None:
                        transaction[str(header)] = row[j]

                if transaction:  # Only add non-empty transactions
                    transactions.append(transaction)

        return transactions

    def _standardize_transactions(self, transactions: List[Dict], format_info: Dict, options: Dict) -> List[Dict]:
        """Standardize transactions to unified format"""
        standardized = []

        for transaction in transactions:
            standard_transaction = {}

            # Apply mapping from format configuration
            for original, standard in format_info['mapping'].items():
                if original in transaction and transaction[original] is not None:
                    value = transaction[original]

                    # Special processing based on column type
                    if 'Date' in standard:
                        value = self._standardize_date(value, options.get('date_format', 'DD/MM/YYYY'))
                    elif standard in ['Debit', 'Credit', 'Balance']:
                        value = self._standardize_amount(value)

                    standard_transaction[standard] = value

            # Ensure all standard columns exist
            for header in self.standard_headers:
                if header not in standard_transaction:
                    standard_transaction[header] = ''

            # Handle debit/credit logic
            self._handle_debit_credit_logic(standard_transaction, transaction)

            standardized.append(standard_transaction)

        return standardized

    def _handle_debit_credit_logic(self, standardized: Dict, original: Dict):
        """Handle debit/credit logic for different formats"""
        # If amounts are in a single column with +/- signs
        if 'Amount' in original and not standardized.get('Debit') and not standardized.get('Credit'):
            amount = self._parse_amount(original['Amount'])
            if amount < 0:
                standardized['Debit'] = f"{abs(amount):.2f}"
                standardized['Credit'] = ''
            else:
                standardized['Credit'] = f"{amount:.2f}"
                standardized['Debit'] = ''

        # Ensure proper formatting
        if standardized.get('Debit') and not standardized.get('Credit'):
            standardized['Credit'] = ''
        if standardized.get('Credit') and not standardized.get('Debit'):
            standardized['Debit'] = ''

    def _standardize_date(self, date_value, target_format: str = 'DD/MM/YYYY') -> str:
        """Standardize date format"""
        if not date_value:
            return ''

        try:
            # Handle Excel serial dates
            if isinstance(date_value, (int, float)) and date_value > 1000:
                # Excel date serial number (days since 1900-01-01)
                excel_epoch = datetime(1900, 1, 1)
                date_obj = excel_epoch + pd.Timedelta(days=date_value - 2)  # Excel has a leap year bug
            elif isinstance(date_value, str):
                # Try to parse string dates
                date_obj = pd.to_datetime(date_value, errors='coerce')
            elif isinstance(date_value, datetime):
                date_obj = date_value
            else:
                return str(date_value)

            if pd.isna(date_obj):
                return str(date_value)

            # Format according to target format
            if target_format == 'DD/MM/YYYY':
                return date_obj.strftime('%d/%m/%Y')
            elif target_format == 'MM/DD/YYYY':
                return date_obj.strftime('%m/%d/%Y')
            elif target_format == 'YYYY-MM-DD':
                return date_obj.strftime('%Y-%m-%d')
            else:
                return date_obj.strftime('%d/%m/%Y')

        except Exception:
            return str(date_value)

    def _standardize_amount(self, amount) -> str:
        """Standardize amount format"""
        if amount == '' or amount is None:
            return ''

        parsed = self._parse_amount(amount)
        return f"{parsed:.2f}" if parsed is not None else ''

    def _parse_amount(self, value) -> Optional[float]:
        """Parse amount from various formats"""
        if isinstance(value, (int, float)):
            return float(value)

        if not isinstance(value, str):
            return 0.0

        # Remove common formatting
        cleaned = re.sub(r'[₦$£€,\s()]', '', str(value))

        try:
            return float(cleaned)
        except ValueError:
            return 0.0

    def _is_date(self, value) -> bool:
        """Check if value appears to be a date"""
        if isinstance(value, (int, float)) and 1000 < value < 100000:
            return True  # Likely Excel serial date

        if isinstance(value, str):
            return any(re.match(pattern, value) for pattern in self.date_patterns)

        return isinstance(value, datetime)

    def _is_amount(self, value) -> bool:
        """Check if value appears to be an amount"""
        if isinstance(value, (int, float)):
            return value != 0

        if isinstance(value, str):
            cleaned = re.sub(r'[₦$£€,\s()]', '', value)
            try:
                return float(cleaned) != 0
            except ValueError:
                return False

        return False

    def generate_standardized_file(self, transformed_data: Dict, output_path: str, options: Dict = None):
        """Generate standardized Excel file"""
        if options is None:
            options = {}

        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Create transactions sheet
            transactions_df = pd.DataFrame(transformed_data['transactions'])
            transactions_df = transactions_df[self.standard_headers]  # Ensure correct column order
            transactions_df.to_excel(writer, sheet_name='Transactions', index=False)

            # Create metadata sheet if requested
            if options.get('include_metadata', True) and transformed_data.get('account_info'):
                metadata = [
                    ['Account Information', ''],
                    ['Account Number', transformed_data['account_info'].get('account_number', '')],
                    ['Account Name', transformed_data['account_info'].get('account_name', '')],
                    ['Opening Balance', transformed_data['account_info'].get('opening_balance', '')],
                    ['Closing Balance', transformed_data['account_info'].get('closing_balance', '')],
                    ['', ''],
                    ['Processing Information', ''],
                    ['Original Format', transformed_data['original_format']],
                    ['Records Processed', transformed_data['records_processed']],
                    ['Processed At', transformed_data['metadata']['processed_at']]
                ]

                metadata_df = pd.DataFrame(metadata, columns=['Field', 'Value'])
                metadata_df.to_excel(writer, sheet_name='Metadata', index=False)

        self.logger.info(f"Standardized file saved to: {output_path}")


# Example usage
if __name__ == "__main__":
    # Initialize transformer
    transformer = BankStatementTransformer()

    # Example: Process a single file
    file_path = "path/to/your/statement.xlsx"

    try:
        result = transformer.transform_statement(file_path, {
            'date_format': 'DD/MM/YYYY',
            'include_metadata': True
        })

        if result['success']:
            print(f"✅ Processed {result['records_processed']} transactions")
            print(f"Account: {result['account_info']}")

            # Generate standardized file
            output_path = f"standardized_{Path(file_path).stem}.xlsx"
            transformer.generate_standardized_file(result, output_path)
            print(f"📄 Standardized file saved: {output_path}")

        else:
            print(f"❌ Processing failed: {result['error']}")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
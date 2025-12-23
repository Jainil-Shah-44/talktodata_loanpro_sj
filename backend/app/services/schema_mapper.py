from sqlalchemy import inspect
from app.models.models import LoanRecord
from app.core.database import engine
from typing import List, Dict, Any

class SchemaMapper:
    """Service to map database schema for LLM prompts."""
    
    def __init__(self):
        # State code to full name mapping
        self.state_mapping = {
            'AP': 'Andhra Pradesh',
            'AR': 'Arunachal Pradesh',
            'AS': 'Assam',
            'BR': 'Bihar',
            'CG': 'Chhattisgarh',
            'GA': 'Goa',
            'GJ': 'Gujarat',
            'HR': 'Haryana',
            'HP': 'Himachal Pradesh',
            'JH': 'Jharkhand',
            'KA': 'Karnataka',
            'KL': 'Kerala',
            'MP': 'Madhya Pradesh',
            'MH': 'Maharashtra',
            'MN': 'Manipur',
            'ML': 'Meghalaya',
            'MZ': 'Mizoram',
            'NL': 'Nagaland',
            'OD': 'Odisha',
            'PB': 'Punjab',
            'RJ': 'Rajasthan',
            'SK': 'Sikkim',
            'TN': 'Tamil Nadu',
            'TS': 'Telangana',
            'TR': 'Tripura',
            'UK': 'Uttarakhand',
            'UP': 'Uttar Pradesh',
            'WB': 'West Bengal',
            'DL': 'Delhi',
            'JK': 'Jammu and Kashmir',
            'LA': 'Ladakh',
            'AN': 'Andaman and Nicobar Islands',
            'CH': 'Chandigarh',
            'DN': 'Dadra and Nagar Haveli and Daman and Diu',
            'LD': 'Lakshadweep',
            'PY': 'Puducherry'
        }

    @staticmethod
    def get_loan_record_schema() -> List[Dict[str, Any]]:
        """
        Get the schema of the LoanRecord model in a format suitable for the LLM.
        
        Returns:
            List of dictionaries containing column information
        """
        inspector = inspect(engine)
        columns = inspector.get_columns('loan_records')
        
        schema_info = []
        for column in columns:
            schema_info.append({
                "name": column['name'],
                "type": str(column['type']),
                "nullable": column['nullable']
            })
        
        # Add descriptions for important fields
        field_descriptions = {
            "agreement_no": "Unique loan agreement number",
            "loan_id": "Unique identifier for the loan",
            "principal_os_amt": "Principal outstanding amount in rupees",
            "interest_overdue_amt": "Interest overdue amount in rupees",
            "total_balance_amt": "Total balance amount (principal + interest)",
            "dpd_as_on_31st_jan_2025": "Days past due as of Jan 31, 2025",
            "dpd": "Days past due (generic field)",
            "classification": "Loan classification category",
            "product_type": "Type of loan product",
            "status": "Current status of the loan",
            "customer_name": "Name of the customer",
            "state": "State where the loan was issued",
            "first_disb_date": "First disbursement date",
            "sanction_date": "Date when the loan was sanctioned",
            "date_of_npa": "Date when the loan became NPA (Non-Performing Asset)",
            "date_of_woff": "Date when the loan was written off",
            "m3_collection": "Collection amount in the first 3 months",
            "m6_collection": "Collection amount in the first 6 months",
            "m12_collection": "Collection amount in the first 12 months",
            "total_collection": "Total collection amount",
            "post_npa_collection": "Collection amount after NPA",
            "post_woff_collection": "Collection amount after write-off",
            "disbursement_amount": "Amount disbursed to the customer",
            "has_validation_errors": "Whether the loan record has validation errors",
            "validation_error_types": "Types of validation errors for this loan"
        }
        
        for item in schema_info:
            if item["name"] in field_descriptions:
                item["description"] = field_descriptions[item["name"]]
        
        return schema_info
    
    def get_schema_description(self) -> str:
        """Get a description of the loan record schema for LLM prompts."""
        schema = self.get_loan_record_schema()
        
        # Format the schema for LLM prompt
        schema_description = "Table: loan_records\n"
        schema_description += "Columns:\n"
        
        for field in schema:
            field_name = field["name"]
            field_type = field["type"]
            field_description = field.get("description", "")
            
            if field_description:
                schema_description += f"- {field_name} ({field_type}): {field_description}\n"
            else:
                schema_description += f"- {field_name} ({field_type})\n"
        
        # Add state code mapping information
        schema_description += "\nState codes and their full names:\n"
        for code, name in self.state_mapping.items():
            schema_description += f"- {code}: {name}\n"
        
        return schema_description
    
    @staticmethod
    def format_schema_for_prompt(schema_info: List[Dict[str, Any]]) -> str:
        """
        Format the schema information for inclusion in the LLM prompt.
        
        Args:
            schema_info: List of dictionaries containing column information
            
        Returns:
            Formatted schema string
        """
        formatted = "Table: loan_records\nColumns:\n"
        for col in schema_info:
            desc = col.get("description", "")
            formatted += f"- {col['name']} ({col['type']}): {desc}\n"
        
        # Add some example queries to help the LLM
        formatted += "\nExample queries:\n"
        formatted += "1. To get total POS by state: SELECT state, SUM(principal_os_amt) as total_pos FROM loan_records WHERE dataset_id = '{dataset_id}' GROUP BY state ORDER BY total_pos DESC\n"
        formatted += "2. To get count of loans by DPD bucket: SELECT CASE WHEN dpd_as_on_31st_jan_2025 <= 30 THEN '0-30' WHEN dpd_as_on_31st_jan_2025 <= 60 THEN '31-60' WHEN dpd_as_on_31st_jan_2025 <= 90 THEN '61-90' ELSE '90+' END as dpd_bucket, COUNT(*) as loan_count FROM loan_records WHERE dataset_id = '{dataset_id}' GROUP BY dpd_bucket ORDER BY dpd_bucket\n"
        formatted += "3. To get collection efficiency: SELECT SUM(total_collection) / SUM(principal_os_amt) * 100 as collection_efficiency FROM loan_records WHERE dataset_id = '{dataset_id}'\n"
        
        return formatted
    
    @staticmethod
    def get_dataset_statistics(dataset_id: str) -> Dict[str, Any]:
        """
        Get basic statistics about a dataset to provide context to the LLM.
        
        Args:
            dataset_id: The ID of the dataset
            
        Returns:
            Dictionary of dataset statistics
        """
        from sqlalchemy.sql import func
        from app.models.models import LoanRecord
        from app.core.database import SessionLocal
        
        db = SessionLocal()
        try:
            # Get total number of records
            total_records = db.query(func.count(LoanRecord.id)).filter(
                LoanRecord.dataset_id == dataset_id
            ).scalar() or 0
            
            # Get total POS
            total_pos = db.query(func.sum(LoanRecord.principal_os_amt)).filter(
                LoanRecord.dataset_id == dataset_id
            ).scalar() or 0
            
            # Get average DPD
            avg_dpd = db.query(func.avg(LoanRecord.dpd_as_on_31st_jan_2025)).filter(
                LoanRecord.dataset_id == dataset_id
            ).scalar() or 0
            
            # Get total collection
            total_collection = db.query(func.sum(LoanRecord.total_collection)).filter(
                LoanRecord.dataset_id == dataset_id
            ).scalar() or 0
            
            # Get count of records with validation errors
            error_count = db.query(func.count(LoanRecord.id)).filter(
                LoanRecord.dataset_id == dataset_id,
                LoanRecord.has_validation_errors == True
            ).scalar() or 0
            
            return {
                "total_records": total_records,
                "total_pos": float(total_pos) if total_pos else 0,
                "avg_dpd": float(avg_dpd) if avg_dpd else 0,
                "total_collection": float(total_collection) if total_collection else 0,
                "error_count": error_count,
                "error_percentage": (error_count / total_records * 100) if total_records > 0 else 0
            }
        finally:
            db.close()

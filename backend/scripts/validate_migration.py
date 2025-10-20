#!/usr/bin/env python3
"""
Data Migration Validation Script

This script validates the completeness and integrity of data migrated
from MongoDB (Node.js) to PostgreSQL (FastAPI).

Usage:
    python validate_migration.py [--detailed] [--output-report=report.json]
"""

import argparse
import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.append(str(Path(__file__).parent.parent))

import pymongo
from sqlalchemy import create_engine, text, func
from sqlalchemy.orm import sessionmaker

from app.core.config import get_settings
from app.models.user import User
from app.models.subscription import Subscription
from app.models.translation import Translation
from app.models.payment import PaymentOrder
from app.models.usage import UsageRecord

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('validation.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationStats:
    """Validation statistics"""
    total_users_mongo: int = 0
    total_users_pg: int = 0
    users_matched: int = 0
    users_missing_pg: int = 0
    users_missing_mongo: int = 0
    
    total_subscriptions_mongo: int = 0
    total_subscriptions_pg: int = 0
    subscriptions_matched: int = 0
    subscriptions_missing_pg: int = 0
    subscriptions_missing_mongo: int = 0
    
    total_translations_mongo: int = 0
    total_translations_pg: int = 0
    translations_matched: int = 0
    translations_missing_pg: int = 0
    translations_missing_mongo: int = 0
    
    total_payments_mongo: int = 0
    total_payments_pg: int = 0
    payments_matched: int = 0
    payments_missing_pg: int = 0
    payments_missing_mongo: int = 0
    
    data_integrity_issues: List[Dict] = None
    validation_errors: List[str] = None
    
    def __post_init__(self):
        if self.data_integrity_issues is None:
            self.data_integrity_issues = []
        if self.validation_errors is None:
            self.validation_errors = []

@dataclass
class DataIntegrityIssue:
    """Data integrity issue"""
    table_name: str
    record_id: str
    issue_type: str
    description: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    recommendation: str

class MigrationValidator:
    """Data migration validation"""
    
    def __init__(self, detailed: bool = False):
        self.detailed = detailed
        self.settings = get_settings()
        self.stats = ValidationStats()
        
        # Database connections
        self.mongo_client = None
        self.mongo_db = None
        self.postgres_engine = None
        self.postgres_session = None
        
    async def connect(self):
        """Establish database connections"""
        try:
            # Connect to MongoDB
            mongo_uri = getattr(self.settings, 'MONGODB_URI', 'mongodb://localhost:27017')
            self.mongo_client = pymongo.MongoClient(mongo_uri)
            self.mongo_db = self.mongo_client.media_translator
            logger.info("✅ Connected to MongoDB")
            
            # Connect to PostgreSQL
            postgres_uri = self.settings.DATABASE_URL
            self.postgres_engine = create_engine(postgres_uri)
            SessionLocal = sessionmaker(bind=self.postgres_engine)
            self.postgres_session = SessionLocal()
            logger.info("✅ Connected to PostgreSQL")
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close database connections"""
        if self.mongo_client:
            self.mongo_client.close()
        if self.postgres_session:
            self.postgres_session.close()
    
    async def validate_all(self) -> ValidationStats:
        """Execute complete validation"""
        logger.info("🔍 Starting migration validation...")
        
        try:
            await self.validate_users()
            await self.validate_subscriptions()
            await self.validate_translations()
            await self.validate_payment_orders()
            await self.validate_data_integrity()
            await self.validate_foreign_keys()
            await self.validate_data_consistency()
            
        except Exception as e:
            logger.error(f"❌ Validation failed: {e}")
            self.stats.validation_errors.append(str(e))
        
        return self.stats
    
    async def validate_users(self):
        """Validate user data migration"""
        logger.info("👥 Validating users...")
        
        try:
            # Get counts
            mongo_users = list(self.mongo_db.users.find({}))
            pg_users = self.postgres_session.query(User).all()
            
            self.stats.total_users_mongo = len(mongo_users)
            self.stats.total_users_pg = len(pg_users)
            
            # Create lookup maps
            mongo_openids = {user.get('openid') for user in mongo_users if user.get('openid')}
            pg_openids = {user.openid for user in pg_users}
            
            # Find matches and differences
            matched_openids = mongo_openids.intersection(pg_openids)
            missing_pg_openids = mongo_openids - pg_openids
            missing_mongo_openids = pg_openids - mongo_openids
            
            self.stats.users_matched = len(matched_openids)
            self.stats.users_missing_pg = len(missing_pg_openids)
            self.stats.users_missing_mongo = len(missing_mongo_openids)
            
            logger.info(f"MongoDB users: {self.stats.total_users_mongo}")
            logger.info(f"PostgreSQL users: {self.stats.total_users_pg}")
            logger.info(f"Matched: {self.stats.users_matched}")
            logger.info(f"Missing in PostgreSQL: {self.stats.users_missing_pg}")
            logger.info(f"Extra in PostgreSQL: {self.stats.users_missing_mongo}")
            
            # Detailed validation if requested
            if self.detailed:
                await self.validate_user_details(mongo_users, pg_users, matched_openids)
            
            # Check for critical issues
            if self.stats.users_missing_pg > 0:
                self.stats.data_integrity_issues.append(DataIntegrityIssue(
                    table_name="users",
                    record_id="multiple",
                    issue_type="missing_records",
                    description=f"{self.stats.users_missing_pg} users missing in PostgreSQL",
                    severity="critical",
                    recommendation="Re-run migration for missing users"
                ))
        
        except Exception as e:
            logger.error(f"❌ User validation failed: {e}")
            self.stats.validation_errors.append(f"User validation: {e}")
    
    async def validate_user_details(self, mongo_users: List[Dict], pg_users: List[User], matched_openids: set):
        """Detailed validation of user data"""
        logger.info("🔬 Performing detailed user validation...")
        
        # Create lookup dictionaries
        mongo_user_map = {user.get('openid'): user for user in mongo_users if user.get('openid')}
        pg_user_map = {user.openid: user for user in pg_users}
        
        for openid in matched_openids:
            mongo_user = mongo_user_map[openid]
            pg_user = pg_user_map[openid]
            
            # Validate critical fields
            if mongo_user.get('subscriptionLevel') != pg_user.subscription_level:
                self.stats.data_integrity_issues.append(DataIntegrityIssue(
                    table_name="users",
                    record_id=openid,
                    issue_type="data_mismatch",
                    description=f"Subscription level mismatch: MongoDB={mongo_user.get('subscriptionLevel')}, PG={pg_user.subscription_level}",
                    severity="medium",
                    recommendation="Update subscription level in PostgreSQL"
                ))
            
            if mongo_user.get('quotaLimit') != pg_user.quota_limit:
                self.stats.data_integrity_issues.append(DataIntegrityIssue(
                    table_name="users",
                    record_id=openid,
                    issue_type="data_mismatch",
                    description=f"Quota limit mismatch: MongoDB={mongo_user.get('quotaLimit')}, PG={pg_user.quota_limit}",
                    severity="medium",
                    recommendation="Update quota limit in PostgreSQL"
                ))
            
            # Validate dates
            mongo_created = mongo_user.get('createdAt')
            pg_created = pg_user.created_at
            if mongo_created and pg_created:
                mongo_dt = self.parse_datetime(mongo_created)
                if abs((mongo_dt - pg_created).total_seconds()) > 300:  # 5 minutes tolerance
                    self.stats.data_integrity_issues.append(DataIntegrityIssue(
                        table_name="users",
                        record_id=openid,
                        issue_type="data_mismatch",
                        description=f"Created date mismatch: MongoDB={mongo_dt}, PG={pg_created}",
                        severity="low",
                        recommendation="Review date migration logic"
                    ))
    
    async def validate_subscriptions(self):
        """Validate subscription data migration"""
        logger.info("💳 Validating subscriptions...")
        
        try:
            mongo_subscriptions = list(self.mongo_db.subscriptions.find({}))
            pg_subscriptions = self.postgres_session.query(Subscription).all()
            
            self.stats.total_subscriptions_mongo = len(mongo_subscriptions)
            self.stats.total_subscriptions_pg = len(pg_subscriptions)
            
            # Note: This is simplified validation as subscriptions are linked by user_id
            # A more detailed validation would match by user and date ranges
            
            logger.info(f"MongoDB subscriptions: {self.stats.total_subscriptions_mongo}")
            logger.info(f"PostgreSQL subscriptions: {self.stats.total_subscriptions_pg}")
            
            # Basic consistency check
            ratio = self.stats.total_subscriptions_pg / max(self.stats.total_users_pg, 1)
            mongo_ratio = self.stats.total_subscriptions_mongo / max(self.stats.total_users_mongo, 1)
            
            if abs(ratio - mongo_ratio) > 0.1:  # 10% tolerance
                self.stats.data_integrity_issues.append(DataIntegrityIssue(
                    table_name="subscriptions",
                    record_id="ratio_check",
                    issue_type="inconsistency",
                    description=f"Subscription/user ratio mismatch: MongoDB={mongo_ratio:.2f}, PG={ratio:.2f}",
                    severity="medium",
                    recommendation="Review subscription migration logic"
                ))
        
        except Exception as e:
            logger.error(f"❌ Subscription validation failed: {e}")
            self.stats.validation_errors.append(f"Subscription validation: {e}")
    
    async def validate_translations(self):
        """Validate translation data migration"""
        logger.info("🔤 Validating translations...")
        
        try:
            mongo_translations = list(self.mongo_db.translations.find({}))
            pg_translations = self.postgres_session.query(Translation).all()
            
            self.stats.total_translations_mongo = len(mongo_translations)
            self.stats.total_translations_pg = len(pg_translations)
            
            # Check by task_id where possible
            mongo_task_ids = {trans.get('taskId') or str(trans.get('_id')) for trans in mongo_translations}
            pg_task_ids = {trans.task_id for trans in pg_translations}
            
            matched_task_ids = mongo_task_ids.intersection(pg_task_ids)
            missing_pg_task_ids = mongo_task_ids - pg_task_ids
            missing_mongo_task_ids = pg_task_ids - mongo_task_ids
            
            self.stats.translations_matched = len(matched_task_ids)
            self.stats.translations_missing_pg = len(missing_pg_task_ids)
            self.stats.translations_missing_mongo = len(missing_mongo_task_ids)
            
            logger.info(f"MongoDB translations: {self.stats.total_translations_mongo}")
            logger.info(f"PostgreSQL translations: {self.stats.total_translations_pg}")
            logger.info(f"Matched: {self.stats.translations_matched}")
            logger.info(f"Missing in PostgreSQL: {self.stats.translations_missing_pg}")
            logger.info(f"Extra in PostgreSQL: {self.stats.translations_missing_mongo}")
            
            # Check for critical issues
            if self.stats.translations_missing_pg > 0:
                self.stats.data_integrity_issues.append(DataIntegrityIssue(
                    table_name="translations",
                    record_id="multiple",
                    issue_type="missing_records",
                    description=f"{self.stats.translations_missing_pg} translations missing in PostgreSQL",
                    severity="critical",
                    recommendation="Re-run migration for missing translations"
                ))
        
        except Exception as e:
            logger.error(f"❌ Translation validation failed: {e}")
            self.stats.validation_errors.append(f"Translation validation: {e}")
    
    async def validate_payment_orders(self):
        """Validate payment order data migration"""
        logger.info("💰 Validating payment orders...")
        
        try:
            mongo_payments = list(self.mongo_db.payment_orders.find({}))
            pg_payments = self.postgres_session.query(PaymentOrder).all()
            
            self.stats.total_payments_mongo = len(mongo_payments)
            self.stats.total_payments_pg = len(pg_payments)
            
            # Check by order number
            mongo_order_nos = {payment.get('orderNo') for payment in mongo_payments if payment.get('orderNo')}
            pg_order_nos = {payment.order_no for payment in pg_payments}
            
            matched_order_nos = mongo_order_nos.intersection(pg_order_nos)
            missing_pg_order_nos = mongo_order_nos - pg_order_nos
            missing_mongo_order_nos = pg_order_nos - mongo_order_nos
            
            self.stats.payments_matched = len(matched_order_nos)
            self.stats.payments_missing_pg = len(missing_pg_order_nos)
            self.stats.payments_missing_mongo = len(missing_mongo_order_nos)
            
            logger.info(f"MongoDB payments: {self.stats.total_payments_mongo}")
            logger.info(f"PostgreSQL payments: {self.stats.total_payments_pg}")
            logger.info(f"Matched: {self.stats.payments_matched}")
            logger.info(f"Missing in PostgreSQL: {self.stats.payments_missing_pg}")
            logger.info(f"Extra in PostgreSQL: {self.stats.payments_missing_mongo}")
        
        except Exception as e:
            logger.error(f"❌ Payment validation failed: {e}")
            self.stats.validation_errors.append(f"Payment validation: {e}")
    
    async def validate_data_integrity(self):
        """Validate data integrity constraints"""
        logger.info("🔒 Validating data integrity...")
        
        try:
            # Check for duplicate openids
            duplicate_openids = self.postgres_session.execute(
                text("""
                SELECT openid, COUNT(*) as count 
                FROM users 
                GROUP BY openid 
                HAVING COUNT(*) > 1
                """)
            ).fetchall()
            
            if duplicate_openids:
                self.stats.data_integrity_issues.append(DataIntegrityIssue(
                    table_name="users",
                    record_id="duplicates",
                    issue_type="duplicate_data",
                    description=f"Duplicate openids found: {duplicate_openids}",
                    severity="critical",
                    recommendation="Remove duplicate openid records"
                ))
            
            # Check for duplicate task_ids in translations
            duplicate_task_ids = self.postgres_session.execute(
                text("""
                SELECT task_id, COUNT(*) as count 
                FROM translations 
                GROUP BY task_id 
                HAVING COUNT(*) > 1
                """)
            ).fetchall()
            
            if duplicate_task_ids:
                self.stats.data_integrity_issues.append(DataIntegrityIssue(
                    table_name="translations",
                    record_id="duplicates",
                    issue_type="duplicate_data",
                    description=f"Duplicate task_ids found: {duplicate_task_ids}",
                    severity="critical",
                    recommendation="Remove duplicate task_id records"
                ))
            
            # Check for negative quotas
            negative_quotas = self.postgres_session.execute(
                text("SELECT COUNT(*) FROM users WHERE quota_used < 0 OR quota_limit < 0")
            ).scalar()
            
            if negative_quotas > 0:
                self.stats.data_integrity_issues.append(DataIntegrityIssue(
                    table_name="users",
                    record_id="negative_quotas",
                    issue_type="invalid_data",
                    description=f"Found {negative_quotas} users with negative quota values",
                    severity="medium",
                    recommendation="Review and fix negative quota values"
                ))
        
        except Exception as e:
            logger.error(f"❌ Data integrity validation failed: {e}")
            self.stats.validation_errors.append(f"Data integrity validation: {e}")
    
    async def validate_foreign_keys(self):
        """Validate foreign key constraints"""
        logger.info("🔗 Validating foreign key constraints...")
        
        try:
            # Check for orphaned translations (no user)
            orphaned_translations = self.postgres_session.execute(
                text("""
                SELECT COUNT(*) FROM translations t 
                LEFT JOIN users u ON t.user_id = u.id 
                WHERE u.id IS NULL
                """)
            ).scalar()
            
            if orphaned_translations > 0:
                self.stats.data_integrity_issues.append(DataIntegrityIssue(
                    table_name="translations",
                    record_id="orphaned_records",
                    issue_type="foreign_key_violation",
                    description=f"Found {orphaned_translations} translations with no user",
                    severity="high",
                    recommendation="Fix or remove orphaned translation records"
                ))
            
            # Check for orphaned subscriptions (no user)
            orphaned_subscriptions = self.postgres_session.execute(
                text("""
                SELECT COUNT(*) FROM subscriptions s 
                LEFT JOIN users u ON s.user_id = u.id 
                WHERE u.id IS NULL
                """)
            ).scalar()
            
            if orphaned_subscriptions > 0:
                self.stats.data_integrity_issues.append(DataIntegrityIssue(
                    table_name="subscriptions",
                    record_id="orphaned_records",
                    issue_type="foreign_key_violation",
                    description=f"Found {orphaned_subscriptions} subscriptions with no user",
                    severity="high",
                    recommendation="Fix or remove orphaned subscription records"
                ))
            
            # Check for orphaned payments (no user)
            orphaned_payments = self.postgres_session.execute(
                text("""
                SELECT COUNT(*) FROM payment_orders p 
                LEFT JOIN users u ON p.user_id = u.id 
                WHERE u.id IS NULL
                """)
            ).scalar()
            
            if orphaned_payments > 0:
                self.stats.data_integrity_issues.append(DataIntegrityIssue(
                    table_name="payment_orders",
                    record_id="orphaned_records",
                    issue_type="foreign_key_violation",
                    description=f"Found {orphaned_payments} payments with no user",
                    severity="high",
                    recommendation="Fix or remove orphaned payment records"
                ))
        
        except Exception as e:
            logger.error(f"❌ Foreign key validation failed: {e}")
            self.stats.validation_errors.append(f"Foreign key validation: {e}")
    
    async def validate_data_consistency(self):
        """Validate data consistency across related tables"""
        logger.info("⚖️ Validating data consistency...")
        
        try:
            # Check user quota consistency
            quota_inconsistency = self.postgres_session.execute(
                text("""
                SELECT COUNT(*) FROM users u 
                WHERE u.quota_used > u.quota_limit
                """)
            ).scalar()
            
            if quota_inconsistency > 0:
                self.stats.data_integrity_issues.append(DataIntegrityIssue(
                    table_name="users",
                    record_id="quota_inconsistency",
                    issue_type="data_inconsistency",
                    description=f"Found {quota_inconsistency} users with used quota exceeding limit",
                    severity="medium",
                    recommendation="Review quota calculation logic"
                ))
            
            # Check subscription status consistency
            expired_active_subscriptions = self.postgres_session.execute(
                text("""
                SELECT COUNT(*) FROM subscriptions s 
                WHERE s.status = 'active' AND s.end_date < NOW()
                """)
            ).scalar()
            
            if expired_active_subscriptions > 0:
                self.stats.data_integrity_issues.append(DataIntegrityIssue(
                    table_name="subscriptions",
                    record_id="expired_active",
                    issue_type="data_inconsistency",
                    description=f"Found {expired_active_subscriptions} active subscriptions that are expired",
                    severity="medium",
                    recommendation="Update subscription status for expired records"
                ))
        
        except Exception as e:
            logger.error(f"❌ Data consistency validation failed: {e}")
            self.stats.validation_errors.append(f"Data consistency validation: {e}")
    
    def parse_datetime(self, dt: Any) -> Optional[datetime]:
        """Parse datetime from various formats"""
        if dt is None:
            return None
        
        if isinstance(dt, datetime):
            return dt
        
        if isinstance(dt, str):
            try:
                return datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except ValueError:
                return None
        
        return None
    
    def generate_report(self, output_file: Optional[str] = None) -> Dict:
        """Generate validation report"""
        report = {
            'validation_timestamp': datetime.now().isoformat(),
            'validation_stats': asdict(self.stats),
            'summary': {
                'total_records_mongo': (self.stats.total_users_mongo + 
                                       self.stats.total_subscriptions_mongo + 
                                       self.stats.total_translations_mongo + 
                                       self.stats.total_payments_mongo),
                'total_records_postgresql': (self.stats.total_users_pg + 
                                            self.stats.total_subscriptions_pg + 
                                            self.stats.total_translations_pg + 
                                            self.stats.total_payments_pg),
                'total_matched': (self.stats.users_matched + 
                                self.stats.subscriptions_matched + 
                                self.stats.translations_matched + 
                                self.stats.payments_matched),
                'total_missing_postgresql': (self.stats.users_missing_pg + 
                                           self.stats.subscriptions_missing_pg + 
                                           self.stats.translations_missing_pg + 
                                           self.stats.payments_missing_pg),
                'total_integrity_issues': len(self.stats.data_integrity_issues),
                'total_validation_errors': len(self.stats.validation_errors)
            },
            'integrity_issues': [asdict(issue) for issue in self.stats.data_integrity_issues],
            'validation_errors': self.stats.validation_errors,
            'recommendations': self.generate_recommendations()
        }
        
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"📄 Report saved to {output_file}")
        
        return report
    
    def generate_recommendations(self) -> List[str]:
        """Generate recommendations based on validation results"""
        recommendations = []
        
        if self.stats.users_missing_pg > 0:
            recommendations.append(f"Re-run migration for {self.stats.users_missing_pg} missing users")
        
        if self.stats.translations_missing_pg > 0:
            recommendations.append(f"Re-run migration for {self.stats.translations_missing_pg} missing translations")
        
        critical_issues = [issue for issue in self.stats.data_integrity_issues if issue.severity == 'critical']
        if critical_issues:
            recommendations.append(f"Address {len(critical_issues)} critical data integrity issues immediately")
        
        high_issues = [issue for issue in self.stats.data_integrity_issues if issue.severity == 'high']
        if high_issues:
            recommendations.append(f"Resolve {len(high_issues)} high priority issues before production deployment")
        
        medium_issues = [issue for issue in self.stats.data_integrity_issues if issue.severity == 'medium']
        if medium_issues:
            recommendations.append(f"Review and fix {len(medium_issues)} medium priority issues")
        
        if not self.stats.validation_errors and not self.stats.data_integrity_issues:
            recommendations.append("Migration validation completed successfully - ready for production deployment")
        
        return recommendations

async def main():
    """Main validation function"""
    parser = argparse.ArgumentParser(description="Validate data migration completeness")
    parser.add_argument("--detailed", action="store_true", help="Perform detailed validation")
    parser.add_argument("--output-report", help="Output report file path")
    
    args = parser.parse_args()
    
    validator = MigrationValidator(detailed=args.detailed)
    
    try:
        await validator.connect()
        stats = await validator.validate_all()
        
        # Generate and print summary
        report = validator.generate_report(args.output_report)
        
        print("\n" + "="*60)
        print("📊 VALIDATION SUMMARY")
        print("="*60)
        
        summary = report['summary']
        print(f"Total Records (MongoDB): {summary['total_records_mongo']}")
        print(f"Total Records (PostgreSQL): {summary['total_records_postgresql']}")
        print(f"Successfully Matched: {summary['total_matched']}")
        print(f"Missing in PostgreSQL: {summary['total_missing_postgresql']}")
        print(f"Integrity Issues: {summary['total_integrity_issues']}")
        print(f"Validation Errors: {summary['total_validation_errors']}")
        
        if summary['total_integrity_issues'] > 0:
            print(f"\n⚠️  Found {summary['total_integrity_issues']} data integrity issues")
            
            severity_counts = {}
            for issue in stats.data_integrity_issues:
                severity_counts[issue.severity] = severity_counts.get(issue.severity, 0) + 1
            
            for severity, count in severity_counts.items():
                print(f"  {severity.upper()}: {count}")
        
        print(f"\n📋 Recommendations:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
        
        print("="*60)
        
        # Exit with appropriate code
        if summary['total_validation_errors'] > 0:
            logger.error("❌ Validation completed with errors")
            sys.exit(1)
        elif summary['total_integrity_issues'] > 0:
            logger.warning("⚠️ Validation completed with integrity issues")
            sys.exit(2)
        else:
            logger.info("✅ Validation completed successfully")
            sys.exit(0)
            
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        sys.exit(1)
    finally:
        await validator.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
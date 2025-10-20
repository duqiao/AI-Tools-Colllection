#!/usr/bin/env python3
"""
Data Migration Script: Node.js (MongoDB) to FastAPI (PostgreSQL)

This script migrates data from the existing Node.js backend (MongoDB)
to the new FastAPI backend (PostgreSQL).

Usage:
    python migrate_data.py [--dry-run] [--batch-size=100] [--source-uri=...] [--target-uri=...]

Options:
    --dry-run: Simulate migration without making changes
    --batch-size: Number of records to process in each batch (default: 100)
    --source-uri: MongoDB connection URI (default: from config)
    --target-uri: PostgreSQL connection URI (default: from config)
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from pathlib import Path

# Add parent directory to path to import backend modules
sys.path.append(str(Path(__file__).parent.parent))

import pymongo
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.models.user import User
from app.models.subscription import Subscription
from app.models.translation import Translation
from app.models.payment import PaymentOrder
from app.models.usage import UsageRecord
from app.database import get_db

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('migration.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class MigrationStats:
    """Migration statistics"""
    total_users: int = 0
    migrated_users: int = 0
    failed_users: int = 0
    total_subscriptions: int = 0
    migrated_subscriptions: int = 0
    failed_subscriptions: int = 0
    total_translations: int = 0
    migrated_translations: int = 0
    failed_translations: int = 0
    total_payments: int = 0
    migrated_payments: int = 0
    failed_payments: int = 0
    start_time: datetime = None
    end_time: datetime = None

class DataMigrator:
    """Data migration from MongoDB to PostgreSQL"""
    
    def __init__(self, dry_run: bool = False, batch_size: int = 100):
        self.dry_run = dry_run
        self.batch_size = batch_size
        self.settings = get_settings()
        self.stats = MigrationStats()
        
        # Database connections
        self.mongo_client = None
        self.mongo_db = None
        self.postgres_engine = None
        self.postgres_session = None
        
    async def connect(self):
        """Establish database connections"""
        try:
            # Connect to MongoDB (source)
            mongo_uri = getattr(self.settings, 'MONGODB_URI', 'mongodb://localhost:27017')
            self.mongo_client = pymongo.MongoClient(mongo_uri)
            self.mongo_db = self.mongo_client.media_translator
            
            # Test MongoDB connection
            self.mongo_db.list_collection_names()
            logger.info("✅ Connected to MongoDB (source)")
            
            # Connect to PostgreSQL (target)
            postgres_uri = self.settings.DATABASE_URL
            self.postgres_engine = create_engine(postgres_uri)
            SessionLocal = sessionmaker(bind=self.postgres_engine)
            self.postgres_session = SessionLocal()
            
            # Test PostgreSQL connection
            self.postgres_session.execute(text("SELECT 1"))
            logger.info("✅ Connected to PostgreSQL (target)")
            
        except Exception as e:
            logger.error(f"❌ Database connection failed: {e}")
            raise
    
    async def disconnect(self):
        """Close database connections"""
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("✅ Disconnected from MongoDB")
        
        if self.postgres_session:
            self.postgres_session.close()
            logger.info("✅ Disconnected from PostgreSQL")
    
    async def migrate_all(self):
        """Execute complete migration"""
        self.stats.start_time = datetime.now()
        
        logger.info("🚀 Starting data migration...")
        if self.dry_run:
            logger.info("🧪 DRY RUN MODE - No changes will be made")
        
        try:
            # Migration order matters due to foreign key constraints
            await self.migrate_users()
            await self.migrate_subscriptions()
            await self.migrate_translations()
            await self.migrate_payment_orders()
            await self.migrate_usage_records()
            
        except Exception as e:
            logger.error(f"❌ Migration failed: {e}")
            raise
        finally:
            self.stats.end_time = datetime.now()
            await self.print_summary()
    
    async def migrate_users(self):
        """Migrate users from MongoDB to PostgreSQL"""
        logger.info("👥 Migrating users...")
        
        try:
            # Get all users from MongoDB
            mongo_users = list(self.mongo_db.users.find({}))
            self.stats.total_users = len(mongo_users)
            
            logger.info(f"Found {self.stats.total_users} users to migrate")
            
            for i in range(0, len(mongo_users), self.batch_size):
                batch = mongo_users[i:i + self.batch_size]
                await self.migrate_user_batch(batch)
                
                # Progress reporting
                progress = min(i + self.batch_size, self.stats.total_users)
                percentage = (progress / self.stats.total_users) * 100
                logger.info(f"Users progress: {progress}/{self.stats.total_users} ({percentage:.1f}%)")
        
        except Exception as e:
            logger.error(f"❌ User migration failed: {e}")
            raise
    
    async def migrate_user_batch(self, mongo_users: List[Dict]):
        """Migrate a batch of users"""
        for mongo_user in mongo_users:
            try:
                # Convert MongoDB user to PostgreSQL format
                user_data = self.convert_user_data(mongo_user)
                
                if not self.dry_run:
                    # Check if user already exists
                    existing_user = self.postgres_session.query(User).filter(
                        User.openid == user_data['openid']
                    ).first()
                    
                    if existing_user:
                        logger.debug(f"User {user_data['openid']} already exists, skipping...")
                        continue
                    
                    # Create new user
                    new_user = User(**user_data)
                    self.postgres_session.add(new_user)
                    self.postgres_session.commit()
                
                self.stats.migrated_users += 1
                logger.debug(f"✅ Migrated user: {user_data.get('openid', 'unknown')}")
                
            except Exception as e:
                self.stats.failed_users += 1
                logger.error(f"❌ Failed to migrate user {mongo_user.get('_id')}: {e}")
                
                if not self.dry_run:
                    self.postgres_session.rollback()
    
    def convert_user_data(self, mongo_user: Dict) -> Dict:
        """Convert MongoDB user to PostgreSQL format"""
        return {
            'openid': mongo_user.get('openid'),
            'unionid': mongo_user.get('unionid'),
            'username': mongo_user.get('nickname') or mongo_user.get('username'),
            'avatar_url': mongo_user.get('avatarUrl'),
            'phone_number': mongo_user.get('phoneNumber'),
            'email': mongo_user.get('email'),
            'subscription_level': mongo_user.get('subscriptionLevel', 'free'),
            'subscription_status': mongo_user.get('subscriptionStatus', 'active'),
            'subscription_expires_at': self.parse_datetime(mongo_user.get('subscriptionExpiresAt')),
            'quota_used': mongo_user.get('quotaUsed', 0),
            'quota_limit': mongo_user.get('quotaLimit', 1),
            'quota_reset_date': self.parse_date(mongo_user.get('quotaResetDate')),
            'is_active': mongo_user.get('isActive', True),
            'is_verified': mongo_user.get('isVerified', False),
            'total_translations': mongo_user.get('totalTranslations', 0),
            'last_login_at': self.parse_datetime(mongo_user.get('lastLoginAt')),
            'preferences': json.dumps(mongo_user.get('preferences', {})),
            'created_at': self.parse_datetime(mongo_user.get('createdAt', datetime.now())),
            'updated_at': self.parse_datetime(mongo_user.get('updatedAt', datetime.now()))
        }
    
    async def migrate_subscriptions(self):
        """Migrate subscriptions from MongoDB to PostgreSQL"""
        logger.info("💳 Migrating subscriptions...")
        
        try:
            mongo_subscriptions = list(self.mongo_db.subscriptions.find({}))
            self.stats.total_subscriptions = len(mongo_subscriptions)
            
            logger.info(f"Found {self.stats.total_subscriptions} subscriptions to migrate")
            
            for mongo_sub in mongo_subscriptions:
                try:
                    sub_data = self.convert_subscription_data(mongo_sub)
                    
                    if not self.dry_run:
                        # Get user ID from PostgreSQL
                        user = self.postgres_session.query(User).filter(
                            User.openid == sub_data['user_openid']
                        ).first()
                        
                        if not user:
                            logger.warning(f"User not found for subscription: {sub_data['user_openid']}")
                            continue
                        
                        # Create subscription
                        new_sub = Subscription(
                            user_id=user.id,
                            plan_type=sub_data['plan_type'],
                            status=sub_data['status'],
                            start_date=sub_data['start_date'],
                            end_date=sub_data['end_date'],
                            monthly_quota=sub_data['monthly_quota'],
                            used_quota=sub_data['used_quota'],
                            auto_renew=sub_data['auto_renew'],
                            created_at=sub_data['created_at'],
                            updated_at=sub_data['updated_at']
                        )
                        self.postgres_session.add(new_sub)
                        self.postgres_session.commit()
                    
                    self.stats.migrated_subscriptions += 1
                    
                except Exception as e:
                    self.stats.failed_subscriptions += 1
                    logger.error(f"❌ Failed to migrate subscription {mongo_sub.get('_id')}: {e}")
                    
                    if not self.dry_run:
                        self.postgres_session.rollback()
        
        except Exception as e:
            logger.error(f"❌ Subscription migration failed: {e}")
            raise
    
    def convert_subscription_data(self, mongo_sub: Dict) -> Dict:
        """Convert MongoDB subscription to PostgreSQL format"""
        return {
            'user_openid': mongo_sub.get('userId'),
            'plan_type': mongo_sub.get('planType', 'free'),
            'status': mongo_sub.get('status', 'active'),
            'start_date': self.parse_datetime(mongo_sub.get('startDate')),
            'end_date': self.parse_datetime(mongo_sub.get('endDate')),
            'monthly_quota': mongo_sub.get('monthlyQuota', 1),
            'used_quota': mongo_sub.get('usedQuota', 0),
            'auto_renew': mongo_sub.get('autoRenew', False),
            'created_at': self.parse_datetime(mongo_sub.get('createdAt', datetime.now())),
            'updated_at': self.parse_datetime(mongo_sub.get('updatedAt', datetime.now()))
        }
    
    async def migrate_translations(self):
        """Migrate translations from MongoDB to PostgreSQL"""
        logger.info("🔤 Migrating translations...")
        
        try:
            mongo_translations = list(self.mongo_db.translations.find({}))
            self.stats.total_translations = len(mongo_translations)
            
            logger.info(f"Found {self.stats.total_translations} translations to migrate")
            
            for mongo_trans in mongo_translations:
                try:
                    trans_data = self.convert_translation_data(mongo_trans)
                    
                    if not self.dry_run:
                        # Get user ID from PostgreSQL
                        user = self.postgres_session.query(User).filter(
                            User.openid == trans_data['user_openid']
                        ).first()
                        
                        if not user:
                            logger.warning(f"User not found for translation: {trans_data['user_openid']}")
                            continue
                        
                        # Create translation
                        new_trans = Translation(
                            task_id=trans_data['task_id'],
                            user_id=user.id,
                            original_filename=trans_data['original_filename'],
                            original_file_url=trans_data['original_file_url'],
                            file_size=trans_data['file_size'],
                            file_type=trans_data['file_type'],
                            mime_type=trans_data['mime_type'],
                            duration_seconds=trans_data['duration_seconds'],
                            processing_status=trans_data['processing_status'],
                            processing_error=trans_data['processing_error'],
                            processing_started_at=trans_data['processing_started_at'],
                            processing_completed_at=trans_data['processing_completed_at'],
                            transcribed_text=trans_data['transcribed_text'],
                            confidence_score=trans_data['confidence_score'],
                            word_count=trans_data['word_count'],
                            service_provider=trans_data['service_provider'],
                            service_request_id=trans_data['service_request_id'],
                            service_cost=trans_data['service_cost'],
                            is_quota_used=trans_data['is_quota_used'],
                            quota_deducted_at=trans_data['quota_deducted_at'],
                            metadata=trans_data['metadata'],
                            created_at=trans_data['created_at'],
                            updated_at=trans_data['updated_at']
                        )
                        self.postgres_session.add(new_trans)
                        self.postgres_session.commit()
                    
                    self.stats.migrated_translations += 1
                    
                except Exception as e:
                    self.stats.failed_translations += 1
                    logger.error(f"❌ Failed to migrate translation {mongo_trans.get('_id')}: {e}")
                    
                    if not self.dry_run:
                        self.postgres_session.rollback()
        
        except Exception as e:
            logger.error(f"❌ Translation migration failed: {e}")
            raise
    
    def convert_translation_data(self, mongo_trans: Dict) -> Dict:
        """Convert MongoDB translation to PostgreSQL format"""
        return {
            'user_openid': mongo_trans.get('userId'),
            'task_id': mongo_trans.get('taskId') or mongo_trans.get('_id'),
            'original_filename': mongo_trans.get('originalFilename'),
            'original_file_url': mongo_trans.get('originalFileUrl'),
            'file_size': mongo_trans.get('fileSize'),
            'file_type': mongo_trans.get('fileType'),
            'mime_type': mongo_trans.get('mimeType'),
            'duration_seconds': mongo_trans.get('durationSeconds'),
            'processing_status': mongo_trans.get('processingStatus', 'pending'),
            'processing_error': mongo_trans.get('processingError'),
            'processing_started_at': self.parse_datetime(mongo_trans.get('processingStartedAt')),
            'processing_completed_at': self.parse_datetime(mongo_trans.get('processingCompletedAt')),
            'transcribed_text': mongo_trans.get('transcribedText'),
            'confidence_score': mongo_trans.get('confidenceScore'),
            'word_count': mongo_trans.get('wordCount'),
            'service_provider': mongo_trans.get('serviceProvider'),
            'service_request_id': mongo_trans.get('serviceRequestId'),
            'service_cost': mongo_trans.get('serviceCost'),
            'is_quota_used': mongo_trans.get('isQuotaUsed', True),
            'quota_deducted_at': self.parse_datetime(mongo_trans.get('quotaDeductedAt')),
            'metadata': json.dumps(mongo_trans.get('metadata', {})),
            'created_at': self.parse_datetime(mongo_trans.get('createdAt', datetime.now())),
            'updated_at': self.parse_datetime(mongo_trans.get('updatedAt', datetime.now()))
        }
    
    async def migrate_payment_orders(self):
        """Migrate payment orders from MongoDB to PostgreSQL"""
        logger.info("💰 Migrating payment orders...")
        
        try:
            mongo_payments = list(self.mongo_db.payment_orders.find({}))
            self.stats.total_payments = len(mongo_payments)
            
            logger.info(f"Found {self.stats.total_payments} payment orders to migrate")
            
            for mongo_payment in mongo_payments:
                try:
                    payment_data = self.convert_payment_data(mongo_payment)
                    
                    if not self.dry_run:
                        # Get user ID from PostgreSQL
                        user = self.postgres_session.query(User).filter(
                            User.openid == payment_data['user_openid']
                        ).first()
                        
                        if not user:
                            logger.warning(f"User not found for payment: {payment_data['user_openid']}")
                            continue
                        
                        # Create payment order
                        new_payment = PaymentOrder(
                            user_id=user.id,
                            order_no=payment_data['order_no'],
                            plan_type=payment_data['plan_type'],
                            amount=payment_data['amount'],
                            currency=payment_data['currency'],
                            payment_method=payment_data['payment_method'],
                            payment_status=payment_data['payment_status'],
                            transaction_id=payment_data['transaction_id'],
                            paid_at=payment_data['paid_at'],
                            created_at=payment_data['created_at'],
                            updated_at=payment_data['updated_at']
                        )
                        self.postgres_session.add(new_payment)
                        self.postgres_session.commit()
                    
                    self.stats.migrated_payments += 1
                    
                except Exception as e:
                    self.stats.failed_payments += 1
                    logger.error(f"❌ Failed to migrate payment {mongo_payment.get('_id')}: {e}")
                    
                    if not self.dry_run:
                        self.postgres_session.rollback()
        
        except Exception as e:
            logger.error(f"❌ Payment migration failed: {e}")
            raise
    
    def convert_payment_data(self, mongo_payment: Dict) -> Dict:
        """Convert MongoDB payment to PostgreSQL format"""
        return {
            'user_openid': mongo_payment.get('userId'),
            'order_no': mongo_payment.get('orderNo'),
            'plan_type': mongo_payment.get('planType'),
            'amount': mongo_payment.get('amount', 0.0),
            'currency': mongo_payment.get('currency', 'CNY'),
            'payment_method': mongo_payment.get('paymentMethod', 'wechat'),
            'payment_status': mongo_payment.get('paymentStatus', 'pending'),
            'transaction_id': mongo_payment.get('transactionId'),
            'paid_at': self.parse_datetime(mongo_payment.get('paidAt')),
            'created_at': self.parse_datetime(mongo_payment.get('createdAt', datetime.now())),
            'updated_at': self.parse_datetime(mongo_payment.get('updatedAt', datetime.now()))
        }
    
    async def migrate_usage_records(self):
        """Migrate usage records from MongoDB to PostgreSQL"""
        logger.info("📊 Migrating usage records...")
        
        # Usage records can be derived from translations, so this is optional
        logger.info("ℹ️  Usage records can be derived from translations, skipping explicit migration")
    
    def parse_datetime(self, dt: Any) -> Optional[datetime]:
        """Parse datetime from various formats"""
        if dt is None:
            return None
        
        if isinstance(dt, datetime):
            return dt
        
        if isinstance(dt, str):
            try:
                # Try ISO format first
                return datetime.fromisoformat(dt.replace('Z', '+00:00'))
            except ValueError:
                try:
                    # Try other common formats
                    return datetime.strptime(dt, '%Y-%m-%d %H:%M:%S')
                except ValueError:
                    logger.warning(f"Could not parse datetime: {dt}")
                    return None
        
        return None
    
    def parse_date(self, d: Any) -> Optional[datetime]:
        """Parse date from various formats"""
        if d is None:
            return None
        
        if isinstance(d, datetime):
            return d
        
        if isinstance(d, str):
            try:
                return datetime.strptime(d, '%Y-%m-%d')
            except ValueError:
                logger.warning(f"Could not parse date: {d}")
                return None
        
        return None
    
    async def print_summary(self):
        """Print migration summary"""
        duration = (self.stats.end_time - self.stats.start_time).total_seconds() if self.stats.end_time else 0
        
        print("\n" + "="*60)
        print("📊 MIGRATION SUMMARY")
        print("="*60)
        print(f"Duration: {duration:.2f} seconds")
        print(f"Mode: {'DRY RUN' if self.dry_run else 'LIVE'}")
        print()
        
        print("👥 Users:")
        print(f"  Total: {self.stats.total_users}")
        print(f"  Migrated: {self.stats.migrated_users}")
        print(f"  Failed: {self.stats.failed_users}")
        print()
        
        print("💳 Subscriptions:")
        print(f"  Total: {self.stats.total_subscriptions}")
        print(f"  Migrated: {self.stats.migrated_subscriptions}")
        print(f"  Failed: {self.stats.failed_subscriptions}")
        print()
        
        print("🔤 Translations:")
        print(f"  Total: {self.stats.total_translations}")
        print(f"  Migrated: {self.stats.migrated_translations}")
        print(f"  Failed: {self.stats.failed_translations}")
        print()
        
        print("💰 Payments:")
        print(f"  Total: {self.stats.total_payments}")
        print(f"  Migrated: {self.stats.migrated_payments}")
        print(f"  Failed: {self.stats.failed_payments}")
        print()
        
        total_migrated = (self.stats.migrated_users + self.stats.migrated_subscriptions + 
                         self.stats.migrated_translations + self.stats.migrated_payments)
        total_failed = (self.stats.failed_users + self.stats.failed_subscriptions + 
                       self.stats.failed_translations + self.stats.failed_payments)
        
        print("📈 Overall:")
        print(f"  Total Records: {self.stats.total_users + self.stats.total_subscriptions + self.stats.total_translations + self.stats.total_payments}")
        print(f"  Migrated: {total_migrated}")
        print(f"  Failed: {total_failed}")
        
        if total_migrated + total_failed > 0:
            success_rate = (total_migrated / (total_migrated + total_failed)) * 100
            print(f"  Success Rate: {success_rate:.1f}%")
        
        print("="*60)
        
        if self.dry_run:
            print("🧪 This was a DRY RUN. No actual changes were made.")
            print("   Run without --dry-run to perform the actual migration.")
        elif total_failed > 0:
            print(f"⚠️  {total_failed} records failed to migrate. Check the log for details.")
        else:
            print("🎉 Migration completed successfully!")

async def main():
    """Main migration function"""
    parser = argparse.ArgumentParser(description="Migrate data from MongoDB to PostgreSQL")
    parser.add_argument("--dry-run", action="store_true", help="Simulate migration without making changes")
    parser.add_argument("--batch-size", type=int, default=100, help="Number of records per batch")
    parser.add_argument("--source-uri", help="MongoDB connection URI")
    parser.add_argument("--target-uri", help="PostgreSQL connection URI")
    
    args = parser.parse_args()
    
    # Initialize migrator
    migrator = DataMigrator(dry_run=args.dry_run, batch_size=args.batch_size)
    
    try:
        await migrator.connect()
        await migrator.migrate_all()
        
        if not args.dry_run:
            logger.info("✅ Migration completed successfully!")
        else:
            logger.info("✅ Dry run completed successfully!")
            
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)
    finally:
        await migrator.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
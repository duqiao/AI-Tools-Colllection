#!/usr/bin/env python3
"""
REAL-TIME MONITOR
=================

Monitor backend performance and activity in real-time
"""

import asyncio
import sys
import time
from datetime import datetime
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from app.core.database import get_collection
from app.core.redis import get_redis

class RealTimeMonitor:
    def __init__(self):
        self.running = True
        
    async def monitor_database_stats(self):
        """Monitor database statistics"""
        print("📊 DATABASE MONITOR")
        print("-" * 30)
        
        while self.running:
            try:
                # Get collection stats
                jobs_collection = await get_collection("processing_jobs")
                users_collection = await get_collection("users")
                media_collection = await get_collection("media_files")
                
                # Job status counts
                pipeline = [
                    {"$group": {
                        "_id": "$processing.status",
                        "count": {"$sum": 1}
                    }}
                ]
                
                status_counts = await jobs_collection.aggregate(pipeline).to_list(None)
                
                print(f"\r[{datetime.now().strftime('%H:%M:%S')}] ", end="")
                
                for status_count in status_counts:
                    status = status_count["_id"] or "unknown"
                    count = status_count["count"]
                    print(f"{status}: {count}  ", end="")
                
                # Total counts
                total_jobs = await jobs_collection.count_documents({})
                total_users = await users_collection.count_documents({})
                total_media = await media_collection.count_documents({})
                
                print(f"| Total: J:{total_jobs} U:{total_users} M:{total_media}", end="", flush=True)
                
                await asyncio.sleep(2)
                
            except Exception as e:
                print(f"\n❌ Monitor error: {e}")
                await asyncio.sleep(5)
    
    async def monitor_redis_activity(self):
        """Monitor Redis activity"""
        print("\n🔄 REDIS MONITOR")
        print("-" * 25)
        
        try:
            redis_client = await get_redis()
            
            while self.running:
                try:
                    # Test Redis connection
                    await redis_client.ping()
                    
                    # Get info
                    info = await redis_client.info()
                    connected_clients = info.get('connected_clients', 0)
                    used_memory = info.get('used_memory_human', '0B')
                    
                    print(f"\r[{datetime.now().strftime('%H:%M:%S')}] Redis: {connected_clients} clients | Memory: {used_memory}", end="", flush=True)
                    
                    await asyncio.sleep(3)
                    
                except Exception as e:
                    print(f"\n❌ Redis monitor error: {e}")
                    await asyncio.sleep(5)
                    
        except Exception as e:
            print(f"❌ Redis not available: {e}")
    
    async def monitor_recent_activity(self):
        """Monitor recent activity"""
        print("\n⏰ RECENT ACTIVITY")
        print("-" * 30)
        
        last_check = time.time()
        
        while self.running:
            try:
                jobs_collection = await get_collection("processing_jobs")
                
                # Get recent jobs (last 10 seconds)
                current_time = datetime.utcnow()
                recent_jobs = await jobs_collection.find({
                    "createdAt": {"$gte": current_time.timestamp() - 10}
                }).sort("createdAt", -1).to_list(None)
                
                if recent_jobs:
                    now = time.time()
                    if now - last_check >= 5:  # Show every 5 seconds
                        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] Recent activity:")
                        for job in recent_jobs[-3:]:  # Show last 3
                            status = job.get('processing', {}).get('status', 'unknown')
                            job_id = job.get('jobId', 'NO ID')[:8]
                            user_id = job.get('userId', 'NO USER')[:8]
                            print(f"  Job {job_id} - {status} - User {user_id}")
                        last_check = now
                
                await asyncio.sleep(1)
                
            except Exception as e:
                print(f"\n❌ Activity monitor error: {e}")
                await asyncio.sleep(5)
    
    async def run_monitor(self):
        """Run all monitors"""
        print("🔍 REAL-TIME BACKEND MONITOR")
        print("=" * 50)
        print("Press Ctrl+C to stop monitoring\n")
        
        # Start all monitoring tasks
        tasks = [
            asyncio.create_task(self.monitor_database_stats()),
            asyncio.create_task(self.monitor_redis_activity()),
            asyncio.create_task(self.monitor_recent_activity())
        ]
        
        try:
            # Wait for any task to complete (they won't unless error)
            await asyncio.gather(*tasks, return_exceptions=True)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping monitor...")
            self.running = False
            
            # Cancel all tasks
            for task in tasks:
                task.cancel()
            
            # Wait for tasks to cancel
            await asyncio.gather(*tasks, return_exceptions=True)
            
            print("✅ Monitor stopped")

if __name__ == "__main__":
    monitor = RealTimeMonitor()
    asyncio.run(monitor.run_monitor())
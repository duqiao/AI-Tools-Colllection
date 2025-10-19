"""
Translation queue service for managing background processing.

This module provides queue management for translation tasks,
including priority handling, worker coordination, and status tracking.
"""

import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from enum import Enum
import json
import logging

from app.core.logging import get_logger

logger = get_logger(__name__)


class TaskPriority(Enum):
    """Task priority levels."""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


class TaskStatus(Enum):
    """Task status in queue."""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class QueuedTask:
    """Represents a task in the processing queue."""
    
    def __init__(
        self,
        task_id: str,
        user_id: int,
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.task_id = task_id
        self.user_id = user_id
        self.priority = priority
        self.metadata = metadata or {}
        self.status = TaskStatus.QUEUED
        self.created_at = datetime.utcnow()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.retry_count = 0
        self.max_retries = 3
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "task_id": self.task_id,
            "user_id": self.user_id,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "metadata": self.metadata
        }


class TranslationQueueService:
    """Service for managing translation task queue."""
    
    def __init__(self, max_concurrent_tasks: int = 5):
        self.max_concurrent_tasks = max_concurrent_tasks
        self.queues = {
            TaskPriority.HIGH: [],
            TaskPriority.NORMAL: [],
            TaskPriority.LOW: []
        }
        self.processing_tasks: Dict[str, QueuedTask] = {}
        self.completed_tasks: Dict[str, QueuedTask] = {}
        self.failed_tasks: Dict[str, QueuedTask] = {}
        self.is_running = False
        
    async def start_queue_processor(self):
        """Start the background queue processor."""
        if self.is_running:
            logger.warning("Queue processor is already running")
            return
        
        self.is_running = True
        logger.info("Starting translation queue processor")
        
        # Start background processor
        asyncio.create_task(self._process_queue())
    
    async def stop_queue_processor(self):
        """Stop the background queue processor."""
        self.is_running = False
        logger.info("Stopping translation queue processor")
    
    async def enqueue_task(
        self,
        task_id: str,
        user_id: int,
        priority: TaskPriority = TaskPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Add a task to the processing queue.
        
        Args:
            task_id: Translation task ID
            user_id: User ID requesting the task
            priority: Task priority level
            metadata: Additional task metadata
            
        Returns:
            True if successfully queued
        """
        try:
            # Check if task already exists
            if self._get_task_by_id(task_id):
                logger.warning(f"Task {task_id} already exists in queue")
                return False
            
            # Create queued task
            queued_task = QueuedTask(task_id, user_id, priority, metadata)
            
            # Add to appropriate priority queue
            self.queues[priority].append(queued_task)
            
            logger.info(f"Queued task {task_id} with priority {priority.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to enqueue task {task_id}: {str(e)}")
            return False
    
    async def dequeue_task(self) -> Optional[QueuedTask]:
        """
        Get the next task from the queue based on priority.
        
        Returns:
            Next task to process or None if queue is empty
        """
        try:
            # Check if we can process more tasks
            if len(self.processing_tasks) >= self.max_concurrent_tasks:
                return None
            
            # Get next task by priority (HIGH -> NORMAL -> LOW)
            for priority in [TaskPriority.HIGH, TaskPriority.NORMAL, TaskPriority.LOW]:
                if self.queues[priority]:
                    task = self.queues[priority].pop(0)
                    task.status = TaskStatus.PROCESSING
                    task.started_at = datetime.utcnow()
                    self.processing_tasks[task.task_id] = task
                    return task
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to dequeue task: {str(e)}")
            return None
    
    async def mark_task_completed(
        self,
        task_id: str,
        result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Mark a task as completed.
        
        Args:
            task_id: Task ID
            result: Task result data
            
        Returns:
            True if successfully marked as completed
        """
        try:
            task = self.processing_tasks.get(task_id)
            if not task:
                logger.warning(f"Task {task_id} not found in processing tasks")
                return False
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.utcnow()
            if result:
                task.metadata.update({"result": result})
            
            # Move to completed tasks
            self.completed_tasks[task_id] = task
            del self.processing_tasks[task_id]
            
            logger.info(f"Task {task_id} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark task {task_id} as completed: {str(e)}")
            return False
    
    async def mark_task_failed(
        self,
        task_id: str,
        error_message: str,
        retry: bool = True
    ) -> bool:
        """
        Mark a task as failed and optionally retry.
        
        Args:
            task_id: Task ID
            error_message: Error description
            retry: Whether to retry the task
            
        Returns:
            True if successfully handled
        """
        try:
            task = self.processing_tasks.get(task_id)
            if not task:
                logger.warning(f"Task {task_id} not found in processing tasks")
                return False
            
            task.error_message = error_message
            task.retry_count += 1
            
            # Check if we should retry
            if retry and task.retry_count < task.max_retries:
                # Re-queue with exponential backoff
                await asyncio.sleep(2 ** task.retry_count)
                
                task.status = TaskStatus.QUEUED
                task.started_at = None
                
                # Add back to queue with lower priority
                retry_priority = TaskPriority.LOW if task.priority == TaskPriority.HIGH else task.priority
                self.queues[retry_priority].append(task)
                
                del self.processing_tasks[task_id]
                
                logger.info(f"Task {task_id} queued for retry {task.retry_count}/{task.max_retries}")
                return True
            else:
                # Mark as permanently failed
                task.status = TaskStatus.FAILED
                task.completed_at = datetime.utcnow()
                
                self.failed_tasks[task_id] = task
                del self.processing_tasks[task_id]
                
                logger.error(f"Task {task_id} failed permanently: {error_message}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to mark task {task_id} as failed: {str(e)}")
            return False
    
    async def cancel_task(self, task_id: str) -> bool:
        """
        Cancel a queued task.
        
        Args:
            task_id: Task ID to cancel
            
        Returns:
            True if successfully cancelled
        """
        try:
            # Check processing tasks
            if task_id in self.processing_tasks:
                task = self.processing_tasks[task_id]
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.utcnow()
                
                self.failed_tasks[task_id] = task
                del self.processing_tasks[task_id]
                
                logger.info(f"Cancelled processing task {task_id}")
                return True
            
            # Check queued tasks
            for priority, queue in self.queues.items():
                for i, task in enumerate(queue):
                    if task.task_id == task_id:
                        task.status = TaskStatus.CANCELLED
                        task.completed_at = datetime.utcnow()
                        
                        queue.pop(i)
                        self.failed_tasks[task_id] = task
                        
                        logger.info(f"Cancelled queued task {task_id}")
                        return True
            
            logger.warning(f"Task {task_id} not found for cancellation")
            return False
            
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {str(e)}")
            return False
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the current status of a task.
        
        Args:
            task_id: Task ID
            
        Returns:
            Task status information or None if not found
        """
        task = self._get_task_by_id(task_id)
        if task:
            return task.to_dict()
        return None
    
    def get_user_tasks(
        self,
        user_id: int,
        status: Optional[TaskStatus] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get tasks for a specific user.
        
        Args:
            user_id: User ID
            status: Filter by task status
            limit: Maximum number of tasks to return
            
        Returns:
            List of task information
        """
        user_tasks = []
        
        # Check all task collections
        all_tasks = []
        
        # Queued tasks
        for queue in self.queues.values():
            all_tasks.extend(queue)
        
        # Processing tasks
        all_tasks.extend(self.processing_tasks.values())
        
        # Completed tasks
        all_tasks.extend(self.completed_tasks.values())
        
        # Failed tasks
        all_tasks.extend(self.failed_tasks.values())
        
        # Filter by user and status
        for task in all_tasks:
            if task.user_id == user_id:
                if status is None or task.status == status:
                    user_tasks.append(task.to_dict())
        
        # Sort by creation time (newest first) and limit
        user_tasks.sort(
            key=lambda x: datetime.fromisoformat(x["created_at"]),
            reverse=True
        )
        
        return user_tasks[:limit]
    
    def get_queue_status(self) -> Dict[str, Any]:
        """
        Get overall queue status.
        
        Returns:
            Queue status information
        """
        try:
            queued_count = sum(len(queue) for queue in self.queues.values())
            processing_count = len(self.processing_tasks)
            completed_count = len(self.completed_tasks)
            failed_count = len(self.failed_tasks)
            
            # Calculate average wait time for queued tasks
            if queued_count > 0:
                oldest_task = min(
                    (task for queue in self.queues.values() for task in queue),
                    key=lambda t: t.created_at
                )
                wait_time = (datetime.utcnow() - oldest_task.created_at).total_seconds()
            else:
                wait_time = 0
            
            return {
                "is_running": self.is_running,
                "max_concurrent_tasks": self.max_concurrent_tasks,
                "queues": {
                    "high": len(self.queues[TaskPriority.HIGH]),
                    "normal": len(self.queues[TaskPriority.NORMAL]),
                    "low": len(self.queues[TaskPriority.LOW])
                },
                "counts": {
                    "queued": queued_count,
                    "processing": processing_count,
                    "completed": completed_count,
                    "failed": failed_count,
                    "total": queued_count + processing_count + completed_count + failed_count
                },
                "performance": {
                    "estimated_wait_time_seconds": wait_time,
                    "utilization_percent": (processing_count / self.max_concurrent_tasks) * 100,
                    "success_rate": (completed_count / (completed_count + failed_count) * 100) if (completed_count + failed_count) > 0 else 100
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get queue status: {str(e)}")
            return {
                "error": str(e),
                "is_running": self.is_running
            }
    
    def _get_task_by_id(self, task_id: str) -> Optional[QueuedTask]:
        """Find task by ID across all collections."""
        # Check queued tasks
        for queue in self.queues.values():
            for task in queue:
                if task.task_id == task_id:
                    return task
        
        # Check processing tasks
        if task_id in self.processing_tasks:
            return self.processing_tasks[task_id]
        
        # Check completed tasks
        if task_id in self.completed_tasks:
            return self.completed_tasks[task_id]
        
        # Check failed tasks
        if task_id in self.failed_tasks:
            return self.failed_tasks[task_id]
        
        return None
    
    async def _process_queue(self):
        """Background queue processor loop."""
        logger.info("Queue processor started")
        
        while self.is_running:
            try:
                # Get next task
                task = await self.dequeue_task()
                
                if task:
                    # Process the task (in a real implementation, this would
                    # call the actual translation processing logic)
                    logger.info(f"Processing task {task.task_id}")
                    
                    # For now, just simulate processing
                    asyncio.create_task(self._simulate_task_processing(task))
                else:
                    # No tasks available, wait briefly
                    await asyncio.sleep(1)
                    
            except Exception as e:
                logger.error(f"Queue processing error: {str(e)}")
                await asyncio.sleep(5)  # Wait before retrying
        
        logger.info("Queue processor stopped")
    
    async def _simulate_task_processing(self, task: QueuedTask):
        """Simulate task processing for demonstration."""
        try:
            # Simulate processing time
            processing_time = 10 + (hash(task.task_id) % 20)  # 10-30 seconds
            await asyncio.sleep(processing_time)
            
            # Simulate success/failure (90% success rate)
            import random
            if random.random() < 0.9:
                await self.mark_task_completed(task.task_id, {
                    "text": f"Simulated transcription for task {task.task_id}",
                    "confidence": 0.95
                })
            else:
                await self.mark_task_failed(task.task_id, "Simulated processing error")
                
        except Exception as e:
            await self.mark_task_failed(task.task_id, f"Processing error: {str(e)}")
    
    def cleanup_old_tasks(self, days: int = 7):
        """
        Clean up old completed and failed tasks.
        
        Args:
            days: Number of days to keep tasks
        """
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Clean up completed tasks
            completed_to_remove = [
                task_id for task_id, task in self.completed_tasks.items()
                if task.completed_at and task.completed_at < cutoff_date
            ]
            
            for task_id in completed_to_remove:
                del self.completed_tasks[task_id]
            
            # Clean up failed tasks
            failed_to_remove = [
                task_id for task_id, task in self.failed_tasks.items()
                if task.completed_at and task.completed_at < cutoff_date
            ]
            
            for task_id in failed_to_remove:
                del self.failed_tasks[task_id]
            
            removed_count = len(completed_to_remove) + len(failed_to_remove)
            if removed_count > 0:
                logger.info(f"Cleaned up {removed_count} old tasks")
                
        except Exception as e:
            logger.error(f"Task cleanup error: {str(e)}")


# Global queue service instance
translation_queue = TranslationQueueService()
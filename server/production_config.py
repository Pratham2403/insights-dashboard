# Production Configuration for Sprinklr Insights Dashboard

import os
from typing import Dict, Any

class ProductionConfig:
    """Production configuration settings"""
    
    # Flask settings
    FLASK_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
    FLASK_PORT = int(os.getenv('FLASK_PORT', 8000))
    FLASK_DEBUG = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    
    # Workflow settings
    LAZY_LOADING_ENABLED = True
    WORKFLOW_TIMEOUT = int(os.getenv('WORKFLOW_TIMEOUT', 300))  # 5 minutes
    MAX_CONCURRENT_WORKFLOWS = int(os.getenv('MAX_CONCURRENT_WORKFLOWS', 10))
    
    # Memory settings
    MEMORY_CLEANUP_INTERVAL = int(os.getenv('MEMORY_CLEANUP_INTERVAL', 3600))  # 1 hour
    MAX_CONVERSATION_AGE = int(os.getenv('MAX_CONVERSATION_AGE', 86400))  # 24 hours
    
    # Logging settings
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'sprinklr_insights_production.log')
    
    # Performance monitoring
    PERFORMANCE_MONITORING_ENABLED = True
    METRICS_COLLECTION_ENABLED = True
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return {
            'flask': {
                'host': cls.FLASK_HOST,
                'port': cls.FLASK_PORT,
                'debug': cls.FLASK_DEBUG
            },
            'workflow': {
                'lazy_loading': cls.LAZY_LOADING_ENABLED,
                'timeout': cls.WORKFLOW_TIMEOUT,
                'max_concurrent': cls.MAX_CONCURRENT_WORKFLOWS
            },
            'memory': {
                'cleanup_interval': cls.MEMORY_CLEANUP_INTERVAL,
                'max_age': cls.MAX_CONVERSATION_AGE
            },
            'logging': {
                'level': cls.LOG_LEVEL,
                'file': cls.LOG_FILE
            },
            'monitoring': {
                'performance': cls.PERFORMANCE_MONITORING_ENABLED,
                'metrics': cls.METRICS_COLLECTION_ENABLED
            }
        }

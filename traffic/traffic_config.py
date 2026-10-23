#!/usr/bin/env python3
"""
traffic_config.py - Centralized configuration for UDP traffic classes
"""

TRAFFIC_CLASSES = {
    'VOICE': {
        'name': 'VOICE',
        'port': 5001,
        'rate_mbps': 1.0,
        'priority': 'HIGH',
        'queue_id': 0,
        'packet_size': 250
    },
    'VIDEO': {
        'name': 'VIDEO',
        'port': 5002,
        'rate_mbps': 4.0,
        'priority': 'MEDIUM',
        'queue_id': 1,
        'packet_size': 1000
    },
    'BULK': {
        'name': 'BULK',
        'port': 5003,
        'rate_mbps': 6.0,
        'priority': 'LOW',
        'queue_id': 2,
        'packet_size': 1400
    }
}

BOTTLENECK_BW_MBPS = 5.0
SERVER_IP = "10.0.0.4"

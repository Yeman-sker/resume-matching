#!/bin/bash

echo "=== 停止所有服务 ==="

pkill -f "streaming_supervisor.sh"
pkill -f "data_generator.py"
pkill -f "streaming_resumes.py"
pkill -f "streaming_jobs.py"
pkill -f "batch_scheduler.py"
pkill -f "[p]ython.*main.py"
pkill -f "vite"

echo "所有服务已停止"

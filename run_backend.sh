#!/bin/bash
cd /home/ubuntu/.openclaw/workspace/construction_cost
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

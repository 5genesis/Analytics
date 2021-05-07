#!/usr/bin/env bash
set -xeuo pipefail

docker build --rm -t 5genesis-analytics/data-handler:0.2.8 "Data handler"
docker build --rm -t 5genesis-analytics/correlation:0.1.5 Correlation
docker build --rm -t 5genesis-analytics/prediction:0.1.7 Prediction
docker build --rm -t 5genesis-analytics/statistical-analysis:0.1.4 "Statistical analysis"
docker build --rm -t 5genesis-analytics/feature-selection:0.1.3 Feature_Selection
docker build --rm -t 5genesis-analytics/visualization:1.0.1 Visualization
docker stack deploy -c analytics-stack.yaml analytics

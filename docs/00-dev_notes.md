# Daemonium Development Notes

## This document contains developer notes and reminders for ongoing work on the Daemonium project.

## To-Do Items

### Vector Processing & Tracking

- Add synchronization between Qdrant and MongoDB tracking:
  - 

### System monitoring with Prometheus/Grafana
The NEW PROJECT NAME now includes a comprehensive monitoring solution using Prometheus and Grafana to track system and container metrics.

#### Overview

This monitoring stack consists of:
- **Prometheus**: Time series database for metrics collection and storage
- **Grafana**: Visualization platform for metrics dashboards
- **cAdvisor**: Container metrics collector
- **Node Exporter**: Host system metrics collector
- **MongoDB Exporter**: MongoDB-specific metrics collector

#### Setup Instructions

1. **Configuration Files**
   - Prometheus configuration: `config/prometheus/prometheus.yml`
   - Grafana dashboards: `config/grafana/dashboards/`
   - Grafana datasources: `config/grafana/datasources.yaml`
   - Docker Compose file: `docker-compose.monitoring.yml`

2. **Starting the Monitoring Stack**
   ```bash
   # Start the main NEW PROJECT NAME services
   docker-compose up -d
   
   # Start the monitoring stack
   docker-compose -f docker-compose.monitoring.yml up -d
   ```

3. **Accessing Dashboards**
   - Prometheus UI: http://localhost:9090
   - Grafana UI: http://localhost:3001
     - Default credentials: admin/admin
     - Preconfigured dashboards:
       - Docker Containers: System-level view of container performance
       - System Metrics: Host machine metrics (CPU, memory, disk, network)

4. **Adding Custom Metrics**
   
   To expose custom metrics from the NEW PROJECT NAME application:
   

5. **Alert Configuration**
   
   To set up alerts for critical conditions:
   
   1. Create an alerting configuration in `config/prometheus/alerts.yml`
   2. Update the Prometheus configuration to include alerts
   3. Configure notification channels in Grafana (email, Slack, etc.)

#### Monitoring Best Practices

1. **Key Metrics to Monitor**
   - Container resource usage (CPU, memory)
   - Host system resources
   - MongoDB performance metrics
   - Application-specific metrics:
     - 

2. **Dashboard Organization**
   - System-level dashboards: Infrastructure health
   - Application-level dashboards: Business logic and performance
   - Service-specific dashboards: MongoDB, Neo4j, Qdrant

3. **Performance Optimization**
   - Use metrics to identify bottlenecks in the pipeline
   - Monitor GPU utilization for vector processing tasks
   - Track memory usage patterns for large embeddings operations

#### Completed Enhancements (May 4, 2025)

- ✓ **Vector Database Monitoring**: Added specific metrics for MongoDB and vector operations in the vector embedding dashboard
- ✓ **Comprehensive Dashboards**: Created multiple dashboards for tracking different aspects of the pipeline:
  - Basic test dashboard for monitoring system connectivity

- ✓ **Documentation**: Created comprehensive Prometheus query documentation in several files:
- 
- ✓ **Diagnostic Script**: Enhanced the check_prometheus_metrics.py script to verify dashboard queries

#### Future Enhancements
- 

#### Troubleshooting
- If metrics aren't appearing, check Prometheus targets at http://localhost:9090/targets


### Documentation Updates
- 

### GPU Optimization

- 
### Web UI Improvements
- 

### Deployment Improvements
- Document resource requirements for different dataset sizes

## Known Issues
- 

## Ideas for Future Development
- 

---

*Last updated: June 21, 2025*

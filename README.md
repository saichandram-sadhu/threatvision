# 🛡️ ThreatVision: The Ultimate Threat Intelligence Platform

![Hero Banner](docs/assets/hero.png)

<div align="center">

[![Infrastructure](https://img.shields.io/badge/Infrastructure-Terraform-623CE4?style=for-the-badge&logo=terraform)](https://www.terraform.io/)
[![Cloud](https://img.shields.io/badge/Cloud-AWS-FF9900?style=for-the-badge&logo=amazon-aws)](https://aws.amazon.com/)
[![Orchestration](https://img.shields.io/badge/Orchestration-ECS_Fargate-2E27AD?style=for-the-badge&logo=amazon-ecs)](https://aws.amazon.com/ecs/)
[![CI/CD](https://img.shields.io/badge/CI/CD-GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions)](https://github.com/features/actions)

**Transforming raw threat data into actionable intelligence with a production-grade DevOps pipeline.**

[Explore the App](http://threatvision-alb-2018723688.ap-south-1.elb.amazonaws.com) • [Report Bug](https://github.com/threatvision/issues) • [Request Feature](https://github.com/threatvision/issues)

</div>

---

## 📽️ Project Vision

**ThreatVision** is not just an application; it's a statement in modern security operations. It bridges the gap between complex MISP data and human-readable insights. This project showcases a full-scale DevOps migration from a local "it works on my machine" state to a globally accessible, resilient AWS infrastructure.

---

## 🏗️ DevOps Architecture

Our architecture follows the **Well-Architected Framework** principles, ensuring high availability, security, and automated recovery.

![Pipeline Flow](docs/assets/pipeline.png)

### The CI/CD Blueprint
1.  **Code (GitHub)**: Semantic versioning and trunk-based development.
2.  **Build (Docker)**: Multi-stage builds for minimal image size.
3.  **Registry (ECR)**: Private, encrypted container image storage.
4.  **Provisioning (Terraform)**: Declarative infrastructure management.
5.  **Compute (ECS Fargate)**: Serverless container execution—no EC2 to manage!
6.  **Database (RDS)**: Multi-AZ PostgreSQL for data integrity.

---

## 🌩️ Deployment Journey & Challenges

The path to production was paved with technical challenges that we conquered through systematic debugging and automation.

### 🔴 The 503 Backend Mystery (Fixed)
*   **Problem**: Backend services kept restarting (0/1 tasks).
*   **Solution**: Fixed the health check logic in `main.py` and adjusted the ALB `health_check_grace_period` in Terraform to allow enough time for the database pool to warm up.

### 🔴 Proxy 401: The JWT Wall (Fixed)
*   **Problem**: Settings and Integrations pages returned `401 Unauthorized` behind the AWS Load Balancer.
*   **Solution**: Refactored the Next.js API proxy to use `getToken` instead of `getServerSession`, ensuring session tokens are correctly forwarded through the AWS network layers.

### 🔴 MISP 405: The Missing Link (Fixed)
*   **Problem**: MISP Explorer wouldn't load due to `Method Not Allowed`.
*   **Solution**: Implemented missing `GET` handlers in the FastAPI backend to synchronize state with the frontend's requirements.

---

## 📊 Live Platform Sneak Peek

<div align="center">

### 🔌 Seamless Integrations
![Integrations](docs/assets/integrations.png)
*Manage MISP, OpenCTI, and custom connectors in one sleek interface.*

### 🔍 Threat Explorer
![MISP Explorer](docs/assets/misp.png)
*Deep dive into IoCs, attributes, and threat actors with advanced filtering.*

### 🔑 Verified Access
![Registration](docs/assets/registration.png)
*Secure registration flow with auto-provisioned API keys.*

</div>

---

## ⌨️ Command Center

### 🚀 Terraform Management
```bash
# Initialize the cloud foundation
terraform init

# Plan the infrastructure changes
terraform plan -out=tfplan

# Apply with confidence
terraform apply "tfplan"
```

### 🐳 Container Ops
```bash
# Build the production image
docker build -t threatvision-backend ./backend

# Authenticate with AWS
aws ecr get-login-password --region ap-south-1 | docker login ...

# Ship it!
docker push <aws_id>.dkr.ecr.ap-south-1.amazonaws.com/threatvision-backend:latest
```

### 📡 ECS Maintenance
```bash
# Force deployment of latest code
aws ecs update-service --cluster threatvision-cluster --service threatvision-backend-service --force-new-deployment

# Run database migrations in production
aws ecs run-task --cluster threatvision-cluster --task-definition threatvision-migration
```

---

## 🛡️ Security First
- **IAM Least Privilege**: Fine-grained roles for ECS tasks.
- **VPC Isolation**: RDS and Backend in private subnets.
- **ALB Encryption**: Managed traffic routing with path-based rules.

---

<div align="center">

**Built for Security Engineers. Engineered for DevSecOps.**

[Back to top ↑](#-threatvision-the-ultimate-threat-intelligence-platform)

</div>

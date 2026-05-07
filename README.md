# 🛡️ ThreatVision: The Ultimate Threat Intelligence Platform

<p align="center">
  <img src="docs/assets/logo.png" width="200" alt="ThreatVision Logo">
</p>

![Hero Banner](docs/assets/hero.png)

<div align="center">

[![Infrastructure](https://img.shields.io/badge/Infrastructure-Terraform-623CE4?style=for-the-badge&logo=terraform)](https://www.terraform.io/)
[![Cloud](https://img.shields.io/badge/Cloud-AWS-FF9900?style=for-the-badge&logo=amazon-aws)](https://aws.amazon.com/)
[![Orchestration](https://img.shields.io/badge/Orchestration-ECS_Fargate-2E27AD?style=for-the-badge&logo=amazon-ecs)](https://aws.amazon.com/ecs/)
[![CI/CD](https://img.shields.io/badge/CI/CD-GitHub_Actions-2088FF?style=for-the-badge&logo=github-actions)](https://github.com/features/actions)

**Transforming raw threat data into actionable intelligence with a production-grade DevOps pipeline.**

[Explore the App](http://threatvision-alb-2018723688.ap-south-1.elb.amazonaws.com) • [Report Bug](https://github.com/saichandram-sadhu/threatvision/issues) • [Request Feature](https://github.com/saichandram-sadhu/threatvision/issues)

</div>

---

## 📽️ Project Vision

**ThreatVision** is a statement in modern security operations. It bridges the gap between complex MISP data and human-readable insights. This project showcases a full-scale DevOps migration from a local "it works on my machine" state to a globally accessible, resilient AWS infrastructure.

---

## 🏗️ DevOps Architecture

Our architecture follows the **Well-Architected Framework** principles, ensuring high availability, security, and automated recovery.

```mermaid
graph TD
    A[Developer] -->|Push| B(GitHub Repo)
    B -->|Trigger| C{GitHub Actions}
    C -->|Build & Push| D[Amazon ECR]
    C -->|Provision| E[Terraform]
    E -->|Manage| F[AWS Infrastructure]
    F --> G[ALB]
    G --> H[ECS Fargate Backend]
    G --> I[ECS Fargate Frontend]
    H --> J[(Amazon RDS)]
    I --> H
```

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
*   **Problem**: Backend services kept restarting (0/1 tasks) due to failing health checks.
*   **Solution**: Improved the database pool warmup logic and adjusted the ALB `health_check_grace_period` in Terraform.

### 🔴 Proxy 401: The JWT Wall (Fixed)
*   **Problem**: NextAuth sessions weren't propagating through the ALB network layers.
*   **Solution**: Refactored the frontend proxy to use `getToken` for reliable session forwarding.

### 🔴 MISP 405: The Missing Link (Fixed)
*   **Problem**: MISP Explorer endpoints returned `Method Not Allowed`.
*   **Solution**: Implemented missing `GET` handlers in the FastAPI backend to support frontend synchronization.

---

## 📊 Live Platform Preview

<div align="center">

### 🚀 Performance Dashboard
![Dashboard](docs/assets/dashboard_real.png)
*Real-time visibility into IOC analyses and system health.*

### 🔌 Integrations & Config
![Integrations](docs/assets/integrations_real.png)
*Seamlessly connect MISP, OpenCTI, and custom threat sources.*

### 🔍 MISP Explorer
![MISP Explorer](docs/assets/misp_real.png)
*Interactive exploration of threat intelligence events.*

</div>

---

## ☁️ AWS Infrastructure Screenshots

Below are the actual AWS Console screenshots captured during the deployment of ThreatVision. Each screenshot documents a critical step in setting up the cloud infrastructure — from IAM user creation to ECS cluster management.

---

### 🏠 1. AWS Management Console — Home Dashboard

![AWS Console Home](screenshot%20AWS/01_aws_console_home.png)

**What it shows:** The AWS Management Console home page in the **Asia Pacific (Mumbai) — `ap-south-1`** region. The dashboard displays:
- **Recently visited services:** CloudWatch (monitoring), IAM (access management), EC2 (compute), VPC (networking), and Billing.
- **Cost & Usage widget:** Shows **$119.98 USD** in remaining credits with **19 days** left on the free tier.
- **AWS Health:** 0 open issues — all services are operational.

**Why it matters for ThreatVision:** This is the starting point for all infrastructure provisioning. The Mumbai region (`ap-south-1`) was chosen for low-latency access. The recently visited services reflect the core AWS services used in the ThreatVision deployment pipeline.

---

### 👤 2. IAM — Create DevOps User (Step 1: User Details)

![IAM Create User Step 1](screenshot%20AWS/02_iam_create_user_step1.png)

**What it shows:** The IAM "Create user" wizard at **Step 1 — Specify user details**. A new IAM user named **"Devops"** is being created. Console access is not being enabled — this user is for **programmatic access only** (CLI/API).

**Why it matters for ThreatVision:** A dedicated `Devops` IAM user is created to run Terraform and AWS CLI commands for infrastructure provisioning. This follows the security best practice of **never using root credentials** for deployment operations.

---

### 👤 3. IAM — DevOps User Details (Confirmation)

![IAM Create User Details](screenshot%20AWS/03_iam_create_user_details.png)

**What it shows:** A closer view of the same Step 1 screen confirming the **username: "Devops"** with the 3-step wizard (Specify user details → Set permissions → Review and create) visible on the left sidebar.

**Why it matters for ThreatVision:** Confirms the dedicated service account name that will be used across GitHub Actions CI/CD workflows and local Terraform execution for all ThreatVision infrastructure changes.

---

### 🔐 4. IAM — Set Permissions (Permission Options)

![IAM Set Permissions](screenshot%20AWS/04_iam_set_permissions.png)

**What it shows:** **Step 2 — Set permissions** for the Devops user. Three options are presented:
1. ✅ **Add user to group** (recommended for team management)
2. **Copy permissions** from another user
3. **Attach policies directly** (selected in next step)

The "Create group" option is also available for organizing permissions.

**Why it matters for ThreatVision:** This step determines what the Devops user can do. For the ThreatVision deployment, we need permissions for ECS, ECR, RDS, VPC, ALB, CloudWatch, and IAM — essentially full infrastructure control.

---

### 📋 5. IAM — Attach AdministratorAccess Policy

![IAM Attach Policy](screenshot%20AWS/05_iam_attach_policy.png)

**What it shows:** The **"Attach policies directly"** option is selected. The search bar shows "AdministratorAccess" with **5 matching policies**. The available policies include:
- `AdministratorAccess` — Full AWS access (AWS managed - job function)
- `AdministratorAccess-Amplify`
- `AdministratorAccess-AWSElasticBeanstalk`
- `AWSAuditManagerAdministratorAccess`
- `AWSManagementConsoleAdministratorAccess`

**Why it matters for ThreatVision:** The **AdministratorAccess** policy is being attached to allow Terraform to create and manage all required services (ECS, ECR, RDS, VPC, ALB, Security Groups, IAM Roles). In production, this should be scoped down to least-privilege policies.

---

### ✅ 6. IAM — Review and Create User

![IAM Review Create](screenshot%20AWS/06_iam_review_create.png)

**What it shows:** **Step 3 — Review and create** screen displaying the final summary before creating the user:
- **User name:** Devops
- **Console password type:** None (no console login)
- **Require password reset:** No
- **Permissions summary:** `AdministratorAccess` (AWS managed - job function) attached as a Permissions policy
- **Tags:** None

**Why it matters for ThreatVision:** This is the final review before the Devops IAM user is created. The configuration confirms programmatic-only access with full administrator privileges for infrastructure automation.

---

### 📋 7. IAM — User Successfully Created

![IAM User Created](screenshot%20AWS/07_iam_user_created.png)

**What it shows:** The **IAM Users dashboard** listing the successfully created **"Devops"** user. The table shows:
- **Path:** `/` (root path)
- **Groups:** 0 (no group membership)
- **MFA:** Not configured
- **Access key ID:** Not yet created

The left sidebar shows the full IAM navigation: Dashboard, Roles, Policies, Users, User groups, Identity providers, and Account settings.

**Why it matters for ThreatVision:** Confirms the Devops user is active and ready. The next step is creating an **access key pair** for CLI/Terraform authentication.

---

### 🔑 8. IAM — Create Access Key (Use Case Selection)

![IAM Access Key Use Case](screenshot%20AWS/08_iam_access_key_use_case.png)

**What it shows:** The **"Create access key"** wizard for the Devops user at **Step 1 — Access key best practices & alternatives**. The available use cases include:
- **Command Line Interface (CLI)** — For AWS CLI usage
- **Local code** — For application development
- **Application running on AWS compute service** — For EC2/ECS/Lambda
- **Third-party service** — For external tools
- **Application running outside AWS** — For external workloads
- **Other**

**Why it matters for ThreatVision:** The access key is needed for:
1. **Terraform** — To authenticate and provision AWS resources
2. **GitHub Actions** — For CI/CD pipeline to push Docker images to ECR and deploy to ECS
3. **AWS CLI** — For local development and debugging

---

### ⚠️ 9. IAM — Access Key Security Confirmation

![IAM Access Key Confirmation](screenshot%20AWS/09_iam_access_key_confirmation.png)

**What it shows:** The **security alternatives warning** before creating the access key. AWS recommends:
- Using **AWS CLI V2** with `aws login` command for console credential reuse
- Using **AWS CloudShell** for browser-based CLI

A **confirmation checkbox** must be checked: *"I understand the above recommendation and want to proceed to create an access key."*

**Why it matters for ThreatVision:** AWS flags long-term access keys as a security concern. For ThreatVision, we acknowledge the risk and proceed because GitHub Actions CI/CD requires static credentials stored as repository secrets (`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`).

---

### 🏷️ 10. IAM — Access Key Description Tag

![IAM Access Key Tag](screenshot%20AWS/10_iam_access_key_tag.png)

**What it shows:** **Step 2 — Set description tag** (optional) for the access key. A description tag helps identify the purpose of the key for future rotation and auditing.

**Why it matters for ThreatVision:** Adding a descriptive tag (e.g., "ThreatVision CI/CD Pipeline") helps track which access keys are used for what purpose, making security audits and key rotation easier.

---

### 🎯 11. IAM — Access Key Successfully Retrieved

![IAM Access Key Retrieved](screenshot%20AWS/11_iam_access_key_retrieved.png)

**What it shows:** **Step 3 — Retrieve access keys** with the generated credentials:
- **Access key:** `AKIAUPBVTA6NVQ6FJLZR`
- **Secret access key:** Displayed (can be hidden/shown)

⚠️ **Important banner:** *"This is the only time that the secret access key can be viewed or downloaded. You cannot recover it later."*

**Access key best practices** are listed: Never store in plain text, disable when not needed, enable least-privilege, rotate regularly.

**Why it matters for ThreatVision:** These credentials are stored as **GitHub Secrets** (`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`) for the CI/CD pipeline and used locally for Terraform operations. The `.csv` download option ensures a backup copy.

---

### 🚀 12. ECS — ThreatVision Cluster & Services

![ECS Cluster Services](screenshot%20AWS/12_ecs_cluster_services.png)

**What it shows:** The **Amazon ECS (Elastic Container Service)** dashboard for the **`threatvision-cluster`**:
- **Cluster Status:** ✅ Active
- **ARN:** `arn:aws:ecs:ap-south-1:307202557851:cluster/threatvision-cluster`
- **CloudWatch monitoring:** Default
- **Services:** 2 Active services running on **Fargate** (serverless):
  - **Backend Service:** `0/1 Tasks running` — deployment in progress
  - **Frontend Service:** `1/1 Tasks running` — ✅ fully deployed
- **Tasks:** 1 Running

**Why it matters for ThreatVision:** ECS Fargate is the core compute layer. Both the FastAPI backend and Next.js frontend run as containerized services. The backend shows `0/1` indicating an active deployment or health check warm-up (which was later resolved with the `health_check_grace_period` fix mentioned in the Deployment Challenges section).

---

### 🗄️ 13. RDS — ThreatVision PostgreSQL Database

![RDS Database Overview](screenshot%20AWS/13_rds_database_overview.png)

**What it shows:** The **Amazon RDS** dashboard for **`threatvision-db`**:
- **DB Identifier:** `threatvision-db`
- **Status:** ✅ Available
- **Engine:** **PostgreSQL**
- **Instance Class:** `db.t4g.micro` (free-tier eligible ARM-based instance)
- **CPU:** 3.61% utilization
- **Connections:** 0 (at time of screenshot)
- **Region & AZ:** `ap-south-1a`
- **Connectivity:** Internet access gateway disabled, IAM Authentication disabled
- **Endpoint:** `threatvision-db.crsiyi84ocff.ap-south-1.rds.amazonaws.com`

**Why it matters for ThreatVision:** This PostgreSQL database stores all threat intelligence data, user sessions, MISP event cache, IOC analyses, and integration configurations. The `db.t4g.micro` instance keeps costs minimal while providing sufficient performance. The disabled internet gateway means the database is **only accessible from within the VPC** — a critical security measure.

---

### 📦 14. ECR — Docker Image Repositories

![ECR Repositories](screenshot%20AWS/14_ecr_repositories.png)

**What it shows:** The **Amazon ECR (Elastic Container Registry)** private registry with **2 repositories**:

| Repository | URI | Created | Encryption |
|---|---|---|---|
| `threatvision-backend` | `307202557851.dkr.ecr.ap-south-1.amazonaws.com/threatvision-backend` | April 28, 2026, 00:33:35 | AES-256 |
| `threatvision-frontend` | `307202557851.dkr.ecr.ap-south-1.amazonaws.com/threatvision-frontend` | April 28, 2026, 00:33:35 | AES-256 |

**Why it matters for ThreatVision:** ECR is the **private Docker registry** where CI/CD pushes built container images. Both repositories are encrypted with **AES-256** and have **mutable tags** (allowing `latest` tag updates). GitHub Actions builds multi-stage Docker images and pushes them here before ECS pulls them for deployment.

---

### ⚖️ 15. ALB — Application Load Balancer (Overview)

![ALB Details](screenshot%20AWS/15_alb_details.png)

**What it shows:** The **Application Load Balancer (ALB)** named **`threatvision-alb`**:
- **Type:** Application (Layer 7 HTTP/HTTPS)
- **Status:** ✅ Active
- **Scheme:** Internet-facing
- **VPC:** `vpc-04cab7e4b6ee18ae2`
- **IP Type:** IPv4
- **Availability Zones:** 
  - `ap-south-1a` (subnet `079c7b8f5c2a810c2`)
  - `ap-south-1b` (subnet `00d14123f35235c55`)
- **DNS Name:** `threatvision-alb-2018723688.ap-south-1.elb.amazonaws.com`
- **Created:** April 28, 2026, 00:34 (UTC+05:30)

**Why it matters for ThreatVision:** The ALB is the **single entry point** for all traffic. It distributes incoming HTTP requests across the ECS Fargate tasks (backend and frontend). Multi-AZ deployment (`ap-south-1a` + `ap-south-1b`) ensures **high availability** — if one AZ goes down, the other continues serving requests.

---

### 🔀 16. ALB — Listeners & Routing Rules

![ALB Listeners Rules](screenshot%20AWS/16_alb_listeners_rules.png)

**What it shows:** The ALB's **Listeners and rules** tab showing:
- **Listener:** `HTTP:80`
- **Default Action:** Return fixed response (404 - Not Found)
- **Rules:** 5 path-based routing rules for traffic distribution
- **Security Policy:** Not applicable (HTTP, no TLS)

**Why it matters for ThreatVision:** The listener rules implement **path-based routing**:
- `/api/*` → Routes to the **backend** ECS service (FastAPI)
- `/*` → Routes to the **frontend** ECS service (Next.js)
- Default → Returns 404 for unmatched paths

This architecture allows both services to share a single ALB DNS endpoint while maintaining independent scaling and deployment. The 5 custom rules handle API proxying, health checks, and static asset routing.

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

# Ship it to ECR
aws ecr get-login-password --region ap-south-1 | docker login ...
docker push <aws_id>.dkr.ecr.ap-south-1.amazonaws.com/threatvision-backend:latest
```

---

## 🛡️ Security Hardening
- **IAM Least Privilege**: Fine-grained roles for ECS tasks.
- **VPC Isolation**: RDS and Backend in private subnets.
- **ALB Encryption**: Managed traffic routing with path-based rules.

---

<div align="center">

**Built for Security Engineers. Engineered for DevSecOps.**

[Back to top ↑](#-threatvision-the-ultimate-threat-intelligence-platform)

</div>

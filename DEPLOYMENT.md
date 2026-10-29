# Docker & Cloud Deployment Guide

This guide details how to build, run, and deploy **ApexFinance** using Docker locally or on cloud providers (Google Cloud Run, AWS App Runner / ECS, Azure Container Apps, DigitalOcean).

---

## 1. Quick Local Deployment with Docker

### Prerequisites
- Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) (ensure Docker daemon is running).

### Option A: Using Docker Compose (Recommended)
This automatically builds the container, binds port `5000`, and sets up a persistent storage volume (`finance_data`) for the database:

```bash
docker compose up -d --build
```

- Check running status:
  ```bash
  docker compose ps
  ```
- View live application logs:
  ```bash
  docker compose logs -f
  ```
- Stop the container:
  ```bash
  docker compose down
  ```

### Option B: Using Plain Docker CLI

1. **Build the image:**
   ```bash
   docker build -t apex-finance:latest .
   ```

2. **Run the container with persistent data volume:**
   ```bash
   docker run -d \
     --name apex-finance-app \
     -p 5000:5000 \
     -v apex_data:/app/data \
     -e SECRET_KEY="your-production-secret-key" \
     apex-finance:latest
   ```

3. **Access the Application:**
   Open **[http://localhost:5000](http://localhost:5000)** in your browser.

---

## 2. Deploy to Google Cloud Run (Serverless Container)

Google Cloud Run allows deploying containerized applications with automated HTTPS, zero-scaling cost, and simple deployments.

1. **Authenticate with Google Cloud:**
   ```bash
   gcloud auth login
   gcloud config set project YOUR_PROJECT_ID
   ```

2. **Deploy directly from source:**
   ```bash
   gcloud run deploy apex-finance \
     --source . \
     --platform managed \
     --region us-central1 \
     --allow-unauthenticated \
     --port 5000
   ```
   *Google Cloud Run will automatically build the container and provide you with a live HTTPS URL.*

---

## 3. Deploy to AWS App Runner

AWS App Runner provides fully managed container deployments directly from your code repository or container image.

1. **Build and push image to Amazon ECR:**
   ```bash
   # Log in to ECR
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

   # Create repository
   aws ecr create-repository --repository-name apex-finance

   # Tag and push
   docker tag apex-finance:latest YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/apex-finance:latest
   docker push YOUR_ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/apex-finance:latest
   ```

2. **Create App Runner Service:**
   - In AWS Console ➔ Search **App Runner** ➔ **Create Service**.
   - Select **Container registry** ➔ **Amazon ECR** ➔ choose `apex-finance:latest`.
   - Set Port: `5000`.
   - Click **Deploy**.

---

## 4. Deploy to Azure Container Apps

1. **Log in to Azure CLI:**
   ```bash
   az login
   ```

2. **Create Resource Group and Container App Environment:**
   ```bash
   az group create --name apex-finance-rg --location eastus
   az containerapp env create --name apex-env --resource-group apex-finance-rg --location eastus
   ```

3. **Build and deploy:**
   ```bash
   az containerapp up \
     --name apex-finance \
     --resource-group apex-finance-rg \
     --environment apex-env \
     --source . \
     --target-port 5000 \
     --ingress external
   ```

---

## 5. Deploy to DigitalOcean App Platform

1. Commit and push the project to GitHub or GitLab.
2. In DigitalOcean Console: Click **Create** ➔ **Apps**.
3. Link your repository. DigitalOcean will automatically detect the `Dockerfile`.
4. Set HTTP Port to `5000`.
5. Click **Launch App**.

---

## Health Check Endpoint

All container orchestrators (Kubernetes, AWS ECS, GCP Cloud Run, Docker) can use the built-in health check endpoint:
- **URL:** `/api/health`
- **Method:** `GET`
- **Expected Status:** `200 OK`
- **Payload:** `{"status": "healthy", "service": "Personal Finance Manager", "version": "1.0.0"}`

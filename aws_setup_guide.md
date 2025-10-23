# Step-by-Step Guide: Deploying a Python Scraper on AWS Fargate

This guide provides detailed instructions for deploying the Python web scraper as a containerized application on AWS Fargate.

## Part 1: Build and Push the Docker Image to ECR

**Objective:** Package the application into a Docker image and store it in AWS Elastic Container Registry (ECR).

1.  **Install Docker:** Make sure you have Docker installed on your local machine.
2.  **Create an ECR Repository:**
    *   Go to the AWS Management Console and navigate to **Elastic Container Registry (ECR)**.
    *   Click **Create repository**.
    *   Choose **Private**.
    *   Give it a name (e.g., `youtube-scraper`).
    *   Click **Create repository**.
3.  **Build the Docker Image:**
    *   Open a terminal in the root of your project (where the `Dockerfile` is).
    *   Run the build command: `docker build -t youtube-scraper .`
4.  **Authenticate Docker to ECR:**
### Detailed Steps for Docker Authentication

This step requires the **AWS CLI (Command Line Interface)** to be installed and configured.

1.  **Install the AWS CLI:**
    *   If you don't have it, follow the official [AWS CLI installation guide](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html).

2.  **Configure the AWS CLI:**
    *   You will need an **Access Key ID** and a **Secret Access Key** for an IAM user in your AWS account.
    *   Open a terminal and run `aws configure`.
    *   Enter your credentials when prompted:
        ```bash
        AWS Access Key ID [None]: YOUR_ACCESS_KEY
        AWS Secret Access Key [None]: YOUR_SECRET_KEY
        Default region name [None]: your-region (e.g., us-east-1)
        Default output format [None]: json
        ```

3.  **Run the Docker Login Command:**
    *   Once the AWS CLI is configured, you can run the command from the ECR console. It will log your Docker client into your ECR registry using a temporary password.

---
    *   In the ECR console, select your repository and click **View push commands**.
    *   Copy and run the first command, which will look something like this:
        ```bash
        aws ecr get-login-password --region your-region | docker login --username AWS --password-stdin your-aws-account-id.dkr.ecr.your-region.amazonaws.com
        ```
5.  **Tag and Push the Image:**
    *   Follow the remaining push commands from the ECR console. They will be similar to this:
        ```bash
        docker tag youtube-scraper:latest your-aws-account-id.dkr.ecr.your-region.amazonaws.com/youtube-scraper:latest
        docker push your-aws-account-id.dkr.ecr.your-region.amazonaws.com/youtube-scraper:latest
        ```

## Part 2: Create an ECS Cluster

**Objective:** Create a logical grouping for our containerized application.

1.  Go to the **Elastic Container Service (ECS)** in the AWS console.
2.  Click **Create cluster**.
3.  Give the cluster a name (e.g., `scraper-cluster`).
4.  Under **Networking**, choose a VPC and subnets. The defaults are usually fine for a new project.
5.  For **Infrastructure**, select **AWS Fargate (serverless)**.
6.  Click **Create**.

## Part 3: Create a Task Definition

**Objective:** Create a blueprint for our application container.

1.  In the ECS console, go to **Task Definitions** and click **Create new task definition**.
2.  Give it a name (e.g., `scraper-task`).
3.  For **Launch type**, select **AWS Fargate**.
4.  For **Operating system/Architecture**, choose **Linux/X86_64**.
5.  For **Task size**, start with **0.5 vCPU** and **1GB Memory**.
6.  In the **Container details** section:
    *   **Name:** `youtube-scraper`
    *   **Image URI:** Paste the URI of the image you pushed to ECR.
    *   **Port mappings:** Add a mapping for port `80`.
7.  Click **Create**.

## Part 4: Create an Application Load Balancer (ALB)

**Objective:** Create a load balancer to distribute traffic to our container.

1.  Go to the **EC2** service in the AWS console.
2.  Under **Load Balancing**, click **Load Balancers**, then **Create Load Balancer**.
3.  Choose **Application Load Balancer**.
4.  **Configuration:**
    *   **Name:** `scraper-alb`
    *   **Scheme:** `Internet-facing`
    *   **Listeners:** It should default to HTTP on port 80.
### Analogy: A Restaurant Host and a Table

To make this easier to understand, think of it like this:

*   **Application Load Balancer (ALB):** The host at a restaurant. It's the single entry point for all incoming API requests.
*   **Target Group:** A specific table in the restaurant, reserved for customers who want to run the scraper.
*   **Fargate Task:** The chef at that table, ready to run your code.

The API request (customer) arrives at the ALB (host), which sends them to the Target Group (table), where a Fargate Task (chef) is ready to handle the request.

---
    *   **VPC and Subnets:** Choose the same VPC and at least two subnets as your cluster.
5.  **Create a Target Group:**
    *   On the next screen, for **Target group**, choose **Create target group**.
    *   **Target type:** `IP addresses`
    *   **Name:** `scraper-tg`
    *   **Port:** `80`
    *   **VPC:** The same as your ALB.
    *   Click **Next** and then **Create target group**.
6.  Go back to the ALB creation screen, select your new target group, and create the load balancer.

## Part 5: Create a Fargate Service

**Objective:** Run and maintain our container task.

1.  Go back to your ECS cluster and click the **Services** tab, then **Create**.
2.  **Deployment configuration:**
    *   **Launch type:** `Fargate`
    *   **Task Definition:** The `scraper-task` you created.
    *   **Service name:** `scraper-service`
    *   **Desired tasks:** `1`
3.  **Networking:**
    *   Under **Load balancing**, choose **Application Load Balancer**.
    *   Select the `scraper-alb` you created.
    *   For the **Listener**, choose port `80`.
    *   For the **Target group**, choose the `scraper-tg` you created.
4.  Click **Create**.

This will launch your container on Fargate and make it accessible through the Application Load Balancer. The next step will be to connect API Gateway to this setup.
## Part 6: Configure API Gateway to Trigger Fargate Task

**Objective:** Create an API endpoint that the frontend can call, which will trigger our Fargate service.

1.  **Create a VPC Link:**
    *   In the API Gateway console, go to **VPC Links** and click **Create**.
    *   Choose **VPC link for REST APIs**.
    *   **Name:** `scraper-vpc-link`
    *   **Target ALB:** Select the `scraper-alb` you created.
    *   Click **Create**. This can take a few minutes to provision.

2.  **Create a REST API:**
    *   In the API Gateway console, click **Create API**.
    *   Choose **REST API** (not the private one).
    *   **API name:** `ScraperAPI`
    *   Click **Create API**.

3.  **Create a Resource and Method:**
    *   Under your new API, click **Actions** and **Create Resource**.
    *   **Resource Name:** `scrape`
    *   Click **Create Resource**.
    *   With the `/scrape` resource selected, click **Actions** and **Create Method**.
    *   Choose **POST** from the dropdown and click the checkmark.

4.  **Configure the POST Method Integration:**
    *   **Integration type:** `VPC Link`
    *   **Use Proxy Integration:** Check this box.
    *   **VPC Link:** Select the `scraper-vpc-link` you created.
    *   **Endpoint URL:** This is the DNS name of your Application Load Balancer, followed by the path to your service. It will look something like `http://your-alb-dns-name/`.
    *   Click **Save**.

5.  **Enable CORS:**
    *   With the `/scrape` resource selected, click **Actions** and **Enable CORS**.
    *   Keep the default settings and click **Enable CORS and replace existing CORS headers**.

6.  **Deploy the API:**
    *   Click **Actions** and **Deploy API**.
    *   **Deployment stage:** `[New Stage]`
    *   **Stage name:** `prod`
    *   Click **Deploy**.

After deployment, you will get an **Invoke URL**. This is the public URL for your API endpoint, which you will use in your frontend application.
## Part 7: CI/CD with GitHub Actions

**Objective:** Automate the deployment of your backend and frontend.

### Frontend CI/CD (Netlify)

1.  **Push to GitHub:** Create a GitHub repository and push your `frontend` directory.
2.  **Connect to Netlify:**
    *   Log in to Netlify, click **Add new site** > **Import an existing project**.
    *   Connect to GitHub and select your repository.
3.  **Build Settings:**
    *   **Branch:** `main`
    *   **Build command:** `npm run build`
    *   **Publish directory:** `build`
4.  **Environment Variables:**
    *   Add `REACT_APP_API_URL` with your API Gateway Invoke URL.

### Backend CI/CD (GitHub Actions)

1.  **Create `.github/workflows/deploy-backend.yml`:**
    ```yaml
    name: Deploy Backend to AWS Fargate

    on:
      push:
        branches:
          - main

    jobs:
      deploy:
        runs-on: ubuntu-latest
        steps:
          - name: Checkout code
            uses: actions/checkout@v2

          - name: Configure AWS credentials
            uses: aws-actions/configure-aws-credentials@v1
            with:
              aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
              aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
              aws-region: your-region

          - name: Login to Amazon ECR
            id: login-ecr
            uses: aws-actions/amazon-ecr-login@v1

          - name: Build, tag, and push image to Amazon ECR
            env:
              ECR_REGISTRY: ${{ steps.login-ecr.outputs.registry }}
              ECR_REPOSITORY: youtube-scraper
              IMAGE_TAG: ${{ github.sha }}
            run: |
              docker build -t $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG .
              docker push $ECR_REGISTRY/$ECR_REPOSITORY:$IMAGE_TAG

          - name: Update ECS service
            uses: aws-actions/amazon-ecs-deploy-task-definition@v1
            with:
              task-definition: scraper-task
              service: scraper-service
              cluster: scraper-cluster
              wait-for-service-stability: true
    ```
2.  **Add AWS Secrets to GitHub:**
    *   In your GitHub repo, go to **Settings** > **Secrets and variables** > **Actions**.
    *   Add `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` from a new IAM user with ECR and ECS permissions.
## Part 8: Environment Variables and Secrets Management

**Objective:** Securely manage sensitive information and configuration.

### Frontend (Netlify)

*   **`REACT_APP_API_URL`**: This is the only environment variable needed for the frontend.
    *   **Value:** The **Invoke URL** from your API Gateway deployment.
    *   **How to set:** In your Netlify site dashboard, go to **Site settings** > **Build & deploy** > **Environment**.

### Backend (AWS)

*   **`AWS_ACCESS_KEY_ID`** and **`AWS_SECRET_ACCESS_KEY`**: These are the credentials for the IAM user that GitHub Actions will use to deploy to AWS.
    *   **How to set:** In your GitHub repository, go to **Settings** > **Secrets and variables** > **Actions**. Add them as repository secrets.
    *   **Security:** Never hardcode these in your workflow file. Always use GitHub secrets.

*   **Other potential secrets:** If your application grows to require other secrets (e.g., database credentials, third-party API keys), you should store them in **AWS Secrets Manager** and grant your Fargate task's IAM role permission to access them. Your Python code can then fetch these secrets at runtime.

By following this guide, you will have a fully functional, scalable, and automated deployment pipeline for both your frontend and backend.
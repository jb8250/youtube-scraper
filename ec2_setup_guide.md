# Step-by-Step Guide: Deploying a Python Scraper on AWS EC2

This guide provides detailed instructions for deploying the Python web scraper on an AWS EC2 instance.

## Part 1: Launching the EC2 Instance

1.  **Navigate to EC2:** In the AWS Management Console, go to the EC2 service.
2.  **Launch Instance:** Click the "Launch instances" button.
3.  **Name and Tags:** Give your instance a name, e.g., `youtube-scraper-server`.
4.  **Application and OS Images (AMI):**
    *   Select **Ubuntu**.
    *   Ensure the version is **Ubuntu Server 22.04 LTS**.
5.  **Instance Type:**
    *   Choose **t2.micro** (this is eligible for the Free Tier).
6.  **Key Pair (for login):**
    *   Click **Create new key pair**.
    *   **Key pair name:** `scraper-key`
    *   **Key pair type:** `RSA`
    *   **Private key file format:** `.pem`
    *   Click **Create key pair** and save the downloaded `.pem` file in a secure location.
7.  **Network Settings:**
    *   Click **Edit**.
    *   **VPC:** Use your default VPC.
    *   **Subnet:** Choose a public subnet.
    *   **Auto-assign public IP:** `Enable`.
    *   **Firewall (security groups):**
        *   Select **Create security group**.
        *   **Security group name:** `scraper-sg`
        *   **Description:** `Allows SSH and HTTP traffic`
        *   **Inbound security groups rules:**
            *   **Rule 1:**
                *   **Type:** `SSH`
                *   **Source type:** `My IP` (This will automatically fill in your current IP address).
            *   **Rule 2:**
                *   **Type:** `HTTP`
                *   **Source type:** `Anywhere` (0.0.0.0/0)
8.  **Configure Storage:**
    *   Keep the default 8 GB `gp2` root volume.
9.  **Advanced Details:**
    *   Scroll down to the **User data** field at the bottom. This is where we will put our setup script. (We will create this script in the next step).
10. **Launch Instance:**
    *   Review the summary and click **Launch instance**.

## Part 2: The User Data Script

Copy and paste the following script into the **User data** field from step 9. This script will automatically set up your server when it first launches.

```bash
#!/bin/bash
apt-get update -y
apt-get install -y python3-pip git
apt-get install -y chromium-browser chromium-chromedriver

# Clone the repository
git clone https://github.com/your-username/your-repo-name.git /app
cd /app

# Install Python dependencies
pip3 install -r requirements.txt

# Run the Flask app
python3 app.py
```

**Important:** You will need to replace `https://github.com/your-username/your-repo-name.git` with the actual URL of your GitHub repository.

## Part 3: Connecting to Your Instance

1.  **Find your Public IP:** In the EC2 console, find the "Public IPv4 address" for your instance.
2.  **Connect via SSH:** Open a terminal and run the following command, replacing the placeholders:
    ```bash
    ssh -i /path/to/your/scraper-key.pem ubuntu@your-public-ip
    ```

This will give you a command line on your EC2 instance where you can manage your application.
## Part 4: Frontend Deployment

1.  **Update the API URL:**
    *   In your `frontend/src/App.js` file, replace `YOUR_EC2_PUBLIC_IP` with the actual public IP address of your EC2 instance.
2.  **Deploy to Netlify:**
    *   Push your code to a GitHub repository.
    *   In Netlify, create a new site from your GitHub repository.
    *   **Build command:** `npm run build`
    *   **Publish directory:** `frontend/build`

## Part 5: Putting It All Together

1.  Launch your EC2 instance using the steps in Part 1 and the User Data script from Part 2.
2.  Once the instance is running, find its public IP address.
3.  Update your `frontend/src/App.js` file with the public IP.
4.  Push your frontend code to GitHub, which will trigger a deployment on Netlify.
5.  Your application should now be live!
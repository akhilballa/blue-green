# Zero-Downtime Blue-Green Deployment Framework

## 1. Project Overview

This project shows how to update a running application without making users wait, refresh, or see errors.

In normal software updates, a website or service may briefly stop while the old version is replaced by the new version. That short stop is called downtime. For real businesses, even a few seconds of downtime can cause user complaints, failed payments, lost orders, or trust issues.

This project solves that problem using a blue-green deployment method.

In simple words:

- The blue version is the current working application.
- The green version is the new version being prepared.
- Users keep using the blue version while the green version is tested.
- After green is confirmed healthy, traffic is switched to green.
- If green has a problem, traffic is quickly switched back to blue.

The goal is to make deployments safer, faster, and close to zero downtime.

## 2. Project Title

Zero-Downtime Blue-Green Deployment Framework for Containerised Microservices Using Ansible and Nginx

## 3. Why This Project Is Necessary

Modern applications are updated frequently. Teams fix bugs, add features, improve security, and release new versions. If every release causes the application to stop, users will face problems.

This project is necessary because it demonstrates how DevOps teams can:

- Update software without interrupting users.
- Test the new version before sending real users to it.
- Automatically roll back when a deployment is unhealthy.
- Reduce manual mistakes during deployment.
- Measure actual downtime instead of only saying the deployment was successful.
- Use practical DevOps tools that are common in real companies.

This is especially important for systems such as:

- E-commerce websites
- Banking or payment systems
- Healthcare portals
- Booking systems
- SaaS platforms
- Internal business tools used by employees every day

For these systems, downtime is not just a technical issue. It directly affects business, users, and reliability.

## 4. What This Project Builds

This repository contains a complete demo system with:

- A 5-service microservice application.
- A blue environment and a green environment.
- Nginx as the traffic gateway.
- Docker Compose to run all containers.
- Ansible playbooks to automate deployment.
- Health checks before switching traffic.
- Automatic rollback if the new version fails.
- Load-test scripts to measure downtime.
- Documentation for experiment results and tutorial writing.

The five demo services are:

- `catalog`
- `cart`
- `checkout`
- `payment`
- `user`

Each service exists in two colors:

- `blue-catalog`, `blue-cart`, `blue-checkout`, `blue-payment`, `blue-user`
- `green-catalog`, `green-cart`, `green-checkout`, `green-payment`, `green-user`

## 5. Tools Used and Why

### Docker

Docker runs each service in a container. A container is a small, isolated environment that contains the application and everything it needs to run.

Why Docker is used:

- It makes the application run the same way on different machines.
- It keeps services separated from each other.
- It makes blue and green copies easy to run side by side.

### Docker Compose

Docker Compose starts many containers together using one configuration file.

Why Docker Compose is used:

- The project has many services.
- Starting each service manually would be slow and error-prone.
- Compose lets us start the full system with one command.

### Nginx

Nginx receives user requests and forwards them to the active application version.

Why Nginx is used:

- It acts like the front door of the application.
- It can switch traffic from blue to green.
- It can reload configuration without fully stopping.

### Ansible

Ansible automates deployment steps.

Why Ansible is used:

- It runs the same deployment process every time.
- It checks whether the new version is healthy.
- It performs rollback automatically if something goes wrong.
- It reduces human error.

### wrk2 or wrk

These tools generate many requests to simulate real users.

Why load testing is used:

- A deployment may look successful when only one person tests it.
- Real applications must work while many users are using them.
- Load testing helps measure whether users would notice downtime.

## 6. System Architecture

```text
User or load-test tool
        |
        v
http://localhost:8080
        |
        v
      Nginx
        |
        +-- Active color receives traffic
        |      Example: blue services
        |
        +-- Inactive color waits ready
               Example: green services
```

When blue is active:

```text
User request -> Nginx -> blue services
```

When green is deployed successfully:

```text
User request -> Nginx -> green services
```

The user still visits the same URL. The switch happens behind the scenes.

## 7. Folder Structure

```text
.
+-- app/
|   +-- Dockerfile
|   +-- service.py
|
+-- ansible/
|   +-- inventory/
|   +-- playbooks/
|   +-- roles/
|
+-- docs/
|   +-- architecture.md
|   +-- experiment-plan.md
|   +-- tutorial-article.md
|
+-- nginx/
|   +-- conf.d/
|
+-- results/
|   +-- README.md
|
+-- scripts/
|   +-- bootstrap.sh
|   +-- smoke_test.sh
|   +-- run_load_test.sh
|   +-- deploy_green.sh
|   +-- rollback_blue.sh
|   +-- wrk2_downtime.lua
|
+-- docker-compose.yml
+-- Makefile
+-- requirements-dev.txt
+-- README.md
```

### What each folder does

`app/`

Contains the demo microservice code. The same Python service is reused for all five services.

`ansible/`

Contains deployment automation. This is where the blue-green switching logic lives.

`nginx/`

Contains Nginx configuration. Nginx decides whether traffic goes to blue or green.

`scripts/`

Contains helper scripts for starting the project, testing it, and running load tests.

`docs/`

Contains supporting documentation for architecture, experiments, and article writing.

`results/`

Stores load-test results.

## 8. Prerequisites

Before running the project, install these tools.

### Required

- Docker Desktop
- Docker Compose v2
- Python 3.10 or newer
- Ansible

### Optional

- `wrk2` for better load testing
- `wrk` as a fallback load-test tool
- `jq` for prettier JSON output

## 9. Step-by-Step Setup

### Step 1: Open the project folder

Open a terminal and go to this folder:

```bash
cd /Users/balla/Desktop/blue
```

Why this is necessary:

The commands in this README assume you are running them from the project root folder.

### Step 2: Install Ansible

Run:

```bash
python3 -m pip install --user -r requirements-dev.txt
```

Why this is necessary:

Ansible is the tool that performs the deployment, health checks, Nginx switch, and rollback.

Check that Ansible is installed:

```bash
./scripts/ansible_playbook.sh --version
```

If this command prints a version number, Ansible is ready. The wrapper first tries `ansible-playbook` from your PATH, then checks `$HOME/.local/bin/ansible-playbook`.

### Step 3: Make sure Docker is running

Start Docker Desktop before running the project.

Check Docker:

```bash
docker --version
docker compose version
```

Why this is necessary:

The application services run inside Docker containers. If Docker is not running, the project cannot start.

### Step 4: Start the complete project

Run:

```bash
make up
```

What this does:

- Builds the demo application image.
- Starts all blue services.
- Starts all green services.
- Starts the Nginx gateway.
- Sets blue as the default active version.

Why this is necessary:

Both blue and green versions must be available so the system can switch between them without stopping the application.

Expected result:

You should see Docker containers starting. At the end, the application should be available at:

```text
http://localhost:8080
```

### Step 5: Check that the system is working

Run:

```bash
make smoke
```

What this does:

It checks the main gateway and all five service health endpoints.

Why this is necessary:

Before deployment testing, we must confirm that the base system is healthy.

Expected result:

You should see messages like:

```text
checking catalog... ok
checking cart... ok
checking checkout... ok
checking payment... ok
checking user... ok
smoke test passed
```

### Step 6: View the current application response

Run:

```bash
curl http://localhost:8080/api/catalog
```

If you have `jq` installed, use:

```bash
curl -s http://localhost:8080/api/catalog | jq
```

What to look for:

The response should include:

```json
"color": "blue"
```

Why this is necessary:

This proves that Nginx is currently sending user traffic to the blue version.

## 10. Deploying the Green Version

Run:

```bash
make deploy-green
```

What this does:

1. Ansible starts or checks the green containers.
2. Ansible verifies that every green service is healthy.
3. Ansible updates the Nginx upstream configuration.
4. Nginx reloads without shutting down the gateway.
5. Ansible checks the public routes again.
6. The project records green as the active color.

Why this is necessary:

This is the main purpose of the project. It shows how a new version can be released only after health checks pass.

After deployment, verify the active color:

```bash
curl -s http://localhost:8080/api/catalog | jq
```

Expected result:

```json
"color": "green"
```

If you do not have `jq`, run:

```bash
curl http://localhost:8080/api/catalog
```

and look for `green` in the output.

## 11. Switching Back to Blue

Run:

```bash
make deploy-blue
```

What this does:

It performs the same health-gated deployment process, but switches traffic back to the blue services.

Why this is necessary:

In a real project, teams often need to switch between versions during testing, rollback, or repeated release experiments.

Check again:

```bash
curl -s http://localhost:8080/api/catalog | jq
```

Expected result:

```json
"color": "blue"
```

## 12. Manual Rollback

If the green version has a problem and you want to return to blue, run:

```bash
make rollback-blue
```

Or run the Ansible playbook directly:

```bash
./scripts/ansible_playbook.sh ansible/playbooks/rollback.yml -e rollback_color=blue
```

Why rollback is necessary:

No deployment method can guarantee that every new version is perfect. Rollback gives the team a fast recovery path when a release fails.

## 13. Measuring Downtime

The project includes a load-test script. It sends many requests while deployment is happening.

### Terminal 1: Start load testing

Run:

```bash
make load-test
```

This uses the default settings:

- URL: `http://localhost:8080/api/catalog`
- Duration: `60s`
- Request rate: `100`

You can also run it manually:

```bash
scripts/run_load_test.sh http://localhost:8080/api/catalog 60s 100
```

### Terminal 2: Deploy while load is running

While the load test is still running, open another terminal and run:

```bash
make deploy-green
```

or:

```bash
make deploy-blue
```

Why this is necessary:

The project is not only about switching traffic. It is also about proving whether users experience errors during that switch.

### Where results are stored

Load-test output is saved inside:

```text
results/
```

The result file includes:

- total responses
- failed responses
- configured request rate
- estimated failure window in milliseconds
- latency statistics from wrk2 or wrk

The most important value is failed responses. If this is zero or very low, the deployment had little or no visible impact on users.

## 14. Important URLs

Open these in a browser or test with `curl`.

```text
http://localhost:8080/health
http://localhost:8080/api/catalog
http://localhost:8080/api/cart
http://localhost:8080/api/checkout
http://localhost:8080/api/payment
http://localhost:8080/api/user
```

Each service response shows:

- service name
- active color
- service version
- hostname
- request path
- downstream health information

## 15. Main Commands

```bash
make up
```

Starts the full project.

```bash
make smoke
```

Checks whether the gateway and services are healthy.

```bash
make deploy-green
```

Switches traffic to green after health checks.

```bash
make deploy-blue
```

Switches traffic to blue after health checks.

```bash
make rollback-blue
```

Rolls traffic back to blue.

```bash
make load-test
```

Runs a load test and saves results.

```bash
make ps
```

Shows running containers.

```bash
make logs
```

Shows container logs.

```bash
make down
```

Stops the project.

```bash
make clean
```

Stops containers and removes orphan containers.

## 16. How the Blue-Green Switch Works Internally

The active color is controlled by this file:

```text
nginx/conf.d/active-upstreams.conf
```

When blue is active, Nginx points to:

```text
blue-catalog
blue-cart
blue-checkout
blue-payment
blue-user
```

When green is active, Nginx points to:

```text
green-catalog
green-cart
green-checkout
green-payment
green-user
```

The Ansible role that manages this is:

```text
ansible/roles/blue_green_switcher/
```

The main deployment playbook is:

```text
ansible/playbooks/deploy-blue-green.yml
```

The rollback playbook is:

```text
ansible/playbooks/rollback.yml
```

## 17. Why This Approach Reduces Downtime

This approach reduces downtime because the new version is prepared before users are sent to it.

Traditional deployment:

```text
Stop old version -> start new version -> hope it works
```

Blue-green deployment:

```text
Keep old version running -> start new version separately -> test new version -> switch traffic
```

The second approach is safer because users continue using the old version until the new version is ready.

## 18. What Makes This Project Valuable

This project is useful because it combines several real DevOps ideas:

- Deployment automation
- Containerised microservices
- Reverse proxy routing
- Health checks
- Rollback strategy
- Load testing
- Downtime measurement
- Reusable Ansible role design

It is not just a sample application. It demonstrates a deployment framework that can be adapted for larger systems.

## 19. Expected Deliverables Covered

### Ansible role library for blue-green switchover

Location:

```text
ansible/roles/blue_green_switcher/
```

This role is reusable and handles health checks, switching, and rollback.

### Demo 5-service microservice application

Location:

```text
app/
docker-compose.yml
```

The project runs five services in blue and green versions.

### Load-test harness and measured downtime results

Location:

```text
scripts/run_load_test.sh
scripts/wrk2_downtime.lua
results/
```

The scripts generate traffic and record downtime-related output.

### Rollback playbook with configurable health-check thresholds

Location:

```text
ansible/playbooks/rollback.yml
ansible/roles/blue_green_switcher/defaults/main.yml
```

Health-check values can be changed in the role defaults.

### Tutorial article

Location:

```text
docs/tutorial-article.md
```

This file contains a draft article suitable for a practitioner-style publication.

## 20. Troubleshooting

### Problem: `docker` command not found

Cause:

Docker is not installed or not available in the terminal.

Fix:

Install Docker Desktop and restart the terminal.

### Problem: Docker is installed but containers do not start

Cause:

Docker Desktop may not be running.

Fix:

Open Docker Desktop and wait until it is fully started. Then run:

```bash
make up
```

### Problem: `ansible-playbook` command not found

Cause:

Ansible is not installed, or it is installed in a user-local folder that is not on your PATH.

Fix:

```bash
python3 -m pip install --user -r requirements-dev.txt
```

Then verify:

```bash
./scripts/ansible_playbook.sh --version
```

### Problem: Port `8080` is already in use

Cause:

Another application is already using port 8080.

Fix:

Stop the other application or change the port mapping in `docker-compose.yml`.

Current mapping:

```yaml
ports:
  - "8080:80"
```

Example alternative:

```yaml
ports:
  - "8081:80"
```

Then use:

```text
http://localhost:8081
```

### Problem: `wrk2` is not installed

Cause:

`wrk2` is optional.

Fix:

The script will try to use `wrk` if available. If neither tool is installed, install one of them or skip the load-test step.

### Problem: Deployment fails and rolls back

Cause:

One or more health checks failed.

Fix:

Check logs:

```bash
make logs
```

Check running containers:

```bash
make ps
```

Then run the smoke test:

```bash
make smoke
```

## 21. Clean Shutdown

When you are finished, stop the project:

```bash
make down
```

Why this is necessary:

It stops the containers and frees system resources.

If you want a stronger cleanup:

```bash
make clean
```

## 22. Suggested Demonstration Flow

Use this sequence when presenting the project:

1. Explain that blue is the current version and green is the new version.
2. Run `make up`.
3. Run `make smoke`.
4. Show that the current response contains `"color": "blue"`.
5. Run `make deploy-green`.
6. Show that the response now contains `"color": "green"`.
7. Run a load test.
8. Switch back with `make deploy-blue`.
9. Show the result file in `results/`.
10. Explain how rollback protects users if the new version fails.

## 23. Conclusion

This project demonstrates a practical zero-downtime deployment workflow. It keeps the current version running, prepares the new version separately, checks health before switching, reloads Nginx to move traffic, and supports rollback if something goes wrong.

The main lesson is simple:

Do not replace a working application blindly. Prepare the new version, test it, switch traffic carefully, and measure whether users were affected.

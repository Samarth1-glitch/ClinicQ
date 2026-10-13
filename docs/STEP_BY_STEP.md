# ClinicQ — Step-by-Step Guide (code → full marks)

Follow the phases in order. Every phase tells you which rubric module (M1–M10) it earns and which
screenshots to capture. Keep a folder called `screenshots/` (do **not** commit secrets in it).

## Phase 0 — Install the tools (once)

| Tool | Why | Check |
|---|---|---|
| Git | version control | `git --version` |
| Docker Desktop (or Docker Engine) | containers | `docker --version` |
| Python 3.12+ | backend + tests | `python --version` |
| Node 22 + npm | frontend | `node --version` |
| kubectl | talk to Kubernetes | `kubectl version --client` |
| Helm 3 | package manager for Kubernetes | `helm version` |
| kind | **free** local Kubernetes | `kind version` |
| Terraform ≥ 1.5 | infrastructure as code (free CLI) | `terraform version` |
| AWS CLI v2 | credentials + kubeconfig | `aws --version` |

On Windows, install **kind** from PowerShell with:

```powershell
winget install Kubernetes.kind
```

Close and reopen PowerShell, then verify with `kind version`. If PowerShell still says `kind` is not
recognized, check that `kind.exe` is on your `PATH` (`Get-Command kind`) or install it from the
[official kind installation instructions](https://kind.sigs.k8s.io/docs/user/quick-start/#installation).
Start Docker Desktop before creating a cluster; kind uses Docker to run its Kubernetes nodes.

## Phase 1 — Run the app locally (M1, M4)

```bash
cd clinicq
docker compose up --build
```

1. Open http://localhost:3000 and http://localhost:8000/docs.
2. In another terminal run `./scripts/seed.sh http://localhost:8000`, refresh the browser.
3. Book an appointment in the UI, then check the patient in and mark it done.

**Screenshots:** browser at `localhost:3000` with data (M1, M4) · terminal showing `docker compose up --build`
running (M4) · Swagger page (M1).

## Phase 2 — Tests (M2)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
pytest -v
ruff check .
```

**Screenshot:** `pytest -v` output, all green (24 tests).

## Phase 3 — Git and GitHub (M3)

1. Create an empty **public** repository on GitHub (no README, no .gitignore). Name it e.g. `clinicq`.
2. From the project root:
   ```bash
   ./scripts/git-bootstrap.sh                 # creates 16 meaningful commits
   git remote add origin https://github.com/<you>/clinicq.git
   git push -u origin main
   ```
3. Replace `OWNER` in `helm/clinicq/values.yaml` with your **lowercase** GitHub username, then commit:
   `git commit -am "deploy: set GHCR image owner in Helm values" && git push`

**Screenshot:** the GitHub commit history page (10+ commits).
Before pushing, run `git log -p | grep -i -E "AKIA|secret"` — nothing AWS-related should appear.

## Phase 4 — CI/CD and security scan (M5, M6)

1. Push to `main`. Open the **Actions** tab. Jobs: *Test*, *Terraform validate*, *Helm lint*, then
   *Build, scan and push* for backend and frontend. The optional *Deploy* job is skipped until you opt in (Phase 7).
2. Fix anything red (see Troubleshooting below), push again until the run is green.
3. Open the repo → **Packages**. Click each package → *Package settings* → *Change visibility* → **Public**
   (so Kubernetes can pull without credentials). Tags are the full commit SHA.

**Screenshots / links:** the green run URL · the Trivy step output (expand the log) · each GHCR package page
showing the SHA tag.
**Trivy write-up (2–3 sentences, example):** *"Trivy scanned the OS packages and Python/Node libraries inside
the backend and frontend images for known CVEs. It reported no fixable HIGH or CRITICAL vulnerabilities, so the
gate passed and the images were pushed. Unfixed CVEs are ignored on purpose because nothing can be done until
upstream publishes a patch."* Use your real result.

If Trivy fails on a real CVE: bump the base image or the vulnerable package, push again.

## Phase 5 — Local Kubernetes for free: Helm, Ingress, HPA, monitoring (M8, M9)

Do all the Kubernetes work on **kind** first. It costs nothing and gives you the same screenshots.

```bash
./scripts/setup-kind.sh          # cluster + ingress-nginx + metrics-server + Prometheus/Grafana + ClinicQ
```

Add `127.0.0.1 clinicq.local` to your hosts file (Windows: `C:\Windows\System32\drivers\etc\hosts`,
needs admin), then open http://clinicq.local and run `./scripts/seed.sh http://clinicq.local`.

```bash
kubectl get pods -n clinicq          # all Running, 2 backend + 2 frontend + postgres
kubectl get svc  -n clinicq
kubectl get ingress,hpa -n clinicq
helm list -n clinicq
```

**Monitoring**
```bash
kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090   # Status → Targets
kubectl port-forward -n monitoring svc/monitoring-grafana 3001:80                   # admin / clinicq-admin
kubectl port-forward -n clinicq svc/clinicq-backend 8000:8000 & curl localhost:8000/metrics | head -30
```
In Prometheus *Targets*, find `serviceMonitor/clinicq/clinicq-backend` = **UP**. In Grafana open
**Dashboards → ClinicQ Overview** (create some bookings in the UI first so panels have data).

**HPA demo** — terminal 1: `kubectl get hpa -n clinicq -w` · terminal 2: `./scripts/load-test.sh`.
Replicas grow past 2 once CPU passes 60 % of the request. Stop with Ctrl+C.

**Troubleshooting labs** — `kubectl apply -f troubleshooting/broken-image.yaml` and
`broken-service.yaml`; the steps to investigate and fix are in the comments at the top of each file.

**Screenshots:** `kubectl get pods`, `get svc`, `helm list`, browser at the Ingress hostname (M8) ·
`/metrics` output, Prometheus Targets UP, Grafana dashboard with populated panels (M9).

## Phase 6 — Terraform on AWS (M7) — the only part that can cost money

### Do I really need AWS? Yes — but only briefly

The rubric wants real VPC + EKS output, so you need an AWS account. **Terraform itself is free** (no
"Terraform account" is needed; HashiCorp Cloud is optional and not used here). The cost comes from AWS.
EKS has no always-free tier, so the strategy is to **run it for as short a time as possible**.

Rough cost in `ap-south-1` while it is running (check the AWS Pricing Calculator; prices change):

| Item | Approx. |
|---|---|
| EKS control plane | ~$0.10 / hour |
| NAT gateway | ~$0.05 / hour + data |
| 2 × t3.medium **Spot** nodes | ~$0.04 / hour total |
| Load balancer (for Ingress) | ~$0.025 / hour |
| **Total** | **≈ $0.25–0.35 per hour → about $1 for a 3-hour session** |

**Ways to pay nothing or close to it**
- Create a new AWS account and look at **Billing → Credits**: AWS has been giving new accounts promotional
  credits. Check what your account shows and which services they cover; I can't verify current terms.
- Ask your instructor/college about **AWS Academy / AWS Educate** or student credits. Learner-lab style
  sandboxes can restrict IAM roles, so confirm EKS works there before relying on it.
- If neither applies, the one-session plan below costs roughly the price of a coffee.

### The one-session plan

**Before you start (5 min)** — protect yourself from surprise bills:
1. Create an AWS account (needs a card; use region **Asia Pacific (Mumbai) ap-south-1**).
2. **Billing → Budgets**: create a *zero-spend* or $5 budget with an email alert.
3. Don't use the root user for work: IAM → create user `terraform-admin` with `AdministratorAccess`
   (fine for a short-lived demo account), create an access key, then run `aws configure`. These keys live only in
   `~/.aws/credentials` — **never in the repo**.
4. Finish Phases 1–5 first so the AWS session is only for capturing proof.

**Session**
```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
terraform fmt -recursive
terraform init
terraform plan -out tfplan            # screenshot the plan (M7: non-empty, no errors)
terraform apply tfplan                # ~15–20 min
$(terraform output -raw configure_kubectl)
kubectl get nodes
```
Screenshot the AWS Console: **VPC** (your VPC + 2 public subnets) and **EKS** (cluster Active, node group) in
`ap-south-1` (M7).

Optional but recommended — deploy the app on EKS (the same screenshots as Phase 5, from the real cluster):
```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm upgrade --install ingress-nginx ingress-nginx/ingress-nginx -n ingress-nginx --create-namespace
helm repo add metrics-server https://kubernetes-sigs.github.io/metrics-server/
helm upgrade --install metrics-server metrics-server/metrics-server -n kube-system
helm upgrade --install monitoring prometheus-community/kube-prometheus-stack -n monitoring --create-namespace \
  -f monitoring/kube-prometheus-stack-values.yaml
kubectl apply -f monitoring/dashboard-configmap.yaml
kubectl apply -f k8s/namespace.yaml
helm upgrade --install clinicq ./helm/clinicq -n clinicq --set serviceMonitor.enabled=true --wait --timeout 10m
kubectl get svc -n ingress-nginx      # EXTERNAL-IP hostname of the load balancer → open it in the browser
```
(`values.yaml` already points at your GHCR images because you set `OWNER` in Phase 3.)

**Tear down — do not skip, and do it in this order** (leftover load balancers block `terraform destroy`):
```bash
helm uninstall clinicq -n clinicq
kubectl delete pvc --all -n clinicq
helm uninstall ingress-nginx -n ingress-nginx
helm uninstall monitoring -n monitoring
sleep 120                              # let AWS remove the load balancer
cd terraform && terraform destroy      # screenshot "Destroy complete!"
```
Afterwards open the AWS Console and confirm: no EKS cluster, no NAT gateways, no load balancers, no unattached
EBS volumes, no Elastic IPs in `ap-south-1`. Then delete the IAM access key.

## Phase 7 — Optional: let the pipeline deploy (bonus for the live demo)

Only while the cluster exists. In GitHub → Settings → *Secrets and variables → Actions*:
secrets `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`; variables `DEPLOY_ENABLED=true`,
`EKS_CLUSTER_NAME=clinicq-eks`, `AWS_REGION=ap-south-1`. Push a commit → the *Deploy* job runs Helm with the new
SHA tag. Set `DEPLOY_ENABLED` back to `false` (and delete the secrets) after the demo.
If your demo is on kind instead, show the same flow by running `helm upgrade` with the new tag by hand.

## Phase 8 — Final demo script (M10, ~10 min)

1. Show the app, create an appointment, watch the live queue.
2. Swagger: create/read/update/delete one record. Show the table: `kubectl exec -n clinicq statefulset/clinicq-postgres -- psql -U clinicq -c 'select * from appointments;'`
3. Make a visible change (e.g. change the sidebar tagline in `frontend/src/App.jsx`), `git commit`, `git push`.
4. Show the Actions run: tests → Trivy → push → (deploy). Show the SHA-tagged package in GHCR.
5. Show the Terraform code and your saved AWS/plan/destroy screenshots.
6. `kubectl get pods,svc,hpa -n clinicq`, `helm list -n clinicq`, open the Ingress URL.
7. Show Prometheus targets and the Grafana dashboard; run `scripts/load-test.sh` and show the HPA scaling.
8. Break and fix a service live (`troubleshooting/broken-service.yaml`).

## Screenshot checklist

- [ ] App in browser (localhost:3000) · `docker compose up --build` terminal
- [ ] `pytest -v` all passing
- [ ] GitHub commit history (10+ commits)
- [ ] Green Actions run URL · Trivy step output · GHCR packages with SHA tags
- [ ] `terraform plan` · AWS Console VPC + EKS · `terraform destroy` complete
- [ ] `kubectl get pods` / `get svc` / `helm list` · app via Ingress
- [ ] `/metrics` output · Prometheus Targets UP · Grafana dashboard

## Make it yours (the rubric zeroes clones)

The domain and code are original to ClinicQ, but you must be able to explain every file in the live demo.
Make a few visible changes of your own: your clinic name and colours, one extra field (for example
`blood_group` on patients — which also gives you a real Alembic migration to write), and one extra test.

## Common problems

| Symptom | Fix |
|---|---|
| `docker compose up --build` cannot resolve Docker Hub (`failed to resolve source metadata`, `no such host`) | Confirm the host can resolve `registry-1.docker.io` and reach port 443. In Docker Desktop, check **Settings → Proxies**: configure the HTTPS proxy required by your network, or disable a stale proxy if direct access is expected. Restart Docker Desktop and retry. If the host works but Docker still cannot resolve the registry, check VPN/firewall and Docker Desktop DNS settings; use a DNS resolver permitted by your network. |
| Trivy fails with HIGH/CRITICAL | Upgrade the affected Python dependency or base-image OS packages (the frontend image refreshes Alpine packages during build), then rerun the scan |
| Trivy "TOOMANYREQUESTS" downloading its DB | Re-run the job; it is a transient rate limit |
| PowerShell says `kind` is not recognized | Install it with `winget install Kubernetes.kind`, reopen PowerShell, and check `Get-Command kind` |
| Pods `ImagePullBackOff` on kind | Re-run `kind load docker-image …` and use `values-dev.yaml` |
| Pods `ImagePullBackOff` on EKS | GHCR packages are still private, or `OWNER` in `values.yaml` is wrong |
| `terraform apply` quota / permissions errors | Use an admin IAM user; confirm the region is `ap-south-1` |
| `terraform destroy` hangs on the VPC | A load balancer is still alive: uninstall ingress-nginx, wait, retry |
| HPA shows `<unknown>` | metrics-server is not installed or not ready yet |
| Postgres pod `Pending` on EKS | EBS CSI add-on not ready; `kubectl get pvc,pods -n kube-system` |

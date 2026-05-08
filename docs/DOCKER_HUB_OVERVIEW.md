**Allure Report 3** (official npm package `allure`) with a **REST API**, **Swagger UI**, **multi-project** storage, **report history**, and a **report navigator** page to browse *latest* and historical builds in one UI.

[![CI](https://github.com/LFBRxD/allure-docker-service/actions/workflows/docker-publish.yml/badge.svg)](https://github.com/LFBRxD/allure-docker-service/actions)

Maintained fork: **[LFBRxD/allure-docker-service](https://github.com/LFBRxD/allure-docker-service)** — based on Frank Escobar’s original project, upgraded for Allure 3.

> **Not** the legacy **Allure 2** image. For Allure Report 3 use **`flaviordesouza/allure-docker-service`** (this image), not `frankescobar/allure-docker-service` on Docker Hub for the old stack.

---

## Quick start (single project)

Mount your local `allure-results` directory (where your tests write Allure output):

```bash
docker run -d --name allure -p 5050:5050 \
  -e CHECK_RESULTS_EVERY_SECONDS=3 \
  -e KEEP_HISTORY=1 \
  -v "$(pwd)/allure-results:/app/allure-results" \
  -v "$(pwd)/allure-reports:/app/default-reports" \
  flaviordesouza/allure-docker-service:latest
```

Then open:

| What | URL |
|------|-----|
| **Latest report** | `http://localhost:5050/allure-docker-service/latest-report` |
| **Report navigator** (latest + history, iframes) | `http://localhost:5050/allure-docker-service/report-navigator` |
| **Swagger** | `http://localhost:5050/allure-docker-service/swagger` |

(`/swagger` without prefix also works.)

Default internal project id: **`default`**.

---

## Ports

| Port | Purpose |
|------|---------|
| **5050** | API + served reports (use this) |
| 4040 | Deprecated static server (compatibility only) |

---

## Tags & architectures

Images are published for **linux/amd64** and **linux/arm64** (armv7 is not built: the Allure CLI stage uses `node:22-bookworm-slim`, which has no armv7 variant).

**Image tag vs Allure npm version:** the Docker tag (e.g. **`1.4.0`** from git tag **`v1.4.0`**) is the **release of this image/service**. The bundled Allure CLI uses the npm package version from the build (e.g. **3.3.1** today) — see `GET /version` on a running container and the image label **`allure.npm.version`**. They are intentionally separate.

Typical tags: **`latest`** (último build bem-sucedido da **main** ou último manifest de tag `v*`, conforme o último push), releases **`1.0.<N>`** em **cada push na `main`** (`N` = contagem de commits até esse commit no Git, ex.: `git rev-list --count HEAD`), além de **`main`** e **`sha-` + 8 hex** por commit. Releases manuais: git tag **`vx.y.z`** → imagem **`:x.y.z`**. See [tags](https://hub.docker.com/r/flaviordesouza/allure-docker-service/tags).

---

## Features (high level)

- Automatic or on-demand report generation from `allure-results`
- **Multiple projects** via API (`POST /projects`, `project_id` on actions)
- **History** / trends (Allure 3 `history.jsonl` + stored report folders)
- **Report navigator** — HTML hub with project selector, themes, responsive sidebar
- **Emailable** HTML report endpoint
- Optional **security** (JWT), TLS, URL prefix — see full README on GitHub

---

## Full documentation

**[github.com/LFBRxD/allure-docker-service#readme](https://github.com/LFBRxD/allure-docker-service#readme)** — compose examples, environment variables, security, Kubernetes, and more.

Examples for generating `allure-results` (Java, Node, Python, etc.):  
**[github.com/fescobar/allure-docker-service-examples](https://github.com/fescobar/allure-docker-service-examples)**

---

## License

**Apache-2.0** — see [NOTICE](https://github.com/LFBRxD/allure-docker-service/blob/main/NOTICE) in the repository.

**Maintainer (this fork):** Flavio Ramos ([@LFBRxD](https://github.com/LFBRxD)).  
**Original author:** Frank Escobar.

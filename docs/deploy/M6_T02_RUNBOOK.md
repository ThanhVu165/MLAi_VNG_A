# M6-T02 — Docker Foundation Runbook

## Safety boundary

- Docker Desktop must be running locally.
- Every service binds only to `127.0.0.1`; it is not a public deployment.
- Compose forces `LLM_MODE=replay`; no API key is added to the image or Compose configuration. Do not override this to `live` for M6-T02.
- `run_local.py` is the container entrypoint. It seeds the selected database and starts the background worker before Streamlit.
- DEV (the default service), STUDY, and DEMO each mount a distinct named volume at `/runtime`; `DATABASE_PATH` is `/runtime/app.db`.

## Build and start

Run these commands from the repository root. Replace the project name only when creating an explicitly disposable validation environment.

```powershell
docker compose config
docker compose build
docker compose up -d dev
docker compose --profile study up -d
docker compose --profile demo up -d
docker compose ps
```

Open the local environments only on their loopback ports:

| Environment | URL | Database volume |
| --- | --- | --- |
| DEV | `http://127.0.0.1:8511` | `dev_data` |
| STUDY | `http://127.0.0.1:8512` | `study_data` |
| DEMO | `http://127.0.0.1:8513` | `demo_data` |

Các cổng mặc định vẫn là `8511`/`8512`/`8513`. Với project validation disposable,
tránh xung đột với môi trường đang chạy bằng `DEV_HOST_PORT`, `STUDY_HOST_PORT` hoặc
`DEMO_HOST_PORT`; ví dụ PowerShell: `$env:DEV_HOST_PORT = '18511'`.

Check the health endpoint and the Python version:

```powershell
Invoke-WebRequest http://127.0.0.1:8511/_stcore/health
Invoke-WebRequest http://127.0.0.1:8512/_stcore/health
Invoke-WebRequest http://127.0.0.1:8513/_stcore/health
docker compose exec -T dev python --version
```

`docker compose logs dev`, `docker compose logs study` và `docker compose logs demo`
phải có marker `Background workers started and alive: email-processing, email-dispatch`
mà không phát sinh provider/API call.

## Isolation and persistence

Do not use the regular profile volumes for reset experiments. Use a unique project name containing `test` or `validation`:

```powershell
$project = 'exodia-m6t02-validation-dev'
$env:DEV_HOST_PORT = '18511'
docker compose --project-name $project up -d dev
docker compose --project-name $project exec -T dev python -c 'from infra.db import execute; execute("CREATE TABLE IF NOT EXISTS m6_t02_probe (value TEXT NOT NULL)"); execute("INSERT INTO m6_t02_probe VALUES (''synthetic'')")'
docker compose --project-name $project restart dev
docker compose --project-name $project exec -T dev python -c 'from infra.db import fetch_one; assert fetch_one("SELECT value FROM m6_t02_probe")[0] == "synthetic"'
python scripts/m6_t02_safe_reset.py $project
Remove-Item Env:DEV_HOST_PORT
```

Guard reset chỉ chấp nhận `exodia-m6t02-validation` hoặc tên bắt đầu bằng
`exodia-m6t02-validation-`. Guard tìm volume theo đúng label
`com.docker.compose.project`, xác minh toàn bộ volume trước khi xóa, và dừng mà không
xóa gì nếu project hoặc label không hợp lệ. Không gọi trực tiếp
`docker compose down --volumes` trong validation M6-T02.

To compare profile databases without deleting anything:

```powershell
docker compose exec -T dev python -c "import os; print(os.environ['DATABASE_PATH'])"
docker compose --profile study exec -T study python -c "import os; print(os.environ['DATABASE_PATH'])"
docker compose --profile demo exec -T demo python -c "import os; print(os.environ['DATABASE_PATH'])"
docker volume ls
```

## Stop and reset

Stop a profile while retaining its database:

```powershell
docker compose stop dev
docker compose up -d dev
```

Chỉ xóa database volume do project validation disposable M6-T02 tạo ra, bằng
`python scripts/m6_t02_safe_reset.py <project>`. Ứng dụng giữ dữ liệu database thông
thường và tạo migration backup trong thư mục database; guard từ chối DEV/STUDY/DEMO
và M6-T02 không cung cấp destructive reset cho các môi trường đó.

## Troubleshooting

- If Docker Desktop reports that its Engine is stopped, start Docker Desktop and wait until the Engine is running.
- If a health check fails, run `docker compose --profile <profile> logs <profile>` and confirm that no `.env` or live credential has been copied into the image.
- A cassette miss is owned by M6-T05. Do not add or modify replay cassettes as part of Docker Foundation.

# PAC‑MCMV Clean Stack (v2)

```bash
# 1. Clone
# 2. Place the three source Excel files in sample_data/
# 3. Build & run
$ docker compose -f docker-compose.clean.yml up --build -d
# 4. Trigger ETL once
$ docker compose -f docker-compose.clean.yml run --rm etl_v2
# 5. Open http://localhost:8503
```

All logic lives here; legacy stack remains untouched.

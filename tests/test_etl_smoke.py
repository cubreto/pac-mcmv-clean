import subprocess, pathlib, sqlalchemy as sa, os

def test_etl_smoke():
    repo = pathlib.Path(__file__).resolve().parents[1]
    compose = ["docker", "compose", "-f", repo/"docker-compose.clean.yml", "run", "--rm", "etl_v2"]
    res = subprocess.run(compose, capture_output=True, text=True)
    assert res.returncode == 0, res.stderr

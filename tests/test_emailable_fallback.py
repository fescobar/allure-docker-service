"""Smoke: emailable preenche a partir de *-result.json quando summary.newTests está vazio."""
import importlib.util
import json
import os
import shutil
import sys
import tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_app_module():
    api_dir = os.path.join(REPO, "allure-docker-api")
    os.environ.setdefault("EMAILABLE_REPORT_FILE_NAME", "emailable-report-allure-docker-service.html")
    spec = importlib.util.spec_from_file_location("allure_app", os.path.join(api_dir, "app.py"))
    mod = importlib.util.module_from_spec(spec)
    sys.path.insert(0, api_dir)
    spec.loader.exec_module(mod)
    return mod


def main():
    app_mod = _load_app_module()
    td = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(td, "reports", "latest"), exist_ok=True)
        os.makedirs(os.path.join(td, "results"), exist_ok=True)
        src = os.path.join(REPO, "docker", "bootstrap-allure-results", "e8fa830a-25a2-462c-b7e8-2a7d732e8695-result.json")
        shutil.copy(src, os.path.join(td, "results", "e8fa830a-25a2-462c-b7e8-2a7d732e8695-result.json"))
        with open(os.path.join(td, "reports", "latest", "summary.json"), "w", encoding="utf-8") as f:
            json.dump({"newTests": []}, f)
        tc = app_mod.load_emailable_test_cases(td)
        assert len(tc) == 1, tc
        assert tc[0]["status"] == "passed"
        assert "test1" in (tc[0].get("name") or "")
    finally:
        shutil.rmtree(td, ignore_errors=True)
    print("OK: test_emailable_fallback.py")


if __name__ == "__main__":
    main()

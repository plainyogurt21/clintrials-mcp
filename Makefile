PY := python3

.PHONY: venv install serve-http serve-stdio test-smoke

venv:
	$(PY) -m venv .venv

install:
	.venv/bin/pip install --upgrade pip
	.venv/bin/pip install -r requirements.txt

serve-http:
	TRANSPORT=http PORT=${PORT:-8081} .venv/bin/python mcp_server.py

serve-stdio:
	.venv/bin/python mcp_server.py

test-smoke:
	.venv/bin/python tests/smoke_http_app.py


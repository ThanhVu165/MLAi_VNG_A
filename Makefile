.PHONY: check

check:
	black --check --line-length 100 .
	ruff check .
	mypy --ignore-missing-imports .
	pytest -q; status=$$?; test $$status -eq 0 -o $$status -eq 5

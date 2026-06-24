UV_PYTHON := 3.12
export UV_PYTHON

generate-requirements: uv.lock
	uv pip compile --generate-hashes --output-file=requirements.txt pyproject.toml
	uv tool run --with='pip<25.1' pybuild-deps compile --generate-hashes --output-file=requirements-build.txt requirements.txt

uv.lock: pyproject.toml
	uv sync


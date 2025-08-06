generate-requirements: uv.lock
	uv pip compile --generate-hashes --output-file=requirements.txt pyproject.toml
	uv tool run pybuild-deps compile --generate-hashes --output-file=requirements-build.txt requirements.txt

uv.lock: pyproject.toml
	uv sync


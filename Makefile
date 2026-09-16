UV_PYTHON := 3.12
export UV_PYTHON

generate-requirements: uv.lock
	uv export --locked --no-dev --no-emit-project --output-file=requirements.txt > /dev/null
	@build_requirements=$$(mktemp); \
	trap 'rm -f "$$build_requirements"' EXIT; \
	awk '/^[[:alnum:]_.-]+==.*sys_platform == .win32./ { skip = 1; next } /^[[:alnum:]_.-]+==/ { skip = 0 } !skip { print }' requirements.txt > $$build_requirements; \
	uv tool run --with='pip<25.1' --with='pip-tools==7.4.1' 'pybuild-deps==0.4.1' compile --quiet --no-header --generate-hashes --output-file=requirements-build.txt $$build_requirements

uv.lock: pyproject.toml
	uv sync

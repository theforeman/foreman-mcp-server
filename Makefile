generate-requirements: uv.lock
	uv pip compile pyproject.toml -o requirements-build.txt --generate-hashes --group build

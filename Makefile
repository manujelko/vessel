project_name = vessel

# ==================================================================================== #
# HELPERS
# ==================================================================================== #

## help: print this help message
.PHONY: help
help:
	@echo 'Usage:'
	@sed -n 's/^##//p' ${MAKEFILE_LIST} | column -t -s ':' |  sed -e 's/^/ /'

.PHONY: confirm
confirm:
	@echo -n 'Are you sure? [y/N] ' && read ans && [ $${ans:-N} = y ]

.PHONY: no-dirty
no-dirty:
	@test -z "$(shell git status --porcelain)"


# ==================================================================================== #
# QUALITY CONTROL
# ==================================================================================== #

## cq/format: Format code
.PHONY: cq/format
cq/format:
	@uv run ruff check --select I --fix
	@uv run ruff format

## qc/format/check: Check that code is formatted
.PHONY: cq/format/check
cq/format/check:
	@uv run ruff check --select I
	@uv run ruff format --check

## cq/lint: Check code style
,PHONY: cq/lint
cq/lint:
	@uv run ruff check

## cq/lint/fix: Fix code style
.PHONY: cq/lint/fix
cq/lint/fix:
	@uv run ruff check --fix

## cq/typecheck: Typecheck code
.PHONY: cq/typecheck
cq/typecheck:
	@uv run mypy

## cq/test: Test code
.PHONY: cq/test
cq/test:
	@uv run pytest -v

## cq/pre-commit
.PHONY: cq/pre-commit
cq/pre-commit:
	@pre-commit run --all-files

# ==================================================================================== #
# DEVELOPMENT
# ==================================================================================== #

## dev/podman_api: Start the podman API
.PHONY: dev/podman_api
dev/podman_api:
	@./scripts/podman_api_tunnel.sh

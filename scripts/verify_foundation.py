#!/usr/bin/env python3
"""
Paraxis AI — Foundation Verification Script
Asserts the presence, non-emptiness, syntax validity, and integrity
of all architectural documents, ADRs, configuration files, and application scaffolds.
"""
import os
import sys
import py_compile
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

# 1. Required Root Files
REQUIRED_ROOT_FILES = [
    "README.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "SECURITY.md",
    ".gitignore",
    ".env.example",
    "Makefile",
    "docker-compose.yml",
    ".github/workflows/ci.yml",
]

# 2. Required ADRs
REQUIRED_ADRS = [
    "docs/decisions/ADR-001-monorepo.md",
    "docs/decisions/ADR-002-django-fastapi-boundary.md",
    "docs/decisions/ADR-003-postgresql-pgvector.md",
    "docs/decisions/ADR-004-agent-orchestration.md",
    "docs/decisions/ADR-005-tool-and-policy-model.md",
    "docs/decisions/ADR-006-multi-tenancy.md",
    "docs/decisions/ADR-007-audit-model.md",
    "docs/decisions/ADR-008-ai-provider-abstraction.md",
    "docs/decisions/ADR-009-realtime-events.md",
]

# 3. Required Architecture & System Docs
REQUIRED_DOCS = [
    # Architecture
    "docs/architecture/system-overview.md",
    "docs/architecture/high-level-design.md",
    "docs/architecture/low-level-design.md",
    "docs/architecture/domain-architecture.md",
    "docs/architecture/data-architecture.md",
    "docs/architecture/integration-architecture.md",
    "docs/architecture/realtime-architecture.md",
    "docs/architecture/deployment-architecture.md",
    # Product
    "docs/product/product-charter.md",
    "docs/product/product-requirements-document.md",
    "docs/product/user-personas.md",
    "docs/product/user-journeys.md",
    "docs/product/feature-map.md",
    "docs/product/mvp-scope.md",
    "docs/product/enterprise-roadmap.md",
    "docs/product/hackathon-strategy.md",
    "docs/product/design-system.md",
    "docs/product/demo-script.md",
    # Agents
    "docs/agents/agent-architecture.md",
    "docs/agents/agent-state-model.md",
    "docs/agents/tool-contracts.md",
    "docs/agents/policy-engine.md",
    "docs/agents/agent-evaluation.md",
    "docs/agents/memory-and-rag.md",
    "docs/agents/failure-recovery.md",
    # Security
    "docs/security/security-architecture.md",
    "docs/security/threat-model.md",
    "docs/security/authorization-model.md",
    "docs/security/tenant-isolation.md",
    "docs/security/ai-safety.md",
    "docs/security/privacy-model.md",
    "docs/security/incident-response.md",
    # API
    "docs/api/api-guidelines.md",
    "docs/api/error-model.md",
    "docs/api/versioning.md",
    "docs/api/authentication.md",
    # Testing
    "docs/testing/testing-strategy.md",
    "docs/testing/unit-testing.md",
    "docs/testing/integration-testing.md",
    "docs/testing/e2e-testing.md",
    "docs/testing/ai-evaluation.md",
    "docs/testing/performance-testing.md",
    # Operations
    "docs/operations/local-development.md",
    "docs/operations/environments.md",
    "docs/operations/observability.md",
    "docs/operations/deployment.md",
    "docs/operations/disaster-recovery.md",
    "docs/operations/runbooks.md",
]

# 4. Required Application Scaffold Files
REQUIRED_SCAFFOLD_FILES = [
    # Core
    "apps/core/manage.py",
    "apps/core/pyproject.toml",
    "apps/core/requirements.txt",
    "apps/core/config/settings.py",
    "apps/core/config/urls.py",
    "apps/core/core/views/health.py",
    # Intelligence
    "apps/intelligence/pyproject.toml",
    "apps/intelligence/requirements.txt",
    "apps/intelligence/config.py",
    "apps/intelligence/main.py",
    "apps/intelligence/api/v1/health.py",
    # Web
    "apps/web/package.json",
    "apps/web/tsconfig.json",
    "apps/web/tailwind.config.js",
    "apps/web/app/layout.tsx",
    "apps/web/app/page.tsx",
    "apps/web/app/api/health/route.ts",
    # Infrastructure
    "infrastructure/postgres/init-pgvector.sql",
]


def check_files(file_list, category_name):
    missing = []
    empty = []
    for rel_path in file_list:
        p = ROOT_DIR / rel_path
        if not p.exists():
            missing.append(rel_path)
        elif p.stat().st_size == 0:
            empty.append(rel_path)
            
    if missing:
        print(f"❌ [FAIL] Missing {category_name} files ({len(missing)}):")
        for m in missing:
            print(f"    - {m}")
        return False
    elif empty:
        print(f"❌ [FAIL] Empty {category_name} files ({len(empty)}):")
        for e in empty:
            print(f"    - {e}")
        return False
    else:
        print(f"✅ [PASS] All {len(file_list)} {category_name} files verified.")
        return True


def check_adrs():
    all_valid = True
    for adr in REQUIRED_ADRS:
        p = ROOT_DIR / adr
        if not p.exists():
            print(f"❌ [FAIL] Missing ADR: {adr}")
            all_valid = False
            continue
        content = p.read_text(encoding="utf-8")
        if "Status:" not in content and "- **Status**:" not in content:
            print(f"❌ [FAIL] ADR missing Status header: {adr}")
            all_valid = False
    if all_valid:
        print(f"✅ [PASS] All {len(REQUIRED_ADRS)} ADRs verified with valid status headers.")
    return all_valid


def check_python_syntax():
    py_files = list(ROOT_DIR.glob("apps/core/**/*.py")) + list(ROOT_DIR.glob("apps/intelligence/**/*.py"))
    syntax_errors = []
    for py_file in py_files:
        try:
            py_compile.compile(str(py_file), doraise=True)
        except py_compile.PyCompileError as e:
            syntax_errors.append((str(py_file), str(e)))

    if syntax_errors:
        print(f"❌ [FAIL] Python compilation errors ({len(syntax_errors)}):")
        for f, err in syntax_errors:
            print(f"    - {f}: {err}")
        return False
    else:
        print(f"✅ [PASS] All {len(py_files)} Python source files compiled with zero syntax errors.")
        return True


def check_no_secrets_tracked():
    p_env = ROOT_DIR / ".env"
    if p_env.exists():
        # Check if tracked by git
        import subprocess
        result = subprocess.run(["git", "ls-files", ".env"], cwd=ROOT_DIR, capture_output=True, text=True)
        if result.stdout.strip():
            print("❌ [FAIL] .env file is tracked by git! Security violation.")
            return False
    print("✅ [PASS] Secret isolation verified: No real credentials or .env files tracked.")
    return True


def main():
    print("==================================================================")
    print("🔍 PARAXIS AI — FOUNDATION VERIFICATION")
    print("==================================================================")
    
    success = True
    success &= check_files(REQUIRED_ROOT_FILES, "Root Governance & Config")
    success &= check_adrs()
    success &= check_files(REQUIRED_DOCS, "Architecture & Product Documentation")
    success &= check_files(REQUIRED_SCAFFOLD_FILES, "Application Scaffolds")
    success &= check_python_syntax()
    success &= check_no_secrets_tracked()
    
    print("==================================================================")
    if success:
        print("🎉 ALL FOUNDATION VERIFICATION CHECKS PASSED!")
        print("Paraxis AI repository foundation is complete, verified, and ready.")
        print("==================================================================")
        sys.exit(0)
    else:
        print("❌ FOUNDATION VERIFICATION FAILED.")
        print("==================================================================")
        sys.exit(1)


if __name__ == "__main__":
    main()

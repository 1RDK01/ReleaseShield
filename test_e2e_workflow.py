"""
ReleaseShield End-to-End Workflow Verification Script
Tests all 7 lifecycle stages and API endpoints.
"""
import sys
import os
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.abspath("."))
from backend.main import app

def run_tests():
    client = TestClient(app)

    print("==================================================")
    print("RELEASESHIELD END-TO-END VERIFICATION")
    print("==================================================")

    print("\n[1/10] Testing health endpoint...")
    r = client.get("/health")
    assert r.status_code == 200, f"Health check failed: {r.text}"
    print(f"       Status: 200 OK — service: {r.json().get('service')}")

    print("\n[2/10] Resetting demo repository to clean BEFORE state...")
    r = client.post("/api/demo/reset")
    assert r.status_code == 200, f"Reset failed: {r.text}"
    print(f"       Status: 200 OK — files restored: {r.json().get('files_restored')}")

    print("\n[3/10] Running initial verification suite (clean state)...")
    r = client.post("/api/verify")
    assert r.status_code == 200
    v = r.json()
    print(f"       All passed: {v.get('all_passed')}")
    for c in v.get("commands", []):
        lbl = c.get("label")
        p = c.get("passed")
        pc = c.get("pass_count")
        tc = c.get("test_count")
        dur = c.get("duration_seconds")
        print(f"       -> {lbl}: {'PASS' if p else 'FAIL'} (passes: {pc}/{tc}, duration: {dur}s)")
    assert v.get("all_passed") is True, "Clean state verification should pass all checks"

    print("\n[4/10] Introducing deliberate 1-file developer change...")
    r = client.post("/api/demo/introduce-change")
    assert r.status_code == 200
    print(f"       Status: 200 OK — {r.json().get('description')}")
    print(f"       Developer-changed files: {r.json().get('changed_files_count')}")

    print("\n[5/10] Running ReleaseShield Analyze (IBM Bob impact analysis)...")
    r = client.post("/api/analyze")
    assert r.status_code == 200
    a = r.json()
    print(f"       Developer-changed files: {a.get('developer_changed_files')}")
    print(f"       Bob-discovered impacted files: {a.get('bob_discovered_files')}")
    print(f"       Risk findings generated: {a.get('findings')}")
    assert a.get("developer_changed_files") == 1, "Expected exactly 1 developer-changed file"
    assert a.get("bob_discovered_files") >= 7, f"Expected at least 7 discovered files, got {a.get('bob_discovered_files')}"

    print("\n[6/10] Fetching Impact Graph & Findings...")
    r = client.get("/api/impact")
    assert r.status_code == 200
    ig = r.json()
    dev_files = ig.get("developer_changed_files", [])
    bob_files = ig.get("bob_discovered_files", [])
    edges = ig.get("dependency_edges", [])
    findings = ig.get("findings", [])
    print(f"       Developer Files: {len(dev_files)}, Bob Discovered: {len(bob_files)}, Edges: {len(edges)}")
    print(f"       Findings count: {len(findings)}")
    for f in findings[:4]:
        print(f"       - [{f.get('severity').upper()}] {f.get('title')}")

    print("\n[7/10] Running Coordinated Multi-File Remediation (Bob Sync)...")
    r = client.post("/api/remediate")
    assert r.status_code == 200
    rem = r.json()
    print(f"       Success: {rem.get('success')}")
    print(f"       Remediated files count: {rem.get('files_modified_count')}")
    for mf in rem.get("modified_files", []):
        print(f"         * {mf}")
    assert rem.get("success") is True

    print("\n[8/10] Running Verification suite on remediated repository...")
    r = client.post("/api/verify")
    assert r.status_code == 200
    pv = r.json()
    print(f"       All passed: {pv.get('all_passed')}")
    for c in pv.get("commands", []):
        lbl = c.get("label")
        p = c.get("passed")
        pc = c.get("pass_count")
        tc = c.get("test_count")
        dur = c.get("duration_seconds")
        print(f"       -> {lbl}: {'PASS' if p else 'FAIL'} (passes: {pc}/{tc}, duration: {dur}s)")
    assert pv.get("all_passed") is True, "Remediated repository must pass all verification checks"

    print("\n[9/10] Fetching Release Evidence Report...")
    r = client.get("/api/report")
    assert r.status_code == 200
    rep = r.json()
    print("       Report generated successfully.")
    print("       Artifact files created:")
    for k, p in rep.get("artifacts", {}).items():
        print(f"         - {k}: {p}")
    assert "release_report" in rep.get("artifacts", {})

    print("\n[10/10] Auditing workflow execution logs...")
    r = client.get("/api/events")
    assert r.status_code == 200
    data = r.json()
    audit_log = data.get("audit_log", [])
    print(f"       Total audit events: {len(audit_log)}")
    for e in audit_log[-5:]:
        print(f"         [{e.get('timestamp')}] {e.get('message')}")
    assert len(audit_log) > 0

    print("\n==================================================")
    print("ALL 10 VERIFICATION STAGES PASSED SUCCESSFULLY!")
    print("==================================================")

if __name__ == "__main__":
    run_tests()

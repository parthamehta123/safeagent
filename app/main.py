from fastapi import FastAPI, HTTPException
from app.models import AgentRequest
from app.llm import choose_files, build_plan
from app.sandbox import execute_plan
from app.snapshot import clone_repo, load_files, hash_files
from app.db import init_db, SessionLocal, AgentSession
from app.models import AgentSessionOut

app = FastAPI()


@app.on_event("startup")
def startup():
    init_db()


@app.post("/analyze")
def analyze(req: AgentRequest):
    repo = clone_repo(req.repo_url)
    files = load_files(repo, content=False)
    return {"files": list(files.keys())}


@app.post("/run")
def run(req: AgentRequest):
    repo = clone_repo(req.repo_url)

    # Phase 1: discover files
    all_files = load_files(repo, content=False)
    file_list = list(all_files.keys())

    # Phase 2: model selects relevant files
    selected = choose_files(req.prompt, file_list)

    if not selected:
        raise HTTPException(400, "Model did not select any files")

    # Phase 3: load only selected files
    files = load_files(repo, include=selected)
    manifest = hash_files(repo)

    # Phase 4: build patch plan
    plan = build_plan(req.prompt, files, manifest)

    # Phase 5: execute plan
    pr = execute_plan(req.repo_url, plan, req.prompt)

    return {
        "status": "success",
        "files_used": selected,
        "pull_request": pr,
    }


@app.post("/run_manual")
def run_manual(req: AgentRequest):
    import os
    import subprocess
    from fastapi import HTTPException

    from app.models import AgentPlan, FileEdit
    from app.snapshot import hash_files

    repo = clone_repo(req.repo_url)

    manifest = hash_files(repo)

    if "README.md" not in manifest:
        raise HTTPException(400, "README.md not found")

    readme_hash = manifest["README.md"]
    readme_path = os.path.join(repo, "README.md")

    # Force deterministic change
    with open(readme_path, "r", encoding="utf-8") as f:
        original = f.read()

    if "# SafeAgent manual test" not in original:
        updated = "# SafeAgent manual test\n\n" + original
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write(updated)

    # Generate patch
    patch = subprocess.check_output(
        ["git", "diff"],
        cwd=repo,
    ).decode()

    if not patch.strip():
        raise HTTPException(500, "Patch generation failed")

    plan = AgentPlan(
        edits=[
            FileEdit(
                file_path="README.md",
                original_hash=readme_hash,
                unified_diff=patch,
            )
        ]
    )

    pr = execute_plan(req.repo_url, plan, req.prompt)

    return {"status": "validated", "pr": pr}


@app.get("/sessions", response_model=list[AgentSessionOut])
def list_sessions(limit: int = 20):
    db = SessionLocal()
    try:
        rows = (
            db.query(AgentSession)
            .order_by(AgentSession.created_at.desc())
            .limit(limit)
            .all()
        )
        return rows
    finally:
        db.close()


@app.get("/sessions/{session_id}")
def get_session(session_id: str):
    db = SessionLocal()
    try:
        row = db.query(AgentSession).filter_by(id=session_id).first()
        if not row:
            raise HTTPException(404, "Session not found")
        return row
    finally:
        db.close()


@app.get("/diff/{session_id}")
def get_diff(session_id: str):
    db = SessionLocal()
    try:
        row = db.query(AgentSession).filter_by(id=session_id).first()
        if not row:
            raise HTTPException(404, "Session not found")
        return {"diff": row.diff}
    finally:
        db.close()


@app.get("/trace/{session_id}")
def get_trace(session_id: str):
    db = SessionLocal()
    try:
        row = db.query(AgentSession).filter_by(id=session_id).first()
        if not row:
            raise HTTPException(404, "Session not found")
        return {"trace": row.trace}
    finally:
        db.close()

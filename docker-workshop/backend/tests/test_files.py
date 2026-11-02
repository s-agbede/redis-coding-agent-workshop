from fastapi.testclient import TestClient
from app import create_app


def test_editor_inventory_exposes_workshop_files_but_not_secrets_or_symlinks(tmp_path):
    (tmp_path/'agent.py').write_text('# learner')
    (tmp_path/'runtime.py').write_text('# supplied')
    (tmp_path/'project').mkdir()
    (tmp_path/'project/AGENTS.md').write_text('instructions')
    (tmp_path/'.env').write_text('secret')
    (tmp_path/'output').mkdir()
    (tmp_path/'output/trace.json').write_text('private session')
    outside=tmp_path.parent/'outside.py';outside.write_text('outside')
    (tmp_path/'linked.py').symlink_to(outside)
    response=TestClient(create_app(workspace=tmp_path)).get('/api/editor/files')
    assert response.status_code == 200
    assert response.json()==[{'path':'agent.py'},{'path':'project/AGENTS.md'},{'path':'runtime.py'}]

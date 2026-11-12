import pytest


@pytest.fixture(autouse=True)
def isolated_server_config(monkeypatch, tmp_path):
    """Keeps tests independent of the developer's saved server address and server environment variables."""
    import lmstudio

    monkeypatch.setattr(lmstudio, "LOCAL_SERVER_FILE", tmp_path / ".local_server")
    monkeypatch.delenv("LM_STUDIO_URL", raising=False)
    monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

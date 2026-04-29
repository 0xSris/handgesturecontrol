from pathlib import Path
from uuid import uuid4
from urllib.request import urlopen

from gesture_control.share import ShareServer, content_type


def test_content_type_defaults_for_unknown_extension():
    assert content_type(Path("file.unknownext")) == "application/octet-stream"


def test_share_server_disabled_without_path():
    server = ShareServer(None)
    status = server.status
    assert status.active is False
    assert "share" in status.message


def test_single_file_share_downloads_from_root():
    shared_file = Path("tmp") / f"share-test-{uuid4().hex}.txt"
    shared_file.parent.mkdir(exist_ok=True)
    shared_file.write_text("hello phone", encoding="utf-8")
    server = ShareServer(str(shared_file), port=0)
    try:
        status = server.start()
        assert status.url is not None
        with urlopen(status.url, timeout=5) as response:
            assert response.read() == b"hello phone"
            assert response.headers["Content-Disposition"].startswith("attachment;")
    finally:
        server.close()
        shared_file.unlink(missing_ok=True)

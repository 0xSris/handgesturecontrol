from pathlib import Path

from gesture_control.media import RecordingSession, list_available_cameras, next_snapshot_path, resolve_camera_index


class FakeCapture:
    def __init__(self, opened):
        self._opened = opened
        self.released = False

    def isOpened(self):
        return self._opened

    def release(self):
        self.released = True


class FakeWriter:
    def __init__(self):
        self.frames = []
        self.released = False

    def isOpened(self):
        return True

    def write(self, frame):
        self.frames.append(frame)

    def release(self):
        self.released = True


class FakeFrame:
    shape = (240, 320, 3)


class FakeCv2:
    def __init__(self, open_indexes=None):
        self.open_indexes = set(open_indexes or [])
        self.writer = FakeWriter()

    def VideoCapture(self, index):
        return FakeCapture(index in self.open_indexes)

    def VideoWriter_fourcc(self, *args):
        return 1234

    def VideoWriter(self, output_path, fourcc, fps, size):
        self.writer_args = (output_path, fourcc, fps, size)
        return self.writer


def test_list_available_cameras_returns_open_indexes():
    cv2 = FakeCv2(open_indexes={1, 3})
    assert list_available_cameras(cv2, limit=5) == [1, 3]


def test_resolve_camera_index_auto_uses_first_open_camera():
    cv2 = FakeCv2(open_indexes={2, 4})
    assert resolve_camera_index(cv2, requested_index=-1, probe_limit=5) == 2


def test_recording_session_lazy_opens_writer():
    cv2 = FakeCv2()
    recorder = RecordingSession("captures/demo.mp4", fps=24)

    recorder.write(cv2, FakeFrame())
    recorder.write(cv2, FakeFrame())
    recorder.close()

    assert Path(cv2.writer_args[0]) == Path("captures/demo.mp4")
    assert cv2.writer_args[1:] == (1234, 24, (320, 240))
    assert recorder.status.frames_written == 2
    assert cv2.writer.released is True


def test_next_snapshot_path_uses_png_extension():
    path = next_snapshot_path("captures")
    assert path.parent == Path("captures")
    assert path.suffix == ".png"

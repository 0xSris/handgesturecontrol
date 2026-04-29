from gesture_control.app import resize_for_display


class FakeFrame:
    def __init__(self, width, height):
        self.shape = (height, width, 3)


class FakeCv2:
    INTER_AREA = 3

    def __init__(self):
        self.resize_calls = []

    def resize(self, frame, size, interpolation):
        self.resize_calls.append((frame, size, interpolation))
        return FakeFrame(size[0], size[1])


def test_resize_for_display_resizes_oversized_frame():
    cv2 = FakeCv2()
    frame = FakeFrame(1920, 1080)

    resized = resize_for_display(cv2, frame, 960, 540)

    assert resized.shape == (540, 960, 3)
    assert cv2.resize_calls[0][1] == (960, 540)


def test_resize_for_display_keeps_matching_frame():
    cv2 = FakeCv2()
    frame = FakeFrame(960, 540)

    resized = resize_for_display(cv2, frame, 960, 540)

    assert resized is frame
    assert cv2.resize_calls == []

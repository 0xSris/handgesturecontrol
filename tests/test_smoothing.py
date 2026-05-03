import numpy as np

from gesture_control.smoothing.one_euro_filter import OneEuroFilter, OneEuroLandmarkFilter


def test_one_euro_filter_reduces_step_jitter():
    filter_ = OneEuroFilter(min_cutoff=1.0, beta=0.0)

    first = filter_.apply(0.0, 1 / 30)
    second = filter_.apply(1.0, 1 / 30)

    assert first == 0.0
    assert 0.0 < second < 1.0


def test_landmark_filter_preserves_shape():
    landmarks = np.zeros((21, 3), dtype=float)
    filter_ = OneEuroLandmarkFilter()

    output = filter_.update(landmarks, 1 / 30)

    assert output.shape == (21, 3)

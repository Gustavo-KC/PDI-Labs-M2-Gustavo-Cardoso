import subprocess
import sys
import cv2
import numpy as np
import pytest
from pdi_lab.__main__ import segment, analyze, validate_mask


def test_fixed_boundary():
    sample = np.array([[119, 120, 121]], dtype=np.uint8)
    color = cv2.cvtColor(sample, cv2.COLOR_GRAY2BGR)
    assert segment(color, 'fixed', 120).tolist() == [[0, 0, 255]]
    assert segment(color, 'fixed', 120, invert=True).tolist() == [[255, 255, 0]]


def test_binary_dimensions():
    img = np.zeros((32, 40, 3), dtype=np.uint8)
    for method in ('fixed', 'otsu', 'adaptive'):
        out = segment(img, method, block_size=7)
        assert out.shape == img.shape[:2]
        validate_mask(out)


def test_diagonal_connectivity(tmp_path):
    from pdi_lab.__main__ import components
    m = np.zeros((15, 15), np.uint8)
    m[4, 4] = m[5, 5] = 255
    assert len(components(m, 4, 0)[1]) == 2
    assert len(components(m, 8, 0)[1]) == 1


def test_open_removes_noise_and_close_fills_hole(tmp_path):
    mask = np.zeros((40, 40), np.uint8)
    mask[10:30, 10:30] = 255
    mask[20, 20] = 0
    mask[3, 3] = 255
    data = analyze(mask, tmp_path / 'sample', 8, 0, 3, 'rect', 'open,close', 1)
    final = cv2.imread(str(tmp_path/'sample_final.png'), 0)
    assert final[3, 3] == 0
    assert final[20, 20] == 255
    assert data['initial']['components_raw'] == 2
    assert data['final']['components_raw'] == 1


def test_empty_and_border(tmp_path):
    empty = np.zeros((32, 32), np.uint8)
    summary = analyze(empty, tmp_path/'empty', 4, 0, 3, 'rect', 'open,close', 1)
    assert summary['final']['components_raw'] == 0
    border = empty.copy()
    border[:12, :12] = 255
    analyze(border, tmp_path/'border', 8, 0, 3, 'rect', 'open,close', 1)


def test_invalid(tmp_path):
    m = np.zeros((20, 20), np.uint8)
    with pytest.raises(ValueError): analyze(m, tmp_path/'bad', 5, 0, 3, 'rect', 'open,close', 1)
    with pytest.raises(ValueError): analyze(m, tmp_path/'bad', 8, -1, 3, 'rect', 'open,close', 1)
    with pytest.raises(ValueError): analyze(m, tmp_path/'bad', 8, 0, 4, 'rect', 'open,close', 1)
    m[0, 0] = 42
    with pytest.raises(ValueError): analyze(m, tmp_path/'bad', 8, 0, 3, 'rect', 'open,close', 1)
    with pytest.raises(ValueError): segment(np.zeros((20,20,3),np.uint8), 'unknown')
    with pytest.raises(ValueError): segment(np.zeros((20,20,3),np.uint8), 'fixed', 300)


def test_cli_failure():
    result = subprocess.run([sys.executable,'-m','pdi_lab','--operation','segment','--input','absent.png','--output','test.png'],capture_output=True)
    assert result.returncode != 0

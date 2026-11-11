"""
Load the stereo calibration (.dat files) and triangulate 3-D points from the
two RealSense colour cameras.

Conventions (from python_stereo_camera_calibrate):
  * camera0 is the world origin (R = I, T = 0)
  * camera1 pose is given relative to camera0 as R, T
  * T is in the same unit as the checkerboard square size used for
    calibration (normally millimetres)

Example
-------
    from stereo import load_session, triangulate
    cams = load_session("session2_updated")
    X = triangulate(cams, uv_cam0=[(640, 360)], uv_cam1=[(610, 355)])
    print(X)   # (N, 3) points in camera0 coordinates
"""
from __future__ import annotations

import os
import numpy as np
import cv2


def _read_blocks(path: str) -> dict[str, np.ndarray]:
    """Parse 'name:' headers followed by rows of numbers."""
    blocks, key = {}, None
    with open(path) as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.endswith(":"):
                key = line[:-1]
                blocks[key] = []
            else:
                blocks[key].append([float(v) for v in line.split()])
    return {k: np.array(v) for k, v in blocks.items()}


def load_camera(folder: str, idx: int) -> dict:
    intr = _read_blocks(os.path.join(folder, f"camera{idx}_intrinsics.dat"))
    ext = _read_blocks(os.path.join(folder, f"camera{idx}_rot_trans.dat"))
    K = intr["intrinsic"]
    dist = intr["distortion"].ravel()
    R = ext["R"]
    T = ext["T"].reshape(3, 1)
    return {"K": K, "dist": dist, "R": R, "T": T, "P": K @ np.hstack([R, T])}


def load_session(folder: str) -> list[dict]:
    """Returns [camera0, camera1]."""
    here = os.path.dirname(os.path.abspath(__file__))
    if not os.path.isabs(folder):
        folder = os.path.join(here, folder)
    return [load_camera(folder, 0), load_camera(folder, 1)]


def triangulate(cams: list[dict], uv_cam0, uv_cam1) -> np.ndarray:
    """Pixel coordinates (N, 2) in each camera -> (N, 3) points in camera0 frame.

    Pixels are undistorted first, so raw image coordinates (e.g. OpenPose
    keypoints) can be passed directly.
    """
    pts = []
    for cam, uv in zip(cams, (uv_cam0, uv_cam1)):
        uv = np.asarray(uv, dtype=np.float64).reshape(-1, 1, 2)
        und = cv2.undistortPoints(uv, cam["K"], cam["dist"], P=cam["K"])
        pts.append(und.reshape(-1, 2).T)
    X = cv2.triangulatePoints(cams[0]["P"], cams[1]["P"], pts[0], pts[1])
    return (X[:3] / X[3]).T


def distortion_valid(cam: dict, uv, tol_px: float = 1.0) -> np.ndarray:
    """True where the distortion model can be inverted reliably at these pixels.

    The saved coefficients have very large k2/k3 terms, and the model stops
    being invertible roughly 250-340 px from the image centre. Points flagged
    False should not be trusted for undistortion or triangulation.
    """
    uv = np.asarray(uv, dtype=np.float64).reshape(-1, 1, 2)
    n = cv2.undistortPoints(uv, cam["K"], cam["dist"]).reshape(-1, 2)
    obj = np.hstack([n, np.ones((len(n), 1))])
    back = cv2.projectPoints(obj, np.zeros(3), np.zeros(3), cam["K"], cam["dist"])[0]
    return np.linalg.norm(back.reshape(-1, 2) - uv.reshape(-1, 2), axis=1) < tol_px


def describe(cams: list[dict]) -> str:
    R, T = cams[1]["R"], cams[1]["T"].ravel()
    angle = np.degrees(np.arccos(np.clip((np.trace(R) - 1) / 2, -1, 1)))
    return (f"camera1 is rotated {angle:.1f} deg relative to camera0, "
            f"baseline {np.linalg.norm(T):.1f} units, T = {np.round(T, 1)}")


if __name__ == "__main__":
    import sys
    session = sys.argv[1] if len(sys.argv) > 1 else "session2_updated"
    cams = load_session(session)
    print(session + ":", describe(cams))
    us, vs = np.meshgrid(np.linspace(0, 1279, 129), np.linspace(0, 719, 73))
    grid = np.stack([us.ravel(), vs.ravel()], 1)
    for i, cam in enumerate(cams):
        print(f"  camera{i}: distortion model valid on "
              f"{100 * distortion_valid(cam, grid).mean():.0f}% of a 1280x720 frame")

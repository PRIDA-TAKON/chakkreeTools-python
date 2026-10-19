"""
3D Rebar Polyline and Tubular Mesh Generator for IngeTrazo Viewport
Standard Thai Rebar Shapes according to TIS / EIT (วสท. / มอก.)

Original Author / Extension: Chakkree Tools Port
"""

import math
from typing import Any, Dict, List, Tuple

Vector3 = Tuple[float, float, float]


def _norm(v: Vector3) -> float:
    return math.hypot(v[0], v[1], v[2])


def _normalize(v: Vector3) -> Vector3:
    n = _norm(v)
    if n < 1e-9:
        return (1.0, 0.0, 0.0)
    return (v[0] / n, v[1] / n, v[2] / n)


def _cross(a: Vector3, b: Vector3) -> Vector3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a: Vector3, b: Vector3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _add(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a: Vector3, b: Vector3) -> Vector3:
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _scale(v: Vector3, s: float) -> Vector3:
    return (v[0] * s, v[1] * s, v[2] * s)


def _rotate_vector(v: Vector3, axis: Vector3, angle: float) -> Vector3:
    """Rotates vector v around unit axis by angle radians using Rodrigues' formula."""
    cos_a = math.cos(angle)
    sin_a = math.sin(angle)
    cross_av = _cross(axis, v)
    dot_av = _dot(axis, v)

    term1 = _scale(v, cos_a)
    term2 = _scale(cross_av, sin_a)
    term3 = _scale(axis, dot_av * (1.0 - cos_a))
    return _add(_add(term1, term2), term3)


def generate_shape_00(
    length: float,
    diameter: float = 0.012,
    origin: Vector3 = (0.0, 0.0, 0.0),
    direction: Vector3 = (1.0, 0.0, 0.0),
) -> List[Vector3]:
    """
    Shape 00: Straight bar (เหล็กเส้นตรง)
    Generates a 3D polyline for a straight rebar segment.
    """
    dx, dy, dz = direction
    norm = math.hypot(dx, dy, dz)
    if norm > 1e-9:
        dx, dy, dz = dx / norm, dy / norm, dz / norm
    else:
        dx, dy, dz = 1.0, 0.0, 0.0

    ox, oy, oz = origin
    p0 = (ox, oy, oz)
    p1 = (ox + dx * length, oy + dy * length, oz + dz * length)
    return [p0, p1]


def generate_shape_21(
    length: float,
    hook_start: float = 0.20,
    hook_end: float = 0.20,
    diameter: float = 0.012,
    origin: Vector3 = (0.0, 0.0, 0.0),
    direction: Vector3 = (1.0, 0.0, 0.0),
    hook_direction: Vector3 = (0.0, 0.0, 1.0),
) -> List[Vector3]:
    """
    Shape 21: U-bent bar with 90-degree hooks for beam main bars (เหล็กนอนดัดฉาก)
    Generates a 3D polyline with 90-degree hooks at both ends.
    """
    dx, dy, dz = direction
    norm_dir = math.hypot(dx, dy, dz)
    if norm_dir > 1e-9:
        dx, dy, dz = dx / norm_dir, dy / norm_dir, dz / norm_dir
    else:
        dx, dy, dz = 1.0, 0.0, 0.0

    hx, hy, hz = hook_direction
    norm_hook = math.hypot(hx, hy, hz)
    if norm_hook > 1e-9:
        hx, hy, hz = hx / norm_hook, hy / norm_hook, hz / norm_hook
    else:
        hx, hy, hz = 0.0, 0.0, 1.0

    ox, oy, oz = origin

    # Start hook tip -> start bend -> end bend -> end hook tip
    p0 = (ox + hx * hook_start, oy + hy * hook_start, oz + hz * hook_start)
    p1 = (ox, oy, oz)
    p2 = (ox + dx * length, oy + dy * length, oz + dz * length)
    p3 = (p2[0] + hx * hook_end, p2[1] + hy * hook_end, p2[2] + hz * hook_end)

    return [p0, p1, p2, p3]


def generate_shape_41(
    width: float,
    depth: float,
    hook_length: float = 0.075,
    diameter: float = 0.009,
    origin: Vector3 = (0.0, 0.0, 0.0),
) -> List[Vector3]:
    """
    Shape 41: Rectangular closed stirrup with 135-degree seismic hooks (เหล็กปลอก)
    Generates 3D polyline in the XY plane centered/offset at origin.
    The hooks bend 135 degrees inward into the section core.
    """
    ox, oy, oz = origin
    w = width
    d = depth

    cos45 = 0.70710678
    sin45 = 0.70710678

    hk1_x = ox + hook_length * cos45
    hk1_y = oy + d - hook_length * sin45
    hk1_z = oz

    c0 = (ox, oy + d, oz)
    c1 = (ox + w, oy + d, oz)
    c2 = (ox + w, oy, oz)
    c3 = (ox, oy, oz)
    c4 = (ox, oy + d, oz)

    hk2_x = ox + hook_length * sin45
    hk2_y = oy + d - hook_length * cos45
    hk2_z = oz

    return [(hk1_x, hk1_y, hk1_z), c0, c1, c2, c3, c4, (hk2_x, hk2_y, hk2_z)]


def generate_shape_99(
    height: float,
    dowel_length: float = 0.30,
    diameter: float = 0.016,
    origin: Vector3 = (0.0, 0.0, 0.0),
    dowel_direction: Vector3 = (1.0, 0.0, 0.0),
) -> List[Vector3]:
    """
    Shape 99: Column vertical bar with 90-degree foundation dowel bend (เหล็กยืนเสาฝากฐานราก)
    Generates 3D polyline from foundation dowel L-bend up to column top.
    """
    ox, oy, oz = origin

    dx, dy, dz = dowel_direction
    norm = math.hypot(dx, dy, dz)
    if norm > 1e-9:
        dx, dy, dz = dx / norm, dy / norm, dz / norm
    else:
        dx, dy, dz = 1.0, 0.0, 0.0

    p0 = (ox + dx * dowel_length, oy + dy * dowel_length, oz)
    p1 = (ox, oy, oz)
    p2 = (ox, oy, oz + height)

    return [p0, p1, p2]


def generate_tubular_mesh(
    polyline: List[Vector3],
    diameter: float,
    radial_segments: int = 8,
    close_caps: bool = True,
) -> Dict[str, Any]:
    """
    Generates a 3D tubular mesh around a 3D polyline path.
    Returns dictionary with vertices, triangle indices, line indices, and polyline points ready
    for IngeTrazo 3D canvas rendering.
    """
    # Filter out consecutive duplicate points
    filtered_points: List[Vector3] = []
    for pt in polyline:
        if not filtered_points or _norm(_sub(pt, filtered_points[-1])) > 1e-6:
            filtered_points.append(pt)

    if len(filtered_points) < 2:
        return {
            "vertices": [],
            "indices": [],
            "line_indices": [],
            "polyline": [list(p) for p in polyline],
        }

    n_points = len(filtered_points)
    radius = diameter / 2.0

    # Calculate segment tangents
    seg_tangents = [
        _normalize(_sub(filtered_points[i + 1], filtered_points[i]))
        for i in range(n_points - 1)
    ]

    # Calculate vertex tangents
    vertex_tangents: List[Vector3] = []
    for i in range(n_points):
        if i == 0:
            vertex_tangents.append(seg_tangents[0])
        elif i == n_points - 1:
            vertex_tangents.append(seg_tangents[-1])
        else:
            vertex_tangents.append(
                _normalize(_add(seg_tangents[i - 1], seg_tangents[i]))
            )

    # Parallel transport frames
    normals: List[Vector3] = []
    binormals: List[Vector3] = []

    # Initial frame at index 0
    t0 = vertex_tangents[0]
    up = (0.0, 0.0, 1.0) if abs(_dot(t0, (0.0, 0.0, 1.0))) < 0.9 else (1.0, 0.0, 0.0)
    b0 = _normalize(_cross(t0, up))
    n0 = _cross(b0, t0)
    normals.append(n0)
    binormals.append(b0)

    # Propagate frame along path
    for i in range(1, n_points):
        t_prev = vertex_tangents[i - 1]
        t_curr = vertex_tangents[i]
        axis = _cross(t_prev, t_curr)
        axis_len = _norm(axis)

        if axis_len > 1e-6:
            axis_unit = _scale(axis, 1.0 / axis_len)
            dot_val = max(-1.0, min(1.0, _dot(t_prev, t_curr)))
            angle = math.acos(dot_val)
            n_curr = _rotate_vector(normals[-1], axis_unit, angle)
            b_curr = _rotate_vector(binormals[-1], axis_unit, angle)
        else:
            n_curr = normals[-1]
            b_curr = binormals[-1]

        normals.append(n_curr)
        binormals.append(b_curr)

    # Generate ring vertices
    mesh_vertices: List[List[float]] = []
    for i in range(n_points):
        pt = filtered_points[i]
        norm = normals[i]
        binorm = binormals[i]

        for j in range(radial_segments):
            angle = 2.0 * math.pi * j / radial_segments
            cos_a = math.cos(angle)
            sin_a = math.sin(angle)

            vx = pt[0] + radius * (cos_a * norm[0] + sin_a * binorm[0])
            vy = pt[1] + radius * (cos_a * norm[1] + sin_a * binorm[1])
            vz = pt[2] + radius * (cos_a * norm[2] + sin_a * binorm[2])
            mesh_vertices.append([round(vx, 6), round(vy, 6), round(vz, 6)])

    indices: List[List[int]] = []
    line_indices: List[List[int]] = []

    # Tube cylinder quad faces & ring lines
    for i in range(n_points - 1):
        ring_a = i * radial_segments
        ring_b = (i + 1) * radial_segments

        for j in range(radial_segments):
            next_j = (j + 1) % radial_segments

            idx_a1 = ring_a + j
            idx_a2 = ring_a + next_j
            idx_b1 = ring_b + j
            idx_b2 = ring_b + next_j

            # Two triangles per quad face
            indices.append([idx_a1, idx_b1, idx_a2])
            indices.append([idx_a2, idx_b1, idx_b2])

            # Wireframe line segments
            line_indices.append([idx_a1, idx_a2])
            line_indices.append([idx_a1, idx_b1])

    # Ring lines for last ring
    last_ring = (n_points - 1) * radial_segments
    for j in range(radial_segments):
        next_j = (j + 1) % radial_segments
        line_indices.append([last_ring + j, last_ring + next_j])

    # End caps
    if close_caps:
        # Start cap
        start_cap_idx = len(mesh_vertices)
        p_start = filtered_points[0]
        mesh_vertices.append([round(p_start[0], 6), round(p_start[1], 6), round(p_start[2], 6)])

        # End cap
        end_cap_idx = len(mesh_vertices)
        p_end = filtered_points[-1]
        mesh_vertices.append([round(p_end[0], 6), round(p_end[1], 6), round(p_end[2], 6)])

        for j in range(radial_segments):
            next_j = (j + 1) % radial_segments
            # Start cap triangles
            indices.append([start_cap_idx, j, next_j])
            # End cap triangles
            indices.append([end_cap_idx, last_ring + next_j, last_ring + j])

    return {
        "vertices": mesh_vertices,
        "indices": indices,
        "line_indices": line_indices,
        "polyline": [list(p) for p in polyline],
    }

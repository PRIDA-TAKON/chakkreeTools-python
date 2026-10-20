"""
3D Rebar Polyline and Tubular Mesh Generator for IngeTrazo Viewport
Standard Thai Rebar Shapes according to TIS / EIT (วสท. / มอก.)

Original Author / Extension: Chakkree Tools Port
"""

import math
import re
from typing import Any, Dict, List, Optional, Tuple, Union

Vector3 = Tuple[float, float, float]

DEFAULT_REBAR_COLORS: Dict[str, str] = {
    "RB6": "#B0C4DE",
    "RB9": "#4682B4",
    "DB12": "#2E8B57",
    "DB16": "#FF8C00",
    "DB20": "#DC143C",
    "DB25": "#8B0000",
    "DB28": "#4B0082",
    "DB32": "#2F4F4F",
}


def get_rebar_color(size_or_dia: Union[str, float, int]) -> str:
    """
    Returns hex color string matching standard rebar size designation or diameter.
    Supports inputs like 'DB16', 'RB6', '16', 0.016, 16, 'RB9@0.15'.
    """
    if isinstance(size_or_dia, (int, float)):
        # Convert diameter in meters (e.g. 0.016 -> 16mm)
        mm = round(size_or_dia * 1000) if size_or_dia < 1.0 else round(size_or_dia)
        size_key = f"DB{mm}" if mm >= 12 else f"RB{mm}"
    else:
        s = str(size_or_dia).strip().upper()
        m = re.search(r"(RB|DB)\s*(\d+)", s)
        if m:
            size_key = f"{m.group(1)}{m.group(2)}"
        elif s.isdigit():
            mm = int(s)
            size_key = f"DB{mm}" if mm >= 12 else f"RB{mm}"
        else:
            m = re.search(r"(\d+)", s)
            if m:
                num = int(m.group(1))
                prefix = "DB" if num >= 12 else "RB"
                size_key = f"{prefix}{num}"
            else:
                size_key = "DB12"

    return DEFAULT_REBAR_COLORS.get(size_key, "#2E8B57")


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
    radial_segments: int = 6,
    close_caps: bool = True,
) -> Dict[str, Any]:
    """
    Generates a 3D tubular mesh around a 3D polyline path.
    Returns dictionary with vertices, triangle indices, faces (3D face vertex loops), line indices,
    and polyline points ready for IngeTrazo 3D canvas rendering.
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
            "faces": [],
            "line_indices": [],
            "polyline": [[round(p[0], 4), round(p[1], 4), round(p[2], 4)] for p in polyline],
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
            mesh_vertices.append([round(vx, 4), round(vy, 4), round(vz, 4)])

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
        mesh_vertices.append([round(p_start[0], 4), round(p_start[1], 4), round(p_start[2], 4)])

        # End cap
        end_cap_idx = len(mesh_vertices)
        p_end = filtered_points[-1]
        mesh_vertices.append([round(p_end[0], 4), round(p_end[1], 4), round(p_end[2], 4)])

        for j in range(radial_segments):
            next_j = (j + 1) % radial_segments
            # Start cap triangles
            indices.append([start_cap_idx, j, next_j])
            # End cap triangles
            indices.append([end_cap_idx, last_ring + next_j, last_ring + j])

    # Generate 3D point face loops for direct viewport mesh scene additions
    faces: List[List[List[float]]] = []
    for tri in indices:
        v0 = mesh_vertices[tri[0]]
        v1 = mesh_vertices[tri[1]]
        v2 = mesh_vertices[tri[2]]
        faces.append([
            [v0[0], v0[1], v0[2]],
            [v1[0], v1[1], v1[2]],
            [v2[0], v2[1], v2[2]],
        ])

    return {
        "vertices": mesh_vertices,
        "indices": indices,
        "faces": faces,
        "line_indices": line_indices,
        "polyline": [[round(p[0], 4), round(p[1], 4), round(p[2], 4)] for p in polyline],
    }


def generate_column_rebar_cage(column: Any) -> List[Dict[str, Any]]:
    """
    Generates 3D rebar cage meshes (main bars and stirrups) for a Column.
    Returns list of rebar mesh dicts with color mapping.
    """
    pos = getattr(column, "position", (0.0, 0.0))
    x_c, y_c = pos[0], pos[1]
    z_bot = float(getattr(column, "elevation", 0.0))
    height = float(getattr(column, "height", 3.50))
    width = float(getattr(column, "width", 0.30))
    depth = float(getattr(column, "depth", 0.30))
    covering = float(getattr(column, "covering", 0.030))
    main_count = int(getattr(column, "main_bar_count", 8))
    main_dia = float(getattr(column, "main_bar_dia", 0.016))
    stirrup_dia = float(getattr(column, "stirrup_dia", 0.009))
    stirrup_space = float(getattr(column, "stirrup_spacing", 0.150))
    profile = str(getattr(column, "profile", "RECTANGULAR")).upper()

    main_color = get_rebar_color(main_dia)
    stirrup_color = get_rebar_color(stirrup_dia)

    rebar_cages: List[Dict[str, Any]] = []

    # Inner core bounds
    half_w = width / 2.0 - covering - stirrup_dia - main_dia / 2.0
    half_d = depth / 2.0 - covering - stirrup_dia - main_dia / 2.0

    # Main longitudinal bar coordinates
    main_coords: List[Tuple[float, float]] = []
    if profile == "CIRCULAR":
        r = width / 2.0 - covering - stirrup_dia - main_dia / 2.0
        for i in range(main_count):
            angle = 2.0 * math.pi * i / main_count
            main_coords.append((x_c + r * math.cos(angle), y_c + r * math.sin(angle)))
    else:
        # Rectangular column layout (4, 6, 8, 12, 14, 16 bars)
        # Always 4 corner bars
        corners = [
            (x_c - half_w, y_c - half_d),
            (x_c + half_w, y_c - half_d),
            (x_c + half_w, y_c + half_d),
            (x_c - half_w, y_c + half_d),
        ]
        main_coords.extend(corners)

        rem_bars = main_count - 4
        if rem_bars > 0:
            # Distribute remaining bars along width & depth
            side_bars = rem_bars // 4
            for i in range(1, side_bars + 1):
                frac = i / (side_bars + 1)
                # Bottom & top sides (along X)
                main_coords.append((x_c - half_w + 2 * half_w * frac, y_c - half_d))
                main_coords.append((x_c - half_w + 2 * half_w * frac, y_c + half_d))
                # Left & right sides (along Y)
                main_coords.append((x_c - half_w, y_c - half_d + 2 * half_d * frac))
                main_coords.append((x_c + half_w, y_c - half_d + 2 * half_d * frac))

    # Generate main bars (Shape 99 or Shape 00)
    dowel_len = 0.30
    for idx, (bx, by) in enumerate(main_coords):
        # Dowel direction points outward/inward
        d_dir = (1.0 if bx >= x_c else -1.0, 1.0 if by >= y_c else -1.0, 0.0)
        polyline = generate_shape_99(
            height=height,
            dowel_length=dowel_len,
            diameter=main_dia,
            origin=(bx, by, z_bot),
            dowel_direction=d_dir,
        )
        mesh = generate_tubular_mesh(polyline, diameter=main_dia, radial_segments=6)
        rebar_cages.append({
            "type": "main_bar",
            "size": f"DB{int(main_dia*1000)}" if main_dia >= 0.012 else f"RB{int(main_dia*1000)}",
            "diameter": main_dia,
            "color": main_color,
            "mesh": mesh,
            "faces": mesh["faces"],
            "polyline": [[round(pt[0], 4), round(pt[1], 4), round(pt[2], 4)] for pt in polyline],
        })

    # Generate stirrups along column height
    stirrup_w = width - 2.0 * covering
    stirrup_d = depth - 2.0 * covering
    stirrup_st_z = z_bot + covering
    stirrup_end_z = z_bot + height - covering
    z_curr = stirrup_st_z

    while z_curr <= stirrup_end_z:
        if profile == "CIRCULAR":
            # Circular stirrup / ring
            r_stirrup = width / 2.0 - covering
            ring_pts = []
            segs = 12
            for s in range(segs + 1):
                ang = 2.0 * math.pi * s / segs
                ring_pts.append((x_c + r_stirrup * math.cos(ang), y_c + r_stirrup * math.sin(ang), z_curr))
            polyline = ring_pts
        else:
            origin_st = (x_c - stirrup_w / 2.0, y_c - stirrup_d / 2.0, z_curr)
            polyline = generate_shape_41(
                width=stirrup_w,
                depth=stirrup_d,
                hook_length=0.075,
                diameter=stirrup_dia,
                origin=origin_st,
            )

        mesh = generate_tubular_mesh(polyline, diameter=stirrup_dia, radial_segments=6)
        rebar_cages.append({
            "type": "stirrup",
            "size": f"RB{int(stirrup_dia*1000)}",
            "diameter": stirrup_dia,
            "color": stirrup_color,
            "mesh": mesh,
            "faces": mesh["faces"],
            "polyline": [[round(pt[0], 4), round(pt[1], 4), round(pt[2], 4)] for pt in polyline],
        })
        z_curr += stirrup_space

    return rebar_cages


def generate_beam_rebar_cage(beam: Any) -> List[Dict[str, Any]]:
    """
    Generates 3D rebar cage meshes (top, bottom, extra bars and stirrups) for a Beam.
    Returns list of rebar mesh dicts with color mapping.
    """
    start_pt = getattr(beam, "start_point", (0.0, 0.0))
    end_pt = getattr(beam, "end_point", (4.0, 0.0))
    width = float(getattr(beam, "width", 0.20))
    depth = float(getattr(beam, "depth", 0.40))
    elevation = float(getattr(beam, "elevation", 3.20))  # Top of beam
    covering = float(getattr(beam, "covering", 0.025))

    top_spec = str(getattr(beam, "top_bar_spec", "2DB12"))
    bot_spec = str(getattr(beam, "bot_bar_spec", "3DB12"))
    extra_spec = str(getattr(beam, "extra_bar_spec", "")) or ""
    stirrup_spec = str(getattr(beam, "stirrup_spec", "RB6@0.175"))

    # Helper function to parse specs like "2DB12" -> (count=2, dia=0.012)
    def parse_bar_spec(spec: str) -> Tuple[int, float]:
        m = re.match(r"(\d+)?\s*(RB|DB)?\s*(\d+)", spec.strip().upper())
        if m:
            cnt = int(m.group(1)) if m.group(1) else 1
            dia_mm = int(m.group(3))
            return cnt, dia_mm / 1000.0
        return 2, 0.012

    top_cnt, top_dia = parse_bar_spec(top_spec)
    bot_cnt, bot_dia = parse_bar_spec(bot_spec)

    def parse_stirrup_spec(spec: str) -> Tuple[float, float]:
        m = re.match(r"(RB|DB)?(\d+)\s*@\s*([\d\.]+)", spec.strip().upper())
        if m:
            s_dia = int(m.group(2)) / 1000.0
            s_sp = float(m.group(3))
            return s_dia, s_sp
        return 0.006, 0.175

    stirrup_dia, stirrup_sp = parse_stirrup_spec(stirrup_spec)

    dx = end_pt[0] - start_pt[0]
    dy = end_pt[1] - start_pt[1]
    L = math.hypot(dx, dy)
    if L < 1e-6:
        return []

    dir_x = dx / L
    dir_y = dy / L
    # Normal vector perpendicular to beam direction in XY plane
    norm_x = -dir_y
    norm_y = dir_x

    z_top_bar = elevation - covering - stirrup_dia - top_dia / 2.0
    z_bot_bar = elevation - depth + covering + stirrup_dia + bot_dia / 2.0

    rebar_cages: List[Dict[str, Any]] = []

    # Top main bars
    top_w = width - 2.0 * covering - 2.0 * stirrup_dia - top_dia
    for i in range(top_cnt):
        offset_w = -top_w / 2.0 + (top_w * i / (top_cnt - 1) if top_cnt > 1 else 0.0)
        p_start = (
            start_pt[0] + norm_x * offset_w,
            start_pt[1] + norm_y * offset_w,
            z_top_bar,
        )
        polyline = generate_shape_21(
            length=L,
            hook_start=0.20,
            hook_end=0.20,
            diameter=top_dia,
            origin=p_start,
            direction=(dir_x, dir_y, 0.0),
            hook_direction=(0.0, 0.0, -1.0),  # Top hooks bend downward
        )
        mesh = generate_tubular_mesh(polyline, diameter=top_dia, radial_segments=6)
        rebar_cages.append({
            "type": "top_main_bar",
            "size": f"DB{int(top_dia*1000)}" if top_dia >= 0.012 else f"RB{int(top_dia*1000)}",
            "diameter": top_dia,
            "color": get_rebar_color(top_dia),
            "mesh": mesh,
            "faces": mesh["faces"],
            "polyline": [[round(pt[0], 4), round(pt[1], 4), round(pt[2], 4)] for pt in polyline],
        })

    # Bottom main bars
    bot_w = width - 2.0 * covering - 2.0 * stirrup_dia - bot_dia
    for i in range(bot_cnt):
        offset_w = -bot_w / 2.0 + (bot_w * i / (bot_cnt - 1) if bot_cnt > 1 else 0.0)
        p_start = (
            start_pt[0] + norm_x * offset_w,
            start_pt[1] + norm_y * offset_w,
            z_bot_bar,
        )
        polyline = generate_shape_21(
            length=L,
            hook_start=0.20,
            hook_end=0.20,
            diameter=bot_dia,
            origin=p_start,
            direction=(dir_x, dir_y, 0.0),
            hook_direction=(0.0, 0.0, 1.0),  # Bottom hooks bend upward
        )
        mesh = generate_tubular_mesh(polyline, diameter=bot_dia, radial_segments=6)
        rebar_cages.append({
            "type": "bot_main_bar",
            "size": f"DB{int(bot_dia*1000)}" if bot_dia >= 0.012 else f"RB{int(bot_dia*1000)}",
            "diameter": bot_dia,
            "color": get_rebar_color(bot_dia),
            "mesh": mesh,
            "faces": mesh["faces"],
            "polyline": [[round(pt[0], 4), round(pt[1], 4), round(pt[2], 4)] for pt in polyline],
        })

    # Extra bars if spec present
    if extra_spec:
        ex_cnt, ex_dia = parse_bar_spec(extra_spec)
        ex_len = L / 3.0
        ex_start_offset = L / 3.0
        z_ex_bar = z_bot_bar + ex_dia + 0.005
        ex_w = width - 2.0 * covering - 2.0 * stirrup_dia - ex_dia
        for i in range(ex_cnt):
            offset_w = -ex_w / 2.0 + (ex_w * i / (ex_cnt - 1) if ex_cnt > 1 else 0.0)
            p_start = (
                start_pt[0] + dir_x * ex_start_offset + norm_x * offset_w,
                start_pt[1] + dir_y * ex_start_offset + norm_y * offset_w,
                z_ex_bar,
            )
            polyline = generate_shape_00(
                length=ex_len,
                diameter=ex_dia,
                origin=p_start,
                direction=(dir_x, dir_y, 0.0),
            )
            mesh = generate_tubular_mesh(polyline, diameter=ex_dia, radial_segments=6)
            rebar_cages.append({
                "type": "extra_bar",
                "size": f"DB{int(ex_dia*1000)}" if ex_dia >= 0.012 else f"RB{int(ex_dia*1000)}",
                "diameter": ex_dia,
                "color": get_rebar_color(ex_dia),
                "mesh": mesh,
                "faces": mesh["faces"],
                "polyline": [[round(pt[0], 4), round(pt[1], 4), round(pt[2], 4)] for pt in polyline],
            })

    # Stirrups along span
    stirrup_w = width - 2.0 * covering
    stirrup_d = depth - 2.0 * covering
    st_z = elevation - depth + covering

    dist = covering
    while dist <= L - covering:
        # Stirrup center point in XY
        st_x = start_pt[0] + dir_x * dist
        st_y = start_pt[1] + dir_y * dist

        # Stirrup 3D vertices (rectangular stirrup perpendicular to beam)
        half_sw = stirrup_w / 2.0
        hk_len = 0.075

        # Corners in beam local CS (along normal and vertical)
        c0 = (st_x - norm_x * half_sw, st_y - norm_y * half_sw, st_z + stirrup_d)
        c1 = (st_x + norm_x * half_sw, st_y + norm_y * half_sw, st_z + stirrup_d)
        c2 = (st_x + norm_x * half_sw, st_y + norm_y * half_sw, st_z)
        c3 = (st_x - norm_x * half_sw, st_y - norm_y * half_sw, st_z)
        c4 = c0

        cos45, sin45 = 0.7071, 0.7071
        hk1 = (c0[0] + norm_x * hk_len * cos45, c0[1] + norm_y * hk_len * cos45, c0[2] - hk_len * sin45)
        hk2 = (c0[0] + norm_x * hk_len * sin45, c0[1] + norm_y * hk_len * sin45, c0[2] - hk_len * cos45)

        polyline = [hk1, c0, c1, c2, c3, c4, hk2]
        mesh = generate_tubular_mesh(polyline, diameter=stirrup_dia, radial_segments=6)
        rebar_cages.append({
            "type": "stirrup",
            "size": f"RB{int(stirrup_dia*1000)}",
            "diameter": stirrup_dia,
            "color": get_rebar_color(stirrup_dia),
            "mesh": mesh,
            "faces": mesh["faces"],
            "polyline": [[round(pt[0], 4), round(pt[1], 4), round(pt[2], 4)] for pt in polyline],
        })
        dist += stirrup_sp

    return rebar_cages


def generate_footing_rebar_cage(footing: Any) -> List[Dict[str, Any]]:
    """
    Generates 3D rebar cage meshes (bottom rebar grid) for a Footing / PileCap.
    Returns list of rebar mesh dicts with color mapping.
    """
    pos = getattr(footing, "position", (0.0, 0.0))
    x_c, y_c = pos[0], pos[1]
    width = float(getattr(footing, "width", getattr(footing, "section_x", 1.20)))
    length = float(getattr(footing, "length", getattr(footing, "section_y", 1.20)))
    thickness = float(getattr(footing, "thickness", 0.35))
    elevation = float(getattr(footing, "elevation", -0.70))  # Top level
    covering = float(getattr(footing, "covering", 0.070))

    rebar_x_count = int(getattr(footing, "rebar_x_count", 5))
    rebar_x_dia = float(getattr(footing, "rebar_x_dia", getattr(footing, "rebar_dia", 0.012)))
    rebar_y_count = int(getattr(footing, "rebar_y_count", 5))
    rebar_y_dia = float(getattr(footing, "rebar_y_dia", getattr(footing, "rebar_dia", 0.012)))

    z_bot = elevation - thickness + covering

    rebar_cages: List[Dict[str, Any]] = []

    # X-direction rebars (bottom layer)
    len_x = width - 2.0 * covering
    y_span = length - 2.0 * covering
    hook_h = thickness - 2.0 * covering

    for i in range(rebar_y_count):
        y_pos = y_c - y_span / 2.0 + (y_span * i / (rebar_y_count - 1) if rebar_y_count > 1 else 0.0)
        p_start = (x_c - len_x / 2.0, y_pos, z_bot + rebar_x_dia / 2.0)
        polyline = generate_shape_21(
            length=len_x,
            hook_start=hook_h,
            hook_end=hook_h,
            diameter=rebar_x_dia,
            origin=p_start,
            direction=(1.0, 0.0, 0.0),
            hook_direction=(0.0, 0.0, 1.0),
        )
        mesh = generate_tubular_mesh(polyline, diameter=rebar_x_dia, radial_segments=6)
        rebar_cages.append({
            "type": "bot_mesh_x",
            "size": f"DB{int(rebar_x_dia*1000)}" if rebar_x_dia >= 0.012 else f"RB{int(rebar_x_dia*1000)}",
            "diameter": rebar_x_dia,
            "color": get_rebar_color(rebar_x_dia),
            "mesh": mesh,
            "faces": mesh["faces"],
            "polyline": [[round(pt[0], 4), round(pt[1], 4), round(pt[2], 4)] for pt in polyline],
        })

    # Y-direction rebars (layer on top of X-rebar)
    len_y = length - 2.0 * covering
    x_span = width - 2.0 * covering
    z_bot_y = z_bot + rebar_x_dia + rebar_y_dia / 2.0

    for i in range(rebar_x_count):
        x_pos = x_c - x_span / 2.0 + (x_span * i / (rebar_x_count - 1) if rebar_x_count > 1 else 0.0)
        p_start = (x_pos, y_c - len_y / 2.0, z_bot_y)
        polyline = generate_shape_21(
            length=len_y,
            hook_start=hook_h - rebar_x_dia,
            hook_end=hook_h - rebar_x_dia,
            diameter=rebar_y_dia,
            origin=p_start,
            direction=(0.0, 1.0, 0.0),
            hook_direction=(0.0, 0.0, 1.0),
        )
        mesh = generate_tubular_mesh(polyline, diameter=rebar_y_dia, radial_segments=6)
        rebar_cages.append({
            "type": "bot_mesh_y",
            "size": f"DB{int(rebar_y_dia*1000)}" if rebar_y_dia >= 0.012 else f"RB{int(rebar_y_dia*1000)}",
            "diameter": rebar_y_dia,
            "color": get_rebar_color(rebar_y_dia),
            "mesh": mesh,
            "faces": mesh["faces"],
            "polyline": [[round(pt[0], 4), round(pt[1], 4), round(pt[2], 4)] for pt in polyline],
        })

    return rebar_cages


def generate_rebar_cage(element: Any) -> List[Dict[str, Any]]:
    """
    Generic dispatcher function to generate rebar cage meshes for any supported RC element.
    """
    cls_name = getattr(element, "class", element.__class__.__name__).lower()
    if "column" in cls_name:
        return generate_column_rebar_cage(element)
    elif "beam" in cls_name:
        return generate_beam_rebar_cage(element)
    elif "footing" in cls_name or "pile" in cls_name:
        return generate_footing_rebar_cage(element)
    return []

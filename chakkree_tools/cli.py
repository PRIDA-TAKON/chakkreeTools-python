"""
Chakkree Tools - Command Line Interface (CLI)
Zero external runtime dependencies (Pure Python Standard Library).
Original Author: Chakkree Tiyawongsuwan
Python Port & OpenBIM CLI: PRIDA-TAKON
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Any, List, Optional

from chakkree_tools.exporter.debim_exporter import DebimExporter, export_to_debim
from chakkree_tools.qto.takeoff import generate_qto_summary
from chakkree_tools.rc.beam import Beam
from chakkree_tools.rc.column import Column
from chakkree_tools.rc.footing import Footing, PileCap, PileSpec
from chakkree_tools.rc.slab import Slab


def _print_qto_table(summary: Any) -> None:
    print("\n" + "=" * 55)
    print("       CHAKKREE TOOLS - QTO & BBS REPORT       ")
    print("=" * 55)
    print(f"Total Structural Elements : {summary.total_elements}")
    print(f"Total Concrete Volume     : {summary.total_concrete_volume_m3:.3f} m3")
    print(f"Total Formwork Area       : {summary.total_formwork_area_m2:.2f} m2")
    print(f"Total Rebar Weight        : {summary.total_rebar_weight_kg:.2f} kg")
    print("-" * 55)
    print("Rebar Breakdown by Diameter (Bar Bending Schedule):")
    for bar_type, wt in summary.rebar_weight_by_size.items():
        print(f"  • {bar_type:<8}: {wt:>8.2f} kg")
    print("=" * 55 + "\n")


def _try_stream_to_bridge(elements: List[Any], host: str = "127.0.0.1", port: int = 8482) -> bool:
    try:
        from chakkree_tools.ingetrazo_plugin.agent_streamer import stream_to_ingetrazo
        exporter = DebimExporter(project_name="Chakkree CLI Stream")
        for el in elements:
            exporter.add_element(el)
        yaml_content = exporter.to_yaml()
        ok = stream_to_ingetrazo(yaml_content, host=host, port=port)
        if ok:
            print(f"[CLI] Successfully streamed {len(elements)} element(s) to IngeTrazo at http://{host}:{port}")
        else:
            print(f"[CLI] Notice: IngeTrazo Agent Bridge not reachable on port {port} (streaming skipped)")
        return ok
    except Exception as e:
        print(f"[CLI] Streaming skipped: {e}")
        return False


def _save_or_print_debim(elements: List[Any], output_file: Optional[str], project_name: str) -> None:
    exporter = DebimExporter(project_name=project_name)
    for el in elements:
        exporter.add_element(el)
    yaml_text = exporter.to_yaml()
    if output_file:
        out_p = Path(output_file)
        out_p.parent.mkdir(parents=True, exist_ok=True)
        out_p.write_text(yaml_text, encoding="utf-8")
        print(f"[CLI] Exported .debim manifest to: {out_p.resolve()}")
    else:
        print(yaml_text)


def handle_footing(args: argparse.Namespace) -> int:
    elements = []
    if args.piles is not None:
        f = PileCap.create_n_piles(
            id_str=args.id,
            pile_count=args.piles,
            pile_size=args.pile_size,
            thickness=args.thickness,
            elevation=args.elevation,
            covering=args.covering,
            rebar_dia=args.rebar_dia,
        )
    else:
        f = Footing(
            id=args.id,
            name=args.name or f"Footing_{args.id}",
            width=args.width,
            length=args.length,
            thickness=args.thickness,
            elevation=args.elevation,
            covering=args.covering,
            rebar_x_count=args.rebar_x_count,
            rebar_x_dia=args.rebar_x_dia,
            rebar_y_count=args.rebar_y_count,
            rebar_y_dia=args.rebar_y_dia,
        )
    elements.append(f)

    print(f"[CLI] Created Footing: ID={f.id}, Size={f.width:.2f}x{f.length:.2f}m, Thickness={f.thickness:.2f}m, Elevation={f.elevation:.2f}m")
    print(f"      Concrete={f.concrete_volume:.3f} m3, Formwork={f.formwork_area:.2f} m2")

    if args.qto:
        summary = generate_qto_summary(elements)
        _print_qto_table(summary)

    if args.stream:
        _try_stream_to_bridge(elements, host=args.host, port=args.port)

    if args.out:
        _save_or_print_debim(elements, args.out, project_name=f"Footing {args.id}")

    return 0


def handle_column(args: argparse.Namespace) -> int:
    pos = tuple(map(float, args.position.split(","))) if args.position else (0.0, 0.0)
    c = Column(
        id=args.id,
        name=args.name or f"Column_{args.id}",
        profile=args.profile.upper(),
        width=args.width,
        depth=args.depth,
        height=args.height,
        elevation=args.elevation,
        position=pos,
        main_bar_count=args.bars,
        main_bar_dia=args.bar_dia,
        stirrup_dia=args.stirrup_dia,
        stirrup_spacing=args.stirrup_spacing,
        covering=args.covering,
    )
    elements = [c]
    print(f"[CLI] Created Column: ID={c.id}, Profile={c.profile}, Size={c.width:.2f}x{c.depth:.2f}m, Height={c.height:.2f}m, Bars={c.main_bar_count}xDB{int(c.main_bar_dia*1000)}")
    print(f"      Concrete={c.concrete_volume:.3f} m3, Formwork={c.formwork_area:.2f} m2")

    if args.qto:
        summary = generate_qto_summary(elements)
        _print_qto_table(summary)

    if args.stream:
        _try_stream_to_bridge(elements, host=args.host, port=args.port)

    if args.out:
        _save_or_print_debim(elements, args.out, project_name=f"Column {args.id}")

    return 0


def handle_beam(args: argparse.Namespace) -> int:
    start_pt = tuple(map(float, args.start.split(","))) if args.start else (0.0, 0.0)
    end_pt = tuple(map(float, args.end.split(","))) if args.end else (args.length, 0.0)
    b = Beam(
        id=args.id,
        name=args.name or f"Beam_{args.id}",
        width=args.width,
        depth=args.depth,
        start_point=start_pt,
        end_point=end_pt,
        elevation=args.elevation,
        top_bar_spec=args.top_bar,
        bot_bar_spec=args.bot_bar,
        extra_bar_spec=args.extra_bar,
        stirrup_spec=args.stirrup,
        covering=args.covering,
    )
    elements = [b]
    print(f"[CLI] Created Beam: ID={b.id}, Size={b.width:.2f}x{b.depth:.2f}m, Length={b.length:.2f}m, Top={b.top_bar_spec}, Bot={b.bot_bar_spec}, Stirrup={b.stirrup_spec}")
    print(f"      Concrete={b.concrete_volume:.3f} m3, Formwork={b.formwork_area:.2f} m2")

    if args.qto:
        summary = generate_qto_summary(elements)
        _print_qto_table(summary)

    if args.stream:
        _try_stream_to_bridge(elements, host=args.host, port=args.port)

    if args.out:
        _save_or_print_debim(elements, args.out, project_name=f"Beam {args.id}")

    return 0


def handle_slab(args: argparse.Namespace) -> int:
    pts = []
    if args.boundary:
        # Expected format: "x1,y1;x2,y2;x3,y3;x4,y4"
        for pair in args.boundary.split(";"):
            pair = pair.strip()
            if pair:
                x_str, y_str = pair.split(",")
                pts.append((float(x_str), float(y_str)))
    else:
        # Default rectangular boundary using span_x, span_y
        sx, sy = args.span_x, args.span_y
        pts = [(0.0, 0.0), (sx, 0.0), (sx, sy), (0.0, sy)]

    s = Slab(
        id=args.id,
        name=args.name or f"Slab_{args.id}",
        slab_type=args.type.upper(),
        boundary=pts,
        thickness=args.thickness,
        elevation=args.elevation,
        topping_thickness=args.topping,
        wire_mesh=args.mesh,
        rebar_spec=args.rebar,
    )
    elements = [s]
    print(f"[CLI] Created Slab: ID={s.id}, Type={s.slab_type}, Area={s.area:.2f} m2, Thickness={s.thickness:.2f}m, Elevation={s.elevation:.2f}m")
    print(f"      Concrete={s.concrete_volume:.3f} m3, Formwork={s.formwork_area:.2f} m2")

    if args.qto:
        summary = generate_qto_summary(elements)
        _print_qto_table(summary)

    if args.stream:
        _try_stream_to_bridge(elements, host=args.host, port=args.port)

    if args.out:
        _save_or_print_debim(elements, args.out, project_name=f"Slab {args.id}")

    return 0


def handle_standards(args: argparse.Namespace) -> int:
    print("\n" + "=" * 60)
    print("      CHAKKREE REBAR STANDARDS & HOOK SPECIFICATIONS      ")
    print("=" * 60)
    print("Author   : Chakkree Tiyawongsuwan (อ.จักรี ติยะวงศ์สุวรรณ)")
    print("Standard : ว.ส.ท. (EIT Standard 1007-34) / ACI 318-19")
    print("-" * 60)
    print("1. Standard Hooks:")
    print("   • 90-degree hook : Extension = 12 x db (minimum 6.5 cm)")
    print("   • 180-degree hook: Extension = 4 x db (minimum 6.5 cm)")
    print("   • 135-degree seismic hook: Extension = 6 x db (minimum 7.5 cm)")
    print("\n2. Minimum Concrete Cover:")
    print("   • Footing (in ground) : 7.5 cm")
    print("   • Column (exposed)    : 4.0 cm (or 3.0 cm indoors)")
    print("   • Beam                : 4.0 cm (or 2.5 cm indoors)")
    print("   • Slab                : 2.0 - 2.5 cm")
    print("\n3. Lap Splice Lengths (Class B Tension):")
    print("   • DB12 : 55 cm")
    print("   • DB16 : 75 cm")
    print("   • DB20 : 95 cm")
    print("   • DB25 : 120 cm")
    print("=" * 60 + "\n")
    return 0


def handle_colors(args: argparse.Namespace) -> int:
    print("\n" + "=" * 55)
    print("       CHAKKREE TOOLS - REBAR COLOR CODES       ")
    print("=" * 55)
    colors = [
        ("RB6", "6mm", "#B0C4DE", "Light Steel Blue"),
        ("RB9", "9mm", "#4682B4", "Steel Blue"),
        ("DB12", "12mm", "#2E8B57", "Sea Green"),
        ("DB16", "16mm", "#FF8C00", "Dark Orange"),
        ("DB20", "20mm", "#DC143C", "Crimson"),
        ("DB25", "25mm", "#8B0000", "Dark Red"),
        ("DB28", "28mm", "#4B0082", "Indigo"),
        ("DB32", "32mm", "#2F4F4F", "Dark Slate Gray"),
    ]
    print(f"{'Size':<8} | {'Diameter':<10} | {'Hex Code':<10} | {'Color Name'}")
    print("-" * 55)
    for sz, dia, hex_c, cname in colors:
        print(f"{sz:<8} | {dia:<10} | {hex_c:<10} | {cname}")
    print("=" * 55 + "\n")
    return 0


def handle_qto(args: argparse.Namespace) -> int:
    from chakkree_tools.exporter.pure_yaml import safe_load
    input_p = Path(args.input)
    if not input_p.exists():
        print(f"[CLI Error] Input file does not exist: {input_p}")
        return 1

    content = safe_load(input_p.read_text(encoding="utf-8"))
    elements = []
    # Parse elements from .debim manifest
    raw_elements = content.get("elements", []) if isinstance(content, dict) else []
    for item in raw_elements:
        cls = item.get("class", "")
        el_id = item.get("id", "EL")
        dims = item.get("dimensions", {})
        if cls == "IfcFooting":
            elements.append(Footing(
                id=el_id,
                width=dims.get("width", 1.0),
                length=dims.get("length", 1.0),
                thickness=dims.get("thickness", 0.35),
            ))
        elif cls == "IfcColumn":
            elements.append(Column(
                id=el_id,
                width=dims.get("width", 0.3),
                depth=dims.get("depth", 0.3),
                height=dims.get("height", 3.5),
            ))
        elif cls == "IfcBeam":
            elements.append(Beam(
                id=el_id,
                width=dims.get("width", 0.2),
                depth=dims.get("depth", 0.4),
                start_point=(0.0, 0.0),
                end_point=(dims.get("length", 4.0), 0.0),
            ))
        elif cls == "IfcSlab":
            elements.append(Slab(
                id=el_id,
                slab_type=item.get("slab_type", "PS"),
                thickness=dims.get("thickness", 0.10),
                boundary=[tuple(p) for p in item.get("boundary", [(0, 0), (4, 0), (4, 4), (0, 4)])],
            ))

    summary = generate_qto_summary(elements)
    _print_qto_table(summary)

    if args.csv:
        csv_p = Path(args.csv)
        lines = ["Item,Concrete_m3,Formwork_m2,Rebar_Weight_kg\n"]
        lines.append(f"Total,{summary.total_concrete_volume_m3:.3f},{summary.total_formwork_area_m2:.2f},{summary.total_rebar_weight_kg:.2f}\n")
        lines.append("\nBar_Size,Weight_kg\n")
        for k, v in summary.rebar_weight_by_size.items():
            lines.append(f"{k},{v:.2f}\n")
        csv_p.write_text("".join(lines), encoding="utf-8")
        print(f"[CLI] Exported QTO CSV to: {csv_p.resolve()}")

    return 0


def handle_about(args: argparse.Namespace) -> int:
    print("\n" + "=" * 65)
    print("      CHAKKREE TOOLS (PYTHON EDITION FOR INGETRAZO & CLI)      ")
    print("=" * 65)
    print("Version     : v0.1.0")
    print("Original Dev: อ.จักรี ติยะวงศ์สุวรรณ (Chakkree Tiyawongsuwan)")
    print("Python Port : PRIDA-TAKON")
    print("Support URL : https://sites.google.com/view/learn-sketchup/myextension/chakkree_tools-v0-4")
    print("GitHub      : https://github.com/PRIDA-TAKON/chakkreeTools-python")
    print("OpenBIM     : debim (.debim.yaml) integration supported")
    print("=" * 65 + "\n")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chakkree",
        description="Chakkree Tools (Python Edition) - Parametric RC Modeling, QTO & OpenBIM CLI",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # 1. Footing command
    p_footing = subparsers.add_parser("footing", help="Parametric Footing / Pile Cap tools")
    p_footing.add_argument("--id", required=True, help="Footing ID (e.g. F1, F2)")
    p_footing.add_argument("--name", default="", help="Element name")
    p_footing.add_argument("--piles", type=int, choices=range(1, 10), default=None, help="Number of piles (1-9). Omit for isolated footing")
    p_footing.add_argument("--pile-size", type=float, default=0.22, help="Pile size in meters (default 0.22)")
    p_footing.add_argument("--width", type=float, default=1.20, help="Footing width B in meters (default 1.20)")
    p_footing.add_argument("--length", type=float, default=1.20, help="Footing length L in meters (default 1.20)")
    p_footing.add_argument("--thickness", type=float, default=0.35, help="Thickness t in meters (default 0.35)")
    p_footing.add_argument("--elevation", type=float, default=-0.70, help="Top elevation Z in meters (default -0.70)")
    p_footing.add_argument("--covering", type=float, default=0.07, help="Covering in meters (default 0.07)")
    p_footing.add_argument("--rebar-x-count", type=int, default=5, help="Rebar count in X direction")
    p_footing.add_argument("--rebar-x-dia", type=float, default=0.012, help="Rebar diameter in X direction (m)")
    p_footing.add_argument("--rebar-y-count", type=int, default=5, help="Rebar count in Y direction")
    p_footing.add_argument("--rebar-y-dia", type=float, default=0.012, help="Rebar diameter in Y direction (m)")
    p_footing.add_argument("--rebar-dia", type=float, default=0.016, help="Rebar diameter for pile caps (m)")
    p_footing.add_argument("--qto", action="store_true", help="Print QTO & rebar calculations")
    p_footing.add_argument("--out", type=str, default=None, help="Output .debim.yaml file path")
    p_footing.add_argument("--stream", action="store_true", help="Stream element directly to IngeTrazo Agent Bridge (port 8482)")
    p_footing.add_argument("--host", default="127.0.0.1", help="IngeTrazo Bridge host (default 127.0.0.1)")
    p_footing.add_argument("--port", type=int, default=8482, help="IngeTrazo Bridge port (default 8482)")
    p_footing.set_defaults(func=handle_footing)

    # 2. Column command
    p_column = subparsers.add_parser("column", help="Parametric Column tools")
    p_column.add_argument("--id", required=True, help="Column ID (e.g. C1, C2)")
    p_column.add_argument("--name", default="", help="Element name")
    p_column.add_argument("--profile", choices=["rectangular", "circular"], default="rectangular", help="Profile type")
    p_column.add_argument("--width", type=float, default=0.30, help="Column width in meters (or diameter if circular)")
    p_column.add_argument("--depth", type=float, default=0.30, help="Column depth in meters")
    p_column.add_argument("--height", type=float, default=3.50, help="Column height in meters")
    p_column.add_argument("--elevation", type=float, default=0.0, help="Base elevation in meters")
    p_column.add_argument("--position", type=str, default="0.0,0.0", help="Plan coordinates 'x,y'")
    p_column.add_argument("--bars", type=int, default=8, help="Main rebar count (4, 6, 8, 10, 12, 14, 16)")
    p_column.add_argument("--bar-dia", type=float, default=0.016, help="Main rebar diameter in meters (e.g. 0.016 for DB16)")
    p_column.add_argument("--stirrup-dia", type=float, default=0.009, help="Stirrup diameter in meters (e.g. 0.009 for RB9)")
    p_column.add_argument("--stirrup-spacing", type=float, default=0.150, help="Stirrup spacing in meters")
    p_column.add_argument("--covering", type=float, default=0.030, help="Covering in meters")
    p_column.add_argument("--qto", action="store_true", help="Print QTO & rebar calculations")
    p_column.add_argument("--out", type=str, default=None, help="Output .debim.yaml file path")
    p_column.add_argument("--stream", action="store_true", help="Stream element directly to IngeTrazo Agent Bridge (port 8482)")
    p_column.add_argument("--host", default="127.0.0.1", help="IngeTrazo Bridge host (default 127.0.0.1)")
    p_column.add_argument("--port", type=int, default=8482, help="IngeTrazo Bridge port (default 8482)")
    p_column.set_defaults(func=handle_column)

    # 3. Beam command
    p_beam = subparsers.add_parser("beam", help="Parametric Beam tools")
    p_beam.add_argument("--id", required=True, help="Beam ID (e.g. B1, B2)")
    p_beam.add_argument("--name", default="", help="Element name")
    p_beam.add_argument("--width", type=float, default=0.20, help="Beam width in meters")
    p_beam.add_argument("--depth", type=float, default=0.40, help="Beam depth in meters")
    p_beam.add_argument("--length", type=float, default=4.0, help="Span length in meters")
    p_beam.add_argument("--start", type=str, default="0.0,0.0", help="Start point 'x,y'")
    p_beam.add_argument("--end", type=str, default=None, help="End point 'x,y'")
    p_beam.add_argument("--elevation", type=float, default=3.20, help="Top elevation in meters")
    p_beam.add_argument("--top-bar", default="2DB12", help="Top rebar spec (e.g. 2DB12)")
    p_beam.add_argument("--bot-bar", default="3DB12", help="Bottom rebar spec (e.g. 3DB12)")
    p_beam.add_argument("--extra-bar", default="1DB12", help="Extra top bar spec")
    p_beam.add_argument("--stirrup", default="RB6@0.175", help="Stirrup spec (e.g. RB6@0.175)")
    p_beam.add_argument("--covering", type=float, default=0.025, help="Covering in meters")
    p_beam.add_argument("--qto", action="store_true", help="Print QTO & rebar calculations")
    p_beam.add_argument("--out", type=str, default=None, help="Output .debim.yaml file path")
    p_beam.add_argument("--stream", action="store_true", help="Stream element directly to IngeTrazo Agent Bridge (port 8482)")
    p_beam.add_argument("--host", default="127.0.0.1", help="IngeTrazo Bridge host (default 127.0.0.1)")
    p_beam.add_argument("--port", type=int, default=8482, help="IngeTrazo Bridge port (default 8482)")
    p_beam.set_defaults(func=handle_beam)

    # 4. Slab command
    p_slab = subparsers.add_parser("slab", help="Parametric Slab tools")
    p_slab.add_argument("--id", required=True, help="Slab ID (e.g. S1, PS1)")
    p_slab.add_argument("--name", default="", help="Element name")
    p_slab.add_argument("--type", choices=["ps", "rc"], default="ps", help="Slab type: 'ps' (precast plank) or 'rc' (cast-in-place)")
    p_slab.add_argument("--span-x", type=float, default=4.0, help="X span in meters for rectangular slab")
    p_slab.add_argument("--span-y", type=float, default=4.0, help="Y span in meters for rectangular slab")
    p_slab.add_argument("--boundary", type=str, default=None, help="Custom polygon points 'x1,y1;x2,y2;x3,y3;x4,y4'")
    p_slab.add_argument("--thickness", type=float, default=0.10, help="Slab thickness in meters")
    p_slab.add_argument("--topping", type=float, default=0.05, help="Topping thickness for PS slab in meters")
    p_slab.add_argument("--elevation", type=float, default=0.0, help="Top elevation in meters")
    p_slab.add_argument("--mesh", default="WM4@0.20", help="Wire mesh spec for PS slab")
    p_slab.add_argument("--rebar", default="RB9@0.15", help="Rebar spec for RC slab")
    p_slab.add_argument("--qto", action="store_true", help="Print QTO & rebar calculations")
    p_slab.add_argument("--out", type=str, default=None, help="Output .debim.yaml file path")
    p_slab.add_argument("--stream", action="store_true", help="Stream element directly to IngeTrazo Agent Bridge (port 8482)")
    p_slab.add_argument("--host", default="127.0.0.1", help="IngeTrazo Bridge host (default 127.0.0.1)")
    p_slab.add_argument("--port", type=int, default=8482, help="IngeTrazo Bridge port (default 8482)")
    p_slab.set_defaults(func=handle_slab)

    # 5. QTO Report command
    p_qto = subparsers.add_parser("qto", help="Quantity Take-off & BBS report from .debim manifest")
    p_qto.add_argument("--input", "-i", required=True, help="Input .debim.yaml file")
    p_qto.add_argument("--csv", help="Save output report as CSV")
    p_qto.set_defaults(func=handle_qto)

    # 6. Standards command
    p_std = subparsers.add_parser("standards", help="Print Chakkree rebar standard specifications & hooks")
    p_std.set_defaults(func=handle_standards)

    # 7. Colors command
    p_colors = subparsers.add_parser("colors", help="Print Chakkree standard rebar color hex mapping")
    p_colors.set_defaults(func=handle_colors)

    # 8. About command
    p_about = subparsers.add_parser("about", help="Display author credits, donation link, and version")
    p_about.set_defaults(func=handle_about)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    parser = build_parser()
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        parser.print_help()
        return 0
    args = parser.parse_args(argv)
    if hasattr(args, "func"):
        return args.func(args)
    parser.print_help()
    return 0


if __name__ == "__main__":
    sys.exit(main())

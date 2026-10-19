# Jules AI Development Roadmap & Issue Backlog

Welcome Jules AI! This backlog contains step-by-step issues to port and advance **Chakkree Tools** into a modern Python ecosystem for **IngeTrazo** and **.debim**.

---

## 📋 Task 1: Complete S2D Parser (`chakkree_tools/dsl/s2d_parser.py`)
- **Objective:** Implement the parser for Structure 2D `.s2d` files (located in `references/original_specs/chakkree_tools/Extensions/`).
- **Input Scripts to Support:**
  - `TopView_RecPile.s2d` (Footings 1-9 Piles)
  - `Column_Section.s2d` (Columns Rectangular & Circular)
  - `TopView_PS.s2d` (Precast Plank Slabs)
  - `Grids.s2d` & `Elevations.s2d` (Grid axes and elevation marks)
- **Requirements:**
  - Support commands: `var`, `set`, `break_IfNOT`, `get_attribute`, `inputbox`.
  - Extract parametric bounding boxes and prompt definitions.
  - Add unit tests in `tests/test_s2d_parser.py`.

---

## 📋 Task 2: 3D Rebar Polyline & Mesh Generator (`chakkree_tools/rc/rebar_mesh.py`)
- **Objective:** Generate 3D spatial coordinate polyline points and tubular meshes for rebar visualization in IngeTrazo.
- **Standard Rebar Shapes to Implement (ตามมาตรฐาน วสท. / มอก.):**
  - **Shape 00:** Straight bar (เหล็กเส้นตรง)
  - **Shape 21:** U-bent bar with hooks for beam main bars (เหล็กนอนดัดฉาก)
  - **Shape 41:** Rectangular closed stirrup with 135° seismic hooks (เหล็กปลอกเสาและคาน)
  - **Shape 99:** Column vertical bar with 90° foundation dowel bend (เหล็กยืนเสาฝากฐานราก)
- **Output:** Returns vertices and line indices ready for IngeTrazo 3D viewport canvas.
- **Add unit tests in `tests/test_rebar_mesh.py`.**

---

## 📋 Task 3: IngeTrazo PySide6 Parametric Dialogs (`chakkree_tools/ingetrazo_plugin/ui/`)
- **Objective:** Provide native, responsive PySide6 dialogs inside IngeTrazo.
- **Dialogs to Implement:**
  - `FootingDialog`: Select 1-9 Piles, pile diameter (180, 220, 250, 300, 350mm), rebar size (DB12, DB16, DB20, DB25), covering.
  - `ColumnDialog`: Width, depth, height, number of bars (4, 6, 8, 14, 16), main bar dia, stirrup spacing.
  - `BeamDialog`: Span length, section b x h, top/bottom bars, stirrup multi-zone spacing.
- **Bridge to IngeTrazo:** Hook dialog submit events to instantiate `Footing`, `Column`, `Beam` and trigger viewport redraw.

---

## 📋 Task 4: Automated QTO & Bar Bending Schedule (BBS)
- **Objective:** Port quantity take-off formulas from `chakkree_tools/QuantityTakeOff/TakeOff_Footing_F1.rbe` and `BarBendingSchedule.rbe`.
- **Calculations:**
  - Steel weight (kg) by rebar diameter:
    - RB6: $0.222 \text{ kg/m}$
    - RB9: $0.499 \text{ kg/m}$
    - DB12: $0.888 \text{ kg/m}$
    - DB16: $1.578 \text{ kg/m}$
    - DB20: $2.466 \text{ kg/m}$
    - DB25: $3.853 \text{ kg/m}$
  - Formwork area ($m^2$)
  - Concrete volume ($m^3$)
  - Excavation and lean concrete ($m^3$)
- **Export Formats:** Markdown report, CSV table, and JSON.

---

## 📋 Task 5: Live Streaming via IngeTrazo Agent Bridge (Port 8482)
- **Objective:** Stream generated models directly into IngeTrazo without writing intermediate files to disk.
- **HTTP POST:** Send generated `.debim.yaml` payload to `http://127.0.0.1:8482` as implemented in `project-debim/debim-ingetrazo`.

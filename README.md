# chakkreeTools-python

[![CI](https://github.com/PRIDA-TAKON/chakkreeTools-python/actions/workflows/ci.yml/badge.svg)](https://github.com/PRIDA-TAKON/chakkreeTools-python/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)

**chakkreeTools-python** คือโครงการพัฒนาต่อยอดและทำวิศวกรรมย้อนกลับ (Reverse Engineering & Porting) จากส่วนขยาย **Chakkree Tools (SketchUp Extension)** ยอดนิยม สู่ภาษา **Python** เพื่อใช้งานบน **IngeTrazo 3D Modeler** และเชื่อมต่อกับระบบ OpenBIM **.debim (Building-as-Code)**

---

## 🏛️ ที่มาและการอ้างอิงผลงานต้นฉบับ (Original Attribution)

> *"เครื่องมือวิศวกรรมโครงสร้าง ค.ส.ล. และเสริมเหล็กมาตรฐานไทย"*

โครงการนี้พัฒนาขึ้นโดยอ้างอิงองค์ความรู้ สถาปัตยกรรม และตรรกะการคำนวณทางวิศวกรรมจาก:
* **ผลงานต้นฉบับ:** Chakkree Tools for SketchUp (`chakkree_tools_v0.4.0.b`)
* **ผู้คิดค้นและพัฒนาต้นฉบับ:** **อ.จักรี ติยะวงศ์สุวรรณ (Chakkree Tiyawongsuwan)** © 2021–2026

การพอร์ตสู่ Python ในครั้งนี้เป็นการตอบรับคำท้าทายและเจตนารมณ์ของผู้พัฒนาต้นฉบับ เพื่อให้เครื่องมือวิศวกรรมโครงสร้างไทยสามารถก้าวข้ามข้อจำกัดของซอฟต์แวร์แบบปิด ไปสู่ **Modern Open-Source CAD Ecosystem** และขับเคลื่อนงานพัฒนาต่อด้วย AI (Jules AI / Antigravity)

---

## 🖥️ หน้าต่างแถบเครื่องมือดั้งเดิม (Original Toolbar UI)

![Chakkree Tools Toolbar](docs/images/original_toolbar_ui.png)

แถบเครื่องมือหลักของ **chakkree_tools** ประกอบด้วยชุดคำสั่งเรียงตามลำดับจากซ้ายไปขวา:

| ลำดับ | ไอคอน | ชื่อคำสั่ง | คำอธิบายการทำงานใน Python / IngeTrazo |
| :---: | :---: | :--- | :--- |
| **1** | `RebarTools.svg` | **Rebar Tools** | เครื่องมือดัดปลายเหล็กขอ 90°/135°/180°, สร้างชุดเหล็กเสริม 3D และตัวคูณระยะทาบ |
| **2** | `FootingTools.svg` | **Footing Tools** | สร้างฐานรากเสาเข็ม 1–9 ต้น (`1Pile` – `9Piles`) และฐานรากแผ่ พร้อมเหล็กตะกร้อและเสาตอม่อ |
| **3** | `BeamTools.svg` | **Beam Tools** | สร้างคาน ค.ส.ล. เหล็กบน-ล่าง-พิเศษ และเหล็กปลอก 1 หรือ 3 ช่วงระยะ (`StirrupPattern`) |
| **4** | `ColumnTools.svg` | **Column Tools** | สร้างเสาสี่เหลี่ยม/กลม เหล็กยืน 4, 6, 8, 14, 16 เส้น พร้อมเหล็กปลอกและระยะทาบต่อท่อน |
| — | *Separator* | — | — |
| **5** | `GridLine.svg` | **GridLine v2026** | ระบบผังกริตไลน์ แกน X/Y พร้อมบอลลูนบอกระยะ และระดับชั้น (Elevations) |
| — | *Separator* | — | — |
| **6** | `TakeOff.svg` | **QTO Take-off** | รายการคำนวณถอดปริมาณ คอนกรีต, ไม้แบบ, เหล็กเสริม, ดินขุด และ Bar Bending Schedule (BBS) |
| **7** | `AnalysisTool.svg` | **RC Analysis / debim** | ตรวจสอบกำลังรับแรงหน้าตัด ค.ส.ล. และส่งออกไฟล์ `.debim` ไปยังโปรเจกต์ debim |
| — | *Separator* | — | — |
| **8** | `ConfigColorRebar.svg`| **Config Colors** | ตั้งค่าสีเหล็กเสริมแยกตามขนาดเส้นผ่านศูนย์กลาง (RB6, RB9, DB12, DB16, DB20, DB25...) |
| — | *Separator* | — | — |
| **9** | `About.svg` | **About** | ข้อมูลลิขสิทธิ์และรุ่นของโปรแกรม © อ.จักรี ติยะวงศ์สุวรรณ |

---

1. **Native IngeTrazo Extension:**
   - ใช้งานเป็นปลั๊กอินในโปรแกรมออกแบบ 3D **IngeTrazo** (`%APPDATA%\ingetrazo\plugins\chakkree_tools`)
   - รองรับการเรียกใช้ผ่านแถบเครื่องมือ (Toolbars) และเมนู `Extensions > Chakkree Tools`

2. **CRS Parser (Chakkree Rebar Script Engine):**
   - ตัวประมวลผลสคริปต์ภาษา `.crs` แปลงคำสั่งพารามิเตอร์ `Box`, `rebar`, `tran`, `rot`, `copy` เป็นรูปทรงเรขาคณิต 3D อัตโนมัติ

3. **Parametric RC Components (ชิ้นส่วน ค.ส.ล. สำเร็จรูป):**
   - **ฐานรากเสาเข็ม (Pile Caps 1–9 Piles):** คำนวณระยะห่างเสาเข็ม ($3D_p$), ระยะขอบ ($1.5D_p$), เหล็กเสริม และปริมาตรคอนกรีต/ไม้แบบ
   - **เสา ค.ส.ล. (RC Columns):** ทั้งแบบสี่เหลี่ยมและกลม พร้อมเหล็กยืน 4, 6, 8, 14, 16 เส้น และเหล็กปลอก
   - **คาน ค.ส.ล. (RC Beams):** คำนวณเหล็กบน เหล็กล่าง เหล็กเสริมพิเศษ และเหล็กปลอกหลายช่วงระยะ (`StirrupPattern`)
   - **แผ่นพื้นสำเร็จรูป (PS Plank Slabs & RC Slabs):** คำนวณพื้นที่รูปหลายเหลี่ยม (Shoelace Formula) และ Topping

4. **1-Click .debim Export (OpenBIM Integration):**
   - ส่งออกโมเดลโครงสร้างเป็นไฟล์ `.debim.yaml` (สเปก `schema: IFC4-Minimal`)
   - เชื่อมต่อกับโปรเจกต์ `debim CLI` เพื่อทำ **QTO (ถอดปริมาณ)**, **BOQ (ประเมินราคา)**, **2D Blueprint Drafting** และ **IFC4 Export** ได้ทันที

---

## 🚀 เริ่มต้นใช้งาน (Quick Start)

### 1. ติดตั้งแพ็กเกจ
```bash
git clone https://github.com/PRIDA-TAKON/chakkreeTools-python.git
cd chakkreeTools-python
pip install -e .
```

### 2. ตัวอย่างการสร้างโมเดลโครงสร้างและส่งออกเป็น `.debim`
```python
from chakkree_tools.rc.footing import PileCap
from chakkree_tools.rc.column import Column
from chakkree_tools.rc.beam import Beam
from chakkree_tools.rc.slab import Slab
from chakkree_tools.exporter.debim_exporter import DebimExporter

# สร้างระบบโมเดลโครงสร้าง
exporter = DebimExporter(project_name="Modern RC House")
exporter.set_grids(
    axes_x={"1": 0.0, "2": 4.0, "3": 8.0},
    axes_y={"A": 0.0, "B": 5.0}
)

# 1. เพิ่มฐานรากเสาเข็ม 2 ต้น
f1 = PileCap.create_n_piles(id_str="F1", pile_count=2, elevation=-0.70)
exporter.add_element(f1)

# 2. เพิ่มเสา ค.ส.ล. เหล็กยืน 8 เส้น
c1 = Column(id="C1", grid_ref=("1", "A"), width=0.3, depth=0.3, height=3.5)
exporter.add_element(c1)

# 3. เพิ่มคาน ค.ส.ล.
b1 = Beam(id="B1", width=0.2, depth=0.4, from_grid=("1", "A"), to_grid=("2", "A"))
exporter.add_element(b1)

# 4. บันทึกเป็น .debim.yaml
exporter.save("output_model.debim.yaml")
print("Exported successfully!")
```

### 3. รันตัวอย่าง Villa
```bash
python examples/generate_villa_rc.py
```

---

## 🧪 การทดสอบชุดคำสั่ง (Running Tests)

รันชุดทดสอบความถูกต้องผ่าน `pytest`:
```bash
pytest
```

---

## 🤖 แผนงานการพัฒนาสำหรับ Jules AI (Development with Jules AI)

ดูรายละเอียดงานและ Backlog ทั้งหมดได้ที่ [JULES_BACKLOG.md](JULES_BACKLOG.md):
- **Task 1:** Structure 2D S2D Parser
- **Task 2:** 3D Rebar Polyline & Mesh Generator
- **Task 3:** IngeTrazo PySide6 UI Dialogs
- **Task 4:** Bar Bending Schedule (BBS) & QTO Report
- **Task 5:** Real-time Viewport Streaming via Agent Bridge (Port 8482)

---

## 📄 สัญญาอนุญาต (License)

โปรเจกต์นี้เผยแพร่ภายใต้สัญญาอนุญาต [MIT License](LICENSE)  
ผลงานแนวคิดและสถาปัตยกรรมโมเดลต้นฉบับ © **อ.จักรี ติยะวงศ์สุวรรณ (Chakkree Tiyawongsuwan)**

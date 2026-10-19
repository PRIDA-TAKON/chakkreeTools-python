"""
สำหรับ ทดสอบ
"""
import socket
import json

# ข้อมูล JSON ที่จะส่ง
data = {
    "unit": "mm",
    "entities": [
        { "type": "line", "params": { "x1": 0, "y1": 0, "x2": 100, "y2": 100 } },
        { "type": "circle", "params": { "cx": 50, "cy": 50, "r": 25, "fill": "red" } },
        { "type": "rect", "params": { "x": 0, "y": 0, "w": 200, "h": 100 , "fill":"none" } }
    ]
}



# แปลงเป็น string
message = json.dumps(data)

# สร้าง TCP socketห
HOST = "127.0.0.1"   # หรือ IP ของเครื่องที่รัน SketchUp
PORT = 62601          # พอร์ตที่ JsonServer เปิดไว้

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall((message+ "\n").encode("utf-8"))
    s.close()

    # ถ้า server มีการตอบกลับ
    #response = s.recv(1024)
    #print("Response:", response.decode("utf-8"))


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect((HOST, PORT))
s.sendall((message+ "\n").encode("utf-8"))

print ("รันเสร็จแล้ว")
"""Demo visual local para Windows. Simulação didática, não controla hardware real."""
import argparse
import csv
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
import math
import os
import time
import tkinter as tk
from tkinter import ttk
try:
    from .navigation_core import (Pose, WaypointController, integrate, pixels_to_meters,
                                  meters_to_pixels, ROUTE_PIXELS, ORIGIN_PX, route_is_clear)
except ImportError:
    from navigation_core import (Pose, WaypointController, integrate, pixels_to_meters,
                                 meters_to_pixels, ROUTE_PIXELS, ORIGIN_PX, route_is_clear)

MAX_LINEAR = 0.45       # m/s
MAX_ANGULAR = 1.2       # rad/s
MAX_ACCEL = 3.8         # m/s² (limite didático)
DT = 0.1

def is_gui_available():
    if os.name == "nt":
        return True
    return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))


def headless_mode(iterations=8, delay=0.1):
    demo = Demo.__new__(Demo)
    demo.last_v = 0.0
    messages = []
    for i in range(iterations):
        attack = i % 4 == 0
        cmd_v, cmd_w = (1.8, 2.0) if attack else (0.25, 0.15)
        ok, reason = demo.validate(cmd_v, cmd_w, max(0.01, min(0.25, delay)))
        status = "ATTACK_BLOCKED" if attack and not ok else "NORMAL"
        if ok:
            demo.last_v = cmd_v
        else:
            demo.last_v = 0.0
        messages.append(
            f"STATUS {status} | ataque={str(attack).upper()} | v={cmd_v:.2f} | ok={ok} | {reason}"
        )
        time.sleep(delay)
    return messages


class Demo:
    def __init__(self, root):
        self.root = root
        root.title("Cyber-Physical AMR Security Lab — Demo local")
        root.geometry("1200x760")
        root.minsize(1100, 680)
        root.configure(bg="#0b1220")
        self.style = ttk.Style(root)
        self.style.theme_use("clam")
        self.style.configure("Header.TFrame", background="#08101c")
        self.style.configure("Panel.TFrame", background="#101827")
        self.style.configure("Accent.TButton", background="#1f9d8b", foreground="#ffffff", padding=(12, 8), font=("Segoe UI", 10, "bold"))
        self.style.map("Accent.TButton", background=[("active", "#1a8d7a")])
        self.style.configure("TLabel", background="#101827", foreground="#e5eefb")
        self.style.configure("TFrame", background="#101827")
        self.style.configure("TLabelframe", background="#101827")
        self.style.configure("TLabelframe.Label", background="#101827", foreground="#dfe9ff", font=("Segoe UI", 10, "bold"))
        self.attack = False
        self.x, self.y, self.theta = 110.0, 230.0, 0.0
        self.v = 0.0
        self.last_v = 0.0
        self.last_time = time.monotonic()
        self.blocked = 0
        self.accepted = 0
        self.status = "NORMAL"
        self.last_reason = "Nenhuma violação detectada"
        self.bridge_status = "Desconectado (demo local)"
        self.events = []
        self.attack_attempts = 0
        self.safe_stops = 0
        self.last_cmd_w = 0.0
        self.command_path = "cmd_vel_untrusted -> sentinela -> cmd_vel"
        self.obstacles = [
            (195, 55, 255, 125),
            (315, 55, 375, 125),
            (435, 55, 495, 125),
            (555, 55, 615, 125),
            (195, 275, 255, 345),
            (315, 275, 375, 345),
            (435, 275, 495, 345),
            (555, 275, 615, 345),
        ]
        self.history = [(self.x, self.y)]
        self.navigation_active = False
        self.nav_pose = Pose()
        self.nav_controller = WaypointController([pixels_to_meters(p) for p in ROUTE_PIXELS])
        self.nav_last_v = 0.0
        self.nav_status = "AGUARDANDO MISSAO"
        self.build_ui()
        self.tick()

    def build_ui(self):
        top = ttk.Frame(self.root, padding=14, style="Header.TFrame")
        top.pack(fill="x")
        ttk.Label(top, text="CYBER-PHYSICAL AMR SECURITY LAB",
                  font=("Segoe UI", 20, "bold"), foreground="#ecf3ff").pack(anchor="w")
        ttk.Label(top, text="Demonstração didática de injeção de comandos, validação de política e mitigação segura",
                  foreground="#b8c8e8").pack(anchor="w")

        controls = ttk.Frame(self.root, padding=(12, 8, 12, 6), style="Panel.TFrame")
        controls.pack(fill="x")
        ttk.Button(controls, text="Iniciar ataque", command=self.start_attack, width=18, style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(controls, text="Parar ataque", command=self.stop_attack, width=18, style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(controls, text="Resetar", command=self.reset, width=18, style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(controls, text="Iniciar missão", command=self.start_mission, style="Accent.TButton").pack(side="left", padx=4)
        ttk.Button(controls, text="Pausar missão", command=self.pause_mission, style="Accent.TButton").pack(side="left", padx=4)
        self.status_label = ttk.Label(controls, text="STATUS: NORMAL", font=("Segoe UI", 11, "bold"), foreground="#d9fbe5")
        self.status_label.pack(side="right", padx=10)
        ttk.Button(controls, text="Exportar CSV", command=self.export_events, style="Accent.TButton").pack(side="left", padx=4)

        content = ttk.Frame(self.root, style="Panel.TFrame")
        content.pack(fill="both", expand=True, padx=12, pady=(0, 10))

        left = ttk.Frame(content, style="Panel.TFrame")
        left.pack(side="left", fill="both", expand=True)
        self.canvas = tk.Canvas(left, width=780, height=440, bg="#edf5fb",
                                highlightthickness=1, highlightbackground="#d0d7e2")
        self.canvas.pack(padx=(0, 8), pady=(0, 6), fill="both", expand=True)

        self.canvas.create_rectangle(25, 30, 755, 390, outline="#5d6777", width=2, fill="#f8fafc")
        self.canvas.create_text(60, 18, text="ARMAZÉM VIRTUAL — simulação local / preparação para bridge Gazebo", anchor="w", fill="#374151", font=("Segoe UI", 10, "bold"))

        for x in range(50, 760, 45):
            self.canvas.create_line(x, 30, x, 390, fill="#dfe7f1", width=1)
        for y in range(40, 370, 35):
            self.canvas.create_line(25, y, 755, y, fill="#dfe7f1", width=1)

        self.canvas.create_rectangle(55, 165, 125, 225, fill="#dbeafe", outline="#2563eb", width=2)
        self.canvas.create_text(90, 195, text="DOCK", fill="#1d4ed8", font=("Segoe UI", 8, "bold"))
        self.canvas.create_rectangle(665, 300, 715, 345, fill="#fef3c7", outline="#d97706", width=2)
        self.canvas.create_text(690, 290, text="META", fill="#92400e", font=("Segoe UI", 8, "bold"))

        for x1, y1, x2, y2 in self.obstacles:
            self.canvas.create_rectangle(x1, y1, x2, y2, fill="#b8bec8", outline="#6b7280", width=2)
            self.canvas.create_text((x1 + x2) / 2, (y1 + y2) / 2, text="RACK", fill="#374151", font=("Segoe UI", 8, "bold"))

        self.canvas.create_rectangle(650, 55, 730, 125, fill="#e2e8f0", outline="#475569", width=2)
        self.canvas.create_text(690, 90, text="CARGA", fill="#334155", font=("Segoe UI", 9, "bold"))
        self.canvas.create_rectangle(135, 150, 635, 250, fill="#edf2f7", outline="#64748b", width=2)
        self.canvas.create_text(385, 165, text="CORREDOR PRINCIPAL", fill="#334155", font=("Segoe UI", 9, "bold"))

        self.canvas.create_text(60, 350, text="Fluxo: comando não confiável → sentinela → comando validado", anchor="w", fill="#455", font=("Segoe UI", 9, "bold"))
        self.route_line = self.canvas.create_line(self.x, self.y, self.x, self.y, fill="#4a90e2", width=4, smooth=True)
        self.canvas.create_line(*sum([ORIGIN_PX] + ROUTE_PIXELS, ()), fill="#0d9488", width=2, dash=(6, 4))
        for i, (px, py) in enumerate(ROUTE_PIXELS, 1):
            self.canvas.create_oval(px-5, py-5, px+5, py+5, fill="#0d9488", outline="white")
            self.canvas.create_text(px, py-13, text=str(i), fill="#0f766e", font=("Segoe UI", 9, "bold"))
        self.goal_marker = self.canvas.create_oval(678, 307, 702, 331, fill="#f59e0b", outline="#b45309", width=2)
        self.robot = self.canvas.create_oval(self.x-18, self.y-18, self.x+18, self.y+18,
                                             fill="#218838", outline="#145523", width=3)
        self.heading = self.canvas.create_line(self.x, self.y, self.x+30, self.y,
                                               fill="#145523", width=5, arrow=tk.LAST)

        right = ttk.Frame(content, padding=(0, 0, 0, 0), style="Panel.TFrame")
        right.pack(side="right", fill="y")
        self.panel = ttk.Frame(right, padding=8, style="Panel.TFrame")
        self.panel.pack(fill="both", expand=True)

        cards = [
            ("Telemetria de segurança", [
                ("status", ttk.Label(self.panel, text="Status: NORMAL", font=("Segoe UI", 11, "bold"), foreground="#1b7f45")),
                ("bridge", ttk.Label(self.panel, text="Bridge: desconectado", foreground="#375a7f")),
                ("accepted", ttk.Label(self.panel, text="Aceitos: 0", foreground="#1b7f45")),
                ("blocked", ttk.Label(self.panel, text="Bloqueados: 0", foreground="#c0392b")),
                ("attacks", ttk.Label(self.panel, text="Tentativas de ataque: 0")),
                ("stops", ttk.Label(self.panel, text="Paradas de segurança: 0")),
                ("velocity", ttk.Label(self.panel, text="Velocidade: 0.00 m/s")),
                ("mission", ttk.Label(self.panel, text="Missão: aguardando", wraplength=260)),
                ("pose", ttk.Label(self.panel, text="Odometria: x=0.00 y=0.00 θ=0°")),
            ]),
            ("Fluxo do sistema", [
                ("route", ttk.Label(self.panel, text="Caminho: cmd_vel_untrusted -> sentinela -> cmd_vel", wraplength=260, justify="left")),
                ("sim", ttk.Label(self.panel, text="Integração: não ativa nesta demo local", wraplength=260, justify="left")),
            ]),
            ("Política e motivo", [
                ("policy", ttk.Label(self.panel, text="Política: |v| ≤ 0.45 m/s | |ω| ≤ 1.20 rad/s | acel. ≤ 3.80 m/s²", wraplength=260, justify="left")),
                ("reason", ttk.Label(self.panel, text="Motivo: Nenhuma violação detectada", wraplength=260, justify="left")),
            ]),
        ]

        self.metrics = {}
        for title, widgets in cards:
            card = ttk.LabelFrame(self.panel, text=title, padding=10, style="TLabelframe")
            card.pack(fill="x", pady=(0, 8))
            for key, widget in widgets:
                widget.pack(anchor="w", pady=2)
                self.metrics[key] = widget

        self.panel.bind("<Configure>", lambda event: None)

        self.info = ttk.Label(self.root, padding=(10, 8), text="", font=("Segoe UI", 10, "bold"), background="#0b1220")
        self.info.pack(fill="x")

        log_frame = ttk.LabelFrame(self.root, text="Log de eventos", padding=(10, 8), style="Panel.TFrame")
        log_frame.pack(fill="x", padx=15, pady=(0, 12))
        self.log = tk.Text(log_frame, height=6, state="disabled", font=("Consolas", 9), bg="#f9fafb")
        self.log.pack(fill="x")
        self.write_log("Simulação local iniciada. ROS/Gazebo NÃO conectado.")

    def export_events(self):
        target = filedialog.asksaveasfilename(
            title="Salvar histórico de segurança", defaultextension=".csv",
            filetypes=[("Arquivo CSV", "*.csv")], initialfile="eventos_safe4.csv")
        if not target:
            return
        try:
            with open(target, "w", newline="", encoding="utf-8-sig") as stream:
                writer = csv.writer(stream, delimiter=";")
                writer.writerow(["data_hora", "evento", "status", "motivo", "velocidade_m_s", "angular_rad_s"])
                writer.writerows(self.events)
            messagebox.showinfo("Exportação concluída", f"Histórico salvo em:\n{target}")
        except OSError as exc:
            messagebox.showerror("Falha ao exportar", str(exc))

    def write_log(self, msg):
        if not hasattr(self, "events"):
            self.events = []
        self.events.append((datetime.now().isoformat(timespec="seconds"), msg,
                            self.status, self.last_reason, self.v, self.last_cmd_w))
        self.log.configure(state="normal")
        self.log.insert("end", f"[{time.strftime('%H:%M:%S')}] {msg}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def start_mission(self):
        if not route_is_clear([ORIGIN_PX] + ROUTE_PIXELS, self.obstacles):
            messagebox.showerror("Rota bloqueada", "A rota passa por uma prateleira.")
            return
        if self.nav_controller.finished:
            self.reset()
        self.navigation_active = True
        self.nav_status = "NAVEGANDO"
        self.write_log("Missão de coleta e expedição iniciada: 5 waypoints.")

    def pause_mission(self):
        self.navigation_active = False
        self.v = 0.0
        self.nav_last_v = 0.0
        self.nav_status = "PAUSADA"
        self.write_log("Missão pausada; comando de parada aplicado.")

    def start_attack(self):
        self.attack = True
        self.status = "ATTACK_TEST"
        self.last_reason = "Origem simulada iniciou injeção controlada de velocidade fora da política"
        self.write_log("Teste de injeção iniciado: origem simulada envia velocidade fora da política.")

    def stop_attack(self):
        self.attack = False
        self.status = "NORMAL"
        self.last_reason = "Origem de comandos voltou ao perfil seguro"
        self.write_log("Teste encerrado. Origem de comandos voltou ao perfil seguro.")

    def reset(self):
        self.attack = False
        self.x, self.y, self.theta, self.v = 110.0, 230.0, 0.0, 0.0
        self.last_v = 0.0
        self.blocked = self.accepted = 0
        self.status = "NORMAL"
        self.last_reason = "Estado da demonstração reiniciado"
        self.history = [(self.x, self.y)]
        self.navigation_active = False
        self.nav_pose = Pose()
        self.nav_controller = WaypointController([pixels_to_meters(p) for p in ROUTE_PIXELS])
        self.nav_last_v = 0.0
        self.nav_status = "AGUARDANDO MISSAO"
        self.attack_attempts = self.safe_stops = 0
        self.events.clear()
        self.write_log("Estado da demonstração reiniciado.")

    def validate(self, linear, angular, dt):
        # Função pura: mesma entrada -> mesma saída; não altera estado nem interface.
        if not all(math.isfinite(n) for n in (linear, angular, dt)) or dt <= 0:
            return False, "valor não finito ou intervalo inválido"
        if abs(linear) > MAX_LINEAR:
            return False, f"velocidade linear {linear:.2f} excede ±{MAX_LINEAR:.2f} m/s"
        if abs(angular) > MAX_ANGULAR:
            return False, f"velocidade angular {angular:.2f} excede ±{MAX_ANGULAR:.2f} rad/s"
        accel = abs(linear - self.last_v) / dt
        if accel > MAX_ACCEL:
            return False, f"aceleração {accel:.2f} excede {MAX_ACCEL:.2f} m/s²"
        return True, "comando aceito"

    def tick(self):
        now = time.monotonic()
        dt = max(0.01, min(0.25, now - self.last_time))
        self.last_time = now
        if self.attack:
            cmd_v, cmd_w = 1.8, 2.0
        elif self.navigation_active:
            cmd_v, cmd_w, self.nav_status = self.nav_controller.step(self.nav_pose)
            # Suavização para respeitar a política de aceleração.
            delta = MAX_ACCEL * dt * 0.5
            cmd_v = max(self.nav_last_v-delta, min(self.nav_last_v+delta, cmd_v))
        else:
            cmd_v, cmd_w = 0.0, 0.0

        self.last_cmd_w = cmd_w
        if self.attack:
            self.attack_attempts += 1
        ok, reason = self.validate(cmd_v, cmd_w, dt)
        if ok:
            self.v = cmd_v
            self.last_v = cmd_v
            self.accepted += 1
            self.status = "NORMAL" if not self.attack else "ATTACK_TEST"
            self.last_reason = "Comando aceito pela política de segurança"
        else:
            self.v = 0.0
            self.last_v = 0.0
            self.blocked += 1
            self.safe_stops += 1
            self.status = "ATTACK_BLOCKED" if self.attack else "SAFE_STOP"
            self.last_reason = reason
            if self.blocked == 1 or self.blocked % 10 == 0:
                self.write_log("SENTINELA BLOQUEOU: " + reason)

        # O robô só obedece aos comandos validados pelo sentinela.
        applied_w = cmd_w if ok else 0.0
        self.nav_last_v = self.v
        if self.navigation_active or self.attack:
            self.nav_pose = integrate(self.nav_pose, self.v, applied_w, dt)
            self.x, self.y = meters_to_pixels(self.nav_pose)
            self.theta = self.nav_pose.theta
        if self.navigation_active and self.nav_controller.finished:
            self.navigation_active = False
            self.nav_status = "CONCLUIDA"
            self.v = self.last_v = self.nav_last_v = 0.0
            self.write_log("MISSÃO CONCLUÍDA: expedição alcançada; robô parado.")

        self.history.append((self.x, self.y))
        if len(self.history) > 30:
            self.history = self.history[-30:]
        self.canvas.coords(self.route_line, *sum(self.history, ()))

        color = "#dc3545" if self.status == "ATTACK_BLOCKED" else "#218838"
        self.canvas.coords(self.robot, self.x-13, self.y-13, self.x+13, self.y+13)
        self.canvas.itemconfigure(self.robot, fill=color)
        self.canvas.coords(self.heading, self.x, self.y,
                           self.x+25*math.cos(self.theta), self.y+25*math.sin(self.theta))

        self.status_label.configure(text="STATUS: " + self.status, foreground="#1b7f45" if self.status != "ATTACK_BLOCKED" else "#c0392b")
        self.metrics["status"].configure(text="Status: " + self.status, foreground="#1b7f45" if self.status != "ATTACK_BLOCKED" else "#c0392b")
        self.metrics["bridge"].configure(text="Bridge: " + self.bridge_status)
        self.metrics["route"].configure(text="Caminho: " + self.command_path)
        self.metrics["reason"].configure(text="Motivo: " + self.last_reason)
        self.metrics["accepted"].configure(text=f"Aceitos: {self.accepted}")
        self.metrics["blocked"].configure(text=f"Bloqueados: {self.blocked}")
        self.metrics["attacks"].configure(text=f"Tentativas de ataque: {self.attack_attempts}")
        self.metrics["stops"].configure(text=f"Paradas de segurança: {self.safe_stops}")
        self.metrics["velocity"].configure(text=f"Velocidade: {self.v:.2f} m/s")
        self.metrics["mission"].configure(text=f"Missão: {self.nav_status} | ponto {min(self.nav_controller.index+1, len(ROUTE_PIXELS))}/{len(ROUTE_PIXELS)}")
        self.metrics["pose"].configure(text=f"Odometria: x={self.nav_pose.x:.2f} y={self.nav_pose.y:.2f} θ={math.degrees(self.nav_pose.theta):.0f}°")
        self.metrics["sim"].configure(text="Integração: somente simulação local; Gazebo/ROS 2 não conectado")

        self.info.configure(
            text=(
                f"Velocidade aplicada: {self.v:.2f} m/s | "
                f"Velocidade angular solicitada: {cmd_w:.2f} rad/s | "
                f"Comandos aceitos: {self.accepted} | "
                f"Bloqueados: {self.blocked}"
            )
        )
        self.root.after(100, self.tick)

def main(argv=None):
    parser = argparse.ArgumentParser(description="Cyber-Physical AMR Security Lab demo")
    parser.add_argument("--headless", action="store_true", help="Executa a simulação em modo terminal sem interface gráfica")
    args = parser.parse_args(argv)

    if args.headless or not is_gui_available():
        print("Ambiente sem interface gráfica; executando modo terminal.")
        for line in headless_mode():
            print(line)
        return

    root = tk.Tk()
    Demo(root)
    root.mainloop()


if __name__ == "__main__":
    main()

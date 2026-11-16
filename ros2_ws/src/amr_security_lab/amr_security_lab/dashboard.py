"""ROS dashboard (requires desktop GUI in WSL)."""
import tkinter as tk
import threading
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from nav_msgs.msg import Odometry
from geometry_msgs.msg import Twist

class Telemetry(Node):
    def __init__(self):
        super().__init__('security_dashboard')
        self.status='AGUARDANDO';self.position='sem odometria';self.velocity='sem comando'
        self.create_subscription(String,'/security_status',lambda m:setattr(self,'status',m.data),10)
        self.create_subscription(Odometry,'/odom',self.odom,10)
        self.create_subscription(Twist,'/cmd_vel',lambda m:setattr(self,'velocity',f'{m.linear.x:.2f} m/s'),10)
    def odom(self,m):
        p=m.pose.pose.position;self.position=f'x={p.x:.2f}, y={p.y:.2f}'

def main(args=None):
    rclpy.init(args=args);n=Telemetry()
    worker=threading.Thread(target=rclpy.spin,args=(n,),daemon=True);worker.start()
    root=tk.Tk();root.title('AMR Security Lab — Telemetria ROS 2');root.geometry('540x250')
    fields=[tk.Label(root,font=('Segoe UI',16),pady=12) for _ in range(3)]
    for f in fields:f.pack()
    def refresh():
        fields[0].config(text='Segurança: '+n.status,fg='red' if 'BLOCKED' in n.status else 'green')
        fields[1].config(text='Posição: '+n.position)
        fields[2].config(text='Velocidade: '+n.velocity)
        root.after(200,refresh)
    refresh();root.mainloop();n.destroy_node();rclpy.shutdown()

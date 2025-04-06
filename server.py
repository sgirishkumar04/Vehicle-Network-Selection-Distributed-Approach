import threading
import time
import math
import socket
import json
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.animation import FuncAnimation
from queue import Queue

# State constants
WS = "WS"  # WiFi Streaming (self)
DS = "DS"  # DSRC Streaming (via neighbor)
CS = "CS"  # Cellular Streaming (fallback)
NS = "NS"  # Not Streaming

WIFI_RANGE = 30  # Maximum range for WiFi sharing 

class Vehicle:
    def __init__(self, vehicle_id, position):
        self.vehicle_id = vehicle_id
        self.position = position
        self.state = WS if vehicle_id in {1, 5} else NS
        self.neighbors = []
        self.wifi_available = vehicle_id in {1, 5}
        self.cellular_available = False if vehicle_id == 4 else False
        self.received_states = {}
        self.received_from = None
        self.lock = threading.Lock()

    def is_streaming(self):
        return self.state in {WS, DS, CS}

    def broadcast_state(self):
        with self.lock:
            for neighbor in self.neighbors:
                neighbor.receive_state(self.vehicle_id, self.state, self.position)

    def receive_state(self, sender_id, state, sender_position):
        with self.lock:
            distance = math.dist(self.position, sender_position)
            if distance <= WIFI_RANGE:
                self.received_states[sender_id] = (state, sender_position)

    def update_state(self):
        with self.lock:
            if self.wifi_available:
                self.state = WS
                self.cellular_available = False
                return
            
            if self.vehicle_id != 4:
                self.cellular_available = False
            
            nearest_ws = None
            min_distance = float('inf')
            
            for vid, (state, pos) in self.received_states.items():
                if state == WS:
                    distance = math.dist(self.position, pos)
                    if distance <= WIFI_RANGE and distance < min_distance:
                        nearest_ws = vid
                        min_distance = distance
            
            if nearest_ws is not None:
                self.state = DS
                self.received_from = nearest_ws
            else:
                if self.vehicle_id == 4:
                    self.state = NS
                else:
                    self.cellular_available = True
                    self.state = CS if self.cellular_available else NS
            
            self.received_states.clear()

    def move(self, new_position):
        with self.lock:
            self.position = new_position
        self.update_state()

    def to_dict(self):
        return {
            'vehicle_id': self.vehicle_id,
            'position': self.position,
            'state': self.state,
            'wifi_available': self.wifi_available,
            'cellular_available': self.cellular_available,
            'received_from': self.received_from,
            'is_streaming': self.is_streaming()
        }

class SimulationServer:
    def __init__(self):
        self.vehicles = []
        self.running = False
        self.command_queue = Queue()
        self.lock = threading.Lock()
        self.initialize_vehicles()
        self.need_refresh = False  # Flag to force refresh
        
        # Visualization setup
        self.fig, self.ax = plt.subplots(figsize=(14, 10))
        self.ax.set_facecolor('#f0f0f0')
        self.ax.set_xlim(-50, 200)
        self.ax.set_ylim(-50, 200)
        self.ax.grid(True, color='white', alpha=0.4)
        self.ax.set_title('Vehicle Network State Visualization', fontsize=16, pad=20)
        
        self.state_colors = {
            'WS': '#2ecc71',  # Emerald green
            'DS': '#3498db',  # Peter River blue
            'CS': '#e67e22',  # Carrot orange
            'NS': '#e74c3c'   # Alizarin red
        }
        
        self.vehicle_markers = []
        self.connection_lines = []
        self.vehicle_labels = []
        self.setup_visualization()
        
        # Network setup
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.host = socket.gethostbyname(socket.gethostname())  # Get local IP
        self.port = 65432
        self.client_threads = []
        self.ani = None
        
    def initialize_vehicles(self):
        positions = [
            (0, 0),      # Vehicle 0
            (10, 0),     # Vehicle 1 (Permanent WiFi)
            (20, 0),     # Vehicle 2
            (100, 100),  # Vehicle 3
            (110, 100),  # Vehicle 4 (No cellular capability)
            (120, 100)   # Vehicle 5 (Permanent WiFi)
        ]
        
        self.vehicles = [Vehicle(i, pos) for i, pos in enumerate(positions)]
        
        # Set up neighbor relationships
        for v in self.vehicles:
            v.neighbors = [n for n in self.vehicles if n.vehicle_id != v.vehicle_id]
    
    def setup_visualization(self):
        for v in self.vehicles:
            color = self.state_colors[v.state]
            marker = self.ax.scatter(
                v.position[0], v.position[1],
                s=400, color=color,
                edgecolor='black', linewidth=2,
                zorder=3,
                alpha=0.9
            )
            
            label = self.ax.text(
                v.position[0], v.position[1] - 10,
                f"V{v.vehicle_id}",
                ha='center', va='center',
                fontsize=12, fontweight='bold',
                color='black',
                bbox=dict(
                    boxstyle='round,pad=0.3',
                    facecolor='white',
                    alpha=0.8,
                    edgecolor='black',
                    linewidth=1,
                    zorder=4
                )
            )
            
            self.vehicle_markers.append(marker)
            self.connection_lines.append(None)
            self.vehicle_labels.append(label)
            
        legend_elements = [
            patches.Patch(color='#2ecc71', label='WS (WiFi Source)'),
            patches.Patch(color='#3498db', label='DS (DSRC Connected)'),
            patches.Patch(color='#e67e22', label='CS (Cellular)'),
            patches.Patch(color='#e74c3c', label='NS (Not Streaming)'),
            patches.Patch(facecolor='white', edgecolor='black', label='Vehicle Number (V#)')
        ]
        
        self.ax.legend(
            handles=legend_elements,
            loc='upper right',
            fontsize=11,
            title='Legend',
            title_fontsize=12,
            framealpha=1
        )
    
    def update_visualization(self, frame):
        # Process any pending commands
        while not self.command_queue.empty():
            cmd = self.command_queue.get()
            self.process_command(cmd)
            self.need_refresh = True  # Set refresh flag when commands are processed
        
        # Only update if there are changes or refresh is needed
        if not self.need_refresh and frame % 10 != 0:  # Update every 10 frames if no changes
            return self.vehicle_markers + self.vehicle_labels + [x for x in self.connection_lines if x is not None]
        
        self.need_refresh = False  # Reset refresh flag
        
        # Clear previous connection lines
        for line in self.connection_lines:
            if line is not None:
                line.remove()
        self.connection_lines = []
        
        # Update all vehicle states first
        for v in self.vehicles:
            v.broadcast_state()
            v.update_state()
        
        # Then update visualization
        for i, v in enumerate(self.vehicles):
            self.vehicle_markers[i].set_offsets([v.position])
            self.vehicle_markers[i].set_color(self.state_colors[v.state])
            self.vehicle_labels[i].set_position((v.position[0], v.position[1] - 10))
            
            if v.state == 'DS':
                source_pos = next((n.position for n in self.vehicles if n.vehicle_id == v.received_from), None)
                if source_pos:
                    line, = self.ax.plot(
                        [v.position[0], source_pos[0]],
                        [v.position[1], source_pos[1]],
                        color='#3498db', linestyle='--', 
                        linewidth=2.5, alpha=0.7,
                        zorder=2
                    )
                    self.connection_lines.append(line)
                else:
                    self.connection_lines.append(None)
            else:
                self.connection_lines.append(None)
        
        return self.vehicle_markers + self.vehicle_labels + [x for x in self.connection_lines if x is not None]
    
    def process_command(self, cmd):
        try:
            cmd_type = cmd.get('type')
            if cmd_type == 'move':
                vid = cmd['vehicle_id']
                x = cmd['x']
                y = cmd['y']
                if 0 <= vid < len(self.vehicles):
                    self.vehicles[vid].move((x, y))
            elif cmd_type == 'status':
                pass  # Handled in client handler
            elif cmd_type == 'refresh':
                self.need_refresh = True
        except Exception as e:
            print(f"Error processing command: {e}")
    
    def get_status(self):
        return [v.to_dict() for v in self.vehicles]
    
    def handle_client(self, conn, addr):
        print(f"Connected by {addr}")
        try:
            while self.running:
                data = conn.recv(1024).decode('utf-8')
                if not data:
                    break
                
                try:
                    cmd = json.loads(data)
                    if cmd.get('type') == 'status':
                        response = json.dumps({'status': 'success', 'data': self.get_status()})
                    else:
                        self.command_queue.put(cmd)
                        response = json.dumps({'status': 'success', 'message': 'Command queued'})
                    
                    conn.sendall(response.encode('utf-8'))
                except json.JSONDecodeError:
                    conn.sendall(json.dumps({'status': 'error', 'message': 'Invalid JSON'}).encode('utf-8'))
        except ConnectionResetError:
            print(f"Client {addr} disconnected abruptly")
        finally:
            conn.close()
            print(f"Connection with {addr} closed")
    
    def cleanup(self):
        print("Cleaning up resources...")
        self.running = False
        
        # Close all client connections
        for thread in self.client_threads:
            thread.join()
        
        # Close server socket
        if hasattr(self, 'server_socket') and self.server_socket:
            self.server_socket.close()
            print("Server socket closed")
        
        # Stop animation
        if self.ani:
            self.ani.event_source.stop()
            print("Animation stopped")
        
        # Close matplotlib figure
        plt.close(self.fig)
        print("Figure closed")
    
    def start_server(self):
        try:
            self.running = True
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            print(f"Server started on {self.host}:{self.port}")
            
            # Start animation with a longer interval to reduce CPU usage
            self.ani = FuncAnimation(
                self.fig, self.update_visualization,
                frames=100, interval=500, blit=False, repeat=True
            )
            
            # Start server thread
            server_thread = threading.Thread(target=self.accept_connections, daemon=True)
            server_thread.start()
            
            # Set up proper closing handler
            def on_close(event):
                self.cleanup()
            
            self.fig.canvas.mpl_connect('close_event', on_close)
            
            plt.show()
            
        except Exception as e:
            print(f"Server error: {e}")
        finally:
            self.cleanup()
    
    def accept_connections(self):
        while self.running:
            try:
                conn, addr = self.server_socket.accept()
                client_thread = threading.Thread(target=self.handle_client, args=(conn, addr))
                client_thread.start()
                self.client_threads.append(client_thread)
            except OSError as e:
                if self.running:
                    print(f"Connection error: {e}")
                break
        
        print("Stopped accepting new connections")

if __name__ == "__main__":
    server = SimulationServer()
    server.start_server()
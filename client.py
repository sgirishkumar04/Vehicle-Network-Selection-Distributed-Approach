import socket
import json
import threading
import time

class VehicleClient:
    def __init__(self, host=None, port=65432):
        self.host = host
        self.port = port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.running = False
        self.controlled_vehicle = None
    
    def connect(self):
        try:
            if self.host is None:
                self.host = input("Enter server IP address: ")
            self.socket.connect((self.host, self.port))
            self.running = True
            print(f"Connected to server at {self.host}:{self.port}")
            return True
        except ConnectionRefusedError:
            print("Connection refused. Is the server running?")
            return False
        except Exception as e:
            print(f"Connection error: {e}")
            return False
    
    def send_command(self, cmd):
        try:
            self.socket.sendall(json.dumps(cmd).encode('utf-8'))
            response = self.socket.recv(1024).decode('utf-8')
            return json.loads(response)
        except Exception as e:
            print(f"Error sending command: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def move_vehicle(self, x, y):
        cmd = {
            'type': 'move',
            'vehicle_id': self.controlled_vehicle,
            'x': x,
            'y': y
        }
        return self.send_command(cmd)
    
    def get_status(self):
        cmd = {'type': 'status'}
        return self.send_command(cmd)
    
    def refresh(self):
        cmd = {'type': 'refresh'}
        return self.send_command(cmd)
    
    def select_vehicle(self):
        response = self.get_status()
        if response['status'] != 'success':
            print("Failed to get vehicle status from server")
            return False
        
        vehicles = response['data']
        print("\nAvailable Vehicles:")
        for v in sorted(vehicles, key=lambda x: x['vehicle_id']):
            print(f"Vehicle {v['vehicle_id']} @ {v['position']}")
        
        while True:
            try:
                vid = int(input("\nEnter Vehicle ID you want to control (or -1 to exit): "))
                if vid == -1:
                    return False
                if any(v['vehicle_id'] == vid for v in vehicles):
                    self.controlled_vehicle = vid
                    print(f"\nYou are now controlling Vehicle {vid}")
                    print("Type 'help' for available commands")
                    return True
                else:
                    print(f"Invalid Vehicle ID. Please choose from available vehicles.")
            except ValueError:
                print("Please enter a valid number")
    
    def start_interactive(self):
        if not self.connect():
            return
        
        if not self.select_vehicle():
            self.socket.close()
            return
        
        try:
            while self.running:
                user_input = input(f"V{self.controlled_vehicle}> ").strip().lower()
                
                if user_input in ['exit', 'quit']:
                    self.running = False
                
                elif user_input in ['status', 's']:
                    response = self.get_status()
                    if response['status'] == 'success':
                        self.print_status(response['data'])
                    else:
                        print(f"Error: {response.get('message', 'Unknown error')}")
                
                elif user_input in ['help', 'h', '?']:
                    self.print_help()
                
                elif user_input.startswith('move'):
                    try:
                        parts = user_input.split()
                        if len(parts) == 3:
                            x = float(parts[1])
                            y = float(parts[2])
                            response = self.move_vehicle(x, y)
                            print(response.get('message', 'Command sent'))
                        else:
                            print("Usage: move x y")
                    except ValueError:
                        print("Invalid coordinates. Please enter numbers.")
                
                elif user_input in ['refresh', 'r']:
                    self.refresh()
                    print("Refresh request sent to server")
                
                else:
                    print("Unknown command. Type 'help' for available commands")
        finally:
            self.socket.close()
            print("Disconnected from server")
    
    def print_status(self, vehicles_data):
        print("\n" + "="*80)
        print("Current Vehicle Status:")
        print("-"*80)
        for v in sorted(vehicles_data, key=lambda x: x['vehicle_id']):
            status = "Streaming" if v['is_streaming'] else "Not Streaming"
            source = ""
            if v['state'] == 'DS':
                source = f" (via Vehicle {v['received_from']})"
            elif v['state'] == 'CS':
                source = " (via Cellular)"
            
            # Highlight the controlled vehicle
            prefix = ">>> " if v['vehicle_id'] == self.controlled_vehicle else "    "
            print(prefix + (f"Vehicle {v['vehicle_id']:>2} @ {str(v['position']):<9} | "
                  f"State: {v['state']:<2} | "
                  f"WiFi: {'ON ' if v['wifi_available'] else 'OFF'} | "
                  f"Cellular: {'ON ' if v['cellular_available'] else 'OFF'} | "
                  f"{status}{source}"))
        print("="*80)
    
    def print_help(self):
        print("\nAvailable Commands:")
        print("status (s)       - Show current status of all vehicles")
        print("move x y         - Move controlled vehicle to new position (e.g., 'move 50 0')")
        print("refresh (r)      - Force server to refresh the visualization")
        print("help (h, ?)      - Show this help message")
        print("exit (quit)      - Disconnect from server")

if __name__ == "__main__":
    client = VehicleClient()
    client.start_interactive()
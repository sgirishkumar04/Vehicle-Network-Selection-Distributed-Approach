# Vehicle Network Selection: A Distributed Approach 🚗💨

[![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![Matplotlib](https://img.shields.io/badge/Matplotlib-3.8-11557C?style=for-the-badge&logo=matplotlib)](https://matplotlib.org/)

A Python-based simulation that models a distributed network selection strategy for vehicles. This project demonstrates how vehicles can intelligently switch between different communication technologies (WiFi, DSRC, Cellular) to maintain continuous data streaming, prioritizing free, high-bandwidth options over costly cellular data.

The simulation features a live, interactive visualization and a multi-client architecture, allowing users to control vehicles and observe network state changes in real-time.

---

## ✨ Key Concepts & Features

-   **Distributed Decision-Making:** Each vehicle independently decides its network state based on available connections, without a central controller. This models a real-world, decentralized vehicle-to-everything (V2X) network.
-   **Multi-Tier Network Strategy:** Vehicles prioritize network connections in a specific order:
    1.  **WiFi (WS):** A vehicle with its own internet source acts as a provider.
    2.  **DSRC (DS):** If no personal WiFi is available, a vehicle will connect to a nearby WiFi-providing vehicle via DSRC (simulated WiFi).
    3.  **Cellular (CS):** If no DSRC connection is found, the vehicle falls back to its cellular data.
    4.  **No Service (NS):** A vehicle with no available connections (or no cellular capability) cannot stream.
-   **Live Matplotlib Visualization:** A server-side GUI provides a real-time plot of all vehicles, their current network state (color-coded), and the active DSRC connections.
-   **Interactive Multi-Client Control:**
    -   A command-line client (`client.py`) allows multiple users to connect to the simulation server.
    -   Users can select and control specific vehicles, issuing movement commands.
    -   The simulation updates in real-time for all connected clients and the main visualization.

---

## 🛠️ Technology Stack & Architecture

This project uses a client-server model to separate the simulation logic from user control.

-   **Simulation Core (`server.py`):**
    -   Manages the state and position of all `Vehicle` objects.
    -   Uses **Python's `threading`** to handle vehicle logic and network communication concurrently.
    -   Implements a **`socket`** server to listen for and process commands from multiple clients.
    -   Renders the visualization using **`matplotlib.animation.FuncAnimation`** for smooth, real-time updates.
-   **Interactive Client (`client.py`):**
    -   A command-line interface for users to interact with the simulation.
    -   Uses **`socket`** programming to connect to the server and send JSON-formatted commands.
-   **Communication Protocol:** A simple JSON-based protocol is used for sending commands (e.g., `move`, `status`) and receiving state updates between the client and server.

---

## 🚀 How to Run the Simulation Locally

### Prerequisites

-   Python 3.x
-   `pip` (Python package installer)

### Installation & Setup

1.  **Clone the repository:**
    ```sh
    git clone https://github.com/YOUR_USERNAME/Vehicle-Network-Selection-Distributed-Approach.git
    cd Vehicle-Network-Selection-Distributed-Approach
    ```

2.  **Install the required packages:**
    ```sh
    pip install -r requirements.txt
    ```

### Running the Simulation

You will need to open **two or more terminal windows**.

1.  **In Terminal 1: Start the Server**
    The server will start, and the Matplotlib visualization window will appear. Note the server's IP address printed in the terminal.
    ```sh
    python server.py
    ```

2.  **In Terminal 2 (and others): Start a Client**
    Run the client script. It will prompt you for the server's IP address (which you noted from Terminal 1).
    ```sh
    python client.py
    ```
    -   Enter the server IP when prompted.
    -   Select a vehicle to control from the available list.
    -   Type `help` to see available commands.

3.  **Interact!**
    -   Use the `move x y` command in the client terminal to move your selected vehicle.
    -   Observe the visualization window and see the vehicle's color (state) and connection lines change automatically as it moves in and out of range of other vehicles.

---

## 💡 Project Purpose & Learnings

This project was built to explore and visualize concepts in distributed systems and networking. Key learnings include:
-   Implementing a multi-threaded server to handle asynchronous client commands and simulation updates.
-   Designing a simple, effective client-server communication protocol with JSON.
-   Using Matplotlib to create dynamic, real-time data visualizations.
-   Modeling and simulating decentralized algorithms where individual agents make decisions based on local information.

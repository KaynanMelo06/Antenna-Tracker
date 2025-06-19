# Antenna Tracker

A Python application using PyQt5 and OpenCV for real-time antenna tracking and control via microcontroller.  
It captures video, corrects distortion, detects colored markers, computes angles, and uses a PID controller to send serial commands.

---

## ✨ Features

- Optical distortion correction (camera calibration).  
- HSV marker detection (orange, pink, green, yellow).  
- Real-time robot position and orientation estimation.  
- PID control for fine antenna adjustment.  
- PyQt5 graphical interface for visualization and calibration.  
- Serial communication (QSerialPort) with a microcontroller (configurable baud rate).

---

## 🚀 Installation

1. **Clone the repository**  
   ```bash
   git clone https://github.com/your-username/projetoantenaV1.git
   cd projetoantenaV1
   ```

2. **Create and activate a virtual environment**  
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate   # Linux / macOS
   .venv\Scripts\activate      # Windows
   ```

3. **Install the dependencies**  
   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration

- **Serial Port**  
  Set in `src/backend/comm/serial.py` or via parameter in `MainWindow`:  
  ```python
  self.serial = Serial(port="/dev/ttyUSB0", baudrate=115200)
  ```

- **Camera Index**  
  Set in `src/ui/mainwindow.py`:  
  ```python
  self.cap = cv2.VideoCapture('/dev/video2')
  ```

- **PID Parameters**  
  Adjust in `src/backend/control/pid.py` or directly through the UI:  
  ```python
  kp, ki, kd = 5.0, 0.00, 0.5
  ```

- **Initial HSV Ranges**  
  Defined in `src/ui/mainwindow.py`, but can be calibrated in real time.

---

## 📈 Usage

1. Launch the application:  
   ```bash
   python3 main.py
   ```

2. In the main window:  
   - View the **original frame** (with annotations) and the **filtered frame**.  
   - Select the marker color or choose “All”.  
   - Press **K** to start/pause the robot.  
   - Press **Esc** to exit fullscreen.

3. To calibrate HSV:  
   - Click **“Calibrate HSV”**.  
   - Adjust **H**, **S**, and **V** sliders.  
   - Use **Reset** to revert to default values or **Apply** to save new ranges.

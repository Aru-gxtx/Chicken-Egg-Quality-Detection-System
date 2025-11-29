# Chicken Egg Quality Detection Device Using Image Processing

This repository contains the software implementation for the **Chicken Egg Quality Detection Device Using Image Processing for Efficient Rural Production** study.

**Authors:** Aru-gxtx (Matthew Arni Bendo) and RafaelAntonioUy (Rafael Antonio E. Uy).

> _**Note:** This repository covers only the **software** aspect of the study. To replicate the full system, specific hardware components (listed below) are required. While manual replication is possible, the system is designed for automation._

---

## Hardware Requirements

To run the main detection program (`grand_final_setup.py`), the following hardware setup is necessary:

1.  **Control Unit:** Raspberry Pi 4 Model B (recommended).
2.  **Camera:** Pi Camera (IR Pi Camera used in this study, but standard models are compatible).
3.  **Microcontroller:** ESP32 Board.
4.  **Connection:** The ESP32 must be connected via **USB0** to the Raspberry Pi.
5.  **Display:** A monitor connected to the Pi for visualization.

---

## Getting Started

### Prerequisites

* Python 3.x.x
* Virtual Environment (`venv`)
* Flutter (for the dashboard)

### Installation

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Aru-gxtx/your-repo-name.git
    cd your-repo-name
    ```

2.  **Set up the Virtual Environment:**
    ```bash
    python -m venv venv
    # Activate the venv:
    source venv/bin/activate  # On Linux/Mac
    # or
    venv\Scripts\activate     # On Windows
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

---

## Usage

### 1. Running the Main System (Grand Final Setup)

The `grand_final_setup.py` is the core script that integrates the camera, the detection model, and the hardware control.

**To run manually:**
```bash
python grand_final_setup.py
```

**Important Notes:**
* The system requires all hardware components (Camera, ESP32 via USB0) to be connected. The script will fail if these conditions are not met.
* **Plug-and-Play Capability:** The system is designed to run automatically when the Pi receives power. To enable this feature, you must manually configure your Raspberry Pi to execute the script on boot (e.g., via `systemd` or `rc.local`).

### 2. Model Training

The repository includes a pre-trained model located in `train/weights/best.pt`. If you wish to retrain the model or create a new one, follow these steps:

1.  **Prepare Datasets:** Place your annotated images in the specified `datasets` folder. Ensure classes are separated into: `AA`, `A`, `B`, and `Inedible`.
2.  **Split Data:** Run the separator utility to divide data into train, validation, and test sets. This ensures better output and prevents overfitting.
    ```bash
    python datasets_separator.py
    ```
3.  **Classify:** Run the YAML configuration program to classify the annotated values.
    ```bash
    python data.yaml
    ```

### 3. Dashboard Application

The dashboard is built with Flutter and is used for analytics and monitoring.

* **Quick Start:** Use the pre-compiled `.exe` file available in the [Releases Page](#).
* **For Developers (Source Code):**
    1.  Navigate to the `dashboardegg` folder.
    2.  Open the source code and manually update the IP addresses in the **Dashboard** and **Analytics** pages.
    3.  **Critical:** The IP must match the address of the Control Unit (Raspberry Pi) running `grand_final_setup.py`.
    4.  Run the app:
        ```bash
        flutter run
        ```

---

## Testing & Calibration Tools

We provide several utility scripts to test individual functions manually. Note that these scripts often run continuously ("lively") and may be resource-intensive if left running.

### Model Accuracy Testing
Use `model_test.py` to test the model's detection accuracy without the full hardware loop.
* **Default:** Uses the PiCamera.
* **Customization:** You can edit the script to use other camera inputs.

### Size Detection Calibration
Use `simple_size_testing.py` to calibrate egg sizing. Since the camera is static, size is calculated based on pixel area.
* **Default Sizing Logic (Pixel Area):**
    * **0 - 300:** Small
    * **301 - 375:** Medium
    * **376+:** Large
* **Calibration:** You may need to adjust these values by testing with actual small and large eggs from a market to ensure accurate categorization.

### ESP32 & Servo Control
The sorting mechanism relies on an ESP32 controlling servos.

**Firmware:**
Upload `servo_controls.cpp` to your ESP32.
* **Default Servo Angles:**
    * **Inedible:** 0°
    * **Class B:** 20°
    * **Class A:** 43°
    * **Class AA:** 63°

**Testing Scripts:**
1.  **Angle Testing:** Use `simple_listener.py` along with `simple_controls.cpp`. This allows you to manually input angles to verify the servo moves to the correct position.
2.  **Communication Testing:** Use `servo_listener.py` to test data transmission from the Pi to the ESP32.
    * *Note:* Ensure you specify the accurate COM port.

---

## License

This project is part of an academic study. Please contact the authors for usage permissions regarding the datasets and specific implementation details.

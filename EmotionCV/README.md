# EmotionCV

This project uses OpenCV and DeepFace to perform real-time emotion detection from a webcam feed. It displays the dominant emotion, a probability distribution of all emotions, and a historical graph of emotion changes. The application also logs the emotion data to a CSV file.

## Features

-   Real-time emotion detection from webcam.
-   Displays dominant emotion and emotion probabilities.
-   Visualizes emotion history with a graph.
-   Logs emotion data to `emotion_log.csv`.
-   Uses MediaPipe for face detection.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/EmotionCV.git
    cd EmotionCV
    ```

2.  **Create a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Install the dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## How to Run

1.  **Activate the virtual environment:**
    ```bash
    source venv/bin/activate
    ```

2.  **Run the application:**
    ```bash
    python3 emotion_detection.py
    ```

3.  **View the output:**
    -   A window will open showing the webcam feed with emotion analysis overlays.
    -   The `emotion_log.csv` file will be created in the project directory and will be updated in real-time with the emotion data.

4.  **To stop the application, press the `ESC` key.**

## Dependencies

The project uses the following major libraries:

-   OpenCV
-   DeepFace
-   TensorFlow
-   MediaPipe
-   Pygame

All dependencies are listed in the `requirements.txt` file.

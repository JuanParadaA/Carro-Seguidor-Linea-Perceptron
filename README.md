# Vision-Based Line Following and Web-Controlled Mobile Robot

This project consists of a mobile robotic vehicle capable of operating in two different modes: autonomous line following using a camera-based vision system, and remote control through a web interface accessible from a smartphone.

The system is built around a Raspberry Pi Pico and integrates embedded processing, computer vision, and wireless control.

---

## Features

- Vision-based line following using an OV7670 camera
- Remote control through a web interface
- Smartphone compatibility for robot control
- LED display showing system status and connection IP
- Dual operating modes (autonomous and manual)
- AI implementation with perceptron to correct line tracking

---

## Hardware

The robot was built using the following main components:

- **Raspberry Pi Pico**
- **OV7670 camera module**
- **Motor driver**
- **DC motors**
- **LED display**
- **Power supply (battery pack)**

---

## System Architecture

The robot operates in two modes:

### 1. Vision-Based Line Following

The OV7670 camera captures images of the track.  
The embedded system processes the image data to detect the line and determine the appropriate steering commands for the motors.

### 2. Web-Based Remote Control

A web interface allows the user to control the robot directly from a smartphone.

Features of the interface include:

- Directional control (forward, backward, left, right)
- Real-time connection through the robot's IP address
- Easy access from any device with a web browser

---

## User Interface

The system includes an LED display that shows:

- Current operating status
- IP address used to access the control interface

This allows users to easily connect to the robot from a smartphone.

---

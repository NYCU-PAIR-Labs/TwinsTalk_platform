# TwinsTalk Remote Vision Inference Server

This repository is part of the **TwinsTalk** project, a general-purpose AI platform designed for distributed, multimodal, and device-agnostic intelligence services.

This module provides a **remote computer vision inference service**, inspired by MediaPipe, enabling object detection and pose estimation to be executed on a powerful server while lightweight clients (including mobile devices) upload images or videos for analysis.

---

## Project Context: TwinsTalk

**TwinsTalk** is a unified AI platform designed to decouple sensing, computation, and interaction across heterogeneous devices.  
Its core design philosophy is to allow resource-constrained clients to access advanced AI capabilities through networked services running on high-performance machines.

Within the TwinsTalk architecture, this repository serves as a **vision inference backend**, demonstrating how visual perception tasks can be deployed as reusable, remote AI services.

---

## Overview

Traditional MediaPipe pipelines require models to run locally, which limits their usability on devices with insufficient computational resources.  
This project extends the MediaPipe concept into a **server-based inference architecture**, where:

- AI models are executed on a centralized server
- Clients upload images or videos via a network interface
- The server performs inference and returns structured results
- The inference task can be switched dynamically (e.g., object detection or pose estimation)

This design enables TwinsTalk to support visual perception as a scalable and reusable AI service.

---

## Key Features

- Remote vision inference server
- MediaPipe-like abstraction with server-side execution
- Support for multiple vision tasks
  - Object Detection
  - Pose Estimation
- Image and video upload from remote clients
- Lightweight client-side scripts
- Designed for project demonstrations and system-level prototyping

---

## Project Structure

```text
.
├── server.py            # Main server entry point
├── analyze.py           # Core vision inference logic
├── upload_video.py      # Client script for uploading videos
├── test_upload.py       # Simple client-side upload test
├── templates/           # HTML templates (if applicable)
├── requirements.txt     # Python dependencies

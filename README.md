# Hermes - Driving The ACROPOLIS Network
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/release/python-3120/)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.16747031.svg)](https://doi.org/10.5281/zenodo.16747031)
[![mypy](https://github.com/tum-esm/hermes/actions/workflows/test-edge-node.yaml/badge.svg)](https://github.com/tum-esm/ACROPOLIS-edge/actions)


Hermes is a management software for autonomous sensor networks. 

It consists of three parts: The sensor system, the server, and the dashboard.

The systems run autonomously and communicate with the server via MQTT. The server stores the data in a database and provides a REST API for data download and the dashboard.

<br/>

## 🎯 Main goals

1. Observe system status and measurements in real-time
2. Update the system configuration remotely
3. Update the system software remotely
4. Easy setup and deployment of Hermes Infrastructure

<br/>

## 📦 Practical usage

This software is developed for the ACROPOLIS network. The goal of ACROPOLIS is to measure CO2 concentrations in the city of Munich. The network spans 20 roof-top systems.

<br/>

## 🔨 Sensor System

![](docs/hermes-main-py.png)

<br/>

## 🔨 Architecture

![](docs/schema.png)

<br/>

## 🪄 Dashboard

Built using React, NextJS, TailwindCSS, and TypeScript.

![](docs/hermes-dashboard-demo-1.png)


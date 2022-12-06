# Tentacruel!

Here, an open-source software for autonomous sensor networks is created.

The network has three parts: the sensors themselves, the server, and the dashboard.

The sensors communicate with the server via MQTT. The server stores the data in a database and provides a REST API for the dashboard.

## Main goals 🎯

- The network and sensors should be as reliable and autonomous as possible
- It must be possible to see what's happening on the sensors in real-time and remotely
- It must be possible to update the software on the sensors remotely
- There must be an easy and clear overview of the status of the sensors
- The software should be reusable for other sensor networks without changes

## Practical usage 📦

This software is developed for the CARBONet (?) project. The goal of CARBONet (?) is to measure CO2 concentrations in the city of Munich. The network spans 20 sensors.

## Structure 🔨

![](assets/schema.png)

# Hermes - Driving The ACROPOLIS Network

Here, a management software for autonomous sensor networks is created.

The system is made of three parts: the sensors system, the server, and the dashboard.

The sensors communicate with the server via MQTT. The server stores the data in a database and provides a REST API for the dashboard.

<br/>

## 🎯 Main goals

1. The status and measurements of the sensors can be observed in real-time and remotely
1. The sensors can be configured remotely
1. The software on the sensors can be updated remotely
1. Easy setup and deployment of Hermes

<br/>

## 📦 Practical usage

This software is developed for the ACROPOLIS network. The goal of ACROPOLIS is to measure CO2 concentrations in the city of Munich. The network spans 20 sensors.

<br/>

## 🔨 Structure

![](docs/schema.png)

<br/>

## 🪄 Hermes Dashboard

Built using React, NextJS, TailwindCSS, and TypeScript.

Some impressions:

![](docs/hermes-dashboard-demo-1.png)

![](docs/hermes-dashboard-demo-2.png)

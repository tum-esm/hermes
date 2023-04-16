import { SENSOR_IDS } from "@/utils/constants";
import { create } from "zustand";

type ServerState = {
  state: null | {
    environment: string;
    commit_sha: string;
    branch_name: string;
    start_timestamp: number;
  };
  setState: (newState: {
    environment: string;
    commit_sha: string;
    branch_name: string;
    start_timestamp: number;
  }) => void;
};

export const useServerStore = create<ServerState>((set) => ({
  state: null,
  setState: (newState) => set((state) => ({ state: newState })),
}));

export type SensorState = {
  sensorId: string;
  data:
    | null
    | {
        sensor_identifier: string;
        creation_timestamp: number;
        measurement: any;
      }[];
  logs:
    | null
    | {
        sensor_identifier: string;
        severity: "error" | "warning" | "info";
        subject: string;
        min_revision: number;
        max_revision: number;
        min_creation_timestamp: number;
        max_creation_timestamp: number;
        count: number;
      }[];
};

type NetworkState = {
  state: SensorState[];
  setSensorData: (
    sensorId: string,
    newSensorData: {
      sensor_identifier: string;
      creation_timestamp: number;
      measurement: any;
    }[]
  ) => void;
  setSensorLogs: (
    sensorId: string,
    newSensorLogs: {
      sensor_identifier: string;
      severity: "error" | "warning" | "info";
      subject: string;
      min_revision: number;
      max_revision: number;
      min_creation_timestamp: number;
      max_creation_timestamp: number;
      count: number;
    }[]
  ) => void;
};

export const useNetworkStore = create<NetworkState>((set) => ({
  state: Object.values(SENSOR_IDS).map((sensorId) => ({
    sensorId: sensorId,
    data: null,
    logs: null,
  })),
  setSensorData: (sensorId, newSensorData) =>
    set((state) => ({
      state: state.state.map((sensor) =>
        sensor.sensorId === sensorId
          ? {
              ...sensor,
              data: newSensorData,
            }
          : { ...sensor }
      ),
    })),
  setSensorLogs: (sensorId, newSensorLogs) =>
    set((state) => ({
      state: state.state.map((sensor) =>
        sensor.sensorId === sensorId
          ? {
              ...sensor,
              logs: newSensorLogs,
            }
          : { ...sensor }
      ),
    })),
}));

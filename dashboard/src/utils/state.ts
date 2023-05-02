import { SENSOR_IDS } from "@/src/utils/constants";
import { create } from "zustand";

namespace StateObjects {
  export type ServerStatus = {
    environment: string;
    commit_sha: string;
    branch_name: string;
    start_timestamp: number;
  };
  export type SensorData = {
    sensor_identifier: string;
    creation_timestamp: number;
    measurement: any;
  };
  export type SensorLog = {
    revision: number;
    creation_timestamp: number;
    sensor_identifier: string;
    severity: "error" | "warning" | "info";
    subject: string;
    details: string;
  };
  export type SensorAggregatedLog = {
    sensor_identifier: string;
    severity: "error" | "warning" | "info";
    subject: string;
    min_revision: number;
    max_revision: number;
    min_creation_timestamp: number;
    max_creation_timestamp: number;
    count: number;
  };
}

type ServerState = {
  state: null | StateObjects.ServerStatus;
  setState: (newState: StateObjects.ServerStatus) => void;
};

export const useServerStore = create<ServerState>((set) => ({
  state: null,
  setState: (newState) => set((state) => ({ state: newState })),
}));

export type SensorState = {
  sensorId: string;
  data: null | StateObjects.SensorData[];
  logs: null | StateObjects.SensorLog[];
  aggregatedLogs: null | StateObjects.SensorAggregatedLog[];
};

type NetworkState = {
  state: SensorState[];
  setData: (sensorId: string, newData: StateObjects.SensorData[]) => void;
  setLogs: (sensorId: string, newLogs: StateObjects.SensorLog[]) => void;
  setAggregatedLogs: (
    sensorId: string,
    newAggregatedLogs: StateObjects.SensorAggregatedLog[]
  ) => void;
};

export const useNetworkStore = create<NetworkState>((set) => ({
  state: Object.values(SENSOR_IDS).map((sensorId) => ({
    sensorId: sensorId,
    data: null,
    logs: null,
    aggregatedLogs: null,
  })),
  setData: (sensorId, newData) =>
    set((state) => ({
      state: state.state.map((sensor) =>
        sensor.sensorId === sensorId
          ? {
              ...sensor,
              data: newData,
            }
          : { ...sensor }
      ),
    })),
  setLogs: (sensorId, newLogs) =>
    set((state) => ({
      state: state.state.map((sensor) =>
        sensor.sensorId === sensorId
          ? {
              ...sensor,
              logs: newLogs,
            }
          : { ...sensor }
      ),
    })),
  setAggregatedLogs: (sensorId, newAggregatedLogs) =>
    set((state) => ({
      state: state.state.map((sensor) =>
        sensor.sensorId === sensorId
          ? {
              ...sensor,
              aggregatedLogs: newAggregatedLogs,
            }
          : { ...sensor }
      ),
    })),
}));

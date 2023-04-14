import { SENSOR_IDS } from "@/components/constants";
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

export function determinSensorStatus(
  sensor: SensorState
): "online" | "unstable" | "error" | "offline" | undefined {
  if (sensor.data === null || sensor.logs === null) {
    return undefined;
  }

  // has data in last 30 minutes
  const hasData =
    sensor.data.filter(
      (data) => data.creation_timestamp > Date.now() - 30 * 60 * 1000
    ).length > 0;

  // has logs in last 30 minutes
  const hasLogs =
    sensor.logs.filter(
      (log) => log.max_creation_timestamp > Date.now() - 30 * 60 * 1000
    ).length > 0;

  if (hasData && !hasLogs) {
    return "online";
  } else if (hasData && hasLogs) {
    return "unstable";
  } else if (!hasData && hasLogs) {
    return "error";
  } else {
    return "offline";
  }
}

import {create} from "zustand";

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

type ClientState = {
    selectedNetwork: string;
    setSelectedNetwork: (newNetwork: string) => void;
}
export const useClientStore = create<ClientState>((set) => ({
    selectedNetwork: "",
    setSelectedNetwork: (newNetwork) => {
        if(window?.localStorage){
            window.localStorage.setItem("selectedNetwork", newNetwork);
        }
        set((_) => ({selectedNetwork: newNetwork}))
    },
}));

type ServerState = {
    state: null | StateObjects.ServerStatus;
    setState: (newState: StateObjects.ServerStatus) => void;
};

export const useServerStore = create<ServerState>((set) => ({
    state: null,
    setState: (newState) => set((state) => ({state: newState})),
}));


type Network = {
    network_identifier: string;
    network_name: string;
};
type NetworksState = {
    networks: Network[],
    setNetworks: (newNetworks: Network[]) => void;
}

export const useNetworksStore = create<NetworksState>((set) => ({
    setNetworks: (newNetworks: Network[]) => set((state) => ({networks: newNetworks})),
    networks: [],
}))

// store auth token, username and wether user is logged in or not
type AuthState = {
    token: string | null;
    username: string | null;
    loggedIn: boolean;
    setAuthState: (newToken: any, newUsername: any, newLoggedIn: any) => void;
    setToken: (newToken: string) => void;
    setUsername: (newUsername: string) => void;
    setLoggedIn: (newLoggedIn: boolean) => void;
}
export const useAuthStore = create<AuthState>((set) => ({
    token: null,
    username: null,
    loggedIn: false,
    setAuthState: (newToken: any, newUsername: any, newLoggedIn: any) => set((state) => ({
        token: newToken,
        username: newUsername,
        loggedIn: newLoggedIn
    })),
    setToken: (newToken) => set((state) => ({token: newToken})),
    setUsername: (newUsername) => set((state) => ({username: newUsername})),
    setLoggedIn: (newLoggedIn) => set((state) => ({loggedIn: newLoggedIn})),
}));

export type SensorState = {
    sensorId: string;
    data: null | StateObjects.SensorData[];
    logs: null | StateObjects.SensorLog[];
    aggregatedLogs: null | StateObjects.SensorAggregatedLog[];
    name: null|string;
};

type SensorsState = {
    state: SensorState[];
    setState: (newState: SensorState[]) => void;
    setData: (sensorId: string, newData: StateObjects.SensorData[]) => void;
    setLogs: (sensorId: string, newLogs: StateObjects.SensorLog[]) => void;
    setAggregatedLogs: (
        sensorId: string,
        newAggregatedLogs: StateObjects.SensorAggregatedLog[]
    ) => void;
};

export const useSensorsStore = create<SensorsState>((set) => ({
    setState: (newState) => set((state) => ({state: newState})),
    state: [],
    setData: (sensorId, newData) =>
        set((state) => ({
            state: state.state.map((sensor) =>
                sensor.sensorId === sensorId
                    ? {
                        ...sensor,
                        data: newData,
                    }
                    : {...sensor}
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
                    : {...sensor}
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
                    : {...sensor}
            ),
        })),
}));

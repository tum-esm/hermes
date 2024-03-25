import {SensorList} from "../components/layout/sensorList";
import {Header} from "../components/layout/header";
import {useEffect} from "react";
import {useServerStore, useSensorsStore, useAuthStore, useNetworksStore, useClientStore} from "../utils/state";
import {SERVER_URL, URL_BASE_NAME} from "../utils/constants";
import {Footer} from "../components/layout/footer";

export default function Layout({children}: { children: React.ReactNode }) {
    const setServerState = useServerStore((state) => state.setState);
    const isLoggedIn = useAuthStore((state) => state.loggedIn);
    const authToken = useAuthStore((state) => state.token);
    const setSensorData = useSensorsStore((state) => state.setData);
    const setSensorLogs = useSensorsStore((state) => state.setLogs);
    let selectedNetwork = useClientStore((state) => state.selectedNetwork);
    const setSensorAggregatedLogs = useSensorsStore(
        (state) => state.setAggregatedLogs
    );

    if (typeof window !== "undefined") {
        if(!isLoggedIn){
            if (window.localStorage.getItem("auth") !== null) {
                console.log("setting auth state from local storage")
                let auth = JSON.parse(window.localStorage.getItem("auth") as string);
                useAuthStore.getState().setAuthState(auth.token, auth.username, auth.loggedIn);
            }else{
                console.log("no auth state in local storage")
                if(window.location.pathname !== URL_BASE_NAME + "/login")
                    window.location.href = URL_BASE_NAME + "/login";
            }
        }

        if (window.localStorage.getItem("selectedNetwork") !== null){
            console.log("setting selected network from local storage")
            useClientStore.getState().setSelectedNetwork(window.localStorage.getItem("selectedNetwork") as string);
        }
    }


    useEffect(() => {
        updateSensorData(setServerState, setSensorData, setSensorLogs, setSensorAggregatedLogs, selectedNetwork);
    }, [selectedNetwork]);

    return (
        <>
            <div className="flex h-screen w-screen items-center justify-center text-lg xl:hidden">
                Please use a larger screen
            </div>
            <div className="hidden xl:block">
                <Header/>
                <main className="flex h-[calc(100vh-4rem)] w-screen flex-row">
                    <nav
                        className="flex h-full w-[24rem] flex-shrink-0 flex-col overflow-y-scroll border-r border-slate-300">
                        <SensorList/>
                    </nav>
                    <div
                        className="h-full flex-grow overflow-y-scroll bg-slate-50 p-6 pb-32 ">
                        {children}
                    </div>
                </main>
                <Footer/>
            </div>
        </>
    );
}


function updateSensorData(
    setServerState: (data: any) => void,
    setSensorData: (sensorId: string, newData: any) => void,
    setSensorLogs: (sensorId: string, newLogs: any) => void,
    setSensorAggregatedLogs: (sensorId: string, newAggregatedLogs: any) => void,
    selectedNetwork:string ) {
    console.log("start fetching");

    fetch(`${SERVER_URL}/status`, {
        headers: {
            "Content-Type": "application/json"
        },
        cache: "no-cache",
    })
        .then((res) => res?.json())
        .then((data) => {
            if (data === undefined) {
                throw "";
            } else {
                console.log({data});
                setServerState(data);
                console.log("successfully loaded server state");
            }
        })
        .catch((err) => {
            console.error("could not load server state");
        });

    fetch(`${SERVER_URL}/networks`, {
        headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${useAuthStore.getState().token}`
        },
        cache: "no-cache",
    })
        .then((res)=>{
            if (res.status === 401) {
                if (typeof window !== "undefined") {
                    window.localStorage.removeItem("auth");
                }
                useAuthStore.getState().setAuthState(null, null, false);
                // redirect to login page if not on login page
                if (window.location.pathname !== URL_BASE_NAME + "/login")
                    window.location.href = URL_BASE_NAME + "/login";
                throw "Unauthorized"
            }
            return res;
        })
        .then((res) => res?.json())
        .then((data) => {
            if (data === undefined || data.hasOwnProperty("details")){
                throw "Failed to fetch networks";
            } else {
                return data;
            }
        })
        .catch((err) => {
            console.error("could not fetch networks");
            throw err;
        })
        .then(async networks => {
            console.log("got networks: ", networks);
            // update networks-store
            useNetworksStore.getState().setNetworks(networks);
            // set selected network
            if(!useClientStore.getState().selectedNetwork && networks.length > 0){
                console.log("setting selected network to first network")
                selectedNetwork = networks[0].network_identifier;
                useClientStore.getState().setSelectedNetwork(selectedNetwork);
            }
            if(!selectedNetwork || networks.length === 0){
                console.log("No networks available");
                return {};
            }else{
                return fetch(`${SERVER_URL}/networks/${selectedNetwork}/sensors`, {
                    headers: {
                        "Content-Type": "application/json",
                        "Authorization": `Bearer ${useAuthStore.getState().token}`
                    },
                    cache: "no-cache",
                }).then((res) => res?.json())
            }
        })
        .then(async (data) => {
            if (data === undefined || !data.map){
                throw "Failed to fetch sensors";
            } else {
                console.log("got sensors: ", data);
                // update sensors-store
                useSensorsStore.getState().setState(data.map((sensor: any) => {
                    return {
                        sensorId: sensor.sensor_identifier,
                        data: null,
                        logs: null,
                        aggregatedLogs: null,
                        name: sensor.sensor_name
                    }
                }));

                let SENSOR_IDS = data.map((sensor: any) => sensor.sensor_identifier);
                for(let sensorId of SENSOR_IDS){
                    if (SENSOR_IDS.length > 30 && SENSOR_IDS.length <= 80) {
                        await new Promise(r => setTimeout(r, 150));
                    }
                    if (SENSOR_IDS.length > 80) {
                        if(!window?.localStorage || sensorId !== window.localStorage.selectedSensor){
                            continue;
                        }
                    }
                    console.log(`start fetching data/logs for sensor id ${sensorId}`);
                    fetch(
                        `${SERVER_URL}/networks/${selectedNetwork}/sensors/${sensorId}/measurements?direction=previous`,
                        {
                            headers: {
                                "Content-Type": "application/json",
                            },
                            cache: "no-cache",
                        }
                    )
                        .then((res) => res?.json())
                        .then((data) => {
                            if (data === undefined) {
                                throw "";
                            } else {
                                setSensorData(sensorId, data);
                                console.log(`loaded sensor data for sensor id ${sensorId}`);
                            }
                        })
                        .catch((err) => {
                            console.error(`could not load sensor data for sensor id ${sensorId}`);
                        });

                    fetch(
                        `${SERVER_URL}/networks/${selectedNetwork}/sensors/${sensorId}/logs?direction=previous`,
                        {
                            headers: {
                                "Content-Type": "application/json",
                            },
                            cache: "no-cache",
                        }
                    )
                        .then((res) => res?.json())
                        .then((data) => {
                            if (data === undefined) {
                                throw "";
                            } else {
                                setSensorLogs(sensorId, data);
                                console.log(`loaded sensor logs for sensor id ${sensorId}`);
                                console.log(`sensor logs: ${data}`);
                            }
                        })
                        .catch((err) => {
                            console.error(`could not load sensor logs for sensor id ${sensorId}`);
                        });

                    fetch(
                        `${SERVER_URL}/networks/${selectedNetwork}/sensors/${sensorId}/logs/aggregates`,
                        {
                            headers: {
                                "Content-Type": "application/json",
                            },
                            cache: "no-cache",
                        }
                    )
                        .then((res) => res?.json())
                        .then((data) => {
                            if (data === undefined) {
                                throw "";
                            } else {
                                setSensorAggregatedLogs(sensorId, data);
                                console.log(`loaded sensor logs for sensor id ${sensorId}`);
                            }
                        })
                        .catch((err) => {
                            console.error(`could not load sensor logs for sensor id ${sensorId}`);
                        });
                }
            }
        });

    /*
    Object.values(SENSOR_IDS).forEach((sensorId) => {
        console.log(`start fetching data/logs for sensor id ${sensorId}`);
        fetch(
            `${SERVER_URL}/networks/1f705cc5-4242-458b-9201-4217455ea23c/sensors/${sensorId}/measurements?direction=previous`,
            {
                headers: {
                    "Content-Type": "application/json",
                },
                cache: "no-cache",
            }
        )
            .then((res) => res?.json())
            .then((data) => {
                if (data === undefined) {
                    throw "";
                } else {
                    setSensorData(sensorId, data);
                    console.log(`loaded sensor data for sensor id ${sensorId}`);
                }
            })
            .catch((err) => {
                console.error(`could not load sensor data for sensor id ${sensorId}`);
            });

        fetch(
            `${SERVER_URL}/networks/1f705cc5-4242-458b-9201-4217455ea23c/sensors/${sensorId}/logs?direction=previous`,
            {
                headers: {
                    "Content-Type": "application/json",
                },
                cache: "no-cache",
            }
        )
            .then((res) => res?.json())
            .then((data) => {
                if (data === undefined) {
                    throw "";
                } else {
                    setSensorLogs(sensorId, data);
                    console.log(`loaded sensor logs for sensor id ${sensorId}`);
                }
            })
            .catch((err) => {
                console.error(`could not load sensor logs for sensor id ${sensorId}`);
            });

        fetch(
            `${SERVER_URL}/networks/1f705cc5-4242-458b-9201-4217455ea23c/sensors/${sensorId}/logs/aggregates`,
            {
                headers: {
                    "Content-Type": "application/json",
                },
                cache: "no-cache",
            }
        )
            .then((res) => res?.json())
            .then((data) => {
                if (data === undefined) {
                    throw "";
                } else {
                    setSensorAggregatedLogs(sensorId, data);
                    console.log(`loaded sensor logs for sensor id ${sensorId}`);
                }
            })
            .catch((err) => {
                console.error(`could not load sensor logs for sensor id ${sensorId}`);
            });
    });*/
}
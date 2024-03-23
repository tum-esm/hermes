import {useAuthStore, useClientStore, useNetworksStore, useSensorsStore} from "../../utils/state";
import {not_logged_in} from "../../components/not_logged_in";
import {SERVER_URL} from "../../utils/constants";

export default function adminSensorsPage() {
    let auth_token = useAuthStore((state) => state.token);
    let isLoggedIn = useAuthStore((state) => state.loggedIn);
    let sensors = useSensorsStore((state) => state.state);
    let selected_network = useClientStore((state) => state.selectedNetwork)
    if(!isLoggedIn){return not_logged_in()}

    function addSensor(selected_network: string) {
        console.log("addSensor")
        let sensor_name = (document.getElementById("new_sensor_name") as HTMLInputElement).value

        fetch(`${SERVER_URL}/networks/${selected_network}/sensors`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + auth_token || ''
            },
            body: JSON.stringify({sensor_name})
        })
            .then(async response => {
                if (response.status < 200 || response.status >= 300) {
                    let response_failure = await response.json();
                    console.error("Failed to add sensor: ", response_failure);
                    alert("Failed to add sensor: " + response_failure.details)
                    throw "Failed to add sensor";
                }
                return response;

            })
            .then(response => response.json())
            .then(data => {
                console.log('Success:', data);
                // refresh page
                window.location.reload();
            });
    }


    return (
        <div className="flex h-full w-full flex-col items-center justify-center gap-y-2">
            <div className="text-xl text-slate-950 mb-8">
                <span className="font-medium">Admin / Sensors</span>
            </div>
            <div className="flex w-full justify-center">
                <h1>Add Sensor</h1>
            </div>
            <div className="flex w-full justify-center mb-8">
                <input id="new_sensor_name" type="text" className="form-control" placeholder="Sensor Name"/>
                <button onClick={(e)=>{e.preventDefault(); addSensor(selected_network)}} className="btn bg-slate-0 ml-2 mr-2 pl-2 pr-2 border border-slate-600">Add</button>
            </div>
            <div className="w-full border-t border-slate-950"></div>
            {
                //list of sensors
            }
            <div className="flex w-full justify-center flex-col">
                {
                    Object.values(sensors).map((sensor) => {
                        return (
                            <div key={sensor.sensorId} className="flex w-full justify-center m-2">
                                <h1>{sensor.sensorId}</h1>
                            </div>
                        )
                    })
                }
            </div>
        </div>
    );
}

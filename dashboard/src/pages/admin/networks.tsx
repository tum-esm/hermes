

// Admin-Page
import {useAuthStore, useNetworksStore, useSensorsStore} from "@/src/utils/state";
import {not_logged_in} from "@/src/components/not_logged_in";
import {SERVER_URL} from "@/src/utils/constants";

export default function Page() {
    let auth_token = useAuthStore((state) => state.token);
    let isLoggedIn = useAuthStore((state) => state.loggedIn);
    let networks = useNetworksStore((state) => state.networks);
    if(!isLoggedIn){return not_logged_in()}

    function addNetwork() {
        console.log("addNetwork")
        let network_name = (document.getElementById("new_network_name") as HTMLInputElement).value

        fetch(`${SERVER_URL}/networks`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': 'Bearer ' + auth_token || ''
            },
            body: JSON.stringify({network_name: network_name})
        })
            .then(async response => {
                if (response.status < 200 || response.status >= 300) {
                    let response_failure = await response.json();
                    console.error("Failed to add network: ", response_failure);
                    alert("Failed to add network: " + response_failure.details)
                    throw "Failed to add network";
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
                <span className="font-medium">Admin / Networks</span>
            </div>
            <div className="flex w-full justify-center">
                <h1>Add Network</h1>
            </div>
            <div className="flex w-full justify-center mb-8">
                <input id="new_network_name" type="text" className="form-control" placeholder="Network Name"/>
                <button onClick={(e)=>{e.preventDefault(); addNetwork()}} className="btn bg-slate-0 ml-2 mr-2 pl-2 pr-2 border border-slate-600">Add</button>
            </div>
            <div className="w-full border-t border-slate-950"></div>
            {
                //list of networks
            }
            <div className="flex w-full justify-center flex-col">
                {
                    networks.map((network, index) => {
                        return (
                            <div key={index} className="flex w-full justify-center m-2">
                                <h1>{network.network_name}</h1>
                            </div>
                        )
                    })
                }
            </div>
        </div>
    );
}

import { Link } from "react-router-dom";
import {ICONS} from "../../components/icons";
import {useAuthStore, useClientStore, useNetworksStore} from "../../utils/state";

export function Header() {
    let isLoggedIn = useAuthStore((state) => state.loggedIn);
    let networks = useNetworksStore((state) => state.networks);
    let selectedNetwork = useClientStore((state) => state.selectedNetwork);
    let setSelectedNetwork = useClientStore((state) => state.setSelectedNetwork);

    function logOut() {
        if (typeof window !== "undefined") {
            window.localStorage.removeItem("auth");
        }
        useAuthStore.getState().setAuthState(null, null, false);
    }

    return (
        <header
            className="flex h-16 w-full flex-shrink-0 flex-row items-center justify-start border-b border-slate-300 px-6">
            <Link to="/"
                className="-ml-6 flex h-full w-[5.5rem] items-center border-r border-slate-300 bg-slate-900 px-6 text-slate-100"
            >
                {ICONS.tum}
            </Link>
            <Link to="/">
                <h1 className="hidden pl-5 font-light uppercase text-slate-950 xl:block xl:text-lg 2xl:text-xl">
                    <span className="font-medium">Acropolis Sensor Network</span>{" "}
                    &nbsp;|&nbsp; Professorship of Environmental Sensing and Modeling
                </h1>
            </Link>
            <p className="ml-5 text-slate-800">
                powered by{" "}
                <a
                    href="https://github.com/tum-esm/hermes"
                    target="_blank"
                    className="font-medium text-slate-950 underline hover:text-rose-600"
                >
                    github.com/tum-esm/hermes
                </a>
            </p>
            <div className="flex-grow"/>
            {
                // network selection dropdown
            }
            <div>
                Network:
            </div>
            <>
                {
                    isLoggedIn ? (
                        <select
                            className="ml-1 form-select mr-2"
                            value={selectedNetwork}
                            onChange={(e) => {
                                console.log(`setting selected network to ${e.target.value}`);
                                setSelectedNetwork(e.target.value);
                            }}
                            disabled={networks.length == 0}
                        >
                            {
                                networks.length == 0 && <option selected key={"none"} value={undefined}>
                                    * no networks available *
                                </option>
                            }
                            {networks.map((network, index) => (
                                <option key={network.network_name} value={network.network_identifier}>
                                    {network.network_name}
                                </option>
                            ))}
                        </select>) : <></>
                }
            </>

            <>
                {
                    isLoggedIn ? (
                        <Link to="/admin">
                        <div
                                className="flex h-full w-[5.5rem] items-center justify-center border-l px-6 text-slate-800">
                                {ICONS.admin}
                            </div>
                        </Link>) : <></>
                }
            </>
            <>
                {
                    isLoggedIn ? (
                        <div onClick={(e) => {
                            e.preventDefault();
                            logOut()
                        }}>
                            <a className="flex h-full w-[5.5rem] items-center justify-center border-l px-6 text-slate-800">
                                Logout
                            </a>
                        </div>) : <></>
                }
            </>
        </header>
    );
}

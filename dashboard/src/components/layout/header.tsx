import {ICONS} from "../../components/icons";
import {useAuthStore, useClientStore, useNetworksStore} from "../../utils/state";

export function Header() {
    let isLoggedIn = useAuthStore((state) => state.loggedIn);
    let networks = useNetworksStore((state) => state.networks);
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
            <a
                href="/"
                className="-ml-6 flex h-full w-[5.5rem] items-center border-r border-slate-300 bg-slate-900 px-6 text-slate-100"
            >
                {ICONS.tum}
            </a>
            <a href="/">
                <h1 className="hidden pl-5 font-light uppercase text-slate-950 xl:block xl:text-lg 2xl:text-xl">
                    <span className="font-medium">Acropolis Sensor Network</span>{" "}
                    &nbsp;|&nbsp; Professorship of Environmental Sensing and Modeling
                </h1>
            </a>
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
                            onChange={(e) => {
                                setSelectedNetwork(e.target.value);
                            }}
                            value={useClientStore((state) => state.selectedNetwork)}
                        >
                            {networks.map((network) => (
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
                        <a href="/admin">
                            <div
                                className="flex h-full w-[5.5rem] items-center justify-center border-l px-6 text-slate-800">
                                {ICONS.admin}
                            </div>
                        </a>) : <></>
                }
            </>
            <>
                {
                    isLoggedIn ? (
                        <a href="#" onClick={(e) => {
                            e.preventDefault();
                            logOut()
                        }}>
                        <a className="flex h-full w-[5.5rem] items-center justify-center border-l px-6 text-slate-800">
                                Logout
                            </a>
                        </a>) : <></>
                }
            </>
        </header>
    );
}

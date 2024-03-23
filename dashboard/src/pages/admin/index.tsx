import {useAuthStore} from "../../utils/state";
import {not_logged_in} from "../../components/not_logged_in";
import {Link, Route, Routes} from "react-router-dom";
import indexPage from "@/src/pages";
import loginPage from "@/src/pages/login";
import sensorPage from "@/src/pages/sensor/[sensorName]";
import adminNetworksPage from "@/src/pages/admin/networks";
import adminSensorsPage from "@/src/pages/admin/sensors";
import adminUsersPage from "@/src/pages/admin/users";

// Admin-Page
export default function adminPage() {
    let isLoggedIn = useAuthStore((state) => state.loggedIn);
    if(!isLoggedIn){return not_logged_in()}

    return (
        <Routes>
            <Route index element={
                <div className="flex h-full w-full flex-col items-center justify-center gap-y-2">
                    <div className="text-xl text-slate-950">
                        <span className="font-medium">Admin</span>
                    </div>
                    <div className="flex h-full w-full flex-col items-center justify-center gap-y-2">
                        <div>
                            <Link to="/admin/networks">Networks</Link>
                        </div>
                        <div>
                            <Link to="/admin/sensors">Sensors</Link>
                        </div>
                        <div>
                            <Link to="/admin/users">Users</Link>
                        </div>
                        <div>
                            <Link to="/admin/logs">Logs</Link>
                        </div>
                    </div>
                </div>
            }/>
            <Route path="networks" Component={adminNetworksPage}/>
            <Route path="sensors" Component={adminSensorsPage}/>
            <Route path="users" Component={adminUsersPage}/>
            <Route path="logs" element={<><h1>Not implemented.</h1><Link to="/admin">go back</Link></>}/>
        </Routes>


    );
}

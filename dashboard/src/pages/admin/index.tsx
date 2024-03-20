import {useAuthStore} from "../../utils/state";
import {not_logged_in} from "../../components/not_logged_in";

// Admin-Page
export default function Page() {
    let isLoggedIn = useAuthStore((state) => state.loggedIn);
    if(!isLoggedIn){return not_logged_in()}

    return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-y-2">
        <div className="text-xl text-slate-950">
            <span className="font-medium">Admin</span>
        </div>
        <div className="flex h-full w-full flex-col items-center justify-center gap-y-2">
            <div>
                <a href="/admin/networks">Networks</a>
            </div>
            <div>
                <a href="/admin/sensors">Sensors</a>
            </div>
            <div>
                <a href="/admin/users">Users</a>
            </div>
            <div>
                <a href="/admin/logs">Logs</a>
            </div>
        </div>
    </div>
  );
}

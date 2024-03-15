

// Admin-Page
import {useAuthStore} from "@/src/utils/state";
import {not_logged_in} from "@/src/components/not_logged_in";

export default function Page() {
    let isLoggedIn = useAuthStore((state) => state.loggedIn);
    if(!isLoggedIn){return not_logged_in()}

    return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-y-2">
        <div className="text-xl text-slate-950">
            <span className="font-medium">Admin / Networks</span>
        </div>
    </div>
  );
}

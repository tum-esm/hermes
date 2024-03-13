import Link from "next/link";
import {SERVER_URL} from "@/src/utils/constants";
import {useAuthStore} from "@/src/utils/state";

// Login-Page
export default function Page() {
    let setAuthState = useAuthStore((state) => state.setAuthState);
    let isLoggedIn = useAuthStore((state) => state.loggedIn);

    if (isLoggedIn){
        return (
            <div>
                <h1>You are already logged in</h1>
                <div >
                    <a href="/">Go to home</a>
                </div>
            </div>
        )
    }
    function login() {
        const username = (document.getElementById("username") as HTMLInputElement).value;
        const password = (document.getElementById("password") as HTMLInputElement).value;
        fetch(`${SERVER_URL}/authentication`, {
            method: "POST",
            headers: {
                "Content-Type": "form-data",
            },
            body: JSON.stringify({ "user_name": username, password }),
        })
            .then(async (response) => {
                if (response.status < 200 || response.status >= 300) {
                    let failure = await response.json();
                    console.error("Login Failed: ", failure);
                    alert(`Login failed: ${failure.details}`)
                    throw "Login failed";
                }
                return response.json();
            })
            .then((data) => {
                if (data.error) {
                    alert(data.error);
                } else {
                    alert("Login successful");
                    if (typeof window !== "undefined") {
                        window.localStorage.setItem("auth", JSON.stringify({token: data.access_token, username, loggedIn: true}));
                    }
                    setAuthState(data.access_token, username, true);
                    console.log(data);
                }
            });
    }

    return (
    <div className="flex h-full w-full flex-col items-center justify-center gap-y-2">
        <form onSubmit={(e)=>{e.preventDefault(); login()}}>
            <div className="text-xl text-slate-950">
                <span className="font-medium">Login</span>
            </div>
            <div className="flex h-full w-full flex-col items-center justify-center gap-y-2">
                <label htmlFor="username">Username:</label>
                <input type="text" id="username" name="username" />
                <label htmlFor="password">Password:</label>
                <input type="password" id="password" name="password" />
                <button type="submit">Login</button>
            </div>
        </form>
    </div>
  );
}

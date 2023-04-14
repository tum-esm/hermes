import { Rubik } from "next/font/google";
import { SensorList } from "@/components/layout/sensorList";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { useEffect } from "react";
import { useServerStore } from "@/components/state";

const RUBIK = Rubik({ subsets: ["latin"] });
const SERVER_URL = "https://sea-turtle-app-38sco.ondigitalocean.app";

export default function Layout({ children }: { children: React.ReactNode }) {
  const setServerState = useServerStore((state) => state.setState);

  useEffect(() => {
    console.log("loading");

    // mock server data with settimeout until server doesn't have CORS error anymore
    setTimeout(() => {
      setServerState({
        environment: "production",
        commit_sha: "12abc345",
        branch_name: "main",
        start_time: 1661475666,
      });
    }, 1500);

    /*fetch(`${SERVER_URL}/status`, {
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-cache",
    }).then((res) => res.json());
      .then((data) => {
        setServerState(data);
        console.log("loaded server state");
      });*/
  }, []);

  return (
    <div className={RUBIK.className}>
      <Header />
      <main className="flex h-[calc(100vh-6.5rem)] w-screen flex-row">
        <nav className="flex h-full w-[24rem] flex-col overflow-y-scroll border-r border-slate-300">
          <SensorList />
        </nav>
        <div className="h-full flex-grow overflow-y-scroll bg-slate-50 p-6">
          {children}
        </div>
      </main>
      <Footer />
    </div>
  );
}

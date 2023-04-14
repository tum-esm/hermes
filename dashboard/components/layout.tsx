import { Rubik } from "next/font/google";
import { SensorList } from "@/components/layout/sensorList";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";
import { useEffect } from "react";
import { useServerStore, useNetworkStore } from "@/components/state";
import { SENSOR_IDS } from "@/components/constants";

const RUBIK = Rubik({ subsets: ["latin"] });
const SERVER_URL = "https://sea-turtle-app-38sco.ondigitalocean.app";

export default function Layout({ children }: { children: React.ReactNode }) {
  const setServerState = useServerStore((state) => state.setState);
  const setSensorData = useNetworkStore((state) => state.setSensorData);
  const setSensorLogs = useNetworkStore((state) => state.setSensorLogs);

  useEffect(() => {
    console.log("start loading data from server");

    fetch(`${SERVER_URL}/status`, {
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-cache",
    })
      .then((res) => res?.json())
      .then((data) => {
        if (data === undefined) {
          console.error("could not load server state");
        } else {
          console.log({ data });
          setServerState(data);
          console.log("successfully loaded server state");
        }
      });
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

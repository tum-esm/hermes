import { Rubik } from "next/font/google";
import { SensorList } from "@/src/components/layout/sensorList";
import { Header } from "@/src/components/layout/header";
import { useEffect, useRef } from "react";
import { useServerStore, useNetworkStore } from "@/src/utils/state";
import { SENSOR_IDS, SERVER_URL } from "@/src/utils/constants";
import Head from "next/head";
import { usePathname } from "next/navigation";

const RUBIK = Rubik({ subsets: ["latin"] });

export default function Layout({ children }: { children: React.ReactNode }) {
  const setServerState = useServerStore((state) => state.setState);
  const setSensorData = useNetworkStore((state) => state.setData);
  const setSensorLogs = useNetworkStore((state) => state.setLogs);
  const setSensorAggregatedLogs = useNetworkStore(
    (state) => state.setAggregatedLogs
  );

  const pathname = usePathname();
  const pageDivRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (pageDivRef.current !== null) {
      pageDivRef.current.scroll({ top: 0, behavior: "smooth" });
    }
  }, [pathname, pageDivRef.current === null]);

  useEffect(() => {
    console.log("start fetching");

    fetch(`${SERVER_URL}/status`, {
      headers: {
        "Content-Type": "application/json",
      },
      cache: "no-cache",
    })
      .then((res) => res?.json())
      .then((data) => {
        if (data === undefined) {
          throw "";
        } else {
          console.log({ data });
          setServerState(data);
          console.log("successfully loaded server state");
        }
      })
      .catch((err) => {
        console.error("could not load server state");
      });

    Object.values(SENSOR_IDS).forEach((sensorId) => {
      console.log(`start fetching data/logs for sensor id ${sensorId}`);

      fetch(
        `${SERVER_URL}/sensors/${sensorId}/measurements?direction=previous`,
        {
          headers: {
            "Content-Type": "application/json",
          },
          cache: "no-cache",
        }
      )
        .then((res) => res?.json())
        .then((data) => {
          if (data === undefined) {
            throw "";
          } else {
            setSensorData(sensorId, data);
            console.log(`loaded sensor data for sensor id ${sensorId}`);
          }
        })
        .catch((err) => {
          console.error(`could not load sensor data for sensor id ${sensorId}`);
        });

      fetch(`${SERVER_URL}/sensors/${sensorId}/logs?direction=previous`, {
        headers: {
          "Content-Type": "application/json",
        },
        cache: "no-cache",
      })
        .then((res) => res?.json())
        .then((data) => {
          if (data === undefined) {
            throw "";
          } else {
            setSensorLogs(sensorId, data);
            console.log(`loaded sensor logs for sensor id ${sensorId}`);
          }
        })
        .catch((err) => {
          console.error(`could not load sensor logs for sensor id ${sensorId}`);
        });

      fetch(`${SERVER_URL}/sensors/${sensorId}/logs/aggregates`, {
        headers: {
          "Content-Type": "application/json",
        },
        cache: "no-cache",
      })
        .then((res) => res?.json())
        .then((data) => {
          if (data === undefined) {
            throw "";
          } else {
            setSensorAggregatedLogs(sensorId, data);
            console.log(`loaded sensor logs for sensor id ${sensorId}`);
          }
        })
        .catch((err) => {
          console.error(`could not load sensor logs for sensor id ${sensorId}`);
        });
    });
  }, []);

  return (
    <div className={RUBIK.className}>
      <Head>
        <title>Acropolis Sensor Network</title>
        <link rel="shortcut icon" href="/favicon.ico" />
        <meta property="og:title" content="Acropolis Sensor Network" />
        <meta
          property="og:description"
          content="Acropolis Sensor Network | Professorship of Environmental Sensing And Modeling"
        />
        <meta property="og:image" content="/favicon.ico" />
      </Head>
      <div className="flex items-center justify-center w-screen h-screen text-lg xl:hidden">
        Please use a larger screen
      </div>
      <div className="hidden xl:block">
        <Header />
        <main className="flex h-[calc(100vh-4rem)] w-screen flex-row">
          <nav className="flex h-full w-[24rem] flex-shrink-0 flex-col overflow-y-scroll border-r border-slate-300">
            <SensorList />
          </nav>
          <div
            className="flex-grow h-full p-6 pb-32 overflow-y-scroll bg-slate-50 "
            ref={pageDivRef}
          >
            {children}
          </div>
        </main>
      </div>
    </div>
  );
}

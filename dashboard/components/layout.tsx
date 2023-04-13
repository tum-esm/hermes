import { Rubik } from "next/font/google";
import { SensorList } from "@/components/layout/sensorList";
import { Header } from "@/components/layout/header";
import { Footer } from "@/components/layout/footer";

const rubik = Rubik({ subsets: ["latin"] });

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className={rubik.className}>
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

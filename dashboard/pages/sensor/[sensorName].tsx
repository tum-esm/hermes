import { SENSOR_IDS } from "@/components/constants";
import { ICONS } from "@/components/icons";
import Link from "next/link";

// TODO: render tabs for logs and measurements
// TODO: render logs
// TODO: render measurements

export function getStaticPaths() {
  return {
    paths: Object.keys(SENSOR_IDS).map((sensorName) => ({
      params: { sensorName },
    })),
    fallback: false,
  };
}

// `getStaticPaths` requires using `getStaticProps`
export function getStaticProps(context: any) {
  return {
    // Passed to the page component as props
    props: { sensorName: context.params.sensorName },
  };
}

export default function Page({ sensorName }: { sensorName: string }) {
  const sensorId = SENSOR_IDS[sensorName];

  return (
    <>
      <Link
        href="/"
        className="inline-flex flex-row items-center justify-center gap-x-1 p-1 text-sm font-medium text-slate-800 hover:text-rose-600"
      >
        <div className="h-3.5 w-3.5 rotate-180">{ICONS.chevronRight}</div>
        <p>back to overview</p>
      </Link>

      <h2 className="mt-3 px-4 text-2xl text-slate-800">
        Station <span className="font-semibold text-black">{sensorName}</span>{" "}
        (ID: {sensorId})
      </h2>
    </>
  );
}

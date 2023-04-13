export function Footer() {
  return (
    <footer className="flex h-10 flex-row items-center justify-center bg-slate-900 text-sm text-slate-100">
      © TUM Professorship of Environmental Sensing and Modeling
      {process.env.NEXT_PUBLIC_BUILD_TIMESTAMP !== undefined && (
        <>
          ,{" "}
          {new Date(
            parseInt(process.env.NEXT_PUBLIC_BUILD_TIMESTAMP) * 1000
          ).getFullYear()}
        </>
      )}
    </footer>
  );
}

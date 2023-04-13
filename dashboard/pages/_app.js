import "./globals.css";
import Layout from "@/components/layout.tsx";

export default function App({ Component, pageProps }) {
  return (
    <Layout>
      <Component {...pageProps} />
    </Layout>
  );
}

import indexPage from "./pages/index";
import Layout from "./components/layout";
import {
    BrowserRouter,
    Route,
    Routes
} from "react-router-dom";
import loginPage from "@/src/pages/login";

export default function App() {
    return (
        <Layout>
            <BrowserRouter>
                <Routes>
                    <Route path="/" Component={indexPage} />
                    <Route path="/login" Component={loginPage} />
                </Routes>
            </BrowserRouter>
        </Layout>
    );
}

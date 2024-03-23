import {Link} from "react-router-dom";

export function not_logged_in(){
    return <>
        <div>
            <h1>You are not logged in</h1>
            <div >
                <Link to="/login">Go to login</Link>
            </div>
        </div>
    </>;
}
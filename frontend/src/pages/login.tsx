import { useEffect } from "react";
import { getCSRFToken } from "../api/auth";

function Login() {
  useEffect(() => {
    getCSRFToken()
      .then((response) => {
        console.log(response.data);
      })
      .catch((error) => {
        console.error(error);
      });
  }, []);

  return <h1>Login</h1>;
}

export default Login;

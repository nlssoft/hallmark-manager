import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../hooks/useAuth";

function LoginPage() {
  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const navigate = useNavigate();
  const { loginUser } = useAuth();

  async function handleLogin(e: React.SubmitEvent<HTMLFormElement>) {
    e.preventDefault();

    try {
      await loginUser({
        username,
        password,
      });

      navigate("/dashboard");
    } catch (e) {
      console.log(e);
    }
  }

  return (
    <form onSubmit={handleLogin}>
      <input
        className="border"
        type="text"
        value={username}
        onChange={(e) => setUsername(e.target.value)}
      />
      <input
        className="border"
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
      />
      <button className="border" type="submit">
        Login
      </button>
    </form>
  );
}

export default LoginPage;

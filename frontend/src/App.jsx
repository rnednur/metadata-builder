import React from "react";
import Routes from "./Routes";
import { JobProvider } from "./contexts/JobContext";

function App() {
  return (
    <JobProvider>
      <Routes />
    </JobProvider>
  );
}

export default App;

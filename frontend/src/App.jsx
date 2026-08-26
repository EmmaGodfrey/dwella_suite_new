import React from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { ToastContainer } from "react-toastify";
import Routers from "./Route";
import { queryClient } from "./Services/queryClient";

const App = () => (
  <div className="App">
    <QueryClientProvider client={queryClient}>
      <Routers />
      <ToastContainer position="top-right" newestOnTop />
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </div>
);

export default App;

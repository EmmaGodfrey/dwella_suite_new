import React from "react";
import { QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import Routers from "./Route";
import { queryClient } from "./Services/queryClient";
import AnimationThemeProvider from "./_helper/AnimationTheme/AnimationThemeProvider";
import CustomizerProvider from "./_helper/Customizer/CustomizerProvider";

const App = () => (
  <div className="App">
    <QueryClientProvider client={queryClient}>
      <CustomizerProvider>
        <AnimationThemeProvider>
          <Routers />
        </AnimationThemeProvider>
      </CustomizerProvider>
      <ReactQueryDevtools initialIsOpen={false} />
    </QueryClientProvider>
  </div>
);

export default App;
